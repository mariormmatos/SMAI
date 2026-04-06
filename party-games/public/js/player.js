// Player-specific logic
const PlayerController = (() => {
  let timerInterval = null;
  let _currentPhase = null;    // Track server phase locally
  let _currentRound = 0;       // Track server round locally
  let _endTime = null;         // Server-authoritative end time
  let _totalSeconds = null;    // Original duration for % calculation

  function init() {
    SocketClient.on('game_started', ({ game }) => {
      if (App.state.isHost) return;
      App.state.game = game;
    });

    SocketClient.on('round_start', (data) => {
      if (App.state.isHost) return;
      // Update server time offset
      if (data.serverTime) SocketClient.updateServerOffset(data.serverTime);
      App.state.round = data.round;
      _currentPhase = 'playing';
      _currentRound = data.round;
      if (data.gameType) App.state.game = data.gameType;
      renderPlayerRound(data);
    });

    SocketClient.on('voting_start', (data) => {
      if (App.state.isHost) return;
      _currentPhase = 'vote';
      renderVotingPhase(data);
    });

    // ── Kahoot-style sync handler ──
    // Every 2s the server pushes authoritative state. If this client is on
    // the wrong screen, force-navigate to the correct one.
    SocketClient.on('sync_state', (data) => {
      if (App.state.isHost) return;
      if (!App.state.sessionId) return;

      // Update server time offset
      if (data.serverTime) SocketClient.updateServerOffset(data.serverTime);

      const activeScreen = document.querySelector('.screen.active')?.id;

      // Phase: playing → client should be on screen-round
      if (data.phase === 'playing' && data.roundData) {
        const shouldBeOnRound = activeScreen === 'screen-round';
        const roundChanged = data.round !== _currentRound;

        if (!shouldBeOnRound || roundChanged) {
          // Client is desynced — force render the current round
          console.log(`[sync] Force-navigating to round ${data.round} (was on ${activeScreen}, round ${_currentRound})`);
          App.state.round = data.round;
          _currentRound = data.round;
          _currentPhase = data.subPhase || 'playing';
          if (data.game) App.state.game = data.game;

          if (data.subPhase === 'vote' && data.voteData) {
            renderVotingPhase({ ...data.voteData, phase: 'vote' });
          } else {
            renderPlayerRound(data.roundData);
          }
        } else {
          // Client is on the right screen — just re-sync the timer
          if (data.endTime) {
            resyncTimer(data.endTime, data.roundData?.timeLimit || _totalSeconds);
          }
        }
      }

      // Phase: round_result → client should be on screen-round-result
      if (data.phase === 'round_result') {
        if (activeScreen !== 'screen-round-result') {
          console.log(`[sync] Force-navigating to round_result (was on ${activeScreen})`);
          _currentPhase = 'round_result';
          if (data.resultData) {
            // Trigger the same flow as round_end
            const scores = data.resultData.scores || [];
            App.state.scores = scores;
            const gameModule = getGameModule(App.state.game);
            if (gameModule && gameModule.onRoundEnd) {
              gameModule.onRoundEnd(data.resultData, false);
            }
            App.renderScoreboard('scoreboard-list', scores, data.resultData.deltas);
            const hostNext = document.getElementById('host-next-btn');
            if (hostNext) hostNext.style.display = 'none';
            App.showScreen('screen-round-result');
          }
        }
      }

      // Phase: final → client should be on screen-final
      if (data.phase === 'final') {
        if (activeScreen !== 'screen-final') {
          console.log(`[sync] Force-navigating to final screen`);
          // The game_end event should have already handled this,
          // but as a safety net, navigate there
          App.showScreen('screen-final');
        }
      }
    });
  }

  function renderPlayerRound(data) {
    clearTimer();
    const roundNum = document.getElementById('round-number');
    if (roundNum) roundNum.textContent = `Ronda ${data.round}`;

    const content = document.getElementById('round-content');
    if (!content) return;

    // Delegate to game module
    const mod = getGameModule(App.state.game);
    if (mod && mod.renderPlayerRound) {
      mod.renderPlayerRound(data, content, App.state.playerName);
    } else {
      content.innerHTML = '<div class="info-box">A carregar...</div>';
    }

    // Start timer using server endTime if available, fallback to duration
    if (data.endTime) {
      startServerTimer(data.endTime, data.timeLimit);
    } else if (data.timeLimit) {
      startServerTimer(Date.now() + data.timeLimit * 1000, data.timeLimit);
    }

    App.showScreen('screen-round');
  }

  function renderVotingPhase(data) {
    clearTimer();
    const content = document.getElementById('round-content');
    if (!content) return;

    const mod = getGameModule(App.state.game);
    if (mod && mod.renderVoting) {
      mod.renderVoting(data, content, App.state.playerName);
    }

    if (data.timeLimit) {
      startServerTimer(Date.now() + data.timeLimit * 1000, data.timeLimit);
    }

    App.showScreen('screen-round');
  }

  // ── Server-driven timer (Kahoot model) ──
  // Instead of counting down from a duration, we calculate remaining time
  // from the server's absolute endTime. This means all clients show the
  // same remaining time regardless of when they received the event.
  function startServerTimer(endTime, totalSec) {
    clearTimer();
    _endTime = endTime;
    _totalSeconds = totalSec || 20;

    function update() {
      const remainMs = SocketClient.getRemainingMs(_endTime);
      if (remainMs === null) return;
      const remaining = Math.ceil(remainMs / 1000);

      const timerEl = document.getElementById('round-timer');
      const barFill = document.querySelector('.timer-bar-fill');

      if (timerEl) {
        timerEl.textContent = remaining;
        timerEl.className = 'round-timer';
        if (remaining <= 5) timerEl.classList.add('urgent');
        else if (remaining <= 10) timerEl.classList.add('warning');
      }
      if (barFill) {
        const pct = (remaining / _totalSeconds) * 100;
        barFill.style.width = Math.max(0, pct) + '%';
        if (pct <= 30) barFill.style.background = '#f85149';
        else if (pct <= 60) barFill.style.background = '#d29922';
        else barFill.style.background = '#7c3aed';
      }

      if (remaining <= 0) clearTimer();
    }

    update();
    timerInterval = setInterval(update, 250); // 4x/s for smoother bar
  }

  // Re-sync timer from heartbeat without re-rendering the whole UI
  function resyncTimer(endTime, totalSec) {
    _endTime = endTime;
    if (totalSec) _totalSeconds = totalSec;
  }

  function clearTimer() {
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
    _endTime = null;
    const timerEl = document.getElementById('round-timer');
    if (timerEl) timerEl.textContent = '';
  }

  function getGameModule(game) {
    return (App.GameModules && App.GameModules[game]) || null;
  }

  return { init, clearTimer };
})();
