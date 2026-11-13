"""Inferência incremental de WAV e vídeo, fusão e entrega persistente.

Mídias de arquivo podem ser reproduzidas no ritmo original (--paced). Isto
mede execução local com entrada gravada, sem afirmar aquisição clínica ao vivo.
Nenhuma chamada paga é feita por este comando.
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
import time

from .core import fonte_indisponivel, fundir_fontes_normalizadas, numero_finito, validar_fonte
from .delivery import AlertStore
from .media import (
    MediaRules,
    MotionMonitor,
    assess_voice,
    motion_features,
    read_wav,
    sha256,
    voice_features,
)
from .reports import atomic_write


def run_media(
    video,
    audio,
    reference,
    output,
    *,
    case_id="midia-demo",
    paced=False,
    simulated=False,
    text_source=None,
    window_s=5.0,
    max_seconds=180.0,
    rules=MediaRules(),
):
    import cv2

    window_s = numero_finito(window_s, "window_s", rules.min_audio_seconds, 30)
    max_seconds = numero_finito(max_seconds, "max_seconds", 1, 600)
    if type(paced) is not bool or type(simulated) is not bool:
        raise ValueError("Modos precisam ser booleanos.")
    if text_source is not None:
        text_source = validar_fonte(text_source)
        if text_source["modalidade"] != "texto_openai":
            raise ValueError("Fonte textual incompatível.")
    # Validate case identifier before opening persistent storage.
    fundir_fontes_normalizadas([], id_caso=case_id, pareamento="demonstracao")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    signal, sr = read_wav(audio)
    if sha256(audio) in reference.get("sha256_referencias", []):
        raise ValueError("A mídia avaliada não pode ser gravação da referência.")
    store = AlertStore(output / "alertas.sqlite3")
    monitor = MotionMonitor(rules=rules, simulated=simulated)
    cap = cv2.VideoCapture(str(video))
    previous = None
    n, processed, next_audio = 0, 0, window_s
    latest_audio = fonte_indisponivel("audio", "Aguardando janela de áudio.", simulado=simulated)
    deliveries, audio_windows, records, times = [], [], [], []
    last_state = None
    journal = output / "eventos_midia.jsonl"
    try:
        if not cap.isOpened():
            raise ValueError("Vídeo não pode ser aberto.")
        fps = numero_finito(cap.get(cv2.CAP_PROP_FPS), "fps", 0.1, 240)
        step = max(1, round(fps / 5))
        last_t = None
        with journal.open("w", encoding="utf-8") as stream:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                t = n / fps
                n += 1
                if t > max_seconds:
                    break
                if (n - 1) % step:
                    continue
                if paced:
                    remaining = started + t - time.perf_counter()
                    if remaining > 0:
                        time.sleep(remaining)
                tick = time.perf_counter()
                if previous is None:
                    previous, last_t = frame, t
                    continue
                visual = monitor.feed(motion_features(previous, frame, t - last_t), t)
                previous, last_t = frame, t
                while t + 1e-8 >= next_audio and next_audio <= len(signal) / sr + 1e-8:
                    left, right = int((next_audio - window_s) * sr), int(next_audio * sr)
                    features = voice_features(signal[left:right], sr)
                    latest_audio = assess_voice(
                        features, reference, rules=rules, simulated=simulated
                    )
                    latest_audio["fim_janela_s"] = next_audio
                    audio_windows.append(latest_audio.copy())
                    next_audio += window_s
                sources = [latest_audio, visual]
                if t - latest_audio.get("fim_janela_s", 0) > window_s * 2:
                    sources[0] = fonte_indisponivel(
                        "audio", "Áudio sem janela recente.", simulado=simulated
                    )
                if text_source is not None:
                    # Explicitly a previously validated cloud result, not new live inference.
                    if t <= window_s * 2:
                        sources.append(
                            {
                                **text_source,
                                "origem_temporal": "resposta_nuvem_previa_associada_manualmente",
                            }
                        )
                    else:
                        sources.append(
                            fonte_indisponivel(
                                "texto_openai", "Resultado textual anterior expirado."
                            )
                        )
                result = fundir_fontes_normalizadas(
                    sources,
                    id_caso=case_id,
                    pareamento="midias_independentes_associadas_em_cenario_tecnico_sem_paciente_real",
                    fontes_esperadas=["audio", "video"]
                    + (["texto_openai"] if text_source is not None else []),
                )
                state = [
                    (f["modalidade"], f["status"], f["alerta"], f["nivel"])
                    for f in result["fontes"]
                ]
                # Persist transitions rather than sending five identical tasks per second.
                if result["alerta"] and state != last_state:
                    result["entrega"] = store.deliver(result)
                    deliveries.append(
                        {
                            "instante_midia_s": t,
                            "id_resultado": result["id_resultado"],
                            "fontes_positivas": [
                                f["modalidade"] for f in result["fontes"] if f.get("alerta")
                            ],
                        }
                    )
                last_state = state
                elapsed_ms = (time.perf_counter() - tick) * 1000
                times.append(elapsed_ms)
                record = {
                    "instante_midia_s": t,
                    "tempo_parede_s": time.perf_counter() - started,
                    "atraso_frente_relogio_midia_s": max(0.0, time.perf_counter() - started - t)
                    if paced
                    else None,
                    "processamento_ms": elapsed_ms,
                    "resultado": result,
                }
                stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
                stream.flush()
                records.append(record)
                processed += 1
        if not processed:
            raise ValueError("Vídeo sem pares de quadros analisáveis.")
    finally:
        cap.release()
    import statistics

    ordered = sorted(times)
    summary = {
        "schema_version": 1,
        "caso": case_id,
        "modo": "reproducao_no_ritmo_original" if paced else "arquivo_acelerado",
        "entrada": "quadros_e_amostras_PCM; sem_resultados_audio_video_precalculados",
        "aquisicao_clinica_ao_vivo": False,
        "simulado": simulated or reference["simulado"],
        "sha256_video": sha256(video),
        "sha256_audio": sha256(audio),
        "quadros_processados": processed,
        "duracao_processada_s": records[-1]["instante_midia_s"],
        "tempo_total_parede_s": time.perf_counter() - started,
        "processamento_mediano_ms": statistics.median(times),
        "processamento_p95_ms": ordered[min(len(ordered) - 1, int(0.95 * len(ordered)))],
        "escopo_latencia": "decodificacao_inicial_no_tempo_total; extracao_acustica_fluxo_optico_fusao_sqlite_por_passo; sem_ASR_nuvem",
        "janela_audio_s": window_s,
        "janelas_audio": audio_windows,
        "eventos_video": monitor.events,
        "alertas_entregues": deliveries,
        "regras": rules.__dict__,
        "inicializacao_referencia_visual_amostras": monitor.warmup,
        "chamadas_pagas": 0,
        "observacao": "Resultado de arquivo reproduzido. Latência por passo exclui espera da janela; câmera/microfone e modelos de nuvem não estão nesta medição.",
    }
    atomic_write(
        output / "resumo_midia.json",
        json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False),
    )
    lines = [
        "# Relatório automático de análise contínua",
        "",
        f"Modo: {summary['modo']}",
        f"Quadros: {processed}; janelas de voz: {len(audio_windows)}; alertas: {len(deliveries)}.",
        f"Processamento p95: {summary['processamento_p95_ms']:.2f} ms por passo.",
        "",
        "## Eventos de movimento",
    ]
    lines += [
        f"- {e['inicio_s']:.2f}–{e['fim_s']:.2f} s: {e['descricao']}" for e in monitor.events
    ] or ["Nenhum evento atingiu a regra."]
    lines += ["", "## Análise vocal"]
    lines += [f"- Até {a['fim_janela_s']:.2f} s: {a['motivo']}" for a in audio_windows]
    lines += [
        "",
        summary["observacao"],
        "",
        "Sinais observacionais para revisão humana; sem diagnóstico.",
    ]
    atomic_write(output / "relatorio_midia.md", "\n".join(lines))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case-id", default="midia-demo")
    parser.add_argument("--text-source", type=Path)
    parser.add_argument("--paced", action="store_true")
    parser.add_argument("--simulated", action="store_true")
    parser.add_argument("--max-seconds", type=float, default=180.0)
    args = parser.parse_args()
    reference = json.loads(args.reference.read_text(encoding="utf-8"))
    text = json.loads(args.text_source.read_text(encoding="utf-8")) if args.text_source else None
    result = run_media(
        args.video,
        args.audio,
        reference,
        args.output,
        case_id=args.case_id,
        paced=args.paced,
        simulated=args.simulated,
        text_source=text,
        max_seconds=args.max_seconds,
    )
    print(
        json.dumps(
            {
                k: result[k]
                for k in [
                    "modo",
                    "quadros_processados",
                    "tempo_total_parede_s",
                    "processamento_p95_ms",
                ]
            }
        )
    )


if __name__ == "__main__":
    main()
