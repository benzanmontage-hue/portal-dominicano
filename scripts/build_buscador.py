#!/usr/bin/env python3
"""Índice del buscador del sitio (/buscar.json), sin servidor: lo usa /buscar.js en el navegador.

Una entrada por página indexable (título, descripción, tipo) más los sueños de la charada con su
número y sus otros significados, para que «39», «conejo» o «soñé con culebra» encuentren la página.
"""
import glob
import html
import json
import os
import re
import unicodedata

from comun import ROOT
from charada import CHARADA, slug, jugada

OMITIR = {"/404.html", "/app.html", "/buscar/"}
VACIAS = {"de", "la", "el", "en", "y", "los", "las", "del", "con", "por", "a", "su", "sus", "un", "una", "que", "o", "al"}


def norm(t):
    t = unicodedata.normalize("NFKD", html.unescape(t).lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def tipo(ruta):
    if ruta.startswith("/suenos/") and ruta != "/suenos/":
        return "Sueño"
    if ruta.startswith("/resultados/") and ruta != "/resultados/":
        return "Fecha"
    if ruta.startswith("/anguila/") and ruta != "/anguila/":
        return "Anguila"
    return ""


def main():
    from generate_landing import LOTERIAS
    from generate_otras import OTRAS
    from generate_juegos import JUEGOS
    loterias = {f'/{l["slug"]}/' for l in LOTERIAS} | {f"/{s}/" for s, *_ in OTRAS}
    juegos = {f"/{s}/" for s, *_ in JUEGOS}
    por_slug = {f"/suenos/{slug(v[0])}/": (n, v) for n, v in CHARADA.items()}

    entradas = []
    for f in sorted(glob.glob(os.path.join(ROOT, "**", "index.html"), recursive=True)):
        rel = "/" + os.path.relpath(f, ROOT).replace("\\", "/")
        if any(rel.startswith(p) for p in ("/scripts/", "/_site/", "/functions/", "/node_modules/")):
            continue
        ruta = rel[:-len("index.html")]
        if ruta in OMITIR:
            continue
        s = open(f, encoding="utf-8").read()
        rob = re.search(r'<meta name="robots" content="([^"]*)"', s)
        if rob and "noindex" in rob.group(1):
            continue
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S)
        h1 = html.unescape(re.sub(r"<[^>]+>", "", h1.group(1))).strip() if h1 else ""
        desc = re.search(r'<meta name="description" content="([^"]*)"', s)
        desc = html.unescape(desc.group(1)) if desc else ""
        t = "Lotería" if ruta in loterias else "Juego" if ruta in juegos else tipo(ruta) or "Sección"
        if ruta == "/":
            h1, t = "Lotería de hoy (portada)", "Sección"
        extra = ""
        if ruta in por_slug:
            n, (principal, otros) = por_slug[ruta]
            h1 = f"{jugada(n)} · {principal}"
            extra = " ".join([jugada(n), str(n), principal, *otros, "sueno sonar sone charada numero"])
        palabras = norm(" ".join([h1, desc, extra, ruta.replace("-", " ")])).split()
        k = " ".join(dict.fromkeys(w for w in palabras if w not in VACIAS))  # sin repetir, en orden
        e = {"u": ruta, "t": h1, "g": t, "k": k}
        if t not in ("Sueño", "Fecha"):
            e["d"] = desc[:120]
        entradas.append(e)

    orden = {"Lotería": 0, "Sección": 1, "Juego": 2, "Anguila": 3, "Sueño": 4, "Fecha": 5}
    entradas.sort(key=lambda e: (orden.get(e["g"], 9), e["u"]))
    with open(os.path.join(ROOT, "buscar.json"), "w", encoding="utf-8") as fh:
        json.dump(entradas, fh, ensure_ascii=False, separators=(",", ":"))
    from plantilla import pagina, escribir, jsonld
    from comun import BASE
    cuerpo = ('  <div id="buscarResultados"><p class="intro">Escribe arriba el nombre de una lotería, un juego, '
              'una fecha, un número o un sueño.</p></div>')
    escribir("/buscar/", pagina(ruta="/buscar/", title="Buscar — Portal Dominicano",
                                desc="Busca resultados de lotería, juegos, fechas y el número de tu sueño en Portal Dominicano.",
                                h1="Buscar en Portal Dominicano", migas=[("Portal Dominicano", "/"), ("Buscar", "/buscar/")],
                                cuerpo=cuerpo, robots="noindex,follow",
                                ld=jsonld(BASE + "/buscar/", "Buscar en Portal Dominicano", "Buscador del sitio",
                                          [("Portal Dominicano", "/"), ("Buscar", "/buscar/")])))
    print(f"buscador: {len(entradas)} páginas en buscar.json + /buscar/")


if __name__ == "__main__":
    main()
