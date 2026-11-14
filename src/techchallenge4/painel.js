"use strict";

const audioChoice = document.querySelector('select[name="audio"]');
const videoChoice = document.querySelector('select[name="video"]');

if (audioChoice) {
  audioChoice.addEventListener("change", () => {
    const player = document.getElementById("audio-preview");
    player.src = "/midia/audio/" + encodeURIComponent(audioChoice.value);
    player.load();
  });
  videoChoice.addEventListener("change", () => {
    const player = document.getElementById("video-preview");
    player.src = "/midia/video/" + encodeURIComponent(videoChoice.value);
    player.load();
  });
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
