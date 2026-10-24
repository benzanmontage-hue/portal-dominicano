#!/usr/bin/env python3
"""Feed RSS de resultados (/feed.xml): los últimos sorteos principales de cada lotería.

Ayuda a Google, Bing y lectores de noticias a descubrir cada sorteo nuevo apenas sale.
"""
import datetime
import os
from email.utils import format_datetime
from xml.sax.saxutils import escape

from comun import ROOT, BASE, NOMBRE_COMPANIA, SLUG_COMPANIA, MESES, cargar_json, limpiar, TZ_RD, minutos_juego
from prerender_home import RESUMEN


def main():
    archivo = cargar_json("archivo.json", {}) or {}
    sorteos = archivo.get("sorteos") or {}
    items = []
    for comp, cands in RESUMEN:
        juegos = [g for g, _m in cands] if cands else \
            [k.split("|", 1)[1] for k in sorteos if k.startswith("Anguila|Anguila ") and minutos_juego(k.split("|", 1)[1]) is not None]
        for g in juegos:
            mins = dict(cands).get(g) if cands else minutos_juego(g)
            for s in sorteos.get(f"{comp}|{g}", [])[:7]:
                d = datetime.date.fromisoformat(s["fecha"])
                cuando = datetime.datetime(d.year, d.month, d.day, tzinfo=TZ_RD) + datetime.timedelta(minutes=(mins or 0) + 10)
                items.append((cuando, comp, g, s["numeros"], s["fecha"]))
    items.sort(key=lambda x: x[0], reverse=True)
    items = items[:60]
    ahora = datetime.datetime.now(TZ_RD)
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>',
           "<title>Portal Dominicano — Resultados de lotería</title>",
           f"<link>{BASE}/</link>",
           f'<atom:link href="{BASE}/feed.xml" rel="self" type="application/rss+xml"/>',
           "<description>Resultados de la lotería dominicana: Nacional, Leidsa, Loteka, Real, La Primera, La Suerte y Anguila.</description>",
           "<language>es-DO</language>",
           f"<lastBuildDate>{format_datetime(ahora)}</lastBuildDate>"]
    for cuando, comp, g, nums, f in items:
        d = cuando.date()
        titulo = f"{limpiar(g)} ({NOMBRE_COMPANIA[comp]}) {d.day} de {MESES[d.month - 1]}: {'-'.join(nums)}"
        enlace = f"{BASE}/{SLUG_COMPANIA[comp]}/"
        xml.append("<item>"
                   f"<title>{escape(titulo)}</title><link>{enlace}</link>"
                   f'<guid isPermaLink="false">{escape(comp + "|" + g + "|" + f)}</guid>'
                   f"<pubDate>{format_datetime(cuando)}</pubDate>"
                   f"<description>{escape('Números ganadores de ' + limpiar(g) + ': ' + ' - '.join(nums) + '. Todos los sorteos del día: ' + BASE + '/resultados/' + f + '/')}</description>"
                   "</item>")
    xml.append("</channel></rss>")
    with open(os.path.join(ROOT, "feed.xml"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(xml) + "\n")
    print(f"OK: feed.xml ({len(items)} sorteos)")


if __name__ == "__main__":
    main()
