"""Verifica a abstenção visual, preservando o falso alerta externo inicial.

Congela também um novo intervalo temporal antes da sua primeira inferência.
É a mesma fonte/paciente do vídeo didático, não outro paciente independente.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "video"))
from techchallenge4.media import sha256
from techchallenge4.reports import atomic_write
from alerta_video import analisar_video
from video_verificar_externo import clip


def main():
    import torch
    from ultralytics import YOLO

    torch.set_num_threads(4)
    private = ROOT / "dados_privados/video_externo_tvasurg"
    source = private / "fonte_tvasurg.mp4"
    original = json.loads(
        (ROOT / "evidence/video_externo_protocolo.json").read_text(encoding="utf-8")
    )
    original_result = json.loads(
        (ROOT / "evidence/video_verificacao_externa.json").read_text(encoding="utf-8")
    )
    reference_path = ROOT / "artifacts/video/referencia_visual.json"
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    model_manifest = json.loads(
        (ROOT / "artifacts/video/manifesto_video.json").read_text(encoding="utf-8")
    )
    weights = ROOT / model_manifest["path"]
    if (
        sha256(source) != original_result["source_sha256"]
        or sha256(weights) != reference["model_sha256"]
        or reference["model_sha256"] != model_manifest["sha256"]
    ):
        raise ValueError("Fonte, modelo ou referência alterados.")
    protocol = {
        "source_page": original["source_page"],
        "source_sha256": sha256(source),
        "model_sha256": sha256(weights),
        "reference_sha256": sha256(reference_path),
        "parameters": original["parameters"],
        "observed_interval_s": [150.0, 240.0],
        "new_temporal_interval_s": [240.0, 330.0],
        "new_interval_never_used_to_fit_or_select": True,
        "same_source_not_independent_patient": True,
        "post_hoc_change": "Filtro motivado por falso alerta em ilustração no intervalo inicial. Referência calculada só em treino e limite só na validação.",
        "clinical_ground_truth": False,
    }
    path = ROOT / "evidence/video_cobertura_protocolo.json"
    if path.exists():
        previous = json.loads(path.read_text(encoding="utf-8"))
        if any(previous.get(k) != v for k, v in protocol.items()):
            raise ValueError("Protocolo já congelado; não alterar silenciosamente.")
        protocol = previous
    else:
        protocol["frozen_at_utc"] = datetime.now(timezone.utc).isoformat()
        atomic_write(path, json.dumps(protocol, ensure_ascii=False, indent=2))
    model = YOLO(str(weights))
    if torch.cuda.is_available():
        model.to("cuda:0")
    cases = []
    for label, start, end in [("filtrado", 150.0, 240.0), ("reserva_temporal", 240.0, 330.0)]:
        media = private / f"trecho_{int(start)}_{int(end)}s.mp4"
        if not media.exists():
            clip(source, media, start, end)
        limits = [
            "Não há referência independente de eventos clínicos para calcular acurácia.",
            "Vídeo didático editado; mesma fonte da verificação inicial, sem independência por paciente.",
            "Filtro estatístico de aparência não identifica anatomia nem garante que a cena seja apropriada.",
        ]
        result = analisar_video(
            media,
            weights,
            saida=private / label,
            modelo=model,
            referencia_visual=reference,
            cobertura_parcial=True,
            limitacoes=limits,
            **protocol["parameters"],
        )
        public = {
            k: v for k, v in result.items() if k not in {"video", "video_anotado", "relatorio"}
        }
        public["eventos"] = [
            {k: v for k, v in e.items() if k != "quadro"} for e in result["eventos"]
        ]
        public.update(
            {
                "origem": "YOLO congelado com abstenção visual — TVASurg",
                "simulado": False,
                "source_page": protocol["source_page"],
                "interval_source_s": [start, end],
                "sha256_video": sha256(media),
                "model_sha256": sha256(weights),
                "reference_sha256": sha256(reference_path),
            }
        )
        atomic_write(
            ROOT / f"evidence/resultado_video_externo_{label}.json",
            json.dumps(public, ensure_ascii=False, indent=2),
        )
        cases.append(
            {
                "case": label,
                "interval_source_s": [start, end],
                "event_count": len(result["eventos"]),
                "stats": result["estatisticas"],
                "clinical_metrics": None,
            }
        )
        print(json.dumps(cases[-1], ensure_ascii=False), flush=True)
    evidence = {
        "protocol_sha256": sha256(path),
        "reference_sha256": sha256(reference_path),
        "original_false_alert_preserved": "evidence/resultado_video_externo.json",
        "original_false_alert_context": "Revisão visual identifica uma ilustração com campos cirúrgicos, não um instrumento endoscópico, no alerta inicial.",
        "reference_fit_external_frames": False,
        "cases": cases,
        "paid_api_calls": 0,
        "clinical_accuracy_claimed": False,
        "media_redistributed_publicly": False,
        "model_weights_unchanged": sha256(weights) == model_manifest["sha256"],
    }
    atomic_write(
        ROOT / "evidence/video_cobertura_externa.json",
        json.dumps(evidence, ensure_ascii=False, indent=2),
    )


if __name__ == "__main__":
    main()
