"""Exibição no Colab/Jupyter e captura das mesmas saídas na execução local."""

from __future__ import annotations

import base64
from dataclasses import dataclass
import io

_capture = None


@dataclass
class HTML:
    content: str


def display(value):
    """Exibe tabelas, figuras ou HTML; a captura não modifica o conteúdo calculado."""
    if _capture is None:
        try:
            from IPython.display import display as native_display, HTML as native_html
        except ImportError:
            print(value.content if isinstance(value, HTML) else value)
        else:
            native_display(native_html(value.content) if isinstance(value, HTML) else value)
        return
    if isinstance(value, HTML):
        data = {"text/html": value.content, "text/plain": "Painel de revisão multimodal"}
    elif hasattr(value, "savefig"):
        buffer = io.BytesIO()
        value.savefig(buffer, format="png", dpi=120, bbox_inches="tight")
        data = {
            "image/png": base64.b64encode(buffer.getvalue()).decode(),
            "text/plain": "Figura calculada na execução da célula",
        }
    elif hasattr(value, "to_html"):
        data = {"text/html": value.to_html(index=False), "text/plain": value.to_string(index=False)}
    else:
        data = {"text/plain": str(value)}
    _capture({"output_type": "display_data", "data": data, "metadata": {}})
