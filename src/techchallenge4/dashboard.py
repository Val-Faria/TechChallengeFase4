"""Painel acadêmico local de revisão; execução vinculada somente a 127.0.0.1."""
from __future__ import annotations
import argparse
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs
from .delivery import AlertStore


def render_dashboard(alerts, *, interactive=True):
    modalities = {"audio": "Voz", "video": "Vídeo", "texto_openai": "Relato da consulta",
                  "texto_azure": "Relato da consulta", "sinais_vitais": "Sinais vitais",
                  "movimentacao": "Movimentação", "prescricoes": "Prescrições"}
    statuses = {"ok": "disponível", "baixa_confianca": "baixa confiança",
                "indisponivel": "indisponível", "erro": "falha no processamento"}
    priorities = {"alto": "ALTO", "medio": "MÉDIO", "baixo": "BAIXO", "nenhum": "SEM SINAL"}
    coverage = {"completo": "completa", "incompleto": "incompleta"}
    cards = []
    for item in alerts:
        r = item["resultado"]
        e = html.escape
        sources = "".join(f"<li><b>{e(modalities.get(f['modalidade'], f['modalidade']))}</b>: "
                          f"{e(statuses.get(f['status'], f['status']))}"
                          f"{' (cobertura parcial)' if f.get('cobertura_parcial') else ''} — "
                          f"{e(f['motivo'].replace('ansiedade_hesitacao', 'ansiedade/hesitação'))}"
                          + ("<details><summary>Limitações para revisão</summary><ul>" +
                             "".join("<li>" + e(v) + "</li>" for v in f.get("limitacoes", [])) +
                             "</ul></details>" if f.get("limitacoes") else "") + "</li>"
                          for f in r["fontes"])
        state = f"Revisado por {e(item['revisor'])}" if item["revisado_em_utc"] else "Aguardando revisão"
        action = ""
        if interactive and not item["revisado_em_utc"]:
            action = (f'<form method="post" action="/ack"><input type="hidden" name="id" value="{e(r["id_resultado"])}">'
                      '<label>Revisor <input name="reviewer" required maxlength="80" value="demonstracao"></label>'
                      '<button type="submit">Confirmar revisão</button></form>')
        cards.append(f'<article><div class="tag">{e(priorities.get(r["nivel"], r["nivel"]))}</div><h2>{e(r["id_caso"])}</h2>'
                     f'<p>{state} · cobertura {e(coverage.get(r["status"], r["status"]))}</p>'
                     f'<p>Contém fonte simulada: {"sim" if r["simulado"] else "não"}.</p>'
                     '<p class="origin">Fontes associadas para demonstração; sem pareamento clínico.</p>'
                     f'<ul>{sources}</ul>{action}</article>')
    return '''<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Caixa de revisão · Tech Challenge 4</title><style>
:root{font-family:system-ui,sans-serif;color:#173339;background:#f3f6f5}body{max-width:1080px;margin:auto;padding:32px}
h1{font-size:32px;margin-bottom:8px}header p{max-width:760px;line-height:1.6}.note{border-left:4px solid #416f70;padding:12px 16px;background:#e6efed}
article{background:white;border:1px solid #cad8d6;margin:22px 0;padding:24px;border-radius:10px}
article h2{margin-top:4px}li{margin-bottom:8px;line-height:1.5}.tag{float:right;padding:6px 12px;background:#fce5cb;border-radius:5px;font-weight:bold}
.origin{font-size:13px;overflow-wrap:anywhere;color:#4c6264}button{background:#245a59;color:white;border:0;padding:10px 16px;border-radius:5px;cursor:pointer}
input{padding:8px;border:1px solid #aabdbb;border-radius:4px;margin:8px}footer{margin-top:32px;color:#526866}
</style><header><p>FIAP · Pós Tech IA para Devs</p><h1>Caixa de revisão multimodal</h1>
<p>Alertas e fontes inconclusivas registrados para avaliação humana.</p>
<p class="note">Protótipo acadêmico. Sem diagnóstico e sem conexão a um hospital.
Dados de demonstração. Origem e limitações registradas no relatório; avaliação humana necessária.</p></header><main>''' + (
        "".join(cards) or "<article>Nenhum resultado aguardando revisão.</article>") + (
        "</main><footer>Atualize a página para consultar novas entregas. A confirmação registra revisão local, sem alterar tratamento.</footer></html>")


def serve(db_path, port=8765):
    store = AlertStore(db_path)
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != "/":
                self.send_error(404)
                return
            content = render_dashboard(store.list_alerts()).encode("utf8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(content)

        def do_POST(self):
            if self.path != "/ack":
                self.send_error(404)
                return
            host = self.headers.get("Host", "")
            if host not in {f"127.0.0.1:{port}", f"localhost:{port}"}:
                self.send_error(403)
                return
            origin = self.headers.get("Origin")
            if origin and origin not in {f"http://127.0.0.1:{port}", f"http://localhost:{port}"}:
                self.send_error(403)
                return
            try:
                length = int(self.headers.get("Content-Length", 0))
                if not 0 < length <= 4096:
                    raise ValueError("Tamanho inválido.")
                values = parse_qs(self.rfile.read(length).decode("utf8"))
                store.acknowledge(values["id"][0], values["reviewer"][0])
            except (ValueError, KeyError, UnicodeError):
                self.send_error(400)
                return
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Painel local: http://127.0.0.1:{port} (Ctrl+C encerra)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="integracao/evidencias/execucao_final/alertas.sqlite3")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    serve(args.db, args.port)


if __name__ == "__main__":
    main()
