#!/usr/bin/env python3
"""Plantilla HTML común para las páginas generadas (fechas, juegos, horarios, feriados).

Usa el mismo estilo que las páginas de lotería (generate_landing.CSS) y rutas absolutas
("/leidsa/") para funcionar a cualquier profundidad.
"""
import json
import os

from comun import ROOT, BASE, SECCIONES, esc
from generate_landing import CSS as CSS_BASE, LOTERIAS

CSS_EXTRA = """
.navfechas{display:flex;justify-content:space-between;gap:10px;margin-top:22px;flex-wrap:wrap}
.navfechas a{flex:1 1 200px;font-weight:700;text-decoration:none;color:var(--azul2);background:var(--card);border:1px solid var(--border);border-radius:12px;padding:12px 14px;min-height:44px}
.navfechas a.sig{text-align:right}
.comp-h{display:flex;align-items:baseline;justify-content:space-between;gap:10px}
.comp-h a{font-size:.85rem;font-weight:700;color:var(--azul2);text-decoration:none;white-space:nowrap}
.meses{display:flex;flex-direction:column;gap:18px}
.meses h3{font-size:1rem;font-weight:800;margin-bottom:8px;text-transform:capitalize}
.dias{display:flex;flex-wrap:wrap;gap:8px}
.dias a{font-size:.88rem;font-weight:600;color:var(--azul2);text-decoration:none;background:var(--card);border:1px solid var(--border);padding:8px 12px;border-radius:10px;min-height:40px;display:inline-flex;align-items:center}
.resumen-txt{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:14px 16px;font-size:.95rem}
.resumen-txt li{margin:4px 0 4px 18px}
.tabla-wrap td a{color:var(--azul2);font-weight:600;text-decoration:none}
.nw{white-space:nowrap;font-weight:800}
.resumen-txt a,.nota a{color:var(--azul2);text-decoration:none;font-weight:600}
@media (prefers-color-scheme:dark){.resumen-txt a,.nota a{color:#7fb0ff}}
.juegos-l{list-style:none;display:flex;flex-direction:column;gap:8px}
.juego{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:12px 14px}
.j-m{font-weight:600;font-size:1rem}
.j-m .gan{font-weight:900}
.j-s{font-size:.82rem;color:var(--muted);margin-top:2px}
.sub-h{font-size:.95rem;font-weight:800;margin:14px 0 8px}
.nota{font-size:.82rem;color:var(--muted);margin-top:10px}
@media (prefers-color-scheme:dark){.navfechas a,.comp-h a,.dias a,.tabla-wrap td a{color:#7fb0ff}}
"""


def jsonld(url, nombre, desc, migas, extra=None, fecha_mod=None):
    pagina = {"@type": "WebPage", "@id": url + "#webpage", "url": url, "name": nombre,
              "description": desc, "inLanguage": "es-DO",
              "isPartOf": {"@type": "WebSite", "@id": BASE + "/#website", "name": "Portal Dominicano", "url": BASE + "/"},
              "breadcrumb": {"@id": url + "#breadcrumb"}}
    if fecha_mod:
        pagina["dateModified"] = fecha_mod
    grafo = [pagina, {"@type": "BreadcrumbList", "@id": url + "#breadcrumb",
                      "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": BASE + h}
                                          for i, (n, h) in enumerate(migas)]}]
    if extra:
        grafo.extend(extra)
    return json.dumps({"@context": "https://schema.org", "@graph": grafo},
                      ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def faq_ld(url, faqs):
    return {"@type": "FAQPage", "@id": url + "#faq",
            "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                           for q, a in faqs]}


def faq_html(faqs):
    return "\n    ".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in faqs)


def pagina(*, ruta, title, desc, h1, sub="", chip="", migas, cuerpo, ld, robots="index,follow,max-image-preview:large", radio=False, aviso=""):
    """ruta: '/resultados/2026-10-17/'. migas: [(nombre, ruta)], la última es esta página."""
    url = BASE + ruta
    crumbs = "\n    ".join(
        f'<li aria-current="page">{esc(n)}</li>' if i == len(migas) - 1 else f'<li><a href="{h}">{esc(n)}</a></li>'
        for i, (n, h) in enumerate(migas))
    otras = " ".join(f'<a href="/{o["slug"]}/">{esc(o["nombre"])}</a>' for o in LOTERIAS)
    secciones = " ".join(f'<a href="/{s}/">{esc(n)}</a>' for s, n in SECCIONES)
    from generate_juegos import JUEGOS  # import tardío (generate_juegos importa este módulo)
    juegos = " ".join(f'<a href="/{slug}/">{esc(nombre)}</a>' for slug, nombre, *_ in JUEGOS if f"/{slug}/" != ruta)
    extras = ('<a href="/resultados/">Resultados por fecha</a> <a href="/horarios-loterias/">Horarios</a> '
              '<a href="/feriados/">Días feriados</a>')
    return f"""<!DOCTYPE html>
<html lang="es-DO">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="Portal Dominicano">
<meta property="og:locale" content="es_DO">
<meta property="og:image" content="{BASE}/img/og-portal-dominicano.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#002a5c">
<meta name="robots" content="{robots}">
<link rel="icon" type="image/png" href="/img/icon-192.png">
<link rel="manifest" href="/manifest.json">
<link rel="alternate" type="application/rss+xml" title="Resultados de lotería — Portal Dominicano" href="https://portaldominicana.net/feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;700;800;900&display=swap"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;700;800;900&display=swap" media="print" onload="this.media='all'"><noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;700;800;900&display=swap"></noscript>
<script type="application/ld+json">{ld}</script>
<style>{CSS_BASE}{CSS_EXTRA}</style>
</head>
<body>
<header class="hero">
  <nav class="crumb" aria-label="Ruta de navegación"><ol>
    {crumbs}
  </ol></nav>
  <h1>{esc(h1)}</h1>
  {f'<p class="fecha">{esc(sub)}</p>' if sub else ''}
  {f'<div class="hora">{esc(chip)}</div>' if chip else ''}
  {f'<div><button class="aviso-btn" type="button" data-aviso="{aviso}" hidden>Avísame</button></div>' if aviso else ''}
</header>
<main class="wrap">
{cuerpo}

  <h2 class="sect"><span class="bar"></span> Loterías dominicanas</h2>
  <nav class="otras" aria-label="Loterías">{otras}</nav>

  <h2 class="sect"><span class="bar"></span> Juegos</h2>
  <nav class="otras" aria-label="Juegos">{juegos}</nav>

  <h2 class="sect"><span class="bar"></span> Más en Portal Dominicano</h2>
  <nav class="otras" aria-label="Secciones">{extras} {secciones}</nav>
</main>
<footer>
  <p>Portal informativo. No vendemos sorteos. Verifica siempre con la fuente oficial.</p>
  <p><a href="/">Portal Dominicano</a> · Datos de lotería: <a href="https://loteriasdominicanas.com" rel="noopener">loteriasdominicanas.com</a></p>
</footer>
{'<script src="/radio.js" defer></script>' if radio else ''}
{'<script src="/avisos.js" defer></script>' if aviso else ''}
</body>
</html>
"""


def escribir(ruta, html):
    d = os.path.join(ROOT, ruta.strip("/"))
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
