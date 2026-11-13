# Revisão do vídeo e das decisões — 11/11/2026

## Diagnóstico e limites da referência

O YOLO reconhece instrumento e também útero nos oito quadros que compõem os dois intervalos de referência da reserva. As caixas de útero não constam nas anotações desses quadros. Essa divergência bloqueia o alerta. Não foi confirmado se a causa é detecção espúria, marcação incompleta ou ambas. O peso e os rótulos originais permanecem preservados.

Os intervalos são derivados de caixas e da montagem de dois segundos por imagem. Não são duas complicações clínicas confirmadas. A concordância temporal continua 2/3 no teste e 0/2 na reserva; a correção de cobertura não transforma esse resultado em sucesso clínico.

## Calibração executada

Uma grade de 30 pares foi avaliada exclusivamente em 74 imagens de validação. O objetivo é macro-F1 por quadro para a condição “instrumento anotado e útero não anotado”. Limites temporais permanecem em cinco segundos e um segundo de tolerância. O alvo mede concordância com marcações, cuja exaustividade não está confirmada.

| Conjunto | Original 0,4/0,6 | Candidato 0,4/0,4 |
|---|---:|---:|
| Validação | 0,934 | 0,951 |
| Teste | 0,967 | 0,967 |
| Reserva já observada | 0,627 | 0,583 |

O candidato não foi promovido. A análise posterior da reserva conhecida não é uma nova avaliação cega. Não se aumentou a confiança de útero apenas para reproduzir os alertas desejados.

## Correções aplicadas

- Mediana/MAD de características de aparência: referência ajustada nas 776 imagens de treino, limite escolhido na validação para reter ao menos 95%. Grade 4/6/8/10; limite escolhido 4; retenção de 74/74, 37/37 e 60/60 em validação, teste e reserva.
- Cenas fora dessa referência interrompem a regra temporal imediatamente, sem se unir pela tolerância. Não são consideradas observações normais. Esse filtro de cores não identifica anatomia nem garante adequação clínica.
- Cobertura parcial, parâmetros, interpretação e limitações são preservados na fusão, nos relatórios e no painel. Um vídeo sem evento, mas com cobertura parcial, continua exigindo revisão. Um alerta alto não é cancelado por essa indicação.
- Entradas temporais, duração, presença booleana de classes e baixa confiança são verificadas. Leitura/gravação de imagens funciona em caminhos do Windows com acentos.

## Verificação externa

Fonte oficial: [TVASurg — Universidade de Toronto, Total Laparoscopic Hysterectomy](https://pie.med.utoronto.ca/TVASurg/project/gyn-tlh/). Não participou do treino, validação ou seleção dos limites do detector.

| Etapa | Intervalo da fonte | Quadros | Fora da referência | Sinais |
|---|---|---:|---:|---:|
| Original sem filtro | 150–240 s | 450 | Não aplicado | 1 |
| Revisão com filtro | 150–240 s | 450 | 73 | 0 |
| Nova reserva temporal com filtro | 240–330 s | 450 | 33 | 1 |

O alerta original ocorreu sobre uma ilustração de campos cirúrgicos, identificado por inspeção visual técnica. O registro original é preservado em `evidence/resultado_video_externo.json`. A proteção foi motivada por essa falha e não é apresentada como validação cega. O segundo intervalo foi definido antes da primeira inferência com a referência congelada; pertence à mesma fonte/paciente. Não há rótulos médicos/temporais para medir acertos e erros. O novo sinal é um pedido de revisão, não comprovação de falha cirúrgica. O pré-treino do modelo base não foi integralmente auditado.

As imagens são mantidas somente na pasta privada, com atribuição e sem inclusão no Git/PDF. A fonte declara direitos reservados; não republicar imagens na apresentação sem autorização. O roteiro pode mostrar os resultados sanitizados e apontar para a página oficial.

## Reprodução

```powershell
python scripts/video_calibrar_alertas.py
python scripts/video_preparar_referencia_visual.py
python scripts/video_infer_reserva.py
python scripts/video_verificar_externo.py --baixar
python scripts/video_verificar_cobertura.py
python scripts/video_validar_integracao.py
```

As três primeiras etapas exigem o dataset preparado e o peso privado; a fonte externa é opcional e o download é limitado a 200 MB. As chamadas à OpenAI são zero. Protocolos e hashes impedem trocar silenciosamente fonte, modelo, referência ou intervalo externo. Reexecutar os scripts não cria uma nova reserva.

## O que permanece sem comprovação

A divergência anatômica da reserva precisa de anotação independente, distinguindo presença, ausência confirmada e visibilidade inconclusiva. Uma planilha técnica com hashes e marcações existentes está em `evidence/video_divergencias_revisao.csv`, sem rótulos clínicos inventados. Só depois dessa revisão faria sentido retreinar e medir generalização em outra origem rotulada. Não se exige ensaio hospitalar adicional ao trabalho; explicita-se o alcance dos resultados do protótipo.
