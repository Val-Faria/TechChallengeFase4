"""Congela compatibilidade visual em treino, com retenção escolhida na validação."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "video"))
from techchallenge4.media import sha256
from techchallenge4.reports import atomic_write
from qualidade import ajustar_referencia, compativel, extrair_caracteristicas, selecionar_limiar


def main():
    import cv2
    import numpy as np
    audit = json.loads((ROOT / "evidence/video_dataset_auditoria.json").read_text(encoding="utf-8"))
    model = json.loads((ROOT / "artifacts/video/manifesto_video.json").read_text(encoding="utf-8"))
    by_partition = {}
    for partition in ("train", "valid", "test", "blind_holdout"):
        rows = []
        for row in audit["records"]:
            if row["particao"] != partition:
                continue
            path = ROOT / "dados_privados/video_dataset_v4" / partition / "images" / row["arquivo"]
            if sha256(path) != row["sha256_imagem"]:
                raise ValueError("Imagem alterada.")
            frame = cv2.imdecode(np.frombuffer(path.read_bytes(), dtype=np.uint8), cv2.IMREAD_COLOR)
            rows.append(extrair_caracteristicas(frame))
        by_partition[partition] = rows
        if partition == "train":
            reference = ajustar_referencia(rows)
        if partition == "valid":
            threshold, candidates = selecionar_limiar(reference, rows)
    manifest = {"schema_version": "1.0", "model_sha256": model["sha256"],
                "dataset_zip_sha256": audit["zip_sha256"], "fit_partition": "train",
                "fit_images": len(by_partition["train"]), "threshold_partition": "valid",
                "threshold_images": len(by_partition["valid"]), "reference": reference,
                "threshold": threshold, "selection_policy": "Menor limite na grade 4/6/8/10 que retém ao menos 95% da validação.",
                "purpose": "Abstenção por aparência fora da referência; não reconhece se uma cena é clínica e não mede qualidade anatômica.",
                "post_hoc_external_failure_observed": True}
    target = ROOT / "artifacts/video/referencia_visual.json"
    atomic_write(target, json.dumps(manifest, ensure_ascii=False, indent=2))
    evidence = {"reference_sha256": sha256(target), "candidates_validation": candidates,
                "retention": {part: {"images": len(rows), "accepted": sum(compativel(r, reference, threshold)[0] for r in rows)}
                              for part, rows in by_partition.items()},
                "threshold": threshold, "used_external_frames_to_fit": False,
                "limitations": "Cores apenas; pode reter cenas inadequadas ou rejeitar cenas clínicas válidas. Cobertura parcial exige revisão, nunca significa normalidade."}
    atomic_write(ROOT / "evidence/video_referencia_visual.json", json.dumps(evidence, ensure_ascii=False, indent=2))
    print(json.dumps(evidence, ensure_ascii=False))


if __name__ == "__main__":
    main()
