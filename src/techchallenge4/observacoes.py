"""Série acadêmica usada para acompanhar sinais, movimentação e prescrições."""

from datetime import datetime, timedelta, timezone
from .core import detectar_series, detectar_prescricoes


def structured_examples():
    start = datetime(2026, 11, 9, 12, tzinfo=timezone.utc)

    def stamp(index):
        return (start + timedelta(seconds=index)).isoformat()

    historical = [
        {
            "timestamp": stamp(i),
            "batimentos": 72 + (i % 5) - 2,
            "oxigenacao": 97 + (i % 3) - 1,
            "movimento": 10 + (i % 5) - 2,
            "pressao_sistolica": 120 + (i % 5) - 2,
            "pressao_diastolica": 80 + (i % 3) - 1,
        }
        for i in range(30)
    ]
    observations = [
        {
            "timestamp": stamp(30),
            "batimentos": 73,
            "oxigenacao": 97,
            "movimento": 11,
            "pressao_sistolica": 121,
            "pressao_diastolica": 80,
        },
        {
            "timestamp": stamp(31),
            "batimentos": 120,
            "oxigenacao": 85,
            "movimento": 50,
            "pressao_sistolica": 160,
            "pressao_diastolica": 105,
        },
    ]
    prescriptions = [
        {
            "timestamp": stamp(0),
            "medicamento_id": "medicamento_demo",
            "dose": 10,
            "unidade": "mg",
            "via": "oral",
            "intervalo_h": 12,
        },
        {
            "timestamp": stamp(31),
            "medicamento_id": "medicamento_demo",
            "dose": 20,
            "unidade": "mg",
            "via": "oral",
            "intervalo_h": 12,
        },
    ]
    sources = [
        detectar_series(
            historical,
            observations,
            ["batimentos", "oxigenacao", "pressao_sistolica", "pressao_diastolica"],
            "sinais_vitais",
            simulado=True,
        ),
        detectar_series(historical, observations, ["movimento"], "movimentacao", simulado=True),
        detectar_prescricoes(prescriptions, simulado=True),
    ]
    return {
        "natureza": "dados_sinteticos_para_demonstracao_de_software",
        "limiares": "estatisticos_demonstrativos_sem_validacao_clinica",
        "historico": historical,
        "observacoes": observations,
        "prescricoes": prescriptions,
        "resultados": sources,
    }
