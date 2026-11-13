"""Gera a apresentação executável da avaliação de áudio."""

from notebook_common import bootstrap, code, md, save

cells = [
    md("""# Análise de áudio — Tech Challenge Fase 4

Whisper e Librosa fornecem as características; o Random Forest classifica a prosódia. Este notebook executa novamente as previsões do **modelo congelado**, com hashes conferidos. Não treina nem utiliza créditos de API.

O corpus contém 1.180 falas sintéticas. As métricas descrevem esse experimento, não diagnóstico de fadiga, disartria ou dificuldade respiratória. A reserva já foi avaliada e sua reexecução não cria uma nova avaliação cega.
"""),
    bootstrap(),
    code("""# A versão usada na persistência evita incompatibilidade ao abrir o modelo no Colab.
import importlib.metadata
if importlib.metadata.version('scikit-learn') != '1.6.1':
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'scikit-learn==1.6.1'], check=True)
import pandas as pd
import matplotlib.pyplot as plt
from techchallenge4.audio_evaluation import avaliar_modelo_congelado
print('Dependências disponíveis; execução em CPU.')
"""),
    md("""## 1. Partições e previsões

As famílias de frases ficam em uma única partição. O modelo foi ajustado somente nos 712 exemplos de treino; validação, teste e reserva possuem 172, 176 e 120 exemplos. A função abaixo chama `predict` sobre as características publicadas. A extração Whisper/Librosa original está registrada nos scripts e nas evidências.
"""),
    code("""resultado = avaliar_modelo_congelado(REPO)
resumo = pd.DataFrame([
    {'conjunto': nome, 'amostras': m['n'], 'acurácia': m['accuracy'], 'macro_F1': m['macro_f1']}
    for nome, m in resultado['metrics'].items()
])
display(resumo.round(4))
# A reexecução deve reproduzir os números do experimento publicado.
registrado = json.loads((REPO / 'evidence/audio_reproducao.json').read_text(encoding='utf-8'))
for nome, m in resultado['metrics'].items():
    assert abs(m['accuracy'] - registrado[nome]['accuracy']) < 1e-12
print('Modelo:', resultado['model_sha256'][:16], '| Novo ajuste:', resultado['fit_performed'])
"""),
    md("## 2. Matriz de confusão da reserva"),
    code("""m = resultado['metrics']['blind_holdout']
fig, ax = plt.subplots(figsize=(6, 4))
im = ax.imshow(m['confusion_matrix'], cmap='Blues')
ax.set(xticks=range(3), yticks=range(3), xticklabels=['Ansiedade', 'Neutro', 'Tristeza'],
       yticklabels=['Ansiedade', 'Neutro', 'Tristeza'], xlabel='Classe prevista', ylabel='Classe de origem',
       title='Reserva de frases — modelo congelado')
for i, linha in enumerate(m['confusion_matrix']):
    for j, valor in enumerate(linha):
        ax.text(j, i, str(valor), ha='center', va='center', color='white' if valor > 25 else 'black')
fig.colorbar(im, ax=ax)
fig.tight_layout()
display(fig)
plt.close(fig)
"""),
    md("""## 3. Gravações externas e confiança

As seis gravações externas usam textos e vozes diferentes. As previsões abaixo de 0,70 são encaminhadas como inconclusivas. Não são convertidas em evidência de neutralidade.
"""),
    code("""externos = pd.read_csv(REPO / 'audio/evidencias/resultado_audio_externo.csv')
colunas = [c for c in ['arquivo', 'classe_audio', 'confianca_audio'] if c in externos.columns]
display(externos[colunas])
print('Transcrições e análises de nuvem: resultados de chamadas anteriores, sem novas solicitações.')
print('Extração completa: python scripts/audio_reproduce.py --device auto (experimento documentado).')
"""),
    md("""## Reprodução e interpretação

O código de extração está em `scripts/audio_reproduce.py`; a inferência de um WAV está em `scripts/audio_infer.py`. A API OpenAI tem evidências próprias em `evidence/`. Não altere o modelo congelado para repetir a apresentação. Um novo treinamento deve ser tratado como outro experimento.

Se utilizar GPU em uma execução opcional no Colab, salve os artefatos e use **Ambiente de execução → Desconectar e excluir ambiente de execução** ao terminar.
"""),
]
save(cells, "audio/notebooks/TechChallengeFase4_audio.ipynb")
