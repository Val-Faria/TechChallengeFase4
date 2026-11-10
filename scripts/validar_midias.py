"""Cenários físicos controlados: bytes PCM e pixels passam pelos detectores reais.

Não injeta classes, caixas ou decisões no detector. Não mede acurácia clínica.
As regras são as constantes públicas de media.py, sem seleção por resultado.
"""
from __future__ import annotations
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import wave

import cv2
import numpy as np

from techchallenge4.media import (MediaRules, MotionMonitor, assess_voice, fit_voice_reference,
                                 motion_features, read_wav, sha256, voice_features)
from techchallenge4.media_stream import run_media
from techchallenge4.reports import atomic_write

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / "dados_privados/midias_complementares"


def write_wav(path, signal, sr):
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(sr)
        out.writeframes((np.clip(signal, -1, .999)*32768).astype("<i2").tobytes())


def make_video(path, changed, seed):
    rng = np.random.default_rng(seed)
    background = rng.integers(30, 65, (180, 320, 3), dtype=np.uint8)
    texture = rng.integers(80, 245, (80, 100, 3), dtype=np.uint8)
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 20, (320, 180))
    if not writer.isOpened():
        raise RuntimeError("Codec indisponível.")
    try:
        for i in range(20*18):
            t = i/20
            if changed and 9 <= t < 16:
                x = int(105+65*np.sin(2*np.pi*.7*(t-9)))
            else:
                x = int(105+1.5*np.sin(2*np.pi*.25*t))
            frame = background.copy()
            frame[50:130, x:x+100] = texture
            writer.write(frame)
    finally:
        writer.release()


def evaluate_video(path, simulated):
    cap = cv2.VideoCapture(str(path))
    monitor = MotionMonitor(simulated=simulated)
    n, previous, last_t, count, positives, inconclusive = 0, None, None, 0, 0, 0
    try:
        if not cap.isOpened():
            raise ValueError("Vídeo inacessível.")
        fps = cap.get(cv2.CAP_PROP_FPS)
        step = max(1, round(fps/5))
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            index = n
            n += 1
            if index % step:
                continue
            t = index/fps
            if previous is not None:
                result = monitor.feed(motion_features(previous, frame, t-last_t), t)
                positives += int(result.get("alerta") is True)
                inconclusive += int(result["status"] != "ok")
                count += 1
            previous, last_t = frame, t
    finally:
        cap.release()
    return {"arquivo": path.name, "sha256": sha256(path), "quadros_decodificados": n,
            "pares_analisados": count, "quadros_com_alerta": positives,
            "quadros_inconclusivos": inconclusive, "eventos": monitor.events,
            "referencia": {"amostras": len(monitor.history), "mediana": monitor.center,
                           "escala": monitor.scale, "congelada_antes_do_trecho_avaliado": True}}


def main():
    PRIVATE.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((PRIVATE / "manifesto_sintese.json").read_text(encoding="utf-8-sig"))
    for case in manifest["casos"]:
        if sha256(PRIVATE/case["arquivo"]) != case["sha256"]:
            raise ValueError("Síntese alterada.")
    # Verify against the classifier's entire corpus and all earlier external WAVs.
    import csv
    with (ROOT/"audio/evidencias/particoes_audio.csv").open(encoding="utf-8", newline="") as stream:
        old_hashes = {row["sha256_wav"] for row in csv.DictReader(stream)}
    old_hashes |= {sha256(p) for p in (ROOT/"dados_privados/audio_inedito").glob("*.wav")}
    if old_hashes & {c["sha256"] for c in manifest["casos"]}:
        raise ValueError("Nova mídia duplicada de conjunto anterior.")
    acoustic = []
    for speaker in ["daniel", "maria"]:
        refs = [PRIVATE/f"{speaker}-ref{i}.wav" for i in [1, 2]]
        reference = fit_voice_reference(refs, speaker=speaker, simulated=True)
        atomic_write(PRIVATE/f"referencia_{speaker}.json", json.dumps(reference, indent=2))
        test = PRIVATE/f"{speaker}-prova.wav"
        signal, sr = read_wav(test)
        # Predetermined physical perturbation; not a recording of a sick person.
        blocks = [signal[i:i+int(.18*sr)] for i in range(0, len(signal), int(.18*sr))]
        interrupted = np.concatenate([np.concatenate([block, np.zeros(int(.38*sr))]) for block in blocks])
        variants = [("original", signal, False), ("ganho_reduzido", signal*.35, False),
                    ("interrompido", interrupted, True), ("silencio", np.zeros_like(signal), None)]
        for name, samples, expected in variants:
            path = test if name == "original" else PRIVATE/f"{speaker}-{name}.wav"
            if name != "original":
                write_wav(path, samples, sr)
            actual, actual_sr = read_wav(path)
            result = assess_voice(voice_features(actual, actual_sr), reference, simulated=True)
            acoustic.append({"voz": speaker, "cenario": name, "sha256": sha256(path),
                "fonte_derivada": name != "original", "sha256_fonte": sha256(test),
                "esperado": expected, "obtido": result["alerta"],
                "aprovado": result["alerta"] == expected, "resultado": result})
    visual = []
    for name, changed, seed in [("controle", False, 1001), ("movimento", True, 2027)]:
        path = PRIVATE/f"movimento_{name}.mp4"
        make_video(path, changed, seed)
        result = evaluate_video(path, True)
        result.update({"cenario": name, "esperado": changed,
                       "aprovado": bool(result["eventos"]) == changed,
                       "origem": "Cena geométrica inédita; sem paciente; pixels reais, sem oráculo de detecção."})
        visual.append(result)
    clinical = evaluate_video(ROOT/"dados_privados/video/video_test_anotado.mp4", False)
    clinical.update({"origem": "Vídeo cirúrgico anotado recebido da equipe, já usado anteriormente.",
                     "inedito": False, "rotulo_clinico_para_fluxo_optico": None,
                     "limitacao": "Sobreposições do detector original também afetam o movimento medido. Eventos inespecíficos não equivalem aos eventos anatômicos YOLO."})
    reference = json.loads((PRIVATE/"referencia_daniel.json").read_text())
    accelerated = run_media(PRIVATE/"movimento_movimento.mp4", PRIVATE/"daniel-interrompido.wav",
        reference, ROOT/"output/private/midias_acelerado", case_id="midias-acelerado", simulated=True)
    paced = run_media(PRIVATE/"movimento_movimento.mp4", PRIVATE/"daniel-interrompido.wav",
        reference, ROOT/"output/private/midias_tempo_original", case_id="midias-tempo-original",
        simulated=True, paced=True)
    evidence = {"instante_utc": datetime.now(timezone.utc).isoformat(), "regras": asdict(MediaRules()),
        "sha256_codigo_detector": sha256(ROOT/"src/techchallenge4/media.py"),
        "audio": {"novas_sinteses": 6, "referencias_por_voz": 2,
                  "provas_ineditas_por_voz": 1, "sobreposicao_sha256_corpus_ou_provas_anteriores": 0,
                  "casos": acoustic, "acuracia_clinica": None,
                  "escopo": "Regras de alterações acústicas intra-voz em cenário controlado; não identifica condição médica."},
        "video": {"casos_controlados": visual, "cirurgia_equipe": clinical,
                  "pesos_privados_necessarios": False, "detector_yolo_reexecutado": False,
                  "desempenho_clinico": None},
        "stream": {"acelerado": accelerated, "ritmo_original": paced},
        "chamadas_pagas": 0,
        "referencias": ["https://arxiv.org/abs/2011.09270", "https://docs.opencv.org/4.x/d4/dee/tutorial_optical_flow.html"],
        "limites": "Cenas de controle não são vídeos clínicos. Derivações compartilham fonte e não são amostras independentes. Não se mediu sensibilidade a doenças ou generalização clínica."}
    atomic_write(ROOT/"evidence/midias_complementares.json", json.dumps(evidence, ensure_ascii=False, indent=2, allow_nan=False))
    print(json.dumps({"audio": [(r["voz"], r["cenario"], r["aprovado"]) for r in acoustic],
                      "video": [(r["cenario"], r["aprovado"], len(r["eventos"])) for r in visual],
                      "cirurgia_eventos_observacionais": len(clinical["eventos"]),
                      "stream_p95_ms": paced["processamento_p95_ms"],
                      "tempo_parede_s": paced["tempo_total_parede_s"]}))
    if not all(r["aprovado"] for r in acoustic+visual):
        raise SystemExit("Há cenários divergentes; evidência preservada, regras não ajustadas.")


if __name__ == "__main__":
    main()
