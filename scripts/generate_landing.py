#!/usr/bin/env python3
"""Generar páginas landing SEO por lotería (7 páginas) + actualizar sitemap."""
import json

LOTERIAS = [
    {
        "slug": "loteria-nacional",
        "nombre": "Lotería Nacional",
        "compania": "Nacional",
        "title": "Lotería Nacional de Hoy — Resultados y Números Ganadores",
        "desc": "Resultados de la Lotería Nacional de hoy en República Dominicana. Números ganadores de la quiniela actualizados en vivo. Consulta Gana Más, Juega + Pega + y Billetes Domingo.",
        "h1": "Lotería Nacional de Hoy",
        "intro": "Consulta los <strong>resultados de la Lotería Nacional de hoy</strong> con sus números ganadores actualizados en vivo. La Lotería Nacional Dominicana sortea todos los días e incluye la <strong>Quiniela</strong> (3 pares de dos cifras), <strong>Gana Más</strong>, <strong>Juega + Pega +</strong> y <strong>Billetes Domingo</strong>.",
        "hora": "Todos los días a las 8:50 PM (hora RD).",
    },
    {
        "slug": "loteria-real",
        "nombre": "Lotería Real",
        "compania": "Loteria Real",
        "title": "Lotería Real de Hoy — Resultados y Quiniela Real",
        "desc": "Resultados de la Lotería Real de hoy en República Dominicana. Números ganadores de la Quiniela Real, Loto Real y más, actualizados en vivo.",
        "h1": "Lotería Real de Hoy",
        "intro": "Consulta los <strong>resultados de la Lotería Real de hoy</strong> con sus números ganadores en vivo. Incluye <strong>Lotería Real Noche</strong>, <strong>Quiniela Real</strong>, <strong>Loto Real</strong>, <strong>Loto Pool</strong> y más sorteos.",
        "hora": "Sorteos diarios, incluyendo Lotería Real Noche.",
    },
    {
        "slug": "anguila",
        "nombre": "Anguila",
        "compania": "Anguila",
        "title": "Lotería Anguila de Hoy — Resultados y Números Ganadores",
        "desc": "Resultados de la Lotería Anguila de hoy en República Dominicana. Todos los sorteos horarios (10:00 AM a 10:00 PM) con sus números ganadores actualizados en vivo.",
        "h1": "Lotería Anguila de Hoy",
        "intro": "Consulta los <strong>resultados de la Lotería Anguila de hoy</strong> con todos sus sorteos horarios. Anguila sortea varias veces al día, desde las <strong>8:00 AM hasta las 10:00 PM</strong>, incluyendo <strong>La Cuarteta</strong>.",
        "hora": "Sorteos horarios desde 8:00 AM hasta 10:00 PM.",
    },
    {
        "slug": "loteka",
        "nombre": "Loteka",
        "compania": "Loteka",
        "title": "Loteka de Hoy — Resultados y Quiniela Loteka",
        "desc": "Resultados de Loteka de hoy en República Dominicana. Números ganadores de la Quiniela Loteka, MegaLotto, Mega Chances y más, en vivo.",
        "h1": "Loteka de Hoy",
        "intro": "Consulta los <strong>resultados de Loteka de hoy</strong> con sus números ganadores en vivo. Incluye <strong>Quiniela Loteka</strong>, <strong>MegaLotto</strong>, <strong>Mega Chances</strong>, <strong>Toca 3</strong> y <strong>MC Repartidera</strong>.",
        "hora": "Sorteos diarios.",
    },
    {
        "slug": "la-primera",
        "nombre": "La Primera",
        "compania": "La Primera",
        "title": "La Primera de Hoy — Resultados y Números Ganadores",
        "desc": "Resultados de La Primera de hoy en República Dominicana. Números ganadores de La Primera Día, Primera Noche y El Quinielón, en vivo.",
        "h1": "La Primera de Hoy",
        "intro": "Consulta los <strong>resultados de La Primera de hoy</strong> con sus números ganadores en vivo. Incluye <strong>La Primera Día</strong>, <strong>Primera Noche</strong>, <strong>El Quinielón</strong> y <strong>Loto 5</strong>.",
        "hora": "Sorteos de día y noche.",
    },
    {
        "slug": "la-suerte",
        "nombre": "La Suerte",
        "compania": "La Suerte",
        "title": "La Suerte de Hoy — Resultados y Números Ganadores",
        "desc": "Resultados de La Suerte de hoy en República Dominicana. Números ganadores de los sorteos 12:30 y 18:00, en vivo.",
        "h1": "La Suerte de Hoy",
        "intro": "Consulta los <strong>resultados de La Suerte de hoy</strong> con sus números ganadores en vivo. La Suerte sortea a las <strong>12:30</strong> y a las <strong>18:00</strong> (hora RD).",
        "hora": "Sorteos a las 12:30 y 18:00.",
    },
    {
        "slug": "leidsa",
        "nombre": "Leidsa",
        "compania": "Leidsa",
        "title": "Leidsa de Hoy — Resultados Quiniela, Loto y Pega 3 Más",
        "desc": "Resultados de Leidsa de hoy en República Dominicana. Números ganadores de Quiniela Leidsa, Loto Pool, Pega 3 Más, Súper Kino TV y Super Palé, en vivo.",
        "h1": "Leidsa de Hoy",
        "intro": "Consulta los <strong>resultados de Leidsa de hoy</strong> con sus números ganadores en vivo. Incluye <strong>Quiniela Leidsa</strong>, <strong>Pega 3 Más</strong>, <strong>Loto Pool</strong>, <strong>Súper Kino TV</strong> y <strong>Super Palé</strong>.",
        "hora": "Sorteos a las 8:55 PM (hora RD).",
    },
]

BASE = "https://portaldominicana.net"

TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{base}/{slug}/">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:url" content="{base}/{slug}/">
<meta property="og:site_name" content="Portal Dominicano">
<meta property="og:locale" content="es_DO">
<meta property="og:image" content="{base}/img/og-portal-dominicano.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#002a5c">
<meta name="robots" content="index,follow">
<link rel="icon" type="image/png" href="../img/icon-192.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"WebPage","name":"{nombre} — Resultados de Hoy","url":"{base}/{slug}/","inLanguage":"es-DO","isPartOf":{{"@type":"WebSite","name":"Portal Dominicano","url":"{base}/"}}}}
</script>
<style>
:root{{--azul:#002a5c;--azul2:#0a5bbf;--rojo:#d90429;--bg:#f4f6fb;--card:#fff;--border:#e5eaf3;--border2:#d8e0ee;--txt:#0d1b33;--muted:#64748b;--gold:#f5b942;--shadow:0 2px 4px rgba(13,27,51,.04),0 8px 20px rgba(13,27,51,.07);--grad:linear-gradient(135deg,#002a5c,#d90429)}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0b1220;--card:#121a2b;--border:#1e2a44;--border2:#2a3a5c;--txt:#e7edf8;--muted:#8b9bb8}}}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--txt);font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;line-height:1.55;-webkit-font-smoothing:antialiased}}
.hero{{position:relative;overflow:hidden;color:#fff;padding:40px 16px 44px;text-align:center;background:var(--azul)}}
.hero::before{{content:"";position:absolute;inset:-40%;background:radial-gradient(40% 60% at 15% 20%,rgba(239,35,60,.55),transparent 60%),radial-gradient(50% 70% at 85% 10%,rgba(10,91,191,.65),transparent 60%);filter:blur(30px)}}
.hero>*{{position:relative;z-index:1}}
.hero .crumb{{font-size:.78rem;opacity:.8;margin-bottom:8px}}
.hero .crumb a{{color:#fff;text-decoration:none}}
.hero h1{{font-size:2rem;font-weight:900;letter-spacing:-.03em;line-height:1.05}}
.hero .hora{{display:inline-block;margin-top:14px;font-size:.8rem;background:rgba(255,255,255,.14);padding:6px 16px;border-radius:999px;backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,.18);font-weight:600}}
.wrap{{max-width:900px;margin:0 auto;padding:22px 16px}}
.intro{{color:var(--muted);font-size:.95rem;line-height:1.65;margin-bottom:6px}}
h2.sect{{font-size:1.15rem;font-weight:800;margin:26px 0 14px;display:flex;align-items:center;gap:10px}}
h2.sect .bar{{width:5px;height:20px;border-radius:99px;background:var(--grad)}}
.loteria-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}}
.lot-card{{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:16px;box-shadow:0 1px 2px rgba(13,27,51,.04),0 2px 6px rgba(13,27,51,.04);transition:transform .18s,box-shadow .18s}}
.lot-card:hover{{transform:translateY(-3px);box-shadow:var(--shadow)}}
.lot-card .game{{font-weight:700;font-size:.95rem}}
.lot-card .nums{{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px}}
.ball{{min-width:36px;height:36px;padding:0 7px;display:inline-flex;align-items:center;justify-content:center;background:var(--bg);border:1px solid var(--border);border-radius:10px;font-weight:800;font-size:1rem;font-variant-numeric:tabular-nums}}
.ball.gold{{background:linear-gradient(180deg,#ffe08a,#f2b32e);color:#3d2800;border-color:#e6a800}}
.otras{{display:flex;flex-wrap:wrap;gap:8px;margin-top:6px}}
.otras a{{font-size:.82rem;font-weight:600;color:var(--azul2);text-decoration:none;background:var(--card);border:1px solid var(--border);padding:8px 14px;border-radius:999px;transition:border-color .15s}}
.otras a:hover{{border-color:var(--azul2)}}
footer{{text-align:center;color:var(--muted);font-size:.75rem;padding:26px 16px 24px;border-top:1px solid var(--border);margin-top:24px}}
footer a{{color:var(--azul2);font-weight:700}}
@media(max-width:600px){{.hero h1{{font-size:1.5rem}}.loteria-grid{{grid-template-columns:1fr 1fr}}}}
</style>
</head>
<body>
<div class="hero">
  <div class="crumb"><a href="{base}/">← Portal Dominicano</a></div>
  <h1>{h1}</h1>
  <div class="hora">🕐 {hora}</div>
</div>
<div class="wrap">
  <p class="intro">{intro}</p>

  <h2 class="sect"><span class="bar"></span> Resultados de hoy</h2>
  <div class="loteria-grid" id="grid"><p style="color:var(--muted)">Cargando resultados…</p></div>

  <h2 class="sect"><span class="bar"></span> Otras loterías</h2>
  <div class="otras">{otras}</div>
</div>
<footer>
  <p>Portal informativo. No vendemos sorteos. Verifica siempre con la fuente oficial.</p>
  <p><a href="{base}/">Portal Dominicano</a> · Datos: <a href="https://loteriasdominicanas.com" rel="noopener">loteriasdominicanas.com</a></p>
</footer>
<script>
var COMPANIA = "{compania}";
fetch('../data/resultados.json?v=' + Date.now())
  .then(function(r){{ return r.json(); }})
  .then(function(d){{
    var grid = document.getElementById('grid');
    var juegos = (d.juegos || []).filter(function(j){{ return j.compania === COMPANIA; }});
    if (!juegos.length){{ grid.innerHTML = '<p style="color:var(--muted)">Sin resultados por ahora.</p>'; return; }}
    grid.innerHTML = '';
    juegos.forEach(function(j){{
      var c = document.createElement('div');
      c.className = 'lot-card';
      var balls = j.numeros.map(function(n){{ return '<span class="ball'+(j.numeros.length<=4?' gold':'')+'">'+n+'</span>'; }}).join('');
      c.innerHTML = '<div class="game">'+j.juego+'</div><div class="nums">'+balls+'</div>';
      grid.appendChild(c);
    }});
  }})
  .catch(function(){{ document.getElementById('grid').innerHTML = '<p style="color:var(--muted)">Error cargando resultados.</p>'; }});
</script>
</body>
</html>
"""


def main():
    import os
    base_dir = "/opt/data/home/portal-dominicano"
    slugs = []

    for l in LOTERIAS:
        links = []
        for o in LOTERIAS:
            if o["slug"] != l["slug"]:
                links.append('<a href="../' + o["slug"] + '/">' + o["nombre"] + '</a>')
        otras = " ".join(links)
        html = TEMPLATE.format(
            base=BASE, slug=l["slug"], nombre=l["nombre"], compania=l["compania"],
            title=l["title"], desc=l["desc"], h1=l["h1"], intro=l["intro"],
            hora=l["hora"], otras=otras,
        )
        d = os.path.join(base_dir, l["slug"])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)
        slugs.append(l["slug"])
        print(f"OK: {l['slug']}/")

    # actualizar sitemap
    urls = ["".join(['  <url>\n    <loc>', BASE, '/</loc>\n    <lastmod>2026-09-08</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>1.0</priority>\n  </url>'])]
    for s in slugs:
        urls.append("".join(['  <url>\n    <loc>', BASE, '/', s, '/</loc>\n    <lastmod>2026-09-08</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>0.8</priority>\n  </url>']))
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>\n"
    with open(os.path.join(base_dir, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap)
    print("sitemap actualizado:", len(slugs) + 1, "URLs")


if __name__ == "__main__":
    main()
