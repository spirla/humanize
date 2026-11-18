#!/usr/bin/env python3
"""Controle local das fases de revisão de uma obra. Use --help para a sintaxe."""

import argparse
from itertools import groupby
import hashlib
import json
import re
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
    return {"versao": 2, "mapa": str(moc), "mapa_sha256": digest,
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


def status(book, detalhar=False):
    phase = book["fase"]
    report = {"versao": book.get("versao", 1), "fase": phase, "unidades": len(book["unidades"])}
    if book.get("pendencias"):
        report["pendencias_abertas"] = len(book["pendencias"])
        if detalhar:
            report["pendencias"] = book["pendencias"]
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
        previous = unit["notas"].pop(later, None)
        if later == "edicao" and previous and previous.get("achados_tratados"):
            history = unit.setdefault("resolucoes_anteriores", {})
            for key, issue in previous["achados_tratados"].items():
                history[key] = {
                    "achado": issue,
                    "decisao": previous["parecer"]["resolucoes"][key],
                    "sha256": previous["sha256"],
                }
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
    if args.saida:
        visible = sys.stdin.read() if args.saida == "-" else Path(args.saida).read_text(encoding="utf-8")
        header = f"Trecho [{start}, {end}) de {len(text)} caracteres\n"
        require(header + text[start:end] in visible, "Saída incompleta ou de outra versão. Repita ler com um bloco menor.")
    elif book.get("versao", 1) >= 2 and end - start >= 1500:
        third = (end - start) // 3
        sample = " ".join(text[start+third:end-third].split())
        supplied = " ".join((args.meio or "").split())
        require(len(supplied) >= min(len(sample), 12) and supplied in sample,
                "Use --meio com expressão literal próxima ao centro visível ou --saida com a saída exibida.")
    book["posicao"] = end
    del book["fim_exibido"]


def series_de_abertura(text):
    """Localiza séries na prosa Markdown e mantém a seção de cada ocorrência."""
    section, fence, paragraph = "", "", []
    passages = []
    frontmatter = text.startswith("---\n") and "\n---\n" in text[3:]
    if frontmatter:
        text = text.split("\n---\n", 1)[1]
    for line in (*text.splitlines(), ""):
        stripped = line.strip()
        if fence:
            if re.fullmatch(re.escape(fence[0]) + "{" + str(len(fence)) + ",}", stripped):
                fence = ""
            continue
        marker = re.match(r"^(`{3,}|~{3,})", stripped)
        heading = re.match(r"^#{1,6}\s+(.+)", stripped)
        structural = re.match(r"^(?:>|\||[-+*]\s|\d+[.)]\s|<|!\[|[-*_]{3,}$)", stripped)
        if stripped and not (marker or heading or structural):
            paragraph.append(stripped)
            continue
        if paragraph:
            opening = " ".join(paragraph)
            clean = re.sub(r"==(?:[a-z]:)?|[*_]", "", opening)
            word = re.match(r"^[«“‘(\[]*([^\W\d_]+)", clean)
            if word:
                passages.append((word.group(1).casefold(), section, opening[:110]))
            paragraph = []
        if marker:
            fence = marker.group(1)
        if heading:
            section = heading.group(1)
    result = []
    for word, group in groupby(passages, key=lambda row: row[0]):
        rows = list(group)
        if len(rows) >= 3:
            result.append({"abertura": word, "passagens": [
                {"secao": sec, "inicio": opening} for _, sec, opening in rows]})
    articles = {"a", "o", "as", "os"}
    for starts_with_article, group in groupby(passages, key=lambda row: row[0] in articles):
        if not starts_with_article:
            continue
        rows = list(group)
        if len(rows) >= 3 and len({word for word, _, _ in rows}) > 1:
            result.append({"abertura": "artigos variados", "passagens": [
                {"secao": sec, "inicio": opening} for _, sec, opening in rows]})
    return result


def registrar_achados(book, note, number):
    issues = note.get("pendencias", [] if book.get("versao", 1) == 1 else None)
    require(isinstance(issues, list), "Informe pendencias como lista, vazia se a unidade estiver apta.")
    for issue in issues:
        require(isinstance(issue, dict), "Indique unidade e problema em cada pendência.")
        target, problem = issue.get("unidade"), issue.get("problema")
        require(type(target) is int and 1 <= target <= len(book["unidades"]), "Unidade da pendência inválida.")
        require(isinstance(problem, str) and problem.strip(), "Descreva o problema e a passagem atingida.")
        key = str(book.get("ultimo_achado", 0) + 1)
        book["ultimo_achado"] = int(key)
        book.setdefault("pendencias", {})[key] = {"origem": number, "fase": book["fase"],
                                                "unidade": target, "problema": problem}


def resolver_achados(book, note, number):
    pending = book.get("pendencias", {})
    keys = {k for k, issue in pending.items() if issue["unidade"] == number}
    answers = note.get("resolucoes", {})
    require(isinstance(answers, dict) and answers.keys() == keys,
            "Informe em resolucoes uma decisão para cada pendência desta unidade. Consulte atual.")
    for key in keys:
        require(isinstance(answers[key], str) and answers[key].strip(), "Descreva como resolveu cada pendência.")
    return {key: pending.pop(key) for key in keys}


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
    if phase in ("conferencia", "remontagem"):
        registrar_achados(book, note, args.numero)
    if phase == "edicao":
        resolved = resolver_achados(book, note, args.numero)
        if resolved:
            record["achados_tratados"] = resolved
    unit["notas"][phase] = record
    reset_position(book)


def execute(book, args):
    cmd, phase = args.comando, book["fase"]
    if cmd == "atual":
        return status(book, detalhar=True)
    if cmd == "atualizar":
        book["versao"] = 2
        return status(book)
    if cmd == "aberturas":
        require(1 <= args.numero <= len(book["unidades"]), "Unidade fora do mapa.")
        unit = book["unidades"][args.numero - 1]
        return series_de_abertura(candidate(unit) if "edicao" in unit["notas"] else original(unit))
    if cmd == "notas":
        require(1 <= args.numero <= len(book["unidades"]), "Unidade fora do mapa.")
        return book["unidades"][args.numero - 1]
    if cmd == "reabrir":
        for number in dict.fromkeys(args.numero):
            reopen(book, args.fase, number)
        return status(book)
    if cmd == "entregar":
        require(phase == "entrega", "Conclua a remontagem antes de entregar.")
        require(not book.get("pendencias"), "Resolva as pendências antes da entrega.")
        verify_book(book)
        book["fase"] = "concluido"
        return status(book)
    require(phase in FIELDS, f"Fase atual: {phase}.")
    number, unit = next_unit(book)
    if cmd == "avancar":
        require(args.fase == phase and unit is None, f"A fase {phase} ainda não foi aceita por inteiro ou mudou.")
        if phase in ("edicao", "conferencia", "remontagem"):
            require(not book.get("pendencias"), "Há pendências abertas. Consulte atual e reabra a edição das unidades atingidas.")
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
    commands.add_parser("atualizar", help="aplicar o contrato atual preservando posições e notas já registradas")
    commands.add_parser("aberturas").add_argument("numero", type=int)
    notes = commands.add_parser("notas")
    notes.add_argument("numero", type=int)
    read = commands.add_parser("ler")
    read.add_argument("--limite", type=int, default=6500)
    ack = commands.add_parser("confirmar")
    ack.add_argument("fim", type=int)
    ack.add_argument("final_lido", nargs="?", default="")
    proof = ack.add_mutually_exclusive_group()
    proof.add_argument("--saida", help="texto exportado da saída realmente exibida ao leitor, ou - para stdin")
    proof.add_argument("--meio", help="expressão literal próxima à metade do bloco")
    reg = commands.add_parser("registrar")
    reg.add_argument("fase", choices=FIELDS.keys())
    reg.add_argument("numero", type=int)
    reg.add_argument("nota", help="arquivo JSON ou - para entrada padrão")
    reg.add_argument("--candidato")
    advance = commands.add_parser("avancar")
    advance.add_argument("fase", choices=FIELDS.keys())
    again = commands.add_parser("reabrir")
    again.add_argument("fase", choices=FIELDS.keys())
    again.add_argument("numero", type=int, nargs="+")
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
                if args.comando not in ("atual", "notas", "aberturas"):
                    db.execute("UPDATE obra SET estado=? WHERE id=1", (json.dumps(book, ensure_ascii=False),))
        print(result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, sqlite3.Error) as error:
        sys.exit(str(error))
