"""Gera a demonstração integrada, com as mesmas regras do pacote Python."""

from notebook_common import bootstrap, code, md, save

cells = [
    md("""# Monitoramento multimodal — Tech Challenge Fase 4

Este é o ponto de entrada da demonstração. Áudio, vídeo, texto e séries estruturadas convergem para uma caixa de revisão. As modalidades são associadas para o experimento; não representam um paciente pareado.

A execução padrão utiliza resultados reais já registrados dos modelos e da nuvem. A fusão, os detectores estruturados, a persistência e o painel são executados novamente. Não há treinamento ou chamadas pagas.
"""),
    bootstrap(html=True),
    code("""import pandas as pd
from techchallenge4.demo import run_demo
SAIDA = REPO / 'integracao/saidas/apresentacao_final'
resumo = run_demo(SAIDA,
    audio_csv=REPO / 'audio/evidencias/resultado_audio_externo.csv', audio_filename='novo-03.wav',
    video_json=REPO / 'evidence/resultado_video_teste.json',
    text_json=REPO / 'evidence/texto_openai_integracao.json')
print('Casos:', resumo['resultados'], '| Na revisão:', resumo['caixa_revisao'],
      '| Entrega idempotente:', resumo['idempotencia'])
"""),
    md("""## 1. Fontes e decisão do caso

A confiança acústica abaixo de 0,70 permanece inconclusiva. A fusão conserva a maior prioridade dos sinais disponíveis; uma modalidade neutra não cancela um alerta alto. Cobertura parcial também exige revisão, mesmo sem alerta positivo.
"""),
    code("""caso = json.loads((SAIDA / 'demonstracao-integrada.json').read_text(encoding='utf-8'))
display(pd.DataFrame([{'fonte': f['modalidade'], 'estado': f['status'], 'alerta': f['alerta'],
                      'nível': f['nivel'], 'cobertura_parcial': f.get('cobertura_parcial', False)} for f in caso['fontes']]))
print('Prioridade final:', caso['nivel'], '| Cobertura:', caso['status'], '| Entrega:', caso['entrega']['status'])
assert caso['nivel'] == 'alto' and caso['requer_revisao']
"""),
    md("## 2. Painel da caixa de revisão"),
    code("""display(HTML((SAIDA / 'painel.html').read_text(encoding='utf-8')))
print('Para confirmar uma revisão, iniciar o painel local sobre o banco desta saída.')
"""),
    md("""## 3. Monitoramento incremental

Trinta amostras sintéticas formam o histórico anterior. Os próximos pacotes verificam uma observação de referência e alterações em sinais vitais, prescrições e movimento. A latência mede processamento e entrega locais, sem nuvem, captura de sensores ou inferência dos modelos.
"""),
    code("""from techchallenge4.monitor import example_packets, run_stream
from techchallenge4.reports import atomic_write
FLUXO = SAIDA / 'monitoramento'
entrada = FLUXO / 'entrada_sintetica.jsonl'
atomic_write(entrada, ''.join(json.dumps(p, ensure_ascii=False) + '\\n' for p in example_packets()))
monitoramento = run_stream(entrada, FLUXO, max_events=32)
print(json.dumps(monitoramento, ensure_ascii=False, indent=2))
display(HTML((FLUXO / 'painel.html').read_text(encoding='utf-8')))
"""),
    md("""## 4. Transcrição e análise textual

A fonte seguinte é a resposta real da API obtida na avaliação anterior. Sua leitura não realiza outra solicitação. Novas chamadas são opcionais, usam `OPENAI_API_KEY` nos Secrets do Colab e respeitam o controle de orçamento descrito no repositório.
"""),
    code("""texto = json.loads((REPO / 'evidence/texto_openai_integracao.json').read_text(encoding='utf-8'))
print(json.dumps(texto, ensure_ascii=False, indent=2))
print('Chamadas pagas nesta execução: 0')
"""),
    md("## 5. Salvar os resultados"),
    code("""import zipfile
pacote = SAIDA.parent / 'resultados_apresentacao.zip'
with zipfile.ZipFile(pacote, 'w', zipfile.ZIP_DEFLATED) as arquivo:
    for p in sorted(SAIDA.rglob('*')):
        if p.is_file() and p.suffix in {'.json', '.jsonl', '.csv', '.md', '.html'}:
            arquivo.write(p, p.relative_to(SAIDA))
print('Resultados salvos: integracao/saidas/resultados_apresentacao.zip')
print('Relatório final: output/pdf/relatorio_tecnico_fase4.pdf')
"""),
    md("""O painel é local e a confirmação registra revisão de demonstração. Os resultados não validam decisões clínicas. Consulte o relatório para as partições, as divergências do vídeo e as limitações dos áudios sintéticos. Ao usar GPU opcional no Colab, salve os artefatos e desconecte/exclua o ambiente ao terminar.
"""),
]
save(cells, "integracao/TechChallengeFase4_integracao.ipynb")
