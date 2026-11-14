from unittest.mock import patch
import pytest

from techchallenge4.consulta_web import Processing
from techchallenge4.dashboard import render_dashboard


def test_reenvio_de_formulario_nao_inicia_segunda_consulta(tmp_path):
    from techchallenge4.delivery import AlertStore

    session = Processing(AlertStore(tmp_path / "alertas.sqlite3"))
    form = {
        "audio": ["novo-03.wav"],
        "video": ["montagem_test.mp4"],
        "chave": ["sk-" + "exemplo-local"],
        "token": [session.token],
    }
    with (
        patch("techchallenge4.consulta_web.missing_files", return_value=[]),
        patch("techchallenge4.consulta_web.Thread") as worker,
    ):
        session.start(form)
        with pytest.raises(ValueError):
            session.start(form)
        session.running = False
        with pytest.raises(ValueError):
            session.start(form)
        assert worker.call_count == 1
        assert form["chave"][0] not in repr(session.view())


def test_midia_fora_do_acervo_rejeitada_antes_de_processar():
    session = Processing(None)
    with pytest.raises(ValueError):
        session.start(
            {
                "audio": ["../fora.wav"],
                "video": ["montagem_test.mp4"],
                "chave": ["sk-exemplo-local"],
            }
        )
    assert not session.running


def test_exportacao_estatica_nao_solicita_credencial():
    assert 'name="chave"' not in render_dashboard([], interactive=False)
