"""Inferência YOLO e regra temporal observacional com pesos fornecidos.

Modelo injetado destina-se a testes de software e não mede qualidade do detector.
"""

import json
import math
import statistics
from pathlib import Path

AVISO = "Sinal de triagem para revisão da equipe médica. Não constitui diagnóstico."


def numero_finito(valor, nome, minimo=None, maximo=None):
    if isinstance(valor, bool):
        raise ValueError(f"{nome}: esperado número")
    numero = float(valor)
    if (
        not math.isfinite(numero)
        or (minimo is not None and numero < minimo)
        or (maximo is not None and numero > maximo)
    ):
        raise ValueError(f"{nome}: valor fora do intervalo permitido")
    return numero


def detectar_eventos(
    quadros, passo_s, min_perda_s=5, tolerancia_s=1, duracao_video=None, quadros_invalidos=()
):
    """Agrupa a condição visual no tempo; quadros inválidos interrompem o trecho sem tolerância."""
    passo_s = numero_finito(passo_s, "passo_s", 1e-9)
    min_perda_s = numero_finito(min_perda_s, "min_perda_s", 1e-9)
    tolerancia_s = numero_finito(tolerancia_s, "tolerancia_s", 0)
    if duracao_video is not None:
        duracao_video = numero_finito(duracao_video, "duracao_video", 0)
    invalidos = {numero_finito(t, "quadro_invalido", 0) for t in quadros_invalidos}
    eventos, inicio, ultimo, confs = [], None, None, []

    def fechar():
        if inicio is None:
            return
        fim = ultimo + passo_s
        if duracao_video is not None:
            fim = min(fim, duracao_video)
        if fim - inicio + 1e-8 >= min_perda_s:
            eventos.append(
                {
                    "descricao": "Instrumento em cena sem visualização do útero",
                    "inicio_s": round(inicio, 3),
                    "fim_s": round(fim, 3),
                    "duracao_s": round(fim - inicio, 3),
                    "confianca": round(statistics.mean(confs), 3),
                }
            )

    anterior = -1.0
    for t, instrumento, utero, conf in quadros:
        t = numero_finito(t, "instante", 0)
        if type(instrumento) is not bool or type(utero) is not bool:
            raise ValueError("Presença de classes deve ser booleana.")
        conf = numero_finito(conf, "confianca_instrumento", 0, 1)
        if duracao_video is not None and t >= duracao_video:
            raise ValueError("Instante fora da duração do vídeo.")
        if t <= anterior:
            raise ValueError("Quadros precisam estar em ordem temporal estrita.")
        anterior = t
        if t in invalidos:
            fechar()
            inicio, ultimo, confs = None, None, []
            continue
        # Não une segmentos separados por uma lacuna de amostragem grande.
        if inicio is not None and t - ultimo > tolerancia_s + passo_s + 1e-8:
            fechar()
            inicio, ultimo, confs = None, None, []
        if instrumento and not utero:
            if inicio is None:
                inicio = t
            ultimo = t
            confs.append(numero_finito(conf, "confianca_instrumento", 0, 1))
        elif inicio is not None and t - ultimo > tolerancia_s + 1e-8:
            fechar()
            inicio, ultimo, confs = None, None, []
    fechar()
    return eventos


def nivel_do_alerta(eventos, min_perda_s=5):
    """Atribui prioridade pela duração e quantidade de eventos, conforme a regra do experimento."""
    if not eventos:
        return "nenhum"
    maior = max(e["duracao_s"] for e in eventos)
    if maior >= 3 * min_perda_s or len(eventos) >= 3:
        return "alto"
    return "medio" if maior >= 2 * min_perda_s else "baixo"


def analisar_video(
    video,
    pesos,
    saida=None,
    conf=0.4,
    conf_area=0.6,
    amostra_fps=5,
    min_perda_s=5,
    tolerancia_s=1,
    salvar_video=True,
    modelo=None,
    imgsz=416,
    cobertura_parcial=False,
    limitacoes=None,
    referencia_visual=None,
):
    """Executa o detector nos quadros válidos e exporta eventos, vídeo e relatório observacionais."""
    import cv2

    if type(cobertura_parcial) is not bool:
        raise ValueError("cobertura_parcial deve ser booleana.")
    if limitacoes is not None and (
        not isinstance(limitacoes, list)
        or any(not isinstance(v, str) or not v.strip() for v in limitacoes)
    ):
        raise ValueError("limitacoes deve ser uma lista de textos.")
    if referencia_visual is not None:
        from qualidade import compativel, extrair_caracteristicas

        # Falhar antes de ler o vídeo se a referência estiver incompleta.
        compativel(
            {"warm_fraction": 0.5, "red_blue_difference": 0.2},
            referencia_visual["reference"],
            referencia_visual["threshold"],
        )
    for nome, v in (("conf", conf), ("conf_area", conf_area)):
        numero_finito(v, nome, 0, 1)
    numero_finito(amostra_fps, "amostra_fps", 1e-9)
    numero_finito(min_perda_s, "min_perda_s", 1e-9)
    numero_finito(tolerancia_s, "tolerancia_s", 0)
    if type(imgsz) is not int or imgsz < 32 or imgsz % 32:
        raise ValueError("imgsz deve ser inteiro positivo múltiplo de 32.")
    pasta = Path(saida or "saida_video")
    pasta.mkdir(parents=True, exist_ok=True)
    if not Path(video).is_file() or (
        modelo is None and (pesos is None or not Path(pesos).is_file())
    ):
        raise FileNotFoundError("Forneça vídeo e pesos treinados nos caminhos configurados.")
    if modelo is None:
        from ultralytics import YOLO

        modelo = YOLO(str(pesos))
    nomes = dict(enumerate(modelo.names)) if isinstance(modelo.names, list) else modelo.names
    ids = {nome: i for i, nome in nomes.items()}
    if not {"Tools", "Uterus"}.issubset(ids):
        raise ValueError("Os pesos precisam conter as classes Tools e Uterus.")
    cap = cv2.VideoCapture(str(video))
    gravador = None
    quadros, n = [], 0
    invalidos = set()
    anotado = pasta / f"{Path(video).stem}_anotado.mp4"
    try:
        if not cap.isOpened():
            raise ValueError("Não foi possível abrir o vídeo.")
        fps = numero_finito(cap.get(cv2.CAP_PROP_FPS), "fps", 1e-9)
        passo = max(1, round(fps / amostra_fps))
        fps_saida = fps / passo
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if n % passo == 0:
                valido = (
                    referencia_visual is None
                    or compativel(
                        extrair_caracteristicas(frame),
                        referencia_visual["reference"],
                        referencia_visual["threshold"],
                    )[0]
                )
                if valido:
                    r = modelo.predict(
                        frame, conf=min(conf, conf_area), imgsz=imgsz, verbose=False
                    )[0]
                    dets = list(zip(r.boxes.cls.tolist(), r.boxes.conf.tolist()))
                else:
                    invalidos.add(n / fps)
                    dets = []
                instr = [p for k, p in dets if int(k) == ids["Tools"] and p >= conf]
                utero = any(int(k) == ids["Uterus"] and p >= conf_area for k, p in dets)
                quadros.append((n / fps, bool(instr), utero, max(instr, default=0.0)))
                if salvar_video:
                    imagem = r.plot() if valido else frame.copy()
                    if not valido:
                        cv2.putText(
                            imagem,
                            "FORA DA REFERENCIA - REVISAR",
                            (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0, 200, 255),
                            2,
                        )
                    elif instr and not utero:
                        cv2.putText(
                            imagem,
                            "AREA CRITICA NAO DETECTADA",
                            (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0, 0, 255),
                            2,
                        )
                    if gravador is None:
                        h, w = imagem.shape[:2]
                        gravador = cv2.VideoWriter(
                            str(anotado), cv2.VideoWriter_fourcc(*"mp4v"), fps_saida, (w, h)
                        )
                        if not gravador.isOpened():
                            raise ValueError("Codec/gravador de vídeo indisponível.")
                    gravador.write(imagem)
            n += 1
        if not quadros:
            raise ValueError("Nenhum quadro foi decodificado.")
        duracao = n / fps
        eventos = detectar_eventos(
            quadros, passo / fps, min_perda_s, tolerancia_s, duracao, quadros_invalidos=invalidos
        )
        for i, evento in enumerate(eventos, 1):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int((evento["inicio_s"] + evento["fim_s"]) / 2 * fps))
            ok, quadro = cap.read()
            if ok:
                destino = pasta / f"{Path(video).stem}_evento{i}.jpg"
                encoded, data = cv2.imencode(
                    ".jpg", modelo.predict(quadro, conf=conf, imgsz=imgsz, verbose=False)[0].plot()
                )
                if encoded:
                    destino.write_bytes(data.tobytes())
                    evento["quadro"] = str(destino)
        res = {
            "alerta": bool(eventos),
            "nivel": nivel_do_alerta(eventos, min_perda_s),
            "motivo": f"{len(eventos)} trecho(s) com instrumento detectado sem detecção sustentada de útero",
            "eventos": eventos,
            "cobertura_parcial": bool(cobertura_parcial or invalidos),
            "limitacoes": list(limitacoes or [])
            + (
                ["Há quadros fora da referência visual; não interpretados como normais."]
                if invalidos
                else []
            ),
            "interpretacao": "Presença/ausência de detecções pelo modelo; ausência de alerta não confirma normalidade nem ausência de falha clínica.",
            "estatisticas": {
                "duracao_video_s": round(duracao, 3),
                "quadros_analisados": len(quadros),
                "amostra_fps_efetivo": fps_saida,
                "quadros_fora_referencia_visual": len(invalidos),
                "quadros_yolo_processados": len(quadros) - len(invalidos),
                "prop_quadros_com_utero": sum(q[2] for q in quadros) / len(quadros),
                "prop_quadros_com_instrumento": sum(q[1] for q in quadros) / len(quadros),
                "prop_instrumento_sem_utero": sum(q[1] and not q[2] for q in quadros)
                / len(quadros),
            },
            "parametros": {
                "conf": conf,
                "conf_area": conf_area,
                "min_perda_s": min_perda_s,
                "tolerancia_s": tolerancia_s,
                "imgsz": imgsz,
                "filtro_visual_ativo": referencia_visual is not None,
            },
            "video": str(video),
            "video_anotado": str(anotado) if salvar_video else None,
            "aviso": AVISO,
        }
    finally:
        cap.release()
        if gravador is not None:
            gravador.release()
    res["relatorio"] = gerar_relatorio(res, pasta / f"relatorio_{Path(video).stem}.md")
    (pasta / f"resultado_{Path(video).stem}.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
    )
    return res


def gerar_relatorio(res, caminho):
    """Relatório automático em Markdown para cada vídeo analisado."""
    est, par = res["estatisticas"], res["parametros"]
    linhas = [
        "# Relatório automático de vídeo cirúrgico",
        "",
        f"**Vídeo:** `{Path(res['video']).name}`  ",
        f"**Resultado:** alerta {res['nivel'].upper()} — {res['motivo']}",
        "**Interpretação:** "
        + res.get("interpretacao", "Resultado observacional; não constitui diagnóstico."),
        "",
        "## Resumo",
        f"- Duração: {est['duracao_video_s']} s ({est['quadros_analisados']} quadros analisados)",
        f"- Fora da referência visual: {est.get('quadros_fora_referencia_visual', 0)} quadro(s); requer revisão, não normalidade",
        f"- Útero visível: {est['prop_quadros_com_utero']:.0%} dos quadros",
        f"- Instrumento em cena: {est['prop_quadros_com_instrumento']:.0%} dos quadros",
        f"- Instrumento sem útero visível: {est['prop_instrumento_sem_utero']:.0%} dos quadros",
        "",
        "## Eventos",
    ]
    if not res["eventos"]:
        linhas.append("Nenhum trecho atingiu o critério de alerta.")
    for i, e in enumerate(res["eventos"], 1):
        linhas.append(
            f"{i}. {e['inicio_s']} s a {e['fim_s']} s — {e['descricao']} "
            f"(confiança média {e['confianca']})"
        )
        if "quadro" in e:
            linhas.append(f"\n   ![Evento {i}]({Path(e['quadro']).name})\n")
    linhas += [
        "",
        "## Critério",
        f"Alerta quando há instrumento (confiança ≥ {par['conf']}) e o útero não é visto "
        f"(confiança ≥ {par['conf_area']}) por pelo menos {par['min_perda_s']} s, "
        f"com tolerância de {par['tolerancia_s']} s para interrupções curtas.",
        "",
        f"> {AVISO}",
    ]
    if res.get("cobertura_parcial"):
        linhas += [
            "",
            "## Limites e revisão",
            "Cobertura parcial: a ausência de alerta exige revisão do material.",
        ]
        linhas.extend("- " + item for item in res.get("limitacoes", []))
    Path(caminho).write_text("\n".join(linhas), encoding="utf-8")
    return str(caminho)
