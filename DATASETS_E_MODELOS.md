# Dados e modelos

## Execução do painel

O repositório inclui os seis WAVs em `dados/audio/`, as duas montagens em `dados/video/`, as referências das vozes em `dados/referencias/` e os modelos em `artifacts/`. A instalação e o campo da chave da API estão descritos no [README](README.md). O painel usa essas entradas diretamente.

Os arquivos WebM em `dados/video/visualizacao/` permitem assistir às montagens no navegador. A inferência lê o MP4 e as imagens exibidas durante o processamento são quadros anotados nessa execução. O [manifesto de arquivos](dados/manifesto.json) registra tamanho e SHA-256. Consulte a [atribuição das mídias](dados/README.md).

## Corpus de voz

O corpus está em `audio/datasets/dataset_audio_emocoes_1180.zip`, armazenado por Git LFS. Contém 1.180 gravações sintéticas. O classificador congelado `artifacts/audio/modelo_audio_1180.joblib` utiliza as seis características registradas no manifesto e foi ajustado somente nos 712 exemplos de treino. As partições foram isoladas por família de frase. Métricas e ambiente constam em `evidence/audio_reproducao.json`.

Para repetir o experimento:

```powershell
git lfs pull
python scripts/audio_reproduce.py --device auto
```

As seis gravações do painel têm hashes e frases distintos do corpus. As referências de pausas foram obtidas com gravações anteriores da mesma voz. As alterações acústicas observadas precisam ser interpretadas no contexto de uma avaliação humana.

## Dataset visual

Fonte: [Uterus v4 no Roboflow Universe](https://universe.roboflow.com/machinelearning-yekk6/uterus-qn1he/dataset/4), disponibilizado por Machinelearning. A exportação declara licença CC BY 4.0 e está em `video/datasets/Uterus.v4i.yolov8.zip`, por Git LFS.

O ZIP possui 40.622.141 bytes e SHA-256 `d2345667a5efa840b7f1f3ff33af52ebf25d8ccf0f7c3c985afdeba6d7e04bf8`. A exportação contém 1.367 imagens, enquanto seu texto de apresentação informa 1.368. A auditoria preserva essa diferença.

Para preparar os dados e repetir o treinamento:

```powershell
git lfs pull
python scripts/video_reproduce.py --dataset-zip video/datasets/Uterus.v4i.yolov8.zip --audit-only
python scripts/video_reproduce.py --dataset-zip video/datasets/Uterus.v4i.yolov8.zip --epochs 80 --batch 8
```

O preparador verifica CRC, nomes, coordenadas e duplicatas. Os 418 polígonos utilizados são convertidos em caixas envolventes. A origem `UterusClip_mov` fornece 776/74/37 imagens de treino/validação/teste. As 60 imagens originais da origem `2024-09-26-20-27-33_mp4` formam a reserva. Suas versões aumentadas foram excluídas do desenvolvimento. A identidade inferida do nome do clipe limita a conclusão sobre independência por paciente.

O peso incluído em `artifacts/video/best_uterus_tools_nirton_v4.pt` foi selecionado pela validação. O manifesto registra seu hash e o ajuste apenas em treino. A referência visual em `artifacts/video/referencia_visual.json` contém a mediana/MAD do treino e o limite de retenção escolhido na validação.

`python scripts/video_infer_reserva.py` reconstrói e analisa as montagens a partir do dataset preparado. As saídas desse experimento são gravadas em `dados_privados/video_novo/`, com resultados sanitizados em `evidence/`. O painel lê as montagens distribuídas em `dados/video/`. Cada imagem ocupa dois segundos e os intervalos seguem essa transformação.

## Avaliação complementar

Os experimentos anteriores com a fonte externa [TVASurg](https://pie.med.utoronto.ca/TVASurg/project/gyn-tlh/) estão descritos em [Revisão do vídeo](relatorio/revisao_video.md). A mídia externa é obtida da fonte oficial para reprodução dessa avaliação complementar. O aplicativo utiliza as montagens do Uterus v4. Os resultados de fontes e protocolos diferentes permanecem identificados nas evidências.

## Credenciais e resultados

A chave OpenAI é informada no campo protegido do painel. Os comandos específicos de experimentação podem usar `OPENAI_API_KEY` ou o arquivo de ambiente indicado por sua interface. Resultados de consultas ficam em `integracao/saidas/painel/`. Os modelos congelados e os dados de entrada permanecem preservados durante o uso.
