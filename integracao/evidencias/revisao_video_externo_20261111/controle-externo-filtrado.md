# Relatório automático multimodal

**Caso:** controle-externo-filtrado
**Resultado:** 4880d780848fc99020f0
**Prioridade:** nenhum
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
- Origem: resultado_video_externo_filtrado.json
- Motivo: 0 trecho(s) com instrumento detectado sem detecção sustentada de útero
- Cobertura parcial: esta fonte exige revisão mesmo sem alerta positivo.
- Interpretação: Presença/ausência de detecções pelo modelo; ausência de alerta não confirma normalidade nem ausência de falha clínica.
- Limitação: Não há referência independente de eventos clínicos para calcular acurácia.
- Limitação: Vídeo didático editado; mesma fonte da verificação inicial, sem independência por paciente.
- Limitação: Filtro estatístico de aparência não identifica anatomia nem garante que a cena seja apropriada.
- Limitação: Há quadros fora da referência visual; não interpretados como normais.

## Resposta operacional

Entrega: {"destino": "caixa_local_equipe_medica", "status": "aguardando_persistencia"}

A caixa de revisão e o painel são locais. Não há envio a um hospital.

> Protótipo acadêmico para revisão humana. Não constitui diagnóstico.
