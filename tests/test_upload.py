from io import BytesIO
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch
import wave

import pytest

from techchallenge4.consulta import ROOT
from techchallenge4.dashboard import create_server
from techchallenge4.entradas import UPLOAD, parse_form, prepare_inputs, validate_audio


def multipart(fields, files):
    boundary = "upload-test-boundary"
    body = bytearray()
    for name, value in fields.items():
        body.extend(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
        )
    for name, filename, raw in files:
        body.extend(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; filename="{filename}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode()
        )
        body.extend(raw)
        body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())
    return bytes(body), "multipart/form-data; boundary=" + boundary


def test_multipart_preserva_bytes_e_normaliza_nome():
    raw = b"\x00\xff\x10\x80"
    body, content_type = multipart({"audio": UPLOAD}, [("audio_upload", "../fala.wav", raw)])
    form, uploads = parse_form(content_type, body)
    assert form == {"audio": [UPLOAD]}
    assert uploads["audio_upload"] == {"name": "fala.wav", "data": raw}


def test_audio_longo_ou_truncado_e_rejeitado():
    raw = BytesIO()
    with wave.open(raw, "wb") as out:
        out.setparams((1, 2, 8000, 0, "NONE", "not compressed"))
        out.writeframes(b"\x01\x00" * 8000 * 61)
    with pytest.raises(ValueError, match="60 segundos"):
        validate_audio(raw.getvalue())
    with pytest.raises(ValueError):
        validate_audio(raw.getvalue()[:100])


def test_audio_do_dispositivo_pode_ser_combinado_com_video_do_acervo(tmp_path):
    uploads = {
        "audio_upload": {
            "name": "<fala>.wav",
            "data": (ROOT / "dados/audio/novo-03.wav").read_bytes(),
        }
    }
    inputs = prepare_inputs(ROOT, tmp_path, UPLOAD, "montagem_test.mp4", uploads)
    assert inputs["audio_upload"] and not inputs["video_upload"]
    assert inputs["audio"] == "<fala>.wav"
    assert inputs["audio_path"].name == "audio.wav"
    assert inputs["video_path"].name == "video.mp4"


def test_video_invalido_nao_mantem_entradas_parciais(tmp_path):
    pytest.importorskip("cv2")
    uploads = {"video_upload": {"name": "consulta.mp4", "data": b"sem video"}}
    with pytest.raises(ValueError, match="vídeo legível"):
        prepare_inputs(ROOT, tmp_path, "novo-03.wav", UPLOAD, uploads)
    assert list(tmp_path.iterdir()) == []


def test_envio_http_de_arquivo_invalido_nao_inicia_modelos(tmp_path):
    server = create_server(tmp_path / "caixa.sqlite3", port=0)
    worker = Thread(target=server.serve_forever)
    worker.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        with urlopen(base) as response:
            page = response.read().decode()
        import re

        token = re.search(r'name="token" type="hidden" value="([^"]+)', page)[1]
        body, content_type = multipart(
            {
                "audio": UPLOAD,
                "video": "montagem_test.mp4",
                "token": token,
                "chave": "sk-exemplo-local",
            },
            [("audio_upload", "fala.wav", b"invalido")],
        )
        with (
            patch("techchallenge4.consulta_web.Thread") as model_worker,
            pytest.raises(HTTPError) as error,
        ):
            urlopen(Request(base + "/processar", body, {"Content-Type": content_type}))
        assert error.value.code == 400 and model_worker.call_count == 0
    finally:
        server.shutdown()
        worker.join()
        server.server_close()


def test_resultado_aponta_para_video_anotado_e_preserva_consultas_antigas():
    from techchallenge4.consulta_web import evidence_html

    import json

    result = json.loads(
        (
            ROOT / "integracao/evidencias/revisao_final_20261111/demonstracao-integrada.json"
        ).read_text(encoding="utf-8")
    )
    result["consulta"] = {
        "audio": "novo-03.wav",
        "video": "montagem_test.mp4",
        "caracteristicas": {"duracao": 10, "proporcao_pausas": 0.2},
        "transcricao_local": "Fala",
        "transcricao_nuvem": "Fala",
        "modelo_transcricao": "asr",
        "modelo_texto": "texto",
        "custo_estimado_usd": 0.001,
        "amostras_referencia": 30,
        "video_processado": True,
    }
    html = evidence_html(result)
    assert "/video_anotado.webm" in html and "/midia/video/" not in html
    del result["consulta"]["video_processado"]
    html = evidence_html(result)
    assert "antes da gravação do vídeo anotado" in html and "/midia/video/" not in html


def test_video_gravado_preserva_as_caixas_do_detector(tmp_path):
    cv2 = pytest.importorskip("cv2")
    np = pytest.importorskip("numpy")
    from video.alerta_video import analisar_video

    source = tmp_path / "video.avi"
    writer = cv2.VideoWriter(str(source), cv2.VideoWriter_fourcc(*"MJPG"), 5, (64, 64))
    assert writer.isOpened()
    for _ in range(5):
        writer.write(np.zeros((64, 64, 3), dtype=np.uint8))
    writer.release()

    class Detector:
        names = {0: "Tools", 1: "Uterus"}

        def predict(self, frame, **kwargs):
            class Result:
                boxes = type("Boxes", (), {"cls": np.array([1]), "conf": np.array([0.99])})()

                def plot(self):
                    marked = frame.copy()
                    cv2.rectangle(marked, (8, 8), (56, 56), (0, 255, 0), 4)
                    return marked

            return [Result()]

    result = analisar_video(
        source, None, saida=tmp_path / "saida", modelo=Detector(), formato_video="webm"
    )
    output = Path(result["video_anotado"])
    assert output.suffix == ".webm" and output.stat().st_size > 0
    cap = cv2.VideoCapture(str(output))
    try:
        ok, frame = cap.read()
        assert ok and frame[6:12, 12:45, 1].mean() > 100
    finally:
        cap.release()
