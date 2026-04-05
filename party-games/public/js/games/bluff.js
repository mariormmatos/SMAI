// Verdade ou Mentira — client-side UI
const BluffGame = (() => {
  let voted = false;
  let answered = false;

  function renderPlayerRound(data, container, myName) {
    answered = false;
    const isHotSeat = data.hotSeatName === myName;

    if (isHotSeat) {
      container.innerHTML = `
        <div class="timer-bar-wrap"><div class="timer-bar-fill" style="width:100%"></div></div>
        <div class="hot-seat-banner">🔥 És o/a Convidado/a de Honra!</div>
        <div class="question-text">${App.esc(data.question)}</div>
        <div class="question-meta">Responde com verdade ou inventa algo para enganar os outros!</div>
        <div class="answer-input-wrap">
          <textarea class="answer-textarea" id="bluff-answer" placeholder="A tua resposta..." maxlength="200" rows="3"></textarea>
          <div style="display: flex; gap: 10px;">
            <button class="btn btn-primary" id="bluff-truth-btn" style="flex:1; padding:14px;">
              ✅ É verdade!
            </button>
            <button class="btn btn-secondary" id="bluff-lie-btn" style="flex:1; padding:14px; border: 2px solid var(--red);">
              🎭 Estou a mentir
            </button>
          </div>
        </div>
      `;
      // FIX: capture container in closure to ensure correct element is updated
      document.getElementById('bluff-truth-btn').addEventListener('click', () => submitBluffAnswer(true, container));
      document.getElementById('bluff-lie-btn').addEventListener('click', () => submitBluffAnswer(false, container));
    } else {
      container.innerHTML = `
        <div class="timer-bar-wrap"><div class="timer-bar-fill" style="width:100%"></div></div>
        <div class="info-box">
          <div style="font-size: 32px; margin-bottom: 8px;">🎭</div>
          <div style="font-weight: 600; font-size: 16px; margin-bottom: 6px;">${App.esc(data.hotSeatName)} está a responder...</div>
          <div class="text-muted">A seguir vais votar se é verdade ou mentira!</div>
        </div>
      `;
    }
  }

  function submitBluffAnswer(isTrue, container) {
    if (answered) return;
    const text = (document.getElementById('bluff-answer') || {}).value || '';
    if (!text.trim()) {
      alert('Escreve uma resposta primeiro!');
      return;
    }
    answered = true;
    SocketClient.emit('submit_answer', { answer: { text: text.trim(), isTrue } });

    // FIX: use the container captured in renderPlayerRound, not hardcoded getElementById
    if (container) {
      container.innerHTML = `
        <div class="answered-state">
          <div class="answered-icon">${isTrue ? '✅' : '🎭'}</div>
          <div>Resposta enviada!</div>
          <div class="text-muted mt-8">${isTrue ? 'Disseste que é verdade.' : 'Disseste que é mentira!'}</div>
          <div class="text-muted mt-8">Aguardando os outros votarem...</div>
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
        <div class="info-box">
          <div style="font-size: 13px; color: var(--text2); margin-bottom: 6px;">A pergunta era:</div>
          <div style="font-weight: 600;">${App.esc(data.question)}</div>
        </div>
        <div class="reveal-box">"${App.esc(data.answer)}"</div>
        <div class="info-box text-muted">Os outros estão a votar se acreditam em ti...</div>
      `;
      return;
    }

    container.innerHTML = `
      <div class="timer-bar-wrap"><div class="timer-bar-fill" style="width:100%"></div></div>
      <div class="info-box">
        <div style="font-size: 13px; color: var(--text2); margin-bottom: 6px;">${App.esc(data.hotSeatName)} disse:</div>
        <div style="font-weight: 600; font-size: 16px;">${App.esc(data.question)}</div>
      </div>
      <div class="reveal-box">"${App.esc(data.answer)}"</div>
      <div class="vote-buttons">
        <div>
          <button class="vote-btn vote-truth" id="vote-truth">✅</button>
          <div class="vote-label">Verdade</div>
        </div>
        <div>
          <button class="vote-btn vote-lie" id="vote-lie">🤥</button>
          <div class="vote-label">Mentira</div>
        </div>
      </div>
    `;
    document.getElementById('vote-truth').addEventListener('click', () => castVote('truth'));
    document.getElementById('vote-lie').addEventListener('click', () => castVote('lie'));
  }

  function castVote(v) {
    if (voted) return;
    voted = true;
    SocketClient.emit('cast_vote', { vote: v });
    document.querySelectorAll('.vote-btn').forEach(b => {
      b.disabled = true;
      b.classList.add('selected');
    });
    const container = document.getElementById('round-content');
    if (container) {
      const hint = document.createElement('div');
      hint.className = 'text-muted text-center mt-16';
      hint.textContent = v === 'truth' ? 'Votaste: Verdade ✅' : 'Votaste: Mentira 🤥';
      container.appendChild(hint);
    }
  }

  function renderHostRound(data, container) {
    container.innerHTML = `
      <div class="info-box">
        <div style="font-size: 28px; margin-bottom: 8px;">🎭</div>
        <div style="font-size: 16px; font-weight: 600;">${App.esc(data.hotSeatName)} está no hot seat</div>
        <div class="text-muted mt-8">Ronda ${data.round} de ${data.total}</div>
      </div>
      <div class="answers-progress text-muted" id="answers-progress">A aguardar resposta...</div>
    `;
  }

  function onRoundEnd(result, isHost) {
    const content = document.getElementById('result-content');
    if (!content) return;
    const truthIcon = result.isTrue ? '✅ Era verdade!' : '🤥 Era mentira!';
    const voteResults = Object.entries(result.votes || {})
      .map(([name, v]) => `<span class="chip ${v === result.correctVote ? 'chip-green' : 'chip-red'}">${App.esc(name)}: ${v === 'truth' ? 'Verdade' : 'Mentira'}</span>`)
      .join(' ');
    content.innerHTML = `
      <div class="info-box">
        <div style="font-size: 13px; color: var(--text2); margin-bottom: 4px;">${App.esc(result.hotSeatName)} disse:</div>
        <div style="font-size: 15px; font-style: italic; margin-bottom: 8px;">"${App.esc(result.hotSeatAnswer)}"</div>
        <div style="font-size: 18px; font-weight: 700;">${truthIcon}</div>
      </div>
      ${voteResults ? `<div style="display:flex; flex-wrap:wrap; gap:6px; padding: 4px 0;">${voteResults}</div>` : ''}
    `;
  }

  App.registerGame('bluff', { renderPlayerRound, renderHostRound, renderVoting, onRoundEnd });
  return { renderPlayerRound, renderHostRound, renderVoting, onRoundEnd };
})();
