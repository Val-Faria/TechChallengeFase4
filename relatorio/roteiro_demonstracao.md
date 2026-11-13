# Roteiro da apresentação — Fase 4

Duração prevista: 13 minutos e 30 segundos, com margem até o limite de 15 minutos. Responsável pela gravação e publicação: Benicio Cardoso.

| Tempo | Conteúdo | Material |
|---|---|---|
| 00:00–01:00 | Problema, recorte e arquitetura | Relatório: introdução e fluxo |
| 01:00–03:30 | Áudio, partições, previsões e confiança | Notebook de áudio executado |
| 03:30–05:30 | YOLO, regra temporal, resultados e limites | Notebook de vídeo executado |
| 05:30–07:00 | Transcrição, termos e contexto em nuvem | Respostas reais salvas da OpenAI |
| 07:00–09:30 | Fusão e detecção de anomalias | Notebook de integração |
| 09:30–11:30 | Entrega e confirmação de revisão | Painel local e auditoria |
| 11:30–13:30 | Métricas, limitações e reprodução | Relatório final e repositório |

## Preparação

Abrir os três notebooks e o relatório. As saídas já estão salvas e não exigem GPU ou novas chamadas à API. Para demonstrar a confirmação de revisão, criar uma saída própria:

```powershell
python scripts/run_demo.py --output integracao/saidas/apresentacao --audio-csv audio/evidencias/resultado_audio_externo.csv --audio-filename novo-03.wav --video-json evidence/resultado_video_teste.json --text-json evidence/texto_openai_integracao.json
python -m techchallenge4.dashboard --db integracao/saidas/apresentacao/alertas.sqlite3
```

Abrir o endereço local exibido, mostrar a prioridade e a cobertura e confirmar a revisão. A evidência publicada já contém uma confirmação automática de teste; a nova pasta evita reutilizá-la durante a gravação.

## Pontos a explicar

- Os áudios e as séries estruturadas são sintéticos; as modalidades não representam um paciente pareado.
- A baixa confiança acústica permanece inconclusiva e não cancela o alerta alto do vídeo.
- As métricas do novo YOLO são distintas dos resultados históricos. Os dois intervalos derivados de caixas na reserva continuam sem concordância; ausência de caixa não confirma ausência anatômica.
- O filtro de aparência remove um falso alerta técnico sobre ilustração. Ele não confirma anatomia nem valida uma falha cirúrgica.
- A API OpenAI substitui o fornecedor sugerido conforme autorização docente. A apresentação lê respostas reais salvas e não consome créditos.
- A latência local é separada da espera da janela; não inclui aquisição clínica, ASR ou rede de nuvem.
- A caixa e a confirmação são locais. Não há envio a um hospital ou alteração de tratamento.

## Publicação

Usar as tabelas, os gráficos e os resultados sanitizados. As imagens TVASurg permanecem privadas e não devem ser incorporadas ao vídeo sem autorização. Conferir com a equipe o material de terceiros escolhido para a apresentação e manter chaves e dados pessoais fora da captura.

Publicar no YouTube ou Vimeo e inserir o link em `\linkdovideo`, no início de `relatorio/latex/main.tex`, e no README. Recompilar o PDF e o pacote Overleaf após essa inclusão.
