"""Entrada de vídeo portátil; evidências por padrão, treino/inferência opcionais."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
cells=[]


def cell(kind,text):
    value={"cell_type":kind,"id":hashlib.sha256((kind+text).encode()).hexdigest()[:12],
           "metadata":{},"source":text.splitlines(keepends=True)}
    if kind=="code":value.update({"execution_count":None,"outputs":[]})
    cells.append(value)


cell("markdown",'''# Fase 4 — vídeo: novo YOLOv8s e reserva de clipe

Entrada da **branch Nirton**, usando os scripts compartilhados. O modelo novo não é o peso original do Marcelo. Há 776 imagens de treino, 74 de validação, 37 de teste e 60 quadros de um prefixo inteiro reservado. Os 418 polígonos usados são convertidos em caixas, sem inventar estruturas.

O modo padrão lê evidências reais, sem GPU, credenciais, API ou novos treinos. A reserva não é usada para escolher checkpoint ou limiar. Montagens de quadros não representam cirurgias contínuas externas. Consulte `DATASETS_E_MODELOS.md`.
''')
cell("code",'''from pathlib import Path
import json, sys, subprocess

TREINAR_NOVO_ESTUDO = False
REEXECUTAR_INFERENCIA = False
if Path("src/techchallenge4").is_dir():
    REPO = Path.cwd()
elif (Path.cwd() / "TechChallengeFase4/src/techchallenge4").is_dir():
    REPO = Path.cwd() / "TechChallengeFase4"
else:
    REPO = Path("/content/TechChallengeFase4")
    if not REPO.exists():
        subprocess.run(["git", "clone", "--branch", "Nirton", "--single-branch",
                        "https://github.com/Val-Faria/TechChallengeFase4.git", str(REPO)], check=True)
sys.path.insert(0, str(REPO / "src"))
# Extrair artefatos_privados.zip na raiz do REPO preserva os caminhos esperados.
ZIP_DATASET = REPO.parent / "Uterus.v4i.yolov8.zip"
print("Repositório:", REPO)
''')
cell("markdown",'''## 1. Conferir o protocolo e os resultados

A página anuncia 1.368 imagens; o ZIP recebido contém 1.367. O preparador registra a diferença, CRC, duplicatas, coordenadas, transformações e a origem da reserva. O prefixo reservado não aparece em treino, validação ou teste do novo estudo.
''')
cell("code",'''for nome in ["video_dataset_auditoria.json", "video_reproducao.json", "video_inferencia_nova.json"]:
    arquivo = REPO / "evidence" / nome
    dados = json.loads(arquivo.read_text(encoding="utf-8"))
    if nome == "video_dataset_auditoria.json":
        print("Partições:", dados["counts_clean"])
        print("Reserva:", dados["blind_source_clip"])
        print("Contornos convertidos:", dados["polygons_converted_to_boxes"])
    elif nome == "video_reproducao.json":
        print("Novo modelo:", dados["model"])
        print("Avaliação:", json.dumps(dados["evaluation"], ensure_ascii=False, indent=2))
    else:
        print("Montagens:", [(m["partition"], m["predicted_events"], m["duration_s"]) for m in dados["montages"]])
''')
cell("markdown",'''## 2. Resultado reservado usado na integração

O JSON sanitizado não contém imagens privadas. A marca de simulação identifica a construção temporal da montagem; as detecções são inferências reais do novo YOLO. A referência temporal usa caixas anotadas, não rótulos de complicação médica.
''')
cell("code",'''resultado_video = json.loads((REPO / "evidence/resultado_video_novo.json").read_text(encoding="utf-8"))
from techchallenge4.core import normalizar_video
fonte = normalizar_video(resultado_video, origem="YOLO_novo_clipe_reservado")
print(json.dumps(fonte, ensure_ascii=False, indent=2))
''')
cell("markdown",'''## 3. Repetir inferência — opcional

Instalar as dependências de vídeo e extrair o pacote privado na raiz do repositório. Para preparar o dataset sem treinar, use `--audit-only`. O comando abaixo usa o peso congelado e seus hashes. Não escolha limiares novos a partir da reserva.
''')
cell("code",'''if REEXECUTAR_INFERENCIA:
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(REPO / "requirements-video.txt")], check=True)
    subprocess.run([sys.executable, str(REPO / "scripts/video_reproduce.py"),
                    "--dataset-zip", str(ZIP_DATASET), "--audit-only"], cwd=REPO, check=True)
    subprocess.run([sys.executable, str(REPO / "scripts/video_infer_reserva.py")], cwd=REPO, check=True)
else:
    print("Inferência opcional desligada; resultados reais salvos foram carregados.")
''')
cell("markdown",'''## 4. Treinamento e encerramento

O script recusa sobrescrever o modelo congelado já existente. Um novo ajuste depois de ver a reserva é outro estudo, sem direito de reutilizar aquela reserva como inédita. O treino original desta consolidação usa GPU local, 80 épocas máximas, batch 8, resolução 416, semente 42 e paciência 20.

No Colab, configurar CUDA e instalar PyTorch/torchvision conforme o ambiente antes de treinar. **Salvar pesos, manifesto e saídas no Drive; depois usar Ambiente de execução → Desconectar e excluir ambiente de execução.** Fechar a aba não encerra a GPU.
''')
cell("code",'''if TREINAR_NOVO_ESTUDO:
    subprocess.run([sys.executable, str(REPO / "scripts/video_reproduce.py"),
                    "--dataset-zip", str(ZIP_DATASET), "--epochs", "80", "--batch", "8"], cwd=REPO, check=True)
else:
    print("Treino desligado. Nenhuma GPU ou API foi utilizada por este notebook no modo padrão.")
''')

notebook={"cells":cells,"metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},
          "language_info":{"name":"python","version":"3.12"}},"nbformat":4,"nbformat_minor":5}
(ROOT/"video/TechChallengeFase4_video.ipynb").write_text(json.dumps(notebook,ensure_ascii=False,indent=1),encoding="utf-8")
print("Notebook de vídeo atualizado a partir dos scripts compartilhados.")
