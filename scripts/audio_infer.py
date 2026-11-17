"""Classify one WAV with the regenerated frozen model and actual local Whisper."""

from __future__ import annotations
import argparse
from pathlib import Path
import json
from techchallenge4.audio import infer_audio

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument(
        "--model", type=Path, default=ROOT / "artifacts/audio/modelo_audio_1180.joblib"
    )
    parser.add_argument(
        "--output", type=Path, default=ROOT / "artifacts/audio/resultado_audio_wav.json"
    )
    args = parser.parse_args()
    result = infer_audio(args.input, args.model)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(args.output),
                "classe_audio": result["classe_audio"],
                "confianca_audio": result["confianca_audio"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
