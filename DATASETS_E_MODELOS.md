# Dados e modelos da entrega final

## Áudio

- Dataset: `audio/datasets/dataset_audio_emocoes_1180.zip`, versionado por Git LFS. Depois de clonar, executar `git lfs pull`.
- Modelo congelado: `artifacts/audio/modelo_audio_1180.joblib`, ajustado somente nos 712 exemplos de treino. SHA-256 e ambiente em `artifacts/audio/manifesto_audio.json` e `evidence/audio_reproducao.json`.
- Reprodução: `python scripts/audio_reproduce.py --device auto`. Não incorporar as reservas ao treino avaliado.
- O modelo anterior da autora, ajustado com todos os 1.180 exemplos, fica como histórico no backup privado. Ele não substitui o modelo com isolamento.

O corpus é sintético. As provas novas têm hashes/frases distintos e não foram usadas no ajuste. As derivações dos controles físicos compartilham fonte e não são observações independentes de pacientes.

## Vídeo

Fonte oficial: [Uterus v4, Roboflow Universe](https://universe.roboflow.com/machinelearning-yekk6/uterus-qn1he/dataset/4). Licença declarada: CC BY 4.0; autor Machinelearning. O link consta no notebook e no relatório originais. A exportação YOLOv8 exige login no Roboflow.

O arquivo `Uterus.v4i.yolov8.zip`, recebido na pasta principal do projeto em 11/11/2026, tem 40.622.141 bytes e SHA-256 `d2345667a5efa840b7f1f3ff33af52ebf25d8ccf0f7c3c985afdeba6d7e04bf8`. Não está no histórico Git nem nas branches verificadas; está preservado no Drive da equipe. A página anuncia 1.368 imagens, enquanto esse ZIP tem 1.367: 1.196 treino, 114 validação e 57 teste. A diferença foi mantida na auditoria.

### Preparação reproduzível

```powershell
python -m pip install -e . -r requirements-video.txt
python scripts/video_reproduce.py --dataset-zip ../Uterus.v4i.yolov8.zip --audit-only
python scripts/video_reproduce.py --dataset-zip ../Uterus.v4i.yolov8.zip --epochs 80 --batch 8
```

Instalar PyTorch/torchvision para a GPU conforme documentação do fornecedor. A execução registrada utiliza RTX 2060 local, PyTorch 2.11.0+cu128, torchvision 0.26.0+cu128 e Ultralytics 8.4.208. Não há uso de API paga ou sessão Colab nessa reprodução.

O preparador verifica CRC, nomes de arquivo, coordenadas e duplicatas; três entradas idênticas de `data.yaml` são aceitas. Os 418 polígonos utilizados são convertidos em caixas envolventes, resolvendo a mistura de formatos para a tarefa de detecção sem inferir rótulos novos.

O clipe `2024-09-26-20-27-33_mp4` fica inteiramente fora do desenvolvimento: suas 420 imagens aumentadas de treino não são usadas, e 60 quadros de validação/teste originais passam à reserva cega. `UterusClip_mov` fornece 776/74/37 imagens para treino/validação/teste. A reserva não seleciona checkpoint nem limiares. Prefixo de arquivo não comprova paciente ou procedimento independente.

### Modelo e inferência

O novo peso é `artifacts/video/best_uterus_tools_nirton_v4.pt`. Ele é um novo treinamento, não recuperação do peso do Marcelo. Seu manifesto registra hash e ajuste apenas em treino, com seleção pela validação. Está no pacote privado do Drive, junto das mídias; copiar para esse caminho após extrair o pacote na raiz do repositório.

```powershell
python scripts/video_infer_reserva.py
```

O comando gera montagens novas de teste e de reserva, executa YOLO nos quadros e produz JSON, relatório, vídeo anotado e evidência temporal. A montagem reservada não participa do treino/validação/teste de desenvolvimento do novo modelo. Dois segundos por quadro são uma construção de demonstração e não a duração original de um evento clínico. A referência deriva de caixas e regra temporal, sem rótulo de complicação médica.

Os números históricos da equipe e as novas métricas têm protocolos diferentes e permanecem separados. Nenhum vídeo clínico ou imagem de terceiros é republicado automaticamente no Git ou no Overleaf.

## Backup e credenciais

O diretório `ENTREGA_FINAL_FASE4`, na pasta principal sincronizada com o Drive, contém relatório, Overleaf, código, artefatos privados e manifestos. Extrair os artefatos privados na raiz do repositório preserva os caminhos necessários. A chave OpenAI fica fora de todos os pacotes; `OPENAI_API_KEY` é opcional para novas chamadas, nunca para a demonstração com cache.

## Revisão de cobertura e fonte complementar

`artifacts/video/referencia_visual.json` registra mediana/MAD calculadas somente em treino e limite de retenção escolhido na validação. O arquivo contém hash do peso e do dataset. `calibracao_alertas.json` é um candidato experimental **não promovido**; a inferência mantém 0,4/0,6. A referência visual não corrige nem inventa rótulos anatômicos.

[Procedimento e resultados](relatorio/revisao_video.md). A fonte adicional é o [TVASurg da Universidade de Toronto](https://pie.med.utoronto.ca/TVASurg/project/gyn-tlh/). `python scripts/video_verificar_externo.py --baixar` obtém o vídeo oficial público (152.904.066 bytes, limitado a 200 MB); `python scripts/video_verificar_cobertura.py` reproduz a proteção e a reserva temporal declarada. Não há ajuste do YOLO nessas mídias, nem anotações médicas que permitam calcular acurácia clínica. Todos os intervalos já executados estão identificados; reexecutá-los não cria uma reserva nova.

O vídeo externo fica em `dados_privados/video_externo_tvasurg/`, fora do Git e do PDF. A fonte declara direitos reservados: não publicar imagens na apresentação sem autorização; usar os resultados sanitizados e a página oficial. O backup privado da equipe preserva os arquivos para reprodução, com os hashes e a atribuição. Nenhuma chave acompanha os pacotes.
