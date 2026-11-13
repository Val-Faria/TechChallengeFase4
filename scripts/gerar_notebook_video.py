"""Gera a apresentação dos resultados de vídeo e da cobertura visual."""

from notebook_common import bootstrap, code, md, save

cells = [
    md("""# Análise de vídeo — Tech Challenge Fase 4

YOLOv8s detecta instrumentos e útero; uma regra temporal encaminha trechos para revisão. Os gráficos deste notebook utilizam as evidências da inferência e do treinamento publicados. A leitura não executa novo treinamento nem exige pesos privados.

A ausência de uma caixa anotada não confirma ausência do órgão. Os intervalos derivados das montagens são referências técnicas, não complicações clínicas confirmadas.
"""),
    bootstrap(),
    code("""import pandas as pd
import matplotlib.pyplot as plt
estudo = json.loads((REPO / 'evidence/video_reproducao.json').read_text(encoding='utf-8'))
display(pd.DataFrame([{'conjunto': k, 'imagens': v} for k, v in estudo['dataset']['counts_clean'].items()]))
print('Modelo:', estudo['model']['sha256'][:16])
print('Origem: Uterus v4; anotações e peso preservados.')
"""),
    md("""## 1. Métricas do detector

O desenvolvimento usa uma origem de vídeo, e outra origem foi reservada. Quadros vizinhos podem ser semelhantes; prefixos distintos não comprovam independência por paciente. As métricas abaixo são as medições salvas, não uma nova avaliação.
"""),
    code("""metricas = pd.DataFrame([{'conjunto': k, 'mAP50': v['map50'], 'mAP50_95': v['map50_95']}
                         for k, v in estudo['evaluation'].items()])
display(metricas.round(4))
fig, ax = plt.subplots(figsize=(7, 4))
metricas.set_index('conjunto')[['mAP50', 'mAP50_95']].plot.bar(ax=ax, color=['#315d80', '#a2b9cb'], rot=0)
ax.set(ylim=(0, 1.05), ylabel='mAP', xlabel='', title='Detecção de objetos por conjunto')
fig.tight_layout(); display(fig); plt.close(fig)
"""),
    md("## 2. Concordância temporal e calibração"),
    code("""infer = json.loads((REPO / 'evidence/video_inferencia_nova.json').read_text(encoding='utf-8'))
display(pd.DataFrame([{'conjunto': m['partition'], 'intervalos_referência': len(m['expected_events']),
                      'sinalizados': m['predicted_events'], 'pareados': m['event_metrics']['tp'],
                      'sem_pareamento': m['event_metrics']['fn']} for m in infer['montages']]))
cal = json.loads((REPO / 'evidence/video_calibracao.json').read_text(encoding='utf-8'))
display(pd.DataFrame([{'conjunto': k, 'macro_F1_original': v['baseline']['macro_f1'],
                      'macro_F1_candidato': v['calibrated']['macro_f1']} for k, v in cal['frame_metrics'].items()]).round(4))
print('Candidato de confiança adotado:', cal['candidate_promoted'])
print('Os dois intervalos da reserva continuam sem concordância; suas anotações exigem revisão independente.')
"""),
    md("""## 3. Fonte externa e cobertura

O filtro de aparência utiliza mediana/MAD do treino e retenção selecionada na validação. A fonte TVASurg não entrou nesse ajuste. O falso alerta inicial sobre uma ilustração foi registrado e removido pela proteção. O trecho seguinte foi definido antes da sua execução com o filtro, mas pertence ao mesmo vídeo/paciente. Não há referência clínica para medir acurácia nessa fonte.
"""),
    code("""externo = json.loads((REPO / 'evidence/video_cobertura_externa.json').read_text(encoding='utf-8'))
display(pd.DataFrame([{'trecho': c['interval_source_s'], 'quadros': c['stats']['quadros_analisados'],
                      'fora_da_referência': c['stats']['quadros_fora_referencia_visual'],
                      'sinais': c['event_count']} for c in externo['cases']]))
from techchallenge4.core import combinar_audio_video
video = json.loads((REPO / 'evidence/resultado_video_externo_filtrado.json').read_text(encoding='utf-8'))
controle = combinar_audio_video(('neutro', .95), video, id_caso='controle-cobertura-video', simulado=True)
print('Alerta positivo:', controle['alerta'], '| Revisão necessária:', controle['requer_revisao'])
assert controle['requer_revisao'] and 'video' in controle['fontes_inconclusivas']
"""),
    md("""## 4. Reprodução opcional

A inferência exige o peso privado e o ZIP restaurados conforme `DATASETS_E_MODELOS.md`. Está desligada para a apresentação, que lê as evidências publicadas. Não escolha limiares pela reserva já observada. Os scripts compartilhados executam o detector e exportam os vídeos e relatórios.
"""),
    code("""REEXECUTAR_INFERENCIA = False
if REEXECUTAR_INFERENCIA:
    subprocess.run([sys.executable, str(REPO / 'scripts/video_infer_reserva.py')], cwd=REPO, check=True)
else:
    print('Inferência opcional desligada. Gráficos calculados a partir das medições publicadas.')
print('Nenhum treinamento ou serviço pago foi executado.')
"""),
    md("""As imagens externas permanecem privadas. A apresentação pode mostrar estes resultados sanitizados e a página oficial da fonte. Os sinais solicitam revisão; não confirmam desvio cirúrgico. No Colab, encerre qualquer GPU opcional após salvar os arquivos.
"""),
]
save(cells, "video/TechChallengeFase4_video.ipynb")
