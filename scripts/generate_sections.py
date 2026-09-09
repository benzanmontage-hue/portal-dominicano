#!/usr/bin/env python3
"""Generar páginas SEO de las secciones (mlb, traductor, tiempo, divisas, economía,
noticias, eventos) + actualizar sitemap a 15 URLs."""

import json
import os

BASE = "https://portaldominicana.net"

# Cada página: slug, keywords, title/desc/h1/intro, y qué data local renderizar
PAGINAS = [
    {
        "slug": "mlb",
        "title": "MLB Hoy — Marcadores y Resultados en Vivo RD",
        "desc": "Marcadores de MLB de hoy en vivo. Resultados de béisbol, juegos de hoy y equipos con peloteros dominicanos. Actualizado en vivo.",
        "h1": "MLB — Marcadores de Hoy",
        "intro": "Consulta los <strong>marcadores de MLB de hoy</strong> en vivo. Resultados de las Grandes Ligas, juegos del día y equipos con peloteros dominicanos.",
        "data": None,
    },
    {
        "slug": "traductor",
        "title": "Traductor Español Inglés — Gratis y Rápido",
        "desc": "Traductor español-inglés gratis en línea. Traduce palabras y frases al instante entre español e inglés. Sin registro.",
        "h1": "Traductor Español ↔ Inglés",
        "intro": "Traduce <strong>español a inglés</strong> (y viceversa) gratis y al instante. Escribe tu texto y obtén la traducción.",
        "data": None,
    },
    {
        "slug": "tiempo-santo-domingo",
        "title": "Clima Santo Domingo Hoy — Tiempo en RD",
        "desc": "Clima de Santo Domingo y las principales ciudades de República Dominicana hoy. Temperatura, humedad y pronóstico actualizado.",
        "h1": "Clima en Santo Domingo y RD",
        "intro": "Consulta el <strong>clima de Santo Domingo</strong> y las principales ciudades de República Dominicana: temperatura actual, humedad, viento y pronóstico.",
        "data": None,
    },
    {
        "slug": "dolar-hoy",
        "title": "Precio del Dólar Hoy en RD — Tasa de Cambio",
        "desc": "Precio del dólar hoy en República Dominicana. Tasa de cambio USD a DOP, euro a peso dominicano y más monedas. Actualizado.",
        "h1": "Precio del Dólar Hoy en RD",
        "intro": "Consulta el <strong>precio del dólar hoy</strong> en República Dominicana. Tasa de cambio del dólar (USD) a peso dominicano (DOP), euro y más monedas.",
        "data": "divisas",
    },
    {
        "slug": "economia-rd",
        "title": "Economía de República Dominicana — Indicadores",
        "desc": "Indicadores económicos de República Dominicana: desempleo, inflación, PIB per cápita y deuda externa. Datos actualizados.",
        "h1": "Economía de República Dominicana",
        "intro": "Consulta los <strong>indicadores económicos de República Dominicana</strong>: desempleo, inflación, PIB per cápita y deuda externa.",
        "data": "economia",
    },
    {
        "slug": "noticias-rd",
        "title": "Noticias de República Dominicana — Hoy",
        "desc": "Noticias de República Dominicana de hoy. Últimas noticias de Santo Domingo y todo el país, actualizadas en tiempo real.",
        "h1": "Noticias de República Dominicana",
        "intro": "Consulta las <strong>noticias de República Dominicana de hoy</strong>. Últimas noticias de Santo Domingo y todo el país.",
        "data": "noticias",
    },
    {
        "slug": "eventos-rd",
        "title": "Eventos y Conciertos en República Dominicana",
        "desc": "Eventos y conciertos próximos en República Dominicana. Conciertos, festivales y espectáculos en Santo Domingo y todo el país.",
        "h1": "Eventos y Conciertos en RD",
        "intro": "Descubre los <strong>eventos y conciertos próximos</strong> en República Dominicana: conciertos, festivales y espectáculos en Santo Domingo y todo el país.",
        "data": "eventos",
    },
]


def tiempo_relativo(fecha_str):
    # la fecha viene en inglés "Thu, 03 Sep 2026 15:26:19 GMT" — convertimos aprox
    import datetime
    try:
        from email.utils import parsedate_to_datetime
        d = parsedate_to_datetime(fecha_str)
    except Exception:
        return ""
    diff = (datetime.datetime.now(datetime.timezone.utc) - d).total_seconds()
    if diff < 3600:
        return "hace " + str(int(diff / 60)) + " min"
    if diff < 86400:
        return "hace " + str(int(diff / 3600)) + " h"
    return "hace " + str(int(diff / 86400)) + " días"


def render_data_html(data_type):
    """Renderizar el contenido de una sección desde data/*.json (estático, indexable)."""
    path = "/opt/data/home/portal-dominicano/data/" + data_type + ".json"
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception:
        return '<p style="color:var(--muted)">Datos no disponibles por ahora.</p>'

    if data_type == "divisas":
        items = d.get("conversiones", [])
        cards = []
        for c in items:
            cards.append(
                '<div class="item-card"><span class="flag">' + c.get("bandera", "") + '</span>'
                '<div><div class="item-tit">' + c.get("moneda", "") + '</div>'
                '<div class="item-val">' + c.get("texto", "") + '</div></div></div>'
            )
        return '<div class="grid">' + "".join(cards) + "</div>"

    if data_type == "economia":
        inds = d.get("indicadores", [])
        cards = []
        for i in inds:
            ultimo = i.get("ultimo", {})
            cards.append(
                '<div class="item-card"><div class="item-tit">' + i.get("nombre", "") + '</div>'
                '<div class="item-val">' + str(ultimo.get("valor", "")) + " " + i.get("unidad", "") + '</div>'
                '<div class="item-sub">Año ' + str(ultimo.get("año", "")) + "</div></div>"
            )
        return '<div class="grid">' + "".join(cards) + "</div>"

    if data_type == "noticias":
        noticias = d.get("noticias", [])[:10]
        items = []
        for n in noticias:
            img = n.get("imagen", "")
            thumb = ('<img class="n-img" src="' + img + '" alt="" loading="lazy" referrerpolicy="no-referrer">') if img else ""
            items.append(
                '<a class="news-item" href="' + n.get("enlace", "#") + '" target="_blank" rel="noopener">'
                + thumb + '<div><div class="item-tit">' + n.get("titulo", "") + "</div>"
                '<div class="item-sub">' + n.get("fuente", "") + " · " + tiempo_relativo(n.get("fecha", "")) + "</div></div></a>"
            )
        return '<div class="list">' + "".join(items) + "</div>"

    if data_type == "eventos":
        eventos = d.get("eventos", [])[:12]
        items = []
        for e in eventos:
            items.append(
                '<a class="news-item" href="' + e.get("enlace", "#") + '" target="_blank" rel="noopener">'
                '<div><div class="item-tit">🎪 ' + e.get("titulo", "") + "</div>"
                '<div class="item-sub">' + e.get("fuente", "") + "</div></div></a>"
            )
        return '<div class="list">' + "".join(items) + "</div>"

    return ""


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
{{"@context":"https://schema.org","@type":"WebPage","name":"{h1}","url":"{base}/{slug}/","inLanguage":"es-DO","isPartOf":{{"@type":"WebSite","name":"Portal Dominicano","url":"{base}/"}}}}
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
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}}
.item-card{{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:16px;box-shadow:0 1px 2px rgba(13,27,51,.04),0 2px 6px rgba(13,27,51,.04)}}
.item-card .flag{{font-size:1.4rem;display:block;margin-bottom:6px}}
.item-card .item-tit{{font-weight:700;font-size:.9rem;color:var(--muted)}}
.item-card .item-val{{font-weight:800;font-size:1.15rem;margin-top:2px}}
.item-card .item-sub{{color:var(--muted);font-size:.76rem;margin-top:2px}}
.list{{display:flex;flex-direction:column;gap:8px}}
.news-item{{display:flex;gap:12px;align-items:center;background:var(--card);border:1px solid var(--border);border-radius:14px;padding:13px 15px;text-decoration:none;color:var(--txt);transition:transform .15s}}
.news-item:hover{{transform:translateX(4px)}}
.news-item .item-tit{{font-weight:600;font-size:.92rem;line-height:1.4}}
.news-item .item-sub{{color:var(--muted);font-size:.76rem;margin-top:4px}}
.news-item .n-img{{width:72px;height:54px;min-width:72px;border-radius:9px;object-fit:cover;border:1px solid var(--border)}}
.otras{{display:flex;flex-wrap:wrap;gap:8px;margin-top:6px}}
.otras a{{font-size:.82rem;font-weight:600;color:var(--azul2);text-decoration:none;background:var(--card);border:1px solid var(--border);padding:8px 14px;border-radius:999px;transition:border-color .15s}}
.otras a:hover{{border-color:var(--azul2)}}
footer{{text-align:center;color:var(--muted);font-size:.75rem;padding:26px 16px 24px;border-top:1px solid var(--border);margin-top:24px}}
footer a{{color:var(--azul2);font-weight:700}}
@media(max-width:600px){{.hero h1{{font-size:1.5rem}}.grid{{grid-template-columns:1fr 1fr}}}}
</style>
</head>
<body>
<div class="hero">
  <div class="crumb"><a href="{base}/">← Portal Dominicano</a></div>
  <h1>{h1}</h1>
</div>
<div class="wrap">
  <p class="intro">{intro}</p>

  <h2 class="sect"><span class="bar"></span> Hoy</h2>
  {contenido}

  <h2 class="sect"><span class="bar"></span> Todo el portal</h2>
  <div class="otras">{otras}</div>
</div>
<footer>
  <p>Portal informativo. Verifica siempre con la fuente oficial.</p>
  <p><a href="{base}/">Portal Dominicano</a> · República Dominicana</p>
</footer>
</body>
</html>
"""


def main():
    base_dir = "/opt/data/home/portal-dominicano"
    slugs = []
    # para el bloque "otras" enlazamos a las 7 loterías + las otras secciones
    todas = [p["slug"] for p in PAGINAS] + [
        "loteria-nacional", "loteria-real", "anguila", "loteka", "la-primera", "la-suerte", "leidsa"
    ]
    nombres = {
        "mlb": "MLB", "traductor": "Traductor", "tiempo-santo-domingo": "Clima",
        "dolar-hoy": "Dólar hoy", "economia-rd": "Economía", "noticias-rd": "Noticias",
        "eventos-rd": "Eventos",
        "loteria-nacional": "Lotería Nacional", "loteria-real": "Lotería Real",
        "anguila": "Anguila", "loteka": "Loteka", "la-primera": "La Primera",
        "la-suerte": "La Suerte", "leidsa": "Leidsa",
    }

    for p in PAGINAS:
        links = []
        for s in todas:
            if s != p["slug"]:
                links.append('<a href="../' + s + '/">' + nombres.get(s, s) + "</a>")
        otras = " ".join(links)
        contenido = render_data_html(p["data"]) if p["data"] else (
            '<p style="color:var(--muted)">Contenido en vivo disponible en la '
            '<a href="{base}/" style="color:var(--azul2);font-weight:700">página principal</a> '
            'del Portal Dominicano.</p>'.replace("{base}", BASE)
        )
        html = TEMPLATE.format(
            base=BASE, slug=p["slug"], title=p["title"], desc=p["desc"],
            h1=p["h1"], intro=p["intro"], contenido=contenido, otras=otras,
        )
        d = os.path.join(base_dir, p["slug"])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)
        slugs.append(p["slug"])
        print(f"OK: {p['slug']}/")

    # sitemap completo: home + 7 loterías + 7 secciones = 15 URLs
    loterias = ["loteria-nacional", "loteria-real", "anguila", "loteka", "la-primera", "la-suerte", "leidsa"]
    todos = ["home"] + loterias + slugs
    urls = []
    for s in todos:
        loc = BASE + "/" if s == "home" else BASE + "/" + s + "/"
        prio = "1.0" if s == "home" else "0.8"
        urls.append("  <url>\n    <loc>" + loc + "</loc>\n    <lastmod>2026-09-09</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>" + prio + "</priority>\n  </url>")
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>\n"
    with open(os.path.join(base_dir, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap)
    print("sitemap actualizado:", len(todos), "URLs")


if __name__ == "__main__":
    main()
