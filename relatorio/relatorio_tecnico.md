# Relatório técnico — Fase 4

O documento principal está em `output/pdf/relatorio_tecnico_fase4.pdf`; fontes em `relatorio/latex/` e projeto importável em `relatorio/overleaf_fase4.zip`. A formatação segue o modelo da Fase 2 anexado pelo integrante: fonte 12, A4, margens de 2,5 cm, espaçamento 1,5, capa por maketitle, autores/RMs e links azuis. Não foram reutilizados dados ou link audiovisual da fase anterior.

## Fluxo

Voz → características/Whisper → Random Forest e comparação intra-voz; transcrição → OpenAI; vídeo → YOLOv8s e regra temporal; séries/prescrições → detectores; fontes normalizadas → fusão → relatório e caixa SQLite → painel e revisão auditável.

O professor autorizou substituir Azure. Foram preservadas 18 chamadas reais OpenAI, com estimativa conservadora acumulada de US$ 0,005980495. Não houve novas chamadas pagas nesta etapa.

## Áudio

O corpus contém 1.180 WAVs sintéticos. O classificador congelado foi ajustado apenas em 712 exemplos de treino; validação 172, teste 176 e reserva cega 120. Acurácias: 93,60%, 86,36% e 88,33%, respectivamente. Famílias de frases, gravações e hashes permanecem separados. O modelo recebido da autora, ajustado em todo o corpus, é histórico e não substitui essa avaliação.

As seis falas externas somam 109 palavras; WER Whisper tiny 11,93% e OpenAI 0% nessa pequena amostra sintética. Todas as previsões emocionais externas ficaram abaixo de 0,70. Não se reduziu o limiar. Oito controles físicos verificam a comparação de pausas e trechos vocais; não medem sensibilidade para doença ou fadiga clínica.

## Novo YOLO e dataset

O ZIP Uterus v4 recebido passou na integridade e contém 1.367 imagens, uma a menos que a página anuncia. O preparador normaliza 418 polígonos em caixas e separa um prefixo inteiro. A nova divisão usa 776/74/37 imagens em treino/validação/teste, mais 60 quadros reservados e 420 aumentos do prefixo reservado não utilizados.

| Avaliação | mAP50 | mAP50–95 |
|---|---|---|
| Validação | 0.941 | 0.620 |
| Teste do mesmo prefixo | 0.980 | 0.615 |
| Reserva de outro prefixo | 0.613 | 0.299 |

A regra temporal recuperou 2/3 eventos no teste e 0/2 na reserva. São eventos construídos a partir de caixas anotadas e dois segundos por quadro; não complicações clínicas confirmadas. Os limiares 0,4/0,6 não foram ajustados após a reserva. O mAP50 histórico 0,928 e o recall de alerta 0,72 do Marcelo permanecem atribuídos a outro experimento, não diretamente comparável.

A inferência nova foi executada sobre as montagens e produz vídeos anotados, JSON, relatório e imagens de eventos no pacote privado. O exemplo positivo da integração usa o teste; a reserva, incluindo suas falhas, é apresentada separadamente. Nenhum desses arquivos é uma cirurgia contínua externa inédita.

## Anomalias e alertas

A demonstração cobre batimentos, pressão sistólica/diastólica, oxigenação, movimentação e prescrições com dados sintéticos. O monitor usa referência anterior congelada, validade das fontes e prioridade preservada. A composição não representa o mesmo paciente.

A execução final produz cinco casos e quatro tarefas de revisão. O painel HTTP e a confirmação por `demonstracao_automatica` foram verificados; a ação está na auditoria SQLite. É um teste operacional, não revisão por médico real.

Há três medidas distintas: replay de resultados; monitor de eventos estruturados; e inferência acústica/fluxo óptico em arquivos no ritmo original. Esta última inclui processamento local e persistência, além da espera de cinco segundos da janela de voz. Não inclui ASR, nuvem ou câmera/microfone clínicos ao vivo.

## Verificação e preservação

A suíte final tem 77 testes e 26 subtestes aprovados. Foi corrigida uma condição transitória de substituição de arquivos concorrentes no Windows, mantendo erros permanentes visíveis. Código, notebooks, hashes e distribuição são auditados. O PDF e o Overleaf compartilham fontes e figuras.

O modelo emocional está no Git. O novo YOLO, as mídias, o dataset e os bancos ficam no backup privado do Drive, com manifestos. A gravação/publicação é de Benicio; inserir o link da Fase 4 na capa e no README. Os limites de síntese, origem e generalização fazem parte dos resultados e não são apresentados como comprovação clínica.
