// Quiz Rápido — server-side game logic

const QUESTIONS = [
  { q: 'Qual é a capital de Portugal?', options: ['Lisboa', 'Porto', 'Braga', 'Faro'], answer: 0 },
  { q: 'Quantos planetas tem o sistema solar?', options: ['7', '8', '9', '10'], answer: 1 },
  { q: 'Quem escreveu "Os Lusíadas"?', options: ['Fernando Pessoa', 'Eça de Queirós', 'Luís de Camões', 'Gil Vicente'], answer: 2 },
  { q: 'Qual é o maior oceano do mundo?', options: ['Atlântico', 'Índico', 'Ártico', 'Pacífico'], answer: 3 },
  { q: 'Em que ano Portugal ganhou o Euro de futebol?', options: ['2012', '2016', '2020', '2004'], answer: 1 },
  { q: 'Quantos lados tem um hexágono?', options: ['5', '6', '7', '8'], answer: 1 },
  { q: 'Qual é o elemento químico representado por "Au"?', options: ['Prata', 'Alumínio', 'Ouro', 'Bronze'], answer: 2 },
  { q: 'Qual país tem a maior população do mundo?', options: ['Índia', 'China', 'EUA', 'Rússia'], answer: 0 },
  { q: 'Qual é o animal terrestre mais rápido?', options: ['Leão', 'Tigre', 'Guepardo', 'Leopardo'], answer: 2 },
  { q: 'Quantas cordas tem uma guitarra standard?', options: ['4', '5', '6', '7'], answer: 2 },
  { q: 'Qual é a fórmula química da água?', options: ['CO2', 'H2O', 'O2', 'NaCl'], answer: 1 },
  { q: 'Qual é o país maior do mundo em área?', options: ['Canadá', 'EUA', 'China', 'Rússia'], answer: 3 },
  { q: 'Quem pintou a Mona Lisa?', options: ['Michelangelo', 'Raffaello', 'Leonardo da Vinci', 'Donatello'], answer: 2 },
  { q: 'Qual é a moeda oficial do Japão?', options: ['Won', 'Yuan', 'Yen', 'Ringgit'], answer: 2 },
  { q: 'Quantos continentes tem a Terra?', options: ['5', '6', '7', '8'], answer: 2 },
  { q: 'Qual destes é um mamífero?', options: ['Crocodilo', 'Tubarão', 'Baleia', 'Águia'], answer: 2 },
  { q: 'Em que continent está o Egipto?', options: ['Ásia', 'Europa', 'África', 'América'], answer: 2 },
  { q: 'Qual é o número atómico do carbono?', options: ['4', '6', '8', '12'], answer: 1 },
  { q: 'Qual é a língua mais falada no mundo?', options: ['Inglês', 'Espanhol', 'Mandarim', 'Hindi'], answer: 2 },
  { q: 'Quem foi o primeiro homem na Lua?', options: ['Buzz Aldrin', 'Neil Armstrong', 'Yuri Gagarin', 'John Glenn'], answer: 1 },
  { q: 'Qual destes filmes ganhou mais Óscares?', options: ['Titanic', 'O Senhor dos Anéis: O Regresso do Rei', 'Ben-Hur', 'Todos os anteriores com 11'], answer: 3 },
  { q: 'Quantos jogadores tem uma equipa de basquetebol?', options: ['4', '5', '6', '7'], answer: 1 },
  { q: 'Qual é o nome científico do ser humano?', options: ['Homo sapiens', 'Homo erectus', 'Homo habilis', 'Pan troglodytes'], answer: 0 },
  { q: 'Em que ano foi fundada a Apple?', options: ['1972', '1974', '1976', '1980'], answer: 2 },
  { q: 'Qual é o instrumento principal do jazz?', options: ['Guitarra', 'Violino', 'Saxofone', 'Trompete'], answer: 2 },
  { q: 'Qual é o rio mais comprido do mundo?', options: ['Amazonas', 'Nilo', 'Yangtzé', 'Mississippi'], answer: 1 },
  { q: 'Quantos zeros tem um bilião (pt-PT)?', options: ['6', '9', '12', '15'], answer: 2 },
  { q: 'De que país é originário o sushi?', options: ['China', 'Coreia', 'Japão', 'Tailândia'], answer: 2 },
  { q: 'Qual é a menor unidade de memória de computador?', options: ['Byte', 'Bit', 'Nibble', 'Kilobyte'], answer: 1 },
  { q: 'Qual é o símbolo do elemento Ferro?', options: ['Fr', 'Fe', 'Fo', 'Fi'], answer: 1 },
];

const TOTAL_ROUNDS = 10;
const TIME_LIMIT = 15;

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
    session.gameData.questions = shuffle(QUESTIONS).slice(0, TOTAL_ROUNDS);
    session.gameData.totalRounds = TOTAL_ROUNDS;
  },

  getRound(session) {
    const idx = session.round - 1;
    if (idx >= session.gameData.totalRounds) return null;
    const q = session.gameData.questions[idx];
    return {
      gameType: 'quiz',
      round: session.round,
      total: session.gameData.totalRounds,
      prompt: q.q,
      options: q.options,
      timeLimit: TIME_LIMIT,
      answerIndex: q.answer, // sent to all but client doesn't use it during round
    };
  },

  onAnswer(session, player, answer, onAllAnswered) {
    if (!session.gameData.currentAnswers) session.gameData.currentAnswers = {};
    if (session.gameData.currentAnswers[player.name] != null) return; // already answered
    session.gameData.currentAnswers[player.name] = {
      answer,
      timestamp: Date.now(),
    };
    const answered = Object.keys(session.gameData.currentAnswers).length;
    const total = session.players.length;
    // Notify host of progress
    const hostSocket = session._io && session._io.to(session.hostSocketId);
    if (session._io) {
      session._io.to(session.sessionId).emit('all_answered', { count: answered, total });
    }
    if (answered >= total) {
      onAllAnswered();
    }
  },

  scoreRound(session) {
    const q = session.gameData.questions[session.round - 1];
    const correctIndex = q.answer;
    const answers = session.gameData.currentAnswers || {};

    // Sort correct answerers by timestamp (fastest first)
    const correct = Object.entries(answers)
      .filter(([, v]) => v.answer === correctIndex)
      .sort(([, a], [, b]) => a.timestamp - b.timestamp);

    const deltas = [];
    const pointsMap = [3, 2, 1]; // 1st, 2nd, 3rd+

    session.players.forEach(p => {
      const entry = answers[p.name];
      if (!entry) {
        deltas.push({ name: p.name, delta: 0 });
        return;
      }
      if (entry.answer !== correctIndex) {
        deltas.push({ name: p.name, delta: 0 });
        return;
      }
      const rank = correct.findIndex(([name]) => name === p.name);
      const pts = rank < pointsMap.length ? pointsMap[rank] : 1;
      deltas.push({ name: p.name, delta: pts });
    });

    return {
      correctIndex,
      correctText: q.options[correctIndex],
      answers: Object.fromEntries(
        Object.entries(answers).map(([name, v]) => [name, v.answer])
      ),
      deltas,
    };
  },
};
