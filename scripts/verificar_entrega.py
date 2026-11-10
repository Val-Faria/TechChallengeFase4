"""Verificações de distribuição: segredos, notebooks e fontes de evidência."""
from pathlib import Path
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    names = subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT).decode().split('\0')
    errors = []
    scanned = 0
    for name in names:
        p = ROOT / name
        if not name or not p.is_file() or p.suffix.lower() not in {'.py','.md','.json','.ipynb','.tex','.txt','.yml','.yaml','.toml','.csv','.html','.ps1'}:
            continue
        text = p.read_text(encoding='utf-8-sig',errors='replace')
        scanned += 1
        if re.search(r'sk-(?:proj-)?[A-Za-z0-9_-]{20,}', text):
            errors.append({'arquivo':name,'erro':'Possível credencial; conteúdo não exibido'})
        if p.suffix == '.py':
            try:
                compile(text, str(p), 'exec')
            except SyntaxError as error:
                errors.append({'arquivo':name,'erro':f'Sintaxe Python: linha {error.lineno}'})
        if p.suffix == '.ipynb':
            notebook = json.loads(text)
            for cell in notebook['cells']:
                if cell['cell_type']=='code':
                    source = ''.join(cell['source'])
                    if not source.lstrip().startswith('%%'):
                        # IPython magic/shell lines are valid notebook constructs.
                        cleaned = '\n'.join(line for line in source.splitlines() if not line.lstrip().startswith(('%','!')))
                        try:
                            compile(cleaned, str(p), 'exec')
                        except SyntaxError as error:
                            errors.append({'arquivo':name,'erro':f'Sintaxe: linha {error.lineno}'})
    summary = {'arquivos_textuais_verificados':scanned,'erros':errors,'segredos_expostos_detectados':any('credencial' in e['erro'] for e in errors)}
    out = ROOT / 'evidence/verificacao_distribuicao.json'
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))
    raise SystemExit(bool(errors))


if __name__ == '__main__':
    main()
