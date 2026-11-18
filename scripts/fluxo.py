#!/usr/bin/env python3
"""Controle local das fases de revisão de uma obra. Use --help para a sintaxe."""

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path


FIELDS = {
    "leitura": ("contribuicao", "encadeamento"),
    "diagnostico": ("progressao", "cadencia", "decisao"),
    "edicao": ("intervencao",),
    "conferencia": ("fidelidade", "bordas"),
    "remontagem": ("ligacao", "resultado"),
}
STAGES = tuple(FIELDS) + ("entrega",)
READING = ("leitura", "conferencia", "remontagem")


def require(test, message):
    if not test:
        raise ValueError(message)


def snapshot(path):
    raw = Path(path).read_bytes()
    return hashlib.sha256(raw).hexdigest(), raw.decode("utf-8")


def checked(path, digest):
    actual, text = snapshot(path)
    require(actual == digest, f"A edição mudou em {path}. Confira a mudança e reabra a unidade.")
    return text


def read_json(path):
    raw = sys.stdin.read() if str(path) == "-" else Path(path).read_text(encoding="utf-8")
    return json.loads(raw)


def new_book(args):
    names = read_json(args.entradas)
    require(isinstance(names, list) and names, "Forneça uma lista ordenada de arquivos.")
    chapters = []
    seen = set()
    for name in names:
        require(isinstance(name, str) and Path(name).is_absolute(), "Cada entrada exige caminho absoluto.")
        path = Path(name).resolve(strict=True)
        identity = (path.stat().st_dev, path.stat().st_ino)
        require(identity not in seen, f"Entrada duplicada no mapa: {path}")
        seen.add(identity)
        digest, _ = snapshot(path)
        chapters.append({"arquivo": str(path), "sha256": digest, "notas": {}})
    moc = Path(args.mapa).resolve(strict=True)
    digest, content = snapshot(moc)
    require(content.strip(), "Preencha o mapa antes de iniciar.")
    return {"versao": 1, "mapa": str(moc), "mapa_sha256": digest,
            "fase": "leitura", "unidades": chapters, "posicao": 0}


def next_unit(book):
    for number, unit in enumerate(book["unidades"], 1):
        if book["fase"] not in unit["notas"]:
            return number, unit
    return None, None


def reset_position(book):
    book["posicao"] = 0
    book.pop("fim_exibido", None)


def original(unit):
    return checked(unit["arquivo"], unit["sha256"])


def candidate(unit):
    edit = unit["notas"]["edicao"]
    return checked(edit["arquivo"], edit["sha256"])


def verify_book(book):
    checked(book["mapa"], book["mapa_sha256"])
    for unit in book["unidades"]:
        original(unit)
        if "edicao" in unit["notas"]:
            candidate(unit)


def status(book):
    phase = book["fase"]
    report = {"fase": phase, "unidades": len(book["unidades"])}
    if phase != "concluido":
        report["ficha"] = str(Path(__file__).resolve().parent.parent / "fases" / (phase + ".md"))
    if phase in FIELDS:
        number, unit = next_unit(book)
        report["registradas"] = sum(phase in u["notas"] for u in book["unidades"])
        if unit:
            report.update(numero=number, entrada=unit["arquivo"], posicao=book["posicao"])
            if "edicao" in unit["notas"]:
                report["candidato"] = unit["notas"]["edicao"]["arquivo"]
        else:
            report["proximo"] = "Conferir as decisões e chamar avancar " + phase
    return report


def reopen(book, phase, number):
    require(1 <= number <= len(book["unidades"]), "Unidade fora do mapa.")
    unit = book["unidades"][number - 1]
    current = book["fase"]
    require(current == "concluido" or STAGES.index(phase) <= STAGES.index(current),
            "Só se pode reabrir uma fase já alcançada.")
    require(phase in unit["notas"] or (current == phase and next_unit(book)[0] == number),
            "Esta fase da unidade ainda não foi alcançada.")
    checked(book["mapa"], book["mapa_sha256"])
    if phase == "leitura":
        unit["sha256"], _ = snapshot(unit["arquivo"])
    else:
        original(unit)
    for later in STAGES[STAGES.index(phase):]:
        unit["notas"].pop(later, None)
    # Uma mudança local também pode afetar retomadas distantes no livro.
    if STAGES.index(phase) <= STAGES.index("edicao"):
        for other in book["unidades"]:
            other["notas"].pop("remontagem", None)
    book["fase"] = phase
    reset_position(book)


def read_chunk(book, text, args):
    start = book["posicao"]
    require(start < len(text), "Leitura completa. Registre a decisão sobre a unidade.")
    require(1 <= args.limite <= 12000, "Use limite entre 1 e 12000 caracteres.")
    end = min(start + args.limite, len(text))
    if end < len(text):
        boundary = text.rfind("\n", start + args.limite // 2, end)
        if boundary >= 0:
            end = boundary + 1
    book["fim_exibido"] = end
    return f"Trecho [{start}, {end}) de {len(text)} caracteres\n" + text[start:end]


def confirm_chunk(book, text, args):
    start = book["posicao"]
    end = book.get("fim_exibido")
    require(end is not None and args.fim == end, "Leia o bloco atual e confirme o fim exibido.")
    tail = " ".join(text[start:end].split())[-180:]
    anchor = " ".join(args.final_lido.split())
    require((not tail and not anchor) or (bool(tail) and len(anchor) >= min(12, len(tail)) and anchor in tail),
            "Transcreva uma expressão literal do final do bloco lido.")
    book["posicao"] = end
    del book["fim_exibido"]


def register(book, unit, args):
    phase = book["fase"]
    require(args.fase == phase, "A fase pedida difere da fase aberta.")
    note = read_json(args.nota)
    require(isinstance(note, dict), "A nota deve ser um objeto JSON.")
    for key in FIELDS[phase]:
        require(isinstance(note.get(key), str) and note[key].strip(), f"Preencha {key}.")
    require(phase == "edicao" or not args.candidato, "Indique o candidato na fase de edição.")
    text = original(unit)
    record = {"parecer": note}
    if phase == "diagnostico":
        require(note["decisao"] in ("preservar", "editar"), "Escolha preservar ou editar.")
    if phase == "edicao":
        require(args.candidato, "Indique o candidato com --candidato.")
        path = Path(args.candidato).resolve(strict=True)
        for other in book["unidades"]:
            if other is unit:
                continue
            paths = [other["arquivo"]]
            if "edicao" in other["notas"]:
                paths.append(other["notas"]["edicao"]["arquivo"])
            require(not any(path.samefile(p) for p in paths), "Este arquivo pertence a outra unidade.")
        digest, text = snapshot(path)
        record.update(arquivo=str(path), sha256=digest)
    if phase in ("conferencia", "remontagem"):
        text = candidate(unit)
    if phase in READING:
        require(book["posicao"] == len(text), "Ainda há texto a ler nesta unidade.")
    anchor = note.get("trecho")
    require(isinstance(anchor, str) and (bool(anchor.strip()) or not text.strip()) and anchor in text,
            "Inclua em trecho uma passagem literal desta edição.")
    unit["notas"][phase] = record
    reset_position(book)


def execute(book, args):
    cmd, phase = args.comando, book["fase"]
    if cmd == "atual":
        return status(book)
    if cmd == "notas":
        require(1 <= args.numero <= len(book["unidades"]), "Unidade fora do mapa.")
        return book["unidades"][args.numero - 1]
    if cmd == "reabrir":
        reopen(book, args.fase, args.numero)
        return status(book)
    if cmd == "entregar":
        require(phase == "entrega", "Conclua a remontagem antes de entregar.")
        verify_book(book)
        book["fase"] = "concluido"
        return status(book)
    require(phase in FIELDS, f"Fase atual: {phase}.")
    number, unit = next_unit(book)
    if cmd == "avancar":
        require(args.fase == phase and unit is None, f"A fase {phase} ainda não foi aceita por inteiro ou mudou.")
        verify_book(book)
        book["fase"] = STAGES[STAGES.index(phase) + 1]
        reset_position(book)
        return status(book)
    require(unit is not None, "Todas as unidades desta fase foram registradas.")
    if cmd == "registrar":
        require(args.numero == number, f"A próxima unidade é {number}.")
        register(book, unit, args)
        return status(book)
    require(phase in READING, "Use ler e confirmar nas fases de leitura, conferência e remontagem.")
    text = original(unit) if phase == "leitura" else candidate(unit)
    if cmd == "ler":
        return read_chunk(book, text, args)
    confirm_chunk(book, text, args)
    return status(book)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("estado", type=Path, help="arquivo SQLite da obra na pasta de trabalho")
    commands = parser.add_subparsers(dest="comando", required=True)
    init = commands.add_parser("iniciar")
    init.add_argument("entradas")
    init.add_argument("mapa")
    commands.add_parser("atual")
    notes = commands.add_parser("notas")
    notes.add_argument("numero", type=int)
    read = commands.add_parser("ler")
    read.add_argument("--limite", type=int, default=6500)
    ack = commands.add_parser("confirmar")
    ack.add_argument("fim", type=int)
    ack.add_argument("final_lido", nargs="?", default="")
    reg = commands.add_parser("registrar")
    reg.add_argument("fase", choices=FIELDS.keys())
    reg.add_argument("numero", type=int)
    reg.add_argument("nota", help="arquivo JSON ou - para entrada padrão")
    reg.add_argument("--candidato")
    advance = commands.add_parser("avancar")
    advance.add_argument("fase", choices=FIELDS.keys())
    again = commands.add_parser("reabrir")
    again.add_argument("fase", choices=FIELDS.keys())
    again.add_argument("numero", type=int)
    commands.add_parser("entregar")
    args = parser.parse_args()
    if args.comando == "iniciar":
        book = new_book(args)
    else:
        require(args.estado.is_file(), "Inicie o controle desta obra primeiro.")
    db = sqlite3.connect(str(args.estado), timeout=10)
    try:
        with db:
            db.execute("BEGIN IMMEDIATE")
            if args.comando == "iniciar":
                db.execute("CREATE TABLE IF NOT EXISTS obra (id INTEGER PRIMARY KEY CHECK(id=1), estado TEXT NOT NULL)")
                require(not db.execute("SELECT 1 FROM obra").fetchone(), "O controle já existe. Use atual.")
                db.execute("INSERT INTO obra VALUES (1, ?)", (json.dumps(book, ensure_ascii=False),))
                result = status(book)
            else:
                row = db.execute("SELECT estado FROM obra WHERE id=1").fetchone()
                require(row is not None, "Controle sem obra.")
                book = json.loads(row[0])
                result = execute(book, args)
                if args.comando not in ("atual", "notas"):
                    db.execute("UPDATE obra SET estado=? WHERE id=1", (json.dumps(book, ensure_ascii=False),))
        print(result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, sqlite3.Error) as error:
        sys.exit(str(error))
