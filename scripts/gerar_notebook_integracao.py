"""Gera a entrada Colab a partir do pacote único, evitando implementações duplicadas."""
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
cells = []


def md(text):
    cells.append({'cell_type':'markdown','id':hashlib.sha256(('md'+text).encode()).hexdigest()[:12],'metadata':{},'source':text.splitlines(keepends=True)})


def code(text):
    cells.append({'cell_type':'code','id':hashlib.sha256(('code'+text).encode()).hexdigest()[:12],'metadata':{},'source':text.splitlines(keepends=True),'execution_count':None,'outputs':[]})


md('''# Monitoramento multimodal — Fase 4

**Entrada única da integração, branch Nirton.** O código executado está no pacote `src/techchallenge4`, com testes automatizados. Não há necessidade de GPU para rever os resultados e executar a demonstração de integração.

O fluxo combina características de voz, resultado de vídeo, texto e exemplos estruturados. Fontes independentes não representam o mesmo paciente. Os resultados são sinais para revisão humana.

Execute em ordem. Chamadas pagas e treinamento começam desligados. Não escreva chaves em células. A gravação final é responsabilidade do grupo.
''')
code('''from pathlib import Path
import os, sys, subprocess, json

USAR_DRIVE = False
EXECUTAR_NUVEM = False
REPRODUZIR_TREINAMENTO_AUDIO = False

if Path("src/techchallenge4").exists():
    REPO = Path.cwd()
elif (Path.cwd() / "TechChallengeFase4/src/techchallenge4").exists():
    REPO = Path.cwd() / "TechChallengeFase4"
else:
    REPO = Path("/content/TechChallengeFase4")
    if not REPO.exists():
        subprocess.run(["git", "clone", "--branch", "Nirton", "--single-branch",
                        "https://github.com/Val-Faria/TechChallengeFase4.git", str(REPO)], check=True)
sys.path.insert(0, str(REPO / "src"))
if (REPO / ".git").exists():
    print("Código:", subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip())
else:
    print("Código exportado sem metadados Git; conferir os hashes em evidence/auditoria_projeto.json.")
SAIDA = REPO / "integracao/saidas/execucao_colab"
if USAR_DRIVE:
    from google.colab import drive
    drive.mount("/content/drive")
    SAIDA = Path("/content/drive/MyDrive/TechChallengeFase4_entrega/execucao_colab")
''')
md('''## 1. Verificar as evidências executadas

Estas evidências foram salvas na entrega. Sua leitura não envia novos pedidos à OpenAI nem executa os modelos. Consulte `evidence/` para distinguir a reprodução feita nesta entrega das métricas históricas do grupo.
''')
code('''for nome in ["audio_reproducao.json", "audio_externo.json", "video_dataset_auditoria.json", "video_reproducao.json", "video_inferencia_nova.json", "openai_validacao.json", "resumo_execucao.json"]:
    arquivo = REPO / "evidence" / nome
    print(nome, "disponível" if arquivo.exists() else "não disponível nesta versão")
if (REPO / "evidence/resumo_execucao.json").exists():
    print((REPO / "evidence/resumo_execucao.json").read_text(encoding="utf-8"))
''')
md('''## 2. Executar a integração

O JSON de vídeo abaixo contém somente eventos e metadados, sem imagens de terceiros. O CSV precisa ser escolhido explicitamente: não misture a versão antiga com a regenerada.

O exemplo pode conter um áudio sintético novo, vídeo de teste de desenvolvimento do novo YOLO; a reserva é reportada separadamente e séries sintéticas. Sua associação é didática, sem pareamento clínico.
''')
code('''from techchallenge4.demo import run_demo

CSV_AUDIO = REPO / "audio/evidencias/resultado_audio_externo.csv"
JSON_VIDEO = REPO / "evidence/resultado_video_teste.json"
TEXTO = REPO / "evidence/texto_openai_integracao.json"
if not TEXTO.exists():
    TEXTO = REPO / "evidence/texto_openai_demo.json"
resumo = run_demo(SAIDA,
    audio_csv=CSV_AUDIO if CSV_AUDIO.exists() else None,
    audio_filename="novo-03.wav" if CSV_AUDIO.exists() else None,
    video_json=JSON_VIDEO if JSON_VIDEO.exists() else None,
    text_json=TEXTO if TEXTO.exists() else None)
print(json.dumps(resumo, ensure_ascii=False, indent=2))
try:
    from IPython.display import HTML, display
except ImportError:
    def HTML(content):
        return content
    def display(content):
        print("Painel HTML salvo na pasta de saída; abra o arquivo no navegador.")
display(HTML((SAIDA / "painel.html").read_text(encoding="utf-8")))
''')
md('''## 3. Nova análise textual — opcional e paga

Cadastre `OPENAI_API_KEY` nos Secrets do Colab. O adaptador usa cache, limite de chamadas, reserva prévia de orçamento e não repete automaticamente falhas. O limite local protege esta execução; ele não é uma trava de cobrança da conta OpenAI.

A demonstração padrão reutiliza a resposta salva; não exige sua chave.
''')
code('''if EXECUTAR_NUVEM:
    from google.colab import userdata
    from techchallenge4.openai_text import analyze_text_openai
    os.environ["OPENAI_API_KEY"] = userdata.get("OPENAI_API_KEY")
    try:
        analise = analyze_text_openai("Estou com falta de ar e tontura desde o começo da tarde.",
                                     SAIDA / "openai", model="gpt-4o-mini", max_budget_usd=.10)
        print(json.dumps(analise, ensure_ascii=False, indent=2))
    finally:
        os.environ.pop("OPENAI_API_KEY", None)
else:
    print("Chamadas pagas desligadas; nenhum crédito consumido nesta célula.")
''')
md('''## 4. Reprodução do áudio — opcional

A extração das 1.180 gravações demora. O treinamento respeita partições por frase-base; a reserva cega não entra no ajuste final. O script registra as versões e os hashes. Consulte o README antes de instalar as dependências de áudio; essa etapa não é necessária para demonstrar a integração.
''')
code('''if REPRODUZIR_TREINAMENTO_AUDIO:
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(REPO / "requirements-audio.txt")], check=True)
    subprocess.run(["git", "lfs", "pull"], cwd=REPO, check=True)
    subprocess.run([sys.executable, str(REPO / "scripts/audio_reproduce.py"), "--device", "auto"], cwd=REPO, check=True)
else:
    print("Treinamento desligado. Usando evidências já salvas.")
''')
md('''## 5. Monitoramento incremental de demonstração

Os pacotes são processados um a um: 30 amostras formam uma referência anterior congelada; uma observação normal é seguida por uma alteração em sinais vitais, movimento e prescrição. Todos esses dados são sintéticos. A latência cobre detectores estatísticos, fusão e registro local, sem aquisição de sensores nem inferência dos modelos.

Para uma fonte que acrescenta linhas ao arquivo, o comando `scripts/run_stream.py --input arquivo.jsonl --follow --idle-timeout 5 --max-events 1000` acompanha novas linhas e encerra com limite de eventos ou ociosidade.
''')
code('''from techchallenge4.monitor import example_packets, run_stream
from techchallenge4.reports import atomic_write

FLUXO = SAIDA / "monitoramento_incremental"
ENTRADA_STREAM = FLUXO / "entrada_sintetica.jsonl"
atomic_write(ENTRADA_STREAM, "".join(json.dumps(p, ensure_ascii=False) + "\\n" for p in example_packets()))
monitoramento = run_stream(ENTRADA_STREAM, FLUXO, max_events=32)
print(json.dumps(monitoramento, ensure_ascii=False, indent=2))
display(HTML((FLUXO / "painel.html").read_text(encoding="utf-8")))
''')
md('''## 5.1. Inferência acústica/visual acrescentada

O guia `integracao/MIDIAS.md` apresenta a execução sobre WAV e vídeo, com referência de voz anterior e fluxo óptico real. Os oito controles acústicos e dois clipes geométricos constam em `evidence/midias_complementares.json`. A reprodução no ritmo original mede inferência local e entrega; não inclui ASR/nuvem. As mídias e caixas estão no backup privado do Drive. A inferência YOLO nova tem evidência própria; os controles físicos não são rótulos clínicos.
''')
md('''## 6. Salvar e encerrar

O ZIP desta célula contém resultados da integração, sem credenciais ou modelos. Se usar GPU no Colab, primeiro salve seus artefatos no Drive e depois use **Ambiente de execução → Desconectar e excluir ambiente de execução**. Fechar a aba não encerra a sessão.
''')
code('''import zipfile
PACOTE = SAIDA.parent / "resultados_integracao.zip"
with zipfile.ZipFile(PACOTE, "w", zipfile.ZIP_DEFLATED) as z:
    for arquivo in SAIDA.rglob("*"):
        if arquivo.is_file() and arquivo.suffix in {".json", ".jsonl", ".csv", ".md", ".html"}:
            z.write(arquivo, arquivo.relative_to(SAIDA))
print("Resultados salvos:", PACOTE)
try:
    from google.colab import files
    files.download(str(PACOTE))
except ImportError:
    pass
''')

nb = {'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
                              'language_info':{'name':'python','version':'3.12'}},'nbformat':4,'nbformat_minor':5}
(ROOT/'integracao/TechChallengeFase4_integracao.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=1),encoding='utf-8')
print('Notebook de integração atualizado.')
