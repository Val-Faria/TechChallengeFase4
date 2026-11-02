# Matriz de requisitos e evidências
Referência: IADT - Fase 4 - Tech challenge.pdf, páginas 2-4. Situação em 02/11/2026.

**Implementado** significa existência de código; **validado** exige evidência de execução apropriada. Simulação não comprova desempenho clínico nem uso de um serviço real.

| Requisito | Evidência existente | Integração | Situação para entrega final |
|---|---|---|---|
| Processar vídeos clínicos | Notebook YOLO e módulo de vídeo da equipe | Adaptação em .ipynb e consumo do JSON | Resultados documentados pela equipe; execução local com pesos pendente |
| Detectar eventos fora do padrão | Regra Tools presente/Uterus ausente por 5 s | Preserva eventos e prioridade no resultado final | Heurística de perda de visualização; não comprova complicação |
| Relatório automático de vídeo | Módulo do Marcelo | Relatório multimodal com eventos | Validado com entradas controladas; exemplo real do grupo pendente |
| Processar áudio e alterações vocais | Whisper, librosa e Random Forest do grupo | Carregamento do modelo e função de inferência | Verificação parcial com WAVs; sem Whisper local e sem validação em pacientes |
| Azure Speech to Text | Não encontrado na versão consultada; Azure usado para síntese | Adaptador de reconhecimento contínuo preparado | Chamada real pendente de recursos e Secrets |
| Azure Text Analytics: sentimentos e termos | Não encontrado na versão consultada | Sentimento, frases-chave e seleção demonstrativa de termos | Contrato testado com cliente controlado; chamada real pendente |
| Anomalias em sinais vitais | Dados ausentes | Detector robusto histórico + observações | Exemplo sintético; avaliação real pendente |
| Evolução de prescrições | Dados ausentes | Comparação de registros por medicamento | Exemplo sintético; regras assistenciais não definidas |
| Padrões de movimentação | Dados de série ausentes | Detector robusto de características numéricas de movimento | Exemplo sintético; não extrai movimento do vídeo |
| Fusão de texto, áudio e vídeo | Integração indicada como em andamento | Fusão por caso, fontes adicionais e cobertura explícita | 49 verificações locais aprovadas; exemplo completo com Azure real pendente |
| Alerta automático à equipe | Contrato de vídeo e CSV de áudio | JSONL de revisão e relatório por caso | Fila local demonstrada; entrega externa não implementada |
| Tempo real e monitoramento contínuo | Não demonstrados | Processamento em lote | Pendente; não afirmar operação em tempo real |
| Código completo em Git | Frentes de áudio, vídeo e integração | Notebook de integração em .ipynb | Preparado na branch Nirton; publicação e revisão pendentes |
| Relatório técnico | Seção de vídeo existente | Relatório consolidado e matriz | Preparado para revisão; atualizar métricas e execuções pendentes |
| Vídeo de até 15 min | Link ainda ausente no README | Roteiro de demonstração | Benicio/grupo deve gravar e publicar |
| Continuidade com a Fase 3 | Código não disponível no repositório consultado | Interfaces por caso e texto | Não verificado |

## Pontos de atenção da documentação anterior
A seção de vídeo menciona quatro categorias de relatório ginecológico. Essas quatro categorias não constam do PDF de Tech Challenge fornecido nesta pasta. A matriz acima segue o documento efetivamente disponibilizado, que exige também séries vitais, prescrições e movimentação.

O README chama o agrupamento do áudio de divisão por frase original. O código usa o identificador da gravação original. Essa distinção foi explicitada no relatório consolidado e no README.
