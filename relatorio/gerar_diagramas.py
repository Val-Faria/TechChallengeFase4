"""Diagramas vetoriais do processamento, da regra visual e da decisão integrada.

O esquema temporal é ilustrativo; a figura de fusão lê o caso publicado.
Não utiliza imagens clínicas ou resultados inventados de modelos.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "relatorio/latex/figures"
INK = "#18394a"
BLUE = "#eaf2f8"
TEAL = "#e8f3ef"
GRAY = "#f3f5f6"
AMBER = "#fff0d4"


def canvas(width, height, xlim, ylim):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(width, height))
    ax.set(xlim=xlim, ylim=ylim)
    ax.axis("off")
    fig.patch.set_facecolor("white")
    fig.subplots_adjust(left=0.015, right=0.985, top=0.985, bottom=0.015)
    return fig, ax


def box(ax, x, y, w, h, text, fill=GRAY, size=11):
    from matplotlib.patches import FancyBboxPatch

    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.025,rounding_size=0.10",
            linewidth=1,
            facecolor=fill,
            edgecolor=INK,
        )
    )
    ax.text(
        x + w / 2,
        y + h / 2,
        text,
        ha="center",
        va="center",
        fontsize=size,
        color=INK,
        linespacing=1.3,
    )


def arrow(ax, start, end, color=INK):
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops={
            "arrowstyle": "-|>",
            "lw": 1.35,
            "color": color,
            "shrinkA": 2,
            "shrinkB": 2,
            "mutation_scale": 12,
        },
    )


def save(fig, stem):
    import matplotlib.pyplot as plt

    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight", pad_inches=0.08)
    fig.savefig(OUT / f"{stem}.png", dpi=200, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)


def architecture():
    fig, ax = canvas(8.5, 7.2, (0, 16), (0, 13))
    xs = [0.2, 4.2, 8.2, 12.2]
    titles = ["VOZ", "TEXTO", "VÍDEO", "SÉRIES"]
    inputs = [
        "Áudio WAV\n16 kHz, mono",
        "Transcrição\nda consulta",
        "Quadros do\nvídeo",
        "Sinais vitais,\nprescrições e\nmovimento",
    ]
    methods = [
        "Whisper + Librosa\nRandom Forest",
        "API OpenAI\nTermos, contexto\ne sentimento",
        "Aparência + YOLOv8\nRegra temporal",
        "Mediana / MAD\nComparação de\nprescrições",
    ]
    outputs = [
        "Classe, confiança\ne características",
        "Menções e\ntrechos de evidência",
        "Intervalos e\ncobertura visual",
        "Desvios e\nmudanças temporais",
    ]
    for x, title, inp, method, output in zip(xs, titles, inputs, methods, outputs):
        ax.text(x + 1.7, 12.55, title, ha="center", fontsize=12.5, weight="bold", color=INK)
        box(ax, x, 10.3, 3.4, 1.65, inp, BLUE, 11.1)
        arrow(ax, (x + 1.7, 10.3), (x + 1.7, 9.6))
        box(ax, x, 7.8, 3.4, 1.8, method, TEAL, 10.6)
        arrow(ax, (x + 1.7, 7.8), (x + 1.7, 7.1))
        box(ax, x, 5.7, 3.4, 1.4, output, GRAY, 10.4)
        arrow(ax, (x + 1.7, 5.7), (x + 1.7, 4.85))
    box(
        ax,
        0.2,
        3.6,
        15.4,
        1.25,
        "VALIDAÇÃO E FUSÃO POR CASO\nMaior prioridade válida + origem + confiança + cobertura",
        BLUE,
        11.6,
    )
    arrow(ax, (7.9, 3.6), (7.9, 2.9))
    box(
        ax,
        0.2,
        1.7,
        15.4,
        1.2,
        "ENTREGA LOCAL\nRelatórios JSON / Markdown / CSV + caixa SQLite",
        GRAY,
        11.6,
    )
    arrow(ax, (7.9, 1.7), (7.9, 1.05))
    box(
        ax,
        0.2,
        0.05,
        15.4,
        1,
        "REVISÃO HUMANA NO PAINEL\nConfirmação de leitura e trilha de auditoria",
        TEAL,
        11.6,
    )
    save(fig, "fluxo_multimodal")


def temporal_rule():
    fig, ax = canvas(8.5, 4.9, (-3.0, 10.4), (-0.7, 7.0))
    ax.text(
        -2.8,
        6.55,
        "A. Condição contínua: forma um intervalo",
        fontsize=12.5,
        weight="bold",
        color=INK,
    )
    rows = [
        (5.5, "Instrumento", [(0, 10, BLUE)]),
        (4.7, "Útero detectado", [(0, 2, TEAL), (8, 10, TEAL)]),
        (3.9, "Condição visual", [(2, 8, AMBER)]),
    ]
    for y, label, segments in rows:
        ax.text(-0.25, y + 0.19, label, ha="right", va="center", fontsize=10.8, color=INK)
        ax.broken_barh([(0, 10)], (y, 0.38), facecolors="#f4f5f6")
        for start, end, color in segments:
            ax.broken_barh(
                [(start, end - start)], (y, 0.38), facecolors=color, edgecolors=INK, linewidth=0.8
            )
    ax.annotate("", xy=(7, 3.55), xytext=(2, 3.55), arrowprops={"arrowstyle": "<->", "color": INK})
    ax.text(4.5, 3.18, "5 s de persistência", ha="center", fontsize=10.5, color=INK)
    ax.text(7.1, 4.05, "Revisar", fontsize=10.5, color=INK)
    ax.text(
        -2.8,
        2.45,
        "B. Quadro incompatível: interrompe o intervalo",
        fontsize=12.5,
        weight="bold",
        color=INK,
    )
    ax.text(-0.25, 1.6, "Condição visual", ha="right", fontsize=10.8, color=INK)
    ax.broken_barh(
        [(2, 2.4), (5.4, 2.6)], (1.4, 0.38), facecolors=AMBER, edgecolors=INK, linewidth=0.8
    )
    ax.broken_barh(
        [(4.4, 1)], (1.3, 0.58), facecolors="#dedee6", edgecolors=INK, hatch="///", linewidth=0.8
    )
    ax.text(4.9, 0.95, "Fora da referência", ha="center", fontsize=10.5, color=INK)
    ax.text(
        0.2,
        0.25,
        "Trechos menores que 5 s: sem evento positivo; cobertura parcial exige revisão.",
        fontsize=10.3,
        color=INK,
    )
    for t in range(11):
        ax.plot([t, t], [-0.2, -0.1], color=INK, lw=0.8)
        ax.text(t, -0.43, str(t), ha="center", fontsize=9.5, color=INK)
    ax.text(10.1, -0.43, "s", fontsize=9.5, color=INK)
    save(fig, "regra_temporal_didatica")


def decision_example():
    case = json.loads(
        (
            ROOT / "integracao/evidencias/revisao_final_20261111/demonstracao-integrada.json"
        ).read_text(encoding="utf-8")
    )
    sources = {s["modalidade"]: s for s in case["fontes"]}
    fig, ax = canvas(8.5, 5.6, (0, 16), (0, 10))
    labels = [
        ("audio", "VOZ", "Confiança 0,595 < 0,70\nResultado inconclusivo"),
        ("video", "VÍDEO", "Sinal ALTO\nCobertura parcial"),
        ("texto_openai", "TEXTO", "Menções afirmadas atuais\nSinal MÉDIO"),
        ("sinais_vitais", "SÉRIES", "Sinais vitais, prescrição e\nmovimento: sinais MÉDIOS"),
    ]
    assert sources["audio"]["confianca_audio"] == 0.595 and sources["video"]["nivel"] == "alto"
    assert (
        sources["texto_openai"]["nivel"] == "medio"
        and case["nivel"] == "alto"
        and case["status"] == "incompleto"
    )
    assert all(
        sources[k]["nivel"] == "medio" for k in ("sinais_vitais", "prescricoes", "movimentacao")
    )
    for i, (_, title, text) in enumerate(labels):
        y = 7.65 - i * 2.25
        box(ax, 0.1, y, 5.2, 1.75, title + "\n" + text, AMBER if i < 2 else GRAY, 11.3)
        # As conexões chegam por um barramento, sem cruzar textos ou caixas.
        ax.plot([5.3, 6.0], [y + 0.875, y + 0.875], color=INK, lw=1.2)
    ax.plot([6.0, 6.0], [1.775, 8.525], color=INK, lw=1.2)
    arrow(ax, (6.0, 8.525), (7.05, 8.525))
    box(
        ax, 7.05, 7.65, 8.65, 1.75, "FUSÃO\nPrioridade final: ALTA\nCobertura: INCOMPLETA", BLUE, 12
    )
    arrow(ax, (11.375, 7.65), (11.375, 6.3))
    box(
        ax,
        7.05,
        4.55,
        8.65,
        1.75,
        "ENCAMINHAMENTO\nRevisão necessária\nRegistro na caixa SQLite",
        TEAL,
        12,
    )
    arrow(ax, (11.375, 4.55), (11.375, 3.2))
    box(
        ax,
        7.05,
        1.45,
        8.65,
        1.75,
        "PAINEL E AUDITORIA\nResponsável + instante de revisão\nSem alteração automática de tratamento",
        GRAY,
        11.2,
    )
    save(fig, "exemplo_fusao")


def main():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "DejaVu Sans", "pdf.fonttype": 42})
    architecture()
    temporal_rule()
    decision_example()
    print("Três diagramas gerados em PDF vetorial e PNG.")


if __name__ == "__main__":
    main()
