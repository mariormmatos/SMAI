// Missão ou Castigo — client-side UI
const MissionGame = (() => {
  let decided = false;
  let voted = false;

  function renderPlayerRound(data, container, myName) {
    decided = false;
    const isHotSeat = data.hotSeatName === myName;

    if (isHotSeat) {
      container.innerHTML = `
        <div class="timer-bar-wrap"><div class="timer-bar-fill" style="width:100%"></div></div>
        <div class="hot-seat-banner">🔥 A tua vez!</div>
        <div class="mission-card">
          <div class="mission-title">A tua missão, se escolheres aceitá-la:</div>
          <div class="mission-text">${App.esc(data.mission)}</div>
        </div>
        <div class="mission-accept-btns">
          <button class="btn-accept" id="btn-accept">✅ Aceito!</button>
          <button class="btn-refuse" id="btn-refuse">❌ Recuso</button>
        </div>
      `;
      // FIX: capture the container in closure so decide() uses the correct
      // element regardless of whether we're the host or a regular player.
      document.getElementById('btn-accept').addEventListener('click', () => decide('accept', container));
      document.getElementById('btn-refuse').addEventListener('click', () => decide('refuse', container));
    } else {
      container.innerHTML = `
        <div class="timer-bar-wrap"><div class="timer-bar-fill" style="width:100%"></div></div>
        <div class="info-box">
          <div style="font-size: 32px; margin-bottom: 8px;">🔥</div>
          <div style="font-weight: 600; font-size: 16px;">${App.esc(data.hotSeatName)} recebeu uma missão!</div>
          <div class="text-muted mt-8">Ronda ${data.round} de ${data.total}</div>
        </div>
        <div class="mission-card">
          <div class="mission-title">A missão:</div>
          <div class="mission-text">${App.esc(data.mission)}</div>
        </div>
        <div class="info-box text-muted">Aguarda a decisão de ${App.esc(data.hotSeatName)}...</div>
      `;
    }
  }

  function decide(choice, container) {
    if (decided) return;
    decided = true;
    SocketClient.emit('submit_answer', { answer: choice });

    // FIX: use the container passed in from renderPlayerRound instead of
    // hardcoded getElementById('round-content') which is null for the host
    // (whose content lives in #host-round-content).
    if (!container) return;

    if (choice === 'accept') {
      container.innerHTML = `
        <div class="answered-state">
          <div class="answered-icon">💪</div>
          <div>Aceitaste o desafio!</div>
          <div class="text-muted mt-8">Cumpre a missão. O grupo vai votar!</div>
        </div>
      `;
    } else {
      container.innerHTML = `
        <div class="answered-state">
          <div class="answered-icon">😬</div>
          <div>Recusaste...</div>
          <div class="text-muted mt-8">Prepara-te para o castigo!</div>
        </div>
      `;
    }
  }

  function renderVoting(data, container, myName) {
    voted = false;
    const isHotSeat = data.hotSeatName === myName;

    if (isHotSeat) {
      container.innerHTML = `
        <div class="timer-bar-wrap"><div class="timer-bar-fill" style="width:100%"></div></div>
        <div class="hot-seat-banner">⏳ Cumpre a missão!</div>
        <div class="mission-card">
          <div class="mission-text">${App.esc(data.mission)}</div>
        </div>
        <div class="info-box text-muted">O grupo está a votar se cumpriu a missão...</div>
      `;
      return;
    }

    container.innerHTML = `
      <div class="timer-bar-wrap"><div class="timer-bar-fill" style="width:100%"></div></div>
      <div class="info-box">
        <div style="font-size: 13px; color: var(--text2); margin-bottom: 6px;">A missão de ${App.esc(data.hotSeatName)}:</div>
        <div style="font-weight: 600;">${App.esc(data.mission)}</div>
      </div>
      <div class="question-meta">Cumpriu a missão?</div>
      <div class="vote-buttons">
        <div>
          <button class="vote-btn vote-truth" id="vote-pass">✅</button>
          <div class="vote-label">Passou!</div>
        </div>
        <div>
          <button class="vote-btn vote-lie" id="vote-fail">❌</button>
          <div class="vote-label">Falhou</div>
        </div>
      </div>
    `;
    document.getElementById('vote-pass').addEventListener('click', () => castVote('pass'));
    document.getElementById('vote-fail').addEventListener('click', () => castVote('fail'));
  }

  function castVote(v) {
    if (voted) return;
    voted = true;
    SocketClient.emit('cast_vote', { vote: v });
    document.querySelectorAll('.vote-btn').forEach(b => { b.disabled = true; });
    const container = document.getElementById('round-content');
    if (container) {
      const hint = document.createElement('div');
      hint.className = 'text-muted text-center mt-16';
      hint.textContent = v === 'pass' ? 'Votaste: Passou! ✅' : 'Votaste: Falhou ❌';
      container.appendChild(hint);
    }
  }

  function renderHostRound(data, container) {
    container.innerHTML = `
      <div class="info-box">
        <div style="font-size: 28px; margin-bottom: 8px;">🔥</div>
        <div style="font-size: 16px; font-weight: 600;">${App.esc(data.hotSeatName)} tem uma missão</div>
        <div class="text-muted mt-8">Ronda ${data.round} de ${data.total}</div>
      </div>
      <div class="mission-card">
        <div class="mission-text">${App.esc(data.mission)}</div>
      </div>
      <div class="answers-progress text-muted" id="answers-progress">Aguardando decisão...</div>
    `;
  }

  function onRoundEnd(result, isHost) {
    const content = document.getElementById('result-content');
    if (!content) return;

    if (!result.accepted) {
      content.innerHTML = `
        <div class="punishment-card">
          <div class="punishment-label">😈 Castigo de ${App.esc(result.hotSeatName)}</div>
          <div class="punishment-text">${App.esc(result.punishment)}</div>
        </div>
      `;
      return;
    }

    if (result.passed) {
      content.innerHTML = `
        <div class="info-box" style="border-color: var(--green);">
          <div style="font-size: 28px; margin-bottom: 6px;">🎉</div>
          <div style="font-weight: 600; color: var(--green);">${App.esc(result.hotSeatName)} completou a missão! +3 pts</div>
        </div>
      `;
    } else {
      content.innerHTML = `
        <div class="punishment-card">
          <div class="punishment-label">😈 Missão falhada — Castigo!</div>
          <div class="punishment-text">${App.esc(result.punishment)}</div>
        </div>
      `;
    }
  }

  App.registerGame('mission', { renderPlayerRound, renderHostRound, renderVoting, onRoundEnd });
  return { renderPlayerRound, renderHostRound, renderVoting, onRoundEnd };
})();
