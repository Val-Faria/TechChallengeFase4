"""Contratos de integração, preservando a maior prioridade e a origem das evidências.

Os limiares são demonstrativos; nenhuma saída constitui diagnóstico.
"""
from __future__ import annotations
import hashlib
import json
import math
import re
import statistics
from copy import deepcopy
from datetime import datetime, timezone

NIVEIS = {"nenhum": 0, "baixo": 1, "medio": 2, "alto": 3}
CLASSES_AUDIO = {"ansiedade_hesitacao", "neutro", "tristeza"}
STATUS_FONTE = {"ok", "baixa_confianca", "indisponivel", "erro"}
AVISO = "Protótipo acadêmico para revisão humana. Não constitui diagnóstico."

def numero_finito(valor, nome, minimo=None, maximo=None):
    if isinstance(valor, bool):
        raise ValueError(f"{nome}: booleano não é um número válido.")
    x = float(valor)
    if not math.isfinite(x) or (minimo is not None and x < minimo) or (
        maximo is not None and x > maximo
    ):
        raise ValueError(f"{nome}: valor fora do intervalo permitido.")
    return x

def fonte_indisponivel(modalidade, motivo, status="indisponivel", simulado=False):
    return {"modalidade": modalidade, "status": status, "alerta": None,
            "nivel": "nenhum", "motivo": str(motivo), "simulado": bool(simulado)}

def normalizar_audio(resultado, origem="classificar_audio", simulado=False, limiar=0.70):
    if type(simulado) is not bool or (isinstance(resultado, dict)
            and "simulado" in resultado and type(resultado["simulado"]) is not bool):
        raise ValueError("simulado deve ser booleano JSON.")
    if resultado is None:
        return fonte_indisponivel("audio", "Áudio não fornecido.", simulado=simulado)
    if isinstance(resultado, dict):
        simulado = bool(simulado or resultado.get("simulado", False))
    limiar = numero_finito(limiar, "limiar", 0, 1)
    if isinstance(resultado, (tuple, list)) and len(resultado) == 2:
        classe, confianca = resultado
    elif isinstance(resultado, dict):
        if resultado.get("status") in {"erro", "indisponivel"}:
            return fonte_indisponivel("audio", resultado.get("motivo", "Falha no áudio."),
                                     resultado["status"], simulado)
        classe = resultado.get("classe_audio", resultado.get("classe"))
        confianca = resultado.get("confianca_audio", resultado.get("confianca"))
    else:
        raise ValueError("Áudio: use tupla (classe, confiança) ou uma linha do CSV.")
    if classe not in CLASSES_AUDIO:
        raise ValueError(f"Classe de áudio desconhecida: {classe!r}")
    p = numero_finito(confianca, "confianca_audio", 0, 1)
    suficiente = p >= limiar
    sinal = suficiente and classe != "neutro"
    return {"modalidade": "audio", "status": "ok" if suficiente else "baixa_confianca",
            "alerta": bool(sinal), "nivel": "medio" if sinal else "nenhum",
            "classe_audio": classe, "confianca_audio": p, "limiar": limiar,
            "motivo": f"Classe acústica: {classe}; confiança {p:.3f}.",
            "origem": origem, "simulado": bool(simulado)}

def normalizar_video(resultado, origem="analisar_video", simulado=False):
    if type(simulado) is not bool or (isinstance(resultado, dict)
            and "simulado" in resultado and type(resultado["simulado"]) is not bool):
        raise ValueError("simulado deve ser booleano JSON.")
    if resultado is None:
        return fonte_indisponivel("video", "Vídeo não fornecido.", simulado=simulado)
    if not isinstance(resultado, dict):
        raise ValueError("Vídeo: esperado um dicionário JSON.")
    simulado = bool(simulado or resultado.get("simulado", False))
    if resultado.get("status") in {"erro", "indisponivel"}:
        return fonte_indisponivel("video", resultado.get("motivo", "Falha no vídeo."),
                                 resultado["status"], simulado)
    if resultado.get("status") == "baixa_confianca":
        return fonte_indisponivel("video", resultado.get("motivo", "Vídeo sem confiança suficiente."),
                                 "baixa_confianca", simulado)
    if resultado.get("status", "ok") != "ok":
        raise ValueError("Vídeo: status desconhecido.")
    alerta = resultado.get("alerta")
    if type(alerta) is not bool:
        raise ValueError("Vídeo: 'alerta' deve ser booleano JSON, nunca 'true' como texto.")
    nivel = resultado.get("nivel", "baixo" if alerta else "nenhum")
    if nivel not in NIVEIS or (alerta and nivel == "nenhum") or (
        not alerta and nivel != "nenhum"
    ):
        raise ValueError("Vídeo: alerta e nível são inconsistentes.")
    eventos = resultado.get("eventos", [])
    if not isinstance(eventos, list):
        raise ValueError("Vídeo: eventos deve ser uma lista.")
    for e in eventos:
        inicio = numero_finito(e["inicio_s"], "inicio_s", 0)
        fim = numero_finito(e["fim_s"], "fim_s", 0)
        if fim <= inicio:
            raise ValueError("Vídeo: evento com intervalo inválido.")
        if "duracao_s" in e and abs(numero_finito(e["duracao_s"], "duracao_s", 0) - (fim-inicio)) > 0.21:
            raise ValueError("Vídeo: duração inconsistente.")
        if "confianca" in e:
            numero_finito(e["confianca"], "confianca", 0, 1)
    if eventos and not alerta:
        raise ValueError("Vídeo: há eventos, mas alerta está desativado.")
    parcial = resultado.get("cobertura_parcial", False)
    if type(parcial) is not bool:
        raise ValueError("Vídeo: cobertura_parcial deve ser booleano JSON.")
    limitacoes = resultado.get("limitacoes", [])
    if not isinstance(limitacoes, list) or any(not isinstance(v, str) or not v.strip() for v in limitacoes):
        raise ValueError("Vídeo: limitações devem ser uma lista de textos.")
    return {"modalidade": "video", "status": "ok", "alerta": alerta, "nivel": nivel,
            "motivo": str(resultado.get("motivo", "Resultado de vídeo recebido.")),
            "eventos": deepcopy(eventos), "estatisticas": deepcopy(resultado.get("estatisticas", {})),
            "cobertura_parcial": parcial, "limitacoes": list(limitacoes),
            "interpretacao": str(resultado.get("interpretacao", "Resultado observacional; não exclui anomalias clínicas.")),
            "parametros": deepcopy(resultado.get("parametros", {})),
            "origem": origem, "simulado": bool(simulado)}

def validar_fonte(fonte):
    if (not isinstance(fonte, dict) or not isinstance(fonte.get("modalidade"), str)
            or not fonte["modalidade"].strip() or not isinstance(fonte.get("motivo"), str)):
        raise ValueError("Fonte adicional inválida.")
    for campo in ("simulado", "cobertura_parcial"):
        if campo in fonte and type(fonte[campo]) is not bool:
            raise ValueError(f"{campo} deve ser booleano JSON.")
    if fonte.get("status") not in STATUS_FONTE or fonte.get("nivel") not in NIVEIS:
        raise ValueError("Fonte adicional com status ou nível inválido.")
    if fonte["status"] == "ok":
        if type(fonte.get("alerta")) is not bool:
            raise ValueError("Fonte disponível exige alerta booleano.")
        if fonte["alerta"] != (fonte["nivel"] != "nenhum"):
            raise ValueError("Fonte adicional com alerta e nível inconsistentes.")
    elif fonte.get("alerta") not in (None, False) or fonte["nivel"] != "nenhum":
        raise ValueError("Fonte inconclusiva não deve fornecer sinal negativo conclusivo ou positivo.")
    return deepcopy(fonte)

def combinar_audio_video(resultado_audio, resultado_video, *, id_caso,
                         origem_audio="classificar_audio", origem_video="analisar_video",
                         simulado=False, pareamento="associacao_manual_por_caso",
                         fontes_adicionais=None, fontes_esperadas=("audio", "video")):
    if not isinstance(id_caso, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", id_caso):
        raise ValueError("Use id_caso com 1 a 80 letras, números, '_' ou '-'.")
    if not isinstance(pareamento, str) or not pareamento.strip():
        raise ValueError("Descreva o pareamento dos arquivos.")
    fontes = [
        normalizar_audio(resultado_audio, origem_audio, simulado),
        normalizar_video(resultado_video, origem_video, simulado),
    ] + [validar_fonte(f) for f in (fontes_adicionais or [])]
    return fundir_fontes_normalizadas(fontes, id_caso=id_caso, pareamento=pareamento,
                                     fontes_esperadas=fontes_esperadas, simulado=simulado)


def fundir_fontes_normalizadas(fontes, *, id_caso, pareamento,
                              fontes_esperadas=("audio", "video"), simulado=False):
    if not isinstance(id_caso, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", id_caso):
        raise ValueError("Identificador de caso inválido.")
    if not isinstance(pareamento, str) or not pareamento.strip():
        raise ValueError("Descreva a associação entre fontes.")
    fontes = [validar_fonte(fonte) for fonte in fontes]
    nomes = [f["modalidade"] for f in fontes]
    if len(nomes) != len(set(nomes)):
        raise ValueError("Há modalidades duplicadas.")
    esperadas = list(dict.fromkeys(fontes_esperadas))
    if not esperadas or not {"audio", "video"}.issubset(esperadas):
        raise ValueError("O escopo mínimo esperado é áudio e vídeo.")
    for nome in esperadas:
        if nome not in nomes:
            fontes.append(fonte_indisponivel(nome, "Fonte prevista, mas não fornecida."))
    indisponiveis = [f["modalidade"] for f in fontes
                    if f["status"] != "ok" or f.get("cobertura_parcial", False)]
    sinais = [f for f in fontes if f["status"] == "ok" and f["alerta"]]
    nivel = max((f["nivel"] for f in sinais), key=NIVEIS.get, default="nenhum")
    assinatura = json.dumps({"id_caso": id_caso, "fontes": fontes, "pareamento": pareamento},
                           ensure_ascii=False, sort_keys=True, allow_nan=False)
    return {
        "schema_version": "2.0",
        "id_caso": id_caso,
        "id_resultado": hashlib.sha256(assinatura.encode()).hexdigest()[:20],
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(),
        "alerta": bool(sinais), "nivel": nivel,
        "requer_revisao": bool(sinais or indisponiveis),
        "status": "incompleto" if indisponiveis else "completo",
        "simulado": bool(simulado or any(f.get("simulado", False) for f in fontes)),
        "pareamento": pareamento,
        "fontes_esperadas": esperadas,
        "fontes_inconclusivas": indisponiveis,
        "motivos": [f["motivo"] for f in sinais],
        "fontes": fontes,
        "entrega": {"destino": "caixa_local_equipe_medica", "status": "aguardando_persistencia"},
        "aviso": AVISO,
    }


def validar_instantes(registros):
    anterior = None
    for r in registros:
        instante = datetime.fromisoformat(str(r["timestamp"]).replace("Z", "+00:00"))
        if instante.tzinfo is None or (anterior is not None and instante <= anterior):
            raise ValueError("Timestamps devem ter fuso e ordem estrita crescente.")
        anterior = instante

def detectar_series(historico, observacoes, campos, modalidade, limiar=6.0, simulado=False):
    if modalidade not in {"sinais_vitais", "movimentacao"} or not campos:
        raise ValueError("Defina modalidade e campos de série.")
    limiar = numero_finito(limiar, "limiar_robusto", 0.1)
    if len(historico) < 20 or not observacoes:
        return fonte_indisponivel(modalidade, "Histórico mínimo: 20 pontos; observações: ao menos 1.",
                                 simulado=simulado)
    validar_instantes(historico + observacoes)
    referencias, eventos, inconclusivos = {}, [], []
    for campo in campos:
        valores = [numero_finito(r[campo], campo) for r in historico]
        centro = statistics.median(valores)
        escala = 1.4826 * statistics.median(abs(v-centro) for v in valores)
        if escala <= 1e-12:
            inconclusivos.append(campo)
            continue
        referencias[campo] = {"mediana": centro, "escala_robusta": escala}
    if not referencias:
        return fonte_indisponivel(modalidade,
            "Referência sem dispersão suficiente: " + ", ".join(inconclusivos), simulado=simulado)
    for r in observacoes:
        for campo, ref in referencias.items():
            valor = numero_finito(r[campo], campo)
            escore = abs(valor-ref["mediana"])/ref["escala_robusta"]
            if escore >= limiar:
                eventos.append({"timestamp": r["timestamp"], "campo": campo,
                                "valor": valor, "escore_robusto": escore})
    sinal = bool(eventos)
    return {"modalidade": modalidade, "status": "ok", "alerta": sinal,
            "nivel": "medio" if sinal else "nenhum",
            "motivo": f"{len(eventos)} desvio(s) estatístico(s) em relação ao histórico.",
            "eventos": eventos, "referencias": referencias, "limiar": limiar,
            "campos_inconclusivos": inconclusivos, "cobertura_parcial": bool(inconclusivos),
            "origem": "serie_estruturada_mad", "simulado": bool(simulado)}

def detectar_prescricoes(registros, limiar_variacao=0.5, simulado=False):
    limiar_variacao = numero_finito(limiar_variacao, "limiar_variacao", 0.01)
    if len(registros) < 2:
        return fonte_indisponivel("prescricoes", "Forneça ao menos duas prescrições.",
                                 simulado=simulado)
    validar_instantes(registros)
    anteriores, eventos, comparacoes = {}, [], 0
    for r in registros:
        chave = r["medicamento_id"]
        dose = numero_finito(r["dose"], "dose", 1e-9)
        intervalo = numero_finito(r["intervalo_h"], "intervalo_h", 1e-9)
        if not chave or not r["unidade"] or not r["via"]:
            raise ValueError("Informe medicamento_id, unidade e via.")
        if chave in anteriores:
            p = anteriores[chave]
            comparacoes += 1
            motivos = []
            if r["unidade"] != p["unidade"]:
                motivos.append("unidade alterada; doses não comparadas")
            if r["via"] != p["via"]:
                motivos.append("via alterada; doses não comparadas")
            if r["unidade"] == p["unidade"] and r["via"] == p["via"]:
                variacao = abs(dose-p["dose"])/p["dose"]
                if variacao >= limiar_variacao:
                    motivos.append(f"variação relativa de dose: {variacao:.1%}")
            if intervalo != p["intervalo_h"]:
                motivos.append("intervalo entre doses alterado")
            if motivos:
                eventos.append({"timestamp": r["timestamp"], "medicamento_id": chave,
                                "motivos": motivos})
        anteriores[chave] = {**r, "dose": dose, "intervalo_h": intervalo}
    if not comparacoes:
        return fonte_indisponivel("prescricoes", "Nenhum medicamento repetido para comparar.",
                                 simulado=simulado)
    sinal = bool(eventos)
    return {"modalidade": "prescricoes", "status": "ok", "alerta": sinal,
            "nivel": "medio" if sinal else "nenhum",
            "motivo": f"{len(eventos)} alteração(ões) de prescrição para revisão.",
            "eventos": eventos, "origem": "comparacao_temporal_prescricoes",
            "simulado": bool(simulado), "limiar_variacao": limiar_variacao}
