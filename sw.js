// Service worker v4 — netwerk-eerst: altijd verse resultaten, cache als offline-fallback.
// v4: (1) cache-versie gebumpd om de oude stale cache (v3, ~7 okt) te wissen,
//     (2) netwerk-eerst i.p.v. stale-while-revalidate/cache-first, zodat de data
//         (8x/dag ververst) nooit meer verouderd getoond wordt.
const CACHE = 'portal-rd-v5';

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
  if (e.request.method !== 'GET' || new URL(e.request.url).pathname.startsWith('/api/')) return;
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

// ---- Avisos al móvil (los envía scripts/notificar.py) ----
self.addEventListener('push', e => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch (_) { d = { title: e.data ? e.data.text() : '' }; }
  e.waitUntil(self.registration.showNotification(d.title || 'Portal Dominicano', {
    body: d.body || 'Nuevos resultados de la lotería.',
    icon: '/img/icon-192.png',
    badge: '/img/icon-192.png',
    tag: d.tag || 'resultados',
    data: { url: d.url || '/' },
  }));
});

self.addEventListener('notificationclick', e => {
  e.notification.close();
  const url = new URL((e.notification.data && e.notification.data.url) || '/', self.location.origin).href;
  e.waitUntil(clients.matchAll({ type: 'window', includeUncontrolled: true }).then(ws => {
    for (const w of ws) { if (w.url === url && 'focus' in w) return w.focus(); }
    return clients.openWindow(url);
  }));
});
