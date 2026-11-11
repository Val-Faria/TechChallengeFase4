# Frente de vídeo — entrega final

A entrada recomendada é [TechChallengeFase4_video.ipynb](TechChallengeFase4_video.ipynb). O modo padrão lê as evidências salvas, sem GPU ou API. Treino e nova inferência são opcionais e utilizam os mesmos scripts da execução local.

- `scripts/video_reproduce.py`: ZIP auditado, polígonos convertidos em caixas e novo treino YOLOv8s.
- `scripts/video_infer_reserva.py`: montagens de teste/reserva, inferência real e relatório temporal.
- `video/alerta_video.py`: regra instrumento presente/útero ausente por pelo menos cinco segundos.
- `evidence/video_reproducao.json`: novas métricas e modelo congelado.
- `evidence/video_inferencia_nova.json`: referência por caixas, eventos, tempos e ausência de sobreposição por hash.
- `evidence/resultado_video_novo.json`: resultado sanitizado consumido pela integração.

O modelo original de Marcelo não foi recuperado. O novo modelo parte de COCO, tem resultados próprios e não é apresentado como repetição exata daquele treinamento. Os resultados históricos continuam em `relatorio/secao_video.md` e `evidence/resultado_video_equipe.json`.

Veja [DATASETS_E_MODELOS.md](../DATASETS_E_MODELOS.md) para links, versões, hashes, comandos e restauração dos pesos privados. A reserva possui 60 quadros de um prefixo completamente fora do desenvolvimento. As montagens não equivalem a cirurgia contínua independente. Limiares 0,4/0,6 e regra temporal são mantidos sem ajuste na reserva.

Para movimento inespecífico, há também [fluxo óptico incremental](../integracao/MIDIAS.md). Ele não reconhece anatomia e tem evidência separada. Todos os sinais exigem revisão humana.
