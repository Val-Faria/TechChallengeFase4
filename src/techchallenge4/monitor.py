"""Monitor incremental de pacotes JSONL, com referência anterior congelada.

Processa cada pacote ao chegar. A medição cobre detectores estatísticos, fusão
e persistência local, sem aquisição de sensores nem inferência de áudio/vídeo.
"""

from __future__ import annotations
import argparse
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import time
from .core import (
    detectar_prescricoes,
    detectar_series,
    fonte_indisponivel,
    fundir_fontes_normalizadas,
    normalizar_audio,
    normalizar_video,
    numero_finito,
    validar_fonte,
)
from .delivery import AlertStore
from .reports import atomic_write, salvar_resultados


def parse_time(value):
    moment = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if moment.tzinfo is None:
        raise ValueError("Timestamp do pacote deve incluir fuso horário.")
    return moment


class StructuredMonitor:
    """Estado de um único caso, sem incorporar observações à referência de treino."""

    def __init__(self, case_id, store, *, warmup=30, max_source_age_s=60):
        if type(warmup) is not int or warmup < 20:
            raise ValueError("A referência exige pelo menos 20 amostras anteriores.")
        self.case_id, self.store, self.warmup = case_id, store, warmup
        self.max_source_age_s = numero_finito(max_source_age_s, "max_source_age_s", 0.1)
        self.history = {"sinais_vitais": [], "movimentacao": []}
        self.fields = {}
        self.prescriptions = []
        self.latest = {}
        self.last_time = None
        self.processed = {}

    def feed(self, packet):
        started = time.perf_counter()
        packet = deepcopy(packet)
        if packet.get("id_caso") != self.case_id:
            raise ValueError("Pacote pertence a outro caso.")
        if not any(
            k in packet
            for k in [
                "sinais_vitais",
                "movimentacao",
                "prescricao",
                "audio",
                "video",
                "texto_openai",
            ]
        ):
            raise ValueError("Pacote sem modalidade reconhecida.")
        encoded = json.dumps(packet, ensure_ascii=False, sort_keys=True, allow_nan=False)
        digest = hashlib.sha256(encoded.encode()).hexdigest()
        event_id = packet.get("event_id", digest)
        if not isinstance(event_id, str) or not 1 <= len(event_id) <= 120:
            raise ValueError("event_id inválido.")
        if event_id in self.processed:
            previous_digest, saved = self.processed[event_id]
            if previous_digest != digest:
                raise ValueError("event_id reutilizado com conteúdo divergente.")
            return {**deepcopy(saved), "duplicado_ignorado": True}
        moment = parse_time(packet["timestamp"])
        if self.last_time is not None and moment <= self.last_time:
            raise ValueError("Pacotes novos exigem timestamps estritamente crescentes.")
        # Transactional in-memory update: an invalid packet never partly changes
        # the baseline or any latest state.
        history, fields = deepcopy(self.history), deepcopy(self.fields)
        prescriptions, latest = deepcopy(self.prescriptions), deepcopy(self.latest)
        simulated = packet.get("simulado", False)
        if type(simulated) is not bool:
            raise ValueError("simulado deve ser booleano.")
        for modality in ["sinais_vitais", "movimentacao"]:
            if modality not in packet:
                continue
            values = packet[modality]
            if not isinstance(values, dict) or not values:
                raise ValueError("Forneça campos numéricos da série.")
            keys = sorted(values)
            if any(
                not isinstance(key, str)
                or not key.strip()
                or key == "timestamp"
                or key.startswith("_")
                for key in keys
            ):
                raise ValueError("Nome de campo reservado ou inválido na série.")
            if modality in fields and fields[modality] != keys:
                raise ValueError("Os campos da série mudaram durante a sessão.")
            fields[modality] = keys
            row = {key: numero_finito(values[key], key) for key in keys}
            row["timestamp"] = packet["timestamp"]
            row["_simulado"] = simulated
            if len(history[modality]) < self.warmup:
                history[modality].append(row)
                source = fonte_indisponivel(
                    modality,
                    f"Referência em aquecimento: {len(history[modality])}/{self.warmup} amostras.",
                    simulado=simulated,
                )
                source["origem"] = "stream_jsonl_referencia_anterior"
                source["amostras_referencia"] = len(history[modality])
            else:
                source = detectar_series(
                    history[modality],
                    [row],
                    keys,
                    modality,
                    simulado=simulated or any(h.get("_simulado", False) for h in history[modality]),
                )
                source["amostras_referencia"] = len(history[modality])
                source["referencia_congelada"] = True
            source["timestamp_amostra"] = packet["timestamp"]
            latest[modality] = source
        if "prescricao" in packet:
            row = {**packet["prescricao"], "timestamp": packet["timestamp"]}
            row["_simulado"] = simulated
            # Validate a first prescription too; the shared comparator only
            # starts once a comparable medication history exists.
            numero_finito(row["dose"], "dose", 1e-9)
            numero_finito(row["intervalo_h"], "intervalo_h", 1e-9)
            if not all(
                isinstance(row[k], str) and row[k].strip()
                for k in ["medicamento_id", "unidade", "via"]
            ):
                raise ValueError("Identificação de prescrição inválida.")
            prescriptions.append(row)
            source = detectar_prescricoes(
                prescriptions, simulado=any(p.get("_simulado", False) for p in prescriptions)
            )
            source["timestamp_amostra"] = packet["timestamp"]
            latest["prescricoes"] = source
        if "audio" in packet:
            latest["audio"] = normalizar_audio(
                packet["audio"], origem="resultado_audio_recebido", simulado=simulated
            )
            latest["audio"]["timestamp_amostra"] = packet["timestamp"]
        if "video" in packet:
            latest["video"] = normalizar_video(
                packet["video"], origem="resultado_video_recebido", simulado=simulated
            )
            latest["video"]["timestamp_amostra"] = packet["timestamp"]
        if "texto_openai" in packet:
            source = validar_fonte(packet["texto_openai"])
            if source["modalidade"] != "texto_openai":
                raise ValueError("Fonte textual deve identificar sua modalidade.")
            source["simulado"] = bool(source.get("simulado", False) or simulated)
            source["timestamp_amostra"] = packet["timestamp"]
            latest["texto_openai"] = source
        fresh = []
        for modality, source in latest.items():
            age = (moment - parse_time(source["timestamp_amostra"])).total_seconds()
            if age > self.max_source_age_s:
                stale = fonte_indisponivel(
                    modality,
                    f"Fonte desatualizada: {age:.1f} s sem nova amostra.",
                    simulado=source.get("simulado", False),
                )
                stale.update({"timestamp_amostra": source["timestamp_amostra"], "idade_s": age})
                fresh.append(stale)
            else:
                fresh.append(source)
        result = fundir_fontes_normalizadas(
            fresh,
            id_caso=self.case_id,
            pareamento="pacotes_do_mesmo_caso_de_demonstracao_sem_validacao_clinica",
            fontes_esperadas=[
                "audio",
                "video",
                "texto_openai",
                "sinais_vitais",
                "movimentacao",
                "prescricoes",
            ],
        )
        positive = [
            source for source in result["fontes"] if source["status"] == "ok" and source["alerta"]
        ]
        warming_up = any(
            not latest.get(modality, {}).get("referencia_congelada", False) for modality in history
        )
        # Warmup is recorded in the journal and visible in the final snapshot;
        # it does not flood the review inbox unless another source raised a signal.
        if warming_up and not positive:
            result["entrega"] = {
                "destino": "caixa_local_equipe_medica",
                "status": "aquecimento_sem_entrega",
            }
        else:
            result["entrega"] = self.store.deliver(result)
        self.history, self.fields = history, fields
        self.prescriptions, self.latest, self.last_time = prescriptions, latest, moment
        record = {
            "event_id": event_id,
            "timestamp_origem": packet["timestamp"],
            "resultado": result,
            "duplicado_ignorado": False,
            "latencia_processamento_local_ms": (time.perf_counter() - started) * 1000,
            "escopo_latencia": "detector_estatistico_fusao_persistencia_sem_inferencia_modelos",
            "amostras_referencia": {key: len(rows) for key, rows in history.items()},
        }
        self.processed[event_id] = digest, deepcopy(record)
        return record


def example_packets():
    start = datetime(2026, 11, 9, 15, tzinfo=timezone.utc)
    packets = []
    for index in range(32):
        packet = {
            "id_caso": "monitor-sintetico",
            "event_id": f"pacote-{index:03d}",
            "timestamp": (start + timedelta(seconds=index)).isoformat(),
            "simulado": True,
            "sinais_vitais": {
                "batimentos": 72 + (index % 5) - 2,
                "oxigenacao": 97 + (index % 3) - 1,
                "pressao_sistolica": 120 + (index % 5) - 2,
                "pressao_diastolica": 80 + (index % 3) - 1,
            },
            "movimentacao": {"intensidade": 10 + (index % 5) - 2},
            "prescricao": {
                "medicamento_id": "medicamento_demo",
                "dose": 10,
                "unidade": "mg",
                "via": "oral",
                "intervalo_h": 12,
            },
        }
        if index == 0:
            packet.update(
                {
                    "audio": {"classe_audio": "neutro", "confianca_audio": 0.95},
                    "video": {"alerta": False, "nivel": "nenhum"},
                    "texto_openai": {
                        "modalidade": "texto_openai",
                        "status": "ok",
                        "alerta": False,
                        "nivel": "nenhum",
                        "motivo": "Controle textual simulado sem sinal.",
                        "origem": "controle_sintetico_sem_chamada_api",
                        "simulado": True,
                    },
                }
            )
        if index == 31:
            packet["sinais_vitais"] = {
                "batimentos": 120,
                "oxigenacao": 85,
                "pressao_sistolica": 160,
                "pressao_diastolica": 105,
            }
            packet["movimentacao"] = {"intensidade": 50}
            packet["prescricao"]["dose"] = 20
        packets.append(packet)
    return packets


def run_stream(
    path, output, *, follow=False, idle_timeout=5.0, max_events=1000, speed=0.0, max_source_age_s=60
):
    if type(max_events) is not int or not 1 <= max_events <= 100000:
        raise ValueError("Defina max_events entre 1 e 100.000.")
    idle_timeout = numero_finito(idle_timeout, "idle_timeout", 0.1, 60)
    speed = numero_finito(speed, "speed", 0)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    store = AlertStore(output / "alertas.sqlite3")
    monitors, journal, previous_time = {}, [], None
    last_received = time.monotonic()
    with (
        Path(path).open(encoding="utf-8-sig") as stream,
        (output / "eventos_processados.jsonl").open("w", encoding="utf8") as log,
    ):
        while len(journal) < max_events:
            position = stream.tell()
            line = stream.readline()
            if line and not line.endswith("\n") and follow:
                # Writers may append a record in several chunks. Keep the
                # incomplete bytes for the next poll instead of dropping them.
                stream.seek(position)
                if time.monotonic() - last_received >= idle_timeout:
                    break
                time.sleep(0.05)
                continue
            if not line:
                if not follow or time.monotonic() - last_received >= idle_timeout:
                    break
                time.sleep(0.05)
                continue
            if not line.strip():
                continue
            packet = json.loads(line)
            moment = parse_time(packet["timestamp"])
            if speed and previous_time is not None:
                delay = max(0, (moment - previous_time).total_seconds() / speed)
                time.sleep(min(delay, 60))
            previous_time = moment
            case = packet["id_caso"]
            if case not in monitors:
                monitors[case] = StructuredMonitor(case, store, max_source_age_s=max_source_age_s)
            monitor = monitors[case]
            record = monitor.feed(packet)
            journal.append(record)
            log.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
            log.flush()
            last_received = time.monotonic()
    final = {record["resultado"]["id_caso"]: record["resultado"] for record in journal}
    if final:
        salvar_resultados(list(final.values()), output)
    from .dashboard import render_dashboard

    atomic_write(output / "painel.html", render_dashboard(store.list_alerts(), interactive=False))
    summary = {
        "pacotes_processados": len(journal),
        "casos": len(monitors),
        "alertas_caixa": len(store.list_alerts()),
        "modo": "tail_jsonl" if follow else "arquivo_jsonl_incremental",
        "limite_eventos": max_events,
        "timeout_ociosidade_s": idle_timeout,
        "escopo": "processamento_incremental_local_sem_sensores_nem_inferencia_modelos",
        "latencias_ms": [record["latencia_processamento_local_ms"] for record in journal],
        "todos_sinteticos": all(record["resultado"]["simulado"] for record in journal),
    }
    atomic_write(
        output / "monitoramento_resumo.json", json.dumps(summary, ensure_ascii=False, indent=2)
    )
    atomic_write(
        output / "entrega_auditoria.json",
        json.dumps(store.audit_log(), ensure_ascii=False, indent=2),
    )
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input")
    parser.add_argument("--output", default="integracao/evidencias/monitoramento_incremental")
    parser.add_argument("--demo", action="store_true", help="Gerar 32 pacotes sintéticos, sem API")
    parser.add_argument("--follow", action="store_true")
    parser.add_argument("--idle-timeout", type=float, default=5)
    parser.add_argument("--max-events", type=int, default=1000)
    parser.add_argument("--speed", type=float, default=0)
    parser.add_argument(
        "--max-source-age",
        type=float,
        default=60,
        help="Prazo operacional sem amostra nova; não é limiar clínico",
    )
    args = parser.parse_args(argv)
    source = args.input
    if args.demo:
        source = Path(args.output) / "entrada_sintetica.jsonl"
        atomic_write(
            source,
            "".join(json.dumps(packet, ensure_ascii=False) + "\n" for packet in example_packets()),
        )
    if not source:
        parser.error("Informe --input ou --demo.")
    print(
        json.dumps(
            run_stream(
                source,
                args.output,
                follow=args.follow,
                idle_timeout=args.idle_timeout,
                max_events=args.max_events,
                speed=args.speed,
                max_source_age_s=args.max_source_age,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
