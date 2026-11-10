"""Qualidade da entrada, referência congelada e persistência do sinal físico."""
from copy import deepcopy
import pytest
from techchallenge4.core import validar_fonte
from techchallenge4.media import MediaRules, MotionMonitor, assess_voice


def reference():
    return {"schema_version": 1, "speaker": "voz-demo", "referencia_congelada": True,
            "simulado": True, "proporcao_pausas": .25, "trecho_vocal_mediano_s": .5}


def features(**kwargs):
    return {"duracao_s": 5., "tempo_vocal_s": 2., "fracao_clipping": 0.,
            "proporcao_pausas": .6, "trecho_vocal_mediano_s": .2, **kwargs}


def test_voz_exige_dois_sinais_e_preserva_origem():
    result = assess_voice(features(), reference())
    assert validar_fonte(result)["alerta"] and result["simulado"]
    assert not assess_voice(features(proporcao_pausas=.3), reference())["alerta"]
    assert not assess_voice(features(trecho_vocal_mediano_s=.5), reference())["alerta"]


@pytest.mark.parametrize("change", [{"tempo_vocal_s": 0}, {"duracao_s": 2}, {"fracao_clipping": .1}])
def test_voz_qualidade_insuficiente_inconclusiva(change):
    result = assess_voice(features(**change), reference())
    assert result["status"] == "indisponivel" and result["alerta"] is None


def test_voz_rejeita_nan_e_referencia_nao_congelada():
    with pytest.raises(ValueError):
        assess_voice(features(proporcao_pausas=float("nan")), reference())
    ref = reference()
    ref["referencia_congelada"] = False
    with pytest.raises(ValueError):
        assess_voice(features(), ref)


def visual(value=.01, **kwargs):
    return {"movimento_relativo": value, "velocidade_camera": 0., "textura": 30., "brilho": 90., **kwargs}


def warm():
    monitor = MotionMonitor(warmup=20, simulated=True)
    for i in range(20):
        assert monitor.feed(visual(), i*.2)["status"] == "indisponivel"
    return monitor


def test_video_exige_persistencia_e_nao_incorpora_desvio_na_referencia():
    monitor = warm()
    frozen = deepcopy(monitor.history)
    assert not monitor.feed(visual(.2), 4.)["alerta"]
    for i in range(1, 6):
        result = monitor.feed(visual(.2), 4.+i*.2)
    assert validar_fonte(result)["alerta"] and monitor.history == frozen
    assert result["referencia"]["congelada"]


def test_video_lacuna_e_camera_nao_unem_evento():
    monitor = warm()
    monitor.feed(visual(.2), 4.)
    assert monitor.feed(visual(.2), 6.)["alerta"] is None
    assert not monitor.feed(visual(.2), 6.2)["alerta"]
    assert monitor.feed(visual(.2, velocidade_camera=.3), 6.4)["alerta"] is None
    assert not monitor.feed(visual(.2), 6.6)["alerta"]


def test_video_quadro_sem_textura_nao_e_amostra_normal():
    monitor = warm()
    result = monitor.feed(visual(textura=0), 4.)
    assert result["status"] == "indisponivel" and result["alerta"] is None
    with pytest.raises(ValueError):
        monitor.feed(visual(), 4.)


def test_regras_rejeitam_parametros_invalidos():
    with pytest.raises(ValueError):
        MediaRules(pause_increase=float("nan"))
    with pytest.raises(ValueError):
        MotionMonitor(warmup=2)
