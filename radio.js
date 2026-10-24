/* Reproductor de radio dominicana para las páginas de lotería (mismo estilo que el de la portada).
   Se carga con <script src="/radio.js" defer>: no frena la página y las emisoras
   (data/radio.json) solo se descargan cuando la persona abre el reproductor. */
(function () {
  if (document.getElementById('radioRD')) return;
  var css = '' +
    '#radioRD{position:fixed;right:16px;bottom:16px;z-index:200;width:min(320px,calc(100vw - 32px));font-family:inherit}' +
    '#radioRD .rc{background:#002d62;color:#fff;border-radius:18px;box-shadow:0 14px 40px rgba(0,0,0,.4);overflow:hidden;border:1px solid rgba(255,255,255,.1)}' +
    '#radioRD .rh{display:flex;align-items:center;gap:10px;padding:10px 12px}' +
    '#radioRD .rp{width:44px;height:44px;min-width:44px;border-radius:50%;border:0;background:rgba(255,255,255,.16);color:#fff;font-size:1.1rem;cursor:pointer;display:flex;align-items:center;justify-content:center}' +
    '#radioRD .rp.on{background:#fff;color:#ce1126}' +
    '#radioRD .rm{flex:1;min-width:0;background:none;border:0;color:#fff;text-align:left;cursor:pointer;padding:4px 0;font:inherit}' +
    '#radioRD .rl{display:block;font-size:.6rem;text-transform:uppercase;letter-spacing:.12em;opacity:.75;font-weight:700}' +
    '#radioRD .rs{display:block;font-weight:800;font-size:.92rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}' +
    '#radioRD .rb{display:none;padding:0 12px 12px}' +
    '#radioRD.abierto .rb{display:block}' +
    '#radioRD .rlst{display:flex;flex-direction:column;gap:5px;max-height:220px;overflow-y:auto}' +
    '#radioRD .rst{background:none;border:1px solid rgba(255,255,255,.14);border-radius:10px;color:#fff;padding:9px 11px;text-align:left;font:inherit;font-size:.84rem;font-weight:600;cursor:pointer;min-height:40px}' +
    '#radioRD .rst:hover,#radioRD .rst.act{background:rgba(255,255,255,.18)}' +
    '#radioRD .rmin{font-size:.75rem;opacity:.7;margin-top:6px}' +
    '@media(max-width:600px){#radioRD{right:12px;bottom:12px;width:calc(100vw - 24px)}}' +
    'body{padding-bottom:84px}';
  var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);

  var w = document.createElement('div');
  w.id = 'radioRD';
  w.innerHTML = '<div class="rc"><div class="rh">' +
    '<button class="rp" type="button" aria-label="Reproducir radio">&#9654;</button>' +
    '<button class="rm" type="button" aria-expanded="false" aria-controls="radioLista"><span class="rl">Radio dominicana en vivo</span><span class="rs">Elige una emisora</span></button>' +
    '</div><div class="rb" id="radioLista"><div class="rlst" role="list"></div><div class="rmin">Escucha mientras esperas los resultados.</div></div></div>';
  document.body.appendChild(w);

  var audio = new Audio(); audio.preload = 'none';
  var play = w.querySelector('.rp'), meta = w.querySelector('.rm'), nombre = w.querySelector('.rs'), lista = w.querySelector('.rlst');
  var emisoras = null, actual = null;

  function guardar(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  function leer(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }

  function cargar(cb) {
    if (emisoras) return cb();
    fetch('/data/radio.json').then(function (r) { return r.json(); }).then(function (d) {
      emisoras = (d.emisoras || []).filter(function (e) { return e.url; });
      lista.innerHTML = '';
      emisoras.forEach(function (e, i) {
        var b = document.createElement('button');
        b.type = 'button'; b.className = 'rst'; b.textContent = e.nombre; b.setAttribute('role', 'listitem');
        b.addEventListener('click', function () { sintonizar(i); });
        lista.appendChild(b);
      });
      cb();
    }).catch(function () { nombre.textContent = 'No se pudieron cargar las emisoras'; });
  }
  function sintonizar(i) {
    var e = emisoras[i]; if (!e) return;
    actual = i; guardar('radio-emisora', e.nombre);
    [].forEach.call(lista.children, function (b, j) { b.classList.toggle('act', j === i); });
    nombre.textContent = e.nombre;
    audio.src = e.url;
    audio.play().then(function () { play.classList.add('on'); play.innerHTML = '&#10074;&#10074;'; })
      .catch(function () { nombre.textContent = e.nombre + ' (no disponible, prueba otra)'; });
  }
  function abrir(si) {
    w.classList.toggle('abierto', si);
    meta.setAttribute('aria-expanded', si ? 'true' : 'false');
  }
  meta.addEventListener('click', function () { cargar(function () { abrir(!w.classList.contains('abierto')); }); });
  play.addEventListener('click', function () {
    if (!audio.paused) { audio.pause(); play.classList.remove('on'); play.innerHTML = '&#9654;'; return; }
    cargar(function () {
      if (actual === null) {
        var pref = leer('radio-emisora'), i = 0;
        emisoras.forEach(function (e, j) { if (e.nombre === pref) i = j; });
        sintonizar(i);
      } else {
        audio.play().then(function () { play.classList.add('on'); play.innerHTML = '&#10074;&#10074;'; }).catch(function () {});
      }
    });
  });
  var pref = leer('radio-emisora'); if (pref) nombre.textContent = pref;
})();
