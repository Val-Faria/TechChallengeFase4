# Integração de áudio, vídeo e texto

O notebook [TechChallengeFase4_integracao.ipynb](TechChallengeFase4_integracao.ipynb) reúne as saídas das frentes de áudio e vídeo e gera um alerta por caso. A análise textual Azure pode ser acrescentada ao mesmo resultado.

Responsável: Nirton Afonso de Oliveira Filho — RM 370221.

## Executar no Colab

1. Abra o Google Colab e faça upload do notebook.
2. Execute todas as células com os controles padrão. A demonstração usa a biblioteca padrão do Python e pode rodar em CPU.
3. Confira os quatro casos simulados e as verificações da seção 10.
4. Os arquivos ficam em `/content/TechChallenge4/integracao/saidas`.

O notebook é versionado sem saídas e sem metadados da sessão. A pasta [evidencias](evidencias) contém o registro das verificações locais.

## Modos de execução

Os controles ficam na primeira célula de código. Todos começam desligados.

| Controle | Função |
|---|---|
| `BAIXAR_AUDIO_DRIVE` | Baixa o modelo e o CSV compartilhados pela frente de áudio |
| `BAIXAR_DATASET_LFS` | Baixa o ZIP de áudio da versão do repositório indicada no notebook |
| `EXECUTAR_CSV_REAL` | Combina uma linha do CSV de áudio com o JSON de vídeo |
| `EXECUTAR_AUDIO_WAV` | Classifica um WAV com Whisper e o Random Forest salvo |
| `EXECUTAR_VIDEO` | Analisa um vídeo com os pesos YOLO fornecidos |
| `EXECUTAR_AZURE` | Transcreve o WAV com Azure Speech e analisa o texto com Azure Language |
| `EXECUTAR_INTEGRACAO` | Combina resultados dos modelos, CSV/JSON e texto Azure |

Os testes de áudio, vídeo e Azure podem ser executados separadamente. A confirmação de pareamento é exigida apenas nas etapas que combinam as fontes.

### Usar o CSV e o JSON existentes

Envie `resultado_audio.csv` e o JSON gerado pela frente de vídeo. Ajuste `CSV_AUDIO` e `JSON_VIDEO`, escolha o nome exato em `ARQUIVO_AUDIO_NO_CSV` e informe `ID_CASO_REAL`.

Depois de conferir a associação dos arquivos, ative `PAREAMENTO_CONFIRMADO` e `EXECUTAR_CSV_REAL`. Não é necessário executar novamente os modelos.

Para acrescentar a análise Azure a esses resultados, use `EXECUTAR_INTEGRACAO` no lugar de `EXECUTAR_CSV_REAL` e ative também `EXECUTAR_AZURE`.

Os datasets de áudio e vídeo são independentes. Os exemplos simulados do notebook demonstram a combinação dessas fontes sem atribuí-las ao mesmo paciente ou procedimento.

### Executar os modelos

| Etapa | Arquivos necessários |
|---|---|
| Áudio | `modelo_audio.joblib` e um WAV |
| Vídeo | `best_uterus_tools_v4.pt` e um vídeo |
| Integração por arquivo | CSV de áudio e JSON de vídeo |

O modelo de áudio foi salvo com scikit-learn 1.6.1. Use Python 3.11 ou 3.12 e as dependências indicadas no notebook. Se a instalação substituir uma biblioteca já importada, reinicie o ambiente antes de executar novamente.

Whisper continua fornecendo a transcrição usada no ritmo de fala, pois essa foi a representação usada no treinamento. A transcrição Azure alimenta a análise textual separadamente.

## Configurar o Azure

São necessários os serviços Speech e Language. No painel Secrets do Colab, cadastre e habilite o acesso para:

| Secret | Origem do valor |
|---|---|
| `SPEECH_KEY` | Chave do recurso Speech |
| `SPEECH_REGION` | Região do mesmo recurso Speech |
| `AZURE_LANGUAGE_KEY` | Chave do recurso Language |
| `AZURE_LANGUAGE_ENDPOINT` | Endpoint completo do recurso Language |

Informe o caminho de um WAV e ative `EXECUTAR_AZURE`. Para testar apenas a conexão, mantenha `EXECUTAR_INTEGRACAO = False`. O notebook salva `transcricao_azure.json` e `texto_azure.json` após a conclusão das duas chamadas.

As credenciais são lidas dos Secrets e não devem ser incluídas em células ou arquivos versionados. A execução contra os serviços reais ainda está pendente.

Referências: [Speech SDK](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/get-started-speech-to-text?pivots=programming-language-python) e [Text Analytics para Python](https://learn.microsoft.com/en-us/python/api/overview/azure/ai-textanalytics-readme?view=azure-python).

## Entradas e saídas

O áudio aceita uma tupla `(classe, confianca)` ou os campos `classe_audio` e `confianca_audio` do CSV. O vídeo segue o contrato documentado em [video/README.md](../video/README.md), com `alerta`, `nivel` e `eventos`.

A função `combinar_audio_video` preserva o maior nível entre os sinais válidos. Um áudio neutro não cancela um evento de vídeo. Uma fonte ausente, com erro ou baixa confiança mantém a indicação de cobertura incompleta.

| Arquivo gerado | Conteúdo |
|---|---|
| `<id_caso>.json` | Resultado completo com evidências por fonte |
| `<id_caso>.md` | Relatório automático do caso |
| `resultados.jsonl` | Todos os resultados do lote |
| `fila_revisao.jsonl` | Casos com sinal ou fonte inconclusiva |
| `resumo.csv` | Identificador, nível, cobertura e indicação de revisão |

A fila é um registro local para revisão humana. O protótipo processa arquivos em lote, sem confirmação de entrega a um sistema hospitalar.

## Verificação e pendências

- 49 verificações de contratos, regras, arquivos e respostas controladas do Azure aprovadas.
- O modelo compartilhado foi carregado com scikit-learn 1.6.1. A verificação em três WAVs usou o texto do metadata; Whisper não foi executado nessa verificação.
- A versão do ZIP contém 1.180 WAVs; o CSV compartilhado tem 1.200 linhas. A lista de nomes sem correspondente está no registro da auditoria.
- O README da versão-base informava acurácia 0,88; a saída salva no notebook de áudio registra 0,92. A reprodução da avaliação e a consolidação da métrica continuam pendentes.
- A inferência YOLO com os pesos da equipe e as chamadas Azure reais ainda precisam ser executadas.
- Os exemplos de sinais vitais, prescrições e movimento são sintéticos.

Detalhes no [relatório técnico](../relatorio/relatorio_tecnico.md) e na [matriz de requisitos](../relatorio/matriz_requisitos.md).
