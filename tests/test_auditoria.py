"""Regressões de falhas encontradas na auditoria do enunciado."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta
import csv
import json
from pathlib import Path
import pytest
from techchallenge4.core import detectar_series, combinar_audio_video, validar_fonte
from techchallenge4.demo import load_audio, structured_examples
from techchallenge4.delivery import AlertStore
from techchallenge4.monitor import StructuredMonitor, example_packets
from techchallenge4.reports import atomic_write
from techchallenge4.openai_text import analyze_text_openai


def test_csv_multiplos_exige_escolha(tmp_path):
    p = tmp_path / 'audio.csv'
    p.write_text('arquivo,classe_audio,confianca_audio\na.wav,neutro,0.9\nb.wav,tristeza,0.8\n')
    with pytest.raises(ValueError, match='audio-filename'):
        load_audio(p)
    assert load_audio(p, 'b.wav')[0]['classe_audio'] == 'tristeza'


def test_serie_constante_nao_oculta_outra_anomalia():
    data = structured_examples()
    history = [{**r, 'oxigenacao': 97} for r in data['historico']]
    r = detectar_series(history, data['observacoes'], ['batimentos', 'oxigenacao'], 'sinais_vitais')
    assert r['alerta'] and r['cobertura_parcial']
    assert r['campos_inconclusivos'] == ['oxigenacao']
    merged = combinar_audio_video(('neutro', .9), {'alerta':False,'nivel':'nenhum'},
        id_caso='parcial', fontes_adicionais=[r])
    assert merged['alerta'] and merged['status'] == 'incompleto'


def test_pressao_arterial_presente_e_monitorada():
    r = structured_examples()['resultados'][0]
    assert {'pressao_sistolica','pressao_diastolica'} <= set(r['referencias'])
    assert {'pressao_sistolica','pressao_diastolica'} <= {e['campo'] for e in r['eventos']}


def test_revisao_concorrente_produz_uma_acao(tmp_path):
    store = AlertStore(tmp_path / 'a.db')
    r = combinar_audio_video(('tristeza',.9), {'alerta':False,'nivel':'nenhum'},id_caso='concorrencia')
    store.deliver(r)
    with ThreadPoolExecutor(max_workers=8) as pool:
        acknowledgements = list(pool.map(lambda i:store.acknowledge(r['id_resultado'],str(i)),range(24)))
    assert sum(acknowledgements) == 1
    assert sum(e['action']=='revisao_confirmada' for e in store.audit_log()) == 1


def test_exportacoes_concorrentes_nao_compartilham_temporario(tmp_path):
    p = tmp_path / 'snapshot.json'
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda i:atomic_write(p,json.dumps({'i':i,'texto':'á'*1000})),range(30)))
    assert len(json.loads(p.read_text(encoding='utf-8'))['texto']) == 1000
    assert not list(tmp_path.glob('*.tmp'))


def test_video_antigo_expira_sem_virar_resultado_normal(tmp_path):
    monitor = StructuredMonitor('monitor-sintetico', AlertStore(tmp_path/'a.db'), max_source_age_s=60)
    first = example_packets()[0]
    first['video'] = {'alerta':True,'nivel':'alto'}
    assert monitor.feed(first)['resultado']['nivel'] == 'alto'
    update = {'id_caso':'monitor-sintetico','event_id':'novo',
        'timestamp':(datetime.fromisoformat(first['timestamp'])+timedelta(seconds=61)).isoformat(),
        'audio':{'classe_audio':'neutro','confianca_audio':.95}}
    r = monitor.feed(update)['resultado']
    assert r['nivel'] == 'nenhum' and r['requer_revisao']
    assert 'video' in r['fontes_inconclusivas']


def test_referencia_sintetica_nao_perde_origem(tmp_path):
    monitor = StructuredMonitor('monitor-sintetico', AlertStore(tmp_path/'a.db'))
    packets = example_packets()
    for p in packets[:30]: monitor.feed(p)
    last = deepcopy(packets[30]); last['simulado'] = False
    r = monitor.feed(last)['resultado']
    assert next(s for s in r['fontes'] if s['modalidade']=='sinais_vitais')['simulado']


def test_pacote_sem_modalidade_rejeitado(tmp_path):
    m=StructuredMonitor('x',AlertStore(tmp_path/'a.db'))
    with pytest.raises(ValueError,match='modalidade'):
        m.feed({'id_caso':'x','timestamp':'2026-11-10T12:00:00Z'})


@pytest.mark.parametrize('bad', [{'modalidade':'x','status':'ok','alerta':False,'nivel':'nenhum'},
    {'modalidade':'x','status':'ok','alerta':False,'nivel':'nenhum','motivo':'x','simulado':'false'}])
def test_contrato_de_fonte_nao_quebra_painel(bad):
    with pytest.raises(ValueError): validar_fonte(bad)


def test_cache_textual_nao_reutiliza_decisao_adulterada(tmp_path):
    text='Não tenho dor.'
    def fake(payload, key):
        return {'status':'completed','usage':{'input_tokens':100,'output_tokens':50},
            'output':[{'content':[{'type':'output_text','text':json.dumps({
                'sentimento':'neutro','mencoes':[{'termo':'dor','estado':'negado',
                 'contexto':'paciente_atual','evidencia':text}],'limitacoes':[]})}]}]}
    analyze_text_openai(text,tmp_path,request_fn=fake)
    cache=next(tmp_path.glob('texto_*.json'))
    content=json.loads(cache.read_text(encoding='utf-8'))
    content.update({'alerta':True,'nivel':'alto'})
    cache.write_text(json.dumps(content),encoding='utf-8')
    result=analyze_text_openai(text,tmp_path,request_fn=lambda *_:pytest.fail('Não deve chamar API'))
    assert result['cache_utilizado'] and not result['alerta'] and result['nivel']=='nenhum'
