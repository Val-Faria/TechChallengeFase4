"""Transcrição opcional dos áudios de inspeção, com orçamento e cache local.

O custo é estimado pela duração e preço de referência, não pela fatura.
Falhas mantêm a reserva e nunca provocam repetição automática.
"""

from __future__ import annotations
import hashlib
import json
from pathlib import Path
import time
import urllib.error
import urllib.request
import uuid
import wave
from .openai_text import _lock
from .reports import atomic_write

MODEL = "gpt-4o-mini-transcribe"
RATE_PER_MINUTE = 0.003


def request_transcription(path, raw, model, key):
    boundary = uuid.uuid4().hex
    body = bytearray()
    for name, value in [("model", model), ("language", "pt"), ("response_format", "json")]:
        body.extend(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
        )
    # Only a safe constant filename enters the multipart headers.
    body.extend(
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="amostra.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode()
    )
    body.extend(raw)
    body.extend(f"\r\n--{boundary}--\r\n".encode())
    request = urllib.request.Request(
        "https://api.openai.com/v1/audio/transcriptions",
        data=bytes(body),
        headers={
            "Authorization": "Bearer " + key,
            "Content-Type": "multipart/form-data; boundary=" + boundary,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(
            f"Transcrição recusada (HTTP {error.code}); sem repetição automática."
        ) from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise RuntimeError(
            "Falha de conexão na transcrição; reserva mantida, sem repetição automática."
        ) from None


def transcribe_wav(
    path, cache_dir, *, key=None, max_budget_usd=0.02, case_id=None, request_fn=None
):
    if not 0 < max_budget_usd <= 0.02:
        raise ValueError("Orçamento de transcrição permitido: até US$ 0,02.")
    path, cache = Path(path), Path(cache_dir)
    raw = path.read_bytes()
    if len(raw) > 25 * 1024 * 1024:
        raise ValueError("Áudio acima do limite local de 25 MB.")
    with wave.open(str(path), "rb") as wav:
        seconds = wav.getnframes() / wav.getframerate()
    if not 0 < seconds <= 60:
        raise ValueError("Amostra deve ter duração positiva de até 60 segundos.")
    audio_digest = hashlib.sha256(raw).hexdigest()
    digest = hashlib.sha256(raw + MODEL.encode()).hexdigest()
    cache.mkdir(parents=True, exist_ok=True)
    target, ledger_path = cache / f"{digest}.json", cache / "orcamento_transcricao.json"
    with _lock(cache / ".orcamento_audio.lock"):
        if target.exists():
            result = json.loads(target.read_text(encoding="utf8"))
            if (
                not isinstance(result.get("text"), str)
                or not result["text"].strip()
                or result.get("modelo") != MODEL
                or result.get("sha256_audio") != audio_digest
                or abs(result.get("duracao_s", -1) - seconds) > 0.000001
            ):
                raise ValueError(
                    "Cache incompatível com o áudio/modelo; revisar sem enviar nova chamada."
                )
            return {**result, "cache_utilizado": True}
        if not key and request_fn is None:
            raise ValueError("Chave da API ausente; nenhum pedido enviado.")
        ledger = (
            json.loads(ledger_path.read_text(encoding="utf8"))
            if ledger_path.exists()
            else {"chamadas": []}
        )
        ledger["limite_usd"] = max_budget_usd
        reservation = seconds * RATE_PER_MINUTE / 60
        used = sum(c["custo_contabilizado_usd"] for c in ledger["chamadas"])
        if len(ledger["chamadas"]) >= 6 or used + reservation > max_budget_usd:
            raise ValueError(
                "Limite de seis chamadas ou orçamento atingido; nenhum pedido enviado."
            )
        entry = {
            "id": case_id or path.stem,
            "modelo": MODEL,
            "sha256_audio": audio_digest,
            "duracao_s": seconds,
            "custo_contabilizado_usd": reservation,
            "estado": "reservado",
        }
        ledger["chamadas"].append(entry)
        atomic_write(ledger_path, json.dumps(ledger, ensure_ascii=False, indent=2))
        started = time.perf_counter()
        try:
            result = (request_fn or request_transcription)(path, raw, MODEL, key)
            if (
                not isinstance(result, dict)
                or not isinstance(result.get("text"), str)
                or not result["text"].strip()
            ):
                raise ValueError("Serviço não retornou transcrição válida.")
            result.update(
                {
                    "modelo": MODEL,
                    "duracao_s": seconds,
                    "latencia_s": time.perf_counter() - started,
                    "sha256_audio": audio_digest,
                    "custo_estimado_usd": reservation,
                    "cache_utilizado": False,
                }
            )
            atomic_write(target, json.dumps(result, ensure_ascii=False, indent=2))
            entry["estado"] = "concluido_estimativa_por_duracao"
        except Exception as error:
            entry.update({"estado": "falha_reserva_mantida", "erro": type(error).__name__})
            atomic_write(ledger_path, json.dumps(ledger, ensure_ascii=False, indent=2))
            raise
        atomic_write(ledger_path, json.dumps(ledger, ensure_ascii=False, indent=2))
        return result
