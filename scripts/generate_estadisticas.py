#!/usr/bin/env python3
"""/numeros-que-mas-salen/: frecuencia de cada número (00–99) en las quinielas dominicanas.

Solo cuenta sorteos de quiniela (3 números de 2 cifras) guardados en data/archivo.json desde
el primer día completo. Muestra los más repetidos, los que más tiempo llevan sin salir, los
más repetidos por lotería y la tabla completa con su significado en la charada.
"""
import collections
import datetime

from comun import (BASE, ORDEN_COMPANIAS, NOMBRE_COMPANIA, SLUG_COMPANIA, esc, limpiar, cargar_json,
                   parse_fecha, fecha_larga, fechas_con_pagina, TZ_RD)
from charada import CHARADA, slug, jugada, de_jugada
from plantilla import pagina, jsonld, faq_ld, faq_html, escribir


def quinielas(archivo, desde):
    """[(fecha, compania, juego, [n1, n2, n3])] desde la fecha indicada."""
    out = []
    for clave, lista in (archivo.get("sorteos") or {}).items():
        comp, juego = clave.split("|", 1)
        for s in lista:
            nums = s["numeros"]
            if s["fecha"] >= desde and len(nums) == 3 and all(len(n) == 2 and n.isdigit() for n in nums):
                out.append((s["fecha"], comp, juego, nums))
    return out


def link_num(n):
    m = de_jugada(n)
    nombre = CHARADA[m][0] if m else ""
    return f'<a href="/suenos/{slug(nombre)}/"><strong>{esc(n)}</strong></a> <span class="nota">{esc(nombre.lower())}</span>'


def main():
    archivo = cargar_json("archivo.json", {}) or {}
    completas = fechas_con_pagina(archivo)
    if not completas:
        print("estadisticas: sin datos")
        return
    desde = completas[0]
    sorteos = quinielas(archivo, desde)
    if len(sorteos) < 30:
        print("estadisticas: pocos sorteos")
        return
    hoy = datetime.datetime.now(TZ_RD).date()
    todos = [jugada(n) for n in range(1, 101)]
    cuenta = collections.Counter(n for *_x, nums in sorteos for n in nums)
    ultima = {}
    for f, comp, juego, nums in sorteos:
        for n in nums:
            if n not in ultima or f > ultima[n][0]:
                ultima[n] = (f, comp, juego)
    total = len(sorteos)
    esperado = total * 3 / 100

    mas = sorted(todos, key=lambda n: (-cuenta[n], n))[:10]
    atrasados = sorted(todos, key=lambda n: (ultima.get(n, ("0000",))[0], n))[:10]

    def fila(n, extra):
        return f"<tr><td>{link_num(n)}</td><td class=\"n\">{cuenta[n]}</td><td>{extra}</td></tr>"

    def ult_txt(n):
        if n not in ultima:
            return f"No ha salido desde el {esc(fecha_larga(parse_fecha(desde), con_anio=False))}"
        f, comp, juego = ultima[n]
        return f"{esc(fecha_larga(parse_fecha(f), con_anio=False))} · {esc(limpiar(juego))}"

    t_mas = "".join(fila(n, ult_txt(n)) for n in mas)
    t_atr = "".join(fila(n, ult_txt(n)) for n in atrasados)

    por_lot = []
    for comp in ORDEN_COMPANIAS:
        ss = [s for s in sorteos if s[1] == comp]
        if len(ss) < 5:
            continue
        c = collections.Counter(n for *_x, nums in ss for n in nums)
        top = [f"{link_num(n)} ({k})" for n, k in c.most_common(5) if k > 1]
        if top:
            por_lot.append(f'<li><a href="/{SLUG_COMPANIA[comp]}/"><strong>{esc(NOMBRE_COMPANIA[comp])}</strong></a> '
                           f'({len(ss)} sorteos): {" · ".join(top)}</li>')

    completa = "".join(
        f"<tr><td>{link_num(n)}</td><td class=\"n\">{cuenta[n]}</td><td>{ult_txt(n)}</td></tr>" for n in todos)

    n1 = mas[0]
    faqs = [
        ("¿Cuáles son los números que más salen en la lotería dominicana?",
         f"Desde el {fecha_larga(parse_fecha(desde))}, en {total} sorteos de quiniela, los que más han salido son "
         + ", ".join(f"{n} ({cuenta[n]} veces)" for n in mas[:5]) + "."),
        ("¿Qué números llevan más tiempo sin salir?",
         "Los que más tiempo llevan sin salir en las quinielas son " + ", ".join(atrasados[:5]) + "."),
        ("¿Sirven las estadísticas para ganar?",
         "No. Cada sorteo es independiente y al azar: que un número haya salido más o menos no cambia su probabilidad en el próximo sorteo. Estas cifras son solo informativas."),
    ]
    cuerpo = f"""  <p class="intro">Estos son los <strong>números que más salen</strong> en las quinielas de las loterías dominicanas (Nacional, Anguila, Real, Loteka, La Primera, La Suerte y Leidsa). Analizamos <strong>{total} sorteos</strong> ({total * 3} números) desde el {esc(fecha_larga(parse_fecha(desde)))}; en promedio, cada número debería haber salido unas {str(round(esperado, 1)).replace(".", ",")} veces.</p>
  <p class="upd">Actualizado: {hoy.strftime('%d/%m/%Y')} · se recalcula cada día con los nuevos sorteos</p>
  <h2 class="sect"><span class="bar"></span> Los 10 números que más salen</h2>
  <div class="tabla-wrap"><table><thead><tr><th>Número</th><th>Veces</th><th>Última vez</th></tr></thead><tbody>{t_mas}</tbody></table></div>
  <h2 class="sect"><span class="bar"></span> Números que más tiempo llevan sin salir</h2>
  <div class="tabla-wrap"><table><thead><tr><th>Número</th><th>Veces</th><th>Última vez</th></tr></thead><tbody>{t_atr}</tbody></table></div>
  <h2 class="sect"><span class="bar"></span> Los que más salen en cada lotería</h2>
  <ul class="resumen-txt">{''.join(por_lot)}</ul>
  <p class="nota">Los sorteos son al azar: un número que ha salido mucho no tiene más probabilidad de volver a salir, ni uno atrasado de salir pronto. Juega con responsabilidad (+18).</p>
  <h2 class="sect"><span class="bar"></span> Tabla completa del 00 al 99</h2>
  <div class="tabla-wrap"><table><thead><tr><th>Número</th><th>Veces</th><th>Última vez</th></tr></thead><tbody>{completa}</tbody></table></div>
  <h2 class="sect"><span class="bar"></span> Preguntas frecuentes</h2>
  <div class="faq">
    {faq_html(faqs)}
  </div>"""
    ruta = "/numeros-que-mas-salen/"
    title = "Números que Más Salen en la Lotería Dominicana — Estadísticas"
    desc = (f"Números que más salen en las quinielas dominicanas: {', '.join(mas[:5])}. "
            "Números atrasados, los más repetidos por lotería y tabla del 00 al 99, actualizada cada día.")
    migas = [("Portal Dominicano", "/"), ("Números que más salen", ruta)]
    ld = jsonld(BASE + ruta, "Números que más salen en la lotería dominicana", desc, migas,
                extra=[faq_ld(BASE + ruta, faqs)], fecha_mod=datetime.datetime.now(TZ_RD).isoformat(timespec="seconds"))
    escribir(ruta, pagina(ruta=ruta, title=title, desc=desc, h1="Números que más salen en la lotería dominicana",
                          sub=f"{total} sorteos de quiniela analizados", migas=migas, cuerpo=cuerpo, ld=ld))
    print(f"OK: /numeros-que-mas-salen/ ({total} sorteos)")


if __name__ == "__main__":
    main()
