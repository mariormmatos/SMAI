// Socket.io client wrapper
// Exposes a simple event bus and emit helpers
// Includes connection stability features for mobile (iOS/Android)

const SocketClient = (() => {
  let socket = null;
  const handlers = {};

  // Stores the last pending submission so we can re-emit after reconnect
  let _pendingSubmit = null;   // { event, data }
  let _keepaliveTimer = null;
  let _bannerTimeout = null;   // Delay before showing disconnect banner

  function connect() {
    socket = io({
      transports: ['websocket', 'polling'],
      reconnectionDelay: 500,
      reconnectionDelayMax: 3000,
      timeout: 20000,
      // Let socket.io upgrade from polling to websocket automatically
      upgrade: true,
    });

    socket.onAny((event, ...args) => {
      if (handlers[event]) {
        handlers[event].forEach(fn => fn(...args));
      }
    });

    socket.on('connect', () => {
      console.log('Socket connected:', socket.id);
      // Hide banner immediately on connect
      clearTimeout(_bannerTimeout);
      _bannerTimeout = null;
      setConnectionBanner(false);

      // Start keepalive to prevent Railway/Cloudflare proxy from
      // dropping the WebSocket connection during idle periods
      clearInterval(_keepaliveTimer);
      _keepaliveTimer = setInterval(() => {
        if (socket && socket.connected) {
          socket.emit('keepalive');
        }
      }, 15000); // every 15s — well within Railway's idle timeout

      // On reconnect, rejoin session if we were already in one
      const s = window._appState;
      // Try sessionStorage backup if _appState was cleared
      const backupSessionId = s?.sessionId || sessionStorage.getItem('pg_sessionId');
      const backupName = s?.playerName || sessionStorage.getItem('pg_playerName');
      const isHost = s?.isHost || sessionStorage.getItem('pg_isHost') === 'true';

      if (backupSessionId && isHost) {
        socket.emit('rejoin_host', { sessionId: backupSessionId });
      } else if (backupSessionId && backupName) {
        socket.emit('rejoin_session', { sessionId: backupSessionId, name: backupName });
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
      clearInterval(_keepaliveTimer);
      // DELAY the banner — don't flash it for brief disconnects (<2s)
      // This makes micro-reconnections invisible to users
      if (!_bannerTimeout) {
        _bannerTimeout = setTimeout(() => {
          setConnectionBanner(true);
        }, 2000);
      }
    });

    socket.on('connect_error', () => {
      if (!_bannerTimeout) {
        _bannerTimeout = setTimeout(() => {
          setConnectionBanner(true);
        }, 3000);
      }
    });

    // ── Mobile-specific reconnection handlers ──

    // iOS: reconnect immediately when user returns to the app/tab
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        if (socket && !socket.connected) {
          console.log('Page visible again — forcing reconnect');
          socket.connect();
        }
      }
    });

    // Network: reconnect when device comes back online (WiFi/cellular switch)
    window.addEventListener('online', () => {
      console.log('Network online — forcing reconnect');
      if (socket && !socket.connected) {
        socket.connect();
      }
    });

    // iOS Safari: page show event (back/forward cache restore)
    window.addEventListener('pageshow', (e) => {
      if (e.persisted && socket && !socket.connected) {
        console.log('Page restored from bfcache — forcing reconnect');
        socket.connect();
      }
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

  // Persist session info to sessionStorage (survives brief page issues)
  function persistSession(sessionId, playerName, isHost) {
    try {
      if (sessionId) sessionStorage.setItem('pg_sessionId', sessionId);
      if (playerName) sessionStorage.setItem('pg_playerName', playerName);
      sessionStorage.setItem('pg_isHost', isHost ? 'true' : 'false');
    } catch (e) { /* sessionStorage not available */ }
  }

  function clearSession() {
    try {
      sessionStorage.removeItem('pg_sessionId');
      sessionStorage.removeItem('pg_playerName');
      sessionStorage.removeItem('pg_isHost');
    } catch (e) { /* ignore */ }
  }

  function setConnectionBanner(show) {
    const el = document.getElementById('connection-banner');
    if (el) el.style.display = show ? 'flex' : 'none';
  }

  return { connect, on, off, emit, persistSession, clearSession };
})();
