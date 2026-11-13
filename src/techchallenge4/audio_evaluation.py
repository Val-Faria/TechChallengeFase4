"""Avaliação do classificador de áudio publicado, sem extração ou novo ajuste.

As dependências de ciência de dados são opcionais para o restante do projeto.
O modelo só é carregado depois de conferir seus arquivos com o manifesto.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def avaliar_modelo_congelado(root):
    """Recalcula as métricas das partições existentes sem modificar os artefatos.

    Retorna métricas e matrizes de confusão para exibição no notebook. Esta
    reexecução usa a reserva já avaliada; não constitui uma nova avaliação cega.
    """
    import joblib
    import pandas as pd
    from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

    root = Path(root).resolve()
    manifest = json.loads(
        (root / "artifacts/audio/manifesto_audio.json").read_text(encoding="utf-8")
    )
    paths = {}
    for name in ("model", "features", "partitions"):
        path = (root / manifest[name]["path"]).resolve()
        if not path.is_relative_to(root):
            raise ValueError("Artefato de áudio fora da pasta do projeto.")
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest != manifest[name]["sha256"]:
            raise ValueError(f"Hash divergente no artefato: {name}.")
        paths[name] = path

    # Joblib usa pickle: carregar somente o modelo conhecido e verificado acima.
    bundle = joblib.load(paths["model"])
    if bundle["metadata"]["fit_partitions"] != ["train"]:
        raise ValueError("O modelo não respeita o protocolo de treino publicado.")
    frame = pd.read_csv(paths["features"])
    model, columns = bundle["modelo"], bundle["colunas"]
    labels = [str(value) for value in model.classes_]
    results = {}
    for partition in ("validation", "test", "blind_holdout"):
        selected = frame.loc[frame["particao"] == partition]
        if selected.empty:
            raise ValueError(f"Partição ausente: {partition}.")
        predicted = model.predict(selected[columns])
        results[partition] = {
            "n": len(selected),
            "accuracy": float(accuracy_score(selected["classe"], predicted)),
            "macro_f1": float(f1_score(selected["classe"], predicted, average="macro")),
            "confusion_matrix": confusion_matrix(
                selected["classe"], predicted, labels=labels
            ).tolist(),
            "labels": labels,
        }
    return {
        "model_sha256": manifest["model"]["sha256"],
        "fit_performed": False,
        "samples": len(frame),
        "metrics": results,
    }
