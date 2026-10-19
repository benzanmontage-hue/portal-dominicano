#!/usr/bin/env python3
"""Páginas de resultados por fecha: /resultados/AAAA-MM-DD/ y el índice /resultados/.

Atacan búsquedas como «resultados lotería 17 de octubre» o «leidsa 17 de octubre».
Una sola página por día con todas las loterías (no una por lotería y día) para evitar
páginas pobres. Solo se publican días con al menos MIN_SORTEOS_FECHA sorteos guardados.
Lee data/archivo.json.
"""
import datetime

from comun import (ORDEN_COMPANIAS, SLUG_COMPANIA, NOMBRE_COMPANIA, JUEGO_PRINCIPAL, MESES, esc,
                   cargar_json, fecha_larga, ordenar_juegos, sorteos_por_fecha, fechas_con_pagina,
                   TZ_RD)
from generate_landing import render_cards
from plantilla import pagina, jsonld, faq_ld, faq_html, escribir


def d_iso(f):
    return datetime.date.fromisoformat(f)


def principal(comp, juegos):
    """El juego estrella de la compañía en ese día (para el resumen y las FAQ)."""
    for nombre in JUEGO_PRINCIPAL.get(comp, []):
        for j in juegos:
            if j["juego"] == nombre:
                return j
    return None


def pagina_fecha(f, sorteos, anterior, siguiente, hoy):
    d = d_iso(f)
    largo = fecha_larga(d)
    corto = f"{d.day} de {MESES[d.month - 1]} {d.year}"
    ruta = f"/resultados/{f}/"
    por_comp = {}
    for comp, juego, nums in sorteos:
        por_comp.setdefault(comp, []).append({"compania": comp, "juego": juego, "numeros": nums, "fecha": f})

    resumen, secciones, faqs = [], [], []
    for comp in ORDEN_COMPANIAS:
        js = por_comp.get(comp)
        if not js:
            continue
        js = ordenar_juegos(comp, js)
        nombre = NOMBRE_COMPANIA[comp]
        p = principal(comp, js)
        if p:
            nums = " - ".join(p["numeros"])
            resumen.append(f"<li><strong>{esc(nombre)}</strong> ({esc(p['juego'])}): <span class=\"nw\">{esc(nums)}</span></li>")
            faqs.append((f"¿Qué números salieron en {nombre} el {d.day} de {MESES[d.month - 1]} de {d.year}?",
                         f"En {p['juego']} del {largo} salieron los números {nums}."))
        secciones.append(
            f'  <section aria-labelledby="h-{SLUG_COMPANIA[comp]}">\n'
            f'  <div class="comp-h"><h2 class="sect" id="h-{SLUG_COMPANIA[comp]}"><span class="bar"></span> {esc(nombre)}</h2>'
            f'<a href="/{SLUG_COMPANIA[comp]}/">{esc(nombre)} de hoy ›</a></div>\n'
            f'  <div class="loteria-grid">\n    {render_cards(js, d)}\n  </div>\n  </section>')

    total = len(sorteos)
    nav = '<nav class="navfechas" aria-label="Otros días">'
    if anterior:
        nav += f'<a href="/resultados/{anterior}/">‹ {esc(fecha_larga(d_iso(anterior), con_anio=False))}</a>'
    if siguiente:
        nav += f'<a class="sig" href="/resultados/{siguiente}/">{esc(fecha_larga(d_iso(siguiente), con_anio=False))} ›</a>'
    nav += "</nav>"

    es_hoy = d == hoy
    intro = (f"Números ganadores de las loterías dominicanas del <strong>{esc(largo)}</strong>: "
             f"{total} sorteos de Lotería Nacional, Anguila, Lotería Real, Loteka, La Primera, La Suerte y Leidsa.")
    if es_hoy:
        intro += " Esta página se completa durante el día a medida que salen los sorteos."
    cuerpo = f"""  <p class="intro">{intro}</p>
  <h2 class="sect"><span class="bar"></span> Resumen del día</h2>
  <ul class="resumen-txt">{''.join(resumen)}</ul>
{chr(10).join(secciones)}
  {nav}
  <h2 class="sect"><span class="bar"></span> Preguntas frecuentes</h2>
  <div class="faq">
    {faq_html(faqs[:4])}
  </div>
  <p class="nota">Verifica siempre tus números con la fuente oficial de cada lotería antes de cobrar un premio.</p>"""

    title = f"Resultados de la Lotería del {d.day} de {MESES[d.month - 1].capitalize()} {d.year} — RD"
    desc = (f"Números ganadores de la lotería dominicana del {largo}: Lotería Nacional, Leidsa, Loteka, "
            f"Real, La Primera, La Suerte y Anguila. {total} sorteos.")
    migas = [("Portal Dominicano", "/"), ("Resultados por fecha", "/resultados/"), (corto, ruta)]
    from comun import BASE
    ld = jsonld(BASE + ruta, f"Resultados de la lotería del {largo}", desc, migas,
                extra=[faq_ld(BASE + ruta, faqs[:4])] if faqs else None)
    html = pagina(ruta=ruta, title=title, desc=desc, h1=f"Resultados de la lotería del {largo}",
                  sub=f"{total} sorteos de 7 loterías dominicanas", migas=migas, cuerpo=cuerpo, ld=ld)
    escribir(ruta, html)


def pagina_indice(fechas, por_fecha, hoy):
    from comun import BASE
    ruta = "/resultados/"
    ultimo = fechas[-1]
    du = d_iso(ultimo)
    etiqueta = {hoy.isoformat(): "Hoy", (hoy - datetime.timedelta(days=1)).isoformat(): "Ayer"}
    meses = {}
    for f in reversed(fechas):
        meses.setdefault(f[:7], []).append(f)
    bloques = []
    for mes, fs in meses.items():
        dm = d_iso(mes + "-01")
        enlaces = "".join(
            f'<a href="/resultados/{f}/">{esc(etiqueta.get(f, fecha_larga(d_iso(f), con_anio=False)))}</a>' for f in fs)
        bloques.append(f'<div><h3>{MESES[dm.month - 1]} {dm.year}</h3><div class="dias">{enlaces}</div></div>')

    resumen = []
    for comp in ORDEN_COMPANIAS:
        js = [{"juego": j, "numeros": n} for c, j, n in por_fecha[ultimo] if c == comp]
        p = principal(comp, js)
        if p:
            resumen.append(f"<li><strong>{esc(NOMBRE_COMPANIA[comp])}</strong> ({esc(p['juego'])}): <span class=\"nw\">{esc(' - '.join(p['numeros']))}</span></li>")

    cuerpo = f"""  <p class="intro">Busca los números ganadores de cualquier día. Cada página tiene todos los sorteos de las 7 loterías dominicanas de esa fecha.</p>
  <h2 class="sect"><span class="bar"></span> Último día completo: {esc(fecha_larga(du))}</h2>
  <ul class="resumen-txt">{''.join(resumen)}</ul>
  <p class="nota"><a href="/resultados/{ultimo}/">Ver todos los sorteos del {esc(fecha_larga(du, con_anio=False))} ›</a></p>
  <h2 class="sect"><span class="bar"></span> Días anteriores</h2>
  <div class="meses">{''.join(bloques)}</div>"""
    title = "Resultados de la Lotería Dominicana por Fecha — Archivo"
    desc = "Archivo de resultados de la lotería dominicana día por día: Lotería Nacional, Leidsa, Loteka, Real, La Primera, La Suerte y Anguila."
    migas = [("Portal Dominicano", "/"), ("Resultados por fecha", ruta)]
    ld = jsonld(BASE + ruta, "Resultados de lotería por fecha", desc, migas)
    escribir(ruta, pagina(ruta=ruta, title=title, desc=desc, h1="Resultados de la lotería por fecha",
                          sub="Archivo de sorteos de República Dominicana", migas=migas, cuerpo=cuerpo, ld=ld))


def main():
    archivo = cargar_json("archivo.json", {}) or {}
    por_fecha = sorteos_por_fecha(archivo)
    fechas = fechas_con_pagina(archivo)
    if not fechas:
        print("archivo: sin fechas con datos suficientes")
        return
    hoy = datetime.datetime.now(TZ_RD).date()
    for i, f in enumerate(fechas):
        pagina_fecha(f, por_fecha[f], fechas[i - 1] if i else None,
                     fechas[i + 1] if i + 1 < len(fechas) else None, hoy)
    pagina_indice(fechas, por_fecha, hoy)
    print(f"OK: {len(fechas)} páginas por fecha + índice /resultados/")


if __name__ == "__main__":
    main()
