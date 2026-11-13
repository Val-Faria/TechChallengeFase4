"""Valida mídia da equipe e vídeos técnicos inéditos, sem simular avaliação YOLO."""

from pathlib import Path
import hashlib
import json
import sys
import zipfile

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "video"))
from alerta_video import analisar_video, detectar_eventos


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DetectorMarcadores:
    """Oráculo determinístico por marcadores. Não é YOLO nem reconhece anatomia."""

    names = {0: "Tools", 1: "Uterus"}

    def predict(self, frame, **kwargs):
        ids = []
        if frame[45:75, 35:65, 0].mean() > 150:
            ids.append(0)
        if frame[45:75, 185:215, 1].mean() > 150:
            ids.append(1)
        boxes = type("Boxes", (), {"cls": np.array(ids), "conf": np.array([0.99] * len(ids))})()
        result = type("Resultado", (), {"boxes": boxes, "plot": lambda self: frame.copy()})()
        return [result]


def main():
    private = ROOT / "dados_privados" / "video_inedito"
    private.mkdir(parents=True, exist_ok=True)
    scenarios = [("normal", 8, True, "nenhum"), ("alerta", 18, False, "alto")]
    checks = []
    for name, duration, uterus, expected in scenarios:
        video = private / f"inedito_{name}.mp4"
        writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"mp4v"), 10, (320, 180))
        if not writer.isOpened():
            raise RuntimeError("Codec de vídeo indisponível")
        try:
            for i in range(duration * 10):
                frame = np.zeros((180, 320, 3), np.uint8)
                cv2.rectangle(frame, (25, 35), (75, 85), (255, 0, 0), -1)
                if uterus:
                    cv2.circle(frame, (200, 60), 35, (0, 255, 0), -1)
                cv2.putText(
                    frame,
                    f"SINTETICO {i / 10:.1f}s",
                    (15, 145),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    1,
                )
                writer.write(frame)
        finally:
            writer.release()
        result = analisar_video(video, None, saida=private / name, modelo=DetectorMarcadores())
        assert result["nivel"] == expected, result
        checks.append(
            {
                "nome": name,
                "sha256": sha(video),
                "duracao_s": duration,
                "nivel_esperado": expected,
                "nivel_obtido": result["nivel"],
                "eventos": result["eventos"],
                "aprovado": True,
            }
        )
    with zipfile.ZipFile(ROOT.parent / "saida_video.zip") as archive:
        rows = [
            json.loads(row)
            for row in archive.read("saida_video/antigos/quadros_video_teste_montagem.jsonl")
            .decode()
            .splitlines()
        ]
    frames = [(r["t"], r["instrumento"], r["area_critica"], r["conf_instrumento"]) for r in rows]
    events = detectar_eventos(frames, 0.2, duracao_video=114)
    assert [(e["inicio_s"], e["fim_s"]) for e in events] == [(76.0, 82.0), (84.0, 114.0)]
    received = json.loads(
        (ROOT / "dados_privados/video/resultado_video_test.json").read_text(encoding="utf-8")
    )
    cap = cv2.VideoCapture(str(ROOT / "dados_privados/video/video_test_anotado.mp4"))
    count = 0
    fps = cap.get(cv2.CAP_PROP_FPS)
    try:
        while True:
            ok, _ = cap.read()
            if not ok:
                break
            count += 1
    finally:
        cap.release()
    assert count == 570, count
    evidence = {
        "status": "validacao_de_software_concluida",
        "detector_yolo_reexecutado": False,
        "motivo": "Pesos best_uterus_tools_v4.pt não disponibilizados nos arquivos nem no Drive acessível.",
        "video_clinico_independente_avaliado": False,
        "novos_videos": {
            "origem": "Gerados localmente por este script; sem imagens clínicas",
            "detector": "Oráculo de marcadores coloridos, sem treinamento",
            "escopo": "Decodificação, amostragem, regra temporal, exportação e fechamento de recursos; não mede desempenho YOLO",
            "casos": checks,
        },
        "artefato_equipe": {
            "quadros_decodificados": count,
            "fps": fps,
            "duracao_s": count / fps,
            "sha256": sha(ROOT / "dados_privados/video/video_test_anotado.mp4"),
            "eventos_recalculados": events,
            "nivel_recebido": received["nivel"],
            "origem": "Montagem do conjunto já usado pela frente de vídeo; não é amostra inédita",
        },
        "ressalva": "Nenhuma métrica clínica ou de generalização do detector foi obtida nesta validação.",
    }
    for c in checks:
        for e in c["eventos"]:
            e.pop("quadro", None)
    out = ROOT / "evidence/video_validacao.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "casos_ineditos_tecnicos": len(checks),
                "eventos_recalculados": len(events),
                "quadros_decodificados": count,
            }
        )
    )


if __name__ == "__main__":
    main()
