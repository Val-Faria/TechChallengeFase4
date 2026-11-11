# Novo YOLOv8s — Uterus v4

Peso: `artifacts/video/best_uterus_tools_nirton_v4.pt`. SHA-256: `efe5cc2588300eea0b62e2921c2ca870f56d8d7991ece4637122cb407910a53a`.

O peso fica no pacote privado do Drive; restaurá-lo nesse caminho após extrair `artefatos_privados.zip` na raiz do repositório. Ele é um novo treinamento, não o peso original de Marcelo.

Arquitetura YOLOv8s, classes Tools/Uterus, resolução 416, batch 8, semente 42, 80 épocas e paciência 20. GPU RTX 2060; versões e configuração em `evidence/video_reproducao.json`. Seleção pela validação, sem escolher checkpoint ou limiar pela reserva.

Dados: 776 treino, 74 validação, 37 teste do prefixo UterusClip_mov. Sessenta quadros do outro prefixo formam a reserva; seus 420 aumentos não são usados. Os 418 polígonos usados foram convertidos em caixas. Identidade de prefixo não comprova paciente independente, e o pré-treinamento externo não foi auditado integralmente.

mAP50: validação 0.941, teste 0.980, reserva 0.613. A regra temporal recuperou 2/3 eventos no teste e 0/2 na reserva. Não ajustar a reserva depois de revelada nem apresentar esses resultados como desempenho clínico confiável.

Reprodução: `scripts/video_reproduce.py`; inferência: `scripts/video_infer_reserva.py`. As montagens e suas anotações temporais são demonstrações, não vídeos contínuos de pacientes independentes. Consultar `DATASETS_E_MODELOS.md` e o relatório.
