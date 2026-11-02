# Roteiro sugerido para o vídeo do grupo
Duração planejada: 13 minutos e 30 segundos, com margem até o limite de 15 minutos.

| Tempo | Conteúdo | Evidência a mostrar |
|---|---|---|
| 00:00-01:00 | Problema, equipe e recorte | Objetivo e diagrama do fluxo |
| 01:00-03:30 | Frente de áudio | Dataset confirmado, transcrição, características e classe/confiança |
| 03:30-06:00 | Frente de vídeo | Detector, evento temporal e JSON gerado pelo Marcelo |
| 06:00-08:00 | Azure | Execução real de Speech to Text e Language, após configurar os recursos |
| 08:00-10:30 | Integração de Afonso | Pareamento explícito, resultado único, prioridade e relatório |
| 10:30-12:00 | Anomalias estruturadas | Exemplos de séries, prescrições e cobertura de fontes |
| 12:00-13:30 | Resultados, limitações e resposta | Fila local de revisão, métricas confirmadas e pendências remanescentes |

## Demonstração da integração
1. Abrir o notebook de integração no Colab.
2. Explicar que a função recebe classe/confiança do áudio e alerta/eventos do vídeo.
3. Mostrar demo-03: um áudio neutro não cancela um alerta alto de vídeo.
4. Mostrar demo-04: uma fonte ausente pede revisão e não é tratada como resultado normal.
5. Mostrar o JSON e o relatório automático, com os tempos dos eventos.
6. Mostrar o modo CSV + JSON com os arquivos da equipe, se o pareamento já estiver confirmado.
7. Mostrar o arquivo da fila de revisão. Explicar que se trata do registro local para uma futura interface, sem alegar envio a um sistema hospitalar.

## Preparação antes de gravar
- Confirmar a versão de áudio e a métrica final com Valkiria.
- Receber pesos/vídeo/JSON do exemplo com Marcelo.
- Executar as chamadas Azure reais. Se não forem executadas, declarar a pendência.
- Identificar no vídeo todos os exemplos sintéticos e as fontes independentes.
- Evitar apresentar o exemplo de cirurgia e o áudio sintético como dados do mesmo paciente.
- Não exibir Secrets, chaves ou valores de credenciais.
- Atualizar o relatório e o link do vídeo somente com evidências efetivamente produzidas.
