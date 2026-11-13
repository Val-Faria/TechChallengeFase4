# Monitoramento multimodal em saúde da mulher

Tech Challenge · Fase 4 · FIAP · IA para Devs

Protótipo que combina voz, vídeo, texto e séries temporais para gerar sinais destinados à revisão humana. Os módulos usam contratos comuns, relatórios automáticos e uma caixa de alertas local. O relatório apresenta métodos, resultados e limitações do experimento.

## Entrega e demonstração

| Material | Acesso |
|---|---|
| Relatório final | [PDF](output/pdf/relatorio_tecnico_fase4.pdf) · [Overleaf](relatorio/overleaf_fase4.zip) |
| Demonstração integrada | [Notebook executado](integracao/TechChallengeFase4_integracao.ipynb) · [Abrir no Colab](https://colab.research.google.com/github/Val-Faria/TechChallengeFase4/blob/Nirton/integracao/TechChallengeFase4_integracao.ipynb) |
| Análise de áudio | [Notebook executado](audio/notebooks/TechChallengeFase4_audio.ipynb) · [Abrir no Colab](https://colab.research.google.com/github/Val-Faria/TechChallengeFase4/blob/Nirton/audio/notebooks/TechChallengeFase4_audio.ipynb) |
| Análise de vídeo | [Notebook executado](video/TechChallengeFase4_video.ipynb) · [Abrir no Colab](https://colab.research.google.com/github/Val-Faria/TechChallengeFase4/blob/Nirton/video/TechChallengeFase4_video.ipynb) |
| Dados e modelos | [Restauração e reprodução](DATASETS_E_MODELOS.md) |
| Requisitos e apresentação | [Matriz](relatorio/matriz_requisitos.md) · [Roteiro](relatorio/roteiro_demonstracao.md) |

Os notebooks contêm saídas de execução local, incluindo tabelas, gráficos e painel. Podem ser visualizados sem executar novamente. O áudio recalcula previsões com o modelo congelado; vídeo apresenta medições registradas; integração executa fusão, detectores e persistência. O modo padrão não faz chamadas pagas nem treina modelos.

## Executar localmente

Python 3.11 ou 3.12 para a integração; os experimentos publicados utilizam Python 3.12. As regras, a persistência e o painel usam a biblioteca padrão.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e . pytest
.venv\Scripts\python -m pytest -q
.venv\Scripts\python scripts/run_demo.py --output integracao/saidas/execucao_local --audio-csv audio/evidencias/resultado_audio_externo.csv --audio-filename novo-03.wav --video-json evidence/resultado_video_teste.json --text-json evidence/texto_openai_integracao.json
.venv\Scripts\python -m techchallenge4.dashboard --db integracao/saidas/execucao_local/alertas.sqlite3
```

Abra o endereço local exibido. A confirmação registra responsável e instante na caixa de revisão; não altera tratamentos. Saídas novas ficam em `integracao/saidas/`, fora do versionamento, preservando as evidências publicadas.

Para executar e salvar as saídas dos três notebooks:

```powershell
python -m pip install -r requirements-notebooks.txt
python scripts/executar_notebooks.py
```

## Fluxo e organização

```mermaid
flowchart LR
 A[Áudio] --> W[Whisper, Librosa e Random Forest]
 V[Vídeo] --> Y[YOLOv8 e regra temporal]
 T[Transcrição] --> L[Análise textual OpenAI]
 S[Sinais vitais, prescrições e movimento] --> D[Detectores temporais]
 W --> F[Fusão por caso, origem e prioridade]
 Y --> F
 L --> F
 D --> F
 F --> R[Relatórios e caixa SQLite]
 R --> P[Painel de revisão]
```

| Diretório | Responsabilidade |
|---|---|
| `src/techchallenge4/` | Contratos, fusão, detectores, nuvem, entrega, painel e suporte aos notebooks |
| `audio/`, `video/` | Notebooks, regras visuais e documentação das modalidades |
| `integracao/` | Demonstração integrada e resultados de referência |
| `scripts/` | Extração, avaliação, reprodução e geração de artefatos |
| `tests/` | Regressões de contratos, regras, cache, orçamento e persistência |
| `evidence/`, `artifacts/` | Métricas, partições, proveniência e manifestos de modelos |
| `relatorio/` | Fonte LaTeX, Overleaf, matriz de requisitos e roteiro |
| `output/pdf/` | Relatório final compilado |

A execução de referência está em `integracao/evidencias/revisao_final_20261111/`. Os controles externos estão em `revisao_video_externo_20261111/`; o monitor estruturado, em `monitoramento_final/`. Resultados anteriores ficam em `integracao/evidencias/historico/` e não substituem a avaliação atual.

## Resultados e alcance

- **Áudio:** 1.180 gravações sintéticas, partições isoladas por família de frase. A reserva tem acurácia de 88,33%. As seis falas externas ficaram abaixo do limiar de confiança e são inconclusivas.
- **Vídeo:** novo YOLOv8s, mAP50 de 0,980 no teste e 0,613 na reserva de origem. A regra pareou 2/3 intervalos derivados de caixas no teste e 0/2 na reserva. Ausência de caixa não confirma ausência anatômica; a divergência exige revisão das anotações e das detecções.
- **Nuvem:** transcrição e análise textual reais da OpenAI, com resultados salvos, negação/contexto e consumo registrado. A substituição do Azure foi [autorizada pelo professor](evidence/orientacao_docente.md).
- **Alertas:** monitoramento incremental, caixa SQLite e confirmação auditável. Baixa confiança ou cobertura parcial não são convertidas em normalidade.

O conjunto não representa pacientes pareados. Séries estruturadas e controles físicos são sintéticos. A proteção visual removeu um falso alerta sobre ilustração em uma fonte didática externa; não demonstra detecção clínica confiável. [Detalhes da avaliação de vídeo](relatorio/revisao_video.md).

## Reprodução e credenciais

O [guia de dados e modelos](DATASETS_E_MODELOS.md) contém hashes, fontes e caminhos de restauração. Áudio, vídeo e análise de mídias têm dependências opcionais próprias. Reproduções de treinamento são experimentos separados da visualização dos notebooks.

`OPENAI_API_KEY` é necessária somente para novas chamadas; usar variável de ambiente ou Secret do Colab. Há cache e controle local de consumo, que não substituem os limites de cobrança da conta. Credenciais e mídias privadas não integram os pacotes públicos. Ao usar GPU opcional no Colab, salvar os artefatos e desconectar/excluir o ambiente ao terminar.

## Equipe e apresentação

| Integrante | RM | Participação |
|---|---|---|
| Marcelo Viana de Araújo | 372707 | Vídeo |
| Nirton Afonso de Oliveira Filho | 370221 | Integração e relatório |
| Valkiria Nonato de Faria | 373256 | Áudio |
| Benicio Antonio Cardoso | 371527 | Apresentação |

A gravação deve ter até 15 minutos e ser publicada no YouTube ou Vimeo. Inserir o link no relatório e nesta página após a publicação. O [roteiro](relatorio/roteiro_demonstracao.md) organiza a demonstração e as restrições de uso das imagens de terceiros.
