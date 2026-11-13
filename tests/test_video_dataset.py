"""Anotações e identificação de origem antes de qualquer treino de vídeo."""

import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location(
    "video_reproduce", Path(__file__).resolve().parents[1] / "scripts/video_reproduce.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_poligono_e_caixa_mistos_preservam_duas_anotacoes():
    result, converted = module.normalize_label("0 .5 .5 .2 .4\n1 .1 .2 .3 .2 .3 .6 .1 .6")
    lines = [[float(x) for x in line.split()] for line in result.splitlines()]
    assert converted == 1 and len(lines) == 2
    assert lines[0] == [0, 0.5, 0.5, 0.2, 0.4]
    assert lines[1] == pytest.approx([1, 0.2, 0.4, 0.2, 0.4])


@pytest.mark.parametrize(
    "text",
    ["2 .5 .5 .2 .2", "0 nan .5 .2 .2", "0 1.1 .5 .2 .2", "0 .5 .5 0 .2", "1 .2 .3 .4 .5 .6"],
)
def test_anotacao_invalida_nao_vira_caixa(text):
    with pytest.raises(ValueError):
        module.normalize_label(text)


def test_origem_conserva_clipe_e_quadro_sem_sufixo_de_aumento():
    clip, frame, family = module.source_identity("2024-09-26-20-27-33_mp4-0047_jpg.rf.abcd.jpg")
    assert clip == module.HOLDOUT_CLIP and frame == 47
    assert family == "2024-09-26-20-27-33_mp4-0047_jpg"
    assert module.source_identity("UterusClip_mov-0001_jpg.rf.efgh.jpg")[0] == module.TRAIN_CLIP
