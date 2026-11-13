"""Verificação qualitativa em fonte clínica externa, excluída do desenvolvimento.

Não há rótulos temporais clínicos; o script não calcula acurácia nem inventa
eventos esperados. O vídeo didático editado continua privado e atribuído à fonte.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "video"))
from techchallenge4.media import sha256
from techchallenge4.reports import atomic_write
from alerta_video import analisar_video

PAGE = "https://pie.med.utoronto.ca/TVASurg/project/gyn-tlh/"
MEDIA = "https://pie.med.utoronto.ca/tvasurg/TVASurg_content/assets/masterFolders/GYN_totallaphyst/video/HD/video.mp4"
START, END = 150.0, 240.0


def download(destination):
    temporary = destination.with_suffix(".download")
    try:
        total = 0
        with urllib.request.urlopen(MEDIA, timeout=30) as response, temporary.open("wb") as target:
            if response.status != 200 or "video/" not in response.headers.get("Content-Type", ""):
                raise ValueError("Resposta não é vídeo público.")
            expected = int(response.headers["Content-Length"])
            if expected > 200_000_000:
                raise ValueError("Download maior que o limite de 200 MB.")
            while block := response.read(1_048_576):
                total += len(block)
                if total > expected:
                    raise ValueError("Resposta excedeu o tamanho declarado.")
                target.write(block)
        if total != expected:
            raise ValueError("Download incompleto.")
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def clip(source, destination, start=START, end=END):
    import cv2

    cap, writer = cv2.VideoCapture(str(source)), None
    try:
        if not cap.isOpened():
            raise ValueError("Vídeo não decodificável.")
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0 or not 0 <= start < end or cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps < end:
            raise ValueError("Vídeo não cobre o intervalo pré-definido.")
        frame_count = 0
        # Mesmo intervalo, em tempo original; não repete imagens para criar duração.
        current = round(start * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, current)
        expected_count = int((end - start) * 5)
        while frame_count < expected_count:
            ok, frame = cap.read()
            if not ok:
                raise ValueError("Falha na leitura do trecho externo.")
            target_frame = round((start + frame_count / 5) * fps)
            if current < target_frame:
                current += 1
                continue
            if writer is None:
                h, w = frame.shape[:2]
                writer = cv2.VideoWriter(
                    str(destination), cv2.VideoWriter_fourcc(*"mp4v"), 5, (w, h)
                )
                if not writer.isOpened():
                    raise ValueError("Codec indisponível.")
            writer.write(frame)
            frame_count += 1
            current += 1
        return frame_count
    finally:
        cap.release()
        if writer is not None:
            writer.release()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baixar",
        action="store_true",
        help="Baixa a fonte pública oficial se ausente (até 200 MB).",
    )
    args = parser.parse_args()
    import torch
    from ultralytics import YOLO

    torch.set_num_threads(4)
    manifest = json.loads(
        (ROOT / "artifacts/video/manifesto_video.json").read_text(encoding="utf-8")
    )
    weights = ROOT / manifest["path"]
    if sha256(weights) != manifest["sha256"]:
        raise ValueError("Peso diferente do congelado.")
    private = ROOT / "dados_privados/video_externo_tvasurg"
    private.mkdir(parents=True, exist_ok=True)
    protocol = {
        "source_page": PAGE,
        "source_media": MEDIA,
        "source": "TVASurg — University of Toronto, Total Laparoscopic Hysterectomy (2020)",
        "interval_source_s": [START, END],
        "interval_selected_by": "Capítulo público Entry & exposure, antes de executar o detector nesta fonte.",
        "model_sha256": manifest["sha256"],
        "parameters": {
            "conf": 0.4,
            "conf_area": 0.6,
            "min_perda_s": 5,
            "tolerancia_s": 1,
            "imgsz": 416,
        },
        "used_for_training": False,
        "used_for_validation": False,
        "used_for_threshold_selection": False,
        "clinical_ground_truth": False,
        "source_is_edited_educational_video": True,
        "rights": "Todos os direitos reservados pela fonte. Uso acadêmico privado; não incluir mídia/imagens no Git, no relatório público ou na apresentação sem autorização.",
        "claim": "Nova fonte nesta avaliação do ajuste local; não se audita todo o pré-treino do modelo base.",
    }
    protocol_path = ROOT / "evidence/video_externo_protocolo.json"
    if protocol_path.exists():
        previous = json.loads(protocol_path.read_text(encoding="utf-8"))
        if any(previous.get(k) != v for k, v in protocol.items()):
            raise ValueError("O protocolo externo já existe e não pode mudar silenciosamente.")
        protocol = previous
    else:
        protocol["frozen_at_utc"] = datetime.now(timezone.utc).isoformat()
        atomic_write(protocol_path, json.dumps(protocol, ensure_ascii=False, indent=2))
    source, selected_clip = private / "fonte_tvasurg.mp4", private / "trecho_150_240s.mp4"
    if not source.exists():
        if not args.baixar:
            raise FileNotFoundError(
                "Fonte ausente; use --baixar para obter a mídia pública oficial."
            )
        download(source)
    count = clip(source, selected_clip)
    print(json.dumps({"download_bytes": source.stat().st_size, "clip_frames": count}), flush=True)
    model = YOLO(str(weights))
    if torch.cuda.is_available():
        model.to("cuda:0")
    limits = [
        "Fonte externa sem anotações médicas/temporais para medir acertos e erros.",
        "Vídeo didático editado, não registro integral e contínuo de cirurgia.",
        "Modelo treinado em outra origem; ausência de alerta não confirma normalidade.",
    ]
    result = analisar_video(
        selected_clip,
        weights,
        saida=private / "resultado",
        modelo=model,
        cobertura_parcial=True,
        limitacoes=limits,
        **protocol["parameters"],
    )
    sanitized = {
        k: v for k, v in result.items() if k not in {"video", "video_anotado", "relatorio"}
    }
    sanitized["eventos"] = [
        {k: v for k, v in e.items() if k != "quadro"} for e in result["eventos"]
    ]
    sanitized.update(
        {
            "origem": "YOLO congelado — verificação qualitativa TVASurg",
            "simulado": False,
            "source_page": PAGE,
            "source_sha256": sha256(source),
            "sha256_video": sha256(selected_clip),
            "model_sha256": manifest["sha256"],
        }
    )
    atomic_write(
        ROOT / "evidence/resultado_video_externo.json",
        json.dumps(sanitized, ensure_ascii=False, indent=2),
    )
    evidence = {
        "protocol_sha256": sha256(protocol_path),
        "model_sha256": manifest["sha256"],
        "source_sha256": sha256(source),
        "clip_sha256": sha256(selected_clip),
        "source_bytes": source.stat().st_size,
        "clip_frames": count,
        "clip_duration_s": END - START,
        "events_predicted": len(result["eventos"]),
        "event_metrics": None,
        "reason_metrics_unavailable": "Não há referência independente de eventos nem ausência anatômica confirmada.",
        "paid_api_calls": 0,
        "new_training": False,
        "training_weights_unchanged": sha256(weights) == manifest["sha256"],
        "qualitative_only": True,
        "public_media_redistributed": False,
    }
    atomic_write(
        ROOT / "evidence/video_verificacao_externa.json",
        json.dumps(evidence, ensure_ascii=False, indent=2),
    )
    print(json.dumps(evidence, ensure_ascii=False))


if __name__ == "__main__":
    main()
