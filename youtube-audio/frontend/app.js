// ─── Config ──────────────────────────────────────────────────────────────────
// Replace with your Railway backend URL after deploying
const BACKEND_URL = (window.BACKEND_URL || "").replace(/\/$/, "");

// ─── State ────────────────────────────────────────────────────────────────────
let queue = loadQueue();      // [{ url, title, thumbnail, duration, uploader }]
let currentIndex = -1;
let isSeeking = false;

// ─── DOM refs ─────────────────────────────────────────────────────────────────
const urlInput     = document.getElementById("url-input");
const loadBtn      = document.getElementById("load-btn");
const spinner      = document.getElementById("spinner");
const errorMsg     = document.getElementById("error-msg");
const playerSection = document.getElementById("player-section");
const thumbnail    = document.getElementById("thumbnail");
const titleEl      = document.getElementById("title");
const uploaderEl   = document.getElementById("uploader");
const progressBar  = document.getElementById("progress-bar");
const currentTimeEl = document.getElementById("current-time");
const totalTimeEl  = document.getElementById("total-time");
const playBtn      = document.getElementById("play-btn");
const skipBackBtn  = document.getElementById("skip-back-btn");
const skipFwdBtn   = document.getElementById("skip-fwd-btn");
const prevBtn      = document.getElementById("prev-btn");
const nextBtn      = document.getElementById("next-btn");
const speedBtns    = document.querySelectorAll(".speed-btn");
const queueList    = document.getElementById("queue-list");
const clearQueueBtn = document.getElementById("clear-queue-btn");
const audio        = document.getElementById("audio");

// ─── Persistence ──────────────────────────────────────────────────────────────
function loadQueue() {
  try { return JSON.parse(localStorage.getItem("yt-audio-queue") || "[]"); }
  catch { return []; }
}

function saveQueue() {
  localStorage.setItem("yt-audio-queue", JSON.stringify(queue));
}

// ─── Utilities ────────────────────────────────────────────────────────────────
function formatTime(sec) {
  if (!isFinite(sec) || sec < 0) return "0:00";
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function showError(msg) {
  errorMsg.textContent = msg;
  errorMsg.classList.add("visible");
}

function clearError() {
  errorMsg.classList.remove("visible");
}

function setLoading(on) {
  loadBtn.disabled = on;
  spinner.classList.toggle("visible", on);
}

// ─── Queue rendering ──────────────────────────────────────────────────────────
function renderQueue() {
  queueList.innerHTML = "";
  if (queue.length === 0) {
    queueList.innerHTML = '<li class="empty-queue">A fila está vazia. Adiciona um link acima.</li>';
    return;
  }
  queue.forEach((item, i) => {
    const li = document.createElement("li");
    li.className = "queue-item" + (i === currentIndex ? " active" : "");
    li.dataset.index = i;
    li.innerHTML = `
      <img class="queue-thumb" src="${item.thumbnail}" alt="" loading="lazy">
      <div class="queue-meta">
        <div class="queue-title">${item.title}</div>
        <div class="queue-uploader">${item.uploader}</div>
      </div>
      <button class="queue-remove" data-index="${i}" title="Remover">
        <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>`;
    li.addEventListener("click", (e) => {
      if (e.target.closest(".queue-remove")) return;
      playIndex(i);
    });
    li.querySelector(".queue-remove").addEventListener("click", (e) => {
      e.stopPropagation();
      removeFromQueue(i);
    });
    queueList.appendChild(li);
  });
}

function removeFromQueue(i) {
  queue.splice(i, 1);
  saveQueue();
  if (currentIndex === i) {
    // Stop current if removed
    audio.pause();
    playerSection.classList.remove("visible");
    currentIndex = -1;
  } else if (currentIndex > i) {
    currentIndex--;
  }
  renderQueue();
}

clearQueueBtn.addEventListener("click", () => {
  if (!queue.length) return;
  audio.pause();
  queue = [];
  currentIndex = -1;
  playerSection.classList.remove("visible");
  saveQueue();
  renderQueue();
});

// ─── Load video info ──────────────────────────────────────────────────────────
async function fetchInfo(url) {
  const res = await fetch(`${BACKEND_URL}/info?url=${encodeURIComponent(url)}`);
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || "Erro ao obter informação do vídeo");
  }
  return res.json();
}

loadBtn.addEventListener("click", handleLoad);
urlInput.addEventListener("keydown", (e) => { if (e.key === "Enter") handleLoad(); });

async function handleLoad() {
  const url = urlInput.value.trim();
  if (!url) return;
  clearError();

  if (!BACKEND_URL) {
    showError("Backend URL não configurado. Edita o ficheiro config.js com o URL do teu servidor Railway.");
    return;
  }

  setLoading(true);
  try {
    const info = await fetchInfo(url);
    const item = { url, ...info };

    // Avoid duplicates
    if (!queue.find((q) => q.url === url)) {
      queue.push(item);
      saveQueue();
    }

    renderQueue();
    urlInput.value = "";

    // Auto-play if nothing is playing
    if (currentIndex === -1) {
      playIndex(queue.length - 1);
    }
  } catch (err) {
    showError(err.message);
  } finally {
    setLoading(false);
  }
}

// ─── Playback ─────────────────────────────────────────────────────────────────
function playIndex(i) {
  if (i < 0 || i >= queue.length) return;
  currentIndex = i;
  const item = queue[i];

  // Set audio source to the proxy stream endpoint
  audio.src = `${BACKEND_URL}/stream?url=${encodeURIComponent(item.url)}`;
  audio.load();
  audio.play().catch(() => {});

  // Update player UI
  titleEl.textContent = item.title;
  uploaderEl.textContent = item.uploader;
  thumbnail.src = item.thumbnail;
  totalTimeEl.textContent = formatTime(item.duration);
  progressBar.value = 0;
  progressBar.style.setProperty("--progress", "0%");
  playerSection.classList.add("visible");

  updatePlayBtn();
  renderQueue();
  updateMediaSession(item);
}

function updatePlayBtn() {
  const paused = audio.paused;
  playBtn.innerHTML = paused
    ? `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>`
    : `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>`;
}

playBtn.addEventListener("click", () => {
  if (audio.paused) audio.play();
  else audio.pause();
});

skipBackBtn.addEventListener("click", () => { audio.currentTime = Math.max(0, audio.currentTime - 15); });
skipFwdBtn.addEventListener("click",  () => { audio.currentTime = audio.currentTime + 30; });
prevBtn.addEventListener("click", () => { if (currentIndex > 0) playIndex(currentIndex - 1); });
nextBtn.addEventListener("click", () => { if (currentIndex < queue.length - 1) playIndex(currentIndex + 1); });

audio.addEventListener("play",  updatePlayBtn);
audio.addEventListener("pause", updatePlayBtn);

audio.addEventListener("timeupdate", () => {
  if (isSeeking || !isFinite(audio.duration)) return;
  const pct = (audio.currentTime / audio.duration) * 100;
  progressBar.value = pct;
  progressBar.style.setProperty("--progress", pct + "%");
  currentTimeEl.textContent = formatTime(audio.currentTime);

  if ("mediaSession" in navigator) {
    navigator.mediaSession.setPositionState({
      duration: audio.duration,
      position: audio.currentTime,
      playbackRate: audio.playbackRate,
    });
  }
});

audio.addEventListener("ended", () => {
  if (currentIndex < queue.length - 1) playIndex(currentIndex + 1);
});

progressBar.addEventListener("mousedown", () => { isSeeking = true; });
progressBar.addEventListener("touchstart", () => { isSeeking = true; });
progressBar.addEventListener("input", () => {
  const pct = progressBar.value;
  progressBar.style.setProperty("--progress", pct + "%");
  currentTimeEl.textContent = formatTime((pct / 100) * (audio.duration || 0));
});
progressBar.addEventListener("change", () => {
  if (isFinite(audio.duration)) {
    audio.currentTime = (progressBar.value / 100) * audio.duration;
  }
  isSeeking = false;
});

// ─── Speed ────────────────────────────────────────────────────────────────────
speedBtns.forEach((btn) => {
  btn.addEventListener("click", () => {
    speedBtns.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    audio.playbackRate = parseFloat(btn.dataset.speed);
  });
});

// ─── Media Session API (lock screen controls) ─────────────────────────────────
function updateMediaSession(item) {
  if (!("mediaSession" in navigator)) return;
  navigator.mediaSession.metadata = new MediaMetadata({
    title: item.title,
    artist: item.uploader,
    artwork: [{ src: item.thumbnail, sizes: "256x256", type: "image/jpeg" }],
  });
  navigator.mediaSession.setActionHandler("play",          () => audio.play());
  navigator.mediaSession.setActionHandler("pause",         () => audio.pause());
  navigator.mediaSession.setActionHandler("seekbackward",  () => { audio.currentTime -= 15; });
  navigator.mediaSession.setActionHandler("seekforward",   () => { audio.currentTime += 30; });
  navigator.mediaSession.setActionHandler("previoustrack", () => { if (currentIndex > 0) playIndex(currentIndex - 1); });
  navigator.mediaSession.setActionHandler("nexttrack",     () => { if (currentIndex < queue.length - 1) playIndex(currentIndex + 1); });
}

// ─── Service Worker ───────────────────────────────────────────────────────────
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").catch(() => {});
}

// ─── Init ─────────────────────────────────────────────────────────────────────
renderQueue();

// Restore last playing item on reload (paused)
if (queue.length > 0) {
  const lastIndex = 0;
  const item = queue[lastIndex];
  titleEl.textContent = item.title;
  uploaderEl.textContent = item.uploader;
  thumbnail.src = item.thumbnail;
  totalTimeEl.textContent = formatTime(item.duration);
  playerSection.classList.add("visible");
  currentIndex = lastIndex;
  renderQueue();
}
