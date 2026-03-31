// Missão ou Castigo — server-side game logic

const MISSIONS = [
  'Faz uma imitação de alguém na sala durante 30 segundos.',
  'Diz 5 palavras em outra língua sem errar.',
  'Liga para alguém e diz "Tenho uma coisa importante a dizer" e depois canta parabéns.',
  'Faz 10 agachamentos enquanto cantas.',
  'Descreve o sabor do teu gelado favorito de olhos fechados.',
  'Faz o melhor discurso de 1 minuto sobre "Por que razão os patos são superiores".',
  'Conta uma piada. O grupo vota se é engraçada ou não.',
  'Imita um animal durante 20 segundos. O grupo tenta adivinhar.',
  'Diz o alfabeto ao contrário o mais rápido possível.',
  'Faz uma dança de 30 segundos ao estilo dos anos 80.',
  'Conta uma história de 1 minuto onde uses as palavras: banana, foguetão e terapeuta.',
  'Faz uma chamada e deixa uma mensagem a dizer que o teu peixe de estimação morreu.',
  'Escreve o nome de 5 países europeus com a mão não dominante em 30 segundos.',
  'Canta 30 segundos de uma música escolhida pelo grupo.',
  'Faz uma pose dramática de capa de romance durante 20 segundos sem rir.',
  'Explica o enredo de um filme famoso usando apenas emojis falados em voz alta.',
  'Imita 3 sotaques diferentes em 30 segundos.',
  'Faz 5 flexões ou 10 saltos à corda imaginária.',
  'Passa 1 minuto a fazer elogios exagerados ao teu telemóvel.',
  'Tira uma selfie com expressão "artística" e publica story.',
  'Faz uma rima sobre alguém na sala (tem de ser simpática).',
  'Diz "Eu sou o melhor/a" 10 vezes olhando nos olhos de alguém diferente de cada vez.',
  'Convence o grupo de que o teu filme favorito é o melhor de sempre em 1 minuto.',
  'Faz uma roda ou a posição da ponte durante 5 segundos.',
  'Cria um slogan para ti mesmo/a como se fosses um produto.',
  'Faz a tua melhor caminhada em passarela de moda durante 20 segundos.',
  'Representa um filme sem falar — o grupo tem 30 segundos para adivinhar.',
  'Canta a música dos parabéns em ópera.',
  'Faz a tua melhor imitação de um robô a fazer compras.',
  'Conta 10 coisas que gostas na pessoa à tua direita em 30 segundos.',
  'Tenta convencer o grupo de que és um alienígena em visita à Terra.',
  'Faz 10 expressões faciais diferentes em 10 segundos.',
  'Lê uma mensagem de texto do teu telemóvel com voz dramática.',
  'Faz a tua melhor imitação de um comentador de futebol durante 30 segundos.',
  'Faz yoga: fica em posição da árvore durante 15 segundos.',
  'Inventa uma letra nova para uma música conhecida sobre o grupo.',
  'Faz mímica de uma profissão sem falar — o grupo adivinha.',
  'Tira uma selfie e posta com a legenda mais dramática possível.',
  'Faz uma revisão de 5 estrelas de um objeto aleatório da sala.',
  'Imita o estilo de andar de um bebé, de um idoso e de um modelo.',
  'Recita um poema sobre o teu prato de comida preferido.',
  'Faz 30 segundos de stand-up comedy sobre o teu trabalho.',
  'Tenta dobrar a língua, levantar uma sobrancelha e pestanejar em alternância.',
  'Entra na sala como se fosses uma celebridade recebendo prémio.',
  'Faz a tua melhor imitação de um apresentador de telejornal a ler uma notícia absurda.',
  'Conta até 20 em outra língua.',
  'Explica o que é a internet a alguém de 1800.',
  'Faz mímica de um animal que começa com a letra que o grupo escolher.',
  'Escreve o teu nome no ar com o nariz.',
  'Canta "Parabéns" em câmara lenta.',
  'Faz a imitação do teu cantor favorito durante 20 segundos.',
  'Convence o grupo em 1 minuto de que a tua cidade é a melhor do mundo.',
  'Faz o som de 5 animais diferentes em 10 segundos.',
  'Diz "supercalifragilisticexpialidocious" 3 vezes seguidas.',
  'Imita um professor a dar aula sobre um assunto absurdo.',
  'Recita os dias da semana ao contrário.',
  'Faz 20 segundos de breakdance (mesmo que seja só no chão).',
  'Entrevista um objeto da sala como se fosse uma celebridade.',
];

const PUNISHMENTS = [
  'Bebe um shot ou um golo da tua bebida.',
  'O grupo escolhe uma verdade embaraçosa que tens de responder.',
  'Troca o telemóvel com a pessoa à tua direita durante 1 minuto.',
  'O próximo round, tens de responder sempre com sotaque.',
  'Adiciona um contacto aleatório ao grupo de WhatsApp do grupo.',
  'Tira uma foto ridícula e envia para um familiar.',
  'Faz 15 saltos em estrela agora mesmo.',
  'O grupo escolhe um emoji e tens de usá-lo em todas as mensagens por 10 minutos.',
  'Cheira o sapato da pessoa à tua esquerda.',
  'Bebe um golo de água com sal.',
  'Fica de pé e imita uma galinha durante 20 segundos.',
  'Mostra a última pesquisa que fizeste no Google.',
  'Manda uma mensagem cringe para alguém do grupo.',
  'O próximo round, só podes responder em voz de bebé.',
  'Deixa o grupo escolher o teu próximo avatar de WhatsApp.',
  'Faz 10 flexões agora mesmo.',
  'Mostra a última foto que tiraste no telemóvel.',
  'Diz um segredo (não muito sério) ao grupo.',
  'Fica de pé durante o próximo round inteiro.',
  'Imita o som de um animal durante 30 segundos sem parar.',
  'Deixa o grupo mandar uma mensagem no teu telemóvel.',
  'Faz uma rabanada (salto) agora mesmo.',
  'Come algo picante ou azedo que haja na sala.',
  'Faz uma declaração de amor dramática a um objeto da sala.',
  'O teu próximo round tens de jogar de olhos fechados.',
  'Mostra o teu emoji mais usado.',
  'Descreve o teu ex em 3 palavras.',
  'Faz 20 agachamentos.',
  'Canta o refrão de uma música a cappella.',
  'Passa o resto do jogo a chamar todas as pessoas pelo nome errado.',
];

function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

const MISSIONS_PER_PLAYER = 2;
const TIME_LIMIT_DECIDE = 30;
const TIME_LIMIT_VOTE = 20;

module.exports = {
  init(session) {
    session.gameData.missions = shuffle(MISSIONS);
    session.gameData.punishments = shuffle(PUNISHMENTS);
    session.gameData.playerOrder = shuffle([...session.players.map(p => p.name)]);
    // Each player gets 2 missions = total rounds
    session.gameData.totalRounds = session.players.length * MISSIONS_PER_PLAYER;
    session.gameData.missionIndex = 0;
    session.gameData.punishmentIndex = 0;
    session.gameData.phase = 'decide'; // 'decide' | 'vote'
  },

  getRound(session) {
    if (session.round - 1 >= session.gameData.totalRounds) return null;
    // Pick whose turn it is
    const idx = (session.round - 1) % session.gameData.playerOrder.length;
    const hotSeatName = session.gameData.playerOrder[idx];
    const mission = session.gameData.missions[session.gameData.missionIndex % session.gameData.missions.length];
    session.gameData.missionIndex++;
    session.gameData.hotSeat = hotSeatName;
    session.gameData.currentMission = mission;
    session.gameData.phase = 'decide';
    session.gameData.currentAnswers = {};
    session.gameData.currentVotes = {};
    session.gameData.accepted = null;

    return {
      gameType: 'mission',
      round: session.round,
      total: session.gameData.totalRounds,
      hotSeatName,
      mission,
      phase: 'decide',
      timeLimit: TIME_LIMIT_DECIDE,
    };
  },

  onAnswer(session, player, answer, onAllAnswered) {
    // Hot-seat player decides: 'accept' or 'refuse'
    if (player.name !== session.gameData.hotSeat) return;
    if (session.gameData.phase !== 'decide') return;

    session.gameData.accepted = answer === 'accept';

    if (!session.gameData.accepted) {
      // Refused — give punishment immediately and end round
      const punishment = session.gameData.punishments[session.gameData.punishmentIndex % session.gameData.punishments.length];
      session.gameData.punishmentIndex++;
      session.gameData.punishment = punishment;
      onAllAnswered();
      return;
    }

    // Accepted — tell group to perform mission and then vote
    session.gameData.phase = 'vote';
    if (session._io) {
      session._io.to(session.sessionId).emit('voting_start', {
        gameType: 'mission',
        hotSeatName: session.gameData.hotSeat,
        mission: session.gameData.currentMission,
        timeLimit: TIME_LIMIT_VOTE,
        phase: 'vote',
      });
    }
  },

  onVote(session, player, vote, onAllAnswered) {
    if (session.gameData.phase !== 'vote') return;
    if (player.name === session.gameData.hotSeat) return;
    if (session.gameData.currentVotes[player.name] != null) return;
    session.gameData.currentVotes[player.name] = vote; // 'pass' | 'fail'

    const eligible = session.players.filter(p => p.name !== session.gameData.hotSeat);
    if (Object.keys(session.gameData.currentVotes).length >= eligible.length) {
      onAllAnswered();
    }
  },

  scoreRound(session) {
    const hotSeatName = session.gameData.hotSeat;
    const accepted = session.gameData.accepted;
    const deltas = [];

    if (!accepted) {
      // Refused: -1 point
      session.players.forEach(p => {
        deltas.push({ name: p.name, delta: p.name === hotSeatName ? -1 : 0 });
      });
      return {
        accepted: false,
        punishment: session.gameData.punishment,
        hotSeatName,
        deltas,
      };
    }

    // Accepted: check votes
    const votes = session.gameData.currentVotes;
    const passVotes = Object.values(votes).filter(v => v === 'pass').length;
    const failVotes = Object.values(votes).filter(v => v === 'fail').length;
    const passed = passVotes >= failVotes;

    if (passed) {
      deltas.push({ name: hotSeatName, delta: 3 });
    } else {
      const punishment = session.gameData.punishments[session.gameData.punishmentIndex % session.gameData.punishments.length];
      session.gameData.punishmentIndex++;
      session.gameData.punishment = punishment;
      deltas.push({ name: hotSeatName, delta: 0 });
    }
    session.players.filter(p => p.name !== hotSeatName).forEach(p => {
      deltas.push({ name: p.name, delta: 0 });
    });

    return {
      accepted: true,
      passed,
      punishment: passed ? null : session.gameData.punishment,
      hotSeatName,
      votes,
      deltas,
    };
  },
};
