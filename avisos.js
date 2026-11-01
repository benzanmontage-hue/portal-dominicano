/* Avisos al móvil: notificación cuando salen los números de las loterías elegidas.
   - Portada: panel #avisosPanel con las 7 loterías.
   - Páginas de lotería: botón [data-aviso="leidsa"] para esa lotería.
   Las suscripciones se guardan en /api/avisos (Cloudflare); el envío lo hace scripts/notificar.py. */
(function () {
  var LOT = [['loteria-nacional', 'Nacional'], ['anguila', 'Anguila'], ['loteria-real', 'Real'], ['loteka', 'Loteka'],
             ['la-primera', 'La Primera'], ['la-suerte', 'La Suerte'], ['leidsa', 'Leidsa']];
  var NOMBRE = {'loteria-nacional': 'Lotería Nacional', 'anguila': 'Anguila', 'loteria-real': 'Lotería Real', 'loteka': 'Loteka',
                'la-primera': 'La Primera', 'la-suerte': 'La Suerte', 'leidsa': 'Leidsa'};
  var soporta = 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
  var ios = /iPhone|iPad|iPod/.test(navigator.userAgent);
  var instalada = (window.matchMedia && matchMedia('(display-mode: standalone)').matches) || navigator.standalone === true;

  var css = '' +
    '.av-card{background:var(--card,#fff);border:1px solid var(--border,#e3e8f2);border-radius:18px;padding:16px;margin:18px 0 0;box-shadow:0 1px 3px rgba(0,0,0,.05)}' +
    '.av-h{font-size:1.1rem;font-weight:800;letter-spacing:-.01em}' +
    '.av-s{font-size:.88rem;color:var(--muted,#64748b);margin:2px 0 12px}' +
    '.av-lots{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px}' +
    '.av-lot{border:1.5px solid var(--border,#e3e8f2);background:transparent;border-radius:999px;padding:8px 14px;font:inherit;font-size:.88rem;font-weight:700;cursor:pointer;color:inherit;min-height:40px}' +
    '.av-lot[aria-pressed="true"]{background:#002d62;border-color:#002d62;color:#fff}' +
    '.av-btn{background:#ce1126;color:#fff;border:0;border-radius:12px;padding:12px 18px;font:inherit;font-weight:800;font-size:.95rem;cursor:pointer;min-height:46px}' +
    '.av-btn[disabled]{opacity:.6;cursor:default}' +
    '.av-msg{font-size:.85rem;margin-top:10px;color:var(--muted,#64748b)}' +
    '.av-msg.ok{color:#15803d;font-weight:700}' +
    '.aviso-btn{display:inline-flex;align-items:center;gap:6px;margin-top:14px;background:#fff;color:#002d62;border:0;border-radius:999px;padding:10px 18px;font:inherit;font-weight:800;font-size:.9rem;cursor:pointer;min-height:44px;box-shadow:0 4px 14px rgba(0,0,0,.18)}' +
    '.aviso-btn.on{background:rgba(255,255,255,.16);color:#fff;box-shadow:none;border:1px solid rgba(255,255,255,.35)}' +
    '.aviso-msg{display:block;font-size:.8rem;margin-top:8px;opacity:.9}';
  var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);

  function leer() { try { return JSON.parse(localStorage.getItem('avisos') || '[]'); } catch (e) { return []; } }
  function guardar(l) { try { localStorage.setItem('avisos', JSON.stringify(l)); } catch (e) {} }
  function bytes(b64) {
    var p = '='.repeat((4 - b64.length % 4) % 4), s = atob((b64 + p).replace(/-/g, '+').replace(/_/g, '/'));
    var out = new Uint8Array(s.length); for (var i = 0; i < s.length; i++) out[i] = s.charCodeAt(i); return out;
  }
  function motivo() {
    if (ios && !instalada) return 'En iPhone primero añade la página a tu pantalla de inicio (botón Compartir → «Añadir a pantalla de inicio») y ábrela desde ahí.';
    if (!soporta) return 'Tu navegador no permite avisos. Prueba con Chrome.';
    if (Notification.permission === 'denied') return 'Tienes los avisos bloqueados para esta página. Actívalos en los ajustes del navegador.';
    return '';
  }

  // Cambia las loterías suscritas (lista vacía = baja). Debe llamarse desde un clic.
  function aplicar(lista) {
    var m = motivo(); if (m) return Promise.reject(new Error(m));
    var permiso = lista.length ? Notification.requestPermission() : Promise.resolve('granted');
    return Promise.resolve(permiso).then(function (p) {
      if (p !== 'granted') throw new Error('Para recibir avisos tienes que permitir las notificaciones.');
      return navigator.serviceWorker.register('/sw.js').then(function () { return navigator.serviceWorker.ready; });
    }).then(function (reg) {
      return reg.pushManager.getSubscription().then(function (sub) {
        if (sub || !lista.length) return sub;
        return fetch('/api/avisos').then(function (r) { return r.json(); }).then(function (d) {
          if (!d.clave) throw new Error(d.error || 'Los avisos no están disponibles ahora; prueba más tarde.');
          return reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: bytes(d.clave) });
        });
      });
    }).then(function (sub) {
      if (!sub) { guardar([]); return []; }
      return fetch('/api/avisos', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subscription: sub.toJSON(), loterias: lista }) })
        .then(function (r) { if (!r.ok) throw new Error('No se pudo guardar; prueba otra vez.'); return r.json(); })
        .then(function (d) { if (!lista.length) sub.unsubscribe(); guardar(d.loterias || []); return d.loterias || []; });
    });
  }

  // ---- Panel de la portada ----
  var panel = document.getElementById('avisosPanel');
  if (panel) {
    var elegidas = leer();
    var marcadas = elegidas.length ? elegidas.slice() : ['loteria-nacional', 'leidsa'];
    panel.innerHTML = '<div class="av-h">🔔 Avísame cuando salgan los números</div>' +
      '<p class="av-s">Elige tus loterías y te llega una notificación al móvil con los números ganadores. Gratis, sin registrarte.</p>' +
      '<div class="av-lots"></div><button class="av-btn" type="button"></button><p class="av-msg" role="status"></p>';
    var cont = panel.querySelector('.av-lots'), btn = panel.querySelector('.av-btn'), msg = panel.querySelector('.av-msg');
    LOT.forEach(function (l) {
      var b = document.createElement('button'); b.type = 'button'; b.className = 'av-lot'; b.textContent = l[1];
      b.setAttribute('aria-pressed', marcadas.indexOf(l[0]) >= 0 ? 'true' : 'false');
      b.addEventListener('click', function () {
        var on = b.getAttribute('aria-pressed') !== 'true'; b.setAttribute('aria-pressed', on ? 'true' : 'false');
        marcadas = on ? marcadas.concat([l[0]]) : marcadas.filter(function (x) { return x !== l[0]; });
        pintar(true);
      });
      cont.appendChild(b);
    });
    function pintar(cambiado) {
      var act = leer();
      btn.textContent = act.length && !marcadas.length ? 'Quitar los avisos' : (act.length ? 'Guardar cambios' : 'Activar avisos');
      btn.disabled = !cambiado && act.length > 0;
      if (!cambiado && act.length) { msg.className = 'av-msg ok'; msg.textContent = '✓ Avisos activos: ' + act.map(function (x) { return NOMBRE[x]; }).join(', '); }
      else if (!cambiado) { msg.className = 'av-msg'; msg.textContent = motivo(); }
    }
    btn.addEventListener('click', function () {
      if (!marcadas.length && !leer().length) { msg.className = 'av-msg'; msg.textContent = 'Elige al menos una lotería.'; return; }
      btn.disabled = true; msg.className = 'av-msg'; msg.textContent = 'Un momento…';
      aplicar(marcadas).then(function () { pintar(false); if (!leer().length) { msg.textContent = 'Avisos quitados.'; } })
        .catch(function (e) { btn.disabled = false; msg.className = 'av-msg'; msg.textContent = e.message; });
    });
    pintar(false);
    panel.hidden = false;
  }

  // ---- Botón en las páginas de cada lotería ----
  [].forEach.call(document.querySelectorAll('[data-aviso]'), function (b) {
    var slug = b.getAttribute('data-aviso'), nombre = NOMBRE[slug] || slug;
    var nota = document.createElement('span'); nota.className = 'aviso-msg'; nota.setAttribute('role', 'status');
    b.insertAdjacentElement('afterend', nota);
    function pintar() {
      var on = leer().indexOf(slug) >= 0;
      b.classList.toggle('on', on);
      b.textContent = on ? '🔕 Quitar aviso de ' + nombre : '🔔 Avísame cuando salga ' + nombre;
    }
    b.addEventListener('click', function () {
      var act = leer(), on = act.indexOf(slug) >= 0;
      var nueva = on ? act.filter(function (x) { return x !== slug; }) : act.concat([slug]);
      b.disabled = true; nota.textContent = 'Un momento…';
      aplicar(nueva).then(function () {
        pintar(); nota.textContent = on ? 'Aviso quitado.' : '✓ Te avisaremos cuando salgan los números de ' + nombre + '.';
      }).catch(function (e) { nota.textContent = e.message; }).then(function () { b.disabled = false; });
    });
    pintar();
    b.hidden = false;
  });
})();
