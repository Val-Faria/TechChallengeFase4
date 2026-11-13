"""Execução reprodutível: arquivos dos modelos, fontes sintéticas e entrega local."""

from __future__ import annotations
import argparse
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
from .core import combinar_audio_video, detectar_series, detectar_prescricoes
from .delivery import AlertStore, replay_events
from .reports import atomic_write, salvar_resultados


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


def load_audio(path, filename=None):
    """Seleciona explicitamente uma gravação quando o CSV contém múltiplos arquivos."""
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError("CSV de áudio vazio.")
    if filename is None and len(rows) != 1:
        raise ValueError("CSV com vários áudios: informe --audio-filename explicitamente.")
    matches = [row for row in rows if row.get("arquivo") == filename] if filename else rows
    if len(matches) != 1:
        raise ValueError("Escolha um arquivo único presente no CSV de áudio.")
    row = matches[0]
    return {
        "classe_audio": row["classe_audio"],
        "confianca_audio": float(row["confianca_audio"]),
    }, row["arquivo"]


def run_demo(output, *, audio_csv=None, audio_filename=None, video_json=None, text_json=None):
    """Executa a composição e os controles; entradas estruturadas são sintéticas e identificadas."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    provenance = {
        "natureza": "demonstracao_com_fontes_independentes_sem_pareamento_clinico",
        "arquivos": {},
    }
    audio, audio_origin = None, "nao_fornecido"
    if audio_csv:
        audio, name = load_audio(audio_csv, audio_filename)
        audio_origin = f"CSV:{Path(audio_csv).name}:{name}"
    video = json.loads(Path(video_json).read_text(encoding="utf-8-sig")) if video_json else None
    text = json.loads(Path(text_json).read_text(encoding="utf-8-sig")) if text_json else None
    for role, path in [
        ("audio_csv", audio_csv),
        ("video_json", video_json),
        ("texto_json", text_json),
    ]:
        if path:
            provenance["arquivos"][role] = {
                "nome": Path(path).name,
                "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
            }
    synthetic = structured_examples()
    final = combinar_audio_video(
        audio,
        video,
        id_caso="demonstracao-integrada",
        origem_audio=audio_origin,
        origem_video=f"JSON:{Path(video_json).name}" if video_json else "nao_fornecido",
        pareamento="composicao_didatica_de_fontes_independentes_sem_mesmo_paciente",
        fontes_adicionais=synthetic["resultados"] + ([text] if text else []),
        fontes_esperadas=[
            "audio",
            "video",
            "texto_openai",
            "sinais_vitais",
            "prescricoes",
            "movimentacao",
        ],
    )
    final["proveniencia"] = provenance
    controls = [
        combinar_audio_video(
            ("neutro", 0.95),
            {"alerta": False, "nivel": "nenhum"},
            id_caso="controle-sem-sinal",
            simulado=True,
        ),
        combinar_audio_video(
            ("neutro", 0.95),
            {
                "alerta": True,
                "nivel": "alto",
                "eventos": [{"inicio_s": 1, "fim_s": 19, "duracao_s": 18}],
            },
            id_caso="controle-preserva-video",
            simulado=True,
        ),
        combinar_audio_video(
            None,
            {"alerta": False, "nivel": "nenhum"},
            id_caso="controle-fonte-ausente",
            simulado=True,
        ),
        combinar_audio_video(
            ("neutro", 0.30),
            {"alerta": False, "nivel": "nenhum"},
            id_caso="controle-baixa-confianca",
            simulado=True,
        ),
    ]
    store = AlertStore(output / "alertas.sqlite3")
    results = [final] + controls
    replay = replay_events(
        [{"offset_s": i * 0.1, "resultado": result} for i, result in enumerate(results)], store
    )
    for result, receipt in zip(results, replay):
        result["entrega"] = receipt["entrega"]
    # Delivering the same result twice must not enqueue two review tasks.
    before = len(store.list_alerts())
    store.deliver(final)
    idempotent = len(store.list_alerts()) == before
    salvar_resultados(results, output)
    atomic_write(
        output / "replay.json",
        json.dumps(
            {
                "eventos": replay,
                "idempotencia_confirmada": idempotent,
                "alertas_na_caixa": len(store.list_alerts()),
                "ressalva": "Replay de resultados; não mede inferência nem sistema hospitalar.",
            },
            ensure_ascii=False,
            indent=2,
        ),
    )
    atomic_write(
        output / "entrega_auditoria.json",
        json.dumps(store.audit_log(), ensure_ascii=False, indent=2),
    )
    atomic_write(
        output / "anomalias_estruturadas.json", json.dumps(synthetic, ensure_ascii=False, indent=2)
    )
    from .dashboard import render_dashboard

    atomic_write(output / "painel.html", render_dashboard(store.list_alerts(), interactive=False))
    return {
        "resultados": len(results),
        "caixa_revisao": len(store.list_alerts()),
        "idempotencia": idempotent,
        "saida": str(output),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="integracao/saidas/execucao_local")
    parser.add_argument("--audio-csv")
    parser.add_argument("--audio-filename")
    parser.add_argument("--video-json")
    parser.add_argument("--text-json")
    args = parser.parse_args(argv)
    print(
        json.dumps(
            run_demo(
                args.output,
                audio_csv=args.audio_csv,
                audio_filename=args.audio_filename,
                video_json=args.video_json,
                text_json=args.text_json,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
