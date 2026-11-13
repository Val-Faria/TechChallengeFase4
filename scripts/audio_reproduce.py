"""Reproduce audio features and reserve phrase-disjoint partitions before fitting.

Run from the repository with Python 3.12:
    python scripts/audio_reproduce.py --device auto
No paid service is used. The supplied synthetic corpus is not clinical data.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import time
import unicodedata
import zipfile

os.environ.setdefault("NUMBA_NUM_THREADS", "2")
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")
ROOT = Path(__file__).resolve().parents[1]
COLUMNS = [
    "duracao",
    "energia_media",
    "proporcao_pausas",
    "ritmo_palavras_minuto",
    "tom_medio_hz",
    "tom_desvio_hz",
]
PREFIX = re.compile(
    r"^(hum,?\s+|bem,?\s+|talvez\s+|eu acho que\s+|sim,?\s+|"
    r"certo,?\s+|agora,?\s+|neste momento,?\s+|eu sinto que\s+|"
    r"bom,?\s+|infelizmente,?\s+)",
    re.IGNORECASE,
)


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def phrase_family(text: str) -> str:
    """Remove only known synthesis prefixes, never symptom words or negation."""
    text = PREFIX.sub("", unicodedata.normalize("NFC", str(text).strip()), count=1)
    return re.sub(r"\s+", " ", text).strip().casefold()


def split_manifest(meta):
    """Deterministic assignment, independent of labels, audio features and scores."""
    families = sorted(
        meta["familia_frase"].unique(),
        key=lambda value: hashlib.sha256(("fiap-f4-audio-split-v1|" + value).encode()).hexdigest(),
    )
    if len(families) < 10:
        raise ValueError("At least 10 phrase families required for independent partitions")
    n_hold = max(2, round(len(families) * 0.10))
    n_test = max(2, round(len(families) * 0.15))
    n_val = max(2, round(len(families) * 0.15))
    assignment = {}
    boundaries = [("blind_holdout", n_hold), ("test", n_test), ("validation", n_val)]
    position = 0
    for partition, length in boundaries:
        for family in families[position : position + length]:
            assignment[family] = partition
        position += length
    for family in families[position:]:
        assignment[family] = "train"
    meta = meta.copy()
    meta["particao"] = meta["familia_frase"].map(assignment)
    # Every augmented variant of an original, including prefixes, stays together.
    if meta.groupby("arquivo_original")["particao"].nunique().max() != 1:
        raise ValueError("An original recording crossed partitions")
    return meta


def prepare_dataset(dataset: Path, destination: Path):
    import pandas as pd

    with zipfile.ZipFile(dataset) as archive:
        names = archive.namelist()
        metadata_names = [name for name in names if Path(name).name == "metadata.csv"]
        if len(metadata_names) != 1:
            raise ValueError("Exactly one metadata.csv is required")
        import io

        meta = pd.read_csv(io.BytesIO(archive.read(metadata_names[0])))
        wav_names = [name for name in names if name.lower().endswith(".wav")]
        wavs = {Path(name).name: name for name in wav_names}
        if len(wavs) != len(wav_names):
            raise ValueError("Duplicate WAV basenames inside archive")
        if len(wavs) != 1180 or len(meta) != 1180:
            raise ValueError(f"Expected 1180 WAVs and rows, got {len(wavs)} and {len(meta)}")
        if meta["arquivo"].duplicated().any():
            raise ValueError("Duplicate metadata filenames")
        destination.mkdir(parents=True, exist_ok=True)
        for filename in meta["arquivo"]:
            if Path(filename).name != filename or filename not in wavs:
                raise ValueError("Invalid metadata filename")
            out = destination / filename
            original_bytes = archive.read(wavs[filename])
            if out.exists() and sha256(out) != hashlib.sha256(original_bytes).hexdigest():
                raise ValueError(f"Extracted WAV differs from versioned archive: {filename}")
            if not out.exists():
                out.write_bytes(original_bytes)
        meta["sha256_wav"] = [sha256(destination / filename) for filename in meta["arquivo"]]
    meta["familia_frase"] = meta["texto"].map(phrase_family)
    meta = split_manifest(meta)
    # A byte-identical sample in another partition is also leakage.
    if meta.groupby("sha256_wav")["particao"].nunique().max() != 1:
        raise ValueError("Identical WAV bytes crossed partitions")
    return meta


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


def extract_features(meta, wav_dir: Path, cache_file: Path, *, device: str, workers: int):
    import numpy as np
    import pandas as pd
    import torch
    import whisper

    torch.set_num_threads(2)
    selected_device = "cuda" if device == "auto" and torch.cuda.is_available() else device
    if selected_device == "auto":
        selected_device = "cpu"
    cache = {}
    if cache_file.exists():
        with cache_file.open(encoding="utf-8") as stream:
            for line in stream:
                row = json.loads(line)
                cache[row["sha256_wav"]] = row
    remaining = [row for row in meta.to_dict("records") if row["sha256_wav"] not in cache]
    model = whisper.load_model("tiny", device=selected_device) if remaining else None
    print(
        json.dumps(
            {
                "device": selected_device,
                "cached": len(meta) - len(remaining),
                "remaining": len(remaining),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    started = time.monotonic()
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with (
        cache_file.open("a", encoding="utf-8") as log,
        ThreadPoolExecutor(max_workers=workers) as pool,
    ):
        # Small batches keep memory bounded; acoustic extraction uses at most two workers.
        for start in range(0, len(remaining), 8):
            batch = remaining[start : start + 8]
            futures = [pool.submit(acoustic_features, wav_dir / row["arquivo"]) for row in batch]
            for row, future in zip(batch, futures):
                acoustic, signal = future.result()
                output = model.transcribe(
                    signal,
                    language="pt",
                    fp16=selected_device == "cuda",
                    verbose=None,
                    temperature=0,
                    condition_on_previous_text=False,
                )
                text = output["text"].strip()
                if not text:
                    raise ValueError(f"Whisper returned empty text for {row['arquivo']}")
                acoustic["ritmo_palavras_minuto"] = len(text.split()) / (acoustic["duracao"] / 60)
                result = {
                    "arquivo": row["arquivo"],
                    "sha256_wav": row["sha256_wav"],
                    "transcricao_whisper": text,
                    **acoustic,
                }
                if not all(np.isfinite(result[column]) for column in COLUMNS):
                    raise ValueError("Non-finite feature")
                cache[row["sha256_wav"]] = result
                log.write(json.dumps(result, ensure_ascii=False) + "\n")
                log.flush()
            done = min(start + 8, len(remaining))
            print(
                json.dumps(
                    {
                        "processed": done,
                        "total_new": len(remaining),
                        "elapsed_s": round(time.monotonic() - started, 1),
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
    features = pd.DataFrame([cache[key] for key in meta["sha256_wav"]])
    merged = meta.merge(features.drop(columns="arquivo"), on="sha256_wav", validate="one_to_one")
    return merged, selected_device


def metrics(truth, prediction, labels):
    from sklearn.metrics import (
        accuracy_score,
        balanced_accuracy_score,
        classification_report,
        confusion_matrix,
        f1_score,
    )

    return {
        "n": len(truth),
        "accuracy": float(accuracy_score(truth, prediction)),
        "balanced_accuracy": float(balanced_accuracy_score(truth, prediction)),
        "macro_f1": float(f1_score(truth, prediction, average="macro", zero_division=0)),
        "labels": labels,
        "confusion_matrix": confusion_matrix(truth, prediction, labels=labels).tolist(),
        "classification_report": classification_report(
            truth, prediction, labels=labels, output_dict=True, zero_division=0
        ),
    }


def evaluate_and_save(features, dataset: Path, output: Path, evidence: Path, device: str):
    import joblib
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier

    output.mkdir(parents=True, exist_ok=True)
    evidence.parent.mkdir(parents=True, exist_ok=True)
    proof_dir = ROOT / "audio" / "evidencias"
    proof_dir.mkdir(parents=True, exist_ok=True)
    labels = sorted(features["classe"].unique())
    split_columns = [
        "arquivo",
        "arquivo_original",
        "texto",
        "familia_frase",
        "particao",
        "sha256_wav",
    ]
    split_file = proof_dir / "particoes_audio.csv"
    features[split_columns].to_csv(split_file, index=False, encoding="utf-8")
    # No hyperparameter tuning. Reserve partitions are never supplied to fit.
    mask = features["particao"] == "train"
    model = RandomForestClassifier(
        n_estimators=200, random_state=42, class_weight="balanced", n_jobs=2
    )
    started = time.monotonic()
    model.fit(features.loc[mask, COLUMNS], features.loc[mask, "classe"])
    training_s = time.monotonic() - started
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "file": dataset.name,
            "sha256": sha256(dataset),
            "wav_count": len(features),
            "original_recordings": int(features["arquivo_original"].nunique()),
            "phrase_families": int(features["familia_frase"].nunique()),
            "classes": {str(k): int(v) for k, v in features["classe"].value_counts().items()},
        },
        "versions": {
            package: importlib.metadata.version(package)
            for package in [
                "openai-whisper",
                "torch",
                "librosa",
                "scikit-learn",
                "pandas",
                "numpy",
                "soundfile",
            ]
        },
        "features": {
            "columns": COLUMNS,
            "transcriber": "openai-whisper tiny local",
            "language": "pt",
            "device": device,
            "sr": 16000,
            "metadata_text_used_as_transcription": False,
        },
        "model": {
            "class": "RandomForestClassifier",
            "n_estimators": 200,
            "class_weight": "balanced",
            "random_state": 42,
            "fit_partitions": ["train"],
            "hyperparameter_search": False,
            "refit_on_reserved_partitions": False,
            "training_s": training_s,
        },
        "partitions": {},
        "leakage": {
            "phrase_overlap": 0,
            "original_overlap": 0,
            "sha256_overlap": 0,
            "manifest_sha256": sha256(split_file),
        },
        "limitations": [
            "Synthetic single-voice corpus; no clinical generalization established.",
            "Blind holdout comes from the existing corpus and is unseen by this newly fitted model only.",
            "Historical model had seen the entire corpus and is not used in this evaluation.",
            "Validation and test are descriptive only; no model or threshold selected from their scores.",
        ],
    }
    records = []
    for partition in ["train", "validation", "test", "blind_holdout"]:
        selected = features[features["particao"] == partition]
        report["partitions"][partition] = {
            "wav_count": len(selected),
            "original_recordings": int(selected["arquivo_original"].nunique()),
            "phrase_families": sorted(selected["familia_frase"].unique().tolist()),
            "classes": {str(k): int(v) for k, v in selected["classe"].value_counts().items()},
        }
        # Blind set is scored exactly once, after fixed model and all partitions are persisted.
        predicted = model.predict(selected[COLUMNS])
        probabilities = model.predict_proba(selected[COLUMNS])
        report[partition] = metrics(selected["classe"], predicted, labels)
        for row, prediction, probability in zip(
            selected.to_dict("records"), predicted, probabilities
        ):
            records.append(
                {
                    "arquivo": row["arquivo"],
                    "particao": partition,
                    "classe_verdadeira": row["classe"],
                    "classe_audio": prediction,
                    "confianca_audio": float(max(probability)),
                    "sha256_wav": row["sha256_wav"],
                }
            )
    model_file = output / "modelo_audio_1180.joblib"
    joblib.dump(
        {
            "modelo": model,
            "colunas": COLUMNS,
            "metadata": {
                "dataset_sha256": report["dataset"]["sha256"],
                "fit_partitions": ["train"],
                "partition_manifest_sha256": report["leakage"]["manifest_sha256"],
                "feature_extractor": "whisper_tiny_librosa_v1",
                "created_at": report["generated_at"],
            },
        },
        model_file,
    )
    feature_file = output / "caracteristicas_audio_1180.csv"
    features.to_csv(feature_file, index=False, encoding="utf-8")
    predictions = pd.DataFrame(records)
    csv_file = output / "resultado_audio_1180.csv"
    predictions.to_csv(csv_file, index=False, encoding="utf-8")
    predictions.to_csv(proof_dir / "predicoes_avaliacao.csv", index=False, encoding="utf-8")
    report["artifacts"] = {
        key: {
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
        }
        for key, path in [
            ("model", model_file),
            ("features", feature_file),
            ("predictions", csv_file),
            ("partitions", split_file),
        ]
    }
    evidence.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "manifesto_audio.json").write_text(
        json.dumps(report["artifacts"], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                partition: report[partition]["accuracy"]
                for partition in ["validation", "test", "blind_holdout"]
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset", type=Path, default=ROOT / "audio/datasets/dataset_audio_emocoes_1180.zip"
    )
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--workers", type=int, choices=[1, 2], default=2)
    parser.add_argument("--audit-only", action="store_true")
    parser.add_argument(
        "--limit", type=int, help="Timing probe only; never writes evaluation artifacts"
    )
    args = parser.parse_args()
    extracted = ROOT / "audio/datasets/extracted"
    meta = prepare_dataset(args.dataset, extracted)
    print(meta.groupby(["particao", "classe"]).size().to_string(), flush=True)
    if args.audit_only:
        return
    selected = meta.head(args.limit) if args.limit else meta
    features, device = extract_features(
        selected,
        extracted,
        ROOT / "artifacts/audio/features_cache.jsonl",
        device=args.device,
        workers=args.workers,
    )
    if args.limit:
        return
    evaluate_and_save(
        features,
        args.dataset,
        ROOT / "artifacts/audio",
        ROOT / "evidence/audio_reproducao.json",
        device,
    )


if __name__ == "__main__":
    main()
