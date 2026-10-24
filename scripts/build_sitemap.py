#!/usr/bin/env python3
"""Generar sitemap.xml con <lastmod> real.

La fecha de cada URL solo cambia cuando el contenido de esa página cambia de verdad
(se ignoran las marcas de hora "Actualizado"). Así Google sabe qué páginas volver a
visitar, sin que le "mintamos" con fechas que cambian sin motivo.
Estado guardado en data/sitemap_estado.json.
"""
import datetime
import hashlib
import json
import os
import re

from comun import ROOT, BASE, TZ_RD, cargar_json, fechas_con_pagina

PAGINAS = [
    ("", "1.0", "hourly"),
    ("loteria-nacional/", "0.9", "hourly"),
    ("anguila/", "0.9", "hourly"),
    ("loteria-real/", "0.9", "hourly"),
    ("loteka/", "0.9", "hourly"),
    ("la-primera/", "0.9", "hourly"),
    ("la-suerte/", "0.9", "hourly"),
    ("leidsa/", "0.9", "hourly"),
    ("dolar-hoy/", "0.7", "daily"),
    ("noticias-rd/", "0.7", "daily"),
    ("eventos-rd/", "0.6", "daily"),
]

VOLATIL = [
    re.compile(r"\d{4}-\d{2}-\d{2}T[\d:.]+(?:[+-]\d{2}:\d{2}|Z)?"),  # timestamps ISO
    re.compile(r"Actualizado:[^<\"']*"),
    re.compile(r"actualizados el [^.]*\."),
    re.compile(r"\?v=\d+"),
    re.compile(r"hace \d+ (?:min|h|días)"),
]


def huella(path):
    try:
        with open(path, encoding="utf-8") as f:
            s = f.read()
    except FileNotFoundError:
        return None
    for r in VOLATIL:
        s = r.sub("", s)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def main():
    estado = cargar_json("sitemap_estado.json", {}) or {}
    ahora = datetime.datetime.now(TZ_RD).isoformat(timespec="minutes")
    urls = []
    from generate_juegos import JUEGOS
    paginas = list(PAGINAS)
    paginas += [("resultados/", "0.8", "daily"), ("horarios-loterias/", "0.7", "monthly"), ("feriados/", "0.6", "monthly"),
                ("lidom/", "0.8", "hourly"), ("combustibles/", "0.8", "weekly")]
    paginas += [(f"{slug}/", "0.7", "daily") for slug, *_ in JUEGOS]
    import glob
    paginas += [(p[len(ROOT) + 1:-len("index.html")], "0.7", "hourly")
                for p in sorted(glob.glob(os.path.join(ROOT, "anguila", "*", "index.html")))]
    paginas += [("suenos/", "0.7", "weekly")]
    from charada import CHARADA, slug as slug_ch
    paginas += [(f"suenos/{slug_ch(v[0])}/", "0.5", "weekly") for v in CHARADA.values()]
    paginas += [(f"resultados/{f}/", "0.5", "never") for f in reversed(fechas_con_pagina(cargar_json("archivo.json", {}) or {}))]
    for ruta, prio, freq in paginas:
        archivo = os.path.join(ROOT, ruta, "index.html")
        h = huella(archivo)
        if h is None:
            continue
        previo = estado.get(ruta or "/", {})
        if previo.get("hash") != h:
            estado[ruta or "/"] = {"hash": h, "lastmod": ahora}
        lastmod = estado[ruta or "/"]["lastmod"]
        urls.append(
            f"  <url>\n    <loc>{BASE}/{ruta}</loc>\n    <lastmod>{lastmod}</lastmod>\n"
            f"    <changefreq>{freq}</changefreq>\n    <priority>{prio}</priority>\n  </url>"
        )
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + "\n".join(urls) + "\n</urlset>\n")
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(xml)
    with open(os.path.join(ROOT, "data", "sitemap_estado.json"), "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=1)
    print(f"sitemap: {len(urls)} URLs")


if __name__ == "__main__":
    main()
