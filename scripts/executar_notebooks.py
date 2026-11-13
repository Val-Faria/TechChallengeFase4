"""Executa as células Python e salva stdout, tabelas, HTML e figuras no ipynb.

Não preenche resultados manualmente. Interrompe na primeira falha, não executa
chamadas pagas opcionais e registra o ambiente real utilizado. Sem kernel GPU.
"""

from __future__ import annotations

import contextlib
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from techchallenge4 import notebook_display

NOTEBOOKS = [
    "audio/notebooks/TechChallengeFase4_audio.ipynb",
    "video/TechChallengeFase4_video.ipynb",
    "integracao/TechChallengeFase4_integracao.ipynb",
]


def execute(path):
    """Mantém um namespace por notebook e atribui contagens somente após executar."""
    notebook = json.loads(path.read_text(encoding="utf-8"))
    namespace = {"__name__": "__main__"}
    count, started = 0, time.perf_counter()
    for cell in notebook["cells"]:
        if cell["cell_type"] != "code":
            continue
        count += 1
        source = cell["source"]
        if isinstance(source, list):
            source = "".join(source)
        outputs, stdout, stderr = [], io.StringIO(), io.StringIO()
        notebook_display._capture = outputs.append
        try:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exec(compile(source, f"{path.name}:célula_{count}", "exec"), namespace)
        finally:
            notebook_display._capture = None
        for name, stream in [("stdout", stdout), ("stderr", stderr)]:
            if stream.getvalue():
                # Oculta somente o caminho pessoal; preserva valores e mensagens.
                value = stream.getvalue().replace(str(ROOT), "<projeto>")
                outputs.insert(0, {"output_type": "stream", "name": name, "text": value})
        cell.update(execution_count=count, outputs=outputs)
    notebook["metadata"]["execution"] = {
        "environment": "Python local; arquivos compatíveis com Google Colab",
        "engine": "Python exec com captura de saídas e exibição MIME",
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "paid_api_calls": 0,
        "training_performed": False,
    }
    path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "code_cells": count,
        "elapsed_s": round(time.perf_counter() - started, 3),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "errors": 0,
    }


def main():
    os.chdir(ROOT)
    os.environ.setdefault("MPLBACKEND", "Agg")
    results = []
    for name in NOTEBOOKS:
        results.append(execute(ROOT / name))
        print(json.dumps(results[-1]), flush=True)
    evidence = {
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version.split()[0],
        "environment": "local_cpu",
        "notebooks": results,
        "versions": {
            p: importlib.metadata.version(p)
            for p in ["numpy", "pandas", "scikit-learn", "matplotlib", "joblib"]
        },
        "paid_api_calls": 0,
        "colab_session_created": False,
        "note": "As saídas foram calculadas pelas células. Métricas históricas são identificadas como leitura de evidências; áudio executa predict no modelo congelado.",
    }
    (ROOT / "evidence/notebooks_execucao.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
