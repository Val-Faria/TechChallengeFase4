# Matriz de requisitos e evidências — 11/11/2026

Referência: PDF original da Fase 4, páginas 2–4; substituição de Azure autorizada pelo professor. A matriz descreve o protótipo e seus tipos de dados, sem transformar aprovação de testes em validação clínica.

| Solicitação | Implementação/evidência | Limite |
|---|---|---|
| Vídeo clínico, eventos e relatório | Novo YOLOv8s, `video_reproducao.json`, `video_inferencia_nova.json`, saídas anotadas | Montagens; 0/2 eventos recuperados na reserva; sem cirurgia contínua externa |
| Áudio e alterações vocais | Whisper, características, Random Forest e referência intra-voz | Síntese e controles físicos; não determina causa médica |
| Transcrição e análise textual | Chamadas reais OpenAI, termos, sentimento, contexto e negação | Fornecedor alternativo autorizado; interpretação requer revisão |
| Sinais vitais | Mediana/MAD com batimentos, pressão e oxigenação | Histórico e desvios sintéticos; limiar não médico |
| Prescrições | Mudanças em dose, unidade, via e intervalo | Não recomenda tratamento |
| Movimentação | Série temporal e fluxo óptico complementar | Sem reconhecimento de postura clínica |
| Fusão e alerta | Contrato por caso, maior prioridade e fontes inconclusivas | Fontes sem pareamento de paciente |
| Encaminhamento e resposta | SQLite, painel HTTP, confirmação e auditoria | Demonstração local; revisão simulada identificada |
| Monitoramento temporal | JSONL e inferência local de mídias no ritmo original | Não mede nuvem ou captura clínica ao vivo |
| Código completo | Branch Nirton, scripts compartilhados, modelos/manifestos e testes | Artefatos privados restaurados conforme `DATASETS_E_MODELOS.md` |
| Relatório técnico | PDF, LaTeX no padrão anexado e Overleaf | Resultados históricos/novos/controlados separados |
| Apresentação até 15 minutos | Roteiro e materiais preservados | Benicio grava/publica e o grupo insere o link |

A reserva de áudio não participa do ajuste emocional. A reserva de vídeo separa o prefixo inteiro disponível; sua origem clínica não é confirmada por paciente. Montagens e derivações não criam automaticamente independência clínica. As quatro categorias mencionadas no relatório histórico de vídeo não são obrigações do PDF fornecido.

O peso original do Marcelo não foi recuperado; isso não bloqueia a nova inferência, feita com outro modelo e protocolo próprios. Não há dados suficientes para afirmar detecção clínica confiável de fadiga/disartria/dificuldade respiratória. [Auditoria detalhada](auditoria_conformidade.md).
