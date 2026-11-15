"""Painel acadêmico local de revisão; execução vinculada somente a 127.0.0.1."""

from __future__ import annotations
import argparse
import html
import json
import re
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from .entradas import MAX_REQUEST_BYTES, parse_form
from .delivery import AlertStore
from .consulta_web import Processing, form_html, evidence_html, running_html
from .consulta import ROOT, WAVS, VIDEOS, AUDIO_DIR, VIDEO_DIR


def render_dashboard(alerts, *, interactive=True, entry="", running=False):
    modalities = {
        "audio": "Classe acústica",
        "padrao_vocal": "Padrão de pausas da voz",
        "video": "Vídeo",
        "texto_openai": "Relato da consulta",
        "texto_azure": "Relato da consulta",
        "sinais_vitais": "Sinais vitais",
        "movimentacao": "Movimentação",
        "prescricoes": "Prescrições",
    }
    statuses = {
        "ok": "disponível",
        "baixa_confianca": "baixa confiança",
        "indisponivel": "indisponível",
        "erro": "falha no processamento",
    }
    priorities = {"alto": "ALTO", "medio": "MÉDIO", "baixo": "BAIXO", "nenhum": "SEM SINAL"}
    coverage = {"completo": "completa", "incompleto": "incompleta"}
    cards = []
    for item in alerts:
        r = item["resultado"]
        e = html.escape
        sources = "".join(
            f"<li><b>{e(modalities.get(f['modalidade'], f['modalidade']))}</b>: "
            f"{e(statuses.get(f['status'], f['status']))}"
            f"{' (cobertura parcial)' if f.get('cobertura_parcial') else ''} — "
            f"{e(f['motivo'].replace('ansiedade_hesitacao', 'ansiedade/hesitação'))}"
            + (
                "<details><summary>Limitações para revisão</summary><ul>"
                + "".join("<li>" + e(v) + "</li>" for v in f.get("limitacoes", []))
                + "</ul></details>"
                if f.get("limitacoes")
                else ""
            )
            + "</li>"
            for f in r["fontes"]
        )
        state = (
            f"Revisado por {e(item['revisor'])}"
            if item["revisado_em_utc"]
            else "Aguardando revisão"
        )
        action = ""
        if interactive and not item["revisado_em_utc"]:
            action = (
                f'<form method="post" action="/ack"><input type="hidden" name="id" value="{e(r["id_resultado"])}">'
                '<label>Revisor <input name="reviewer" required maxlength="80" placeholder="Nome do revisor"></label>'
                '<button type="submit">Confirmar revisão</button></form>'
            )
        cards.append(
            f'<article><div class="tag">{e(priorities.get(r["nivel"], r["nivel"]))}</div><h2>{e(r["id_caso"])}</h2>'
            f"<p>{state} · cobertura {e(coverage.get(r['status'], r['status']))}</p>"
            f"<p>Contém fonte simulada: {'sim' if r['simulado'] else 'não'}.</p>"
            '<p class="origin">Fontes associadas para demonstração; sem pareamento clínico.</p>'
            f"<ul>{sources}</ul>{evidence_html(r)}{action}</article>"
        )
    return (
        """<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Caixa de revisão · Tech Challenge 4</title><style>
:root{font-family:system-ui,sans-serif;color:#173339;background:#f3f6f5}body{max-width:1080px;margin:auto;padding:32px}
h1{font-size:32px;margin-bottom:8px}header p{max-width:760px;line-height:1.6}.note{border-left:4px solid #416f70;padding:12px 16px;background:#e6efed}
article{background:white;border:1px solid #cad8d6;margin:22px 0;padding:24px;border-radius:10px}
article h2{margin-top:4px}li{margin-bottom:8px;line-height:1.5}.tag{float:right;padding:6px 12px;background:#fce5cb;border-radius:5px;font-weight:bold}
.origin{font-size:13px;overflow-wrap:anywhere;color:#4c6264}button{background:#245a59;color:white;border:0;padding:10px 16px;border-radius:5px;cursor:pointer}
input{padding:8px;border:1px solid #aabdbb;border-radius:4px;margin:8px}footer{margin-top:32px;color:#526866}
.entry{background:#fff;border-top:4px solid #245a59;border-radius:8px;padding:22px 24px;margin:22px 0}
.entry [hidden]{display:none!important}.entry h2{margin-top:0}.entry label{display:block;margin:14px 0;font-weight:600}
.entry select,.entry input[type=password]{display:block;box-sizing:border-box;padding:9px;margin:4px 0;width:min(100%,480px);border:1px solid #91aaa4;border-radius:4px}
.findings{margin:18px 0;padding:14px;background:#f2f7f5}summary{cursor:pointer}blockquote{border-left:3px solid #8eb1aa;margin:8px 0;padding-left:12px}
audio,video{display:block;width:min(100%,480px);margin:10px 0}video,#live-frame{max-width:100%;border-radius:6px;background:#142827}#live-frame{display:block;width:480px;margin:14px 0}#live-frame[hidden]{display:none}progress{display:block;width:min(100%,480px);height:18px}#stage{font-weight:600}</style>"""
        + ('<script src="/painel.js" defer></script>' if entry else "")
        + """<header><p>FIAP · Pós Tech IA para Devs</p><h1>Caixa de revisão multimodal</h1>
<p>Alertas e fontes inconclusivas registrados para avaliação humana.</p>
<p class="note">Protótipo acadêmico. Sem diagnóstico e sem conexão a um hospital.
Dados de demonstração. Origem e limitações registradas no relatório; avaliação humana necessária.</p></header><main>"""
        + entry
        + ("".join(cards) or "<article>Nenhum resultado aguardando revisão.</article>")
        + (
            "</main><footer>Atualize a página para consultar novas entregas. A confirmação registra revisão local, sem alterar tratamento.</footer></html>"
        )
    )


def create_server(db_path, port=8765):
    store = AlertStore(db_path)

    processing = Processing(store)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.headers.get("Host") not in {f"127.0.0.1:{port}", f"localhost:{port}"}:
                self.send_error(403)
                return
            path = urlsplit(self.path).path
            if path == "/status":
                self.send_bytes(json.dumps(processing.status()).encode(), "application/json")
                return
            if path == "/quadro.jpg":
                with processing.lock:
                    frame = processing.image
                if frame:
                    self.send_bytes(frame, "image/jpeg")
                else:
                    self.send_error(404)
                return
            if path == "/painel.js":
                self.send_bytes(
                    Path(__file__).with_name("painel.js").read_bytes(), "text/javascript"
                )
                return
            if path.startswith("/midia/audio/") and path.removeprefix("/midia/audio/") in WAVS:
                self.media(ROOT / AUDIO_DIR / path.removeprefix("/midia/audio/"), "audio/wav")
                return
            if path.startswith("/midia/video/") and path.removeprefix("/midia/video/") in VIDEOS:
                name = Path(path).stem + ".webm"
                self.media(ROOT / VIDEO_DIR / "visualizacao" / name, "video/webm")
                return
            case_media = re.fullmatch(
                r"/caso/(consulta-\d{8}-\d{6}-[a-f0-9]{6})/(audio.wav|video_anotado.webm)", path
            )
            if case_media:
                case, name = case_media.groups()
                folder = store.path.parent / "consultas" / case
                if name == "audio.wav":
                    self.media(folder / "entradas" / name, "audio/wav")
                else:
                    self.media(folder / "video" / name, "video/webm")
                return
            if path != "/":
                self.send_error(404)
                return
            self.page()

        def page(self, message="", status=200):
            running, stage, error, case, token = processing.view()
            entry = running_html(processing) if running else form_html(token)
            if message or error:
                entry = (
                    '<p role="alert" class="note">' + html.escape(message or error) + "</p>" + entry
                )
            elif case:
                entry += "<p>Consulta concluída · " + html.escape(case) + "</p>"
            content = render_dashboard(
                reversed(store.list_alerts()), entry=entry, running=running
            ).encode("utf8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'none'; script-src 'self'; connect-src 'self'; img-src 'self'; media-src 'self' blob:; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
            )
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(content)

        def send_bytes(self, content, content_type):
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(content)

        def media(self, path, content_type):
            if not path.is_file():
                self.send_error(404)
                return
            size = path.stat().st_size
            start, end = 0, size - 1
            value = self.headers.get("Range")
            if value:
                match = re.fullmatch(r"bytes=(\d*)-(\d*)", value)
                if not match or not any(match.groups()):
                    self.range_error(size)
                    return
                first, last = match.groups()
                if first:
                    start, end = int(first), min(int(last), size - 1) if last else size - 1
                else:
                    start = max(0, size - int(last))
                    if int(last) == 0:
                        self.range_error(size)
                        return
                if start >= size or end < start:
                    self.range_error(size)
                    return
            self.send_response(206 if value else 200)
            self.send_header("Content-Type", content_type)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(end - start + 1))
            if value:
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.end_headers()
            try:
                with path.open("rb") as stream:
                    stream.seek(start)
                    remaining = end - start + 1
                    while remaining:
                        chunk = stream.read(min(65536, remaining))
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        remaining -= len(chunk)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass  # O navegador pode cancelar uma faixa ao avançar o vídeo.

        def range_error(self, size):
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.end_headers()

        def do_POST(self):
            if self.path not in {"/ack", "/processar"}:
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
                limit = MAX_REQUEST_BYTES if self.path == "/processar" else 4096
                if not 0 < length <= limit:
                    raise ValueError("Tamanho inválido.")
                body = self.rfile.read(length)
                if len(body) != length:
                    raise ValueError("Envio incompleto.")
                values, uploads = parse_form(self.headers.get("Content-Type", ""), body)
                if self.path == "/processar":
                    try:
                        processing.start(values, uploads)
                    except ValueError as exc:
                        self.page(str(exc), 400)
                        return
                else:
                    store.acknowledge(values["id"][0], values["reviewer"][0])
            except (ValueError, KeyError, UnicodeError):
                self.send_error(400)
                return
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    port = server.server_port
    return server


def serve(db_path, port=8765):
    server = create_server(db_path, port)
    print(f"Painel local: http://127.0.0.1:{port} (Ctrl+C encerra)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="integracao/saidas/painel/alertas.sqlite3")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    serve(args.db, args.port)


if __name__ == "__main__":
    main()
