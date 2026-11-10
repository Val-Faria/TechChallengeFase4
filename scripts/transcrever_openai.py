"""Transcreve apenas os seis WAVs novos, com teto local de US$0,02 e cache."""
from pathlib import Path
import argparse
import json
import sys
import re

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from techchallenge4.openai_audio import transcribe_wav
from techchallenge4.reports import atomic_write
MODEL = 'gpt-4o-mini-transcribe'
RATE_PER_MINUTE = .003


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file',type=Path,required=True)
    args = parser.parse_args()
    match = re.search(r'sk-[A-Za-z0-9_\-]+',args.env_file.read_text(encoding='utf-8-sig'))
    if not match:
        raise SystemExit('Chave não reconhecida; nenhum pedido enviado.')
    key = match.group()
    source = ROOT / 'dados_privados/audio_inedito'
    manifest = json.loads((source/'manifesto.json').read_text(encoding='utf-8-sig'))
    cache = ROOT / 'evidence/openai_audio'
    cache.mkdir(exist_ok=True)
    ledgerpath = cache / 'orcamento_transcricao.json'
    ledger = json.loads(ledgerpath.read_text(encoding='utf-8')) if ledgerpath.exists() else {'limite_usd':.02,'chamadas':[]}
    if not 1 <= len(manifest['casos']) <= 6:
        raise ValueError('Permitidos no máximo seis áudios sintéticos novos.')
    cases = []
    for case in manifest['casos']:
        path = source / case['arquivo']
        if path.resolve().parent != source.resolve():
            raise ValueError('Arquivo fora da pasta autorizada.')
        result = transcribe_wav(path, cache, key=key, max_budget_usd=.02, case_id=case['id'])
        cases.append({'id':case['id'],'arquivo':case['arquivo'],'texto_referencia':case['texto'],
                      'transcricao':result['text'],'provedor':'OpenAI API','natureza':'audio_sintetico_novo',**result})
    ledger = json.loads(ledgerpath.read_text(encoding='utf-8'))
    output={'modelo':MODEL,'fonte_preco':'https://developers.openai.com/api/docs/pricing',
        'natureza':'audio_sintetico_novo_fora_das_particoes_de_desenvolvimento',
        'chamadas':len(ledger['chamadas']),
        'custo_estimado_cumulativo_usd':sum(c['custo_contabilizado_usd'] for c in ledger['chamadas']),
        'casos':cases}
    atomic_write(ROOT/'evidence/audio_openai_transcricoes.json', json.dumps(output,ensure_ascii=False,indent=2))
    print(json.dumps({'transcricoes':len(cases),'custo_estimado_usd':output['custo_estimado_cumulativo_usd']}))


if __name__=='__main__':
    try:
        main()
    except Exception as error:
        # Avoid logging request objects, authorization headers or raw server bodies.
        print(f'Transcrição interrompida com segurança: {type(error).__name__}. Consulte o ledger local; não há repetição automática.', file=sys.stderr)
        raise SystemExit(1) from None
