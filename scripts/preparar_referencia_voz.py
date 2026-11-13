"""Congela referência de ao menos dois WAVs anteriores da mesma voz."""

import argparse
import json
from pathlib import Path
from techchallenge4.media import fit_voice_reference
from techchallenge4.reports import atomic_write


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio", nargs="+", type=Path, required=True)
    parser.add_argument(
        "--speaker", required=True, help="Identificador local pseudonimizado da mesma voz."
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--simulated", action="store_true")
    args = parser.parse_args()
    result = fit_voice_reference(args.audio, speaker=args.speaker, simulated=args.simulated)
    atomic_write(args.output, json.dumps(result, ensure_ascii=False, indent=2))
    print("Referência congelada; não inclua nela as gravações reservadas para avaliação.")


if __name__ == "__main__":
    main()
