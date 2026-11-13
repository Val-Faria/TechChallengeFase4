from __future__ import annotations
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from techchallenge4 import (
    AlertStore,
    combinar_audio_video,
    detectar_prescricoes,
    detectar_series,
    replay_events,
    salvar_resultados,
)
from techchallenge4.core import normalizar_video, normalizar_audio
from techchallenge4.demo import structured_examples, run_demo
from techchallenge4.dashboard import render_dashboard
from techchallenge4.openai_text import BudgetExceeded, analyze_text_openai, validate_analysis


def result(audio=("neutro", 0.9), video=None, **kwargs):
    return combinar_audio_video(
        audio,
        video or {"alerta": False, "nivel": "nenhum"},
        id_caso=kwargs.pop("id_caso", "teste"),
        **kwargs,
    )


class FusionTests(unittest.TestCase):
    def test_neutral_does_not_cancel_high_video(self):
        r = result(
            video={"alerta": True, "nivel": "alto", "eventos": [{"inicio_s": 1, "fim_s": 20}]}
        )
        self.assertEqual(r["nivel"], "alto")
        self.assertTrue(r["requer_revisao"])

    def test_missing_and_low_confidence_request_review(self):
        for audio in [None, ("neutro", 0.1), {"status": "erro", "motivo": "arquivo ilegível"}]:
            with self.subTest(audio=audio):
                r = result(audio)
                self.assertEqual(r["status"], "incompleto")
                self.assertFalse(r["alerta"])
                self.assertTrue(r["requer_revisao"])

    def test_expected_text_missing_is_explicit(self):
        r = result(fontes_esperadas=["audio", "video", "texto_openai"])
        self.assertIn("texto_openai", r["fontes_inconclusivas"])

    def test_video_parcial_sem_evento_nao_vira_normalidade(self):
        source = {
            "alerta": False,
            "nivel": "nenhum",
            "cobertura_parcial": True,
            "limitacoes": ["Anotações de ausência não confirmadas."],
            "parametros": {"conf": 0.4},
        }
        r = result(video=source)
        self.assertFalse(r["alerta"])
        self.assertTrue(r["requer_revisao"])
        self.assertEqual(r["status"], "incompleto")
        self.assertIn("video", r["fontes_inconclusivas"])
        self.assertEqual(r["fontes"][1]["limitacoes"], source["limitacoes"])
        r["fontes"][1]["limitacoes"].append("novo")
        self.assertEqual(len(source["limitacoes"]), 1)

    def test_video_parcial_nao_cancela_alerta_positivo(self):
        r = result(video={"alerta": True, "nivel": "alto", "cobertura_parcial": True})
        self.assertTrue(r["alerta"])
        self.assertEqual(r["nivel"], "alto")
        self.assertIn("video", r["fontes_inconclusivas"])

    def test_video_recusa_cobertura_textual(self):
        with self.assertRaises(ValueError):
            normalizar_video({"alerta": False, "nivel": "nenhum", "cobertura_parcial": "false"})

    def test_painel_preserva_limites_e_escapa_conteudo(self):
        r = result(
            video={
                "alerta": False,
                "nivel": "nenhum",
                "cobertura_parcial": True,
                "limitacoes": ["<script>injetado</script>"],
            }
        )
        page = render_dashboard([{"resultado": r, "revisor": "", "revisado_em_utc": None}])
        self.assertIn("cobertura parcial", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn("<script>", page)

    def test_baixa_confianca_video_nao_e_descartada(self):
        r = result(video={"status": "baixa_confianca", "motivo": "Cena não suportada."})
        self.assertIn("video", r["fontes_inconclusivas"])
        self.assertTrue(r["requer_revisao"])
        self.assertFalse(r["alerta"])

    def test_unknown_class_and_nonfinite_confidence_rejected(self):
        for audio in [
            ("diagnostico", 0.8),
            ("neutro", math.nan),
            ("neutro", True),
            ("neutro", 1.1),
        ]:
            with self.subTest(audio=audio), self.assertRaises(ValueError):
                normalizar_audio(audio)

    def test_confidence_boundary_is_inclusive(self):
        self.assertEqual(normalizar_audio(("tristeza", 0.7))["status"], "ok")
        self.assertEqual(normalizar_audio(("tristeza", 0.699))["status"], "baixa_confianca")

    def test_invalid_video_contract_rejected(self):
        values = [
            {"alerta": "true", "nivel": "alto"},
            {"alerta": False, "nivel": "alto"},
            {"alerta": True, "nivel": "alto", "eventos": [{"inicio_s": 5, "fim_s": 1}]},
            {
                "alerta": True,
                "nivel": "alto",
                "eventos": [{"inicio_s": 1, "fim_s": 2, "duracao_s": 10}],
            },
        ]
        for value in values:
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalizar_video(value)

    def test_duplicate_source_rejected(self):
        with self.assertRaises(ValueError):
            result(fontes_adicionais=[normalizar_audio(("neutro", 0.9))])

    def test_safe_case_id_and_stable_identity(self):
        self.assertEqual(result()["id_resultado"], result()["id_resultado"])
        for case in ["../arquivo", "", "a" * 81]:
            with self.subTest(case=case), self.assertRaises(ValueError):
                result(id_caso=case)

    def test_sources_not_mutated(self):
        video = {"alerta": True, "nivel": "alto", "eventos": [{"inicio_s": 1, "fim_s": 2}]}
        r = result(video=video)
        r["fontes"][1]["eventos"][0]["inicio_s"] = 100
        self.assertEqual(video["eventos"][0]["inicio_s"], 1)


class StructuredTests(unittest.TestCase):
    def setUp(self):
        self.examples = structured_examples()

    def test_all_three_anomaly_sources_detect_controlled_changes(self):
        self.assertEqual(
            {r["modalidade"] for r in self.examples["resultados"]},
            {"sinais_vitais", "movimentacao", "prescricoes"},
        )
        self.assertTrue(all(r["alerta"] and r["simulado"] for r in self.examples["resultados"]))

    def test_history_never_fit_on_current_outlier(self):
        r = self.examples["resultados"][0]
        self.assertLess(r["referencias"]["batimentos"]["mediana"], 80)
        self.assertTrue(any(e["valor"] == 120 for e in r["eventos"]))

    def test_normal_observation_has_no_anomaly(self):
        r = detectar_series(
            self.examples["historico"],
            self.examples["observacoes"][:1],
            ["batimentos"],
            "sinais_vitais",
        )
        self.assertFalse(r["alerta"])

    def test_constant_history_and_insufficient_history_inconclusive(self):
        h = [{**x, "batimentos": 72} for x in self.examples["historico"]]
        for hist in [h, h[:2]]:
            r = detectar_series(hist, self.examples["observacoes"], ["batimentos"], "sinais_vitais")
            self.assertEqual(r["status"], "indisponivel")

    def test_unsorted_and_naive_timestamps_rejected(self):
        for h in [
            list(reversed(self.examples["historico"])),
            [{**x, "timestamp": x["timestamp"][:-6]} for x in self.examples["historico"]],
        ]:
            with self.subTest(h=h[:1]), self.assertRaises(ValueError):
                detectar_series(h, self.examples["observacoes"], ["batimentos"], "sinais_vitais")

    def test_different_units_are_flagged_without_comparing_doses(self):
        p = self.examples["prescricoes"]
        p[1] = {**p[1], "unidade": "g", "dose": 0.02}
        r = detectar_prescricoes(p)
        reasons = r["eventos"][0]["motivos"]
        self.assertTrue(any("não comparadas" in x for x in reasons))
        self.assertFalse(any("variação relativa" in x for x in reasons))

    def test_zero_or_nonfinite_dose_rejected(self):
        for dose in [0, -1, math.inf, True]:
            p = [{**x} for x in self.examples["prescricoes"]]
            p[1]["dose"] = dose
            with self.subTest(dose=dose), self.assertRaises(ValueError):
                detectar_prescricoes(p)


class DeliveryTests(unittest.TestCase):
    def test_concurrent_duplicate_delivery_creates_one_review_task(self):
        from concurrent.futures import ThreadPoolExecutor

        with tempfile.TemporaryDirectory() as d:
            store = AlertStore(Path(d) / "a.db")
            r = result(("tristeza", 0.9))
            with ThreadPoolExecutor(max_workers=8) as pool:
                receipts = list(pool.map(lambda _: store.deliver(r), range(50)))
            self.assertEqual(len(store.list_alerts()), 1)
            self.assertTrue(all(receipt == receipts[0] for receipt in receipts))
            self.assertEqual(len(store.audit_log()), 1)

    def test_same_identifier_with_divergent_evidence_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            store = AlertStore(Path(d) / "a.db")
            r = result(("tristeza", 0.9))
            store.deliver(r)
            r["nivel"] = "alto"
            with self.assertRaises(ValueError):
                store.deliver(r)

    def test_persistence_dedup_and_review_audit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inbox.db"
            store = AlertStore(path)
            r = result(("tristeza", 0.9))
            first = store.deliver(r)
            self.assertEqual(first["status"], "persistido")
            self.assertEqual(store.deliver(r), first)
            reopened = AlertStore(path)
            self.assertEqual(len(reopened.list_alerts()), 1)
            self.assertTrue(reopened.acknowledge(r["id_resultado"], "teste"))
            self.assertFalse(reopened.acknowledge(r["id_resultado"], "teste"))
            self.assertEqual(len(reopened.audit_log()), 2)
            self.assertIsNotNone(reopened.list_alerts()[0]["revisado_em_utc"])

    def test_healthy_result_is_not_enqueued(self):
        with tempfile.TemporaryDirectory() as d:
            store = AlertStore(Path(d) / "a.db")
            store.deliver(result())
            self.assertEqual(store.list_alerts(), [])

    def test_replay_reports_only_delivery_latency(self):
        with tempfile.TemporaryDirectory() as d:
            store = AlertStore(Path(d) / "a.db")
            events = [{"offset_s": 1, "resultado": result(("tristeza", 0.9))}]
            rows = replay_events(events, store)
            self.assertGreaterEqual(rows[0]["latencia_entrega_local_ms"], 0)
            self.assertEqual(rows[0]["escopo_latencia"], "persistencia_local_sem_inferencia")
            with self.assertRaises(ValueError):
                replay_events(events + [{"offset_s": 0.1, "resultado": result()}], store)

    def test_dashboard_escapes_content_and_shows_synthetic_flag(self):
        with tempfile.TemporaryDirectory() as d:
            store = AlertStore(Path(d) / "a.db")
            r = result(("tristeza", 0.9), simulado=True)
            r["fontes"][0]["motivo"] = "<script>alert(1)</script>"
            store.deliver(r)
            page = render_dashboard(store.list_alerts())
            self.assertNotIn("<script>", page)
            self.assertIn("&lt;script&gt;", page)
            self.assertIn("Contém fonte simulada: sim", page)

    def test_snapshot_export_is_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            salvar_resultados([result()], d)
            salvar_resultados([result()], d)
            lines = (Path(d) / "resultados.jsonl").read_text(encoding="utf8").splitlines()
            self.assertEqual(len(lines), 1)
            self.assertEqual(json.loads(lines[0])["id_caso"], "teste")

    def test_end_to_end_offline_demo(self):
        with tempfile.TemporaryDirectory() as d:
            summary = run_demo(d)
            self.assertTrue(summary["idempotencia"])
            r = json.loads((Path(d) / "demonstracao-integrada.json").read_text(encoding="utf8"))
            self.assertEqual(r["status"], "incompleto")
            self.assertIn("texto_openai", r["fontes_inconclusivas"])
            self.assertEqual(r["entrega"]["status"], "persistido")


class TextTests(unittest.TestCase):
    def test_rejected_response_records_usage_and_never_enters_cache(self):
        def fake(payload, key):
            return {
                "status": "completed",
                "id": "rejected-offline-test",
                "usage": {"input_tokens": 200, "output_tokens": 150},
                "output": [{"content": [{"type": "output_text", "text": json.dumps(self.data())}]}],
            }

        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                analyze_text_openai("Estou bem.", d, request_fn=fake)
            self.assertEqual(len(list(Path(d).glob("rejeitada_*.json"))), 1)
            self.assertEqual(list(Path(d).glob("texto_*.json")), [])
            ledger = json.loads((Path(d) / "orcamento_openai.json").read_text(encoding="utf8"))
            self.assertEqual(ledger["chamadas"][0]["estado"], "falha_com_consumo_medido")
            self.assertEqual(ledger["chamadas"][0]["input_tokens"], 200)

    def data(self, state="negado", context="paciente_atual", quote="não estou com falta de ar"):
        return {
            "sentimento": "neutro",
            "mencoes": [
                {"termo": "falta de ar", "estado": state, "contexto": context, "evidencia": quote}
            ],
            "limitacoes": [],
        }

    def test_negation_does_not_raise_symptom_alert(self):
        self.assertFalse(
            validate_analysis(self.data(), "Hoje não estou com falta de ar.")["alerta"]
        )

    def test_historical_or_third_party_does_not_raise_current_alert(self):
        for context in ["historico", "terceiro"]:
            with self.subTest(context=context):
                self.assertFalse(
                    validate_analysis(
                        self.data("afirmado", context), "Hoje não estou com falta de ar."
                    )["alerta"]
                )

    def test_affirmed_and_uncertain_are_routed_to_review(self):
        text = "estou com falta de ar"
        for state in ["afirmado", "incerto"]:
            r = validate_analysis(self.data(state, quote=text), text)
            self.assertTrue(r["alerta"])

    def test_fabricated_evidence_and_unknown_fields_rejected(self):
        with self.assertRaises(ValueError):
            validate_analysis(self.data(), "Olá, estou bem.")
        with self.assertRaises(ValueError):
            validate_analysis(
                {**self.data(), "diagnostico": "invento"}, "não estou com falta de ar"
            )

    def test_budget_reservation_cache_and_zero_network_on_second_call(self):
        calls = []

        def fake(payload, key):
            calls.append(payload)
            return {
                "status": "completed",
                "id": "offline-test",
                "usage": {"input_tokens": 100, "output_tokens": 100},
                "output": [{"content": [{"type": "output_text", "text": json.dumps(self.data())}]}],
            }

        with tempfile.TemporaryDirectory() as d:
            first = analyze_text_openai("não estou com falta de ar", d, request_fn=fake)
            second = analyze_text_openai("não estou com falta de ar", d, request_fn=fake)
            self.assertEqual(len(calls), 1)
            self.assertFalse(first["cache_utilizado"])
            self.assertTrue(second["cache_utilizado"])
            ledger = json.loads((Path(d) / "orcamento_openai.json").read_text(encoding="utf8"))
            self.assertLess(ledger["chamadas"][0]["custo_contabilizado_usd"], 0.01)
            self.assertFalse(calls[0]["store"])

    def test_budget_prevents_call_and_failed_call_keeps_reservation(self):
        def fail(payload, key):
            raise TimeoutError("offline")

        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(BudgetExceeded):
                analyze_text_openai("Olá", d, max_budget_usd=0.00000001, request_fn=fail)
            with self.assertRaises(TimeoutError):
                analyze_text_openai("Olá", d, request_fn=fail)
            ledger = json.loads((Path(d) / "orcamento_openai.json").read_text(encoding="utf8"))
            self.assertEqual(len(ledger["chamadas"]), 1)
            self.assertEqual(ledger["chamadas"][0]["estado"], "falha_reserva_mantida")


if __name__ == "__main__":
    unittest.main()
