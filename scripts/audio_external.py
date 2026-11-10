"""One-shot software verification on newly synthesized, disjoint voices/sentences.

These samples have no validated emotional/clinical ground truth. Report ASR word
errors and classifier behavior, never emotional or clinical accuracy.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import time
import unicodedata

from audio_reproduce import ROOT, COLUMNS, acoustic_features, phrase_family, sha256


def tokens(text):
    return re.findall(r"\w+", unicodedata.normalize("NFC", text).casefold())


def edit_distance(reference, hypothesis):
    previous = list(range(len(hypothesis) + 1))
    for i, a in enumerate(reference, 1):
        current = [i]
        for j, b in enumerate(hypothesis, 1):
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (a != b)))
        previous = current
    return previous[-1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "dados_privados/audio_inedito")
    parser.add_argument("--model", type=Path, default=ROOT / "artifacts/audio/modelo_audio_1180.joblib")
    parser.add_argument("--asr-only", action="store_true", help="Extract only ASR/acoustics while the classifier is fitting")
    args = parser.parse_args()
    import joblib
    import numpy as np
    import pandas as pd
    import torch
    import whisper
    torch.set_num_threads(2)
    manifest = json.loads((args.input / "manifesto.json").read_text(encoding="utf-8-sig"))
    training_manifest = pd.read_csv(ROOT / "audio/evidencias/particoes_audio.csv")
    existing_hashes = set(training_manifest["sha256_wav"])
    existing_phrases = set(training_manifest["familia_frase"])
    model = None
    if not args.asr_only:
        model_manifest = args.model.parent / "manifesto_audio.json"
        expected = json.loads(model_manifest.read_text(encoding="utf-8"))["model"]["sha256"]
        if sha256(args.model) != expected:
            raise ValueError("Frozen model differs from artifact manifest; no pickle loaded")
        bundle = joblib.load(args.model)
        if bundle.get("metadata", {}).get("fit_partitions") != ["train"]:
            raise ValueError("Only the newly frozen train-only model can be used")
        model = bundle["modelo"]
    device = "cuda" if torch.cuda.is_available() else "cpu"
    cached_file = ROOT / "artifacts/audio/externo_features.json"
    cache = json.loads(cached_file.read_text(encoding="utf-8")) if cached_file.exists() else {}
    asr = whisper.load_model("tiny", device=device) if not cache else None
    records = []
    total_words = total_errors = 0
    for sample in manifest["casos"]:
        path = args.input / sample["arquivo"]
        digest = sha256(path)
        if digest != sample["sha256"] or digest in existing_hashes:
            raise ValueError("External WAV is modified or duplicated from the corpus")
        if phrase_family(sample["texto"]) in existing_phrases:
            raise ValueError("External source sentence duplicates a corpus family")
        started = time.perf_counter()
        if digest in cache:
            features = cache[digest]["caracteristicas"]
            transcription = cache[digest]["transcricao_whisper"]
        else:
            if asr is None:
                asr = whisper.load_model("tiny", device=device)
            features, signal = acoustic_features(path)
            transcription = asr.transcribe(signal, language="pt", fp16=device == "cuda",
                                            verbose=None, temperature=0, condition_on_previous_text=False)["text"].strip()
        if not transcription:
            raise ValueError("Empty external transcription")
        features["ritmo_palavras_minuto"] = len(transcription.split()) / (features["duracao"] / 60)
        cache[digest] = {"caracteristicas": features.copy(), "transcricao_whisper": transcription}
        probabilities = model.predict_proba(pd.DataFrame([features], columns=COLUMNS))[0] if model is not None else None
        best = int(np.argmax(probabilities)) if probabilities is not None else None
        n_words = len(tokens(sample["texto"]))
        n_errors = edit_distance(tokens(sample["texto"]), tokens(transcription))
        total_words += n_words
        total_errors += n_errors
        records.append({"id": sample["id"], "arquivo": sample["arquivo"], "sha256": digest,
                        "voz": sample["voz"], "texto_referencia": sample["texto"],
                        "transcricao_whisper": transcription, "caracteristicas": features,
                        "classe_audio": str(model.classes_[best]) if model is not None else None,
                        "confianca_audio": float(probabilities[best]) if probabilities is not None else None,
                        "probabilidades": {str(label): float(p) for label, p in zip(model.classes_, probabilities)} if model is not None else None,
                        "wer": n_errors / n_words, "word_errors": n_errors, "reference_words": n_words,
                        "latencia_s": time.perf_counter() - started,
                        "cenario_textual_planejado": sample["esperado"], "rotulo_emocional_validado": None})
        print(json.dumps({"id": sample["id"], "transcricao": transcription,
                          "classe": records[-1]["classe_audio"], "wer": records[-1]["wer"]}, ensure_ascii=False), flush=True)
    cached_file.parent.mkdir(parents=True, exist_ok=True)
    cached_file.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.asr_only:
        output = ROOT / "evidence/audio_externo_transcricoes.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({"schema_version": 1, "sintetico": True,
                                      "observacao": "ASR sem classificador; não é avaliação emocional.",
                                      "casos": records}, ensure_ascii=False, indent=2), encoding="utf-8")
        return
    report = {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
              "origem": manifest["origem"], "sintetico": True, "n": len(records),
              "model_sha256": sha256(args.model), "device": device,
              "novas_vozes": sorted(set(sample["voz"] for sample in records)),
              "treino": False, "validacao": False, "teste_desenvolvimento": False,
              "modelo_congelado_antes_da_avaliacao": True,
              "sobreposicao_sha256_dataset": 0, "sobreposicao_frase_base_dataset": 0,
              "wer_global": total_errors / total_words, "word_errors": total_errors,
              "reference_words": total_words,
              "acuracia_emocional": None,
              "ressalva": "Verificacao funcional externa sintetica, sem rotulos emocionais ou clinicos validados; WER mede apenas transcricao.",
              "casos": records}
    output = ROOT / "evidence/audio_externo.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    import csv
    csv_path = ROOT / "audio/evidencias/resultado_audio_externo.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        columns = ["arquivo", "classe_audio", "confianca_audio"]
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows({key: row[key] for key in columns} for row in records)


if __name__ == "__main__":
    main()
