// Quiz Rápido — client-side UI

const QuizGame = (() => {
  let answered = false;

  function renderPlayerRound(data, container, myName) {
    answered = false;
    container.innerHTML = `
      <div class="timer-bar-wrap"><div class="timer-bar-fill" style="width:100%"></div></div>
      <div class="question-meta">Pergunta ${data.round} de ${data.total}</div>
      <div class="question-text">${App.esc(data.prompt)}</div>
      <div class="answers-grid" id="quiz-options"></div>
    `;
    const grid = container.querySelector('#quiz-options');
    data.options.forEach((opt, i) => {
      const btn = document.createElement('button');
      btn.className = 'btn-answer';
      btn.textContent = opt;
      btn.addEventListener('click', () => {
        if (answered) return;
        answered = true;
        // Mark selected
        grid.querySelectorAll('.btn-answer').forEach(b => b.disabled = true);
        btn.classList.add('selected');
        SocketClient.emit('submit_answer', { answer: i });
        // Show "aguardando" text
        const hint = document.createElement('div');
        hint.className = 'answered-state';
        hint.innerHTML = '<div class="answered-icon">⏳</div><div>Resposta enviada! Aguardando os outros...</div>';
        // Don't replace grid, just add hint
        container.appendChild(hint);
      });
      grid.appendChild(btn);
    });
  }

  function renderHostRound(data, container) {
    container.innerHTML = `
      <div class="info-box">
        <div style="font-size: 28px; margin-bottom: 8px;">⚡</div>
        <div style="font-size: 16px; font-weight: 600; margin-bottom: 8px;">${App.esc(data.prompt)}</div>
        <div class="text-muted">Pergunta ${data.round} de ${data.total}</div>
      </div>
      <div class="answers-grid">
        ${data.options.map((o, i) => `<div class="host-answer-item"><span>${i+1}. ${App.esc(o)}</span></div>`).join('')}
      </div>
      <div class="info-box text-muted" id="answers-progress">0/${data.options ? '?' : '?'} responderam</div>
    `;
  }

  function onRoundEnd(result, isHost) {
    const content = document.getElementById('result-content');
    if (!content) return;
    content.innerHTML = `
      <div class="info-box">
        <div style="font-size: 13px; color: var(--text2); margin-bottom: 6px;">Resposta correta</div>
        <div style="font-size: 18px; font-weight: 700; color: var(--green);">✓ ${App.esc(result.correctText)}</div>
      </div>
    `;
  }

  App.registerGame('quiz', { renderPlayerRound, renderHostRound, onRoundEnd });
  return { renderPlayerRound, renderHostRound, onRoundEnd };
})();
