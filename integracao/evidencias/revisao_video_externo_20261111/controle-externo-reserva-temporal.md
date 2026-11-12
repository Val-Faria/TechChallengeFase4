# Relatório automático multimodal

**Caso:** controle-externo-reserva-temporal
**Resultado:** ca35163830ecb64bb1c5
**Prioridade:** alto
**Cobertura:** incompleto
**Revisão necessária:** True
**Contém fonte simulada:** True
**Associação:** controle_sintetico_de_integracao_sem_paciente_pareado

## audio

- Estado: ok
- Origem: controle_de_software_neutro_nao_gravacao_clinica
- Motivo: Classe acústica: neutro; confiança 0.950.

## video

- Estado: ok
- Origem: resultado_video_externo_reserva_temporal.json
- Motivo: 1 trecho(s) com instrumento detectado sem detecção sustentada de útero
- Cobertura parcial: esta fonte exige revisão mesmo sem alerta positivo.
- Interpretação: Presença/ausência de detecções pelo modelo; ausência de alerta não confirma normalidade nem ausência de falha clínica.
- Limitação: Não há referência independente de eventos clínicos para calcular acurácia.
- Limitação: Vídeo didático editado; mesma fonte da verificação inicial, sem independência por paciente.
- Limitação: Filtro estatístico de aparência não identifica anatomia nem garante que a cena seja apropriada.
- Limitação: Há quadros fora da referência visual; não interpretados como normais.
- Evidência: {"descricao": "Instrumento em cena sem visualização do útero", "inicio_s": 57.0, "fim_s": 81.4, "duracao_s": 24.4, "confianca": 0.668}

## Resposta operacional

Entrega: {"confirmacao": "gravacao_transacional_sqlite", "destino": "caixa_local_equipe_medica", "entrega_hospitalar": false, "recebido_em_utc": "2026-11-12T00:07:41.570656+00:00", "status": "persistido"}

A caixa de revisão e o painel são locais. Não há envio a um hospital.

> Protótipo acadêmico para revisão humana. Não constitui diagnóstico.
