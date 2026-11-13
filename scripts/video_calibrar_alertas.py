"""Audita divergências e calibra confiança usando somente as 74 imagens válidas.

O peso e as anotações originais são preservados. A reserva já observada é um
diagnóstico posterior, não nova avaliação cega. Não cria rótulos médicos.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "video"))
from techchallenge4.media import sha256
from techchallenge4.reports import atomic_write
from calibracao import DEFAULTS, avaliar_quadros, selecionar_calibracao


def collect(model, records, device):
    paths = [
        ROOT / "dados_privados/video_dataset_v4" / r["particao"] / "images" / r["arquivo"]
        for r in records
    ]
    for path, row in zip(paths, records):
        if sha256(path) != row["sha256_imagem"]:
            raise ValueError("Imagem diferente da auditada.")
    results = model.predict(
        source=[str(p) for p in paths],
        conf=0.01,
        imgsz=416,
        batch=8,
        device=device,
        verbose=False,
        stream=True,
    )
    output = []
    for row, path, prediction in zip(records, paths, results, strict=True):
        label = path.parent.parent / "labels" / (path.stem + ".txt")
        classes = {int(line.split()[0]) for line in label.read_text().splitlines() if line.strip()}
        boxes = [
            {"class": model.names[int(c)], "score": float(p), "xyxyn": [float(v) for v in xy]}
            for c, p, xy in zip(
                prediction.boxes.cls.tolist(),
                prediction.boxes.conf.tolist(),
                prediction.boxes.xyxyn.tolist(),
            )
        ]
        scores = {
            name: max((b["score"] for b in boxes if b["class"] == name), default=0.0)
            for name in ("Tools", "Uterus")
        }
        output.append(
            {
                "filename": row["arquivo"],
                "partition": row["particao"],
                "source_clip": row["clipe"],
                "frame": row["quadro_origem"],
                "image_sha256": row["sha256_imagem"],
                "label_sha256": sha256(label),
                "tools_annotated": 0 in classes,
                "uterus_annotated": 1 in classes,
                "tools_score": scores["Tools"],
                "uterus_score": scores["Uterus"],
                "boxes": boxes,
            }
        )
    return output


def main():
    import torch
    from ultralytics import YOLO

    torch.set_num_threads(4)
    device = 0 if torch.cuda.is_available() else "cpu"
    audit = json.loads((ROOT / "evidence/video_dataset_auditoria.json").read_text(encoding="utf-8"))
    manifest = json.loads(
        (ROOT / "artifacts/video/manifesto_video.json").read_text(encoding="utf-8")
    )
    weights = ROOT / manifest["path"]
    if sha256(weights) != manifest["sha256"]:
        raise ValueError("Peso diferente do congelado.")
    model = YOLO(str(weights))
    all_rows = []
    for partition in ("valid", "test", "blind_holdout"):
        records = sorted(
            (r for r in audit["records"] if r["particao"] == partition),
            key=lambda r: (r["quadro_origem"], r["arquivo"]),
        )
        rows = collect(model, records, device)
        if partition == "valid":
            selected = selecionar_calibracao(rows)
            config = {
                "schema_version": "1.0",
                "model_sha256": manifest["sha256"],
                "dataset_zip_sha256": audit["zip_sha256"],
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "selection_partition": "valid",
                "selection_images": len(rows),
                "selection_data_sha256": hashlib.sha256(
                    json.dumps(rows, sort_keys=True).encode()
                ).hexdigest(),
                "parameters": {
                    **selected["selected"],
                    "min_perda_s": 5.0,
                    "tolerancia_s": 1.0,
                    "imgsz": 416,
                },
                "objective": selected["objective"],
                "clinical_ground_truth": False,
                "post_hoc_study": True,
                "approved_for_default_inference": False,
                "promotion_policy": "Candidato experimental; a demonstração mantém 0,4/0,6. Melhora na validação não comprova generalização.",
                "note": "Nova versão após observar a reserva original; limites escolhidos somente em validação. Não é nova avaliação cega.",
            }
            atomic_write(
                ROOT / "artifacts/video/calibracao_alertas.json",
                json.dumps(config, ensure_ascii=False, indent=2),
            )
        all_rows.extend(rows)
        print(
            json.dumps({"partition": partition, "images": len(rows)}, ensure_ascii=False),
            flush=True,
        )
    metrics, divergences = {}, []
    for partition in ("valid", "test", "blind_holdout"):
        rows = [r for r in all_rows if r["partition"] == partition]
        metrics[partition] = {
            "baseline": avaliar_quadros(rows, **DEFAULTS),
            "calibrated": avaliar_quadros(rows, **selected["selected"]),
        }
        for row in rows:
            if not row["uterus_annotated"] and row["uterus_score"] >= 0.6:
                divergences.append({k: v for k, v in row.items() if k != "boxes"})
    evidence = {
        "model_sha256": manifest["sha256"],
        "calibration_sha256": sha256(ROOT / "artifacts/video/calibracao_alertas.json"),
        "selection": selected,
        "frame_metrics": metrics,
        "divergences": divergences,
        "records": all_rows,
        "interpretation": "Ausência de caixa anotada não confirma ausência anatômica. Divergência exige revisão do rótulo e da detecção; rótulos originais não foram alterados.",
        "external_blind_evaluation": False,
        "paid_api_calls": 0,
        "candidate_promoted": False,
        "training_performed": False,
        "weights_unchanged": sha256(weights) == manifest["sha256"],
    }
    atomic_write(
        ROOT / "evidence/video_calibracao.json", json.dumps(evidence, ensure_ascii=False, indent=2)
    )
    print(
        json.dumps(
            {
                "selected": selected["selected"],
                "frame_metrics": metrics,
                "divergences": len(divergences),
                "weights_unchanged": evidence["weights_unchanged"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
