# Relatório automático multimodal

**Caso:** demonstracao-integrada
**Resultado:** dcb37e4a81e872d052fc
**Prioridade:** alto
**Cobertura:** incompleto
**Revisão necessária:** True
**Contém fonte simulada:** True
**Associação:** composicao_didatica_de_fontes_independentes_sem_mesmo_paciente

## audio

- Estado: baixa_confianca
- Origem: CSV:resultado_audio_externo.csv:novo-03.wav
- Motivo: Classe acústica: neutro; confiança 0.595.

## video

- Estado: ok
- Origem: JSON:resultado_video_teste.json
- Motivo: 2 trecho(s) com instrumento sem útero visível
- Evidência: {"descricao": "Instrumento em cena sem visualização do útero", "inicio_s": 10.0, "fim_s": 16.0, "duracao_s": 6.0, "confianca": 0.867}
- Evidência: {"descricao": "Instrumento em cena sem visualização do útero", "inicio_s": 36.0, "fim_s": 74.0, "duracao_s": 38.0, "confianca": 0.839}

## sinais_vitais

- Estado: ok
- Origem: serie_estruturada_mad
- Motivo: 4 desvio(s) estatístico(s) em relação ao histórico.
- Evidência: {"timestamp": "2026-11-09T12:00:31+00:00", "campo": "batimentos", "valor": 120.0, "escore_robusto": 32.37555645487657}
- Evidência: {"timestamp": "2026-11-09T12:00:31+00:00", "campo": "oxigenacao", "valor": 85.0, "escore_robusto": 8.093889113719143}
- Evidência: {"timestamp": "2026-11-09T12:00:31+00:00", "campo": "pressao_sistolica", "valor": 160.0, "escore_robusto": 26.97963037906381}
- Evidência: {"timestamp": "2026-11-09T12:00:31+00:00", "campo": "pressao_diastolica", "valor": 105.0, "escore_robusto": 16.86226898691488}

## movimentacao

- Estado: ok
- Origem: serie_estruturada_mad
- Motivo: 1 desvio(s) estatístico(s) em relação ao histórico.
- Evidência: {"timestamp": "2026-11-09T12:00:31+00:00", "campo": "movimento", "valor": 50.0, "escore_robusto": 26.97963037906381}

## prescricoes

- Estado: ok
- Origem: comparacao_temporal_prescricoes
- Motivo: 1 alteração(ões) de prescrição para revisão.
- Evidência: {"timestamp": "2026-11-09T12:00:31+00:00", "medicamento_id": "medicamento_demo", "motivos": ["variação relativa de dose: 100.0%"]}

## texto_openai

- Estado: ok
- Origem: openai_responses
- Motivo: 2 menção(ões) afirmada(s) atuais; 0 incerta(s).
- Menção: falta de ar; estado: afirmado; contexto: paciente_atual; trecho: “Desde o começo da tarde sinto falta de ar e uma tontura que não passa.”.
- Menção: tontura; estado: afirmado; contexto: paciente_atual; trecho: “Desde o começo da tarde sinto falta de ar e uma tontura que não passa.”.

## Resposta operacional

Entrega: {"destino": "caixa_local_equipe_medica", "status": "persistido", "recebido_em_utc": "2026-11-11T03:50:47.368923+00:00", "confirmacao": "gravacao_transacional_sqlite", "entrega_hospitalar": false}

A caixa de revisão e o painel são locais. Não há envio a um hospital.

> Protótipo acadêmico para revisão humana. Não constitui diagnóstico.
