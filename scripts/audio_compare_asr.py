"""Compare real ASR outputs on six new synthetic recordings, with no new calls."""
from __future__ import annotations
from datetime import datetime, timezone
import json
from audio_reproduce import ROOT
from audio_external import tokens, edit_distance


def main():
    local = json.loads((ROOT / "evidence/audio_externo_transcricoes.json").read_text(encoding="utf-8"))
    cloud = json.loads((ROOT / "evidence/audio_openai_transcricoes.json").read_text(encoding="utf-8"))
    cloud_by_id = {row["id"]: row for row in cloud["casos"]}
    rows, word_count, local_errors, cloud_errors = [], 0, 0, 0
    for row in local["casos"]:
        remote = cloud_by_id[row["id"]]
        if row["sha256"] != remote["sha256_audio"]:
            raise ValueError("The ASR comparison must use the same WAV bytes")
        reference = tokens(row["texto_referencia"])
        if reference != tokens(remote["texto_referencia"]):
            raise ValueError("The ASR reference differs between sources")
        remote_text = remote.get("transcricao", remote.get("text", ""))
        n_local = edit_distance(reference, tokens(row["transcricao_whisper"]))
        n_cloud = edit_distance(reference, tokens(remote_text))
        word_count += len(reference)
        local_errors += n_local
        cloud_errors += n_cloud
        rows.append({"id": row["id"], "sha256_audio": row["sha256"],
                     "reference_words": len(reference), "texto_referencia": row["texto_referencia"],
                     "whisper_tiny": {"transcricao": row["transcricao_whisper"],
                                      "word_errors": n_local, "wer": n_local / len(reference)},
                     "openai_api": {"transcricao": remote_text,
                                    "word_errors": n_cloud, "wer": n_cloud / len(reference)}})
    output = {
        "schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
        "n": len(rows), "reference_words": word_count,
        "normalization": "Unicode NFC, casefold, Unicode word tokens; punctuation ignored; accents preserved.",
        "whisper_tiny": {"model": "tiny", "word_errors": local_errors,
                         "wer_global": local_errors / word_count, "used_for": "acoustic speech-rate feature"},
        "openai_api": {"model": cloud["modelo"], "word_errors": cloud_errors,
                       "wer_global": cloud_errors / word_count, "used_for": "textual analysis"},
        "sintetico": True, "corpus_inedito_para_classificador": True,
        "clinical_or_emotional_accuracy": None,
        "limitations": "Only six new synthetic utterances, two SAPI voices. WER evaluates transcription, not emotional classification or clinical detection. No tuning was performed on these samples.",
        "casos": rows,
    }
    target = ROOT / "evidence/asr_comparacao.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"n": len(rows), "word_count": word_count,
                      "wer_tiny": output["whisper_tiny"]["wer_global"],
                      "wer_api": output["openai_api"]["wer_global"]}))


if __name__ == "__main__":
    main()
