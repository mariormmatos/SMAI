// Mente Coletiva — server-side game logic

const QUESTIONS = [
  // Países e geografía
  'Nome um país da Europa.',
  'Nome um país da América do Sul.',
  'Nome um país de África.',
  'Nome um país da Ásia.',
  'Nome um país da América Central ou Caraíbas.',
  'Nome uma capital europeia.',
  'Nome uma capital da América do Sul.',
  'Nome uma capital africana.',
  'Nome um país com mais de 100 milhões de habitantes.',
  'Nome um país com costa para o Mediterrâneo.',
  'Nome um país onde se fala espanhol.',
  'Nome um país da Oceânia.',
  'Nome um país famoso pelo turismo de praia.',
  'Nome uma ilha famosa no mundo.',
  'Nome um país sem mar.',
  'Nome um rio famoso do mundo.',
  'Nome uma montanha famosa.',
  'Nome um lago conhecido.',
  'Nome uma cidade europeia famosa.',
  'Nome uma cidade americana famosa.',
  'Nome uma cidade asiática famosa.',

  // Animais
  'Nome um animal selvagem africano.',
  'Nome um animal doméstico.',
  'Nome um animal que vive no mar.',
  'Nome um pássaro que não voa.',
  'Nome um réptil.',
  'Nome um animal que hiberna.',
  'Nome um inseto.',
  'Nome um animal muito grande.',
  'Nome um animal muito pequeno.',
  'Nome um animal venenoso.',
  'Nome um animal da selva amazónica.',
  'Nome um animal que vive no Ártico.',
  'Nome um animal com listras.',
  'Nome um animal com manchas.',
  'Nome um pássaro comum em Portugal.',
  'Nome um animal que pode ser de estimação exótico.',
  'Nome um animal que faz barulho à noite.',

  // Comida e bebida
  'Nome uma fruta tropical.',
  'Nome um legume.',
  'Nome um tipo de massa (pasta).',
  'Nome um prato típico português.',
  'Nome uma marca de chocolate.',
  'Nome uma bebida alcoólica.',
  'Nome uma bebida sem álcool.',
  'Nome um fast food famoso.',
  'Nome um tipo de queijo.',
  'Nome uma especiaria ou erva aromática.',
  'Nome um peixe comestível.',
  'Nome um marisco.',
  'Nome uma fruta vermelha.',
  'Nome um cereal.',
  'Nome um tipo de pão.',
  'Nome um doce típico português.',
  'Nome uma sobremesa famosa no mundo.',
  'Nome uma marca de cerveja.',
  'Nome um tipo de chá.',
  'Nome algo que colocas numa pizza.',

  // Desporto
  'Nome um desporto olímpico.',
  'Nome um desporto de equipa.',
  'Nome um desporto individual.',
  'Nome um desporto aquático.',
  'Nome um desporto de inverno.',
  'Nome um clube de futebol português.',
  'Nome um clube de futebol europeu famoso.',
  'Nome um jogador de futebol famoso.',
  'Nome um atleta olímpico famoso.',
  'Nome um tenista famoso.',
  'Nome uma corrida de automóveis famosa.',
  'Nome uma maratona famosa.',
  'Nome um ciclista famoso.',
  'Nome um boxer famoso.',
  'Nome uma modalidade de artes marciais.',
  'Nome um evento desportivo mundial.',

  // Música
  'Nome um tipo de música.',
  'Nome um cantor ou cantora português/a.',
  'Nome uma banda de rock famosa.',
  'Nome um artista de hip-hop famoso.',
  'Nome um cantor pop internacional.',
  'Nome um instrumento de corda.',
  'Nome um instrumento de sopro.',
  'Nome um instrumento de percussão.',
  'Nome um festival de música famoso.',
  'Nome uma música de Natal.',
  'Nome uma música que toda a gente conhece.',
  'Nome um álbum famoso.',

  // Cinema e televisão
  'Nome um filme de super-heróis.',
  'Nome um filme de animação.',
  'Nome um ator ou atriz famoso/a.',
  'Nome uma série de televisão famosa.',
  'Nome um filme de terror.',
  'Nome um filme romântico.',
  'Nome um filme de ficção científica.',
  'Nome um personagem de cartoon.',
  'Nome um realizador de cinema famoso.',
  'Nome um prémio de cinema famoso.',
  'Nome um personagem de videojogo.',
  'Nome uma plataforma de streaming.',

  // Tecnologia e marcas
  'Nome uma rede social.',
  'Nome uma marca de telemóvel.',
  'Nome uma marca de computador.',
  'Nome uma marca de roupa desportiva.',
  'Nome uma marca de automóvel alemão.',
  'Nome uma marca de luxo.',
  'Nome uma marca de gelados.',
  'Nome uma marca de refrigerante.',
  'Nome uma marca de café.',
  'Nome uma app que usas todos os dias.',
  'Nome um motor de busca.',
  'Nome uma empresa de tecnologia americana.',

  // Casa e vida quotidiana
  'Nome algo que encontras numa cozinha.',
  'Nome algo que encontras num escritório.',
  'Nome algo que levas para a praia.',
  'Nome algo que é sempre frio.',
  'Nome algo que fazes antes de dormir.',
  'Nome algo que fazes logo ao acordar.',
  'Nome um aparelho eletrodoméstico.',
  'Nome um tipo de mobília.',
  'Nome algo que encontras numa casa de banho.',
  'Nome algo que comprarias num supermercado.',
  'Nome algo que guardas numa mala de viagem.',
  'Nome algo que podes ver da janela.',
  'Nome algo que usas todos os dias.',
  'Nome algo que encontras num quarto de criança.',
  'Nome algo que se usa para limpeza.',

  // Profissões e educação
  'Nome uma profissão da área da saúde.',
  'Nome uma profissão criativa.',
  'Nome uma profissão que usa uniforme.',
  'Nome uma profissão que existe há séculos.',
  'Nome uma profissão bem paga.',
  'Nome uma cadeira que se estuda na escola.',
  'Nome um tipo de escola ou universidade.',
  'Nome um cientista famoso.',
  'Nome um escritor famoso.',
  'Nome um filósofo famoso.',

  // Cultura e curiosidades
  'Nome uma cor primária.',
  'Nome uma forma geométrica.',
  'Nome um número de 1 a 10.',
  'Nome um planeta do sistema solar.',
  'Nome uma constelação famosa.',
  'Nome um elemento químico.',
  'Nome um tipo de energia.',
  'Nome uma língua muito falada no mundo.',
  'Nome uma religião mundial.',
  'Nome uma maravilha do mundo.',
  'Nome um monumento famoso.',
  'Nome um museu famoso.',
  'Nome uma obra de arte famosa.',
  'Nome um livro famoso.',
  'Nome um conto de fadas.',
  'Nome um super-herói.',
  'Nome um vilão de ficção famoso.',
  'Nome um personagem de Shakespeare.',
  'Nome um deus da mitologia grega.',
  'Nome uma figura histórica importante.',
  'Nome um rei ou rainha famoso/a.',

  // Portugal específico
  'Nome uma cidade portuguesa.',
  'Nome um prato típico português.',
  'Nome uma praia portuguesa famosa.',
  'Nome um rio português.',
  'Nome uma Serra em Portugal.',
  'Nome um museu de Lisboa.',
  'Nome algo típico do Porto.',
  'Nome uma celebridade portuguesa.',
  'Nome um futebolista português famoso.',
  'Nome um cantor/a de fado.',
  'Nome um monumento português famoso.',
  'Nome um vinho português.',
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
