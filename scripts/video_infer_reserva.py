"""Inferência YOLO real em montagens novas, incluindo origem reservada inteira.

A referência é presença de classes anotadas + regra temporal, não anotação
clínica de complicações. Nenhum limiar é escolhido pela reserva.
"""
from __future__ import annotations
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"src"))
sys.path.insert(0, str(ROOT/"video"))
from techchallenge4.media import sha256
from techchallenge4.reports import atomic_write
from alerta_video import analisar_video, detectar_eventos


def temporal_metrics(expected, predicted):
    candidates = []
    for i,a in enumerate(expected):
        for j,b in enumerate(predicted):
            intersection = max(0., min(a["fim_s"],b["fim_s"])-max(a["inicio_s"],b["inicio_s"]))
            union = max(a["fim_s"],b["fim_s"])-min(a["inicio_s"],b["inicio_s"])
            iou = intersection/union if union else 0.
            if iou >= .5:candidates.append((iou,i,j))
    used_a, used_b = set(), set()
    for _,i,j in sorted(candidates, reverse=True):
        if i not in used_a and j not in used_b:
            used_a.add(i);used_b.add(j)
    tp,fp,fn = len(used_a),len(predicted)-len(used_b),len(expected)-len(used_a)
    return {"tp":tp,"fp":fp,"fn":fn,"precision":tp/(tp+fp) if tp+fp else None,
            "recall":tp/(tp+fn) if tp+fn else None,"iou_min":.5,
            "scope":"eventos derivados de caixas em montagem; não complicações clínicas"}


def make_montage(rows, destination, dataset):
    import cv2
    import numpy as np
    rows = sorted(rows,key=lambda r:(r["quadro_origem"],r["arquivo"]))
    destination.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(destination),cv2.VideoWriter_fourcc(*"mp4v"),5,(416,416))
    if not writer.isOpened():raise RuntimeError("Codec indisponível.")
    truth, source_hashes = [], []
    try:
        for row in rows:
            path=dataset/row["particao"]/"images"/row["arquivo"]
            if sha256(path)!=row["sha256_imagem"]:raise ValueError("Quadro-fonte alterado.")
            frame=cv2.imdecode(np.frombuffer(path.read_bytes(), dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is None:raise ValueError("Quadro não decodificável.")
            frame=cv2.resize(frame,(416,416))
            label=dataset/row["particao"]/"labels"/(Path(row["arquivo"]).stem+".txt")
            classes={int(line.split()[0]) for line in label.read_text().splitlines() if line.strip()}
            for _ in range(10):
                t=len(truth)/5
                truth.append((t,0 in classes,1 in classes,1. if 0 in classes else 0.))
                writer.write(frame)
            source_hashes.append(row["sha256_imagem"])
    finally:writer.release()
    return detectar_eventos(truth,.2,duracao_video=len(truth)/5),source_hashes


def public_result(result, partition, model_sha, video_sha):
    sanitized={k:v for k,v in result.items() if k not in {"video","video_anotado","relatorio"}}
    sanitized["eventos"]=[{k:v for k,v in e.items() if k!="quadro"} for e in result["eventos"]]
    label="clipe reservado" if partition=="blind_holdout" else "teste de desenvolvimento"
    sanitized.update({"origem":f"YOLOv8s novo; peso congelado; {label}; inferência reexecutada",
                      "natureza":f"Montagem de {label}; não cirurgia contínua externa.",
                      "particao":partition,"simulado":True,"modelo_sha256":model_sha,
                      "sha256_video":video_sha,
                      "cobertura_parcial":True,
                      "limitacoes":["Montagem com dois segundos por imagem; não duração original de evento.",
                                    "Ausência de anotação não confirma ausência anatômica.",
                                    "Resultados do prefixo reservado já conhecidos; novas análises são posteriores à avaliação original."]})
    return sanitized


def main():
    from ultralytics import YOLO
    audit=json.loads((ROOT/"evidence/video_dataset_auditoria.json").read_text(encoding="utf-8"))
    model_manifest=json.loads((ROOT/"artifacts/video/manifesto_video.json").read_text(encoding="utf-8"))
    weights=ROOT/model_manifest["path"]
    if sha256(weights)!=model_manifest["sha256"]:raise ValueError("Peso diferente do congelado.")
    model=YOLO(str(weights))
    reference_path=ROOT/"artifacts/video/referencia_visual.json"
    reference=json.loads(reference_path.read_text(encoding="utf-8")) if reference_path.exists() else None
    if reference is not None and reference["model_sha256"]!=model_manifest["sha256"]:
        raise ValueError("Referência visual incompatível com o modelo.")
    dataset=ROOT/"dados_privados/video_dataset_v4"
    private=ROOT/"dados_privados/video_novo"
    output={"model_sha256":model_manifest["sha256"],"model_original_marcelo":False,
            "thresholds_frozen":{"conf":.4,"conf_area":.6,"min_perda_s":5.,"tolerancia_s":1.},
            "thresholds_tuned_on_blind":False,"montages":[],
            "visual_reference_sha256":sha256(reference_path) if reference is not None else None,
            "evaluation_phase":"Reexecução após diagnóstico; referência visual de treino/validação. A reserva original já foi observada.",
            "annotation_absence_confirmed_anatomical_absence":False}
    for partition in ["test","blind_holdout"]:
        rows=[r for r in audit["records"] if r["particao"]==partition]
        path=private/f"montagem_{partition}.mp4"
        expected,hashes=make_montage(rows,path,dataset)
        if partition=="blind_holdout":
            development={r["sha256_imagem"] for r in audit["records"] if r["particao"]!="blind_holdout"}
            assert not set(hashes)&development
            assert all(r["clipe"]==audit["blind_source_clip"] for r in rows)
        started=time.perf_counter()
        result=analisar_video(path,weights,saida=private/partition,modelo=model,
            cobertura_parcial=True,referencia_visual=reference,limitacoes=["Montagem temporal artificial.",
                "Referência derivada de caixas, sem confirmação de ausência anatômica ou falha clínica."])
        summary={"partition":partition,"source_images":len(rows),"duration_s":len(rows)*2,
                 "sha256_video":sha256(path),"sha256_sources":hashes,
                 "predicted_events":len(result["eventos"]),"expected_events":expected,
                 "event_metrics":temporal_metrics(expected,result["eventos"]),
                 "processing_wall_s":time.perf_counter()-started,
                 "construction":"Dois segundos por quadro de fonte; não cirurgia contínua.",
                 "source_clips":sorted({r["clipe"] for r in rows})}
        output["montages"].append(summary)
        if partition=="blind_holdout":
            output["blind_montage"]=summary
        sanitized=public_result(result,partition,model_manifest["sha256"],summary["sha256_video"])
        name="resultado_video_novo.json" if partition=="blind_holdout" else "resultado_video_teste.json"
        atomic_write(ROOT/"evidence"/name,json.dumps(sanitized,ensure_ascii=False,indent=2))
    atomic_write(ROOT/"evidence/video_inferencia_nova.json",json.dumps(output,ensure_ascii=False,indent=2))
    print(json.dumps({"concluido":True,"montagens":[{"particao":m["partition"],"eventos":m["predicted_events"],"referencia":len(m["expected_events"])} for m in output["montages"]]}))


if __name__=="__main__":main()
