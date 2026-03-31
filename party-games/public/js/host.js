// Host-specific logic
const HostController = (() => {
  function init() {
    SocketClient.on('game_started', ({ game }) => {
      if (!App.state.isHost) return;
      App.state.game = game;
    });

    SocketClient.on('round_start', (data) => {
      if (!App.state.isHost) return;
      App.state.round = data.round;
      if (data.gameType) App.state.game = data.gameType;
      renderHostRound(data);
    });

    SocketClient.on('all_answered', ({ count, total }) => {
      if (!App.state.isHost) return;
      const el = document.getElementById('answers-progress');
      if (el) el.textContent = `${count}/${total} jogadores responderam`;
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

    const forceBtn = document.getElementById('btn-force-next');
    if (forceBtn) {
      forceBtn.onclick = () => SocketClient.emit('next_round', {});
    }
  }

  return { init };
})();
