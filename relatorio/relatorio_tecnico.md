# Relatório técnico consolidado - Fase 4

**Monitoramento multimodal em saúde da mulher**
Pós Tech FIAP - Inteligência Artificial para Devs
Consolidação: **10/11/2026** | Branch: **Nirton**

| Integrante | RM | Frente |
|---|---|---|
| Benicio Antonio Cardoso | 371527 | Gravação e edição do vídeo |
| Marcelo Viana de Araújo | 372707 | YOLOv8 e análise de vídeo |
| Nirton Afonso de Oliveira Filho | 370221 | Integração, testes e relatório |
| Valkiria Nonato de Faria | 373256 | Dataset e classificação de áudio |

## Documento principal

O relatório completo é gerado em **LaTeX**, com PDF e pacote importável no Overleaf:

- `output/pdf/relatorio_tecnico_fase4.pdf`: documento final.
- `relatorio/latex/main.tex`: fonte principal.
- `relatorio/latex/dados_gerados.tex`: tabelas extraídas das evidências.
- `relatorio/overleaf_fase4.zip`: projeto pronto para upload.
- `relatorio/COMO_COMPILAR.md`: instruções de reprodução.

O PDF é compilado das mesmas fontes do ZIP, sem depender de imagens privadas de cirurgia ou de credenciais.

## Fluxo

**WAV → Whisper + Librosa → Random Forest; transcrição → OpenAI; vídeo/JSON → eventos YOLO; séries/prescrições → detectores → fusão → JSON/relatório + caixa de alertas e painel.**

A fusão preserva a maior prioridade entre sinais válidos. As confianças de modelos diferentes não são somadas nem promediadas. Fonte ausente ou inconclusiva permanece visível.

O professor autorizou serviços alternativos ao Azure em 09/11/2026. Whisper fornece a representação de ritmo acústico; a OpenAI transcreve os WAVs novos e realiza a análise textual. Azure Speech permanece registrado na síntese do dataset, sem ser apresentado como transcrição executada.

## Dados e avaliação

- **Áudio:** 1.180 WAVs (380 ansiedade/hesitação, 400 neutros, 400 tristeza); quatro versões por gravação. O modelo regenerado utiliza partições por família de frase-base e verificação cega separada de treino, validação e teste.
- **Vídeo:** pacote de Marcelo com vídeo anotado, JSON, imagens e relatório. Eventos 76-82 s e 84-114 s. Artefato decodificado com 570 quadros, 5 FPS e 114 s.
- **Séries e prescrições:** cenários sintéticos para verificar detectores e fluxo temporal, sem dados de pacientes.
- **Pareamento:** áudio e vídeo não correspondem à mesma pessoa ou instante; a associação é demonstrativa.

As métricas novas de áudio estão em `evidence/audio_reproducao.json`. O número histórico **89% em 236 exemplos** é atribuído ao relatório anterior da Val e não substitui a nova avaliação. Os valores antigos de 88% e 92% não são desempenho final consolidado.

As métricas de vídeo **mAP50 0,928**, precisão **1,00** e recall **0,72** são atribuídas ao Marcelo. Sem pesos, não houve nova inferência YOLO. Clipes inéditos com marcadores coloridos verificam software por oráculo, sem medir generalização anatômica.

## Evidências

| Caminho | Conteúdo |
|---|---|
| `evidence/audio_reproducao.json` | Auditoria, versões, partições e métricas |
| `audio/evidencias/particoes_audio.csv` | Arquivo/gravação/família e partição |
| `audio/evidencias/predicoes_avaliacao.csv` | Predições dos conjuntos reservados |
| `artifacts/audio/manifesto_audio.json` | Identidade dos artefatos regenerados |
| `evidence/video_validacao.json` | Decodificação, eventos e clipes controlados |
| `evidence/resumo_execucao.json` | Testes, nuvem e recursos |
| `integracao/evidencias/execucao_final/` | Resultados por caso, anomalias, reprodução e entrega |

## Entrega e tempo de resposta

O painel local mostra a caixa persistida em SQLite e permite confirmar revisão. A auditoria diferencia entrega, repetição e confirmação. A latência do reprodutor mede persistência; a do monitor incremental inclui detectores estatísticos, fusão e entrega local. Ambas excluem captura, inferência dos modelos e atendimento hospitalar. A nova execução de mídia, registrada separadamente, inclui características acústicas, fluxo óptico, fusão e persistência, além da espera da janela; não inclui ASR ou nuvem.

## Limitações

1. Voz sintética única não valida fadiga, disartria ou dificuldade respiratória.
2. O isolamento cego se refere ao classificador regenerado; não audita pré-treinamento do Whisper.
3. Proveniência de vídeo e proximidade de quadros limitam a independência das métricas históricas.
4. Avaliação clínica independente YOLO não foi possível sem pesos e vídeo externo anotado.
5. Não existe conjunto pareado para métrica multimodal global.
6. Detectores estruturados usam limiares demonstrativos, sem recomendação de tratamento.
7. A entrega local não comprova conexão hospitalar.
8. O código da Fase 3 não foi disponibilizado; continuidade executável não é afirmada.

A cobertura está em `matriz_requisitos.md`. O roteiro de Benicio está em `roteiro_demonstracao.md`; gravação e publicação permanecem sob responsabilidade dele.

## Resultados finais desta consolidação

- **Áudio:** validação 93,60% (172 WAVs); teste 86,36% (176); verificação cega 88,33% (120). F1 macro: 0,933 / 0,862 / 0,883. Nenhuma sobreposição por família, gravação original ou SHA-256. Modelo ajustado somente com 712 WAVs de treino.
- **Áudios novos:** seis WAVs em duas novas vozes, fora do corpus. Todas as saídas acústicas têm confiança entre 0,50 e 0,60 e são inconclusivas pelo limiar 0,70; não há acurácia emocional externa.
- **ASR:** nos mesmos seis WAVs, Whisper tiny errou 13 de 109 palavras (WER 11,93%) e a API não errou palavras (0%). Amostra pequena e sintética, sem conclusão clínica ou superioridade geral.
- **Software:** 68 testes pytest e 26 subtestes aprovados, zero falhas.
- **Nuvem:** 18 chamadas, estimativa conservadora total US$ 0,005980495; inclui duas respostas rejeitadas e uma reserva conservadora. Não representa leitura da fatura.
- **Drive:** modelo e CSV corrigidos recebidos; 1.180 linhas e zero nomes ausentes. Modelo da autora treinado em todo corpus, separado do modelo da avaliação cega.
- **Integração:** alerta alto preservado, cobertura incompleta pela baixa confiança acústica; entrega e revisão local confirmadas.
- **Recursos:** GPU local RTX 2060 utilizada e processamento encerrado. Nenhuma sessão Colab iniciada.

## Parecer após complementação

Foram implementadas comparação acústica intra-voz e inferência contínua de áudio/vídeo em arquivos. Oito controles de áudio e dois clipes visuais novos tiveram os resultados esperados. Referências e provas foram separadas; não houve retreinamento do classificador emocional ou novas chamadas pagas. O fluxo óptico dispensa pesos privados, mas detecta movimento inespecífico e não reproduz a análise anatômica YOLO. A montagem cirúrgica foi processada e não atingiu a nova regra de aumento persistente.

A gravação continua com Benicio. O peso ausente ainda impede reproduzir especificamente o detector anatômico original. A avaliação de voz é uma prova controlada de alterações físicas, sem sensibilidade clínica; os vídeos geométricos inéditos não são vídeos clínicos independentes. Esses limites devem ser apresentados, sem transformar testes de software em resultados médicos. Consulte [a auditoria atualizada](auditoria_conformidade.md) e [o guia de reprodução](../integracao/MIDIAS.md).
