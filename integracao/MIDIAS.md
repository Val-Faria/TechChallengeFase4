# Voz e vídeo: execução direta sobre mídias

Os módulos complementares recebem PCM e quadros. Não usam classes, caixas ou eventos prontos para decidir. Acrescentam sinais observacionais e não alteram o classificador emocional ou as métricas YOLO anteriores.

## Demonstração preparada no computador do grupo

```powershell
.venv\Scripts\python -m pip install -e . -r requirements-media.txt
# Executar uma vez, caso as novas gravações ainda não existam:
& scripts\gerar_cenarios_midias.ps1
.venv\Scripts\python scripts\validar_midias.py
```

O gerador requer Windows e as vozes Daniel e Maria Desktop. Recusa sobrescrever as gravações reservadas. Se `dados_privados/midias_complementares/manifesto_sintese.json` já existe, pule a geração. A validação dura aproximadamente um minuto e não utiliza API paga, treinamento ou GPU.

As seis novas sínteses são distintas por hash do corpus e das provas externas anteriores. Para cada voz, duas gravações formam a referência; uma terceira, de conteúdo novo, fica reservada. Versões com volume reduzido, pausas inseridas e silêncio verificam o comportamento físico. As derivações compartilham a gravação-fonte e não são amostras clínicas independentes.

Dois vídeos geométricos novos verificam fluxo óptico, aquecimento da referência, persistência, fusão e entrega. A montagem da equipe também é decodificada e processada. Nenhum destes procedimentos reproduz a inferência anatômica YOLO.

## Executar e mostrar os alertas

```powershell
.venv\Scripts\python -m techchallenge4.media_stream --video dados_privados/midias_complementares/movimento_movimento.mp4 --audio dados_privados/midias_complementares/daniel-interrompido.wav --reference dados_privados/midias_complementares/referencia_daniel.json --output output/private/apresentacao_midias --case-id apresentacao-midias --paced --simulated
.venv\Scripts\python -m techchallenge4.dashboard --db output/private/apresentacao_midias/alertas.sqlite3
```

O diretório de saída recebe `eventos_midia.jsonl`, `resumo_midia.json`, `relatorio_midia.md` e a caixa SQLite. O painel permite confirmar revisão. O diário registra inferência e cobertura em cada passo, inclusive aquecimento e áudio vencido. A caixa recebe transições com sinal, evitando uma tarefa idêntica por quadro.

A entrada é um arquivo reproduzido no ritmo original. A medida por passo inclui características acústicas, fluxo óptico, fusão e persistência; a medida total inclui inicialização e espera. A janela de voz acumula cinco segundos antes da primeira decisão. ASR, texto em nuvem e câmera/microfone ao vivo estão fora desta medição. `--text-source` anexa uma resposta OpenAI previamente validada, associada manualmente, sem apresentá-la como inferência de nuvem ao vivo.

## Usar outros arquivos

```powershell
python scripts/preparar_referencia_voz.py --audio referencia1.wav referencia2.wav --speaker voz-001 --output referencia.json
python -m techchallenge4.media_stream --video video.mp4 --audio consulta.wav --reference referencia.json --output resultados --case-id caso-001 --paced
```

Use referência anterior da mesma voz e condições de gravação comparáveis. Não inclua a gravação avaliada na referência. O comando recusa áudio cujo hash conste entre as referências. Marque `--simulated` ao usar mídias construídas; a origem sintética da referência também é preservada.

## Critérios e limites

- **Voz:** exige aumento de pausas ≥0,20 e trecho vocal mediano ≤65% da referência. Janela curta, saturação ou voz insuficiente ficam inconclusivas. A estimativa de atividade vocal usa energia, podendo confundir ruído. Não reconhece respirações nem estima doença ou fadiga clínica.
- **Vídeo:** fluxo óptico de Farnebäck, remoção da translação global mediana, referência inicial de 30 amostras congelada e aumento persistente de movimento. Câmera instável ou quadro sem informação ficam inconclusivos. Zoom, rotação, iluminação e anotações podem interferir. Não reconhece anatomia, postura ou complicação.
- **Sem mudança detectada:** significa somente que a regra não foi atingida; não comprova normalidade clínica. A montagem recebida não gerou aumento persistente pelo fluxo óptico, embora tenha dois eventos anatômicos na análise histórica YOLO.

Evidência consolidada: [midias_complementares.json](../evidence/midias_complementares.json). O estudo de [Rashid et al.](https://arxiv.org/abs/2011.09270) motiva investigar pausas e padrões vocais; seu classificador, população e métricas não foram transferidos. A implementação visual segue a [documentação primária do OpenCV](https://docs.opencv.org/4.x/d4/dee/tutorial_optical_flow.html).

Para reproduzir especificamente instrumento/útero, continua necessário receber `best_uterus_tools_v4.pt` e executar o módulo original. A segunda rota é executável sem esse artefato, com escopo diferente.
