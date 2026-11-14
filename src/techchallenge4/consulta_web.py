"""Formulário, acompanhamento da execução e evidências de uma consulta."""

from html import escape
from threading import Lock, Thread
from secrets import token_urlsafe
import re
import time

from .consulta import ROOT, WAVS, VIDEOS, missing_files, process_case


class Processing:
    def __init__(self, store):
        self.store = store
        self.lock = Lock()
        self.token = token_urlsafe(24)
        self.running = False
        self.stage = ""
        self.error = ""
        self.case = ""
        self.wav = "novo-03.wav"
        self.mp4 = "montagem_test.mp4"
        self.image = None
        self.video_progress = None
        self.last_frame_at = 0.0

    def start(self, form):
        wav, mp4, key = (form.get(k, [""])[0].strip() for k in ("audio", "video", "chave"))
        if (
            wav not in WAVS
            or mp4 not in VIDEOS
            or not re.fullmatch(r"sk-[A-Za-z0-9_-]{8,500}", key)
        ):
            raise ValueError("Selecione as mídias e informe uma chave da API OpenAI.")
        if missing_files(ROOT, wav, mp4):
            raise ValueError(
                "Os arquivos da seleção estão ausentes. Confira se o download do repositório foi concluído."
            )
        with self.lock:
            if self.running or form.get("token") != [self.token]:
                raise ValueError(
                    "Esta solicitação já foi usada. Atualize o painel antes de iniciar outra consulta."
                )
            self.token = token_urlsafe(24)
            self.running = True
            self.stage = "Extraindo características de voz e transcrevendo com Whisper local"
            self.case = self.error = ""
            self.wav, self.mp4 = wav, mp4
            self.image = self.video_progress = None
            self.last_frame_at = 0.0
        Thread(target=self._run, args=(wav, mp4, key), daemon=True).start()

    def _progress(self, stage):
        with self.lock:
            self.stage = stage

    def frame(self, image, seconds, processed, total):
        import cv2

        now = time.monotonic()
        if now - self.last_frame_at < 0.4 and processed < total:
            return
        ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if ok:
            with self.lock:
                self.image = encoded.tobytes()
                self.video_progress = {"seconds": seconds, "processed": processed, "total": total}
                self.last_frame_at = now

    def status(self):
        with self.lock:
            return {
                "running": self.running,
                "stage": self.stage,
                "error": self.error,
                "case": self.case,
                "video": self.video_progress,
                "frame": self.last_frame_at,
            }

    def _run(self, wav, mp4, key):
        try:
            case = process_case(
                ROOT, self.store, wav, mp4, key, self._progress, on_frame=self.frame
            )
            with self.lock:
                self.case = case
        except Exception as exc:
            # Mostra apenas orientações fixas. Respostas do provedor e credenciais
            # nunca são copiadas para a página nem para o histórico do painel.
            msg = str(exc)
            http = re.search(r"HTTP (\d{3})", msg)
            if http:
                status = http.group(1)
                detail = {
                    "401": "Confira a chave informada.",
                    "403": "Confira a permissão do projeto para esse modelo.",
                    "429": "Confira os créditos e os limites de requisições.",
                }.get(status, "Confira a disponibilidade da API.")
                reason = f"OpenAI retornou HTTP {status}. {detail}"
            elif isinstance(exc, ImportError):
                reason = "Confira se as dependências de áudio e vídeo estão instaladas no Python que abriu o painel."
            elif "orçamento" in msg.lower() or "limite" in msg.lower():
                reason = "O limite local de consumo foi atingido."
            elif "API" in self.stage:
                reason = "A chamada não produziu uma resposta utilizável. Confira a conexão e o acesso à API."
            else:
                reason = "Confira as mídias, os modelos restaurados e as dependências indicadas no README."
            with self.lock:
                self.error = self.stage + ". " + reason
        finally:
            with self.lock:
                self.running = False

    def view(self):
        with self.lock:
            return self.running, self.stage, self.error, self.case, self.token


def form_html(token):
    def options(values, selected):
        return "".join(
            f'<option value="{file}"{" selected" if file == selected else ""}>{name} · {file}</option>'
            for file, name in values.items()
        )

    missing = missing_files(ROOT, "novo-03.wav", "montagem_test.mp4")
    notice = (
        (
            "<p class='note'>Confira o download do repositório para a seleção inicial. "
            "Arquivos ausentes: " + ", ".join(map(escape, missing)) + ".</p>"
        )
        if missing
        else ""
    )
    return f"""<section class="entry"><h2>Nova consulta</h2>{notice}
<form action="/processar" method="post" autocomplete="off">
<input name="token" type="hidden" value="{escape(token)}">
<label>Gravação de voz<select name="audio">{options(WAVS, "novo-03.wav")}</select></label>
<audio id="audio-preview" controls preload="metadata" src="/midia/audio/novo-03.wav"></audio>
<label>Vídeo cirúrgico<select name="video">{options(VIDEOS, "montagem_test.mp4")}</select></label>
<video id="video-preview" controls preload="metadata" src="/midia/video/montagem_test.mp4"></video>
<label>Chave da API OpenAI<input type="password" name="chave" required autocomplete="off" spellcheck="false" maxlength="504" placeholder="sk-…"></label>
<p>Ao processar, o sistema envia o áudio sintético à OpenAI e analisa a transcrição em uma segunda chamada paga. A chave vale apenas para esta execução. O vídeo é analisado neste computador.</p>
<button type="submit">Processar consulta</button></form></section>"""


def evidence_html(result):
    if "consulta" not in result:
        return ""
    c = result["consulta"]
    sources = {s["modalidade"]: s for s in result["fontes"]}
    video, text = sources["video"], sources["texto_openai"]
    voice = c["caracteristicas"]
    events = (
        ", ".join(f"{e['inicio_s']:g} a {e['fim_s']:g} s" for e in video["eventos"])
        or "nenhum intervalo"
    )
    mentions = "".join(
        f"<li>{escape(m['termo'])} · {escape(m['estado'])} · {escape(m['contexto'])}<br><q>{escape(m['evidencia'])}</q></li>"
        for m in text["mencoes"]
    )
    rows = []
    for modality in ["sinais_vitais", "movimentacao", "prescricoes"]:
        for event in sources[modality]["eventos"]:
            if "campo" in event:
                rows.append(
                    f"<li>{escape(event['campo'])} · {event['valor']:g} (mediana anterior {sources[modality]['referencias'][event['campo']]['mediana']:g})</li>"
                )
            else:
                rows.append("<li>Prescrição · " + escape(", ".join(event["motivos"])) + "</li>")
    return f"""<details class="findings"><summary>Ver processamento do caso</summary>
<h3>Voz · {escape(c["audio"])}</h3><audio controls preload="metadata" src="/midia/audio/{escape(c["audio"])}"></audio><p>{voice["duracao"]:.1f} s de áudio · {voice["proporcao_pausas"]:.1%} de pausas. Transcrição local do Whisper:</p><blockquote>{escape(c["transcricao_local"])}</blockquote>
<h3>Relato da consulta · OpenAI</h3><p>Transcrição recebida de {escape(c["modelo_transcricao"])}</p><blockquote>{escape(c["transcricao_nuvem"])}</blockquote>
<p>Análise por {escape(c["modelo_texto"])} · sentimento {escape(text["sentimento"])} · custo estimado das duas chamadas US$ {c["custo_estimado_usd"]:.6f}</p><ul>{mentions or "<li>Nenhuma menção extraída.</li>"}</ul>
<h3>Vídeo · {escape(c["video"])}</h3><video controls preload="metadata" src="/midia/video/{escape(c["video"])}"></video><p>{video["estatisticas"]["quadros_analisados"]} quadros analisados. Intervalos sinalizados: {events}.</p>
<h3>Observações sintéticas</h3><p>Referência de {c["amostras_referencia"]} observações. Alterações identificadas:</p><ul>{"".join(rows)}</ul></details>"""


def running_html(processing):
    return f"""<section class="entry" id="processing"><h2>Consulta em processamento</h2>
<p id="stage" role="status">{escape(processing.stage)}</p>
<label>Áudio selecionado</label><audio controls preload="metadata" src="/midia/audio/{processing.wav}"></audio>
<p id="video-progress">Aguardando a análise dos quadros do vídeo.</p>
<progress id="video-bar" max="100" value="0" aria-label="Quadros analisados"></progress>
<img id="live-frame" alt="Quadro do vídeo analisado pelo detector" hidden>
<p id="connection" role="status"></p></section>"""
