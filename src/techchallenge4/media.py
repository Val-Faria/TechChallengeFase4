"""Detectores observacionais de voz e movimento, sem pesos privados.

Referências anteriores são congeladas. As regras sinalizam alterações físicas
mensuráveis para revisão; não estimam diagnóstico ou probabilidade de doença.
Dependências de mídia são importadas somente ao executar essas funções.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from pathlib import Path
import statistics
import wave

from .core import fonte_indisponivel, numero_finito


@dataclass(frozen=True)
class MediaRules:
    # Regras fixadas antes de produzir os novos cenários controlados.
    pause_increase: float = .20
    burst_ratio: float = .65
    min_audio_seconds: float = 3.
    motion_z: float = 6.
    motion_floor: float = .01  # frações da largura do quadro por segundo
    min_event_seconds: float = 1.
    max_camera_speed: float = .12

    def __post_init__(self):
        numero_finito(self.pause_increase, "pause_increase", .01, .9)
        numero_finito(self.burst_ratio, "burst_ratio", .01, .99)
        for key in ["min_audio_seconds", "motion_z", "motion_floor",
                    "min_event_seconds", "max_camera_speed"]:
            numero_finito(getattr(self, key), key, .001)


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_wav(path):
    """PCM16 mono/stereo only; reject malformed and unbounded input."""
    import numpy as np
    with wave.open(str(path), "rb") as stream:
        sr, channels = stream.getframerate(), stream.getnchannels()
        if stream.getsampwidth() != 2 or channels not in (1, 2) or not 8000 <= sr <= 48000:
            raise ValueError("Use WAV PCM16, mono/estéreo, 8–48 kHz.")
        if not 0 < stream.getnframes() / sr <= 600:
            raise ValueError("A demonstração aceita até dez minutos de WAV.")
        expected_samples = stream.getnframes()*channels
        data = np.frombuffer(stream.readframes(stream.getnframes()), dtype="<i2")
    if len(data) != expected_samples or len(data) % channels:
        raise ValueError("WAV truncado.")
    return data.reshape(-1, channels).astype(float).mean(axis=1) / 32768., sr


def voice_features(samples, sr):
    """20 ms RMS gate relative to this recording; no ASR or symptom text used.

    This is an energy-based vocal-activity proxy, not a breathing classifier.
    Background sounds can affect the result; same-speaker recordings required.
    """
    import numpy as np
    signal = np.asarray(samples, dtype=float)
    if signal.ndim != 1 or not np.isfinite(signal).all() or not 8000 <= sr <= 48000:
        raise ValueError("Sinal/taxa inválidos.")
    size = int(.02 * sr)
    frames = len(signal) // size
    if frames < 150:
        raise ValueError("A janela acústica precisa de pelo menos três segundos.")
    rms = np.sqrt(np.mean(signal[:frames * size].reshape(frames, size) ** 2, axis=1))
    peak = float(np.quantile(rms, .95))
    active = rms > max(.0005, peak * .12)
    # Bridge a single 20 ms gap, preserving longer pauses.
    if len(active) >= 3:
        active[1:-1] |= active[:-2] & active[2:]
    runs, start = [], 0
    for index in range(1, len(active) + 1):
        if index == len(active) or active[index] != active[start]:
            runs.append((bool(active[start]), (index-start)*.02))
            start = index
    voiced = [duration for value, duration in runs if value and duration >= .08]
    pauses = [duration for value, duration in runs if not value]
    return {"duracao_s": len(signal)/sr,
            "proporcao_pausas": float(1.-active.mean()),
            "trecho_vocal_mediano_s": statistics.median(voiced) if voiced else 0.,
            "maior_pausa_s": max(pauses, default=0.),
            "tempo_vocal_s": float(active.sum()*.02),
            "rms_p95": peak,
            "fracao_clipping": float(np.mean(np.abs(signal) >= .999)),
            "proxy_atividade_vocal": "energia_relativa_20ms"}


def fit_voice_reference(paths, *, speaker, simulated=False):
    if not isinstance(speaker, str) or not speaker.strip() or type(simulated) is not bool:
        raise ValueError("Informe a identidade local da voz e a origem sintética.")
    if len(paths) < 2:
        raise ValueError("Forneça ao menos duas gravações anteriores da mesma voz.")
    rows, hashes = [], []
    for path in paths:
        digest = sha256(path)
        if digest in hashes:
            raise ValueError("Gravação duplicada na referência acústica.")
        signal, sr = read_wav(path)
        features = voice_features(signal, sr)
        if features["tempo_vocal_s"] < 1 or features["fracao_clipping"] > .01:
            raise ValueError("Referência sem voz suficiente ou saturada.")
        rows.append(features)
        hashes.append(digest)
    return {"schema_version": 1, "speaker": speaker, "simulado": simulated,
            "sha256_referencias": hashes, "referencia_congelada": True,
            "proporcao_pausas": statistics.median(r["proporcao_pausas"] for r in rows),
            "trecho_vocal_mediano_s": statistics.median(r["trecho_vocal_mediano_s"] for r in rows),
            "escopo": "comparacao_intra_voz; sem ajuste com a midia avaliada"}


def assess_voice(features, reference, *, rules=MediaRules(), simulated=False):
    if type(simulated) is not bool or type(reference.get("simulado")) is not bool:
        raise ValueError("Origem sintética deve ser booleana.")
    simulated |= reference["simulado"]
    if (reference.get("schema_version") != 1 or reference.get("referencia_congelada") is not True
            or not isinstance(reference.get("speaker"), str) or not reference["speaker"].strip()):
        raise ValueError("Referência acústica ausente ou incompatível.")
    duration = numero_finito(features["duracao_s"], "duracao_s", 0)
    voiced = numero_finito(features["tempo_vocal_s"], "tempo_vocal_s", 0, duration+.001)
    clipping = numero_finito(features["fracao_clipping"], "fracao_clipping", 0, 1)
    if duration < rules.min_audio_seconds or voiced < .5 or clipping > .01:
        return fonte_indisponivel("audio", "Janela curta, sem voz suficiente ou saturada.",
                                 simulado=simulated)
    base_pause = numero_finito(reference["proporcao_pausas"], "pausa_referencia", 0, 1)
    base_burst = numero_finito(reference["trecho_vocal_mediano_s"], "trecho_referencia", .001)
    pause = numero_finito(features["proporcao_pausas"], "proporcao_pausas", 0, 1)
    burst = numero_finito(features["trecho_vocal_mediano_s"], "trecho_vocal_mediano_s", 0)
    delta, ratio = pause-base_pause, burst/base_burst
    signal = delta >= rules.pause_increase and ratio <= rules.burst_ratio
    return {"modalidade": "audio", "status": "ok", "alerta": signal,
            "nivel": "medio" if signal else "nenhum", "simulado": simulated,
            "origem": "comparacao_acustica_intra_voz",
            "motivo": ("Pausas aumentadas e trechos vocais encurtados; revisar possível esforço vocal/respiratório."
                       if signal else "A janela não atingiu os dois critérios de alteração acústica."),
            "caracteristicas": features, "referencia": reference,
            "diferenca_pausas": delta, "razao_trecho_vocal": ratio,
            "regras": asdict(rules),
            "limitacoes": "Não identifica a causa das pausas, respirações, doença ou fadiga clínica. Ruído, conteúdo e microfone interferem."}


def motion_features(previous, frame, dt):
    import cv2
    import numpy as np
    numero_finito(dt, "intervalo_quadros", .001)
    if previous.shape != frame.shape:
        raise ValueError("Dimensões do vídeo mudaram.")
    def gray(image):
        # Fixed crop reduces overlays; cannot remove annotations in received clips.
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        h, w = image.shape
        return cv2.resize(image[int(.1*h):int(.9*h), int(.1*w):int(.9*w)], (256, 160))
    a, b = gray(previous), gray(frame)
    flow = cv2.calcOpticalFlowFarneback(a, b, None, .5, 3, 15, 3, 5, 1.2, 0)
    global_shift = np.median(flow.reshape(-1, 2), axis=0)
    residual = flow-global_shift
    speed = np.linalg.norm(residual, axis=2)/(256*dt)
    return {"movimento_relativo": float(np.quantile(speed, .95)),
            "velocidade_camera": float(np.linalg.norm(global_shift)/(256*dt)),
            "textura": float(cv2.Laplacian(b, cv2.CV_64F).var()),
            "brilho": float(b.mean()),
            "metodo": "Farneback_p95_residual_mediana_global"}


class MotionMonitor:
    """First 30 observations are prior reference; never refit on later events.

    Alerts are persistent increases in apparent movement, not anatomy findings.
    Camera shifts, dark/textureless frames produce inconclusive observations.
    """
    def __init__(self, *, warmup=30, rules=MediaRules(), simulated=False):
        if type(warmup) is not int or warmup < 20 or type(simulated) is not bool:
            raise ValueError("Referência visual exige ao menos vinte amostras.")
        self.warmup, self.rules, self.simulated = warmup, rules, simulated
        self.history, self.events = [], []
        self.started = None
        self.last = None
        self.center = self.scale = None

    def feed(self, features, timestamp):
        t = numero_finito(timestamp, "timestamp_video", 0)
        if self.last is not None and t <= self.last:
            raise ValueError("Ordem temporal visual inválida.")
        value = numero_finito(features["movimento_relativo"], "movimento_relativo", 0)
        camera = numero_finito(features["velocidade_camera"], "velocidade_camera", 0)
        texture = numero_finito(features["textura"], "textura", 0)
        brightness = numero_finito(features["brilho"], "brilho", 0, 255)
        gap = self.last is not None and t-self.last > 1.
        self.last = t
        if gap or camera > self.rules.max_camera_speed or texture < 3 or brightness < 8 or brightness > 247:
            self.started = None
            return fonte_indisponivel("video", "Lacuna, câmera instável ou quadro sem informação suficiente.",
                                     simulado=self.simulated)
        if len(self.history) < self.warmup:
            self.history.append(value)
            if len(self.history) == self.warmup:
                self.center = statistics.median(self.history)
                self.scale = max(self.rules.motion_floor,
                    1.4826*statistics.median(abs(v-self.center) for v in self.history))
            return fonte_indisponivel("video", f"Referência visual em aquecimento: {len(self.history)}/{self.warmup}.",
                                     simulado=self.simulated)
        score = (value-self.center)/self.scale
        if score >= self.rules.motion_z:
            if self.started is None:
                self.started = t
        else:
            self.started = None
        signal = self.started is not None and t-self.started+1e-8 >= self.rules.min_event_seconds
        current = []
        if signal:
            current = [{"inicio_s": self.started, "fim_s": t,
                        "duracao_s": t-self.started,
                        "descricao": "Aumento persistente de movimento visual frente à referência anterior."}]
            if not self.events or self.events[-1]["inicio_s"] != self.started:
                self.events.append(current[0].copy())
            else:
                self.events[-1] = current[0].copy()
        return {"modalidade": "video", "status": "ok", "alerta": signal,
                "nivel": "medio" if signal else "nenhum", "simulado": self.simulated,
                "origem": "fluxo_optico_referencia_anterior",
                "motivo": "Movimento visual aumentado persistentemente." if signal else "Sem aumento persistente de movimento.",
                "eventos": current, "caracteristicas": features, "escore_robusto": score,
                "referencia": {"mediana": self.center, "escala": self.scale,
                               "amostras": len(self.history), "congelada": True},
                "regras": asdict(self.rules),
                "limitacoes": "Desvio visual inespecífico; não reconhece útero, instrumentos, postura ou complicação cirúrgica."}
