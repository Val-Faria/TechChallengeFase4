"""Exportação atômica de snapshots legíveis e verificáveis."""
from __future__ import annotations
import csv
import io
import json
import os
import tempfile
from pathlib import Path


def atomic_write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def relatorio_automatico(resultado):
    r = resultado
    lines = ["# Relatório automático multimodal", "",
             f"**Caso:** {r['id_caso']}",
             f"**Resultado:** {r['id_resultado']}",
             f"**Prioridade:** {r['nivel']}",
             f"**Cobertura:** {r['status']}",
             f"**Revisão necessária:** {r['requer_revisao']}",
             f"**Contém fonte simulada:** {r['simulado']}",
             f"**Associação:** {r['pareamento']}", ""]
    for source in r["fontes"]:
        lines += [f"## {source['modalidade']}", "",
                  f"- Estado: {source['status']}",
                  f"- Origem: {source.get('origem', 'não fornecida')}",
                  f"- Motivo: {source['motivo']}"]
        for event in source.get("eventos", []):
            lines.append("- Evidência: " + json.dumps(event, ensure_ascii=False))
        for mention in source.get("mencoes", []):
            lines.append(f"- Menção: {mention['termo']}; estado: {mention['estado']}; "
                         f"contexto: {mention['contexto']}; trecho: “{mention['evidencia']}”.")
        lines.append("")
    lines += ["## Resposta operacional", "",
              "Entrega: " + json.dumps(r.get("entrega", {}), ensure_ascii=False), "",
              "A caixa de revisão e o painel são locais. Não há envio a um hospital.", "",
              "> " + r["aviso"], ""]
    return "\n".join(lines)


def salvar_resultados(resultados, pasta):
    pasta = Path(pasta)
    ids = [r["id_caso"] for r in resultados]
    if len(ids) != len(set(ids)):
        raise ValueError("Cada snapshot deve conter um identificador por caso.")
    # Filenames must remain safe even if a caller bypassed the fusion function.
    import re
    if any(not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", value) for value in ids):
        raise ValueError("Identificador de caso inválido para exportação.")
    for r in resultados:
        encoded = json.dumps(r, ensure_ascii=False, indent=2, allow_nan=False)
        atomic_write(pasta / f"{r['id_caso']}.json", encoded + "\n")
        atomic_write(pasta / f"{r['id_caso']}.md", relatorio_automatico(r))
    for name, rows in [("resultados.jsonl", resultados),
                       ("fila_revisao.jsonl", [r for r in resultados if r["requer_revisao"]])]:
        atomic_write(pasta / name, "".join(json.dumps(r, ensure_ascii=False, allow_nan=False)
                                         + "\n" for r in rows))
    stream = io.StringIO(newline="")
    columns = ["id_caso", "nivel", "alerta", "status", "simulado", "requer_revisao"]
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows({key: r[key] for key in columns} for r in resultados)
    atomic_write(pasta / "resumo.csv", stream.getvalue())
    return pasta
