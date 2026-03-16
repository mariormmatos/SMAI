// Socket.io client wrapper
// Exposes a simple event bus and emit helpers

const SocketClient = (() => {
  let socket = null;
  const handlers = {};

  function connect() {
    socket = io({ transports: ['websocket', 'polling'] });

    socket.onAny((event, ...args) => {
      if (handlers[event]) {
        handlers[event].forEach(fn => fn(...args));
      }
    });

    socket.on('connect', () => {
      console.log('Socket connected:', socket.id);
    });

    socket.on('disconnect', () => {
      console.log('Socket disconnected');
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

  return { connect, on, off, emit };
})();
