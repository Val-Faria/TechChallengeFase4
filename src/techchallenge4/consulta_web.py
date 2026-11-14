"""Formulário, acompanhamento da execução e evidências de uma consulta."""

from html import escape
from threading import Lock, Thread
from secrets import token_urlsafe
import re

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
                "Os arquivos da seleção estão ausentes. Extraia artefatos_privados.zip na raiz do projeto."
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
        Thread(target=self._run, args=(wav, mp4, key), daemon=True).start()

    def _progress(self, stage):
        with self.lock:
            self.stage = stage

    def _run(self, wav, mp4, key):
        try:
            case = process_case(ROOT, self.store, wav, mp4, key, self._progress)
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
            "<p class='note'>Para a seleção inicial, extraia artefatos_privados.zip na raiz do projeto. "
            "Arquivos ausentes: " + ", ".join(map(escape, missing)) + ".</p>"
        )
        if missing
        else ""
    )
    return f"""<section class="entry"><h2>Nova consulta</h2>{notice}
<form action="/processar" method="post" autocomplete="off">
<input name="token" type="hidden" value="{escape(token)}">
<label>Gravação de voz<select name="audio">{options(WAVS, "novo-03.wav")}</select></label>
<label>Vídeo cirúrgico<select name="video">{options(VIDEOS, "montagem_test.mp4")}</select></label>
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
<h3>Voz · {escape(c["audio"])}</h3><p>{voice["duracao"]:.1f} s de áudio · {voice["proporcao_pausas"]:.1%} de pausas. Transcrição local do Whisper:</p><blockquote>{escape(c["transcricao_local"])}</blockquote>
<h3>Relato da consulta · OpenAI</h3><p>Transcrição recebida de {escape(c["modelo_transcricao"])}</p><blockquote>{escape(c["transcricao_nuvem"])}</blockquote>
<p>Análise por {escape(c["modelo_texto"])} · sentimento {escape(text["sentimento"])} · custo estimado das duas chamadas US$ {c["custo_estimado_usd"]:.6f}</p><ul>{mentions or "<li>Nenhuma menção extraída.</li>"}</ul>
<h3>Vídeo · {escape(c["video"])}</h3><p>{video["estatisticas"]["quadros_analisados"]} quadros analisados. Intervalos sinalizados: {events}.</p>
<h3>Observações sintéticas</h3><p>Referência de {c["amostras_referencia"]} observações. Alterações identificadas:</p><ul>{"".join(rows)}</ul></details>"""
