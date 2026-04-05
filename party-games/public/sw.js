const CACHE_NAME = 'party-games-v15';
const SHELL_FILES = [
  '/',
  '/index.html',
  '/css/style.css',
  '/js/app.js',
  '/js/socket.js',
  '/js/qr.js',
  '/js/host.js',
  '/js/player.js',
  '/js/games/quiz.js',
  '/js/games/bluff.js',
  '/js/games/creative.js',
  '/js/games/mission.js',
  '/js/games/consensus.js',
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_FILES))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Skip Socket.io, API calls, and join redirect — always network
  if (url.pathname.startsWith('/socket.io') || url.pathname.startsWith('/join')) {
    return;
  }

  // For JS files: network-first with cache fallback
  // This ensures mobile devices always get the latest code
  if (url.pathname.endsWith('.js')) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          // Update cache with fresh version
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // For other assets (CSS, images, HTML): cache-first for speed
  event.respondWith(
    caches.match(event.request).then((cached) => {
      return cached || fetch(event.request);
    })
  );
});
