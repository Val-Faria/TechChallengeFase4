# Organização e manutenção

As modalidades permanecem separadas para permitir executar e avaliar cada componente. O pacote `src/techchallenge4` contém contratos e regras compartilhadas; os notebooks são pontos de apresentação, não cópias dessas regras.

## Responsabilidades

- `core.py`: normalização de fontes, fusão e detectores estruturados.
- `delivery.py` e `reports.py`: persistência idempotente, auditoria e exportação atômica.
- `monitor.py` e `media_stream.py`: processamento incremental e medições de latência.
- `openai_audio.py` e `openai_text.py`: chamadas, cache e controles locais de consumo.
- `audio_evaluation.py`: avaliação do modelo congelado com conferência de hashes.
- `video/`: inferência, regra temporal, calibração e referência de aparência.
- `scripts/`: entradas de reprodução, validação e construção dos artefatos.

Comentários e docstrings descrevem decisões, limites e efeitos das interfaces. Os nomes do contrato são preservados para manter compatibilidade entre módulos.

## Verificar uma alteração

```powershell
python -m pytest -q
python -m ruff check src scripts tests video relatorio --select E9,F63,F7,F82,F401
python scripts/verificar_entrega.py
```

Para atualizar as fontes dos notebooks, executar os três scripts `gerar_notebook_audio.py`, `gerar_notebook_video.py` e `gerar_notebook_integracao.py`. Depois formatar os notebooks com Ruff e executar `python scripts/executar_notebooks.py`. O executor interrompe na primeira falha e salva as saídas calculadas, com versões e hashes em `evidence/notebooks_execucao.json`. Não preencher saídas manualmente.

Para o relatório, executar `python relatorio/gerar_relatorio.py --compile --package`. Os mesmos arquivos LaTeX e figuras integram o Overleaf. Preservar os resultados originais, os protocolos e a identificação dos dados sintéticos. Saídas experimentais novas ficam nas pastas ignoradas; não substituir pesos congelados para repetir uma apresentação.
