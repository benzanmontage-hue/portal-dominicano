#!/usr/bin/env python3
"""Generar las 7 páginas SEO de lotería con los resultados ESCRITOS en el HTML.

Google lee los números, la fecha del sorteo, el historial y las preguntas frecuentes
sin tener que ejecutar JavaScript. El JS de la página solo refresca los números si hay
datos más nuevos que los del HTML.

Lee:  data/resultados.json, data/archivo.json
Escribe: <slug>/index.html
"""
import datetime
import re
import json
import os

from comun import (ROOT, BASE, MESES, SECCIONES, esc, limpiar, cargar_json, parse_fecha, fechas_con_pagina, minutos_juego, titulo,
                   fecha_larga, actualizado_rd, hora_12, ordenar_juegos, balls_html)

LOTERIAS = [
    {
        "slug": "loteria-nacional",
        "nombre": "Lotería Nacional",
        "compania": "Nacional",
        "title": "Lotería Nacional de Hoy — Resultados y Números Ganadores",
        "desc": "Resultados de la Lotería Nacional de hoy en República Dominicana. Números ganadores de la quiniela, Gana Más, Juega + Pega + y Billetes Domingo, con historial de días anteriores.",
        "h1": "Lotería Nacional de Hoy",
        "intro": "Consulta los <strong>resultados de la Lotería Nacional de hoy</strong> con sus números ganadores. La Lotería Nacional Dominicana sortea todos los días e incluye la <strong>Quiniela</strong> (3 pares de dos cifras), <strong>Gana Más</strong>, <strong>Juega + Pega +</strong> y <strong>Billetes Domingo</strong>.",
        "hora": "Gana Más 2:30 PM. Noche: lun–sáb 8:50–9:00 PM, domingo 6:00 PM (hora RD).",
    },
    {
        "slug": "loteria-real",
        "nombre": "Lotería Real",
        "compania": "Loteria Real",
        "title": "Lotería Real de Hoy — Resultados y Quiniela Real",
        "desc": "Resultados de la Lotería Real de hoy en República Dominicana. Números ganadores de la Quiniela Real, Lotería Real Noche, Loto Real, Loto Pool y Super Palé, con historial.",
        "h1": "Lotería Real de Hoy",
        "intro": "Consulta los <strong>resultados de la Lotería Real de hoy</strong> con sus números ganadores. Incluye <strong>Lotería Real Noche</strong>, <strong>Quiniela Real</strong>, <strong>Loto Real</strong>, <strong>Loto Pool</strong> y más sorteos.",
        "hora": "Quiniela Real todos los días a las 12:55 PM (hora RD).",
    },
    {
        "slug": "anguila",
        "nombre": "Anguila",
        "compania": "Anguila",
        "title": "Lotería Anguila de Hoy — Resultados y Números Ganadores",
        "desc": "Resultados de la Lotería Anguila de hoy en República Dominicana. Todos los sorteos horarios de 8:00 AM a 10:00 PM y La Cuarteta, con sus números ganadores.",
        "h1": "Lotería Anguila de Hoy",
        "intro": "Consulta los <strong>resultados de la Lotería Anguila de hoy</strong> con todos sus sorteos horarios. Anguila sortea varias veces al día, desde las <strong>8:00 AM hasta las 10:00 PM</strong>, e incluye <strong>La Cuarteta</strong>.",
        "hora": "Cada hora de 8:00 AM a 10:00 PM (hora RD).",
    },
    {
        "slug": "loteka",
        "nombre": "Loteka",
        "compania": "Loteka",
        "title": "Loteka de Hoy — Resultados y Quiniela Loteka",
        "desc": "Resultados de Loteka de hoy en República Dominicana. Números ganadores de la Quiniela Loteka, MegaLotto, Mega Chances y Toca 3, con historial de días anteriores.",
        "h1": "Loteka de Hoy",
        "intro": "Consulta los <strong>resultados de Loteka de hoy</strong> con sus números ganadores. Incluye <strong>Quiniela Loteka</strong>, <strong>MegaLotto</strong>, <strong>Mega Chances</strong>, <strong>Toca 3</strong> y <strong>MC Repartidera</strong>.",
        "hora": "Todos los días a las 7:55 PM (hora RD).",
    },
    {
        "slug": "la-primera",
        "nombre": "La Primera",
        "compania": "La Primera",
        "title": "La Primera de Hoy — Resultados y Números Ganadores",
        "desc": "Resultados de La Primera de hoy en República Dominicana. Números ganadores de La Primera Día, Primera Noche, El Quinielón y Loto 5, con historial.",
        "h1": "La Primera de Hoy",
        "intro": "Consulta los <strong>resultados de La Primera de hoy</strong> con sus números ganadores. Incluye <strong>La Primera Día</strong>, <strong>Primera Noche</strong>, <strong>El Quinielón</strong> y <strong>Loto 5</strong>.",
        "hora": "Día 12:00 PM y Noche 8:00 PM, todos los días (hora RD).",
    },
    {
        "slug": "la-suerte",
        "nombre": "La Suerte",
        "compania": "La Suerte",
        "title": "La Suerte de Hoy — Resultados y Números Ganadores",
        "desc": "Resultados de La Suerte Dominicana de hoy. Números ganadores de los sorteos de las 12:30 y las 6:00 PM, con historial de días anteriores.",
        "h1": "La Suerte de Hoy",
        "intro": "Consulta los <strong>resultados de La Suerte de hoy</strong> con sus números ganadores. La Suerte sortea a las <strong>12:30 PM</strong> y a las <strong>6:00 PM</strong> (hora RD).",
        "hora": "12:30 PM y 6:00 PM, todos los días (hora RD).",
    },
    {
        "slug": "leidsa",
        "nombre": "Leidsa",
        "compania": "Leidsa",
        "title": "Leidsa de Hoy — Resultados Quiniela, Loto y Pega 3 Más",
        "desc": "Resultados de Leidsa de hoy en República Dominicana. Números ganadores de Quiniela Leidsa, Loto Pool, Pega 3 Más, Súper Kino TV y Super Palé, con historial.",
        "h1": "Leidsa de Hoy",
        "intro": "Consulta los <strong>resultados de Leidsa de hoy</strong> con sus números ganadores. Incluye <strong>Quiniela Leidsa</strong>, <strong>Pega 3 Más</strong>, <strong>Loto Pool</strong>, <strong>Súper Kino TV</strong> y <strong>Super Palé</strong>.",
        "hora": "Lun–sáb 8:55 PM; domingo 3:55 PM (hora RD).",
    },
]

DIAS_HISTORIAL = 7

CSS = """
:root{--azul:#002a5c;--azul2:#0a5bbf;--rojo:#d90429;--bg:#f4f6fb;--card:#fff;--border:#e5eaf3;--txt:#0d1b33;--muted:#5b6b82;--grad:linear-gradient(135deg,#002a5c,#d90429)}
@media (prefers-color-scheme:dark){:root{--bg:#0b1220;--card:#121a2b;--border:#1e2a44;--txt:#e7edf8;--muted:#9aa9c3;--azul2:#6aa8ff;--rojo:#ff6b7d}}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--txt);font-family:'Archivo',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;line-height:1.55;-webkit-font-smoothing:antialiased}
.hero{position:relative;overflow:hidden;color:#fff;padding:34px 16px 40px;text-align:center;background:var(--azul)}
.hero::before{content:"";position:absolute;inset:-40%;background:radial-gradient(40% 60% at 15% 20%,rgba(239,35,60,.55),transparent 60%),radial-gradient(50% 70% at 85% 10%,rgba(10,91,191,.65),transparent 60%);filter:blur(30px)}
.hero>*{position:relative;z-index:1}
.crumb{font-size:.78rem;opacity:.85;margin-bottom:10px}
.crumb ol{list-style:none;display:flex;flex-wrap:wrap;justify-content:center;gap:6px}
.crumb li+li::before{content:"›";margin-right:6px;opacity:.7}
.crumb a{color:#fff;text-decoration:none}
.hero h1{font-size:2rem;font-weight:900;letter-spacing:-.03em;line-height:1.08}
.hero .fecha{margin-top:8px;font-size:.95rem;opacity:.92}
.hero .hora{display:inline-block;margin-top:14px;font-size:.8rem;background:rgba(255,255,255,.14);padding:6px 16px;border-radius:999px;border:1px solid rgba(255,255,255,.18);font-weight:600}
.wrap{max-width:900px;margin:0 auto;padding:22px 16px}
.intro{color:var(--muted);font-size:.95rem;line-height:1.65;margin-bottom:6px}
.upd{font-size:.8rem;color:var(--muted);margin-top:10px}
h2.sect{font-size:1.15rem;font-weight:800;margin:28px 0 14px;display:flex;align-items:center;gap:10px}
h2.sect .bar{width:5px;height:20px;border-radius:99px;background:var(--grad);flex:none}
.loteria-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}
.lot-card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:16px;box-shadow:0 1px 2px rgba(13,27,51,.04),0 2px 6px rgba(13,27,51,.04)}
.lot-card h3{font-weight:700;font-size:.95rem}
.lot-card .lot-meta{font-size:.76rem;color:var(--muted);margin-top:2px}
.lot-card .lot-meta .ant{color:var(--rojo);font-weight:600}
.lot-card .nums{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px}
.ball{min-width:36px;height:36px;padding:0 7px;display:inline-flex;align-items:center;justify-content:center;background:var(--bg);border:1px solid var(--border);border-radius:10px;font-weight:800;font-size:1rem;font-variant-numeric:tabular-nums}
.ball.gold{background:linear-gradient(180deg,#ffe08a,#f2b32e);color:#3d2800;border-color:#e6a800}
.tabla-wrap{overflow-x:auto;background:var(--card);border:1px solid var(--border);border-radius:16px}
table{width:100%;border-collapse:collapse;font-size:.88rem}
th,td{text-align:left;padding:10px 12px;border-bottom:1px solid var(--border);vertical-align:top}
th{font-size:.75rem;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}
tr:last-child td{border-bottom:0}
td a{color:var(--azul2);font-weight:600;text-decoration:none}
td.n{font-weight:800;font-variant-numeric:tabular-nums;letter-spacing:.03em}
@media(max-width:600px){table{font-size:.8rem}th,td{padding:9px 8px}}
.juegos{display:flex;flex-wrap:wrap;gap:8px}
.juegos li a{color:var(--azul2);text-decoration:none;font-weight:600}
.juegos li{list-style:none;font-size:.85rem;background:var(--card);border:1px solid var(--border);padding:6px 12px;border-radius:999px}
.faq details{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:14px 16px;margin-bottom:8px}
.faq summary{font-weight:700;cursor:pointer;font-size:.95rem}
.faq p{color:var(--muted);margin-top:8px;font-size:.92rem}
.otras{display:flex;flex-wrap:wrap;gap:8px;margin-top:6px}
.otras a{font-size:.82rem;font-weight:600;color:var(--azul2);text-decoration:none;background:var(--card);border:1px solid var(--border);padding:8px 14px;border-radius:999px}
.otras a:hover{border-color:var(--azul2)}
footer{text-align:center;color:var(--muted);font-size:.75rem;padding:26px 16px 24px;border-top:1px solid var(--border);margin-top:24px}
footer a{color:var(--azul2);font-weight:700}
@media(max-width:600px){.hero h1{font-size:1.55rem}.loteria-grid{grid-template-columns:1fr}}
"""

JS = """
(function(){
  var COMPANIA = %(compania)s, UPDATED = %(updated)s;
  var DIAS=['domingo','lunes','martes','miércoles','jueves','viernes','sábado'];
  var MESES=['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
  function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  function limpio(s){return String(s).replace(/\\s+/g,' ').trim();}
  function fecha(s){if(!s)return'';var p=s.split('-');var d=new Date(+p[0],p[1]-1,+p[2]);return DIAS[d.getDay()]+' '+d.getDate()+' de '+MESES[d.getMonth()];}
  fetch('../data/resultados.json?v='+Date.now()).then(function(r){return r.json();}).then(function(d){
    if(!d.updated || d.updated<=UPDATED) return;
    var js=(d.juegos||[]).filter(function(j){return j.compania===COMPANIA;});
    if(!js.length) return;
    var hoy=d.updated.slice(0,10);
    var grid=document.getElementById('grid');
    var orden={};[].forEach.call(grid.querySelectorAll('h3'),function(h,i){orden[h.textContent]=i;});
    function r(j){var x=orden[limpio(j.juego)];return x===undefined?99:x;}
    js.sort(function(a,b){return r(a)-r(b);});
    grid.innerHTML=js.map(function(j){
      var g=j.numeros.length<=4?' gold':'';
      var f=(j.fecha||'').slice(0,10);
      return '<article class="lot-card"><h3>'+esc(limpio(j.juego))+'</h3><div class="lot-meta">'+fecha(f)+(f&&f<hoy?' · <span class="ant">sorteo anterior</span>':'')+'</div><div class="nums">'+j.numeros.map(function(n){return '<span class="ball'+g+'">'+esc(n)+'</span>';}).join('')+'</div></article>';
    }).join('');
    var u=document.getElementById('upd'); if(u) u.textContent='Actualizado: '+d.fecha+' '+d.hora+' (hora RD)';
  }).catch(function(){});
})();
"""


def render_cards(juegos, hoy):
    cards = []
    for j in juegos:
        d = parse_fecha(j.get("fecha"))
        meta = fecha_larga(d, con_anio=False) if d else ""
        if d and d < hoy:
            meta += ' · <span class="ant">sorteo anterior</span>'
        ancla = re.sub(r"[^a-z0-9]+", "-", limpiar(j["juego"]).lower().replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u").replace("ñ","n")).strip("-")
        cards.append(
            f'<article class="lot-card" id="{ancla}">'
            f'<h3>{esc(limpiar(j["juego"]))}</h3>'
            f'<div class="lot-meta">{meta}</div>'
            f'<div class="nums">{balls_html(j["numeros"])}</div>'
            '</article>'
        )
    return "\n    ".join(cards)


def render_historial(compania, juegos_hoy, archivo, hoy):
    """Tabla con los sorteos de los últimos días (sin repetir los de las tarjetas de hoy)."""
    sorteos = archivo.get("sorteos", {})
    mostrados = {(limpiar(j["juego"]), (j.get("fecha") or "")[:10]) for j in juegos_hoy}
    limite = (hoy - datetime.timedelta(days=DIAS_HISTORIAL)).isoformat()
    filas = []
    for clave, lista in sorteos.items():
        comp, juego = clave.split("|", 1)
        if comp != compania:
            continue
        for s in lista:
            if s["fecha"] < limite or (juego, s["fecha"]) in mostrados:
                continue
            filas.append((s["fecha"], juego, s["numeros"]))
    if not filas:
        return ""
    orden = {j["juego"]: i for i, j in enumerate(ordenar_juegos(compania, [{"juego": f[1]} for f in filas]))}
    filas.sort(key=lambda f: (f[0], -orden.get(f[1], 0)), reverse=True)  # fecha desc, juego principal primero
    trs = []
    con_pagina = set(fechas_con_pagina(archivo))
    for fecha, juego, nums in filas[:60]:
        txt = esc(fecha_larga(parse_fecha(fecha), con_anio=False))
        celda = f'<a href="/resultados/{fecha}/">{txt}</a>' if fecha in con_pagina else txt
        trs.append(f'<tr><td>{celda}</td><td>{esc(juego)}</td>'
                   f'<td class="n">{esc(" - ".join(nums))}</td></tr>')
    return ('<div class="tabla-wrap"><table><thead><tr><th>Fecha</th><th>Sorteo</th><th>Números</th></tr></thead>'
            "<tbody>" + "".join(trs) + "</tbody></table></div>")


def faqs_para(l, juegos, upd):
    nombre = l["nombre"]
    faqs = []
    if juegos:
        j = juegos[0]
        d = parse_fecha(j.get("fecha"))
        cuando = f" del {fecha_larga(d)}" if d else ""
        faqs.append((
            f"¿Cuáles son los números ganadores de {nombre} hoy?",
            f"En el último sorteo de {limpiar(j['juego'])}{cuando} salieron los números "
            f"{' - '.join(j['numeros'])}. En esta página están los resultados de todos los juegos de {nombre}, "
            f"actualizados el {fecha_larga(upd.date())} a las {hora_12(upd)} (hora RD)."
        ))
    faqs.append((f"¿A qué hora juega {nombre}?", l["hora"] + " Ver todos los horarios en portaldominicana.net/horarios-loterias/."))
    if juegos:
        nombres = [limpiar(j["juego"]) for j in juegos]
        lista = nombres[0] if len(nombres) == 1 else ", ".join(nombres[:-1]) + " y " + nombres[-1]
        faqs.append((f"¿Qué juegos tiene {nombre}?",
                     f"En Portal Dominicano publicamos los resultados de {len(nombres)} juegos de {nombre}: {lista}."))
    faqs.append(("¿Cada cuánto se actualizan los resultados?",
                 "Los resultados se actualizan automáticamente varias veces al día, después de los sorteos. "
                 "En esta página también verás los resultados de los días anteriores."))
    faqs.append((f"¿Puedo comprar o jugar {nombre} en Portal Dominicano?",
                 "No. Portal Dominicano es un sitio informativo: no vendemos billetes ni jugadas. "
                 "Verifica siempre tus números con la fuente oficial antes de cobrar un premio."))
    return faqs


def render_pagina(l, resultados, archivo):
    upd = actualizado_rd(resultados)
    hoy = upd.date()
    juegos = ordenar_juegos(l["compania"], [j for j in resultados.get("juegos", [])
                                            if j.get("compania") == l["compania"]])
    url = f"{BASE}/{l['slug']}/"
    fecha_txt = fecha_larga(hoy)
    pref, _, suf = l["title"].partition(" — ")
    if juegos:
        p = juegos[0]
        if l["compania"] == "Anguila":
            p = max(juegos, key=lambda j: ((j.get("fecha") or "")[:10], minutos_juego(limpiar(j["juego"])) or 0))
        dp = parse_fecha(p.get("fecha")) or hoy
        title = titulo(f"{pref} {dp.day} de {MESES[dp.month - 1]}: {'-'.join(p['numeros'])}", suf, "Resultados")
    else:
        title = titulo(f"{pref}, {hoy.day} de {MESES[hoy.month - 1]} {hoy.year}", suf, "Resultados")

    cards = render_cards(juegos, hoy) if juegos else '<p class="intro">Sin resultados por ahora. Vuelve más tarde.</p>'
    historial = render_historial(l["compania"], juegos, archivo, hoy)
    faqs = faqs_para(l, juegos, upd)

    from generate_juegos import JUEGOS  # import tardío: generate_juegos importa este módulo
    pag_juego = {(c, g): slug for slug, _n, _h, claves in JUEGOS for c, g in claves}
    todos_juegos = " ".join(f'<a href="/{slug}/">{esc(n)}</a>' for slug, n, *_ in JUEGOS)
    lista_juegos = "".join(
        f'<li><a href="/{pag_juego[(j["compania"], limpiar(j["juego"]))]}/">{esc(limpiar(j["juego"]))}</a></li>'
        if (j["compania"], limpiar(j["juego"])) in pag_juego else f"<li>{esc(limpiar(j['juego']))}</li>"
        for j in juegos)
    otras = " ".join(f'<a href="../{o["slug"]}/">{esc(o["nombre"])}</a>' for o in LOTERIAS if o["slug"] != l["slug"])
    secciones = " ".join(f'<a href="../{s}/">{esc(n)}</a>' for s, n in SECCIONES)

    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage", "@id": url + "#webpage", "url": url,
                "name": f"{l['h1']} — Resultados del {fecha_txt}",
                "description": l["desc"], "inLanguage": "es-DO",
                "dateModified": upd.isoformat(timespec="seconds"),
                "isPartOf": {"@type": "WebSite", "@id": BASE + "/#website", "name": "Portal Dominicano", "url": BASE + "/"},
                "about": {"@type": "Thing", "name": l["nombre"]},
                "breadcrumb": {"@id": url + "#breadcrumb"},
            },
            {
                "@type": "BreadcrumbList", "@id": url + "#breadcrumb",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Portal Dominicano", "item": BASE + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Lotería de hoy", "item": BASE + "/#loteria"},
                    {"@type": "ListItem", "position": 3, "name": l["nombre"], "item": url},
                ],
            },
            {
                "@type": "FAQPage", "@id": url + "#faq",
                "mainEntity": [{"@type": "Question", "name": q,
                                "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs],
            },
        ],
    }
    ld_json = json.dumps(ld, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    faq_html = "\n    ".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in faqs)
    hist_html = ""
    if historial:
        hist_html = (f'<h2 class="sect"><span class="bar"></span> Resultados anteriores de {esc(l["nombre"])}</h2>\n'
                     f'  <p class="intro" style="margin-bottom:12px">Números ganadores de {esc(l["nombre"])} de los últimos días.</p>\n'
                     f"  {historial}")

    js = JS % {"compania": json.dumps(l["compania"]), "updated": json.dumps(resultados.get("updated", ""))}

    return f"""<!DOCTYPE html>
<html lang="es-DO">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(l['desc'])}">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(l['desc'])}">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="Portal Dominicano">
<meta property="og:locale" content="es_DO">
<meta property="og:image" content="{BASE}/img/og-portal-dominicano.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#002a5c">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta name="geo.region" content="DO">
<link rel="icon" type="image/png" href="../img/icon-192.png">
<link rel="manifest" href="../manifest.json">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;700;800;900&display=swap"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;700;800;900&display=swap" media="print" onload="this.media='all'"><noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;700;800;900&display=swap"></noscript>
<script type="application/ld+json">{ld_json}</script>
<style>{CSS}</style>
</head>
<body>
<header class="hero">
  <nav class="crumb" aria-label="Ruta de navegación"><ol>
    <li><a href="../">Portal Dominicano</a></li>
    <li><a href="../#loteria">Lotería de hoy</a></li>
    <li aria-current="page">{esc(l['nombre'])}</li>
  </ol></nav>
  <h1>{esc(l['h1'])}</h1>
  <p class="fecha">Resultados del {esc(fecha_txt)}</p>
  <div class="hora">🕐 {esc(l['hora'])}</div>
</header>
<main class="wrap">
  <p class="intro">{l['intro']}</p>
  <p class="upd" id="upd">Actualizado: {upd.strftime('%d/%m/%Y')} {hora_12(upd)} (hora RD)</p>

  <h2 class="sect"><span class="bar"></span> Resultados de {esc(l['nombre'])} de hoy</h2>
  <div class="loteria-grid" id="grid">
    {cards}
  </div>

  {hist_html}

  <p class="intro" style="margin-top:10px"><a href="/resultados/" style="color:var(--azul2);font-weight:700">Ver resultados de días anteriores por fecha ›</a></p>

  <h2 class="sect"><span class="bar"></span> Juegos de {esc(l['nombre'])}</h2>
  <ul class="juegos">{lista_juegos}</ul>

  <h2 class="sect"><span class="bar"></span> Preguntas frecuentes sobre {esc(l['nombre'])}</h2>
  <div class="faq">
    {faq_html}
  </div>

  <h2 class="sect"><span class="bar"></span> Otras loterías dominicanas</h2>
  <nav class="otras" aria-label="Otras loterías">{otras}</nav>

  <h2 class="sect"><span class="bar"></span> Resultados por juego</h2>
  <nav class="otras" aria-label="Juegos">{todos_juegos}</nav>

  <h2 class="sect"><span class="bar"></span> Más en Portal Dominicano</h2>
  <nav class="otras" aria-label="Secciones">{secciones}</nav>
</main>
<footer>
  <p>Portal informativo. No vendemos sorteos. Verifica siempre con la fuente oficial.</p>
  <p><a href="../">Portal Dominicano</a> · Datos: <a href="https://loteriasdominicanas.com" rel="noopener">loteriasdominicanas.com</a></p>
</footer>
<script>{js}</script>
</body>
</html>
"""


def main():
    resultados = cargar_json("resultados.json", {}) or {}
    archivo = cargar_json("archivo.json", {}) or {}
    for l in LOTERIAS:
        html = render_pagina(l, resultados, archivo)
        d = os.path.join(ROOT, l["slug"])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)
        print(f"OK: {l['slug']}/")


if __name__ == "__main__":
    main()
