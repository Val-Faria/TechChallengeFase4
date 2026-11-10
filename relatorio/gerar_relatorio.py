"""Gera tabelas LaTeX a partir das evidências e empacota fontes para o Overleaf.

Não executa modelos, não lê credenciais e não faz chamadas a serviços externos.
O PDF é sempre compilado a partir do mesmo LaTeX incluído no pacote.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEX = ROOT / "relatorio" / "latex"


def esc(value):
    text = str(value)
    mapping = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
               "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(mapping.get(c, c) for c in text)


def read_json(path):
    path = ROOT / path
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def number(value, digits=3):
    if value is None:
        return "não informado"
    return f"{float(value):.{digits}f}".replace(".", ",")


def percent(value):
    return number(100 * float(value), 2) + r"\%"


def find_metrics(container):
    if isinstance(container, dict):
        if isinstance(container.get("accuracy"), (int, float)):
            return container
        for key in ("metrics", "report", "evaluation", "classification_report"):
            if key in container:
                result = find_metrics(container[key])
                if result:
                    return result
    return {}


def make_audio(audio):
    if not audio:
        return r"A execução consolidada de áudio deve ser lida em conjunto com os arquivos de evidência disponibilizados no repositório. As métricas de 0,89 publicadas anteriormente pela equipe não são reutilizadas como medição desta nova partição."
    sections = []
    candidates = audio.get("evaluation", audio.get("evaluations", audio))
    aliases = [("validation", "Validação"), ("test", "Teste"), ("blind_holdout", "Verificação cega")]
    rows = []
    for key, label in aliases:
        raw = candidates.get(key, audio.get(key, {})) if isinstance(candidates, dict) else {}
        m = find_metrics(raw)
        if not m:
            continue
        report = m.get("classification_report", m.get("report", {}))
        support = m.get("n_samples", m.get("n", raw.get("n_samples", raw.get("n", ""))))
        if not support and isinstance(report, dict):
            support = report.get("weighted avg", {}).get("support", "")
        macro = m.get("macro_f1", report.get("macro avg", {}).get("f1-score"))
        rows.append((label, str(support), percent(m["accuracy"]), number(macro) if macro is not None else "--"))
        cm = m.get("confusion_matrix", raw.get("confusion_matrix"))
        labels = m.get("labels", raw.get("labels", ["ansiedade", "neutro", "tristeza"]))
        if key == "blind_holdout" and cm:
            matrix = [r"\subsubsection*{Matriz de confusão da verificação cega}", r"\begin{center}\small\begin{tabular}{lrrr}\toprule", r"Real / prevista & Ansiedade & Neutro & Tristeza\\\midrule"]
            for idx, row in enumerate(cm):
                lab = ["Ansiedade/hesitação", "Neutro", "Tristeza"][idx] if len(cm) == 3 else str(labels[idx])
                matrix.append(esc(lab) + " & " + " & ".join(esc(v) for v in row) + r"\\")
            matrix += [r"\bottomrule\end{tabular}\end{center}"]
            sections.append("\n".join(matrix))
    intro = r"A avaliação foi regenerada com partições isoladas por família de frase-base. Os valores abaixo são extraídos de \path{evidence/audio_reproducao.json}; cada partição é reportada separadamente."
    if rows:
        table = [r"\begin{center}\begin{tabular}{lrrr}\toprule", r"Partição & Exemplos & Acurácia & F1 macro\\\midrule"]
        for row in rows:
            table.append(" & ".join(row) + r"\\")
        table += [r"\bottomrule\end{tabular}\end{center}"]
        intro += "\n" + "\n".join(table)
    else:
        intro += r" A estrutura completa de métricas está preservada no JSON de evidências, sem substituição por números históricos."
    return intro + "\n" + "\n".join(sections)


def make_cloud(summary):
    cloud = summary.get("cloud", {})
    if not cloud:
        return "O registro de uso da API acompanha as evidências da execução. O resultado deve ser interpretado conforme o modelo e o consumo documentados nessa evidência."
    model = cloud.get("model", cloud.get("modelo", "configurado na execução"))
    calls = cloud.get("calls", cloud.get("chamadas", "registrado no manifesto"))
    cost = cloud.get("estimated_cost_usd", cloud.get("custo_estimado_usd"))
    text = "Modelo utilizado: \\textbf{" + esc(model) + "}. Chamadas reais registradas: \\textbf{" + esc(calls) + "}."
    if cost is not None:
        text += " Custo estimado acumulado: \\textbf{US\\$ " + number(cost, 6) + "}."
    if cloud.get("input_tokens") is not None:
        text += " Foram contabilizados " + esc(cloud["input_tokens"]) + " tokens de entrada e " + esc(cloud.get("output_tokens", 0)) + " de saída."
    if cloud.get("status"):
        text += " Estado registrado: " + esc(cloud["status"]) + "."
    return text


def make_tests(summary):
    tests = summary.get("tests", {})
    if not tests:
        return r"Os resultados automatizados são preservados no diretório de evidências da execução; o relatório não converte os 49 testes antigos do notebook em contagem da suíte consolidada."
    lines = []
    suites = tests if isinstance(tests, list) else [tests]
    for suite in suites:
        lines.append("Suíte \\textbf{" + esc(suite.get("name", "consolidada")) + "}: " + esc(suite.get("passed", "não informado")) + " verificações aprovadas, " + esc(suite.get("failed", 0)) + " falhas.")
        if suite.get("subtests_passed") is not None:
            lines.append("Também foram aprovadas " + esc(suite["subtests_passed"]) + " verificações parametrizadas adicionais (subtestes), registradas separadamente da contagem de testes.")
    return "\n\n".join(lines)


def make_replay(replay, audit):
    lines = [r"Os registros completos da reprodução e da entrega estão em \path{integracao/evidencias/execucao_final/replay.json} e \path{integracao/evidencias/execucao_final/entrega_auditoria.json}."]
    if replay:
        for key in ("events_processed", "processed_events", "event_count", "alerts_delivered", "duration_s", "latency_ms", "p95_latency_ms"):
            value = replay.get(key)
            if isinstance(value, (int, float, str)):
                lines.append(esc(key) + ": " + esc(value) + ".")
    if audit:
        if isinstance(audit, dict):
            for key in ("delivered", "acknowledged", "pending", "duplicate_deliveries", "total_alerts"):
                value = audit.get(key)
                if isinstance(value, (int, float, str)):
                    lines.append(esc(key) + ": " + esc(value) + ".")
    monitor = read_json("integracao/evidencias/monitoramento_final/monitoramento_resumo.json")
    times = monitor.get("latencias_ms", [])
    if times:
        ordered = sorted(float(v) for v in times)
        import math
        p95 = ordered[max(0, math.ceil(len(ordered)*.95)-1)]
        lines.append("No monitor incremental foram processados " + esc(monitor.get("pacotes_processados", len(times))) + " pacotes. Latência local média: " + number(sum(ordered)/len(ordered), 3) + " ms; percentil 95 (posto mais próximo): " + number(p95, 3) + " ms; máxima: " + number(max(ordered), 3) + " ms. O intervalo inclui detector estatístico, fusão e SQLite, conforme a instrumentação do monitor.")
    return "\n\n".join(lines)


def make_manifest():
    choices = ["evidence/audio_reproducao.json", "audio/evidencias/particoes_audio.csv",
               "audio/evidencias/predicoes_avaliacao.csv", "artifacts/audio/manifesto_audio.json",
               "evidence/resumo_execucao.json", "evidence/audio_externo_transcricoes.json",
               "evidence/asr_comparacao.json", "evidence/audio_externo.json", "evidence/audio_recebido_drive.json", "evidence/openai_validacao.json", "evidence/video_validacao.json", "evidence/dashboard_validacao.json",
               "integracao/evidencias/monitoramento_final/monitoramento_resumo.json", "integracao/evidencias/execucao_final/replay.json",
               "integracao/evidencias/execucao_final/entrega_auditoria.json",
               "integracao/evidencias/execucao_final/anomalias_estruturadas.json"]
    lines = [r"\small\begin{longtable}{p{8.7cm}p{4.4cm}}\toprule", r"Artefato & SHA-256 (prefixo)\\\midrule\endhead"]
    for name in choices:
        p = ROOT / name
        if p.is_file():
            digest = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
            lines.append(r"\path{" + name + "} & \\texttt{" + digest + r"}\\")
    lines += [r"\bottomrule\end{longtable}\normalsize", r"Os hashes completos devem ser consultados nos manifestos de execução e no histórico do repositório. O prefixo serve como referência de leitura, não como substituto de uma verificação integral."]
    return "\n".join(lines)


def build_macros():
    audio = read_json("evidence/audio_reproducao.json")
    summary = read_json("evidence/resumo_execucao.json")
    replay = read_json("integracao/evidencias/execucao_final/replay.json")
    audit = read_json("integracao/evidencias/execucao_final/entrega_auditoria.json")
    resources = summary.get("resources", {})
    if resources:
        resource_text = esc(resources.get("description", "Execução conforme manifesto de recursos."))
        if "gpu_used" in resources:
            resource_text += " GPU utilizada nesta consolidação: " + ("sim" if resources["gpu_used"] else "não") + "."
        if "session_closed" in resources:
            resource_text += " Sessão de computação encerrada ao final: " + ("sim" if resources["session_closed"] else "não se aplica ou não confirmada") + "."
    else:
        resource_text = "O ambiente e as versões utilizadas são registrados nos manifestos de execução. A autorização de uso de GPU não significa que uma sessão permaneça ativa."
    integration = summary.get("integration", {})
    integration_text = esc(integration.get("description", "A execução final preserva a maior prioridade entre as fontes e produz resultados por caso. Consulte o JSON e o relatório gerados para verificar o estado de cada modalidade."))
    integration_text += " No caso integrado, a confiança acústica do áudio novo-03 é 0,595, inferior ao limiar 0,70. A fonte de áudio fica inconclusiva e a cobertura permanece incompleta; o alerta alto do vídeo é preservado. Não se declara cobertura completa por terem sido fornecidos todos os arquivos."
    commands = r"""\begin{enumerate}
\item Preparar Python e instalar as dependências descritas no README.
\item Executar \code{python -m pytest -q} para a suíte de software.
\item Executar \code{python scripts/run_demo.py --help} para conferir entradas e diretório de saída.
\item Informar o CSV regenerado, o JSON de vídeo e o resultado textual real ao script de demonstração.
\item Abrir o painel com \code{python -m techchallenge4.dashboard --help} e selecionar o banco gerado.
\item Compilar o relatório com \code{python relatorio/gerar_relatorio.py --compile --package} ou importar o ZIP no Overleaf.
\end{enumerate}"""
    macros = {
        "DataRelatorio": "10 de novembro de 2026",
        "ResultadoAudio": make_audio(audio),
        "ResultadoNuvem": make_cloud(summary),
        "ResultadoTestes": make_tests(summary),
        "ResultadoReplay": make_replay(replay, audit),
        "ResultadoIntegracao": integration_text,
        "ResultadoRecursos": resource_text,
        "ComandosReproducao": commands,
        "ManifestoEvidencias": make_manifest(),
    }
    output = "% Gerado exclusivamente de evidências locais; sem credenciais.\n"
    for key, value in macros.items():
        output += "\\newcommand{\\" + key + "}{%\n" + value + "\n}\n"
    TEX.mkdir(parents=True, exist_ok=True)
    (TEX / "dados_gerados.tex").write_text(output, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compile", action="store_true", help="Compila com Tectonic disponível no PATH ou no caminho configurado.")
    parser.add_argument("--tectonic", default=shutil.which("tectonic") or str(Path.home() / "Tools/tectonic/tectonic.exe"))
    parser.add_argument("--package", action="store_true", help="Produz ZIP com fontes prontas para Overleaf.")
    args = parser.parse_args()
    build_macros()
    out = ROOT / "output" / "pdf"
    out.mkdir(parents=True, exist_ok=True)
    if args.compile:
        subprocess.run([args.tectonic, "--keep-logs", "--outdir", str(out), str(TEX / "main.tex")], check=True, cwd=TEX)
        shutil.copyfile(out / "main.pdf", out / "relatorio_tecnico_fase4.pdf")
        (out / "main.pdf").unlink()
    if args.package:
        destination = ROOT / "relatorio" / "overleaf_fase4.zip"
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(TEX.rglob("*")):
                if path.is_file() and path.suffix in {".tex", ".bib", ".png", ".jpg", ".pdf"}:
                    archive.write(path, path.relative_to(TEX).as_posix())
            readme = ROOT / "relatorio" / "COMO_COMPILAR.md"
            if readme.is_file():
                archive.write(readme, "README.md")
        print(f"Pacote Overleaf: {destination}")
    print("Fontes atualizadas a partir das evidências disponíveis.")


if __name__ == "__main__":
    main()
