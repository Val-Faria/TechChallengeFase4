"""Audita Uterus v4, reserva um clipe inteiro e treina um NOVO YOLOv8s.

Não recupera os pesos originais da equipe. Polígonos são convertidos em caixas
envolventes, preservando a tarefa de detecção. A reserva não participa do ajuste
ou da escolha do checkpoint. As imagens ficam em dados_privados, fora do Git.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import io
import json
import math
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from techchallenge4.reports import atomic_write

HOLDOUT_CLIP = "2024-09-26-20-27-33_mp4"
TRAIN_CLIP = "UterusClip_mov"
SOURCE = "https://universe.roboflow.com/machinelearning-yekk6/uterus-qn1he/dataset/4"


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def normalize_label(text):
    """Convert supplied polygons; never infer missing clinical annotations."""
    rows, converted = [], 0
    for line in text.splitlines():
        if not line.strip():
            continue
        fields = [float(v) for v in line.split()]
        if not all(math.isfinite(v) for v in fields) or fields[0] not in (0., 1.):
            raise ValueError("Classe ou valor inválido na anotação.")
        coords = fields[1:]
        if any(v < -1e-6 or v > 1+1e-6 for v in coords):
            raise ValueError("Coordenada fora da imagem.")
        coords = [min(1., max(0., v)) for v in coords]
        if len(fields) == 5:
            cx, cy, width, height = coords
        elif len(fields) >= 7 and len(coords) % 2 == 0:
            xs, ys = coords[::2], coords[1::2]
            cx, cy = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2
            width, height = max(xs)-min(xs), max(ys)-min(ys)
            converted += 1
        else:
            raise ValueError("Formato de anotação não reconhecido.")
        if width <= 0 or height <= 0:
            raise ValueError("Caixa sem área.")
        rows.append(f"{int(fields[0])} {cx:.8f} {cy:.8f} {width:.8f} {height:.8f}")
    return "\n".join(rows)+("\n" if rows else ""), converted


def source_identity(name):
    stem = Path(name).stem.split(".rf.")[0]
    match = re.fullmatch(r"(.+?)[-_](\d+)(?:_jpg|_png|_jpeg)?", stem)
    if not match:
        raise ValueError("Origem do quadro não identificável pelo nome.")
    return match.group(1), int(match.group(2)), stem


def prepare(dataset_zip, destination):
    from PIL import Image
    import yaml
    destination.mkdir(parents=True, exist_ok=True)
    records, rejected, duplicates, paths = [], [], [], {}
    with zipfile.ZipFile(dataset_zip) as archive:
        bad_crc = archive.testzip()
        if bad_crc:
            raise ValueError("ZIP corrompido.")
        for entry in archive.infolist():
            part = PurePosixPath(entry.filename)
            if part.is_absolute() or ".." in part.parts or "\\" in entry.filename or ":" in entry.filename:
                raise ValueError("Caminho inseguro no ZIP.")
            if entry.file_size > 50_000_000:
                raise ValueError("Entrada excessiva no ZIP.")
            if entry.filename in paths:
                if archive.read(paths[entry.filename]) != archive.read(entry):
                    raise ValueError("Caminho duplicado com conteúdos diferentes.")
                duplicates.append(entry.filename)
            else:
                paths[entry.filename] = entry
        metadata = yaml.safe_load(archive.read(paths["data.yaml"]))
        if metadata.get("names") != ["Tools", "Uterus"]:
            raise ValueError("Classes diferentes de Tools/Uterus.")
        raw_counts, clip_counts = Counter(), defaultdict(Counter)
        for name, entry in sorted(paths.items()):
            if not re.fullmatch(r"(train|valid|test)/images/[^/]+\.(jpg|jpeg|png)", name, re.I):
                continue
            original_split = name.split("/")[0]
            clip, frame, family = source_identity(name)
            raw_counts[original_split] += 1
            clip_counts[clip][original_split] += 1
            if clip not in {HOLDOUT_CLIP, TRAIN_CLIP}:
                raise ValueError("Novo clipe encontrado: rever a reserva antes de treinar.")
            if clip == HOLDOUT_CLIP and original_split == "train":
                # Never use augmented copies of the held-out source, even in evaluation.
                continue
            partition = "blind_holdout" if clip == HOLDOUT_CLIP else original_split
            raw = archive.read(entry)
            label = name.replace("/images/", "/labels/").rsplit(".", 1)[0]+".txt"
            try:
                with Image.open(io.BytesIO(raw)) as image:
                    image.verify()
                normalized, converted = normalize_label(archive.read(paths[label]).decode("utf-8"))
            except (ValueError, OSError, KeyError) as error:
                rejected.append({"arquivo": name, "motivo": str(error)})
                continue
            records.append({"arquivo_zip": name, "arquivo": Path(name).name,
                "particao": partition, "particao_original": original_split, "clipe": clip,
                "quadro_origem": frame, "familia": family,
                "sha256_imagem": hashlib.sha256(raw).hexdigest(),
                "poligonos_convertidos": converted, "_raw": raw, "_label": normalized})
    # Prioritize reserved observations when a frame/content occurs in two partitions.
    priority = {"blind_holdout": 0, "test": 1, "valid": 2, "train": 3}
    family_partition, bytes_partition, accepted, purged = {}, {}, [], []
    for row in sorted(records, key=lambda r: (priority[r["particao"]], r["arquivo"])):
        key = (row["clipe"], row["familia"])
        conflicts = [family_partition.get(key), bytes_partition.get(row["sha256_imagem"])]
        if any(p is not None and p != row["particao"] for p in conflicts):
            purged.append({"arquivo": row["arquivo_zip"], "particao": row["particao"]})
            continue
        family_partition[key] = bytes_partition[row["sha256_imagem"]] = row["particao"]
        image_path = destination/row["particao"]/"images"/row["arquivo"]
        label_path = destination/row["particao"]/"labels"/(Path(row["arquivo"]).stem+".txt")
        image_path.parent.mkdir(parents=True, exist_ok=True)
        label_path.parent.mkdir(parents=True, exist_ok=True)
        if image_path.exists() and image_path.read_bytes() != row["_raw"]:
            raise ValueError("Destino contém mídia alterada.")
        image_path.write_bytes(row.pop("_raw"))
        label_path.write_text(row.pop("_label"), encoding="utf-8", newline="\n")
        accepted.append(row)
    counts = Counter(r["particao"] for r in accepted)
    if any(counts[partition] < 10 for partition in priority):
        raise ValueError("Partição insuficiente após a auditoria.")
    data = {"path": destination.resolve().as_posix(), "train": "train/images",
            "val": "valid/images", "test": "test/images", "names": {0: "Tools", 1: "Uterus"}}
    (destination/"data.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")
    data["test"] = "blind_holdout/images"
    (destination/"data_blind.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")
    audit = {"source": SOURCE, "zip_sha256": digest(dataset_zip), "zip_bytes": dataset_zip.stat().st_size,
        "counts_original": dict(raw_counts), "counts_by_clip": {k: dict(v) for k,v in clip_counts.items()},
        "counts_clean": dict(counts), "identical_duplicate_paths": duplicates,
        "rejected": rejected, "cross_partition_frames_purged": purged,
        "polygons_converted_to_boxes": sum(r["poligonos_convertidos"] for r in accepted),
        "blind_source_clip": HOLDOUT_CLIP,
        "protocol": "Clip timestamp entirely withheld. Its 420 augmented training variants are unused; only original valid/test frames form blind verification. Other clip retains supplied train/valid/test, with duplicate-frame/content purging.",
        "limitations": "Clip identity inferred from filename, not patient identity. Development validation/test can contain neighboring frames of the same clip. Blind montage is not an independent continuous surgery.",
        "records": accepted}
    atomic_write(ROOT/"evidence/video_dataset_auditoria.json", json.dumps(audit, ensure_ascii=False, indent=2))
    return audit


def evaluate(model, data, split, name, output):
    result = model.val(data=str(data), split=split, imgsz=416, batch=8, device=0,
                       workers=2, plots=True, project=str(output), name=name, exist_ok=True)
    return {"map50": float(result.box.map50), "map50_95": float(result.box.map),
            "precision": float(result.box.mp), "recall": float(result.box.mr),
            "per_class_map50": {model.names[i]:float(value) for i,value in enumerate(result.box.ap50)},
            "speed_ms": result.speed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-zip", type=Path, required=True)
    parser.add_argument("--audit-only", action="store_true")
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--batch", type=int, default=8)
    args = parser.parse_args()
    destination = ROOT/"dados_privados/video_dataset_v4"
    audit = prepare(args.dataset_zip, destination)
    print(json.dumps({"dataset": audit["counts_clean"], "polygons_to_boxes": audit["polygons_converted_to_boxes"],
                      "rejected": len(audit["rejected"])}, ensure_ascii=False), flush=True)
    if args.audit_only:
        return
    import torch
    from ultralytics import YOLO
    torch.set_num_threads(4)
    if not torch.cuda.is_available():
        raise RuntimeError("GPU CUDA necessária para esta reprodução; nada foi treinado.")
    output = ROOT/"dados_privados/video_runs"
    model_path = ROOT/"artifacts/video/best_uterus_tools_nirton_v4.pt"
    if model_path.exists():
        raise FileExistsError("Modelo congelado já existe. Não retreinar sobre a reserva revelada.")
    model_path.parent.mkdir(parents=True, exist_ok=True)
    config = {"model":"yolov8s.pt", "epochs":args.epochs, "batch":args.batch, "imgsz":416,
              "patience":20, "seed":42, "device":0, "workers":2, "deterministic":True}
    started = time.perf_counter()
    model = YOLO("yolov8s.pt")
    model.train(data=str(destination/"data.yaml"), **{k:v for k,v in config.items() if k!="model"},
                project=str(output), name="treino_novo_v4", exist_ok=False, plots=True)
    completed_epochs = int(model.trainer.epoch+1)
    best = Path(model.trainer.best)
    shutil.copyfile(best, model_path)
    frozen_hash = digest(model_path)
    model = YOLO(str(model_path))
    result = {"generated_at": datetime.now(timezone.utc).isoformat(), "dataset": {k:v for k,v in audit.items() if k!="records"},
              "training": {"config":config, "elapsed_s":time.perf_counter()-started,
                           "gpu":torch.cuda.get_device_name(0), "epochs_completed":completed_epochs},
              "versions": {p:importlib.metadata.version(p) for p in ["ultralytics","torch","torchvision","numpy"]},
              "model": {"path":model_path.relative_to(ROOT).as_posix(), "sha256":frozen_hash,
                        "trained_partitions":["train"], "selected_by":"validation_only", "original_team_weights":False},
              "evaluation":{}}
    for split in ["val", "test"]:
        result["evaluation"][split] = evaluate(model, destination/"data.yaml", split, f"avaliacao_{split}", output)
        atomic_write(ROOT/"evidence/video_reproducao.json", json.dumps(result, ensure_ascii=False, indent=2))
    # The checkpoint is frozen before any evaluation of the reserved source clip.
    assert digest(model_path)==frozen_hash
    result["evaluation"]["blind_holdout"] = evaluate(model, destination/"data_blind.yaml", "test", "verificacao_cega", output)
    atomic_write(ROOT/"evidence/video_reproducao.json", json.dumps(result, ensure_ascii=False, indent=2))
    atomic_write(model_path.parent/"manifesto_video.json", json.dumps(result["model"], ensure_ascii=False, indent=2))
    print(json.dumps({"concluido":True,"modelo_sha256":frozen_hash,"evaluation":result["evaluation"]}), flush=True)


if __name__ == "__main__":
    main()
