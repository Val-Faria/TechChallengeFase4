# Frente de áudio: reprodução e avaliação independente

O conjunto oficial contém **1.180 WAVs**, 295 gravações originais e 20 frases-base, todos sintéticos. O Azure Speech foi utilizado pela equipe apenas para a síntese original; a extração abaixo usa **Whisper tiny local** e librosa, sem chamadas pagas.

## Reprodução

Na raiz do repositório, com Python 3.12:

```powershell
python -m pip install -r audio/requirements.txt
git lfs pull
python scripts/audio_reproduce.py --device auto
```

`--device auto` usa CUDA se disponível, ou CPU. O script limita o trabalho acústico a dois workers e persiste um cache incremental por SHA-256; uma execução interrompida pode ser retomada. O cache contém transcrições efetivamente produzidas pelo Whisper, nunca o texto dos metadados em seu lugar. Não há serviço pago nessa etapa.

O [notebook executado](notebooks/TechChallengeFase4_audio.ipynb) recalcula as previsões do modelo congelado e exibe as métricas e a matriz de confusão. Ele usa as características já extraídas e não retreina o modelo. A reprodução completa da extração fica no comando acima; GPU de entrada é suficiente para Whisper tiny. Salve os resultados antes de encerrar uma sessão opcional de GPU.

## Partições e ausência de vazamento

A divisão antiga por gravação original é preservada na documentação histórica da equipe, mas o modelo reproduzido usa uma divisão mais rigorosa: famílias de **frases-base**. Os prefixos definidos na síntese são removidos somente para agrupar a frase; o áudio e sua transcrição permanecem intactos.

As 20 famílias são atribuídas deterministicamente, antes do ajuste, a treino (12 famílias), validação (3), teste de desenvolvimento (3) e holdout cego (2). Nenhuma gravação original, variação aumentada, frase-base ou SHA-256 atravessa as partições. O Random Forest mantém os 200 estimadores e os hiperparâmetros fixos da equipe, sem busca de configuração. Ele é ajustado **somente no treino** e não é reajustado com os conjuntos reservados.

O holdout é inédito para esse modelo regenerado. Ele pertence ao corpus sintético existente e não deve ser chamado de avaliação clínica ou externa. O modelo histórico ajustado nos 1.180 arquivos não é usado nesse ensaio.

## Artefatos produzidos

| Arquivo | Conteúdo |
|---|---|
| `artifacts/audio/modelo_audio_1180.joblib` | Modelo congelado com colunas e identidade do dataset/partições |
| `artifacts/audio/resultado_audio_1180.csv` | Predições, classe de referência e partição de cada WAV |
| `artifacts/audio/caracteristicas_audio_1180.csv` | Seis características e transcrição efetivamente produzida |
| `artifacts/audio/manifesto_audio.json` | Caminhos, tamanhos e hashes dos artefatos |
| `audio/evidencias/particoes_audio.csv` | Manifesto de particionamento para auditoria |
| `audio/evidencias/predicoes_avaliacao.csv` | Predições por partição |
| `evidence/audio_reproducao.json` | Versões, auditoria, métricas e matrizes de confusão |

Arquivos do modelo e WAVs devem ficar no pacote persistente/Drive; não devem ser copiados para células ou commits indiscriminadamente. Arquivos joblib só devem ser carregados de origem confiável.

## Verificação funcional em novos áudios

`scripts/audio_external.py` aplica o modelo já congelado aos seis WAVs novos produzidos por síntese local do Windows, com outras vozes e textos ausentes do corpus. Antes da inferência, confere hashes e ausência da frase-base no dataset. Os arquivos não entram em treinamento, validação ou teste de desenvolvimento.

```powershell
python scripts/audio_external.py
```

O resultado é `evidence/audio_externo.json`, contendo transcrição, características, probabilidades e WER (erros de palavras em relação ao texto sintetizado). Não há rótulos emocionais ou clínicos validados nessas gravações; portanto **não se calcula acurácia emocional ou médica**. O objetivo é verificar comportamento do software sob mudança de voz e conteúdo.

As classes `ansiedade_hesitacao`, `neutro` e `tristeza` são rótulos do corpus sintético. Elas não comprovam reconhecimento de fadiga, disartria, falta de ar, depressão ou qualquer condição clínica em pacientes reais.


## Detectores complementares executados

Consulte [o guia de mídias](../integracao/MIDIAS.md): comparação acústica intra-voz e fluxo óptico incremental, com controles físicos novos e evidência de execução. Não substituem semanticamente os modelos originais nem comprovam diagnóstico clínico.
