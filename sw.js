// Service worker — offline real: shell + datos cacheados, datos stale-while-revalidate
const CACHE = 'portal-rd-v2';
const ASSETS = [
  './',
  './index.html',
  './app.html',
  './manifest.json',
  './img/icon-192.png',
  './img/icon-512.png',
  './data/resultados.json',
  './data/radio.json',
  './data/tendencias.json',
  './data/noticias.json',
  './data/divisas.json',
  './data/economia.json',
  './data/eventos.json',
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(ASSETS)).catch(() => {})
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
  const url = new URL(e.request.url);

  // datos: stale-while-revalidate (cache primero, refresca en background).
  // Se usa la URL canónica (sin query) para que el ?v=1 del frontend matchee la cache.
  if (url.pathname.includes('/data/')) {
    const key = new Request(url.origin + url.pathname);
    e.respondWith(
      caches.match(key).then(cached => {
        const fresh = fetch(e.request).then(resp => {
          if (resp.ok) {
            const clone = resp.clone();
            caches.open(CACHE).then(c => c.put(key, clone));
          }
          return resp;
        }).catch(() => cached);
        return cached || fresh;
      })
    );
    return;
  }

  // shell + resto: cache-first, actualiza en background
  e.respondWith(
    caches.match(e.request).then(cached => {
      const fresh = fetch(e.request).then(resp => {
        if (resp.ok) {
          const clone = resp.clone();
          caches.open(CACHE).then(c => c.put(e.request, clone));
        }
        return resp;
      }).catch(() => cached);
      return cached || fresh;
    })
  );
});
