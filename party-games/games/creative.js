// Artista Relâmpago — server-side game logic

const PROMPTS = [
  'Inventa um nome para um perfume feito para pessoas que trabalham de casa.',
  'Escreve o slogan de uma marca de pizza para astronautas.',
  'Dá um título a um filme sobre um gato que descobre a Internet.',
  'Inventa um nome para um superpoder completamente inútil.',
  'Escreve uma frase motivacional completamente absurda.',
  'Nomeia uma app de encontros para veganos extremistas.',
  'Inventa uma lei estranha que faria sentido no séc. XXII.',
  'Descreve o sabor de uma gelatina de queijo em 1 frase.',
  'Cria o título de um livro sobre o tédio do trabalho em escritório.',
  'Inventa uma matéria escolar que deveria existir mas não existe.',
  'Escreve a mensagem de erro de uma app de meditação que crashou.',
  'Dá um nome épico a uma loja de meias.',
  'Descreve o WiFi do inferno em 1 frase.',
  'Inventa uma profissão do futuro que vai existir nos próximos 10 anos.',
  'Escreve a bio de Instagram de um crocodilo influencer.',
  'Cria o nome de uma música country sobre ficar preso no trânsito em Lisboa.',
  'Inventa a senha de entrada de um clube secreto de reformados.',
  'Descreve o "prato do dia" de um restaurante num aeroporto às 3 da manhã.',
  'Escreve a sinopse de um romance histórico que nunca conseguiria ser publicado.',
  'Inventa o nome de um festival de música para pessoas que odeiam música alta.',
];

const TOTAL_ROUNDS = 5;
const TIME_LIMIT_WRITE = 60;
const TIME_LIMIT_VOTE = 20;

function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

module.exports = {
  init(session) {
    session.gameData.prompts = shuffle(PROMPTS).slice(0, TOTAL_ROUNDS);
    session.gameData.totalRounds = TOTAL_ROUNDS;
    session.gameData.phase = 'write';
  },

  getRound(session) {
    const idx = session.round - 1;
    if (idx >= session.gameData.totalRounds) return null;
    session.gameData.phase = 'write';
    session.gameData.currentAnswers = {};
    session.gameData.currentVotes = {};
    session.gameData.answerOrder = null;
    return {
      gameType: 'creative',
      round: session.round,
      total: session.gameData.totalRounds,
      prompt: session.gameData.prompts[idx],
      timeLimit: TIME_LIMIT_WRITE,
      phase: 'write',
    };
  },

  onAnswer(session, player, answer, onAllAnswered) {
    if (session.gameData.phase !== 'write') return;
    if (session.gameData.currentAnswers[player.name] != null) return;
    session.gameData.currentAnswers[player.name] = answer.trim().substring(0, 200);

    const answered = Object.keys(session.gameData.currentAnswers).length;
    if (answered >= session.players.length) {
      // Start voting phase
      const items = shuffle(
        Object.entries(session.gameData.currentAnswers).map(([name, text]) => ({ name, text }))
      );
      session.gameData.answerOrder = items;
      session.gameData.phase = 'vote';
      if (session._io) {
        session._io.to(session.sessionId).emit('voting_start', {
          gameType: 'creative',
          items,
          timeLimit: TIME_LIMIT_VOTE,
          phase: 'vote',
        });
      }
    }
  },

  onVote(session, player, vote, onAllAnswered) {
    if (session.gameData.phase !== 'vote') return;
    if (session.gameData.currentVotes[player.name] != null) return;
    // vote = name of the player they voted for
    // can't vote for yourself
    if (vote === player.name) return;
    session.gameData.currentVotes[player.name] = vote;

    const voted = Object.keys(session.gameData.currentVotes).length;
    if (voted >= session.players.length) {
      onAllAnswered();
    }
  },

  scoreRound(session) {
    const votes = session.gameData.currentVotes;
    const voteTally = {};

    // Count votes per player
    Object.values(votes).forEach(targetName => {
      voteTally[targetName] = (voteTally[targetName] || 0) + 1;
    });

    // Sort by votes
    const ranked = Object.entries(voteTally).sort(([, a], [, b]) => b - a);
    const deltas = [];
    session.players.forEach(p => {
      const v = voteTally[p.name] || 0;
      let pts = 0;
      if (ranked[0] && ranked[0][0] === p.name) pts = 3;
      else if (ranked[1] && ranked[1][0] === p.name) pts = 1;
      deltas.push({ name: p.name, delta: pts });
    });

    return {
      votes: voteTally,
      answers: session.gameData.currentAnswers,
      answerOrder: session.gameData.answerOrder,
      deltas,
    };
  },
};
