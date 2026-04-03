// Artista Relâmpago — client-side UI

const CreativeGame = (() => {
  let submitted = false;
  let voted = false;

  function renderPlayerRound(data, container, myName) {
    submitted = false;
    container.innerHTML = `
      <div class="timer-bar-wrap"><div class="timer-bar-fill" style="width:100%"></div></div>
      <div class="question-meta">Ronda ${data.round} de ${data.total} · Criatividade</div>
      <div class="question-text">${App.esc(data.prompt)}</div>
      <div class="answer-input-wrap">
        <textarea class="answer-textarea" id="creative-answer" placeholder="A tua resposta criativa..." maxlength="200" rows="3" autofocus></textarea>
        <button class="btn btn-primary" id="creative-submit">Enviar Resposta ✓</button>
      </div>
    `;
    document.getElementById('creative-submit').addEventListener('click', submitAnswer);
    document.getElementById('creative-answer').addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submitAnswer(); }
    });
  }

  function submitAnswer() {
    if (submitted) return;
    const val = (document.getElementById('creative-answer') || {}).value || '';
    if (!val.trim()) { alert('Escreve uma resposta primeiro!'); return; }
    submitted = true;
    SocketClient.emit('submit_answer', { answer: val.trim() });
    const container = document.getElementById('round-content');
    if (container) {
      container.innerHTML = `
        <div class="answered-state">
          <div class="answered-icon">💡</div>
          <div>Resposta enviada!</div>
          <div class="text-muted mt-8">"${App.esc(val.trim().substring(0, 80))}"</div>
          <div class="text-muted mt-8">Aguardando os outros...</div>
        </div>
      `;
    }
  }

  function renderVoting(data, container, myName) {
    voted = false;
    container.innerHTML = `
      <div class="timer-bar-wrap"><div class="timer-bar-fill" style="width:100%"></div></div>
      <div class="question-meta">Vota na melhor resposta! (não podes votar em ti mesmo)</div>
      <div class="creative-gallery" id="creative-gallery"></div>
    `;
    const gallery = container.querySelector('#creative-gallery');
    (data.items || []).forEach(item => {
      const div = document.createElement('div');
      div.className = 'creative-item';
      const isMine = item.name === myName;
      div.innerHTML = `
        <div class="creative-item-text">${App.esc(item.text)}</div>
        ${isMine ? '<div class="creative-item-votes text-muted">A tua resposta</div>' : ''}
      `;
      if (!isMine) {
        div.addEventListener('click', () => {
          if (voted) return;
          voted = true;
          SocketClient.emit('cast_vote', { vote: item.name });
          gallery.querySelectorAll('.creative-item').forEach(el => el.style.cursor = 'default');
          div.classList.add('voted');
          const hint = document.createElement('div');
          hint.className = 'creative-item-votes';
          hint.textContent = '✓ Votaste nesta!';
          div.appendChild(hint);
        });
      }
      gallery.appendChild(div);
    });
  }

  function renderHostRound(data, container) {
    container.innerHTML = `
      <div class="info-box">
        <div style="font-size: 28px; margin-bottom: 8px;">💡</div>
        <div style="font-size: 16px; font-weight: 600; margin-bottom: 8px;">${App.esc(data.prompt)}</div>
        <div class="text-muted">Ronda ${data.round} de ${data.total}</div>
      </div>
      <div class="info-box text-muted" id="answers-progress">A aguardar respostas...</div>
    `;
  }

  function onRoundEnd(result, isHost) {
    const content = document.getElementById('result-content');
    if (!content) return;
    if (!result.answerOrder) return;
    const voteMap = result.votes || {};
    content.innerHTML = `
      <div class="creative-gallery">
        ${result.answerOrder.map(item => `
          <div class="creative-item" style="cursor:default;">
            <div class="creative-item-text">${App.esc(item.text)}</div>
            <div class="creative-item-votes">${App.esc(item.name)} · ${voteMap[item.name] || 0} voto(s)</div>
          </div>
        `).join('')}
      </div>
    `;
  }

  App.registerGame('creative', { renderPlayerRound, renderHostRound, renderVoting, onRoundEnd });
  return { renderPlayerRound, renderHostRound, renderVoting, onRoundEnd };
})();
