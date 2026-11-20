/* Buscador del sitio, sin servidor: busca en /buscar.json (lo genera scripts/build_buscador.py).
   - Cualquier <input data-buscar> muestra sugerencias mientras se escribe.
   - En /buscar/?q=… pinta la lista completa en #buscarResultados.
   Tolera acentos y una o dos letras mal escritas; «39» encuentra el sueño de ese número. */
(function () {
  var VACIAS = {de: 1, la: 1, el: 1, en: 1, y: 1, los: 1, las: 1, del: 1, con: 1, por: 1, a: 1, su: 1, un: 1, una: 1,
                que: 1, o: 1, al: 1, hoy: 1, resultados: 1, resultado: 1, loteria: 1, numeros: 1, numero: 1, sone: 1, sonar: 1, sueno: 1};
  var datos = null, cargando = null;

  var css = '' +
    '.bz{position:relative;margin-top:10px;width:100%;max-width:520px}' +
    '.bz input{width:100%;font:inherit;font-size:16px;padding:11px 14px 11px 38px;border-radius:12px;border:1px solid var(--border,#d7deea);' +
      'background:#fff url("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%2718%27 height=%2718%27 viewBox=%270 0 24 24%27 fill=%27none%27 stroke=%27%2364748b%27 stroke-width=%272.2%27 stroke-linecap=%27round%27%3E%3Ccircle cx=%2711%27 cy=%2711%27 r=%277%27/%3E%3Cpath d=%27M20 20l-3.5-3.5%27/%3E%3C/svg%3E") no-repeat 12px center;color:#0f172a;-webkit-appearance:none;appearance:none}' +
    '.bz input:focus{outline:2px solid #0a5bbf;outline-offset:1px}' +
    '.bz-l{position:absolute;left:0;right:0;top:calc(100% + 6px);z-index:300;background:#fff;color:#0f172a;border:1px solid #d7deea;border-radius:14px;' +
      'box-shadow:0 14px 40px rgba(0,0,0,.18);overflow:hidden;text-align:left;max-height:70vh;overflow-y:auto}' +
    '.bz-l[hidden]{display:none}' +
    '.bz-i{display:block;padding:10px 14px;text-decoration:none;color:inherit;border-top:1px solid #eef2f7}' +
    '.bz-i:first-child{border-top:0}' +
    '.bz-i.sel,.bz-i:hover{background:#f1f5fb}' +
    '.bz-t{font-weight:700;font-size:.95rem}' +
    '.bz-g{display:inline-block;font-size:.68rem;font-weight:800;text-transform:uppercase;letter-spacing:.06em;color:#0a5bbf;margin-right:6px}' +
    '.bz-d{font-size:.8rem;color:#64748b;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}' +
    '.bz-v{padding:12px 14px;font-size:.88rem;color:#64748b}' +
    '.bz-todo{display:block;padding:10px 14px;font-size:.85rem;font-weight:700;color:#0a5bbf;text-decoration:none;border-top:1px solid #eef2f7;background:#f8fafc}' +
    '.hero .bz,.hoy-in .bz{margin-left:auto;margin-right:auto}' +
    '.br-lista{display:flex;flex-direction:column;gap:8px;margin-top:14px}' +
    '.br-lista .bz-i{background:var(--card,#fff);border:1px solid var(--border,#e3e8f2);border-radius:14px}';
  var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);

  function norm(t) {
    return String(t || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, ' ').trim();
  }
  function cargar() {
    if (datos) return Promise.resolve(datos);
    if (!cargando) cargando = fetch('/buscar.json').then(function (r) { return r.json(); }).then(function (d) {
      datos = d.map(function (e) { e.w = e.k.split(' '); e.tw = norm(e.t).split(' '); return e; }); return datos;
    });
    return cargando;
  }
  // distancia de edición limitada (para tolerar letras mal escritas)
  function dist(a, b, max) {
    if (Math.abs(a.length - b.length) > max) return max + 1;
    var pprev = [], prev = [], cur, i, j;
    for (j = 0; j <= b.length; j++) prev[j] = j;
    for (i = 1; i <= a.length; i++) {
      cur = [i]; var minFila = i;
      for (j = 1; j <= b.length; j++) {
        cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
        if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) cur[j] = Math.min(cur[j], pprev[j - 2] + 1);
        if (cur[j] < minFila) minFila = cur[j];
      }
      if (minFila > max) return max + 1;
      pprev = prev; prev = cur;
    }
    return prev[b.length];
  }
  function puntosToken(tok, e) {
    if (/^\d{1,2}$/.test(tok) && e.g === 'Sueño') {   // «39» o «9» -> sueño de ese número
      var n = tok.length === 1 ? '0' + tok : tok;
      if (e.w[0] === n) return 12;
    }
    var mejor = 0, max = tok.length >= 6 ? 2 : tok.length >= 4 ? 1 : 0;
    for (var i = 0; i < e.w.length; i++) {
      var w = e.w[i], p = 0;
      if (w === tok) p = 4;
      else if (tok.length >= 2 && w.indexOf(tok) === 0) p = 3;
      else if (max && w.length >= 3 && dist(tok, w, max) <= max) p = 1.5;
      if (p && e.tw.indexOf(w) >= 0) p += 2;   // está en el título
      if (p > mejor) mejor = p;
      if (mejor >= 6) break;
    }
    return mejor;
  }
  function buscar(q, limite) {
    var toks = norm(q).split(' ').filter(function (t) { return t && !VACIAS[t]; });
    if (!toks.length) toks = norm(q).split(' ').filter(Boolean);
    if (!toks.length) return [];
    var orden = {'Lotería': 0, 'Sección': 1, 'Juego': 2, 'Anguila': 3, 'Sueño': 4, 'Fecha': 5};
    var res = [];
    datos.forEach(function (e) {
      var total = 0, todos = true;
      toks.forEach(function (t) { var p = puntosToken(t, e); if (!p) todos = false; total += p; });
      if (total > 0) {
        var tc = e.tw.filter(function (w) { return !VACIAS[w]; });   // título sin «lotería», «de»…
        if (tc[0] === toks[0] || (e.g === 'Sueño' && tc[1] === toks[0])) total += 3;   // el título empieza por la búsqueda
        if (e.g === 'Lotería') total += 1.5;                                             // la página principal primero
        if (e.g === 'Sueño' && tc.length === 2 && toks.length === 1 && tc[1] === toks[0]) total += 1;  // «muerto» = 08
      }
      if (total > 0) res.push({e: e, p: total + (todos ? 10 : 0), todos: todos});
    });
    var completos = res.filter(function (r) { return r.todos; });
    if (completos.length) res = completos;
    res.sort(function (a, b) { return b.p - a.p || (orden[a.e.g] || 9) - (orden[b.e.g] || 9) || (a.e.g === 'Fecha' ? (a.e.u < b.e.u ? 1 : -1) : 0); });
    return res.slice(0, limite).map(function (r) { return r.e; });
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]; }); }
  function item(e) {
    return '<a class="bz-i" href="' + esc(e.u) + '"><div class="bz-t"><span class="bz-g">' + esc(e.g) + '</span>' + esc(e.t) + '</div>' +
      (e.d ? '<div class="bz-d">' + esc(e.d) + '</div>' : '') + '</a>';
  }

  // ---- sugerencias en cada caja de búsqueda ----
  [].forEach.call(document.querySelectorAll('input[data-buscar]'), function (inp) {
    var caja = inp.parentNode; caja.classList.add('bz');
    var lista = document.createElement('div'); lista.className = 'bz-l'; lista.hidden = true; lista.setAttribute('role', 'listbox');
    caja.appendChild(lista);
    var sel = -1;
    function pintar() {
      var q = inp.value.trim();
      if (!q) { lista.hidden = true; return; }
      cargar().then(function () {
        var r = buscar(q, 8); sel = -1;
        lista.innerHTML = r.length ? r.map(item).join('') + '<a class="bz-todo" href="/buscar/?q=' + encodeURIComponent(q) + '">Ver todos los resultados ›</a>'
                                   : '<div class="bz-v">Sin resultados para «' + esc(q) + '». Prueba con el nombre de la lotería, un número o un sueño.</div>';
        lista.hidden = false;
      });
    }
    inp.addEventListener('input', pintar);
    inp.addEventListener('focus', function () { cargar(); if (inp.value.trim()) pintar(); });
    inp.addEventListener('keydown', function (ev) {
      var items = lista.querySelectorAll('.bz-i');
      if (ev.key === 'ArrowDown' || ev.key === 'ArrowUp') {
        if (!items.length) return; ev.preventDefault();
        sel = (sel + (ev.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length;
        [].forEach.call(items, function (a, i) { a.classList.toggle('sel', i === sel); });
      } else if (ev.key === 'Enter' && sel >= 0 && items[sel]) {
        ev.preventDefault(); location.href = items[sel].getAttribute('href');
      } else if (ev.key === 'Escape') { lista.hidden = true; }
    });
    document.addEventListener('click', function (ev) { if (!caja.contains(ev.target)) lista.hidden = true; });
  });

  // ---- página /buscar/ ----
  var destino = document.getElementById('buscarResultados');
  if (destino) {
    var q = new URLSearchParams(location.search).get('q') || '';
    var campo = document.querySelector('input[data-buscar]'); if (campo) campo.value = q;
    if (q.trim()) {
      document.title = 'Buscar «' + q + '» — Portal Dominicano';
      cargar().then(function () {
        var r = buscar(q, 40);
        destino.innerHTML = r.length ? '<p class="intro">' + r.length + ' resultado' + (r.length > 1 ? 's' : '') + ' para «' + esc(q) + '»</p><div class="br-lista">' + r.map(item).join('') + '</div>'
                                     : '<p class="intro">Sin resultados para «' + esc(q) + '». Prueba con el nombre de la lotería (Leidsa, Anguila…), un número (39) o un sueño (conejo).</p>';
      });
    }
  }
})();
