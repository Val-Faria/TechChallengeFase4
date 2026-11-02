# Tech Challenge Fase 4 — Monitoramento Multimodal em Saúde da Mulher

Extensão do assistente clínico da Fase 3 para a análise de **vídeo** e **áudio**, com geração de alertas para a equipe médica.

O sistema analisa vídeos de procedimentos ginecológicos e gravações de consultas, identifica sinais de risco em cada um e combina os dois resultados em um alerta único.

## Escopo do protótipo

- Identificação de perda de visualização da área crítica em vídeos ginecológicos
- Classificação de características acústicas em falas sintéticas
- Síntese com Azure Speech e conectores para transcrição e análise textual
- Detecção de anomalias com alerta multimodal

## Arquitetura

```text
Vídeo cirúrgico ──► YOLOv8 (útero + instrumentos) ──► regras de anomalia ──┐
                                                                           ├──► Fusão ──► Alerta (JSONL)
Áudio da consulta ─► Whisper + librosa ─► classificador (Random Forest) ───┘
```

| Frente | Modelo | Dados | Status |
|---|---|---|---|
| Vídeo | YOLOv8 customizado | Uterus v4 (Roboflow Universe, CC BY 4.0) | Concluído (mAP50 0,928) |
| Áudio | Whisper + Random Forest | Falas sintéticas (Azure Speech) | Implementado; avaliação registrada no notebook |
| Integração | `combinar_audio_video` | Áudio, vídeo e texto opcional | Demonstração e 49 verificações aprovadas; Azure real pendente |

## Organização

```text
audio/
├── datasets/      dataset_audio_emocoes_1200.zip (Git LFS)
└── notebooks/     TechChallengeFase4_audio.ipynb
video/
├── TechChallengeFase4_video.ipynb
└── alerta_video.py
integracao/
├── TechChallengeFase4_integracao.ipynb
├── README.md
└── evidencias/
relatorio/
├── relatorio_tecnico.md
├── matriz_requisitos.md
├── roteiro_demonstracao.md
└── secao_video.md
```

## Como executar

1. **Áudio:** ver a seção [Frente de áudio](#frente-de-áudio).
2. **Vídeo:** ver [`video/README.md`](video/README.md).
3. **Integração:** abra `integracao/TechChallengeFase4_integracao.ipynb` no Colab. A demonstração padrão usa CPU e dispensa credenciais. Veja [integracao/README.md](integracao/README.md).

> O dataset de áudio está no Git LFS. Após clonar o repositório, rode `git lfs install` e `git lfs pull`. Sem isso, o ZIP baixado é só um arquivo de referência de poucos bytes.

## Frente de áudio

### O que faz

- Gera falas sintéticas rotuladas com Azure Speech, nas classes `ansiedade_hesitacao`, `neutro` e `tristeza`
- Expande o conjunto localmente com aumento de dados (velocidade, ruído etc.), chegando a 1.200 áudios
- Transcreve com Whisper
- Extrai pausas, ritmo e tom
- Classifica as características acústicas com Random Forest
- Gera uma saída pronta para ser combinada ao resultado do vídeo no alerta final

### Como executar

1. Abra `audio/notebooks/TechChallengeFase4_audio.ipynb` no Google Colab.
2. Cadastre `SPEECH_KEY` e `SPEECH_REGION` nos Secrets do Colab.
3. Execute as células em ordem.
4. Se o dataset já estiver disponível, use o ZIP em `audio/datasets/` e pule a geração.

### Resultado

A divisão entre treino e teste é feita por gravação original (`GroupShuffleSplit`), para que as variações de uma mesma fala não apareçam nos dois conjuntos.

| Classe | Precisão | Recall | F1 |
|---|---|---|---|
| ansiedade_hesitacao | 0,93 | 0,84 | 0,88 |
| neutro | 0,81 | 0,91 | 0,85 |
| tristeza | 1,00 | 1,00 | 1,00 |
| **Acurácia** | | | **0,92** |

Métricas da saída salva no notebook de áudio, em 240 exemplos de teste. A versão anterior deste README informava 0,88; a avaliação ainda precisa ser reproduzida para consolidar o resultado.

O ZIP do Git LFS contém 1.180 WAVs e 1.180 linhas de metadata, enquanto o CSV compartilhado contém 1.200 predições. A diferença está registrada no [relatório técnico](relatorio/relatorio_tecnico.md).

## Frente de vídeo

YOLOv8 treinado para detectar útero e instrumentos cirúrgicos em laparoscopia ginecológica. O alerta dispara quando há instrumento em cena e o útero não é visto por 5 s ou mais. Detalhes em [`video/README.md`](video/README.md).

| Detector (teste) | mAP50 | | Alerta (teste) | Precisão | Recall |
|---|---|---|---|---|---|
| Geral | 0,928 | | `conf_area` = 0,6 | 1,00 | 0,72 |
| Útero | 0,950 | | | | |
| Instrumentos | 0,906 | | | | |

## Integração

O notebook de integração aceita a classe/confiança do áudio e o JSON da frente de vídeo. A regra preserva a maior prioridade entre os sinais válidos e registra fontes ausentes, com erro ou baixa confiança.

São gerados um JSON e um relatório por caso, um resumo CSV e uma fila local de revisão em JSONL. A demonstração usa quatro casos simulados. As chamadas Azure podem ser testadas separadamente antes da integração final.

A preparação dos arquivos e os quatro Secrets necessários estão em [integracao/README.md](integracao/README.md). O [relatório técnico consolidado](relatorio/relatorio_tecnico.md) descreve o fluxo, os modelos e os resultados. A [matriz de requisitos](relatorio/matriz_requisitos.md) relaciona as evidências e as etapas pendentes.

## Limitações

- Os áudios são sintéticos, gerados para demonstrar e validar o pipeline. Não representam gravações clínicas reais e não permitem, sozinhos, validação médica.
- O dataset de vídeo é pequeno (cerca de 570 imagens únicas) e a origem das imagens não é documentada pelo autor.
- Os alertas são sinais de triagem para revisão da equipe médica, não diagnósticos.
- Nenhum dado de paciente real foi usado ou enviado a serviços de terceiros.

- Áudio e vídeo são de datasets independentes, sem sincronização por paciente ou procedimento.
- As chamadas reais de Azure Speech to Text e Language ainda estão pendentes.
- Os exemplos adicionais de sinais vitais, prescrições e movimento são sintéticos.
- A fila de revisão é local; o processamento ocorre em lote.

## Tecnologias

- Azure Speech (camada F0)
- OpenAI Whisper
- Librosa
- Scikit-learn
- Ultralytics YOLOv8
- Google Colab

## Fontes

- **Uterus Dataset v4** — Roboflow Universe, CC BY 4.0. https://universe.roboflow.com/machinelearning-yekk6/uterus-qn1he/dataset/4

## Vídeo de demonstração

Link: em breve.

## Equipe

| Nome | RM |
|------|-----|
| Benicio Antonio Cardoso | 371527 |
| Marcelo Viana de Araújo | 372707 |
| Nirton Afonso de Oliveira Filho | 370221 |
| Valkiria Nonato de Faria | 373256 |
