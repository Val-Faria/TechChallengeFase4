# Integração multimodal

O notebook `TechChallengeFase4_integracao.ipynb` é a entrada para o Colab. Ele usa o pacote testado de `src/techchallenge4`, evitando implementar as mesmas regras em duas versões.

1. Execute as células em ordem, com nuvem e treinamento desligados.
2. Confira as evidências salvas em `evidence/`.
3. Execute a composição com `resultado_audio_externo.csv`, `resultado_video_equipe.json` e `texto_openai_integracao.json`.
4. Abra o painel. O HTML exportado é estático; para registrar revisão, execute o servidor local descrito no README principal.
5. Salve o ZIP gerado. Para gravar no Drive, ative `USAR_DRIVE` antes de executar.

## Fontes

O áudio `novo-03.wav` foi criado depois da divisão do dataset e não entra no treinamento. O JSON de vídeo contém os eventos recebidos do Marcelo, sem publicação de imagens. A resposta textual veio de uma chamada real OpenAI sobre a transcrição do mesmo áudio novo; o padrão somente reutiliza a resposta. Sinais vitais, prescrições e movimento são sintéticos, identificados individualmente. A composição não representa um mesmo paciente nem sincronização entre áudio e vídeo.

## Monitor e entrega

`scripts/run_stream.py` aceita JSONL e acompanha novas linhas com limites de duração e quantidade. A referência estatística usa somente observações anteriores e fica congelada antes do monitoramento. O servidor do painel se vincula apenas a `127.0.0.1`; a confirmação registra revisor e instante em trilha local, sem mensagens a terceiros.

`evidencias/execucao_final/` guarda a composição multimodal. `evidencias/monitoramento_final/` guarda o processamento incremental de dados estruturados. As evidências antigas são históricas.

## Credenciais e GPU

Use Secrets do Colab ou variáveis de ambiente. Arquivos `.env`, mídia privada e modelos são ignorados pelo Git. Se ativar GPU, salve antes os artefatos no Drive e desconecte/exclua o ambiente ao terminar; fechar a aba não basta.


## Detectores complementares executados

Consulte [o guia de mídias](../integracao/MIDIAS.md): comparação acústica intra-voz e fluxo óptico incremental, com controles físicos novos e evidência de execução. Não substituem semanticamente os modelos originais nem comprovam diagnóstico clínico.
