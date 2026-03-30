// Main app controller: screen router + global state

const App = (() => {
  const state = {
    role: null,         // 'host' | 'player'
    sessionId: null,
    playerName: null,
    game: null,
    isHost: false,
    round: 0,
    scores: [],
  };

  const GAME_NAMES = {
    quiz: 'Quiz Rápido',
    bluff: 'Verdade ou Mentira',
    creative: 'Artista Relâmpago',
    mission: 'Missão ou Castigo',
    consensus: 'Mente Coletiva',
  };

  function showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    const target = document.getElementById(id);
    if (target) {
      target.classList.add('active');
      target.scrollTop = 0;
    }
  }

  function gameName(key) {
    return GAME_NAMES[key] || key;
  }

  function renderScoreboard(listId, scores, deltas) {
    const ul = document.getElementById(listId);
    if (!ul) return;
    ul.innerHTML = '';
    const deltaMap = {};
    if (deltas) deltas.forEach(d => { deltaMap[d.name] = d.delta; });
    scores.forEach((p, i) => {
      const li = document.createElement('li');
      const rank = ['🥇', '🥈', '🥉'][i] || `${i + 1}.`;
      const delta = deltaMap[p.name];
      const deltaHtml = delta != null
        ? `<span class="score-delta ${delta > 0 ? 'positive' : 'zero'}">${delta > 0 ? '+' + delta : delta}</span>`
        : '';
      li.innerHTML = `
        <span class="score-rank">${rank}</span>
        <span class="score-name">${esc(p.name)}</span>
        ${deltaHtml}
        <span class="score-pts">${p.score} pts</span>
      `;
      ul.appendChild(li);
    });
  }

  function esc(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function init() {
    SocketClient.connect();
    setupHomeScreen();
    setupJoinScreen();
    setupLobbyScreen();
    setupGameSelectScreen();
    setupRoundResultScreen();
    setupFinalScreen();
    HostController.init();
    PlayerController.init();

    // Handle /join?s=CODE URL on page load
    const params = new URLSearchParams(window.location.search);
    const sessionCode = params.get('s');
    if (sessionCode) {
      showScreen('screen-join');
      const input = document.getElementById('input-session-id');
      if (input) input.value = sessionCode.toUpperCase();
      document.getElementById('input-player-name')?.focus();
    } else {
      showScreen('screen-home');
    }
  }

  function setupHomeScreen() {
    document.getElementById('btn-host').addEventListener('click', () => {
      state.role = 'host';
      state.isHost = true;
      showScreen('screen-game-select');
    });
    document.getElementById('btn-player').addEventListener('click', () => {
      state.role = 'player';
      state.isHost = false;
      showScreen('screen-join');
    });
  }

  function setupJoinScreen() {
    document.getElementById('back-from-join').addEventListener('click', () => {
      showScreen('screen-home');
    });
    document.getElementById('btn-join').addEventListener('click', doJoin);
    document.getElementById('input-player-name').addEventListener('keydown', e => {
      if (e.key === 'Enter') doJoin();
    });
  }

  function doJoin() {
    const sessionId = document.getElementById('input-session-id').value.trim().toUpperCase();
    const name = document.getElementById('input-player-name').value.trim();
    const errorEl = document.getElementById('join-error');
    errorEl.textContent = '';

    if (!sessionId || sessionId.length !== 6) {
      errorEl.textContent = 'Introduz o código de 6 letras da sessão.';
      return;
    }
    if (!name) {
      errorEl.textContent = 'Introduz o teu nome.';
      return;
    }

    state.sessionId = sessionId;
    state.playerName = name;
    SocketClient.emit('join_session', { sessionId, name });
  }

  function setupGameSelectScreen() {
    document.getElementById('back-from-game-select').addEventListener('click', () => {
      showScreen('screen-home');
    });
    document.querySelectorAll('.game-card').forEach(card => {
      card.addEventListener('click', () => {
        const game = card.dataset.game;
        state.game = game;
        SocketClient.emit('create_session', { game });
      });
    });
  }

  function setupLobbyScreen() {
    document.getElementById('btn-start').addEventListener('click', () => {
      SocketClient.emit('start_game', {});
    });
  }

  function setupRoundResultScreen() {
    document.getElementById('btn-next-round').addEventListener('click', () => {
      SocketClient.emit('next_round', {});
    });
  }

  function setupFinalScreen() {
    document.getElementById('btn-play-again').addEventListener('click', () => {
      // Reset state and go home
      state.sessionId = null;
      state.playerName = null;
      state.game = null;
      state.round = 0;
      state.scores = [];
      showScreen('screen-home');
    });
  }

  // Global socket listeners
  SocketClient.on('session_created', ({ sessionId }) => {
    state.sessionId = sessionId;
    document.getElementById('lobby-session-id').textContent = sessionId;
    document.getElementById('lobby-game-name').textContent = gameName(state.game);
    const joinUrl = `${window.location.origin}/join?s=${sessionId}`;
    QRHelper.render('qr-container', joinUrl);
    showScreen('screen-lobby');
  });

  SocketClient.on('player_joined', ({ players }) => {
    state.scores = players;
    const list = document.getElementById('player-list');
    const count = document.getElementById('player-count');
    if (list) {
      list.innerHTML = players.map(p =>
        `<li>${esc(p.name)}</li>`
      ).join('');
    }
    if (count) count.textContent = players.length;
    const startBtn = document.getElementById('btn-start');
    const hint = document.getElementById('start-hint');
    if (startBtn) {
      startBtn.disabled = players.length < 1;
    }
    if (hint) {
      hint.textContent = players.length >= 1
        ? `${players.length} jogador${players.length > 1 ? 'es' : ''} pronto${players.length > 1 ? 's' : ''}!`
        : 'Precisas de pelo menos 1 jogador';
    }
    // Update waiting screen player list
    const wp = document.getElementById('waiting-players');
    if (wp) {
      wp.textContent = players.map(p => p.name).join(', ');
    }
  });

  SocketClient.on('join_success', ({ sessionId, name, game }) => {
    state.sessionId = sessionId;
    state.playerName = name;
    state.game = game;
    const badge = document.getElementById('waiting-game-badge');
    if (badge) badge.textContent = gameName(game);
    showScreen('screen-waiting');
  });

  SocketClient.on('join_error', ({ message }) => {
    const errorEl = document.getElementById('join-error');
    if (errorEl) errorEl.textContent = message;
  });

  SocketClient.on('start_error', ({ message }) => {
    alert(message);
  });

  SocketClient.on('round_end', ({ scores, deltas, ...roundResult }) => {
    state.scores = scores;
    const title = document.getElementById('result-title');
    if (title) title.textContent = 'Resultado da Ronda';

    // Let game module render result content
    const gameModule = GameModules[state.game];
    if (gameModule && gameModule.onRoundEnd) {
      gameModule.onRoundEnd(roundResult, state.isHost);
    }

    renderScoreboard('scoreboard-list', scores, deltas);
    const hostNext = document.getElementById('host-next-btn');
    if (hostNext) hostNext.style.display = state.isHost ? 'block' : 'none';
    showScreen('screen-round-result');
  });

  SocketClient.on('game_end', ({ finalScores }) => {
    renderFinalPodium(finalScores);
    showScreen('screen-final');
  });

  function renderFinalPodium(scores) {
    const top3 = document.getElementById('podium-top3');
    const ranking = document.getElementById('final-ranking');
    if (!top3 || !ranking) return;

    const medals = ['🥇', '🥈', '🥉'];
    const classes = ['first', 'second', 'third'];

    top3.innerHTML = '';
    scores.slice(0, 3).forEach((p, i) => {
      const div = document.createElement('div');
      div.className = `podium-place ${classes[i]}`;
      div.innerHTML = `
        <div class="podium-medal">${medals[i]}</div>
        <div class="podium-name">${esc(p.name)}</div>
        <div class="podium-score">${p.score} pts</div>
        <div class="podium-bar"></div>
      `;
      top3.appendChild(div);
    });

    ranking.innerHTML = '';
    scores.slice(3).forEach((p, i) => {
      const li = document.createElement('li');
      li.innerHTML = `
        <span class="final-rank-num">${i + 4}.</span>
        <span class="final-rank-name">${esc(p.name)}</span>
        <span class="final-rank-pts">${p.score} pts</span>
      `;
      ranking.appendChild(li);
    });
  }

  // Game modules registry (filled by each game JS file)
  const GameModules = {};

  function registerGame(name, module) {
    GameModules[name] = module;
  }

  return { init, showScreen, state, gameName, renderScoreboard, registerGame, esc };
})();

document.addEventListener('DOMContentLoaded', App.init);
