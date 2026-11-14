import json
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from techchallenge4.consulta_web import Processing
from techchallenge4.dashboard import create_server


@pytest.fixture
def panel(tmp_path):
    server = create_server(tmp_path / "alertas.sqlite3", port=0)
    worker = Thread(target=server.serve_forever)
    worker.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        worker.join()
        server.server_close()


def test_audio_reproduz_faixas_e_aceita_busca(panel):
    with urlopen(Request(panel + "/midia/audio/novo-03.wav", headers={"Range": "bytes=0-43"})) as r:
        assert r.status == 206 and r.read().startswith(b"RIFF")
        assert r.headers["Content-Range"].startswith("bytes 0-43/")
    with urlopen(
        Request(panel + "/midia/video/montagem_test.mp4", headers={"Range": "bytes=-32"})
    ) as r:
        assert r.status == 206 and len(r.read()) == 32
        assert r.headers["Content-Type"] == "video/webm"


def test_faixa_invalida_e_arquivo_fora_do_acervo(panel):
    for path, headers, status in [
        ("/midia/audio/novo-03.wav", {"Range": "bytes=9999999-"}, 416),
        ("/midia/audio/novo-03.wav", {"Range": "bytes=-0"}, 416),
        ("/midia/audio/../../.env", {}, 404),
    ]:
        with pytest.raises(HTTPError) as error:
            urlopen(Request(panel + path, headers=headers))
        assert error.value.code == status


def test_formulario_carrega_reprodutores_sem_credencial_persistida(panel):
    with urlopen(panel) as r:
        page = r.read().decode()
        assert "<audio" in page and "<video" in page
        assert "media-src 'self'" in r.headers["Content-Security-Policy"]
    with urlopen(panel + "/status") as r:
        state = json.load(r)
        assert not state["running"] and "chave" not in state
    with urlopen(panel + "/painel.js") as r:
        assert r.headers["Content-Type"] == "text/javascript"


def test_quadro_exibido_vem_do_callback_da_inferencia():
    cv2 = pytest.importorskip("cv2")
    np = pytest.importorskip("numpy")
    processing = Processing(None)
    processing.frame(np.zeros((32, 32, 3), dtype=np.uint8), 2.0, 10, 100)
    image = cv2.imdecode(np.frombuffer(processing.image, dtype=np.uint8), cv2.IMREAD_COLOR)
    assert image.shape == (32, 32, 3)
    assert processing.status()["video"] == {"seconds": 2.0, "processed": 10, "total": 100}
