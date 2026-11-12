"""Calibração de confiança em validação, sem dependências de visão ou GPU.

O alvo é concordância com classes anotadas, não ausência anatômica confirmada.
Os limites temporais continuam fixos e não são escolhidos pela montagem.
"""
from __future__ import annotations

import math

DEFAULTS = {"conf": 0.4, "conf_area": 0.6}
GRID_TOOLS = (0.2, 0.3, 0.4, 0.5, 0.6)
GRID_UTERUS = (0.4, 0.5, 0.6, 0.7, 0.8, 0.9)


def validar_registro(row):
    if row.get("partition") not in {"valid", "test", "blind_holdout"}:
        raise ValueError("Partição desconhecida.")
    for name in ("tools_annotated", "uterus_annotated"):
        if type(row.get(name)) is not bool:
            raise ValueError("Presença anotada deve ser booleana.")
    for name in ("tools_score", "uterus_score"):
        value = row.get(name)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError("Confiança precisa ser finita entre zero e um.")


def metricas_binarias(expected, predicted):
    if len(expected) != len(predicted) or not expected:
        raise ValueError("Referência e previsões devem ter o mesmo tamanho positivo.")
    if any(type(v) is not bool for v in [*expected, *predicted]):
        raise ValueError("Métricas exigem valores booleanos.")
    tp = sum(a and b for a, b in zip(expected, predicted))
    tn = sum(not a and not b for a, b in zip(expected, predicted))
    fp = sum(not a and b for a, b in zip(expected, predicted))
    fn = sum(a and not b for a, b in zip(expected, predicted))
    f1_pos = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.
    f1_neg = 2 * tn / (2 * tn + fp + fn) if 2 * tn + fp + fn else 0.
    return {"n": len(expected), "tp": tp, "tn": tn, "fp": fp, "fn": fn,
            "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None,
            "f1": f1_pos, "macro_f1": (f1_pos + f1_neg) / 2,
            "accuracy": (tp + tn) / len(expected)}


def avaliar_quadros(rows, conf, conf_area):
    for value in (conf, conf_area):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 < value <= 1:
            raise ValueError("Limiar precisa estar no intervalo (0, 1].")
    for row in rows:
        validar_registro(row)
    expected = [r["tools_annotated"] and not r["uterus_annotated"] for r in rows]
    predicted = [r["tools_score"] >= conf and r["uterus_score"] < conf_area for r in rows]
    return metricas_binarias(expected, predicted)


def selecionar_calibracao(rows):
    if not rows or any(r.get("partition") != "valid" for r in rows):
        raise ValueError("A seleção aceita exclusivamente quadros de validação.")
    for row in rows:
        validar_registro(row)
    targets = {r["tools_annotated"] and not r["uterus_annotated"] for r in rows}
    if targets != {True, False}:
        raise ValueError("A validação deve conter as duas condições anotadas.")
    candidates = []
    for conf in GRID_TOOLS:
        for conf_area in GRID_UTERUS:
            candidates.append({"conf": conf, "conf_area": conf_area,
                               "metrics": avaliar_quadros(rows, conf, conf_area)})
    # Empate: preservar a configuração mais próxima da original.
    def rank(candidate):
        distance = sum(abs(candidate[k] - DEFAULTS[k]) for k in DEFAULTS)
        return (candidate["metrics"]["macro_f1"], -round(distance, 8),
                -candidate["conf"], -candidate["conf_area"])
    best = max(candidates, key=rank)
    return {"selected": {k: best[k] for k in DEFAULTS},
            "baseline": avaliar_quadros(rows, **DEFAULTS),
            "selected_metrics": best["metrics"], "candidates": candidates,
            "objective": "macro_F1_da_condicao_por_quadro_anotado",
            "tie_break": "menor_distancia_aos_limites_originais",
            "selection_partition": "valid",
            "clinical_ground_truth": False}
