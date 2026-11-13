"""Construção dos notebooks de apresentação a partir de células versionadas."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def md(source):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "id": hashlib.sha256(source.encode()).hexdigest()[:12],
        "source": source,
    }


def code(source):
    return {
        "cell_type": "code",
        "metadata": {},
        "id": hashlib.sha256(source.encode()).hexdigest()[:12],
        "source": source,
        "execution_count": None,
        "outputs": [],
    }


def bootstrap(html=False):
    """Localiza o checkout em qualquer subpasta; clona somente no Colab."""
    cell = code("""from pathlib import Path
import json, sys, subprocess

# A mesma entrada funciona na raiz, em subpastas locais e no Google Colab.
candidatos = [Path.cwd(), *Path.cwd().parents, Path.cwd() / "TechChallengeFase4"]
REPO = next((p for p in candidatos if (p / "src/techchallenge4").is_dir()), None)
if REPO is None:
    if not Path("/content").is_dir():
        raise FileNotFoundError("Abra o notebook dentro do repositório TechChallengeFase4.")
    REPO = Path("/content/TechChallengeFase4")
    if not REPO.exists():
        subprocess.run(["git", "clone", "--branch", "Nirton", "--single-branch",
                        "https://github.com/Val-Faria/TechChallengeFase4.git", str(REPO)], check=True)
sys.path.insert(0, str(REPO / "src"))
from techchallenge4.notebook_display import display, HTML
print("Projeto: TechChallengeFase4 | execução local ou Google Colab")
""")
    if not html:
        cell["source"] = cell["source"].replace("import display, HTML", "import display")
    return cell


def save(cells, name):
    """Grava fontes; as saídas são produzidas por executar_notebooks.py."""
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "cells": cells,
        "metadata": {
            "kernelspec": {"name": "python3", "language": "python", "display_name": "Python 3"},
            "language_info": {"name": "python", "version": "3.12"},
        },
    }
    (ROOT / name).write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Fontes atualizadas: {name}")
