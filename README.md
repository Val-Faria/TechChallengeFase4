# Tech Challenge — Contribuição de Áudio

Este repositório contém **somente a contribuição da frente de áudio** do Tech Challenge Fase 4. A implementação de vídeo, incluindo YOLOv8/YOLO Pose e a integração final do sistema, será desenvolvida por outro integrante do grupo.

## Entregas desta frente

- Geração de falas sintéticas rotuladas com Azure Speech;
- Classes `ansiedade_hesitacao`, `neutro` e `tristeza`;
- Expansão local do conjunto por aumento de dados;
- Transcrição com Whisper;
- Extração de pausas, ritmo e tom;
- Classificação das características acústicas;
- Estrutura de saída preparada para ser combinada ao resultado do vídeo no alerta final.

## Organização

```text
audio/
├── datasets/
│   └── dataset_audio_emocoes_1200.zip
└── notebooks/
    └── TechChallengeFase4_audio.ipynb
```

## Como executar

1. Abra `audio/notebooks/TechChallengeFase4_audio.ipynb` no Google Colab.
2. Cadastre `SPEECH_KEY` e `SPEECH_REGION` nos Secrets do Colab.
3. Execute as células em ordem.
4. Use o ZIP em `audio/datasets/` quando o dataset já estiver disponível.

## Observação metodológica

Os áudios são sintéticos e foram gerados para demonstração e validação do pipeline. Eles não representam gravações clínicas reais nem permitem, isoladamente, validação médica. O resultado desta frente deve ser integrado ao resultado de vídeo produzido pelo outro integrante.

## Tecnologias

- Azure Speech F0;
- OpenAI Whisper;
- Librosa;
- Scikit-learn;
- Google Colab.
