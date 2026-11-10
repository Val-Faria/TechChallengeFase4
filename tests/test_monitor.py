from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from techchallenge4.delivery import AlertStore
from techchallenge4.monitor import StructuredMonitor, example_packets, run_stream


class MonitorTests(unittest.TestCase):
    def test_incremental_detection_excludes_future_outlier_from_baseline(self):
        with tempfile.TemporaryDirectory() as d:
            store = AlertStore(Path(d)/"a.db")
            monitor = StructuredMonitor("monitor-sintetico", store)
            packets = example_packets()
            rows = [monitor.feed(packet) for packet in packets[:31]]
            self.assertFalse(rows[-1]["resultado"]["alerta"])
            self.assertEqual(rows[-1]["resultado"]["status"], "completo")
            self.assertEqual(store.list_alerts(), [])
            baseline = deepcopy(monitor.history)
            changed = monitor.feed(packets[31])
            self.assertEqual(baseline, monitor.history)
            self.assertEqual(len(monitor.history["sinais_vitais"]), 30)
            positives = {s["modalidade"] for s in changed["resultado"]["fontes"] if s["alerta"]}
            self.assertEqual(positives, {"sinais_vitais", "movimentacao", "prescricoes"})
            self.assertEqual(len(store.list_alerts()), 1)
            self.assertGreaterEqual(changed["latencia_processamento_local_ms"], 0)

    def test_duplicate_is_ignored_and_divergent_event_id_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            monitor = StructuredMonitor("monitor-sintetico", AlertStore(Path(d)/"a.db"))
            p = example_packets()[0]
            monitor.feed(p)
            again = monitor.feed(p)
            self.assertTrue(again["duplicado_ignorado"])
            self.assertEqual(len(monitor.history["sinais_vitais"]), 1)
            changed = deepcopy(p)
            changed["sinais_vitais"]["batimentos"] = 500
            with self.assertRaises(ValueError):
                monitor.feed(changed)

    def test_invalid_packet_rolls_back_all_modalities_and_clock(self):
        with tempfile.TemporaryDirectory() as d:
            monitor = StructuredMonitor("monitor-sintetico", AlertStore(Path(d)/"a.db"))
            p = example_packets()[0]
            invalid = deepcopy(p)
            invalid["movimentacao"]["intensidade"] = True
            with self.assertRaises(ValueError):
                monitor.feed(invalid)
            self.assertEqual(monitor.history["sinais_vitais"], [])
            self.assertIsNone(monitor.last_time)
            monitor.feed(p)
            previous = deepcopy(example_packets()[1])
            previous["timestamp"] = p["timestamp"]
            with self.assertRaises(ValueError):
                monitor.feed(previous)

    def test_live_tail_processes_append_and_stops_at_bound(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d)/"entrada.jsonl"
            source.write_text("", encoding="utf8")
            packets = example_packets()[:2]
            def append():
                time.sleep(.1)
                with source.open("a", encoding="utf8") as writer:
                    encoded = json.dumps(packets[0])+"\n"
                    writer.write(encoded[:20]); writer.flush()
                    time.sleep(.1)
                    writer.write(encoded[20:]); writer.flush()
                    writer.write(json.dumps(packets[1])+"\n"); writer.flush()
            thread = threading.Thread(target=append)
            thread.start()
            summary = run_stream(source, Path(d)/"saida", follow=True, idle_timeout=1, max_events=2)
            thread.join()
            self.assertEqual(summary["pacotes_processados"], 2)
            self.assertEqual(summary["modo"], "tail_jsonl")

    def test_live_tail_idle_timeout_is_bounded(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d)/"vazio.jsonl"
            source.write_text("", encoding="utf8")
            started = time.monotonic()
            summary = run_stream(source, Path(d)/"saida", follow=True, idle_timeout=.1)
            self.assertEqual(summary["pacotes_processados"], 0)
            self.assertLess(time.monotonic()-started, 2)


if __name__ == "__main__":
    unittest.main()
