const CACHE_NAME = 'party-games-v13';
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

  // Skip Socket.io and API calls — always network
  if (url.pathname.startsWith('/socket.io') || url.pathname.startsWith('/join')) {
    return;
  }

  // Cache-first for shell assets
  event.respondWith(
    caches.match(event.request).then((cached) => {
      return cached || fetch(event.request);
    })
  );
});
