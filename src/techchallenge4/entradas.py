"""Recebimento das mídias e cópia das entradas de cada consulta."""

from datetime import datetime
from email import policy
from email.parser import BytesParser
from io import BytesIO
from pathlib import Path
from uuid import uuid4
import wave

MAX_AUDIO_BYTES = 25 * 1024 * 1024
MAX_VIDEO_BYTES = 100 * 1024 * 1024
MAX_REQUEST_BYTES = MAX_AUDIO_BYTES + MAX_VIDEO_BYTES + 65536
UPLOAD = "__upload__"
VIDEO_EXTENSIONS = {".mp4", ".webm", ".avi", ".mov"}


def parse_form(content_type, body):
    if not content_type.startswith("multipart/form-data"):
        from urllib.parse import parse_qs

        return parse_qs(body.decode("utf-8")), {}
    message = BytesParser(policy=policy.default).parsebytes(
        ("Content-Type: " + content_type + "\r\nMIME-Version: 1.0\r\n\r\n").encode() + body
    )
    if not message.is_multipart():
        raise ValueError("O envio de arquivos está incompleto.")
    form, uploads = {}, {}
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        if not name or name in form or name in uploads:
            raise ValueError("Campos repetidos ou inválidos no formulário.")
        data = part.get_payload(decode=True)
        if data is None:
            raise ValueError("Conteúdo do arquivo inválido.")
        filename = part.get_filename()
        if filename:
            if name not in {"audio_upload", "video_upload"}:
                raise ValueError("Campo de arquivo desconhecido.")
            uploads[name] = {"name": filename.replace("\\", "/").split("/")[-1][:120], "data": data}
        else:
            if len(data) > 4096:
                raise ValueError("Campo de texto acima do tamanho permitido.")
            form[name] = [data.decode("utf-8")]
    return form, uploads


def validate_audio(raw):
    if not 0 < len(raw) <= MAX_AUDIO_BYTES:
        raise ValueError("Envie um áudio WAV de até 25 MB.")
    try:
        with wave.open(BytesIO(raw), "rb") as audio:
            seconds = audio.getnframes() / audio.getframerate()
            valid = (
                audio.getsampwidth() == 2
                and audio.getnchannels() in (1, 2)
                and 8000 <= audio.getframerate() <= 48000
                and 0 < seconds <= 60
            )
            expected = audio.getnframes() * audio.getnchannels() * 2
            complete = len(audio.readframes(audio.getnframes())) == expected
    except (wave.Error, EOFError, ZeroDivisionError):
        valid = complete = False
    if not valid or not complete:
        raise ValueError("Use WAV PCM16, mono ou estéreo, de 8 a 48 kHz e até 60 segundos.")


def prepare_inputs(root, case_root, wav, mp4, uploads):
    from .consulta import AUDIO_DIR, VIDEO_DIR

    audio_upload, video_upload = wav == UPLOAD, mp4 == UPLOAD
    audio = (
        uploads.get("audio_upload")
        if audio_upload
        else {"name": wav, "data": (root / AUDIO_DIR / wav).read_bytes()}
    )
    video = (
        uploads.get("video_upload")
        if video_upload
        else {"name": mp4, "data": (root / VIDEO_DIR / mp4).read_bytes()}
    )
    if not audio or not video:
        raise ValueError("Selecione os arquivos do dispositivo para as mídias indicadas.")
    if Path(audio["name"]).suffix.lower() != ".wav":
        raise ValueError("O áudio deve estar no formato WAV.")
    extension = Path(video["name"]).suffix.lower()
    if extension not in VIDEO_EXTENSIONS or not 0 < len(video["data"]) <= MAX_VIDEO_BYTES:
        raise ValueError("Use vídeo MP4, WebM, AVI ou MOV de até 100 MB.")
    validate_audio(audio["data"])
    case = "consulta-" + datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid4().hex[:6]
    folder = case_root / case
    inputs = folder / "entradas"
    inputs.mkdir(parents=True)
    audio_path, video_path = inputs / "audio.wav", inputs / ("video" + extension)
    try:
        audio_path.write_bytes(audio["data"])
        video_path.write_bytes(video["data"])
        if video_upload:
            import cv2

            cap = cv2.VideoCapture(str(video_path))
            try:
                ok, _ = cap.read()
                fps = cap.get(cv2.CAP_PROP_FPS)
                duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps if fps > 0 else 0
                if not ok or not 0 < duration <= 300:
                    raise ValueError("Use um vídeo legível com duração de até cinco minutos.")
            finally:
                cap.release()
    except Exception:
        # Apenas os dois caminhos internos criados nesta solicitação são removidos.
        audio_path.unlink(missing_ok=True)
        video_path.unlink(missing_ok=True)
        inputs.rmdir()
        folder.rmdir()
        raise
    return {
        "id": case,
        "folder": folder,
        "audio": audio["name"],
        "video": video["name"],
        "audio_path": audio_path,
        "video_path": video_path,
        "audio_upload": audio_upload,
        "video_upload": video_upload,
    }
