# Frente de vídeo

Detecção de **útero** e **instrumentos cirúrgicos** em vídeos de laparoscopia ginecológica com YOLOv8, e alerta quando há instrumento em cena sem o útero visível.

## Arquivos

| Arquivo | O que faz |
|---|---|
| `TechChallengeFase4_video.ipynb` | Notebook completo: dataset, treino, avaliação, demonstração e avaliação do alerta |
| `alerta_video.py` | Função `analisar_video`: roda o modelo num vídeo e gera o alerta, o relatório e o vídeo anotado |

## Como executar

1. No Google Drive, crie `MyDrive/TechChallenge4/` com:
   - `Uterus.v4i.yolov8.zip` (dataset em formato YOLOv8, link abaixo)
   - `frente_video/video/alerta_video.py`
2. Abra o notebook no Colab com **T4 GPU** e rode as células em ordem.
3. O treino é pulado se `best_uterus_tools_v4.pt` já estiver na pasta.

Para usar só o alerta (por exemplo, na integração):

```python
from alerta_video import analisar_video
resultado_video = analisar_video("cirurgia.mp4", "best_uterus_tools_v4.pt")
```

## Dataset

**Uterus v4** — Roboflow Universe, licença CC BY 4.0.
https://universe.roboflow.com/machinelearning-yekk6/uterus-qn1he/dataset/4

- Classes: `Tools` (instrumentos) e `Uterus` (útero)
- Divisão: 1.197 treino / 114 validação / 57 teste (o treino inclui 3 versões aumentadas de cada imagem)
- O dataset não é versionado neste repositório.

## Regra de alerta

Alerta quando há **instrumento em cena** (confiança ≥ 0,4) e o **útero não é visto** (confiança ≥ 0,6) por **5 s ou mais**. Falhas de detecção de até 1 s não interrompem o trecho.

O útero exige confiança maior para que detecções fracas ("útero fantasma") não escondam um evento. O valor 0,6 foi escolhido no conjunto de validação.

| Nível | Critério |
|---|---|
| baixo | maior trecho ≥ 5 s |
| médio | maior trecho ≥ 10 s |
| alto | maior trecho ≥ 15 s, ou 3 ou mais trechos |

## Saída (`resultado_video`)

```json
{
  "alerta": true,
  "nivel": "alto",
  "motivo": "2 trecho(s) com instrumento ativo e útero fora de vista",
  "eventos": [
    {"descricao": "Instrumento em cena sem visualização do útero por 6.0 s",
     "inicio_s": 76.0, "fim_s": 82.0, "duracao_s": 6.0, "confianca": 0.81,
     "quadro": "saida_video/video_test_evento1.jpg"}
  ],
  "estatisticas": {"duracao_video_s": 114.0, "quadros_analisados": 570,
                   "prop_quadros_com_utero": 0.54, "prop_quadros_com_instrumento": 0.825,
                   "prop_instrumento_sem_utero": 0.425},
  "relatorio": "saida_video/relatorio_video_test.md",
  "video_anotado": "saida_video/video_test_anotado.mp4"
}
```

A chave `alerta` é a que a função `combinar_audio_video` (frente de áudio) lê.

Arquivos gerados na pasta de saída: o relatório automático (`relatorio_<video>.md`), o resultado completo (`resultado_<video>.json`), o vídeo anotado e a imagem de cada evento.

## Resultados

### Detector (conjunto de teste, 56 imagens)

| Classe | mAP50 | mAP50-95 | Precisão* | Recall* |
|---|---|---|---|---|
| Geral | 0,928 | 0,636 | — | — |
| Tools | 0,906 | 0,538 | 0,87 | 0,84 |
| Uterus | 0,950 | 0,734 | 0,70 | 0,95 |

\* No limiar de operação (confiança 0,4), calculados pela matriz de confusão.

### Alerta (vídeos montados com as imagens de cada conjunto, 2 s por imagem)

| Conjunto | `conf_area` | Precisão | Recall |
|---|---|---|---|
| Validação | 0,4 | 1,00 | 0,84 |
| Validação | **0,6 (escolhido)** | **1,00** | **0,98** |
| Teste | 0,4 | 1,00 | 0,64 |
| Teste | **0,6** | **1,00** | **0,72** |

## Limitações

- Dataset pequeno (cerca de 570 imagens únicas) e de origem não documentada pelo autor.
- Os quadros trazem a marca d'água "Dr R K Mishra", indicando origem em vídeos educativos de terceiros. Não versione a pasta de saída (imagens e vídeos gerados).
- Treino e teste podem conter quadros do mesmo clipe, o que deixa as métricas otimistas.
- O alerta foi avaliado em montagens das imagens do dataset, não em uma cirurgia contínua.
- O teste é pequeno: no alerta, cada imagem perdida vale cerca de 4 pontos de recall.
- A regra é heurística: o útero pode sair de cena por motivos normais do procedimento. O alerta é um sinal de triagem para revisão humana, não um diagnóstico.
