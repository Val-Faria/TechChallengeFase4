"""Regressões da regra temporal, independentes de pesos e bibliotecas de GPU."""
import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('alerta_video', Path(__file__).parents[1] / 'video/alerta_video.py')
video = importlib.util.module_from_spec(spec)
spec.loader.exec_module(video)


def test_evento_no_fim_nao_extrapola_video():
    rows = [(i, True, False, .9) for i in range(6)]
    events = video.detectar_eventos(rows, 1, duracao_video=5.5)
    assert events[0]['fim_s'] == 5.5
    assert events[0]['duracao_s'] == 5.5


def test_lacuna_grande_nao_vira_evento_continuo():
    rows = [(0, True, False, .9), (20, True, False, .9)]
    assert video.detectar_eventos(rows, 1) == []


@pytest.mark.parametrize('rows', [[(1,True,False,.8),(1,True,False,.8)], [(float('nan'),True,False,.8)]])
def test_rejeita_tempo_invalido(rows):
    with pytest.raises(ValueError):
        video.detectar_eventos(rows, 1)


def test_tolerancia_curta_preserva_evento():
    rows = [(i/5, True, i == 10, .9) for i in range(30)]
    events = video.detectar_eventos(rows, .2, tolerancia_s=1)
    assert len(events) == 1
    assert events[0]['duracao_s'] == 6


def test_prioridade_e_intervalos():
    assert video.nivel_do_alerta([]) == 'nenhum'
    assert video.nivel_do_alerta([{'duracao_s': 15}]) == 'alto'
    with pytest.raises(ValueError):
        video.detectar_eventos([], -1)


@pytest.mark.parametrize("duration", [float("nan"), -1, True])
def test_rejeita_duracao_invalida(duration):
    with pytest.raises(ValueError):
        video.detectar_eventos([], .2, duracao_video=duration)


def test_presenca_como_texto_nao_cria_alerta_falso():
    with pytest.raises(ValueError, match="booleana"):
        video.detectar_eventos([(0, "false", False, .9)], .2)


def test_quadro_fora_da_duracao_nao_extrapola_evento():
    with pytest.raises(ValueError, match="fora"):
        video.detectar_eventos([(2, True, False, .9)], .2, duracao_video=1)


def test_quadro_fora_da_referencia_interrompe_evento_sem_tolerancia():
    rows = [(i, True, False, .9) for i in range(11)]
    events = video.detectar_eventos(rows, 1, quadros_invalidos=[5])
    assert [(e["inicio_s"], e["fim_s"]) for e in events] == [(0, 5), (6, 11)]
