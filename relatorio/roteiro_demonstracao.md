# Roteiro para Benicio - demonstração final

Duração planejada: **13 minutos e 30 segundos**, com margem até 15 minutos. Publicar no YouTube ou Vimeo, público ou não listado conforme as condições do material utilizado.

| Tempo | Conteúdo | Evidência |
|---|---|---|
| 00:00-01:00 | Problema, equipe e recorte | Diagrama do fluxo e sinais de triagem |
| 01:00-03:30 | Áudio | 1.180 WAVs, amostra reservada, transcrição, características, classe/confiança e partições |
| 03:30-05:30 | Vídeo | Eventos 76-82 s e 84-114 s; diferenciar métricas históricas das verificações novas |
| 05:30-07:00 | Texto em nuvem | Resposta real da OpenAI, evidências, negação e consumo, sem credenciais |
| 07:00-09:30 | Integração | Caso combinado, prioridade preservada, cobertura, JSON e relatório |
| 09:30-11:30 | Anomalias e resposta | Séries/prescrições sintéticas, reprodução temporal, painel e confirmação de revisão |
| 11:30-13:30 | Resultados e limites | Testes, avaliação cega, métricas atribuídas e reprodutibilidade |

## Preparação

1. Abrir a branch `Nirton` e conferir o README de execução.
2. Disponibilizar os artefatos regenerados de áudio e o pacote privado de Marcelo.
3. Usar evidências reais já salvas para evitar gastar créditos ou tempo de GPU durante a gravação.
4. Executar a demonstração e abrir o painel antes da captura.
5. Deixar o PDF aberto na arquitetura e nos resultados.
6. Fechar `.env`, Secrets, abas de chaves e telas com credenciais.
7. Selecionar com Marcelo imagens compatíveis com a orientação do grupo sobre o material de terceiros.

## Demonstração prática

1. Mostrar classe/confiança de um WAV reservado e explicar o isolamento do novo classificador.
2. Mostrar transcrição e resultado textual real.
3. Mostrar o JSON de vídeo da equipe e os tempos dos eventos.
4. Executar `scripts/run_demo.py` conforme o README.
5. Localizar a origem de cada modalidade no resultado.
6. Mostrar que áudio neutro não cancela alerta alto e que fonte ausente não vira normalidade.
7. Abrir o painel, conferir o alerta e confirmar sua revisão.
8. Mostrar a auditoria e explicar o que a latência mede.

## Formulações corretas

- “O protótipo gera sinais para revisão humana, não diagnósticos.”
- “As falas são sintéticas. A verificação cega foi reservada para o novo classificador, sem representar validação em pacientes.”
- “O professor autorizou outros fornecedores. Utilizamos Whisper e análise textual OpenAI.”
- “O vídeo recebido pertence à avaliação original; os clipes inéditos são verificações controladas de software.”
- “Há medições distintas: replay de resultados, monitor estruturado e nova inferência de mídia sobre arquivos no ritmo original. Esta última mede extração acústica, fluxo óptico, fusão e persistência; a espera da janela é de cinco segundos e a nuvem está fora dessa latência.”
- “O painel demonstra entrega e revisão no protótipo, sem conexão hospitalar.”

Após publicar, inserir o link no README e conferir duração e revisão do código. Não publicar credenciais, bancos ou mídias privadas junto do código.


## Trecho prático acrescentado

Reserve cerca de um minuto das partes de áudio/vídeo para o comando de [MIDIAS.md](../integracao/MIDIAS.md). Mostre o controle estável, o vídeo geométrico alterado, as janelas de voz e o banco gerado. O exemplo usa PCM e pixels, não decisões prontas. Explique que os critérios observacionais não identificam a causa médica nem reconhecem anatomia. No original da equipe, diferencie resultados YOLO recebidos da nova inferência de movimento. Não diga que o peso anatômico foi recuperado.
