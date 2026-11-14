"""Extração acústica e inferência com o classificador treinado no corpus de voz."""

from datetime import datetime, timezone
import json
from pathlib import Path
import time
from .media import sha256

COLUMNS = [
    "duracao",
    "energia_media",
    "proporcao_pausas",
    "ritmo_palavras_minuto",
    "tom_medio_hz",
    "tom_desvio_hz",
]


def acoustic_features(path: Path):
    import librosa
    import numpy as np

    signal, sr = librosa.load(str(path), sr=16000, mono=True)
    if len(signal) < 2048 or not np.isfinite(signal).all():
        raise ValueError(f"Invalid or too-short WAV: {path.name}")
    duration = len(signal) / sr
    if float(np.max(np.abs(signal))) < 1e-5:
        raise ValueError(f"Silent WAV: {path.name}")
    intervals = librosa.effects.split(signal, top_db=30)
    voiced_time = sum((end - start) / sr for start, end in intervals)
    f0, _, _ = librosa.pyin(signal, fmin=70, fmax=500, sr=sr)
    valid_f0 = f0[~np.isnan(f0)]
    return {
        "duracao": float(duration),
        "energia_media": float(np.mean(librosa.feature.rms(y=signal)[0])),
        "proporcao_pausas": max(duration - voiced_time, 0.0) / duration,
        "tom_medio_hz": float(np.mean(valid_f0)) if len(valid_f0) else 0.0,
        "tom_desvio_hz": float(np.std(valid_f0)) if len(valid_f0) else 0.0,
    }, signal


def infer_audio(path: Path, model_path: Path):
    import joblib
    import numpy as np
    import pandas as pd
    import torch
    import whisper

    started = time.perf_counter()
    torch.set_num_threads(2)
    artifact_manifest = model_path.parent / "manifesto_audio.json"
    if not artifact_manifest.exists():
        raise ValueError("Model manifest required; only load trusted project artifacts")
    expected = json.loads(artifact_manifest.read_text(encoding="utf-8"))["model"]["sha256"]
    if sha256(model_path) != expected:
        raise ValueError("Model SHA-256 differs from trusted artifact manifest")
    bundle = joblib.load(model_path)
    if bundle.get("colunas") != COLUMNS:
        raise ValueError("Unexpected model feature schema")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    features, signal = acoustic_features(path)
    asr = whisper.load_model("tiny", device=device)
    text = asr.transcribe(
        signal,
        language="pt",
        fp16=device == "cuda",
        verbose=None,
        temperature=0,
        condition_on_previous_text=False,
    )["text"].strip()
    if not text:
        raise ValueError("No recognized speech; acoustic class inconclusive")
    features["ritmo_palavras_minuto"] = len(text.split()) / (features["duracao"] / 60)
    model = bundle["modelo"]
    probabilities = model.predict_proba(pd.DataFrame([features], columns=COLUMNS))[0]
    best = int(np.argmax(probabilities))
    return {
        "classe_audio": str(model.classes_[best]),
        "confianca_audio": float(probabilities[best]),
        "transcricao_whisper": text,
        "caracteristicas": features,
        "probabilidades": {str(label): float(p) for label, p in zip(model.classes_, probabilities)},
        "arquivo": path.name,
        "sha256_wav": sha256(path),
        "sha256_modelo": expected,
        "transcritor": "whisper-tiny-local",
        "device": device,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "latencia_s": time.perf_counter() - started,
        "ressalva": "Classificador de características de fala sintética; não é diagnóstico.",
    }
