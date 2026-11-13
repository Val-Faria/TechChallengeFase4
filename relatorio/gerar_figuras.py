"""Figuras científicas extraídas das evidências; sem imagens clínicas privadas."""

from __future__ import annotations
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from techchallenge4.demo import structured_examples

    out = ROOT / "relatorio/latex/figures"
    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
    audio = json.loads((ROOT / "evidence/audio_reproducao.json").read_text(encoding="utf-8"))
    matrix = np.array(audio["blind_holdout"]["confusion_matrix"])
    fig, ax = plt.subplots(figsize=(6, 4.7), layout="constrained")
    im = ax.imshow(matrix, cmap="Blues", vmin=0)
    for i in range(3):
        for j in range(3):
            ax.text(
                j,
                i,
                str(matrix[i, j]),
                ha="center",
                va="center",
                color="white" if matrix[i, j] > matrix.max() / 2 else "black",
            )
    labels = ["Ansiedade/hesitação", "Neutro", "Tristeza"]
    ax.set(
        xticks=range(3),
        yticks=range(3),
        xticklabels=labels,
        yticklabels=labels,
        xlabel="Classe prevista",
        ylabel="Classe de referência",
    )
    plt.setp(ax.get_xticklabels(), rotation=15, ha="right")
    fig.colorbar(im, ax=ax, label="Gravações sintéticas")
    fig.savefig(out / "audio_matriz_cega.png", dpi=180)
    plt.close(fig)
    data = structured_examples()
    rows = data["historico"] + data["observacoes"]
    fig, axes = plt.subplots(4, 1, figsize=(8.2, 8), sharex=True, layout="constrained")
    groups = [
        (["batimentos"], "Batimentos (bpm)"),
        (["pressao_sistolica", "pressao_diastolica"], "Pressão (mmHg)"),
        (["oxigenacao"], "Oxigenação (%)"),
        (["movimento"], "Movimento (u.a.)"),
    ]
    for ax, (fields, label) in zip(axes, groups):
        for field in fields:
            ax.plot(
                range(len(rows)),
                [r[field] for r in rows],
                marker=".",
                label=field.replace("pressao_", "").replace("_", " "),
            )
        ax.axvspan(-0.5, 29.5, color="#e8edf4", label="Histórico anterior")
        ax.axvline(31, color="#b22222", linestyle="--", label="Observação alterada")
        ax.set_ylabel(label)
        ax.grid(alpha=0.2)
        ax.legend(fontsize=8, loc="upper left", ncol=3)
    axes[-1].set_xlabel("Instante da série sintética (s)")
    fig.savefig(out / "series_demonstracao.png", dpi=180)
    plt.close(fig)
    results = ROOT / "dados_privados/video_runs/treino_novo_v4/results.csv"
    if results.is_file():
        with results.open(encoding="utf-8") as stream:
            raw = list(csv.DictReader(stream))
        rows = [{k.strip(): v for k, v in r.items()} for r in raw]
        rows = [r for r in rows if r.get("metrics/mAP50(B)") and r.get("epoch")]
        fig, ax = plt.subplots(figsize=(8, 4.1), layout="constrained")
        for field, label in [("metrics/mAP50(B)", "mAP50"), ("metrics/mAP50-95(B)", "mAP50–95")]:
            ax.plot([int(r["epoch"]) for r in rows], [float(r[field]) for r in rows], label=label)
        ax.set(xlabel="Época", ylabel="Métrica na validação", ylim=(0, 1))
        ax.legend()
        ax.grid(alpha=0.2)
        fig.savefig(out / "video_treino.png", dpi=180)
        plt.close(fig)
    print("Figuras geradas a partir das evidências e do histórico de validação.")


if __name__ == "__main__":
    main()
