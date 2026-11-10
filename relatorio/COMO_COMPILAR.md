# Relatório em LaTeX

O PDF é compilado a partir de `latex/main.tex`, a mesma fonte incluída no pacote `overleaf_fase4.zip`. Não há dependência de imagens privadas de cirurgia nem de credenciais.

## Overleaf

1. Crie um projeto com **New Project > Upload Project**.
2. Envie `overleaf_fase4.zip`.
3. Selecione `main.tex` como documento principal.
4. Compile com **pdfLaTeX**. O projeto também é compatível com XeLaTeX/Tectonic.

`dados_gerados.tex` contém tabelas e números extraídos das evidências no momento da geração. Alterar o relatório não executa modelos nem chama APIs.

## Compilação local

Na raiz do repositório:

```powershell
python relatorio/gerar_relatorio.py --compile --package
```

É necessário ter Tectonic disponível no PATH. Também é possível indicar o executável:

```powershell
python relatorio/gerar_relatorio.py --compile --package --tectonic C:/caminho/tectonic.exe
```

O PDF final fica em `output/pdf/relatorio_tecnico_fase4.pdf`. As fontes e o ZIP ficam em `relatorio/`.

Para usar uma instalação LaTeX tradicional, abra `relatorio/latex/` e execute `pdflatex main.tex` duas vezes. O sumário e a paginação exigem as passagens adicionais.

## Atualizar resultados

Execute primeiro os scripts de reprodução. Depois execute novamente `gerar_relatorio.py`. O gerador usa `evidence/audio_reproducao.json`, `evidence/resumo_execucao.json` e os resultados de `integracao/evidencias/execucao_final/` quando presentes.

Não inclua arquivos `.env`, bancos de alertas, áudios, vídeos privados, chaves ou cabeçalhos de autenticação no projeto Overleaf. O pacote produzido pelo gerador utiliza uma lista explícita de formatos e diretórios de documentação.
