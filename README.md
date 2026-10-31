# Tech Challenge Fase 4 — Monitoramento Multimodal em Saúde da Mulher

Extensão do assistente clínico da Fase 3 para a análise de **vídeo** e **áudio**, com geração de alertas para a equipe médica.

O sistema analisa vídeos de procedimentos ginecológicos e gravações de consultas, identifica sinais de risco em cada um e combina os dois resultados em um alerta único.

## Objetivos atendidos

- Detecção precoce de riscos em procedimentos ginecológicos (vídeo)
- Monitoramento do bem-estar psicológico pela voz (áudio)
- Uso de serviços em nuvem (Azure Speech)
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
| Áudio | Whisper + Random Forest | 1.200 falas sintéticas (Azure Speech) | Concluído (acurácia 0,88) |
| Integração | `combinar_audio_video` | Saídas das duas frentes | Em andamento |

## Organização

```text
audio/
├── datasets/      dataset_audio_emocoes_1200.zip (Git LFS)
└── notebooks/     TechChallengeFase4_audio.ipynb
video/
├── TechChallengeFase4_video.ipynb
└── alerta_video.py
integracao/        pipeline que junta áudio e vídeo no alerta final
relatorio/
└── secao_video.md
```

## Como executar

1. **Áudio:** ver a seção [Frente de áudio](#frente-de-áudio).
2. **Vídeo:** ver [`video/README.md`](video/README.md).
3. **Integração:** em andamento.

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

A divisão entre treino e teste é feita por frase original (`GroupShuffleSplit`), para que as variações de uma mesma fala não apareçam nos dois conjuntos.

| Classe | Precisão | Recall | F1 |
|---|---|---|---|
| ansiedade_hesitacao | 0,81 | 0,86 | 0,84 |
| neutro | 0,86 | 0,79 | 0,82 |
| tristeza | 0,97 | 1,00 | 0,99 |
| **Acurácia** | | | **0,88** |

## Frente de vídeo

YOLOv8 treinado para detectar útero e instrumentos cirúrgicos em laparoscopia ginecológica. O alerta dispara quando há instrumento em cena e o útero não é visto por 5 s ou mais. Detalhes em [`video/README.md`](video/README.md).

| Detector (teste) | mAP50 | | Alerta (teste) | Precisão | Recall |
|---|---|---|---|---|---|
| Geral | 0,928 | | `conf_area` = 0,6 | 1,00 | 0,72 |
| Útero | 0,950 | | | | |
| Instrumentos | 0,906 | | | | |

## Limitações

- Os áudios são sintéticos, gerados para demonstrar e validar o pipeline. Não representam gravações clínicas reais e não permitem, sozinhos, validação médica.
- O dataset de vídeo é pequeno (cerca de 570 imagens únicas) e a origem das imagens não é documentada pelo autor.
- Os alertas são sinais de triagem para revisão da equipe médica, não diagnósticos.
- Nenhum dado de paciente real foi usado ou enviado a serviços de terceiros.

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
