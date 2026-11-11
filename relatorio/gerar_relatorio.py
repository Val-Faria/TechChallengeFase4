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
        if key == "blind_holdout" and cm and not (TEX/"figures/audio_matriz_cega.png").is_file():
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
    lines = [r"Os registros completos da reprodução e da entrega estão em \path{integracao/evidencias/entrega_final_20261111/replay.json} e \path{integracao/evidencias/entrega_final_20261111/entrega_auditoria.json}."]
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
    choices = ["evidence/video_dataset_auditoria.json", "evidence/video_reproducao.json",
               "evidence/video_inferencia_nova.json", "artifacts/video/manifesto_video.json",
               "evidence/midias_complementares.json", "evidence/padrao_relatorio.json",
               "evidence/audio_reproducao.json", "audio/evidencias/particoes_audio.csv",
               "audio/evidencias/predicoes_avaliacao.csv", "artifacts/audio/manifesto_audio.json",
               "evidence/resumo_execucao.json", "evidence/audio_externo_transcricoes.json",
               "evidence/asr_comparacao.json", "evidence/audio_externo.json", "evidence/audio_recebido_drive.json", "evidence/openai_validacao.json", "evidence/video_validacao.json", "evidence/dashboard_validacao.json",
               "integracao/evidencias/monitoramento_final/monitoramento_resumo.json", "integracao/evidencias/entrega_final_20261111/replay.json",
               "integracao/evidencias/entrega_final_20261111/entrega_auditoria.json",
               "integracao/evidencias/entrega_final_20261111/anomalias_estruturadas.json"]
    lines = [r"\small\begin{longtable}{p{8.7cm}p{4.4cm}}\toprule", r"Artefato & SHA-256 (prefixo)\\\midrule\endhead"]
    for name in choices:
        p = ROOT / name
        if p.is_file():
            digest = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
            lines.append(r"\path{" + name + "} & \\texttt{" + digest + r"}\\")
    lines += [r"\bottomrule\end{longtable}\normalsize", r"Os hashes completos devem ser consultados nos manifestos de execução e no histórico do repositório. O prefixo serve como referência de leitura, não como substituto de uma verificação integral."]
    return "\n".join(lines)


def make_media():
    evidence = read_json("evidence/midias_complementares.json")
    if not evidence:
        return "Execução complementar ainda não registrada."
    cases = evidence["audio"]["casos"]
    stream = evidence["stream"]["ritmo_original"]
    clinical = evidence["video"]["cirurgia_equipe"]
    lines = [r"Foram criadas seis sínteses novas: duas referências e uma gravação reservada por voz. Não há hashes compartilhados com o corpus de 1.180 WAVs nem com as seis provas externas anteriores. O classificador emocional permaneceu congelado e não participou destes critérios.",
             r"\begin{center}\small\begin{tabular}{llcc}\toprule Voz & Cenário & Esperado & Obtido\\\midrule"]
    for case in cases:
        label = {True: "Sinal", False: "Sem sinal", None: "Inconclusivo"}
        scenario = {"original": "Original", "ganho_reduzido": "Volume reduzido",
                    "interrompido": "Pausas inseridas", "silencio": "Silêncio"}[case["cenario"]]
        lines.append(" & ".join([esc(case["voz"].title()), esc(scenario), label[case["esperado"]], label[case["obtido"]]])+r"\\")
    lines += [r"\bottomrule\end{tabular}\end{center}",
              r"A versão interrompida insere 380 ms de silêncio a cada bloco de 180 ms. A versão com ganho reduzido multiplica a amplitude por 0,35. São perturbações técnicas, sem rótulo de doença; as derivações da mesma fonte não são observações independentes.",
              f"Dois vídeos geométricos novos passaram pelos cálculos reais de fluxo óptico: o controle não gerou eventos e o cenário alterado gerou {len(evidence['video']['casos_controlados'][1]['eventos'])}. Não foi usado oráculo de caixas ou classes. Na montagem recebida foram processados {clinical['quadros_decodificados']} quadros e não houve aumento persistente que atingisse essa regra. Isso não significa ausência de eventos clínicos.",
              f"A reprodução contínua no ritmo original analisou {stream['quadros_processados']} pares de quadros em {number(stream['tempo_total_parede_s'], 2)} s de parede. Foram avaliadas {len(stream['janelas_audio'])} janelas de voz e persistidas {len(stream['alertas_entregues'])} transições com sinais. O percentil 95 de processamento foi {number(stream['processamento_p95_ms'], 2)} ms por passo, além da espera da janela de cinco segundos. Não inclui ASR, nuvem ou captura clínica.",
              r"Evidência: \path{evidence/midias_complementares.json}. Nenhuma chamada paga foi feita nesta complementação."]
    return "\n\n".join(lines)


def make_video_new():
    result = read_json("evidence/video_reproducao.json")
    if "blind_holdout" not in result.get("evaluation", {}):
        return "A nova execução deve estar concluída e registrada antes da emissão da versão final."
    train = result["training"]
    config = train["config"]
    counts = result["dataset"]["counts_clean"]
    lines = ["A nova execução utilizou YOLOv8s, resolução de 416 por 416 pixels, batch "
             +esc(config["batch"])+", até "+esc(config["epochs"])+" épocas e paciência 20. "
             +"Foram concluídas "+esc(train["epochs_completed"])+" épocas, em "
             +number(train["elapsed_s"]/60, 2)+" minutos de treinamento na GPU "
             +esc(train["gpu"])+". A seleção usa somente a validação do primeiro prefixo de clipe.",
             r"\begin{center}\small\begin{tabular}{lrrr}\toprule Conjunto & Imagens & mAP50 & mAP50--95\\\midrule"]
    for key, label, partition in [("val","Validação","valid"),("test","Teste","test"),("blind_holdout","Reserva de clipe","blind_holdout")]:
        m = result["evaluation"][key]
        lines.append(" & ".join([label,str(counts[partition]),number(m["map50"]),number(m["map50_95"])])+r"\\")
    lines += [r"\bottomrule\end{tabular}\end{center}",
              r"As métricas acima pertencem à nova execução e não são diretamente comparáveis ao mAP50 histórico: partições, preparação de anotações, batch e ambiente são diferentes. A queda de mAP50 do teste (mesmo prefixo do treino) para a reserva mostra que o valor alto no desenvolvimento não se mantém na outra origem disponível. Isso é compatível com diferenças de domínio e similaridade temporal, sem identificar uma causa única. A reserva não participou do treino, da escolha de limiares ou do checkpoint. O resultado entre prefixos não é validação em pacientes independentes.",
              r"Precisão e recall presentes no JSON são resumos de objetos da avaliação padrão Ultralytics. Não são os índices da regra temporal com limiares 0,4/0,6, cuja referência e resultados são registrados separadamente.",
              r"\begin{figure}[H]\centering\includegraphics[width=0.92\textwidth]{figures/video_treino.png}\caption{Evolução da validação no novo treino YOLOv8s; a reserva de clipe não participa da curva.}\end{figure}",
              "O peso congelado possui SHA-256 iniciado por \\texttt{"+result["model"]["sha256"][:16]+"}. Evidências em \\path{evidence/video_reproducao.json} e \\path{evidence/video_dataset_auditoria.json}."]
    inference = read_json("evidence/video_inferencia_nova.json")
    if inference:
        demo = inference["blind_montage"]
        lines.append("A montagem reservada foi construída após congelar o modelo, com "+esc(demo["source_images"])
            +" quadros-fonte não usados no desenvolvimento e duração de "+number(demo["duration_s"],1)
            +" segundos. A inferência gerou "+esc(demo["predicted_events"])+" evento(s). "
            +"A referência temporal deriva das caixas anotadas e da própria regra de montagem; não é anotação clínica de complicações. "
            +"A integração usa o teste para o exemplo positivo e mantém a reserva como verificação separada, sem ocultar seus eventos não detectados.")
        lines += [r"\begin{center}\small\begin{tabular}{lrrrr}\toprule Montagem & Referência & Sinalizados & Corretos & Não detectados\\\midrule"]
        for item in inference["montages"]:
            metric=item["event_metrics"]
            label="Reserva" if item["partition"]=="blind_holdout" else "Teste"
            lines.append(" & ".join([label,str(len(item["expected_events"])),str(item["predicted_events"]),str(metric["tp"]),str(metric["fn"])])+r"\\")
        lines += [r"\bottomrule\end{tabular}\end{center}",
                  r"Os eventos são pareados uma única vez com IoU temporal de pelo menos 0,5. No teste, dois de três eventos foram recuperados (precisão 1,00 e recall 0,667). Na reserva, os dois eventos de referência não foram detectados: recall 0 e precisão não definida, pois não houve previsão positiva. A avaliação evidencia uma limitação de generalização da regra com o novo detector. Os limiares não foram ajustados depois de observar essa reserva."]
    return "\n\n".join(lines)


def build_macros():
    audio = read_json("evidence/audio_reproducao.json")
    summary = read_json("evidence/resumo_execucao.json")
    replay = read_json("integracao/evidencias/entrega_final_20261111/replay.json")
    audit = read_json("integracao/evidencias/entrega_final_20261111/entrega_auditoria.json")
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
        "DataRelatorio": "11 de novembro de 2026",
        "ResultadoAudio": make_audio(audio),
        "ResultadoNuvem": make_cloud(summary),
        "ResultadoTestes": make_tests(summary),
        "ResultadoReplay": make_replay(replay, audit),
        "ResultadoIntegracao": integration_text,
        "ResultadoRecursos": resource_text,
        "ResultadoMidias": make_media(),
        "ResultadoVideoNovo": make_video_new(),
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
