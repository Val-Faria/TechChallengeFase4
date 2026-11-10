# Auditoria de conformidade — Fase 4

Data: 10/11/2026. Referência primária: PDF original `IADT - Fase 4 - Tech challenge.pdf`, páginas 2–4, relido nesta auditoria.

## Parecer

**O protótipo está organizado e executável, mas não há evidência suficiente para declarar atendimento integral ao enunciado.** A gravação da apresentação não é a única pendência. A resposta anterior que destacou somente os pesos do vídeo estava incompleta: também permanece uma diferença funcional entre classificar emoções sintéticas e demonstrar alterações vocais indicativas das condições médicas citadas no PDF.

## Cobertura verificada

| Solicitação do PDF | Situação | Evidência ou ação necessária |
|---|---|---|
| Processar vídeo clínico, detectar evento e produzir relatório | Parcialmente demonstrado | Código YOLO e eventos/relatório do Marcelo existem. Falta disponibilizar o peso personalizado e reproduzir a inferência a partir do vídeo selecionado. |
| Processar consulta e detectar alterações vocais | Parcial | Existem transcrição, características acústicas e classificador emocional sintético. Esses resultados não demonstram detecção de cansaço ou dificuldade respiratória pela voz. É necessário acrescentar cenários e uma referência apropriada para avaliar essa funcionalidade. |
| Transcrição e análise textual em nuvem | Demonstrado no protótipo | Chamadas reais da OpenAI e respostas salvas. O professor autorizou substituir o Azure; o fornecedor não é pendência. |
| Termos críticos e sentimentos | Implementado e demonstrado | Citações literais, negação e contexto; quatro controles verificam os alertas, sem constituir avaliação abrangente da qualidade de sentimentos. |
| Anomalias em batimentos, pressão e oxigenação | Demonstrado com dados sintéticos | Pressão sistólica e diastólica foram acrescentadas nesta auditoria. Mediana/MAD e referência anterior detectam as alterações controladas. |
| Evolução de prescrições | Demonstrado com dados sintéticos | Mudanças de dose, unidade, via e intervalo são encaminhadas à revisão. Não recomenda tratamento. |
| Padrões de movimentação | Demonstrado com série sintética | Detector de intensidade ao longo do tempo; não é reconhecimento de postura clínica. O PDF não obriga usar OpenPose especificamente. |
| Alertas automáticos e monitoramento temporal | Demonstrado localmente | Entrada incremental JSONL, validade das fontes, caixa persistente, painel e confirmação. A latência medida exclui os modelos e não demonstra processamento multimodal completo em tempo real. |
| Código completo e relatório | Entregues, com restrição de reprodução do detector | Branch Nirton, módulos, notebooks, testes, PDF e LaTeX. Distribuir o peso de vídeo ou documentar uma forma efetivamente reproduzível de obtê-lo. |
| Vídeo de até 15 minutos no YouTube/Vimeo | Com o grupo | Benicio grava; depois inserir o link no README e na entrega. |

Dados clínicos reais, ensaio hospitalar, homologação médica e envio de mensagens por e-mail não foram tratados como exigências adicionais. Os datasets do PDF são sugestões. O uso de exemplos sintéticos deve continuar declarado. A avaliação em mídias inéditas foi uma exigência adicional do integrante e não uma regra de particionamento expressa no PDF.

## Correções realizadas nesta auditoria

1. CSV com vários áudios agora exige escolha explícita; não seleciona o primeiro arquivo silenciosamente.
2. Uma medida sem dispersão no histórico não esconde os desvios detectáveis nas demais. O resultado preserva o alerta e indica cobertura parcial.
3. Pressão arterial sistólica e diastólica acrescentadas às demonstrações em lote e incremental.
4. Fontes antigas expiram após prazo operacional configurável (`--max-source-age`, padrão 60 segundos). Fonte expirada é inconclusiva; não é tratada como observação normal.
5. Referência sintética mantém sua origem mesmo quando um pacote posterior não traz a marca de simulação.
6. Confirmações simultâneas de revisão são serializadas, produzindo uma única ação de auditoria.
7. Exportação usa arquivos temporários exclusivos, evitando colisões entre escritores concorrentes.
8. Contratos rejeitam fontes sem motivo, indicadores de simulação inválidos e campos reservados nas séries.
9. Cache textual confere identidade de texto/modelo e recalcula a decisão a partir das menções validadas; não reutiliza um campo de alerta alterado no cache.
10. WAVs extraídos são conferidos contra os bytes do ZIP. Nomes duplicados no arquivo são rejeitados.
11. O modelo é conferido por hash antes de ser carregado na avaliação externa; o script passa a regenerar também o CSV usado pela integração.
12. O modo `--audit-only` do áudio e as execuções de medição não sobrescrevem o manifesto oficial das partições.
13. A verificação de distribuição também compila todos os arquivos Python e todas as células Python dos notebooks, inclusive células iniciadas por instalação IPython.

14. Exportações CSV/JSON e notebooks preservam seus bytes no Git; isso evita que conversões de fim de linha invalidem os hashes registrados em outro sistema operacional.

## Verificações

- Inventário e análise sintática: **28 arquivos Python e 3 notebooks**, sem erros; inventário com hashes em `evidence/auditoria_projeto.json`.
- Suíte: **59 testes e 26 subtestes aprovados**; evidência em `evidence/testes_auditoria.xml`.
- Análise estática: verificações de sintaxe, nomes indefinidos e erros de controle passaram no Ruff.
- Demonstrações reexecutadas: cinco casos em lote e 32 eventos incrementais, com um alerta estruturado.
- Instalação editável do pacote e comandos de entrada por `python -m` verificados.
- Auditoria do ZIP oficial executada sem retreinar e sem chamadas pagas.
- As métricas acústicas anteriores continuam válidas para o modelo e as partições registrados. Não houve ajuste do modelo, dos limiares ou do conjunto cego para melhorar resultados nesta revisão.
- **Nenhuma chamada adicional à OpenAI e nenhuma nova sessão de GPU** nesta auditoria.

## O que fechar antes de afirmar atendimento integral

**Vídeo — Marcelo:** fornecer `best_uterus_tools_v4.pt` e o vídeo autorizado da demonstração; executar o detector, conferir os eventos e registrar a origem dos dados. Para o teste independente solicitado pelo integrante, usar outra mídia que não pertença às partições já usadas pelo detector.

**Áudio — frente responsável:** demonstrar alterações vocais relacionadas ao objetivo médico do trabalho com dados/cenários e referência adequados. Separar essa funcionalidade da extração de sintomas mencionados no texto e da classificação emocional. Os seis áudios novos ficaram abaixo do limiar de confiança; isso é uma limitação observada, não deve ser corrigida diminuindo o limiar depois de ver seus resultados.

**Tempo real e demonstração — integração/grupo:** apresentar o modo incremental com seus limites. Se o grupo pretende declarar todo o fluxo de áudio/vídeo em tempo real, ainda precisa executar essa aquisição/inferência contínua e medir o tempo total. A evidência atual sustenta processamento incremental das séries estruturadas e integração de resultados multimodais previamente calculados.

**Entrega — grupo:** reunir a versão correta da branch, os artefatos necessários, o relatório atualizado e o link final da apresentação. Não apresentar fonte ausente ou baixa confiança como cobertura completa.
