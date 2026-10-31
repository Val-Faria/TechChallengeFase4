# Frente de vídeo — análise de cirurgias ginecológicas

## 1. Objetivo e categoria monitorada

A frente de vídeo monitora **sinais de complicação em cirurgias ginecológicas laparoscópicas**. O indicador escolhido é a **perda de visualização da área crítica**: trechos em que há instrumento cirúrgico em cena, mas o útero não está visível. Instrumento ativo fora do campo de visão da estrutura em operação é uma situação que merece atenção da equipe, seja por desvio de procedimento, mudança brusca de campo ou perda de referência anatômica.

O resultado é um **sinal de triagem** para revisão humana, não um diagnóstico.

## 2. Fluxo da frente de vídeo

```text
Vídeo cirúrgico
   │  amostragem: 5 quadros por segundo
   ▼
YOLOv8 customizado ── detecta "Tools" (instrumentos) e "Uterus" (útero) em cada quadro
   │
   ▼
Regra temporal ── instrumento presente E útero ausente por ≥ 5 s seguidos
   │               (falhas de até 1 s não interrompem o trecho)
   ▼
resultado_video ── { alerta, nivel, motivo, eventos[], estatisticas }
   │
   ├──► relatório automático (Markdown) + vídeo anotado + imagem de cada evento
   └──► fusão com o resultado do áudio (combinar_audio_video) ──► alerta à equipe
```

## 3. Modelo aplicado

| Item | Escolha |
|---|---|
| Arquitetura | YOLOv8s (Ultralytics), 11,1 milhões de parâmetros |
| Estratégia | Fine-tuning a partir de pesos pré-treinados no COCO |
| Dataset | Uterus v4, Roboflow Universe, CC BY 4.0 |
| Classes | `Tools` (instrumentos) e `Uterus` (útero) |
| Divisão | 1.197 treino / 114 validação / 57 teste |
| Resolução | 416 × 416 |
| Treino | até 80 épocas, parada antecipada com paciência 20, batch 16, GPU T4 (Colab) |

O conjunto de treino inclui 3 versões aumentadas de cada imagem original (espelhamento, cisalhamento, saturação), o que corresponde a cerca de 400 imagens únicas no treino. As caixas no treino somam 1.466 de instrumentos e 515 de útero, uma proporção de quase 3 para 1.

## 4. Resultados

### 4.1 Detector

Avaliação no conjunto de teste (56 imagens; uma foi descartada pela biblioteca por misturar polígono e caixa na anotação):

| Classe | mAP50 | mAP50-95 | Precisão* | Recall* |
|---|---|---|---|---|
| **Geral** | **0,928** | **0,636** | — | — |
| Tools | 0,906 | 0,538 | 0,87 | 0,84 |
| Uterus | 0,950 | 0,734 | 0,70 | 0,95 |

\* No limiar de operação (confiança 0,4), calculados a partir da matriz de confusão.

Apesar de ter quase 3 vezes menos exemplos, o útero teve desempenho melhor que os instrumentos. O útero é uma estrutura grande e de forma regular. Os instrumentos são finos, aparecem vários por imagem e ficam parcialmente encobertos com frequência.

O ponto fraco identificado foi o **"útero fantasma"**: em 8 casos o modelo detectou útero onde não havia (precisão de 0,70 para a classe). Para a regra de alerta isso é crítico, porque um útero falso faz o sistema acreditar que a área crítica está visível e esconde um evento real.

### 4.2 Ajuste da regra de alerta

Para reduzir o efeito do útero fantasma, a regra passou a exigir **confiança maior para o útero** (`conf_area`) do que para o instrumento (0,4). O limiar foi escolhido no conjunto de **validação**, e só depois medido no teste, para que o número final não seja otimista.

Para medir o alerta, as imagens de cada conjunto foram montadas em um vídeo (2 s por imagem) e comparadas com a anotação:

| Conjunto | `conf_area` | Precisão | Recall |
|---|---|---|---|
| Validação | 0,4 | 1,00 | 0,84 |
| Validação | 0,5 | 1,00 | 0,85 |
| Validação | **0,6** | **1,00** | **0,98** |
| Validação | 0,7 | 0,96 | 0,98 |
| Teste | 0,4 (antes) | 1,00 | 0,64 |
| Teste | **0,6 (escolhido)** | **1,00** | **0,72** |

- **Precisão:** fração dos quadros sinalizados que de fato tinham instrumento e não tinham útero.
- **Recall:** fração dos trechos reais de 6 s ou mais que foram sinalizados.

O valor 0,6 maximiza o recall na validação sem nenhum alarme falso; 0,7 não traz ganho e passa a errar. No teste, o ajuste elevou o recall de 0,64 para 0,72, mantendo a precisão em 1,00.

A diferença entre validação (0,98) e teste (0,72) se explica pelo tamanho do teste: apenas 25 imagens pertencem a trechos que contam, então cada imagem perdida vale cerca de 4 pontos de recall.

### 4.3 Exemplos de anomalias detectadas

No vídeo de teste (114 s), o sistema gerou alerta de **nível alto** com dois eventos:

| Evento | Trecho | Duração | Verificação pela anotação |
|---|---|---|---|
| 1 | 01:16 – 01:22 | 6 s | 3 de 3 imagens corretas |
| 2 | 01:24 – 01:54 | 30 s | todas as imagens do trecho corretas |

As imagens de cada evento e o vídeo anotado estão em `saida_video/` e fazem parte da demonstração. Todo o processo está no notebook `video/TechChallengeFase4_video.ipynb`.

**Casos não detectados.** Dois trechos reais de 6 s escaparam:
- imagens 25–27: na imagem 25 o modelo não detectou o instrumento e detectou útero inexistente, quebrando o trecho em apenas 4 s;
- imagens 34–36: útero fantasma com confiança alta nas imagens 35 e 36.

## 5. Relatório automático

Para cada vídeo analisado, o sistema gera automaticamente:
- `relatorio_<video>.md`: resumo, lista de eventos com início, fim, duração e confiança, imagem de cada evento e critério usado;
- `resultado_<video>.json`: o `resultado_video` completo, usado pela integração com o áudio;
- `<video>_anotado.mp4`: vídeo com as caixas e o aviso "ÚTERO FORA DE VISTA";
- uma imagem do momento central de cada evento.

Das quatro categorias de relatório automático do enunciado, esta frente cobre **sinais de complicações em cirurgias ginecológicas**. Desvios em procedimentos obstétricos, indicadores visuais de desconforto psicológico e alertas de violência doméstica exigiriam dados de outra natureza (partos, consultas e triagem filmadas) e ficam como trabalho futuro.

## 6. Limitações

- **Dataset pequeno e de origem não documentada:** cerca de 570 imagens únicas; o autor não informa de onde vieram os vídeos. As imagens não foram republicadas neste repositório.
- **Imagens de terceiros:** os quadros trazem a marca d'água "Dr R K Mishra", o que indica que foram extraídos de vídeos educativos de cirurgia publicados por terceiros. Por isso as imagens e os vídeos gerados não são versionados no repositório, e o vídeo de demonstração é publicado como não listado.
- **Possível vazamento entre treino e teste:** os nomes dos arquivos indicam quadros extraídos de clipes, e quadros vizinhos de um mesmo clipe podem estar em conjuntos diferentes. As métricas do detector podem estar otimistas.
- **Vídeo de avaliação montado:** o alerta foi medido em montagens das imagens do dataset, não em uma cirurgia contínua.
- **Imagens esticadas para 416 × 416** no pré-processamento, o que pode reduzir o desempenho em vídeos com outra proporção.
- **Regra heurística:** o útero pode sair de cena por motivos normais do procedimento. A regra não distingue esses casos de uma situação de risco, por isso o resultado é um sinal de triagem.

## 7. Fonte do dataset

Machinelearning. *Uterus Dataset*, versão 4. Roboflow Universe, 2024. Licença CC BY 4.0. Disponível em: https://universe.roboflow.com/machinelearning-yekk6/uterus-qn1he/dataset/4
