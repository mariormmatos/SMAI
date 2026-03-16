// Player-specific logic
const PlayerController = (() => {
  let timerInterval = null;

  function init() {
    SocketClient.on('game_started', ({ game }) => {
      if (App.state.isHost) return;
      App.state.game = game;
    });

    SocketClient.on('round_start', (data) => {
      if (App.state.isHost) return;
      App.state.round = data.round;
      renderPlayerRound(data);
    });

    SocketClient.on('voting_start', (data) => {
      if (App.state.isHost) return;
      renderVotingPhase(data);
    });
  }

  function renderPlayerRound(data) {
    clearTimer();

    const roundNum = document.getElementById('round-number');
    if (roundNum) roundNum.textContent = `Ronda ${data.round}`;

    const content = document.getElementById('round-content');
    if (!content) return;

    // Delegate to game module
    const gameModule = window[`Game_${data.gameType || App.state.game}`];
    const mod = getGameModule(App.state.game);
    if (mod && mod.renderPlayerRound) {
      mod.renderPlayerRound(data, content, App.state.playerName);
    } else {
      content.innerHTML = '<div class="info-box">A carregar...</div>';
    }

    // Start timer if provided
    if (data.timeLimit) {
      startTimer(data.timeLimit);
    }

    App.showScreen('screen-round');
  }

  function renderVotingPhase(data) {
    const content = document.getElementById('round-content');
    if (!content) return;
    const mod = getGameModule(App.state.game);
    if (mod && mod.renderVoting) {
      mod.renderVoting(data, content, App.state.playerName);
    }
    if (data.timeLimit) {
      clearTimer();
      startTimer(data.timeLimit);
    }
  }

  function startTimer(seconds) {
    const timerEl = document.getElementById('round-timer');
    const barFill = document.querySelector('.timer-bar-fill');
    let remaining = seconds;

    function update() {
      if (timerEl) {
        timerEl.textContent = remaining;
        timerEl.className = 'round-timer';
        if (remaining <= 5) timerEl.classList.add('urgent');
        else if (remaining <= 10) timerEl.classList.add('warning');
      }
      if (barFill) {
        const pct = (remaining / seconds) * 100;
        barFill.style.width = pct + '%';
        if (pct <= 30) barFill.style.background = '#f85149';
        else if (pct <= 60) barFill.style.background = '#d29922';
        else barFill.style.background = '#7c3aed';
      }
    }

    update();
    timerInterval = setInterval(() => {
      remaining--;
      update();
      if (remaining <= 0) clearTimer();
    }, 1000);
  }

  function clearTimer() {
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
    const timerEl = document.getElementById('round-timer');
    if (timerEl) timerEl.textContent = '';
  }

  function getGameModule(game) {
    const map = {
      quiz: typeof QuizGame !== 'undefined' ? QuizGame : null,
      bluff: typeof BluffGame !== 'undefined' ? BluffGame : null,
      creative: typeof CreativeGame !== 'undefined' ? CreativeGame : null,
      mission: typeof MissionGame !== 'undefined' ? MissionGame : null,
      consensus: typeof ConsensusGame !== 'undefined' ? ConsensusGame : null,
    };
    return map[game] || null;
  }

  return { init, clearTimer };
})();
