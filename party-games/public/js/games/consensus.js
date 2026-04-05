// Mente Coletiva — client-side UI
const ConsensusGame = (() => {
  let submitted = false;

  function renderPlayerRound(data, container, myName) {
    submitted = false;
    const pairMap = data.pairMap || {};
    const partner = pairMap[myName];
    const partnerHtml = partner
      ? `<div class="pair-badge">🤝 O teu par esta ronda: <strong>${App.esc(partner)}</strong></div>`
      : `<div class="pair-badge">🎯 Estás sozinho/a esta ronda</div>`;

    container.innerHTML = `
      <div class="timer-bar-wrap"><div class="timer-bar-fill" style="width:100%"></div></div>
      <div class="question-meta">Ronda ${data.round} de ${data.total} · Resposta mais comum = pontos!</div>
      ${partnerHtml}
      <div class="question-text">${App.esc(data.prompt)}</div>
      <div class="answer-input-wrap">
        <input type="text" class="form-input" id="consensus-answer" placeholder="A tua resposta..." maxlength="60" autocomplete="off" autocorrect="off">
        <button class="btn btn-primary" id="consensus-submit">Enviar ✓</button>
      </div>
    `;
    // FIX: capture container in closure
    document.getElementById('consensus-submit').addEventListener('click', () => submitAnswer(container));
    document.getElementById('consensus-answer').addEventListener('keydown', e => {
      if (e.key === 'Enter') submitAnswer(container);
    });
    setTimeout(() => document.getElementById('consensus-answer')?.focus(), 200);
  }

  function submitAnswer(container) {
    if (submitted) return;
    const val = (document.getElementById('consensus-answer') || {}).value || '';
    if (!val.trim()) {
      alert('Escreve uma resposta!');
      return;
    }
    submitted = true;
    SocketClient.emit('submit_answer', { answer: val.trim() });

    // FIX: use the captured container instead of hardcoded getElementById
    if (container) {
      container.innerHTML = `
        <div class="answered-state">
          <div class="answered-icon">🧠</div>
          <div>Respondeste: <strong>${App.esc(val.trim())}</strong></div>
          <div class="text-muted mt-8">Aguardando os outros...</div>
        </div>
      `;
    }
  }

  function renderHostRound(data, container) {
    container.innerHTML = `
      <div class="info-box">
        <div style="font-size: 28px; margin-bottom: 8px;">🧠</div>
        <div style="font-size: 16px; font-weight: 600; margin-bottom: 8px;">${App.esc(data.prompt)}</div>
        <div class="text-muted">Ronda ${data.round} de ${data.total}</div>
      </div>
      <div class="info-box text-muted" id="answers-progress">A aguardar respostas...</div>
    `;
  }

  function onRoundEnd(result, isHost) {
    const content = document.getElementById('result-content');
    if (!content) return;
    if (!result.revealList) return;
    content.innerHTML = `
      <div class="consensus-reveal">
        ${result.revealList.map(r => `
          <div class="consensus-answer-row ${r.count === result.maxCount && result.maxCount > 1 ? 'winner' : ''}">
            <span class="consensus-answer-text">${App.esc(r.text)}</span>
            <span class="consensus-answer-count">${r.count}×</span>
          </div>
        `).join('')}
      </div>
    `;
  }

  App.registerGame('consensus', { renderPlayerRound, renderHostRound, onRoundEnd });
  return { renderPlayerRound, renderHostRound, onRoundEnd };
})();
