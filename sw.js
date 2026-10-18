// Service worker v4 — netwerk-eerst: altijd verse resultaten, cache als offline-fallback.
// v4: (1) cache-versie gebumpd om de oude stale cache (v3, ~7 okt) te wissen,
//     (2) netwerk-eerst i.p.v. stale-while-revalidate/cache-first, zodat de data
//         (8x/dag ververst) nooit meer verouderd getoond wordt.
const CACHE = 'portal-rd-v4';

const SHELL = [
  './',
  './index.html',
  './app.html',
  './manifest.json',
  './img/icon-192.png',
  './img/icon-512.png',
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(SHELL)).catch(() => {})
  );
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => k !== CACHE).map(k => caches.delete(k))
    ))
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  // Netwerk eerst, cache als fallback (offline). Zo is data + shell altijd actueel.
  e.respondWith(
    fetch(e.request).then(resp => {
      if (resp.ok) {
        const clone = resp.clone();
        caches.open(CACHE).then(c => c.put(e.request, clone));
      }
      return resp;
    }).catch(() => caches.match(e.request))
  );
});
