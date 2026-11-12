"""Abstenção visual e seleção sem imagens externas."""
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("qualidade", Path(__file__).parents[1] / "video/qualidade.py")
quality = importlib.util.module_from_spec(spec)
spec.loader.exec_module(quality)


def sample(warm=.8, difference=.3):
    return {"warm_fraction": warm, "red_blue_difference": difference}


def test_referencia_constante_nao_divide_por_zero():
    ref = quality.ajustar_referencia([sample()] * 20)
    assert quality.compativel(sample(), ref, 4)[0]
    assert not quality.compativel(sample(.1, -.2), ref, 4)[0]


def test_limiar_preserva_retencao_minima():
    ref = quality.ajustar_referencia([sample()] * 20)
    selected, candidates = quality.selecionar_limiar(ref, [sample()] * 20)
    assert selected == 4
    assert candidates[0]["retention"] == 1


def test_validacao_incompativel_impede_ativacao():
    ref = quality.ajustar_referencia([sample()] * 20)
    with pytest.raises(ValueError, match="não ativar"):
        quality.selecionar_limiar(ref, [sample(.0, -.9)] * 20)


@pytest.mark.parametrize("value", [float("nan"), 2., True])
def test_caracteristica_invalida_nao_passa(value):
    with pytest.raises(ValueError):
        quality.ajustar_referencia([sample(value)] * 20)
