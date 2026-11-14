#!/usr/bin/env python3
"""Generar páginas SEO de las secciones (mlb, traductor, tiempo, divisas, economía,
noticias, eventos). El sitemap lo genera scripts/build_sitemap.py."""

import datetime
import json
import os
from html import escape as esc

# Raíz del repositorio (funciona en GitHub Actions y en cualquier servidor)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
    path = os.path.join(ROOT, "data", data_type + ".json")
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
            ultimo = i.get("ultimo") or {}
            if not ultimo:  # la fuente no trajo dato para este indicador
                continue
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
            thumb = ('<img class="n-img" src="' + esc(img) + '" alt="" width="72" height="54" loading="lazy" referrerpolicy="no-referrer">') if img else ""
            items.append(
                '<a class="news-item" href="' + esc(n.get("enlace", "#")) + '" target="_blank" rel="noopener">'
                + thumb + '<div><div class="item-tit">' + esc(n.get("titulo", "")) + "</div>"
                '<div class="item-sub">' + esc(n.get("fuente", "")) + " · " + tiempo_relativo(n.get("fecha", "")) + "</div></div></a>"
            )
        return '<div class="list">' + "".join(items) + "</div>"

    if data_type == "eventos":
        eventos = d.get("eventos", [])[:12]
        items = []
        for e in eventos:
            items.append(
                '<a class="news-item" href="' + esc(e.get("enlace", "#")) + '" target="_blank" rel="noopener">'
                '<div><div class="item-tit">🎪 ' + esc(e.get("titulo", "")) + "</div>"
                '<div class="item-sub">' + esc(e.get("fuente", "")) + "</div></div></a>"
            )
        return '<div class="list">' + "".join(items) + "</div>"

    return ""


MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
         "octubre", "noviembre", "diciembre"]


def dolar_titulos_e_historial():
    """Título con fecha y valor; guarda y muestra el historial diario (data/divisas_historial.json)."""
    try:
        d = json.load(open(os.path.join(ROOT, "data", "divisas.json"), encoding="utf-8"))
    except Exception:
        d = {}
    usd = d.get("dop_por_usd")
    eur = next((c.get("valor") for c in d.get("conversiones", []) if c.get("codigo") == "EUR" and c.get("a") == "DOP"), None)
    fecha = (d.get("updated") or "")[:10]
    hist_path = os.path.join(ROOT, "data", "divisas_historial.json")
    try:
        hist = json.load(open(hist_path, encoding="utf-8"))
    except Exception:
        hist = {}
    if not (usd and fecha):
        return "Precio del Dólar Hoy en RD — Tasa de Cambio", "Precio del Dólar Hoy en RD", ""
    hist[fecha] = {"usd": usd, "eur": eur}
    hist = dict(sorted(hist.items())[-400:])
    with open(hist_path, "w", encoding="utf-8") as f:
        json.dump(hist, f, ensure_ascii=False, indent=1)
    dt = datetime.date.fromisoformat(fecha)
    cuando = f"{dt.day} de {MESES[dt.month - 1]}"
    title = f"Dólar Hoy {cuando}: RD${usd:.2f} — Tasa de Cambio RD"
    h1 = f"Precio del Dólar Hoy en RD: RD${usd:.2f}"
    td = '<td style="padding:10px;border-top:1px solid var(--border)">'
    filas = []
    for f, v in sorted(hist.items(), reverse=True)[:30]:
        df = datetime.date.fromisoformat(f)
        e = f"RD${v['eur']:.2f}" if v.get("eur") else "—"
        filas.append(f"<tr>{td}{df.day} de {MESES[df.month - 1]} {df.year}</td>{td}RD${v['usd']:.2f}</td>{td}{e}</td></tr>")
    th = '<th style="text-align:left;padding:10px">'
    extra = (f'<p class="intro" style="margin-top:14px">Hoy, {cuando}, un dólar estadounidense equivale a <strong>RD${usd:.2f}</strong>'
             + (f' y un euro a <strong>RD${eur:.2f}</strong>' if eur else '')
             + '. Es una tasa de referencia: los bancos y casas de cambio aplican su propio precio de compra y venta.</p>'
             '<h2 class="sect"><span class="bar"></span> Historial del dólar</h2>'
             '<div style="overflow-x:auto;background:var(--card);border:1px solid var(--border);border-radius:14px">'
             f'<table style="width:100%;border-collapse:collapse"><thead><tr>{th}Fecha</th>{th}Dólar</th>{th}Euro</th></tr></thead><tbody>'
             + "".join(filas) + "</tbody></table></div>")
    conv = "".join(f"<tr>{td}US${n:,}</td>{td}RD${n * usd:,.2f}</td>{td}RD${n * eur:,.2f}</td></tr>" for n in (1, 10, 20, 50, 100, 500, 1000)) if eur else ""
    if conv:
        extra += ('<h2 class="sect"><span class="bar"></span> Convertir dólares y euros a pesos</h2>'
                  '<div style="overflow-x:auto;background:var(--card);border:1px solid var(--border);border-radius:14px">'
                  f'<table style="width:100%;border-collapse:collapse"><thead><tr>{th}Cantidad</th>{th}En dólares → pesos</th>{th}En euros → pesos</th></tr></thead><tbody>'
                  + conv + "</tbody></table></div>")
    faqs = [(f"¿A cuánto está el dólar hoy en República Dominicana?",
             f"Hoy, {cuando}, la tasa de referencia es RD${usd:.2f} por cada dólar estadounidense."),
            ("¿Cuánto son 100 dólares en pesos dominicanos?", f"Con la tasa de hoy, 100 dólares son unos RD${100 * usd:,.2f}."),
            ("¿Por qué el banco me da otro precio?",
             "Los bancos y casas de cambio compran el dólar un poco más barato y lo venden un poco más caro que la tasa de referencia. Consulta la tasa de compra y venta de tu banco antes de cambiar.")]
    extra += '<h2 class="sect"><span class="bar"></span> Preguntas frecuentes</h2>' + "".join(
        f'<details style="background:var(--card);border:1px solid var(--border);border-radius:14px;padding:14px 16px;margin-bottom:8px">'
        f'<summary style="font-weight:700;cursor:pointer">{q}</summary><p style="color:var(--muted);margin-top:8px">{a}</p></details>' for q, a in faqs)
    return title, h1, extra


TEMPLATE = """<!DOCTYPE html>
<html lang="es-DO">
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
<meta name="robots" content="{robots}">
<link rel="icon" type="image/png" href="../img/icon-192.png">
<link rel="ai-catalog" href="../ai-catalog.json">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;700;800;900&display=swap"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;700;800;900&display=swap" media="print" onload="this.media='all'"><noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;700;800;900&display=swap"></noscript>
<script type="application/ld+json">
{{"@context":"https://schema.org","@graph":[{{"@type":"WebPage","name":"{h1}","url":"{base}/{slug}/","inLanguage":"es-DO","isPartOf":{{"@type":"WebSite","@id":"{base}/#website","name":"Portal Dominicano","url":"{base}/"}},"breadcrumb":{{"@id":"{base}/{slug}/#breadcrumb"}}}},{{"@type":"BreadcrumbList","@id":"{base}/{slug}/#breadcrumb","itemListElement":[{{"@type":"ListItem","position":1,"name":"Portal Dominicano","item":"{base}/"}},{{"@type":"ListItem","position":2,"name":"{h1}","item":"{base}/{slug}/"}}]}}]}}
</script>
<style>
:root{{--azul:#002a5c;--azul2:#0a5bbf;--rojo:#d90429;--bg:#f4f6fb;--card:#fff;--border:#e5eaf3;--border2:#d8e0ee;--txt:#0d1b33;--muted:#64748b;--gold:#f5b942;--shadow:0 2px 4px rgba(13,27,51,.04),0 8px 20px rgba(13,27,51,.07);--grad:linear-gradient(135deg,#002a5c,#d90429)}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0b1220;--card:#121a2b;--border:#1e2a44;--border2:#2a3a5c;--txt:#e7edf8;--muted:#8b9bb8}}}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--txt);font-family:'Archivo',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;line-height:1.55;-webkit-font-smoothing:antialiased}}
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
<header class="hero">
  <nav class="crumb" aria-label="Ruta de navegación"><a href="../">Portal Dominicano</a> › <span aria-current="page">{h1}</span></nav>
  <h1>{h1}</h1>
</header>
<main class="wrap">
  <p class="intro">{intro}</p>

  <h2 class="sect"><span class="bar"></span> Hoy</h2>
  {contenido}

  <h2 class="sect"><span class="bar"></span> Todo el portal</h2>
  <nav class="otras" aria-label="Todo el portal">{otras}</nav>
</main>
<footer>
  <p>Portal informativo. Verifica siempre con la fuente oficial.</p>
  <p><a href="{base}/">Portal Dominicano</a> · República Dominicana</p>
</footer>
</body>
</html>
"""


def main():
    base_dir = ROOT
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
        links += ['<a href="/resultados/">Resultados por fecha</a>', '<a href="/horarios-loterias/">Horarios</a>',
                  '<a href="/feriados/">Días feriados</a>']
        otras = " ".join(links)
        ancla = {"mlb": "mlb", "traductor": "traductor", "tiempo-santo-domingo": "tiempo"}.get(p["slug"], "")
        contenido = render_data_html(p["data"]) if p["data"] else (
            '<p style="color:var(--muted)">Esta herramienta funciona en vivo en la '
            '<a href="/#' + ancla + '" style="color:var(--azul2);font-weight:700">página principal</a> '
            'del Portal Dominicano.</p>'
        )
        robots = "index,follow" if p["data"] and p["slug"] != "economia-rd" else "noindex,follow"  # economía: muy poco contenido
        title, h1 = p["title"], p["h1"]
        if p["slug"] == "dolar-hoy":
            title, h1, extra = dolar_titulos_e_historial()
            contenido += extra
        html = TEMPLATE.format(
            base=BASE, slug=p["slug"], title=title, desc=p["desc"],
            h1=h1, intro=p["intro"], contenido=contenido, otras=otras, robots=robots,
        )
        d = os.path.join(base_dir, p["slug"])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)
        slugs.append(p["slug"])
        print(f"OK: {p['slug']}/")


if __name__ == "__main__":
    main()
