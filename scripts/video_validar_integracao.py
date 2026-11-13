"""Controles offline: vídeo sem evento parcial e vídeo positivo continuam na revisão."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from techchallenge4.core import combinar_audio_video
from techchallenge4.delivery import AlertStore
from techchallenge4.reports import atomic_write, salvar_resultados
from techchallenge4.dashboard import render_dashboard


def main():
    output = ROOT / "integracao/evidencias/revisao_video_externo_20261111"
    store = AlertStore(output / "alertas.sqlite3")
    results = []
    for name in ("filtrado", "reserva_temporal"):
        source = ROOT / f"evidence/resultado_video_externo_{name}.json"
        video = json.loads(source.read_text(encoding="utf-8"))
        result = combinar_audio_video(
            ("neutro", 0.95),
            video,
            id_caso=f"controle-externo-{name.replace('_', '-')}",
            simulado=True,
            origem_audio="controle_de_software_neutro_nao_gravacao_clinica",
            origem_video=source.name,
            pareamento="controle_sintetico_de_integracao_sem_paciente_pareado",
        )
        if not result["requer_revisao"] or "video" not in result["fontes_inconclusivas"]:
            raise AssertionError("Cobertura parcial foi perdida.")
        if result["alerta"] != video["alerta"]:
            raise AssertionError("Sinal positivo foi alterado pela fusão.")
        result["entrega"] = store.deliver(result)
        results.append(result)
    salvar_resultados(results, output)
    atomic_write(output / "painel.html", render_dashboard(store.list_alerts(), interactive=False))
    summary = {
        "cases": [
            {
                "id": r["id_caso"],
                "alerta": r["alerta"],
                "nivel": r["nivel"],
                "requer_revisao": r["requer_revisao"],
                "status": r["status"],
            }
            for r in results
        ],
        "queued": len(store.list_alerts()),
        "paid_api_calls": 0,
        "neutral_audio_is_software_control": True,
        "clinical_pairing": False,
    }
    atomic_write(
        ROOT / "evidence/video_integracao_revisao.json",
        json.dumps(summary, ensure_ascii=False, indent=2),
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
