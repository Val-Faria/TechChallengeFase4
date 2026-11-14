"""Processamento de uma consulta a partir das mídias do acervo acadêmico."""

from datetime import datetime
import json
from pathlib import Path
from uuid import uuid4

from .audio import infer_audio
from .core import combinar_audio_video
from .observacoes import structured_examples
from .media import assess_voice, read_wav, sha256, voice_features
from .openai_audio import transcribe_wav
from .openai_text import analyze_text_openai
from .reports import salvar_resultados

ROOT = Path(__file__).resolve().parents[2]
WAVS = {f"novo-{i:02}.wav": f"Consulta {i:02} · voz sintética" for i in range(1, 7)}
VIDEOS = {
    "montagem_test.mp4": "Montagem de teste",
    "montagem_blind_holdout.mp4": "Montagem da reserva",
}
AUDIO_DIR = Path("dados/audio")
VIDEO_DIR = Path("dados/video")
WEIGHTS = Path("artifacts/video/best_uterus_tools_nirton_v4.pt")
AUDIO_MODEL = Path("artifacts/audio/modelo_audio_1180.joblib")
REFERENCE = Path("artifacts/video/referencia_visual.json")


def missing_files(root, wav, mp4):
    required = [
        AUDIO_DIR / wav,
        VIDEO_DIR / mp4,
        WEIGHTS,
        AUDIO_MODEL,
        REFERENCE,
        AUDIO_DIR / "manifesto.json",
        Path("dados/referencias/referencia_daniel.json"),
        Path("dados/referencias/referencia_maria.json"),
        Path("artifacts/audio/manifesto_audio.json"),
        Path("artifacts/video/manifesto_video.json"),
    ]
    return [p.as_posix() for p in required if not (root / p).is_file()]


def process_case(root, store, wav, mp4, key, progress, on_frame=None):
    """As duas chamadas usam a chave desta solicitação e o orçamento da instalação."""
    from video.alerta_video import analisar_video

    if wav not in WAVS or mp4 not in VIDEOS:
        raise ValueError("Escolha uma das mídias do acervo.")
    if missing_files(root, wav, mp4):
        raise ValueError("Confira os arquivos do acervo incluídos na pasta dados do projeto.")
    case = "consulta-" + datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid4().hex[:6]
    folder = store.path.parent / "consultas" / case
    budget = store.path.parent / "consumo_api"
    weights = json.loads(
        (root / "artifacts/video/manifesto_video.json").read_text(encoding="utf-8")
    )
    reference = json.loads((root / REFERENCE).read_text(encoding="utf-8"))
    if (
        sha256(root / WEIGHTS) != weights["sha256"]
        or reference["model_sha256"] != weights["sha256"]
    ):
        raise ValueError("Pesos ou referência visual incompatíveis com o modelo da equipe.")
    audio = infer_audio(root / AUDIO_DIR / wav, root / AUDIO_MODEL)
    samples = json.loads((root / AUDIO_DIR / "manifesto.json").read_text(encoding="utf-8-sig"))
    sample = next((entry for entry in samples["casos"] if entry["arquivo"] == wav), None)
    if not sample or sample["sha256"] != audio["sha256_wav"]:
        raise ValueError("O WAV difere da gravação cadastrada.")
    speaker = {"Microsoft Daniel": "daniel", "Microsoft Maria Desktop": "maria"}[sample["voz"]]
    baseline = root / "dados/referencias" / f"referencia_{speaker}.json"
    reference_voice = json.loads(baseline.read_text(encoding="utf-8"))
    if (
        reference_voice["speaker"] != speaker
        or audio["sha256_wav"] in reference_voice["sha256_referencias"]
    ):
        raise ValueError("Referência acústica incompatível com a gravação.")
    signal, rate = read_wav(root / AUDIO_DIR / wav)
    vocal = assess_voice(voice_features(signal, rate), reference_voice, simulated=True)
    vocal["modalidade"] = "padrao_vocal"
    if isinstance(vocal.get("limitacoes"), str):
        vocal["limitacoes"] = [vocal["limitacoes"]]
    progress("Analisando os quadros do vídeo com YOLOv8")
    video = analisar_video(
        root / VIDEO_DIR / mp4,
        root / WEIGHTS,
        saida=folder / "video",
        salvar_video=False,
        on_frame=on_frame,
        cobertura_parcial=True,
        referencia_visual=reference,
        limitacoes=["Montagem temporal de quadros. A ausência de detecção exige revisão."],
    )
    progress("Transcrevendo o áudio pela API da OpenAI")
    transcript = transcribe_wav(
        root / AUDIO_DIR / wav,
        budget / "voz",
        key=key,
        case_id=case,
        max_budget_usd=0.02,
        use_cache=False,
    )
    progress("Analisando o relato transcrito pela API da OpenAI")
    text = analyze_text_openai(
        transcript["text"],
        budget / "texto",
        key=key,
        model="gpt-4o-mini",
        max_budget_usd=0.02,
        use_cache=False,
    )
    progress("Comparando as séries e encaminhando o caso para revisão")
    structured = structured_examples()
    result = combinar_audio_video(
        audio,
        video,
        id_caso=case,
        origem_audio=wav,
        origem_video=mp4,
        simulado=True,
        pareamento="fontes acadêmicas independentes",
        fontes_adicionais=[vocal, text, *structured["resultados"]],
        fontes_esperadas=[
            "audio",
            "padrao_vocal",
            "video",
            "texto_openai",
            "sinais_vitais",
            "movimentacao",
            "prescricoes",
        ],
    )
    result["consulta"] = {
        "audio": wav,
        "video": mp4,
        "transcricao_local": audio["transcricao_whisper"],
        "caracteristicas": audio["caracteristicas"],
        "transcricao_nuvem": transcript["text"],
        "modelo_transcricao": transcript["modelo"],
        "modelo_texto": text["modelo"],
        "amostras_referencia": len(structured["historico"]),
        "custo_estimado_usd": transcript["custo_estimado_usd"] + text["custo_estimado_usd"],
    }
    result["entrega"] = store.deliver(result)
    salvar_resultados([result], folder)
    return case
