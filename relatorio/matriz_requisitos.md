# Matriz de requisitos e evidências

Referência: **IADT - Fase 4 - Tech challenge.pdf**, páginas 2-4. Consolidação: **10/11/2026**.

O professor Wagner Santos autorizou serviços alternativos ao Azure em esclarecimento de 09/11/2026. Essa autorização não dispensa análise de vídeo, áudio, anomalias, integração e alertas. A versão utiliza Whisper para o ritmo acústico e OpenAI para transcrição dos WAVs novos e análise textual.

**Executado** indica saída verificável nesta consolidação. **Relatado** identifica resultados anteriores da frente responsável. **Sintético/controlado** caracteriza o dado; não representa validação clínica.

| Requisito | Implementação e evidência | Cobertura e limites |
|---|---|---|
| Processar vídeos clínicos | Notebook/módulo YOLO da equipe; pacote de Marcelo decodificado, 570 quadros a 5 FPS | YOLO integrado por resultado; fluxo óptico complementar executado nos quadros sem peso privado |
| Detectar eventos fora do padrão | Regra instrumento presente/útero ausente; eventos 76-82 s e 84-114 s reproduzidos das detecções salvas | Heurística anatômica histórica; novo detector mede aumento persistente de movimento, sem diagnosticar complicação |
| Verificação inédita do processamento de vídeo | Dois novos clipes geométricos com fluxo óptico real; `evidence/midias_complementares.json` | Verifica inferência de movimento em cenários controlados; não mede generalização YOLO ou clínica |
| Relatório automático | Markdown/JSON de vídeo e relatórios multimodais por caso | Saídas com evidências para revisão humana |
| Processar áudio e alterações vocais | Whisper, Librosa e Random Forest; `evidence/audio_reproducao.json` | Comparação intra-voz de pausas e trechos vocais acrescentada; controles físicos, sem rótulo médico |
| Amostras não vistas pelo classificador | Famílias de frase-base separadas; verificação cega fora de treino/validação/teste | Isolamento do modelo regenerado; mesmo domínio e voz sintéticos |
| Transcrição e texto em nuvem | Whisper para ritmo acústico; transcrição e análise textual OpenAI, com trechos e negação | Fornecedor alternativo autorizado; síntese Azure não é transcrição |
| Termos críticos e sentimentos | Menção afirmada/negada/incerta, contexto, evidência literal e sentimento | Interpretação da LLM requer revisão |
| Anomalias em sinais vitais | Mediana/MAD sobre histórico anterior e observações posteriores | Dados sintéticos e limiar estatístico |
| Evolução de prescrições | Comparação temporal de dose, unidade, via e intervalo | Regras demonstrativas; não recomenda tratamento |
| Movimentação | Detector de série numérica temporal | Não extrai postura clínica do vídeo |
| Fusão multimodal | Contrato por caso, maior prioridade e fontes inconclusivas | Fontes independentes, sem pareamento clínico |
| Alerta automático | Caixa SQLite, painel local e confirmação de revisão | Entrega local, sem sistema hospitalar real |
| Processamento temporal | Monitor JSONL incremental e latência de detectores, fusão e entrega local | Inferência acústica/visual incremental medida sobre arquivos no ritmo original; não mede ASR, nuvem ou captura clínica ao vivo |
| Código completo | Branch `Nirton`, com notebooks, pacote, scripts e testes | Artefatos privados e credenciais em armazenamento separado |
| Relatório técnico | `relatorio/latex/`, PDF e pacote Overleaf | Compila sem mídias clínicas privadas |
| Vídeo até 15 minutos | `relatorio/roteiro_demonstracao.md` | Gravação/publicação com Benicio |


## Limites para a apresentação

- Não existe conjunto clínico pareado para calcular desempenho multimodal global.
- O isolamento de áudio se refere ao classificador regenerado; o pré-treinamento do Whisper não é auditado.
- O vídeo clínico fornecido já foi usado na avaliação da equipe. Os clipes novos usam fluxo óptico real; a validação anterior por marcadores permanece identificada como teste por oráculo.
- mAP50 0,928 e precisão/recall do alerta 1,00/0,72 são resultados relatados pelo Marcelo.
- Classes emocionais sintéticas não validam sinais médicos ou psicológicos em pessoas reais.
- As quatro categorias específicas citadas no relatório antigo de vídeo não constam do PDF fornecido. A matriz segue o enunciado disponível.

## Atualização após execução complementar

Comparação acústica intra-voz e inferência contínua de mídia foram implementadas e exercitadas. O detector de movimento é reproduzível sem peso privado e tem escopo distinto da análise anatômica original. Oito controles de voz e dois clipes geométricos novos passaram; 68 testes e 26 subtestes estão aprovados. A gravação segue com Benicio. Não se apresentam controles sintéticos como validação de doença, nem se declara reproduzido o YOLO ausente. [Parecer detalhado](auditoria_conformidade.md).
