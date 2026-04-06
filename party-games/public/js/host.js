// Host-specific logic
const HostController = (() => {
  let hostTimerInterval = null;
  let _endTime = null;
  let _totalSeconds = null;
  let _currentRound = 0;

  function startHostServerTimer(endTime, totalSec) {
    clearHostTimer();
    _endTime = endTime;
    _totalSeconds = totalSec || 20;

    function update() {
      const remainMs = SocketClient.getRemainingMs(_endTime);
      if (remainMs === null) return;
      const remaining = Math.ceil(remainMs / 1000);
      const barFill = document.querySelector('#host-round-content .timer-bar-fill');
      if (barFill) {
        const pct = (remaining / _totalSeconds) * 100;
        barFill.style.width = Math.max(0, pct) + '%';
        barFill.style.background = pct <= 30 ? '#f85149' : pct <= 60 ? '#d29922' : '#7c3aed';
      }
      if (remaining <= 0) clearHostTimer();
    }
    update();
    hostTimerInterval = setInterval(update, 250);
  }

  function clearHostTimer() {
    if (hostTimerInterval) { clearInterval(hostTimerInterval); hostTimerInterval = null; }
    _endTime = null;
  }

  function init() {
    SocketClient.on('game_started', ({ game }) => {
      if (!App.state.isHost) return;
      App.state.game = game;
    });

    SocketClient.on('round_start', (data) => {
      if (!App.state.isHost) return;
      if (data.serverTime) SocketClient.updateServerOffset(data.serverTime);
      App.state.round = data.round;
      _currentRound = data.round;
      if (data.gameType) App.state.game = data.gameType;
      clearHostTimer();
      renderHostRound(data);
    });

    SocketClient.on('voting_start', (data) => {
      if (!App.state.isHost) return;
      const content = document.getElementById('host-round-content');
      if (!content) return;
      const gameModule = App.GameModules ? App.GameModules[App.state.game] : null;
      if (gameModule && gameModule.renderVoting) {
        gameModule.renderVoting(data, content, App.state.playerName || 'Anfitrião');
      }
      if (data.timeLimit) {
        startHostServerTimer(Date.now() + data.timeLimit * 1000, data.timeLimit);
      }
    });

    SocketClient.on('all_answered', ({ count, total }) => {
      if (!App.state.isHost) return;
      const el = document.getElementById('answers-progress');
      if (el) el.textContent = `${count}/${total} jogadores responderam`;
    });

    // ── Host sync handler ──
    SocketClient.on('sync_state', (data) => {
      if (!App.state.isHost) return;
      if (!App.state.sessionId) return;
      if (data.serverTime) SocketClient.updateServerOffset(data.serverTime);

      const activeScreen = document.querySelector('.screen.active')?.id;

      // Phase: playing → host should be on screen-host-round
      if (data.phase === 'playing' && data.roundData) {
        const shouldBeOnRound = activeScreen === 'screen-host-round';
        const roundChanged = data.round !== _currentRound;

        if (!shouldBeOnRound || roundChanged) {
          console.log(`[host-sync] Force-navigating to round ${data.round}`);
          App.state.round = data.round;
          _currentRound = data.round;
          if (data.game) App.state.game = data.game;
          renderHostRound(data.roundData);
        } else if (data.endTime) {
          // Just re-sync timer
          _endTime = data.endTime;
          if (data.roundData?.timeLimit) _totalSeconds = data.roundData.timeLimit;
        }
      }

      // Phase: round_result → host should be on screen-round-result
      if (data.phase === 'round_result' && activeScreen !== 'screen-round-result') {
        if (data.resultData) {
          console.log(`[host-sync] Force-navigating to round_result`);
          App.state.scores = data.resultData.scores || [];
          const gameModule = App.GameModules ? App.GameModules[App.state.game] : null;
          if (gameModule && gameModule.onRoundEnd) {
            gameModule.onRoundEnd(data.resultData, true);
          }
          App.renderScoreboard('scoreboard-list', data.resultData.scores, data.resultData.deltas);
          const hostNext = document.getElementById('host-next-btn');
          if (hostNext) hostNext.style.display = 'block';
          App.showScreen('screen-round-result');
        }
      }
    });
  }

  function renderHostRound(data) {
    const title = document.getElementById('host-round-title');
    if (title) title.textContent = `Ronda ${data.round}`;

    const content = document.getElementById('host-round-content');
    if (!content) return;

    const gameModule = App.GameModules ? App.GameModules[App.state.game] : null;
    // Host always plays as a participant — show interactive view
    if (gameModule && gameModule.renderPlayerRound) {
      gameModule.renderPlayerRound(data, content, App.state.playerName || 'Anfitrião');
    } else {
      content.innerHTML = `
        <div class="info-box">
          <div style="font-size: 24px; margin-bottom: 8px;">⏳</div>
          <div>Os jogadores estão a responder...</div>
          <div class="text-muted mt-8" id="answers-progress"></div>
        </div>
      `;
    }

    App.showScreen('screen-host-round');

    // Start server-driven timer
    if (data.endTime) {
      startHostServerTimer(data.endTime, data.timeLimit);
    } else if (data.timeLimit) {
      startHostServerTimer(Date.now() + data.timeLimit * 1000, data.timeLimit);
    }

    const forceBtn = document.getElementById('btn-force-next');
    if (forceBtn) {
      forceBtn.onclick = () => SocketClient.emit('next_round', {});
    }
  }

  return { init };
})();
