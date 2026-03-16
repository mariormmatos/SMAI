// Mente Coletiva — server-side game logic

const QUESTIONS = [
  'Nome um país da Europa.',
  'Nome uma fruta tropical.',
  'Nome algo que encontras numa cozinha.',
  'Nome um animal selvagem africano.',
  'Nome uma marca de carro.',
  'Nome um instrumento musical.',
  'Nome uma cor primária.',
  'Nome um país da América do Sul.',
  'Nome algo que levas para a praia.',
  'Nome uma profissão da área da saúde.',
  'Nome um desporto olímpico.',
  'Nome uma rede social.',
  'Nome algo que encontras num escritório.',
  'Nome um tipo de massa (pasta).',
  'Nome uma capital europeia.',
  'Nome uma marca de roupa desportiva.',
  'Nome algo que é sempre frio.',
  'Nome um animal doméstico.',
  'Nome um tipo de música.',
  'Nome algo que fazes antes de dormir.',
];

const TOTAL_ROUNDS = 8;
const TIME_LIMIT = 20;

function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function normalize(str) {
  return str.trim().toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '') // remove accents
    .replace(/[^a-z0-9\s]/g, '')
    .replace(/\s+/g, ' ');
}

module.exports = {
  init(session) {
    session.gameData.questions = shuffle(QUESTIONS).slice(0, TOTAL_ROUNDS);
    session.gameData.totalRounds = TOTAL_ROUNDS;
    // Random pairs for cooperation bonus
    session.gameData.pairs = makePairs(session.players.map(p => p.name));
  },

  getRound(session) {
    const idx = session.round - 1;
    if (idx >= session.gameData.totalRounds) return null;
    session.gameData.currentAnswers = {};
    // Re-shuffle pairs each round
    session.gameData.pairs = makePairs(session.players.map(p => p.name));
    const pairMap = {};
    session.gameData.pairs.forEach(([a, b]) => {
      if (a && b) {
        pairMap[a] = b;
        pairMap[b] = a;
      }
    });
    session.gameData.pairMap = pairMap;
    return {
      gameType: 'consensus',
      round: session.round,
      total: session.gameData.totalRounds,
      prompt: session.gameData.questions[idx],
      timeLimit: TIME_LIMIT,
      pairs: session.gameData.pairs,
      pairMap,
    };
  },

  onAnswer(session, player, answer, onAllAnswered) {
    if (session.gameData.currentAnswers[player.name] != null) return;
    session.gameData.currentAnswers[player.name] = answer.trim().substring(0, 60);

    const answered = Object.keys(session.gameData.currentAnswers).length;
    if (answered >= session.players.length) {
      onAllAnswered();
    }
  },

  scoreRound(session) {
    const answers = session.gameData.currentAnswers;
    const pairMap = session.gameData.pairMap;

    // Group by normalized answer
    const groups = {};
    Object.entries(answers).forEach(([name, raw]) => {
      const key = normalize(raw);
      if (!groups[key]) groups[key] = { raw, names: [] };
      groups[key].names.push(name);
    });

    // Find modal answer(s)
    const maxCount = Math.max(...Object.values(groups).map(g => g.names.length));

    const deltas = [];
    session.players.forEach(p => {
      const raw = answers[p.name];
      if (!raw) { deltas.push({ name: p.name, delta: 0 }); return; }
      const key = normalize(raw);
      const group = groups[key];
      let pts = 0;
      if (group && group.names.length === maxCount && maxCount > 1) {
        pts += 3;
      }
      // Cooperation bonus: if my pair partner answered the same
      const partnerName = pairMap[p.name];
      if (partnerName) {
        const partnerAnswer = answers[partnerName];
        if (partnerAnswer && normalize(partnerAnswer) === key) {
          pts += 2;
        }
      }
      deltas.push({ name: p.name, delta: pts });
    });

    // Build reveal list sorted by count
    const revealList = Object.values(groups)
      .sort((a, b) => b.names.length - a.names.length)
      .map(g => ({ text: g.raw, count: g.names.length, players: g.names }));

    return {
      answers,
      revealList,
      maxCount,
      deltas,
    };
  },
};

function makePairs(names) {
  const shuffled = shuffle([...names]);
  const pairs = [];
  for (let i = 0; i < shuffled.length - 1; i += 2) {
    pairs.push([shuffled[i], shuffled[i + 1]]);
  }
  if (shuffled.length % 2 !== 0) {
    pairs.push([shuffled[shuffled.length - 1], null]); // solo player
  }
  return pairs;
}
