# Relatório automático multimodal

**Caso:** monitor-sintetico
**Resultado:** 3bd13daa36339d19b5b2
**Prioridade:** medio
**Cobertura:** completo
**Revisão necessária:** True
**Contém fonte simulada:** True
**Associação:** pacotes_do_mesmo_caso_de_demonstracao_sem_validacao_clinica

## sinais_vitais

- Estado: ok
- Origem: serie_estruturada_mad
- Motivo: 2 desvio(s) estatístico(s) em relação ao histórico.
- Evidência: {"timestamp": "2026-11-09T15:00:31+00:00", "campo": "batimentos", "valor": 120.0, "escore_robusto": 32.37555645487657}
- Evidência: {"timestamp": "2026-11-09T15:00:31+00:00", "campo": "oxigenacao", "valor": 85.0, "escore_robusto": 8.093889113719143}

## movimentacao

- Estado: ok
- Origem: serie_estruturada_mad
- Motivo: 1 desvio(s) estatístico(s) em relação ao histórico.
- Evidência: {"timestamp": "2026-11-09T15:00:31+00:00", "campo": "intensidade", "valor": 50.0, "escore_robusto": 26.97963037906381}

## prescricoes

- Estado: ok
- Origem: comparacao_temporal_prescricoes
- Motivo: 1 alteração(ões) de prescrição para revisão.
- Evidência: {"timestamp": "2026-11-09T15:00:31+00:00", "medicamento_id": "medicamento_demo", "motivos": ["variação relativa de dose: 100.0%"]}

## audio

- Estado: ok
- Origem: resultado_audio_recebido
- Motivo: Classe acústica: neutro; confiança 0.950.

## video

- Estado: ok
- Origem: resultado_video_recebido
- Motivo: Resultado de vídeo recebido.

## texto_openai

- Estado: ok
- Origem: controle_sintetico_sem_chamada_api
- Motivo: Controle textual simulado sem sinal.

## Resposta operacional

Entrega: {"confirmacao": "gravacao_transacional_sqlite", "destino": "caixa_local_equipe_medica", "entrega_hospitalar": false, "recebido_em_utc": "2026-11-09T23:40:58.437999+00:00", "status": "persistido"}

A caixa de revisão e o painel são locais. Não há envio a um hospital.

> Protótipo acadêmico para revisão humana. Não constitui diagnóstico.
