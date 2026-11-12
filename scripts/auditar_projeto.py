"""Inventário de todos os códigos/notebooks e evidências de cobertura do enunciado.

Não executa modelos ou chamadas pagas. A conformidade exige análise do enunciado;
compilação e testes de software não comprovam desempenho médico.
"""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    paths = subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT).decode().split('\0')
    inventory, errors = [], []
    for name in sorted(set(paths)):
        p = ROOT / name
        if not p.is_file() or p.suffix not in {'.py','.ipynb'}:
            continue
        source = p.read_text(encoding='utf-8-sig')
        code_cells = 0
        try:
            if p.suffix == '.py':
                ast.parse(source,filename=name)
            else:
                notebook = json.loads(source)
                for c in notebook['cells']:
                    if c['cell_type'] != 'code': continue
                    code_cells += 1
                    content = ''.join(c['source'])
                    if content.lstrip().startswith('%%'): continue
                    content = '\n'.join(line for line in content.splitlines()
                                        if not line.lstrip().startswith(('%','!')))
                    ast.parse(content, filename=name)
        except (SyntaxError,ValueError,KeyError) as error:
            errors.append({'arquivo':name,'tipo':type(error).__name__})
        inventory.append({'arquivo':name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                          'celulas_codigo':code_cells})
    requirements = [
        {'requisito':'Vídeo clínico e eventos','status':'nova_reproducao_com_reserva_de_clipe',
         'observacao':'Novo YOLOv8s, calibração só na validação e candidato não promovido. Cobertura visual ajustada em treino/validação; falso alerta externo sobre ilustração preservado e removido pela proteção. Nova janela temporal da mesma fonte, sem rótulos clínicos. Ausência de caixa não comprova ausência anatômica; divergência 0/2 mantida.'},
        {'requisito':'Alterações vocais indicativas de condições médicas','status':'demonstracao_acustica_controlada',
         'observacao':'Referência intra-voz anterior, pausas e duração dos trechos vocais. Controles físicos executados. Sem rótulos médicos, sensibilidade clínica ou atribuição causal.'},
        {'requisito':'Transcrição, termos críticos e sentimentos em nuvem','status':'atendido_no_prototipo',
         'observacao':'OpenAI autorizada pelo professor. Chamadas reais salvas; sentimento não é gravidade clínica.'},
        {'requisito':'Sinais vitais, prescrições e movimento','status':'demonstrado_com_dados_sinteticos',
         'observacao':'Inclui batimentos, oxigenação e pressão arterial. Limiares demonstrativos, sem exigência inferida de ensaio hospitalar.'},
        {'requisito':'Alertas e monitoramento temporal','status':'demonstrado_no_prototipo_local',
         'observacao':'Eventos estruturados e inferência acústica/visual incremental sobre arquivos, medida no ritmo original; a latência de nuvem/captura ao vivo não está incluída.'},
        {'requisito':'Código e relatório','status':'atendido_com_limitacoes_explicitas'},
        {'requisito':'Vídeo de até15min noYouTube/Vimeo','status':'pendente_grupo'}]
    result = {'data':'2026-11-11','codigo':inventory,'arquivos_python':sum(x['arquivo'].endswith('.py') for x in inventory),
        'notebooks':sum(x['arquivo'].endswith('.ipynb') for x in inventory),'erros_sintaxe':errors,
        'requisitos':requirements,'conformidade_integral':False,
        'ressalva':'Dados clínicos reais, validação hospitalar e envio por e-mail não são tratados como exigências adicionais ao PDF.'}
    (ROOT/'evidence/auditoria_projeto.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['arquivos_python','notebooks','erros_sintaxe','conformidade_integral']}))
    raise SystemExit(bool(errors))


if __name__ == '__main__': main()
