# Auditoria de conformidade — Fase 4

Data: 10/11/2026. Referência primária: PDF original `IADT - Fase 4 - Tech challenge.pdf`, páginas 2–4, relido nesta auditoria.

## Parecer atualizado após execução das pendências

Foram acrescentados e executados os módulos que podiam ser construídos com os materiais disponíveis: comparação acústica intra-voz, detecção de mudanças visuais sem pesos privados e inferência incremental sobre amostras/quadros. As novas evidências permitem demonstrar essas funções, com controles físicos e limites explícitos. Não equivalem a validação clínica nem à reprodução do detector anatômico cujo peso não foi recebido.

| Solicitação | Estado verificável |
|---|---|
| Vídeo e eventos | YOLO histórico preservado; novo fluxo óptico executado diretamente em dois vídeos geométricos inéditos e na montagem recebida. Sem aumento persistente na montagem pela nova regra. |
| Alterações vocais | Referência congelada por voz; oito cenários controlados com pausas, volume e silêncio. Detecta mudança física; não identifica causa médica. |
| Transcrição, termos e sentimentos em nuvem | Chamadas reais OpenAI preservadas; alternativa ao Azure autorizada pelo professor. |
| Sinais vitais, prescrições e movimento | Cenários sintéticos executados, incluindo pressão arterial. |
| Fusão, alertas e resposta | Caixa SQLite e painel; inferência acústica/visual incremental executada no ritmo original. ASR/nuvem e captura ao vivo não fazem parte dessa medida. |
| Código, relatório e fontes | Branch Nirton, documentação, testes, PDF e Overleaf atualizados. |
| Apresentação até 15 minutos | Benicio grava e publica; inserir o link final. |

Não se deve afirmar que o sistema detecta clinicamente fadiga, disartria ou dificuldade respiratória com sensibilidade conhecida. Os exemplos médicos do PDF motivam a triagem; não são rótulos dos controles. Também não se deve apresentar o fluxo óptico como identificação de útero/instrumentos. Dados clínicos reais, ensaio hospitalar e envio por e-mail não foram acrescentados como obrigações do enunciado.

## Complementação executada

- Seis novas sínteses, com duas referências e uma prova reservada por voz; sem hashes compartilhados com o corpus ou as provas anteriores.
- Oito controles acústicos: originais e ganho reduzido sem sinal, pausas inseridas com sinal, silêncio inconclusivo. Regras fixas, sem baixar o limiar emocional.
- Dois vídeos geométricos inéditos processados por fluxo óptico real: controle sem evento; movimento aumentado com dois intervalos. Sem oráculo ou resultados de detecção injetados.
- Montagem recebida reprocessada: 570 quadros; nenhum aumento persistente atingiu a regra. Não se interpreta isso como ausência de anomalia clínica.
- Fluxo de mídia no ritmo original, com 89 pares de quadros, três janelas de voz e alertas persistidos durante a inferência. A espera da janela de cinco segundos é distinta da latência computacional.
- Evidência em `evidence/midias_complementares.json`; guia em `integracao/MIDIAS.md`. Nenhuma nova chamada paga, GPU ou sessão Colab.

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
- Suíte: **68 testes e 26 subtestes aprovados**; evidência em `evidence/testes_auditoria.xml`.
- Análise estática: verificações de sintaxe, nomes indefinidos e erros de controle passaram no Ruff.
- Demonstrações reexecutadas: cinco casos em lote e 32 eventos incrementais, com um alerta estruturado.
- Instalação editável do pacote e comandos de entrada por `python -m` verificados.
- Auditoria do ZIP oficial executada sem retreinar e sem chamadas pagas.
- As métricas acústicas anteriores continuam válidas para o modelo e as partições registrados. Não houve ajuste do modelo, dos limiares ou do conjunto cego para melhorar resultados nesta revisão.
- **Nenhuma chamada adicional à OpenAI e nenhuma nova sessão de GPU** nesta auditoria.

## Limites e dependências externas que permanecem

**Detector anatômico original:** somente o arquivo `best_uterus_tools_v4.pt` da equipe permite repetir especificamente a inferência YOLO publicada por Marcelo. O peso não foi localizado. O detector complementar é uma alternativa funcional com outro escopo, não uma recuperação daquele modelo.

**Avaliação clínica e mídia independente:** os novos clipes são geométricos; a montagem cirúrgica recebida já foi usada. Não há nova avaliação em cirurgia/fisioterapia clínica independente, nem rótulos médicos para as vozes de controle. A exigência adicional do integrante sobre mídias clínicas inéditas permanece limitada pela disponibilidade dos materiais. Recortar a montagem ou transformar o mesmo áudio não torna suas fontes independentes.

**Apresentação:** Benicio grava/publica e o grupo inclui o link. A entrega deve mostrar o que cada detector efetivamente mede. Não se declara atendimento integral com validação médica ou reprodução YOLO inexistentes.

## Distribuição e regressões

O PDF anexado em Downloads foi comparado ao original: ambos têm cinco páginas e SHA-256 `5166f7d0f963d641b79e59768bb81b78d15924cce90735624a234076b20d5ba1`. A revisão anterior verificou uma exportação sem Git em Python limpo e corrigiu a inicialização do notebook. A complementação mantém o pacote básico sem dependências de mídia obrigatórias; NumPy/OpenCV são opcionais. A suíte atual tem 68 testes e 26 subtestes aprovados, incluindo qualidade de voz, referência congelada, persistência, lacunas e câmera instável. Consulte os registros de distribuição e execução em `evidence/`.
