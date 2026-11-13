"""As saídas devem vir da execução; falhas não podem ser gravadas como sucesso."""

import importlib.util
import json
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location(
    "executar_notebooks", Path(__file__).parents[1] / "scripts/executar_notebooks.py"
)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_calculo_e_html_sao_salvos(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    path = tmp_path / "controle.ipynb"
    cells = [
        {"cell_type": "code", "source": "valor = 6 * 7\nprint(valor)", "outputs": []},
        {
            "cell_type": "code",
            "source": "from techchallenge4.notebook_display import display, HTML\ndisplay(HTML('<p>' + str(valor) + '</p>'))",
            "outputs": [],
        },
    ]
    path.write_text(json.dumps({"metadata": {}, "cells": cells}), encoding="utf-8")
    result = runner.execute(path)
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert result["code_cells"] == 2
    assert saved["cells"][0]["outputs"][0]["text"] == "42\n"
    assert saved["cells"][1]["outputs"][0]["data"]["text/html"] == "<p>42</p>"
    assert [c["execution_count"] for c in saved["cells"]] == [1, 2]
    assert runner.notebook_display._capture is None


def test_falha_nao_grava_sucesso(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    path = tmp_path / "falha.ipynb"
    original = json.dumps(
        {
            "metadata": {},
            "cells": [
                {"cell_type": "code", "source": "raise ValueError('falha real')", "outputs": []}
            ],
        }
    )
    path.write_text(original, encoding="utf-8")
    with pytest.raises(ValueError, match="falha real"):
        runner.execute(path)
    assert path.read_text(encoding="utf-8") == original
    assert runner.notebook_display._capture is None
