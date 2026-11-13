"""Compatibilidade visual por mediana/MAD; não classifica anatomia ou doença.

Uma cena fora da referência interrompe a regra, sem virar resultado normal.
O critério utiliza a mesma família estatística dos monitores estruturados.
"""

from __future__ import annotations

import math
import statistics

FEATURES = ("warm_fraction", "red_blue_difference")
SCALE_FLOOR = 0.02
THRESHOLDS = (4.0, 6.0, 8.0, 10.0)


def extrair_caracteristicas(frame):
    """Resume a aparência por tons quentes e diferença vermelho-azul, sem classificar anatomia."""
    import cv2
    import numpy as np

    if (
        not isinstance(frame, np.ndarray)
        or frame.dtype != np.uint8
        or frame.ndim != 3
        or frame.shape[2] != 3
        or not frame.size
    ):
        raise ValueError("Esperado quadro BGR uint8 não vazio.")
    small = cv2.resize(frame, (64, 64), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    warm = (
        ((hsv[:, :, 0] <= 35) | (hsv[:, :, 0] >= 170)) & (hsv[:, :, 1] >= 50) & (hsv[:, :, 2] >= 25)
    )
    return {
        "warm_fraction": float(warm.mean()),
        "red_blue_difference": float((small[:, :, 2].astype(float) - small[:, :, 0]).mean() / 255),
    }


def validar_valores(row):
    if set(row) != set(FEATURES) or any(
        isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
        for v in row.values()
    ):
        raise ValueError("Características visuais inválidas.")
    if not 0 <= row["warm_fraction"] <= 1 or not -1 <= row["red_blue_difference"] <= 1:
        raise ValueError("Características fora dos limites físicos.")


def ajustar_referencia(rows):
    if len(rows) < 20:
        raise ValueError("Referência visual exige ao menos 20 imagens de treino.")
    for row in rows:
        validar_valores(row)
    reference = {}
    for name in FEATURES:
        values = [r[name] for r in rows]
        center = statistics.median(values)
        raw = 1.4826 * statistics.median(abs(v - center) for v in values)
        reference[name] = {"median": center, "scale": max(SCALE_FLOOR, raw), "raw_mad_scale": raw}
    return reference


def compativel(values, reference, threshold):
    """Verifica desvios em relação à referência visual e retorna os escores por característica."""
    validar_valores(values)
    if (
        isinstance(threshold, bool)
        or not isinstance(threshold, (int, float))
        or not math.isfinite(threshold)
        or threshold <= 0
    ):
        raise ValueError("Limiar visual deve ser finito e positivo.")
    scores = {}
    if set(reference) != set(FEATURES):
        raise ValueError("Referência visual incompleta.")
    for name in FEATURES:
        center, scale = reference[name]["median"], reference[name]["scale"]
        if (
            isinstance(center, bool)
            or isinstance(scale, bool)
            or not math.isfinite(center)
            or not math.isfinite(scale)
            or scale < SCALE_FLOOR
        ):
            raise ValueError("Referência visual inválida.")
        scores[name] = abs(values[name] - center) / scale
    return all(v <= threshold for v in scores.values()), scores


def selecionar_limiar(reference, validation_rows):
    if len(validation_rows) < 20:
        raise ValueError("Validação visual exige ao menos 20 imagens.")
    # Política declarada antes da verificação externa: reter ao menos 95% da validação.
    candidates = [
        {
            "threshold": threshold,
            "retention": sum(compativel(r, reference, threshold)[0] for r in validation_rows)
            / len(validation_rows),
        }
        for threshold in THRESHOLDS
    ]
    accepted = [r for r in candidates if r["retention"] >= 0.95]
    if not accepted:
        raise ValueError("Nenhum limiar retém 95% da validação; não ativar filtro automaticamente.")
    return min(accepted, key=lambda r: r["threshold"])["threshold"], candidates
