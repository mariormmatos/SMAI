// Verdade ou Mentira — server-side game logic

const QUESTIONS = [
  'Já comi algo que encontrei no chão.',
  'Já menti para sair de uma situação embaraçosa no trabalho/escola.',
  'Já fingi estar doente para não ir a um evento.',
  'Já li o diário de outra pessoa sem permissão.',
  'Já enviei uma mensagem para a pessoa errada e entrei em pânico.',
  'Já fiz amizade com alguém só para obter algo em troca.',
  'Já chorei a ver um filme de animação.',
  'Já fui apanhado/a a falar mal de alguém que estava perto.',
  'Já roubei comida do frigorífico de outra pessoa.',
  'Já fiz algo ilegal sem me ter apercebido na altura.',
  'Já inventei uma desculpa para não ajudar alguém.',
  'Já pesquisei o meu próprio nome no Google.',
  'Já fingi não ter recebido uma mensagem para não ter de responder.',
  'Já caí ou tropecei em público e fingi que não aconteceu nada.',
  'Já dei um presente que recebi a outra pessoa.',
  'Já cantei em voz alta quando achei que estava sozinho/a e afinal havia alguém.',
  'Já espiei o feed de alguém no Instagram por mais de 20 minutos.',
  'Já disse "já estou a caminho" quando nem tinha saído de casa.',
  'Já parti alguma coisa em casa de alguém e não disse nada.',
  'Já menti sobre ter visto um filme/série famoso/a para não parecer desinformado/a.',
  'Já adicionei uma pessoa no LinkedIn só para ver o seu perfil.',
  'Já aplausei um espetáculo que achei péssimo.',
  'Já fiz um pedido diferente no restaurante e comi o que trouxeram sem dizer nada.',
  'Já deixei uma notificação pendente há mais de uma semana.',
  'Já tirei uma selfie em local inapropriado.',
];

const TIME_LIMIT_ANSWER = 60;   // time for hot seat player to answer
const TIME_LIMIT_VOTE = 15;     // time for others to vote

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
    session.gameData.questions = shuffle(QUESTIONS);
    session.gameData.playerOrder = shuffle([...session.players.map(p => p.name)]);
    session.gameData.totalRounds = session.players.length;
    session.gameData.phase = 'answer'; // 'answer' | 'vote'
  },

  getRound(session) {
    const idx = session.round - 1;
    if (idx >= session.gameData.totalRounds) return null;
    const hotSeatName = session.gameData.playerOrder[idx];
    const question = session.gameData.questions[idx % session.gameData.questions.length];
    session.gameData.hotSeat = hotSeatName;
    session.gameData.phase = 'answer';
    session.gameData.hotSeatAnswer = null;
    session.gameData.isTrue = null;
    session.gameData.currentVotes = {};
    return {
      gameType: 'bluff',
      round: session.round,
      total: session.gameData.totalRounds,
      question,
      hotSeatName,
      timeLimit: TIME_LIMIT_ANSWER,
      phase: 'answer',
    };
  },

  onAnswer(session, player, answer, onAllAnswered) {
    // In bluff, only the hot-seat player submits an answer in 'answer' phase
    if (session.gameData.phase !== 'answer') return;
    if (player.name !== session.gameData.hotSeat) return;

    // answer = { text, isTrue }
    session.gameData.hotSeatAnswer = answer.text;
    session.gameData.isTrue = answer.isTrue;

    // Broadcast to all: reveal the answer and start voting
    if (session._io) {
      session._io.to(session.sessionId).emit('voting_start', {
        gameType: 'bluff',
        hotSeatName: session.gameData.hotSeat,
        answer: answer.text,
        question: session.gameData.questions[(session.round - 1) % session.gameData.questions.length],
        timeLimit: TIME_LIMIT_VOTE,
        phase: 'vote',
      });
    }
    session.gameData.phase = 'vote';
  },

  onVote(session, player, vote, onAllAnswered) {
    if (session.gameData.phase !== 'vote') return;
    if (player.name === session.gameData.hotSeat) return; // hot seat can't vote on themselves
    if (session.gameData.currentVotes[player.name] != null) return;
    session.gameData.currentVotes[player.name] = vote; // 'truth' | 'lie'

    const eligible = session.players.filter(p => p.name !== session.gameData.hotSeat);
    const answered = Object.keys(session.gameData.currentVotes).length;
    if (answered >= eligible.length) {
      onAllAnswered();
    }
  },

  scoreRound(session) {
    const isTrue = session.gameData.isTrue;
    const votes = session.gameData.currentVotes;
    const hotSeatName = session.gameData.hotSeat;
    const correctVote = isTrue ? 'truth' : 'lie';

    const deltas = [];
    let correctVoters = 0;
    const eligible = session.players.filter(p => p.name !== hotSeatName);

    eligible.forEach(p => {
      const v = votes[p.name];
      if (v === correctVote) {
        deltas.push({ name: p.name, delta: 2 });
        correctVoters++;
      } else {
        deltas.push({ name: p.name, delta: 0 });
      }
    });

    // Hot seat gets +3 if they fooled the majority
    const fooled = eligible.length - correctVoters;
    const hotSeatDelta = fooled > correctVoters ? 3 : 0;
    deltas.push({ name: hotSeatName, delta: hotSeatDelta });

    return {
      isTrue,
      hotSeatName,
      votes,
      correctVote,
      hotSeatAnswer: session.gameData.hotSeatAnswer,
      question: session.gameData.questions[(session.round - 1) % session.gameData.questions.length],
      deltas,
    };
  },
};
