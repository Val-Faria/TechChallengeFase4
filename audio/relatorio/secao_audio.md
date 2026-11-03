# Frente de áudio — monitoramento de sinais emocionais pela voz

## 1. Objetivo e categoria monitorada

A frente de áudio classifica características vocais associadas a três categorias: **ansiedade/hesitação**, **neutro** e **tristeza**. Para cada gravação, a função `classificar_audio(caminho_audio)` retorna a classe prevista e a confiança estimada pelo classificador, no formato `(classe, confiança)`. Essa saída pode ser enviada à integração multimodal como sinal de triagem para revisão da equipe.

O resultado não é diagnóstico nem avaliação clínica. A confiança é a probabilidade estimada pelo Random Forest, não uma medida de certeza clínica.

## 2. Fluxo da frente de áudio

```text
ZIP do dataset versionado no GitHub (1.180 WAVs)
   │  quatro versões por fala original: original, lento, rápido e ruído
   ▼
Whisper tiny ──► transcrição em português
   │
   ├──► Librosa: duração, energia, proporção de pausas, ritmo de fala,
   │             tom médio e variação do tom
   ▼
Random Forest ──► classe prevista + confiança
   │
   ├──► classificar_audio(caminho_audio) para um áudio
   └──► lote de WAVs ──► resultado_audio_1180.csv + relatório de falhas
```

O Azure Speech é usado para **sintetizar as falas que deram origem ao conjunto**. A transcrição e a análise de texto deste notebook são feitas localmente pelo Whisper; não há chamada de transcrição ou análise de texto pelo Azure neste fluxo.

## 3. Dataset e preparação

A versão usada nesta execução é `audio/datasets/dataset_audio_emocoes_1180.zip`, com **1.180 arquivos WAV** e metadados. A distribuição confirmada no ZIP é:

| Classe | WAVs |
|---|---:|
| Ansiedade/hesitação | 380 |
| Neutro | 400 |
| Tristeza | 400 |
| **Total** | **1.180** |

O conjunto contém quatro variações de cada gravação original: original, lenta, rápida e com ruído. A divisão de avaliação agrupa os exemplos pela gravação original, evitando colocar variações da mesma fala simultaneamente no treino e no teste.

## 4. Modelo e características

| Item | Escolha |
|---|---|
| Transcrição | Whisper `tiny`, idioma português (`pt`) |
| Extração acústica | Librosa |
| Classificador | Random Forest, 200 árvores, `class_weight="balanced"` |
| Entrada do classificador | Duração, energia média, proporção de pausas, palavras por minuto, tom médio e desvio do tom |
| Divisão de avaliação | `GroupShuffleSplit`, 80% treino e 20% teste, agrupado por gravação original |
| Modelo final | Reajustado com os 1.180 exemplos depois da avaliação |
| Arquivo do modelo | `modelo_audio_1180.joblib` no Google Drive |

A função `classificar_audio(caminho_audio)` repete a extração das mesmas características para um WAV, aplica o modelo final e devolve `(classe, confiança)`. O objeto `modelo_whisper` precisa estar carregado para a função transcrever o áudio.

## 5. Resultados

### 5.1 Avaliação no conjunto de teste

A avaliação registrada para a versão de 1.180 WAVs usou **236 exemplos de teste**:

| Classe | Precisão | Recall | F1 | Suporte |
|---|---:|---:|---:|---:|
| Ansiedade/hesitação | 0,85 | 0,82 | 0,84 | 80 |
| Neutro | 0,84 | 0,85 | 0,84 | 80 |
| Tristeza | 0,99 | 1,00 | 0,99 | 76 |
| **Geral** |  |  | **Acurácia: 0,89** | **236** |
| Macro média | 0,89 | 0,89 | 0,89 | 236 |
| Média ponderada | 0,89 | 0,89 | 0,89 | 236 |

Essas métricas vêm da divisão agrupada de teste, e não do CSV de previsões em lote. O modelo final foi reajustado com todos os dados depois da avaliação; portanto, as previsões do lote descrevem as saídas do sistema e não constituem uma medida independente de desempenho.

### 5.2 Processamento do lote

Na execução do conjunto versionado, a validação encontrou **1.180 WAVs válidos**, **zero inválidos**, e a classificação concluiu **1.180 arquivos sem falhas**. A saída consolidada foi salva no Drive como `resultado_audio_1180.csv`; o relatório de erros foi salvo como `erros_classificacao_audio_1180.csv` e registrou zero falhas.

Cada linha do CSV inclui o caminho/nome do arquivo, a classe prevista e a confiança. A função individual foi testada durante o desenvolvimento e retornou uma tupla com esses dois valores.

## 6. Artefatos e execução

- Notebook: `audio/notebooks/TechChallengeFase4_audio.ipynb`.
- Dataset: `audio/datasets/dataset_audio_emocoes_1180.zip` (Git LFS).
- Modelo treinado: `modelo_audio_1180.joblib`, salvo no Drive da conta Google que executou o Colab.
- Previsões do lote: `resultado_audio_1180.csv`, salvo no mesmo Drive.
- Falhas do lote: `erros_classificacao_audio_1180.csv`.

No Colab, execute as células em ordem: instalação/carregamento do Whisper; download e extração do ZIP oficial; extração das características; avaliação e treino final; salvamento do modelo; definição e teste de `classificar_audio`; classificação do lote. O Drive é montado na conta de quem executa a célula e os arquivos resultantes não ficam automaticamente visíveis aos demais integrantes.

## 7. Limitações e escopo pendente

- **Áudios sintéticos:** as falas foram sintetizadas com Azure Speech e aumentadas localmente. Elas não representam variação real entre pessoas, sotaques, condições de gravação ou situações clínicas; a acurácia não deve ser interpretada como validação clínica.
- **Generalização não demonstrada em áudio real:** a avaliação usa variações de falas sintéticas. O teste com gravações reais independentes ainda é necessário antes de qualquer uso operacional.
- **Confiança do modelo:** `predict_proba` fornece uma estimativa do Random Forest e não garante que a classe esteja correta. O valor não deve ser apresentado como probabilidade clínica calibrada.
- **Sensibilidade à transcrição:** ritmo de fala é calculado a partir do texto produzido pelo Whisper; erros de transcrição podem alterar essa característica.
- **Processamento em lote:** o notebook processa arquivos sequencialmente e não implementa captura ou análise de áudio em tempo real.
- **Azure Text/Speech:** o notebook não implementa transcrição nem análise de texto pelo Azure. O Azure Speech é usado somente na síntese do dataset.
- **Integração multimodal:** a saída da frente de áudio pode alimentar a função de fusão, mas a integração ponta a ponta com vídeo e os dados simulados de sinais vitais, prescrições e movimentação em tempo real permanece pendente no projeto.

A saída deve ser tratada como **sinal de triagem para revisão humana**, nunca como diagnóstico ou decisão clínica automatizada.
