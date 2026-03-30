const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const path = require('path');
const os = require('os');
const { v4: uuidv4 } = require('uuid');
const games = require('./games/index');

const app = express();
const server = http.createServer(app);
const io = new Server(server, { cors: { origin: '*' } });

const PORT = process.env.PORT || 3000;

// Public base URL: Railway sets RAILWAY_PUBLIC_DOMAIN automatically.
// Falls back to local network IP for home WiFi use.
function getBaseUrl() {
  if (process.env.RAILWAY_PUBLIC_DOMAIN) {
    return `https://${process.env.RAILWAY_PUBLIC_DOMAIN}`;
  }
  if (process.env.BASE_URL) {
    return process.env.BASE_URL;
  }
  // Local WiFi fallback
  const ifaces = os.networkInterfaces();
  for (const name of Object.keys(ifaces)) {
    for (const iface of ifaces[name]) {
      if (iface.family === 'IPv4' && !iface.internal) {
        return `http://${iface.address}:${PORT}`;
      }
    }
  }
  return `http://localhost:${PORT}`;
}

const BASE_URL = getBaseUrl();

// In-memory sessions: sessionId → session object
const sessions = new Map();

function generateSessionId() {
  return uuidv4().substring(0, 6).toUpperCase();
}

app.use(express.static(path.join(__dirname, 'public')));

// Join via QR code URL redirect
app.get('/join', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

io.on('connection', (socket) => {
  console.log('Client connected:', socket.id);

  // HOST: create a new game session
  socket.on('create_session', ({ game }) => {
    const sessionId = generateSessionId();
    const joinUrl = `${BASE_URL}/join?s=${sessionId}`;
    const session = {
      sessionId,
      hostSocketId: socket.id,
      game,
      phase: 'lobby',
      players: [],
      round: 0,
      gameData: {},
      joinUrl,
      _io: io,
    };
    sessions.set(sessionId, session);
    socket.join(sessionId);
    socket.emit('session_created', { sessionId, joinUrl });
    console.log(`Session ${sessionId} created for game: ${game}`);
  });

  // PLAYER: join an existing session
  socket.on('join_session', ({ sessionId, name }) => {
    const session = sessions.get(sessionId.toUpperCase());
    if (!session) {
      socket.emit('join_error', { message: 'Sessão não encontrada. Verifica o código.' });
      return;
    }
    if (session.phase !== 'lobby') {
      socket.emit('join_error', { message: 'O jogo já começou. Não é possível entrar.' });
      return;
    }
    const trimmedName = name.trim().substring(0, 20);
    if (!trimmedName) {
      socket.emit('join_error', { message: 'O nome não pode estar vazio.' });
      return;
    }
    const nameTaken = session.players.some(p => p.name.toLowerCase() === trimmedName.toLowerCase());
    if (nameTaken) {
      socket.emit('join_error', { message: 'Esse nome já está em uso. Escolhe outro.' });
      return;
    }

    const player = { socketId: socket.id, name: trimmedName, score: 0 };
    session.players.push(player);
    socket.join(sessionId.toUpperCase());
    socket.emit('join_success', { sessionId: session.sessionId, name: trimmedName, game: session.game });
    io.to(session.sessionId).emit('player_joined', { players: session.players.map(p => ({ name: p.name, score: p.score })) });
    console.log(`${trimmedName} joined session ${session.sessionId}`);
  });

  // PLAYER: rejoin after socket reconnect
  socket.on('rejoin_session', ({ sessionId, name }) => {
    const session = sessions.get(sessionId.toUpperCase());
    if (!session) return;
    const player = session.players.find(p => p.name.toLowerCase() === name.toLowerCase());
    if (!player) return;
    player.socketId = socket.id;
    socket.join(session.sessionId);
    socket.emit('join_success', { sessionId: session.sessionId, name: player.name, game: session.game });
    // If round already in progress, resend current round data
    if (session.phase === 'playing' && session.gameData.roundData) {
      socket.emit('game_started', { game: session.game });
      socket.emit('round_start', session.gameData.roundData);
    }
    console.log(`${name} rejoined session ${session.sessionId}`);
  });

  // HOST: start the game
  socket.on('start_game', () => {
    const session = findSessionByHost(socket.id);
    if (!session) return;
    if (session.players.length < 1) {
      socket.emit('start_error', { message: 'Precisas de pelo menos 1 jogador.' });
      return;
    }
    session.phase = 'playing';
    session.round = 0;
    const gameModule = games.getGame(session.game);
    gameModule.init(session);
    io.to(session.sessionId).emit('game_started', { game: session.game });
    setTimeout(() => startNextRound(session), 1000);
  });

  // HOST: advance to next round
  socket.on('next_round', () => {
    const session = findSessionByHost(socket.id);
    if (!session) return;
    startNextRound(session);
  });

  // PLAYER: submit an answer
  socket.on('submit_answer', ({ answer }) => {
    const { session, player } = findSessionByPlayer(socket.id);
    if (!session || !player) return;
    const gameModule = games.getGame(session.game);
    gameModule.onAnswer(session, player, answer, () => {
      // called when all players have answered
      endRound(session);
    });
  });

  // PLAYER: cast a vote
  socket.on('cast_vote', ({ vote }) => {
    const { session, player } = findSessionByPlayer(socket.id);
    if (!session || !player) return;
    const gameModule = games.getGame(session.game);
    gameModule.onVote && gameModule.onVote(session, player, vote, () => {
      endRound(session);
    });
  });

  // HOST: end game early
  socket.on('end_game', () => {
    const session = findSessionByHost(socket.id);
    if (!session) return;
    finishGame(session);
  });

  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id);
    // Remove player from session if they disconnect
    for (const [sessionId, session] of sessions) {
      const idx = session.players.findIndex(p => p.socketId === socket.id);
      if (idx !== -1 && session.phase === 'lobby') {
        session.players.splice(idx, 1);
        io.to(sessionId).emit('player_joined', { players: session.players.map(p => ({ name: p.name, score: p.score })) });
      }
      // Clean up host sessions
      if (session.hostSocketId === socket.id) {
        sessions.delete(sessionId);
      }
    }
  });
});

function startNextRound(session) {
  const gameModule = games.getGame(session.game);
  session.round++;
  const roundData = gameModule.getRound(session);
  if (!roundData) {
    finishGame(session);
    return;
  }
  session.phase = 'playing';
  session.gameData.currentAnswers = {};
  session.gameData.currentVotes = {};
  session.gameData.roundData = roundData;
  io.to(session.sessionId).emit('round_start', roundData);
}

function endRound(session) {
  const gameModule = games.getGame(session.game);
  const result = gameModule.scoreRound(session);
  // Apply score deltas
  result.deltas.forEach(({ name, delta }) => {
    const player = session.players.find(p => p.name === name);
    if (player) player.score += delta;
  });
  session.phase = 'round_result';
  io.to(session.sessionId).emit('round_end', {
    ...result,
    scores: session.players.map(p => ({ name: p.name, score: p.score })).sort((a, b) => b.score - a.score),
  });
}

function finishGame(session) {
  session.phase = 'final';
  const finalScores = session.players
    .map(p => ({ name: p.name, score: p.score }))
    .sort((a, b) => b.score - a.score);
  io.to(session.sessionId).emit('game_end', { finalScores });
  // Clean up after 30 min
  setTimeout(() => sessions.delete(session.sessionId), 30 * 60 * 1000);
}

function findSessionByHost(socketId) {
  for (const session of sessions.values()) {
    if (session.hostSocketId === socketId) return session;
  }
  return null;
}

function findSessionByPlayer(socketId) {
  for (const session of sessions.values()) {
    const player = session.players.find(p => p.socketId === socketId);
    if (player) return { session, player };
  }
  return { session: null, player: null };
}

server.listen(PORT, '0.0.0.0', () => {
  console.log(`\n🎮 Party Games server running!`);
  console.log(`   Local:    http://localhost:${PORT}`);
  console.log(`   Public:   ${BASE_URL}`);
  console.log(`\n   Share the Public URL (or QR code) with your friends.\n`);
});
