"""Classify one WAV with the regenerated frozen model and actual local Whisper."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from audio_reproduce import ROOT, COLUMNS, acoustic_features, sha256


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
    text = asr.transcribe(signal, language="pt", fp16=device == "cuda", verbose=None,
                          temperature=0, condition_on_previous_text=False)["text"].strip()
    if not text:
        raise ValueError("No recognized speech; acoustic class inconclusive")
    features["ritmo_palavras_minuto"] = len(text.split()) / (features["duracao"] / 60)
    model = bundle["modelo"]
    probabilities = model.predict_proba(pd.DataFrame([features], columns=COLUMNS))[0]
    best = int(np.argmax(probabilities))
    return {"classe_audio": str(model.classes_[best]), "confianca_audio": float(probabilities[best]),
            "transcricao_whisper": text, "caracteristicas": features,
            "probabilidades": {str(label): float(p) for label, p in zip(model.classes_, probabilities)},
            "arquivo": path.name, "sha256_wav": sha256(path), "sha256_modelo": expected,
            "transcritor": "whisper-tiny-local", "device": device,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "latencia_s": time.perf_counter() - started,
            "ressalva": "Classificador de características de fala sintética; não é diagnóstico."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--model", type=Path, default=ROOT / "artifacts/audio/modelo_audio_1180.joblib")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/audio/resultado_audio_wav.json")
    args = parser.parse_args()
    result = infer_audio(args.input, args.model)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "classe_audio": result["classe_audio"],
                      "confianca_audio": result["confianca_audio"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
