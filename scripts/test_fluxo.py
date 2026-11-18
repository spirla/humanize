"""Regressões do controle editorial, exercitadas pela linha de comando pública."""

import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().with_name("fluxo.py")


class Fluxo(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.db = self.root / "obra.sqlite"
        self.paths = []
        for idx, content in enumerate(("Primeiro bloco do capítulo.\nSegunda passagem com condição e exceção.", "A última retomada fecha a obra.")):
            p = self.root / f"capitulo-{idx}.md"
            p.write_text(content, encoding="utf-8")
            self.paths.append(p)
        self.entries = self.root / "entradas.json"
        self.entries.write_text(json.dumps([str(p) for p in self.paths]))
        self.moc = self.root / "moc.md"
        self.moc.write_text("1. Condição e exceção. 2. A retomada.", encoding="utf-8")
        self.cmd("iniciar", self.entries, self.moc)

    def cmd(self, *args, fail=None, data=None):
        r = subprocess.run([sys.executable, str(SCRIPT), str(self.db)] + list(map(str, args)),
                           input=json.dumps(data) if data is not None else None,
                           capture_output=True, text=True)
        if fail is not None:
            self.assertNotEqual(r.returncode, 0)
            self.assertIn(fail, r.stderr)
        else:
            self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def read_all(self, path):
        text = path.read_text(encoding="utf-8")
        start = 0
        while start < len(text):
            output = self.cmd("ler", "--limite", 31)
            line, piece = output.split("\n", 1)
            end = int(line.split(", ")[1].split(")")[0])
            self.assertEqual(piece, text[start:end] + "\n")
            self.cmd("confirmar", end, " ".join(text[start:end].split())[-18:])
            start = end

    def record(self, phase, number, path, *args, fail=None, **extra):
        notes = {
            "leitura": {"contribuicao":"Apresenta o efeito da condição.", "encadeamento":"A exceção segue a condição."},
            "diagnostico": {"progressao":"A regra prepara a exceção.", "cadencia":"O fecho traz uma condição própria.", "decisao":"preservar"},
            "edicao": {"intervencao":"Preservada a condição expressa."},
            "conferencia": {"fidelidade":"A exceção conserva a redação inicial.", "bordas":"O fecho completa a regra."},
            "remontagem": {"ligacao":"O segundo capítulo retoma a condição.", "resultado":"A aplicação fica no último capítulo."},
        }
        note = dict(notes[phase], trecho=path.read_text(encoding="utf-8").splitlines()[0])
        if phase in ("conferencia", "remontagem"):
            note["pendencias"] = []
        note.update(extra)
        self.cmd("registrar", phase, number, "-", *args, fail=fail, data=note)

    def test_rejects_skips_and_partial_or_stale_reads(self):
        path = self.paths[0]
        self.cmd("confirmar", 12, "sem leitura", fail="Leia o bloco")
        self.cmd("avancar", "leitura", fail="não foi aceita")
        self.cmd("entregar", fail="remontagem")
        self.record("leitura", 2, path, fail="próxima unidade")
        self.record("edicao", 1, path, fail="fase pedida")
        sample = self.cmd("ler", "--limite", 12)
        self.assertIn(path.read_text(encoding="utf-8")[:12], sample)
        self.cmd("confirmar", 12, "outra passagem", fail="literal")
        self.cmd("confirmar", 12, path.read_text(encoding="utf-8")[:12])
        self.record("leitura", 1, path, fail="Ainda há texto")
        path.write_text("Alteração material.", encoding="utf-8")
        self.cmd("ler", fail="edição mudou")
        self.cmd("reabrir", "leitura", 1)
        self.assertIn("Alteração material.", self.cmd("ler"))

    def test_truncated_output_and_legacy_resume(self):
        path = self.paths[0]
        path.write_text("A entrada orienta. " + "O prazo corre da inscrição. " * 90 + "Fim do capítulo.")
        self.cmd("reabrir", "leitura", 1)
        shown = self.cmd("ler")
        text = path.read_text()
        visible = self.root / "saida.txt"
        visible.write_text(shown[:210] + "…saída truncada…" + shown[-200:])
        self.cmd("confirmar", len(text), text[-16:], "--saida", visible, fail="Saída incompleta")
        self.assertEqual(json.loads(self.cmd("atual"))["posicao"], 0)
        self.cmd("confirmar", len(text), text[-16:], "--meio", "outro conceito", fail="--meio")
        visible.write_text(shown)
        self.cmd("confirmar", len(text), text[-16:], "--saida", visible)
        self.cmd("reabrir", "leitura", 1)
        self.cmd("ler")
        self.cmd("confirmar", len(text), text[-16:], "--meio", "prazo corre da inscrição")
        self.cmd("reabrir", "leitura", 1)
        with sqlite3.connect(self.db) as db:
            b = json.loads(db.execute("SELECT estado FROM obra").fetchone()[0])
            b["versao"] = 1
            db.execute("UPDATE obra SET estado=?", (json.dumps(b),))
        self.cmd("ler", "--limite", 1550)
        self.cmd("confirmar", 1550, text[1530:1550])
        status = json.loads(self.cmd("atualizar"))
        self.assertEqual((status["posicao"], status["versao"]), (1550, 2))

    def test_aberturas_cross_sections_and_protected_text(self):
        p = self.paths[0]
        p.write_text("# Início\n\nA regra vale.\n\n> Outra voz.\n\nA exceção permanece.\n\n"
                     "## Aplicação\n\n```md\nO código fica.\n```\n\nA hipótese muda.\n\n"
                     "| Tabela |\n|---|\n\n==A consequência== depende do ato.\n")
        self.cmd("reabrir", "leitura", 1)
        series = json.loads(self.cmd("aberturas", 1))
        self.assertEqual(len(series), 1)
        self.assertEqual([x["secao"] for x in series[0]["passagens"]],
                         ["Início", "Início", "Aplicação", "Aplicação"])

    def test_batch_findings_survive_reopening_and_block_delivery(self):
        for phase in ("leitura", "diagnostico", "edicao", "conferencia", "remontagem"):
            for number, path in enumerate(self.paths, 1):
                if phase in ("leitura", "conferencia", "remontagem"):
                    self.read_all(path)
                extra = {}
                if phase == "remontagem" and number == 2:
                    extra["pendencias"] = [{"unidade": 1, "problema": "Harmonizar o título com o ato."},
                                            {"unidade": 2, "problema": "Completar a hipótese do exercício."}]
                self.record(phase, number, path, *(["--candidato", path] if phase == "edicao" else []), **extra)
            if phase != "remontagem":
                self.cmd("avancar", phase)
        self.cmd("avancar", "remontagem", fail="pendências abertas")
        self.cmd("reabrir", "edicao", 1, 9, fail="fora do mapa")
        self.assertEqual(json.loads(self.cmd("atual"))["fase"], "remontagem")
        self.cmd("reabrir", "edicao", 1, 2)
        self.assertEqual(len(json.loads(self.cmd("atual"))["pendencias"]), 2)
        self.record("edicao", 1, self.paths[0], "--candidato", self.paths[0], fail="resolucoes")
        for n, path in enumerate(self.paths, 1):
            self.record("edicao", n, path, "--candidato", path, resolucoes={str(n): "A passagem foi cotejada e a hipótese está expressa."})
        self.cmd("avancar", "edicao")
        previous = json.loads(self.cmd("notas", 1))["notas"]["edicao"]
        self.cmd("reabrir", "edicao", 1)
        self.record("edicao", 1, self.paths[0], "--candidato", self.paths[0])
        unit = json.loads(self.cmd("notas", 1))
        self.assertEqual(unit["resolucoes_anteriores"]["1"], {
            "achado": previous["achados_tratados"]["1"],
            "decisao": previous["parecer"]["resolucoes"]["1"],
            "sha256": previous["sha256"],
        })
        self.assertNotIn("2", unit["resolucoes_anteriores"])
        self.assertNotIn("pendencias", json.loads(self.cmd("atual")))
        self.cmd("avancar", "edicao")
        for phase in ("conferencia", "remontagem"):
            for n, path in enumerate(self.paths, 1):
                self.read_all(path)
                self.record(phase, n, path)
            self.cmd("avancar", phase)
        self.assertEqual(json.loads(self.cmd("entregar"))["fase"], "concluido")

    def test_entire_book_reassembly_and_version_changes(self):
        candidates = []
        for path in self.paths:
            candidate = self.root / ("rev-" + path.name)
            candidate.write_bytes(path.read_bytes())
            candidates.append(candidate)
        for phase in ("leitura", "diagnostico", "edicao", "conferencia", "remontagem"):
            for number, path in enumerate(self.paths if phase in ("leitura", "diagnostico") else candidates, 1):
                if phase in ("leitura", "conferencia", "remontagem"):
                    self.read_all(path)
                args = ["--candidato", path] if phase == "edicao" else []
                self.record(phase, number, path, *args)
            self.cmd("avancar", phase)
        candidates[1].write_text("O fecho aprovado sofreu alteração.", encoding="utf-8")
        self.cmd("entregar", fail="edição mudou")
        self.cmd("reabrir", "edicao", 2)
        retained = json.loads(self.cmd("notas", 1))["notas"]
        self.assertIn("conferencia", retained)
        self.assertNotIn("remontagem", retained)
        self.record("edicao", 2, candidates[1], "--candidato", candidates[1])
        self.cmd("avancar", "edicao")
        self.read_all(candidates[1])
        self.record("conferencia", 2, candidates[1])
        self.cmd("avancar", "conferencia")
        for number, path in enumerate(candidates, 1):
            self.read_all(path)
            self.record("remontagem", number, path)
        self.cmd("avancar", "remontagem")
        self.assertEqual(json.loads(self.cmd("entregar"))["fase"], "concluido")
        self.cmd("iniciar", self.entries, self.moc, fail="já existe")


if __name__ == "__main__":
    unittest.main()
