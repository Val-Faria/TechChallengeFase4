"""Isolamento da calibração e métricas independentes de pesos/GPU."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "calibracao", Path(__file__).parents[1] / "video/calibracao.py"
)
cal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cal)


def row(part="valid", tools=True, uterus=False, ts=0.8, us=0.5):
    return {
        "partition": part,
        "tools_annotated": tools,
        "uterus_annotated": uterus,
        "tools_score": ts,
        "uterus_score": us,
    }


@pytest.mark.parametrize("partition", ["test", "blind_holdout"])
def test_calibracao_recusa_dados_de_avaliacao(partition):
    with pytest.raises(ValueError, match="exclusivamente"):
        cal.selecionar_calibracao([row(), row(part=partition, uterus=True)])


def test_empate_preserva_limites_originais():
    selected = cal.selecionar_calibracao([row(us=0.1), row(uterus=True, us=0.99)])
    assert selected["selected"] == cal.DEFAULTS
    assert selected["selected_metrics"]["macro_f1"] == 1


def test_selecao_melhora_concordancia_sem_alterar_referencias():
    rows = [row(us=0.65), row(uterus=True, us=0.95)]
    result = cal.selecionar_calibracao(rows)
    assert result["selected"] == {"conf": 0.4, "conf_area": 0.7}
    assert result["selected_metrics"]["fn"] == 0
    assert rows[0]["uterus_score"] == 0.65
    assert result["clinical_ground_truth"] is False


def test_sem_previsao_positiva_precision_indefinida():
    m = cal.metricas_binarias([True, False], [False, False])
    assert m["precision"] is None
    assert m["recall"] == 0
    assert m["fn"] == 1 and m["tn"] == 1


@pytest.mark.parametrize("value", [float("nan"), -1.0, 2.0, True])
def test_rejeita_scores_invalidos(value):
    with pytest.raises(ValueError):
        cal.avaliar_quadros([row(ts=value)], 0.4, 0.6)


def test_validacao_sem_as_duas_condicoes_nao_calibra():
    with pytest.raises(ValueError, match="duas condições"):
        cal.selecionar_calibracao([row()])
