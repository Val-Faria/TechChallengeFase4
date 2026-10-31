"""
Alerta de vídeo cirúrgico — Tech Challenge Fase 4.

Roda o YOLOv8 treinado (classes Tools e Uterus) num vídeo e procura trechos
em que há instrumento em cena, mas o útero não está visível.

Uso:
    from alerta_video import analisar_video
    resultado = analisar_video("cirurgia.mp4", "best.pt")

O resultado é um sinal de triagem para revisão da equipe médica, não um diagnóstico.
"""
import json
from pathlib import Path

import cv2
from ultralytics import YOLO

AVISO = "Sinal de triagem para revisão da equipe médica. Não constitui diagnóstico."


def detectar_eventos(quadros, passo_s, min_perda_s=5, tolerancia_s=1):
    """Encontra trechos com instrumento e sem útero por pelo menos `min_perda_s` segundos.

    quadros: lista de (segundo, tem_instrumento, tem_utero, confianca_instrumento).
    Falhas de detecção de até `tolerancia_s` segundos não interrompem o trecho.
    """
    eventos, inicio, ultimo, confs = [], None, None, []
    fim_do_video = (float("inf"), False, True, 0)  # força o fechamento do último trecho

    for t, instrumento, utero, conf in quadros + [fim_do_video]:
        if instrumento and not utero:
            if inicio is None:
                inicio, confs = t, []
            ultimo = t
            confs.append(conf)
        elif inicio is not None and t - ultimo > tolerancia_s:
            fim = ultimo + passo_s
            if fim - inicio >= min_perda_s:
                eventos.append({
                    "descricao": f"Instrumento em cena sem visualização do útero por {fim - inicio:.1f} s",
                    "inicio_s": round(inicio, 1),
                    "fim_s": round(fim, 1),
                    "duracao_s": round(fim - inicio, 1),
                    "confianca": round(sum(confs) / len(confs), 2),
                })
            inicio = None
    return eventos


def nivel_do_alerta(eventos, min_perda_s=5):
    if not eventos:
        return "nenhum"
    maior = max(e["duracao_s"] for e in eventos)
    if maior >= 3 * min_perda_s or len(eventos) >= 3:
        return "alto"
    return "medio" if maior >= 2 * min_perda_s else "baixo"


def analisar_video(video, pesos, saida="saida_video", conf=0.4, conf_area=0.6,
                   amostra_fps=5, min_perda_s=5, tolerancia_s=1,
                   salvar_video=True, modelo=None):
    """Analisa o vídeo e devolve o `resultado_video` (chave principal: "alerta").

    conf:      confiança mínima para o instrumento.
    conf_area: confiança mínima para o útero. Mais alta que `conf` para que
               detecções fracas de útero ("útero fantasma") não escondam um evento.
               0,6 foi escolhido no conjunto de validação.
    """
    modelo = modelo or YOLO(pesos)
    ids = {nome: i for i, nome in modelo.names.items()}
    id_instr, id_utero = ids["Tools"], ids["Uterus"]

    pasta = Path(saida)
    pasta.mkdir(parents=True, exist_ok=True)
    nome = Path(video).stem

    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    passo = max(1, round(fps / amostra_fps))   # analisa 1 a cada `passo` quadros
    gravador, quadros, n = None, [], 0

    # 1) Detecta instrumento e útero nos quadros amostrados
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if n % passo == 0:
            r = modelo.predict(frame, conf=min(conf, conf_area), verbose=False)[0]
            deteccoes = list(zip(r.boxes.cls.tolist(), r.boxes.conf.tolist()))
            conf_instr = [c for k, c in deteccoes if k == id_instr and c >= conf]
            tem_utero = any(k == id_utero and c >= conf_area for k, c in deteccoes)
            quadros.append((n / fps, bool(conf_instr), tem_utero, max(conf_instr, default=0)))

            if salvar_video:
                imagem = r.plot()
                if conf_instr and not tem_utero:
                    cv2.putText(imagem, "UTERO FORA DE VISTA", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                if gravador is None:
                    h, w = imagem.shape[:2]
                    gravador = cv2.VideoWriter(str(pasta / f"{nome}_anotado.mp4"),
                                               cv2.VideoWriter_fourcc(*"mp4v"), amostra_fps, (w, h))
                gravador.write(imagem)
        n += 1
    if gravador:
        gravador.release()

    # 2) Aplica a regra temporal
    eventos = detectar_eventos(quadros, passo / fps, min_perda_s, tolerancia_s)

    # 3) Salva a imagem do meio de cada evento
    for i, e in enumerate(eventos, 1):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int((e["inicio_s"] + e["fim_s"]) / 2 * fps))
        ok, frame = cap.read()
        if ok:
            e["quadro"] = str(pasta / f"{nome}_evento{i}.jpg")
            cv2.imwrite(e["quadro"], modelo.predict(frame, conf=conf, verbose=False)[0].plot())
    cap.release()

    total = len(quadros) or 1
    resultado = {
        "alerta": bool(eventos),
        "nivel": nivel_do_alerta(eventos, min_perda_s),
        "motivo": (f"{len(eventos)} trecho(s) com instrumento ativo e útero fora de vista"
                   if eventos else "Nenhuma anomalia detectada"),
        "eventos": eventos,
        "estatisticas": {
            "duracao_video_s": round(n / fps, 1),
            "quadros_analisados": len(quadros),
            "prop_quadros_com_utero": round(sum(q[2] for q in quadros) / total, 3),
            "prop_quadros_com_instrumento": round(sum(q[1] for q in quadros) / total, 3),
            "prop_instrumento_sem_utero": round(sum(q[1] and not q[2] for q in quadros) / total, 3),
        },
        "parametros": {"conf": conf, "conf_area": conf_area, "min_perda_s": min_perda_s},
        "video": str(video),
        "video_anotado": str(pasta / f"{nome}_anotado.mp4") if salvar_video else None,
        "aviso": AVISO,
    }
    resultado["relatorio"] = gerar_relatorio(resultado, pasta / f"relatorio_{nome}.md")
    (pasta / f"resultado_{nome}.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    return resultado


def gerar_relatorio(res, caminho):
    """Relatório automático em Markdown para cada vídeo analisado."""
    est, par = res["estatisticas"], res["parametros"]
    linhas = [
        "# Relatório automático de vídeo cirúrgico",
        "",
        f"**Vídeo:** `{Path(res['video']).name}`  ",
        f"**Resultado:** alerta {res['nivel'].upper()} — {res['motivo']}",
        "",
        "## Resumo",
        f"- Duração: {est['duracao_video_s']} s ({est['quadros_analisados']} quadros analisados)",
        f"- Útero visível: {est['prop_quadros_com_utero']:.0%} dos quadros",
        f"- Instrumento em cena: {est['prop_quadros_com_instrumento']:.0%} dos quadros",
        f"- Instrumento sem útero visível: {est['prop_instrumento_sem_utero']:.0%} dos quadros",
        "",
        "## Eventos",
    ]
    if not res["eventos"]:
        linhas.append("Nenhum trecho atingiu o critério de alerta.")
    for i, e in enumerate(res["eventos"], 1):
        linhas.append(f"{i}. {e['inicio_s']} s a {e['fim_s']} s — {e['descricao']} "
                      f"(confiança média {e['confianca']})")
        if "quadro" in e:
            linhas.append(f"\n   ![Evento {i}]({Path(e['quadro']).name})\n")
    linhas += [
        "",
        "## Critério",
        f"Alerta quando há instrumento (confiança ≥ {par['conf']}) e o útero não é visto "
        f"(confiança ≥ {par['conf_area']}) por pelo menos {par['min_perda_s']} s seguidos.",
        "",
        f"> {AVISO}",
    ]
    Path(caminho).write_text("\n".join(linhas), encoding="utf-8")
    return str(caminho)
