# Frente de vídeo — entrega final

A entrada recomendada é [TechChallengeFase4_video.ipynb](TechChallengeFase4_video.ipynb). O modo padrão lê as evidências salvas, sem GPU ou API. Treino e nova inferência são opcionais e utilizam os mesmos scripts da execução local.

- `scripts/video_reproduce.py`: ZIP auditado, polígonos convertidos em caixas e novo treino YOLOv8s.
- `scripts/video_infer_reserva.py`: montagens de teste/reserva, inferência real e relatório temporal.
- `video/alerta_video.py`: instrumento detectado sem detecção sustentada da área crítica por pelo menos cinco segundos; não confirma ausência anatômica.
- `video/qualidade.py`: compatibilidade de aparência por mediana/MAD; cenas incompatíveis interrompem a regra e exigem revisão.
- `scripts/video_calibrar_alertas.py`: busca somente na validação; candidato experimental não promovido.
- `scripts/video_preparar_referencia_visual.py`: referência de treino e retenção selecionada na validação.
- `scripts/video_verificar_externo.py` e `scripts/video_verificar_cobertura.py`: fonte didática externa, falso alerta original preservado e reserva temporal adicional.
- `evidence/video_reproducao.json`: novas métricas e modelo congelado.
- `evidence/video_inferencia_nova.json`: referência por caixas, eventos, tempos e ausência de sobreposição por hash.
- `evidence/resultado_video_teste.json`: exemplo positivo consumido pela integração; `resultado_video_novo.json` preserva a montagem reservada separadamente.

O modelo original de Marcelo não foi recuperado. O novo modelo parte de COCO, tem resultados próprios e não é apresentado como repetição exata daquele treinamento. Os resultados históricos continuam em `relatorio/secao_video.md` e `evidence/resultado_video_equipe.json`.

Veja [DATASETS_E_MODELOS.md](../DATASETS_E_MODELOS.md) para links, versões, hashes, comandos e restauração dos pesos privados. A reserva possui 60 quadros de um prefixo completamente fora do desenvolvimento. As montagens não equivalem a cirurgia contínua independente. Limiares 0,4/0,6 e regra temporal são mantidos sem ajuste na reserva.

Para movimento inespecífico, há também [fluxo óptico incremental](../integracao/MIDIAS.md). Ele não reconhece anatomia e tem evidência separada. Todos os sinais exigem revisão humana.

[Revisão e limitações](../relatorio/revisao_video.md): a proteção visual removeu um falso alerta sobre ilustração na fonte externa; os dois intervalos derivados de caixas da reserva continuam sem concordância e exigem revisão independente dos rótulos/detecções. Não foram alteradas as anotações nem o modelo para forçar esse resultado. As mídias externas não devem ser republicadas sem autorização.
