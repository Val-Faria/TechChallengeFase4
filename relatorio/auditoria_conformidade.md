# Auditoria da entrega técnica — Fase 4

Data: 13/11/2026. Referência: enunciado original, páginas 2–4; SHA-256 `5166f7d0f963d641b79e59768bb81b78d15924cce90735624a234076b20d5ba1`.

## Estado da entrega

A entrega contém código, modelos/manifestos, demonstrações, testes, evidências e relatório no padrão LaTeX fornecido pela equipe. O ZIP Uterus foi recebido, auditado e usado em **novo treino YOLOv8s**. Assim, a inferência anatômica deixou de depender somente dos resultados históricos. O peso original do Marcelo não foi recuperado; não se afirma reprodução exata daquele experimento.

O trabalho continua sendo um protótipo com limitações medidas. A aprovação dos testes não significa detecção clínica confiável. A apresentação e o link YouTube/Vimeo permanecem com Benicio, conforme divisão do grupo.

| Requisito | Evidência executada | Limite declarado |
|---|---|---|
| Vídeo clínico, eventos e relatório | YOLOv8s novo; dataset auditado, montagens de teste/reserva, saída anotada, JSON e relatório | Quadros e montagens; falhas na reserva; sem cirurgia contínua externa |
| Voz e alterações vocais | Whisper, características, Random Forest e comparação de pausas/trechos com referência anterior | Corpus e controles sintéticos; sem confirmação de causa médica |
| Transcrição, termos e sentimentos em nuvem | Chamadas OpenAI reais, citações literais, negação/contexto e consumo | Alternativa ao Azure autorizada; revisão humana necessária |
| Sinais vitais | Histórico anterior e desvios de batimentos, pressão sistólica/diastólica e oxigenação | Valores sintéticos; limiar estatístico demonstrativo |
| Prescrições e movimentação | Comparações temporais e sinais por campo | Não recomenda tratamento ou postura clínica |
| Alertas e resposta | Fusão, SQLite, painel e confirmação auditável | Entrega local, sem sistema hospitalar |
| Processamento temporal | JSONL e inferência acústica/visual em arquivos no ritmo original | Espera da janela distinta da computação; nuvem/captura ao vivo fora da medida |
| Código e relatório | Branch Nirton, modelos, scripts, notebooks, PDF e Overleaf | Artefatos clínicos/YOLO no pacote privado; caminhos documentados |
| Apresentação até 15 minutos | Roteiro e material de demonstração | Benicio grava/publica e o grupo insere o link |

## Nova reprodução e reserva

- ZIP recebido: 40.622.141 bytes, CRC válido, SHA-256 `d2345667a5efa840b7f1f3ff33af52ebf25d8ccf0f7c3c985afdeba6d7e04bf8`.
- A página anuncia 1.368 imagens; o arquivo contém 1.367. Três entradas YAML idênticas foram conferidas; 418 polígonos usados foram convertidos em caixas envolventes.
- `UterusClip_mov`: 776 treino, 74 validação e 37 teste. `2024-09-26-20-27-33_mp4`: totalmente fora do desenvolvimento; 60 quadros na reserva, 420 aumentos não utilizados.
- Novo modelo: YOLOv8s, resolução 416, batch 8, 80 épocas máximas, semente 42 e paciência 20, GPU RTX 2060 local. Seleção do checkpoint pela validação, com peso congelado antes da reserva.
- mAP50: validação **0,941**, teste **0,980**, reserva **0,613**. Protocolos diferentes dos números históricos do Marcelo.
- Regra temporal: teste com 2 verdadeiros positivos, 0 falsos positivos e 1 evento não detectado; reserva com 0 previsões e 2 eventos não detectados. Recall da reserva **0**, precisão indefinida. Os limiares não foram alterados para melhorar a reserva.
- Referência temporal: caixas anotadas + montagem de dois segundos por quadro; não anotações clínicas de complicações. Prefixo de arquivo não comprova paciente/procedimento independente.

Os resultados fracos da reserva são uma limitação do sistema e estão preservados, não convertidos em sucesso. O exemplo integrado positivo usa o teste; a reserva permanece uma verificação separada. Evidências: `video_dataset_auditoria.json`, `video_reproducao.json`, `video_inferencia_nova.json` e os dois JSONs sanitizados.

## Áudio e interpretação médica

O modelo emocional permanece congelado, ajustado somente em treino. As seis falas externas ficaram abaixo de 0,70; não se reduziu o limiar após vê-las. A comparação acústica adicional utiliza referências anteriores da mesma voz e oito cenários físicos. Os controles detectam pausas inseridas, não confundem redução de volume com sinal e tratam silêncio como inconclusivo.

Essas verificações não medem sensibilidade para fadiga, disartria ou dificuldade respiratória em pacientes. A extração de uma menção textual também não comprova detectar um sintoma pela acústica. Os sinais observacionais solicitam revisão, sem diagnóstico. O PDF não foi interpretado como exigindo ensaio hospitalar, homologação médica ou envio por e-mail.

## Correções e verificações de software

A suíte tem **106 testes e 26 subtestes aprovados**. Inclui contratos, prioridade, fontes inconclusivas, pressão arterial, validade temporal, referências congeladas, seleção explícita de áudio, revisão concorrente, cache e integridade de arquivos.

Foi corrigido um bloqueio intermitente do Windows ao substituir snapshots concorrentes: destinos são serializados no processo, e erros transitórios específicos recebem repetição limitada. Erros permanentes continuam visíveis e o snapshot anterior é preservado. Há testes próprios para os dois comportamentos.

O notebook de vídeo usa os scripts compartilhados e lê evidências por padrão. As dependências pesadas, treino e GPU são opcionais. A revisão de distribuição verifica sintaxe de todos os códigos/notebooks e ausência de credenciais. A exportação sem Git e o ambiente Python mínimo são conferidos na checagem final.

## Relatório e preservação

O relatório segue o padrão anexado da Fase 2: fonte 12, A4, margens de 2,5 cm, espaçamento 1,5, capa simples com autores/RMs, links azuis e sumário antes do resumo. Os dados, figuras, resultados e links pertencem à Fase 4. O link audiovisual anterior não foi reutilizado.

O PDF é compilado das mesmas fontes incluídas no Overleaf. O backup do Drive preserva ZIP original, pesos, vídeos e relatórios privados, código, evidências e manifestos. Nenhuma credencial integra os pacotes. Nesta etapa não houve novas chamadas pagas nem sessão Colab; os processos locais de GPU foram encerrados após treino/inferência.

## Revisão das divergências e cobertura de vídeo

A ausência de caixa anotada não confirma ausência anatômica. Os dois intervalos da reserva continuam sem concordância; os rótulos originais não foram alterados. A revisão encontrou 15 divergências de útero anotado/predito nos três conjuntos avaliados. A planilha de revisão conserva hashes e deixa a adjudicação independente pendente, sem criar rótulos médicos.

A calibração em validação melhorou macro-F1 por quadro de 0,934 para 0,951, mas piorou na reserva conhecida de 0,627 para 0,583. O candidato não foi promovido; os limites operacionais continuam 0,4/0,6. A reserva já observada não é reutilizada como nova verificação cega.

A compatibilidade visual por mediana/MAD é ajustada só em treino e retém 74/74 imagens de validação, 37/37 de teste e 60/60 da reserva. Quadros incompatíveis interrompem a regra e indicam cobertura parcial; não se tornam observações normais. A fusão, o relatório e o painel preservam essa indicação e mantêm o pedido de revisão mesmo sem evento positivo.

Uma fonte TVASurg oficial adicional foi processada fora do ajuste. O falso alerta inicial em ilustração foi preservado e removido pela proteção de cobertura. Uma janela temporal seguinte foi definida antes da inferência com essa proteção; é a mesma fonte/paciente, sem rótulos clínicos. As mídias continuam privadas e não entram no Git/PDF. Não se declara acurácia clínica ou solução completa da divergência anatômica. Detalhes em [revisao_video.md](revisao_video.md); alinhamento com o material docente em [alinhamento_docente.md](alinhamento_docente.md).

## Organização e notebooks de entrega

Os módulos permanecem separados, com regras compartilhadas no pacote Python. Resultados anteriores ficam em `integracao/evidencias/historico/`. Os três notebooks contêm saídas de execução local em CPU: áudio com previsões do modelo congelado, vídeo com medições registradas e integração com nova execução dos detectores, fusão e caixa de revisão. Não houve treinamento ou chamadas pagas. A redação do relatório foi organizada por métodos e resultados, preservando o protocolo, as limitações e a identificação dos dados sintéticos.
