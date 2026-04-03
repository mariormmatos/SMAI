// Socket.io client wrapper
// Exposes a simple event bus and emit helpers

const SocketClient = (() => {
  let socket = null;
  const handlers = {};

  function connect() {
    socket = io({
      transports: ['websocket', 'polling'],
      reconnectionDelay: 500,
      reconnectionDelayMax: 3000,
      timeout: 10000,
    });

    socket.onAny((event, ...args) => {
      if (handlers[event]) {
        handlers[event].forEach(fn => fn(...args));
      }
    });

    socket.on('connect', () => {
      console.log('Socket connected:', socket.id);
      setConnectionBanner(false);
      // On reconnect, rejoin session if we were already in one
      const s = window._appState;
      if (s && s.sessionId && s.isHost) {
        socket.emit('rejoin_host', { sessionId: s.sessionId });
      } else if (s && s.sessionId && s.playerName) {
        socket.emit('rejoin_session', { sessionId: s.sessionId, name: s.playerName });
      }
    });

    socket.on('disconnect', () => {
      console.log('Socket disconnected');
      setConnectionBanner(true);
    });

    socket.on('connect_error', () => {
      setConnectionBanner(true);
    });
  }

  function on(event, fn) {
    if (!handlers[event]) handlers[event] = [];
    handlers[event].push(fn);
  }

  function off(event, fn) {
    if (!handlers[event]) return;
    handlers[event] = handlers[event].filter(h => h !== fn);
  }

  function emit(event, data) {
    if (!socket) return;
    socket.emit(event, data || {});
  }

  function setConnectionBanner(show) {
    const el = document.getElementById('connection-banner');
    if (el) el.style.display = show ? 'flex' : 'none';
  }

  return { connect, on, off, emit };
})();
