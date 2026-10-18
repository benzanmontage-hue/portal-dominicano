#!/usr/bin/env python3
"""Escribir los resultados de lotería directamente en index.html (portada).

Reemplaza lo que hay entre <!--LOTERIA:INICIO ...--> y <!--LOTERIA:FIN--> con las
tarjetas de resultados, para que Google las lea sin ejecutar JavaScript. Cuando la
página carga, el JavaScript existente las reemplaza por la versión interactiva.
También rellena la fecha de la sección y el texto "Actualizado".
"""
import os
import re

from comun import (ROOT, ORDEN_COMPANIAS, SLUG_COMPANIA, NOMBRE_COMPANIA, esc, limpiar,
                   cargar_json, parse_fecha, actualizado_rd, hora_12, ordenar_juegos,
                   balls_html, MESES)

INDEX = os.path.join(ROOT, "index.html")
MARCA = re.compile(r"(<!--LOTERIA:INICIO[^>]*-->)(.*?)(<!--LOTERIA:FIN-->)", re.S)


def fecha_corta(d):
    return f"{d.day} {MESES[d.month - 1][:3]}" if d else ""


def tarjetas(res):
    upd = actualizado_rd(res)
    hoy = upd.date()
    por_comp = {}
    for j in res.get("juegos", []):
        por_comp.setdefault(j["compania"], []).append(j)
    partes = []
    for comp in ORDEN_COMPANIAS:
        juegos = por_comp.get(comp)
        if not juegos:
            continue
        partes.append(f'<div class="lot-comp"><a href="{SLUG_COMPANIA[comp]}/">{esc(NOMBRE_COMPANIA[comp])}</a></div>')
        for j in ordenar_juegos(comp, juegos):
            d = parse_fecha(j.get("fecha"))
            meta = f'<span class="lot-fecha">{fecha_corta(d)}</span>' if d else ""
            if d and d < hoy:
                meta += '<span class="lot-dia">día anterior</span>'
            partes.append(
                '<div class="lot-card">'
                f'<div class="game">{esc(limpiar(j["juego"]))}</div>'
                + (f'<div class="lot-meta">{meta}</div>' if meta else "")
                + f'<div class="nums">{balls_html(j["numeros"])}</div></div>'
            )
    return "\n".join(partes), upd


def main():
    res = cargar_json("resultados.json", {}) or {}
    with open(INDEX, encoding="utf-8") as f:
        html = f.read()
    if not MARCA.search(html):
        raise SystemExit("index.html no tiene las marcas <!--LOTERIA:INICIO--> / <!--LOTERIA:FIN-->")
    contenido, upd = tarjetas(res)
    html = MARCA.sub(lambda m: m.group(1) + "\n" + contenido + "\n" + m.group(3), html, count=1)
    html = re.sub(r'(<span class="meta" id="loteria-fecha">)[^<]*(</span>)',
                  lambda m: m.group(1) + upd.strftime("%d/%m/%Y") + m.group(2), html, count=1)
    html = re.sub(r'(<div class="hero-updated" id="updated">)[^<]*(</div>)',
                  lambda m: m.group(1) + f"Actualizado: {upd.strftime('%d/%m/%Y')} {hora_12(upd)} (hora RD)" + m.group(2),
                  html, count=1)
    with open(INDEX, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"OK: portada con {contenido.count('lot-card')} resultados escritos en el HTML")


if __name__ == "__main__":
    main()
