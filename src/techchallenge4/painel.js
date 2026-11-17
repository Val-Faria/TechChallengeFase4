"use strict";

const audioChoice = document.querySelector('select[name="audio"]');
const videoChoice = document.querySelector('select[name="video"]');

if (audioChoice) {
  for (const [kind, choice] of [["audio", audioChoice], ["video", videoChoice]]) {
    const upload = document.querySelector('input[name="' + kind + '_upload"]');
    const label = document.getElementById(kind + "-upload-label");
    const player = document.getElementById(kind + "-preview");
    const message = document.getElementById(kind + "-preview-status");
    player.addEventListener("error", () => {
      if (player.getAttribute("src")) {
        message.textContent = "Prévia indisponível neste navegador. O arquivo será verificado durante o processamento.";
      }
    });
    player.addEventListener("loadedmetadata", () => { message.textContent = ""; });
    let localUrl = null;
    function releasePreview() {
      if (localUrl) URL.revokeObjectURL(localUrl);
      localUrl = null;
    }
    function updatePreview() {
      message.textContent = "";
      releasePreview();
      if (choice.value === "__upload__") {
        const file = upload.files[0];
        if (file) {
          localUrl = URL.createObjectURL(file);
          player.src = localUrl;
          player.hidden = false;
        } else {
          player.removeAttribute("src");
          player.hidden = true;
        }
      } else {
        player.src = "/midia/" + kind + "/" + encodeURIComponent(choice.value);
        player.hidden = false;
      }
      player.load();
    }
    choice.addEventListener("change", () => {
      const fromDevice = choice.value === "__upload__";
      label.hidden = !fromDevice;
      upload.disabled = !fromDevice;
      upload.required = fromDevice;
      updatePreview();
    });
    upload.addEventListener("change", updatePreview);
    window.addEventListener("pagehide", releasePreview);
  }
}

if (document.getElementById("processing")) {
  let previousFrame = null;
  async function update() {
    try {
      const response = await fetch("/status", {cache: "no-store"});
      if (!response.ok) throw new Error("status");
      const state = await response.json();
      if (!state.running) {
        window.location.replace("/");
        return;
      }
      document.getElementById("stage").textContent = state.stage;
      document.getElementById("connection").textContent = "";
      if (state.video) {
        const video = state.video;
        document.getElementById("video-progress").textContent =
          video.processed + " de " + video.total + " quadros · posição " +
          video.seconds.toFixed(1) + " s";
        const bar = document.getElementById("video-bar");
        bar.max = video.total;
        bar.value = video.processed;
        if (state.frame !== previousFrame) {
          const frame = document.getElementById("live-frame");
          frame.src = "/quadro.jpg?frame=" + state.frame;
          frame.hidden = false;
          previousFrame = state.frame;
        }
      }
    } catch {
      document.getElementById("connection").textContent =
        "Aguardando conexão com o painel. A consulta continua no servidor.";
    }
    setTimeout(update, 700);
  }
  update();
}
