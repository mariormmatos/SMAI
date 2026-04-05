// Socket.io client wrapper
// Exposes a simple event bus and emit helpers

const SocketClient = (() => {
  let socket = null;
  const handlers = {};

  // Stores the last pending submission so we can re-emit after reconnect
  let _pendingSubmit = null;   // { event, data }
  let _keepaliveTimer = null;

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

      // Start keepalive to prevent Railway's ~40s proxy timeout from
      // dropping the WebSocket connection mid-game
      clearInterval(_keepaliveTimer);
      _keepaliveTimer = setInterval(() => {
        if (socket && socket.connected) {
          socket.emit('keepalive');
        }
      }, 20000);

      // On reconnect, rejoin session if we were already in one
      const s = window._appState;
      if (s && s.sessionId && s.isHost) {
        socket.emit('rejoin_host', { sessionId: s.sessionId });
      } else if (s && s.sessionId && s.playerName) {
        socket.emit('rejoin_session', { sessionId: s.sessionId, name: s.playerName });
      }

      // Re-emit any submission that was lost during disconnect
      if (_pendingSubmit) {
        console.log('Re-emitting lost submission:', _pendingSubmit.event);
        socket.emit(_pendingSubmit.event, _pendingSubmit.data);
        _pendingSubmit = null;
      }
    });

    socket.on('disconnect', () => {
      console.log('Socket disconnected');
      setConnectionBanner(true);
      clearInterval(_keepaliveTimer);
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
    // Track critical game submissions so they can be re-sent after a reconnect
    if (event === 'submit_answer' || event === 'cast_vote') {
      if (!socket.connected) {
        // Store and wait for reconnect
        _pendingSubmit = { event, data: data || {} };
        console.log('Socket offline — queuing submission:', event);
        return;
      }
    }
    socket.emit(event, data || {});
  }

  function setConnectionBanner(show) {
    const el = document.getElementById('connection-banner');
    if (el) el.style.display = show ? 'flex' : 'none';
  }

  return { connect, on, off, emit };
})();
