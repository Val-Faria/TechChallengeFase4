# Alinhamento ao enunciado e às aulas fornecidas

Esta revisão utiliza o PDF da Fase 4 como referência dos requisitos. As aulas fornecidas orientam as famílias de técnicas; não tornam obrigatória a inclusão de todas as bibliotecas exemplificadas.

| Referência fornecida | Relação com a solução |
|---|---|
| Enunciado, p. 3: YOLOv8 para objetos e áreas críticas | YOLOv8s, OpenCV e regra temporal; preservados os resultados da frente de vídeo. A proteção visual é um controle estatístico complementar, não outro detector anatômico. |
| Aula 03: atividades, ações, keypoints e landmarks | Processamento temporal e análise de movimento. OpenPose/MediaPipe são alternativas; não é obrigatório adicionar ambos ao caminho YOLO. |
| Aula 04: transcrição, MoviePy e SpeechRecognition | Transcrição de gravações e tratamento de mídia. A equipe já utilizava Whisper; ele é mantido, sem apresentar bibliotecas alternativas como obrigações extras. |
| Aula 05: classificação supervisionada de texto | Extração de termos/contexto e sentimento. Características acústicas e Random Forest são escolhas da frente de áudio, com seu domínio sintético explicitado. |
| Aulas OpenAI 02, 03 e 05: API, GPT, integração e automação | API real OpenAI, respostas estruturadas, cache e controle de consumo. A substituição do Azure foi autorizada pelo professor e está documentada em `evidence/orientacao_docente.md`. |
| Enunciado, p. 3: sinais vitais, prescrições e movimentação | Detectores temporais e regras de mudança. Mediana/MAD é uma opção de implementação estatística; não se afirma que foi a fórmula específica ensinada. |
| Enunciado, p. 4: código, relatório e demonstração até 15 minutos | Branch Nirton, notebooks executáveis, evidências, PDF e fontes Overleaf; gravação/publicação e link permanecem com Benicio/grupo. |

Reconhecimento facial das aulas 01/02, OCR/Textract, AWS Comprehend e geração de imagens não foram acrescentados como requisitos que o enunciado não pede. A solução permanece centrada em áudio, vídeo, texto, anomalias e entrega do alerta. Os materiais didáticos originais não são republicados com o código.

Vozes sintéticas e montagens não são convertidas em confirmação de condições médicas. Os dados e limites permanecem identificados no relatório. O novo vídeo didático externo verifica funcionamento e cobertura, sem fornecer acurácia clínica na ausência de referência anotada.
