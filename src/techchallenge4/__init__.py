"""Integração multimodal acadêmica: decisões rastreáveis, sem diagnóstico."""

from .core import (
    AVISO,
    combinar_audio_video,
    detectar_series,
    detectar_prescricoes,
    fonte_indisponivel,
)
from .delivery import AlertStore, replay_events
from .reports import salvar_resultados, relatorio_automatico

__all__ = [
    "AVISO",
    "combinar_audio_video",
    "detectar_series",
    "detectar_prescricoes",
    "fonte_indisponivel",
    "AlertStore",
    "replay_events",
    "salvar_resultados",
    "relatorio_automatico",
]
