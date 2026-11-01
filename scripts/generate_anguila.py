#!/usr/bin/env python3
"""Una página por cada sorteo horario de Anguila: /anguila/8am/ … /anguila/10pm/.

Atacan búsquedas como «anguila 10 am», «anguila de las 6». Cada página tiene el último sorteo
de esa hora, su significado en la charada, el historial de esa hora, los números que más se
repiten a esa hora y enlaces a las demás horas. Lee data/resultados.json y data/archivo.json.
"""
import collections
import datetime

from comun import (BASE, MESES, esc, limpiar, cargar_json, parse_fecha, fecha_larga, actualizado_rd,
                   hora_12, minutos_juego, fechas_con_pagina, titulo)
from charada import significado
from generate_landing import render_cards
from plantilla import pagina, jsonld, faq_ld, faq_html, escribir


def slug_hora(mins):
    h, ap = mins // 60, "am" if mins < 720 else "pm"
    return f"{h % 12 or 12}{ap}"


def etiqueta(mins):
    h = mins // 60
    return f"{h % 12 or 12}:{mins % 60:02d} {'AM' if mins < 720 else 'PM'}"


def sorteos_horarios(res):
    """[(mins, juego_actual)] de los sorteos horarios de Anguila, ordenados por hora."""
    out = []
    for j in res.get("juegos", []):
        n = limpiar(j["juego"])
        if j["compania"] == "Anguila" and n.startswith("Anguila ") and minutos_juego(n) is not None:
            out.append((minutos_juego(n), j))
    return sorted(out, key=lambda x: x[0])


def charada_txt(nums):
    partes = []
    for n in nums:
        nombre, url = significado(n)
        partes.append(f'<a href="{url}">{esc(n)} = {esc(nombre)}</a>' if nombre else esc(n))
    return " · ".join(partes)


def main():
    res = cargar_json("resultados.json", {}) or {}
    archivo = cargar_json("archivo.json", {}) or {}
    upd = actualizado_rd(res)
    hoy = upd.date()
    horas = sorteos_horarios(res)
    if not horas:
        print("anguila: sin datos")
        return
    con_pagina = set(fechas_con_pagina(archivo))
    nav = " ".join(f'<a href="/anguila/{slug_hora(m)}/">{etiqueta(m)}</a>' for m, _ in horas)

    for i, (mins, j) in enumerate(horas):
        nombre_juego = limpiar(j["juego"])
        et = etiqueta(mins)
        ruta = f"/anguila/{slug_hora(mins)}/"
        d = parse_fecha(j.get("fecha"))
        es_hoy = d == hoy
        hist = sorted((archivo.get("sorteos") or {}).get(f"Anguila|{nombre_juego}", []),
                      key=lambda s: s["fecha"], reverse=True)

        filas = []
        for s in hist[:30]:
            ds = parse_fecha(s["fecha"])
            txt = esc(fecha_larga(ds, con_anio=False))
            celda = f'<a href="/resultados/{s["fecha"]}/">{txt}</a>' if s["fecha"] in con_pagina else txt
            filas.append(f'<tr><td>{celda}</td><td class="n nw">{esc("-".join(s["numeros"]))}</td>'
                         f'<td>{charada_txt(s["numeros"])}</td></tr>')
        tabla = ('<div class="tabla-wrap"><table><thead><tr><th>Fecha</th><th>Números</th><th>En la charada</th></tr></thead>'
                 f'<tbody>{"".join(filas)}</tbody></table></div>') if filas else '<p class="intro">Aún no hay historial.</p>'

        cuenta = collections.Counter(n for s in hist for n in s["numeros"])
        top = cuenta.most_common(6)
        frec = ""
        if len(hist) >= 5 and top and top[0][1] > 1:
            frec = (f'<h2 class="sect"><span class="bar"></span> Números que más han salido a las {et}</h2>'
                    f'<p class="intro">En los últimos {len(hist)} sorteos de Anguila {et} guardados: '
                    + ", ".join(f"<strong>{esc(n)}</strong> ({c} veces)" for n, c in top if c > 1)
                    + '. Los sorteos son al azar: que un número haya salido más no significa que vaya a volver a salir.</p>')

        prev_m, sig_m = horas[i - 1][0] if i else None, horas[i + 1][0] if i + 1 < len(horas) else None
        vecinos = '<nav class="navfechas" aria-label="Sorteos vecinos">'
        if prev_m is not None:
            vecinos += f'<a href="/anguila/{slug_hora(prev_m)}/">‹ Anguila {etiqueta(prev_m)}</a>'
        if sig_m is not None:
            vecinos += f'<a class="sig" href="/anguila/{slug_hora(sig_m)}/">Anguila {etiqueta(sig_m)} ›</a>'
        vecinos += "</nav>"

        nums = " - ".join(j["numeros"])
        cuando = "hoy" if es_hoy else f"el {fecha_larga(d)}"
        faqs = [
            (f"¿Qué salió en la Anguila de las {et} hoy?",
             (f"En la Anguila de las {et} de hoy salieron los números {nums}." if es_hoy else
              f"El sorteo de hoy de las {et} aún no se ha publicado. El último fue {cuando}: {nums}.")),
            (f"¿A qué hora juega la Anguila de las {et}?",
             f"Todos los días a las {et}, hora de República Dominicana. Anguila tiene sorteos cada hora de 8:00 AM a 10:00 PM."),
            (f"¿Qué significan los números {nums} en la charada?",
             " · ".join(f"{n} = {significado(n)[0]}" for n in j["numeros"] if significado(n)[0]) or "No aplica."),
        ]
        estado = (f"Resultado de hoy, {fecha_larga(d)}." if es_hoy else
                  f"El sorteo de hoy a las {et} aún no se ha publicado; abajo está el último ({fecha_larga(d)}).")
        cuerpo = f"""  <p class="intro">Resultados de la <strong>Anguila de las {et}</strong> de hoy, con los números ganadores, su significado en la charada y los resultados de días anteriores a esta misma hora. {esc(estado)}</p>
  <p class="upd">Actualizado: {upd.strftime('%d/%m/%Y')} {hora_12(upd)} (hora RD)</p>
  <h2 class="sect"><span class="bar"></span> Anguila {et}: último sorteo</h2>
  <div class="loteria-grid">
    {render_cards([j], hoy)}
  </div>
  <p class="nota">En la charada: {charada_txt(j["numeros"])}</p>
  <h2 class="sect"><span class="bar"></span> Anguila {et}: días anteriores</h2>
  {tabla}
  {frec}
  {vecinos}
  <h2 class="sect"><span class="bar"></span> Todos los sorteos de Anguila</h2>
  <nav class="otras" aria-label="Horas de Anguila"><a href="/anguila/">Anguila hoy (todas las horas)</a> {nav} <a href="/la-cuarteta/">La Cuarteta</a></nav>
  <h2 class="sect"><span class="bar"></span> Preguntas frecuentes</h2>
  <div class="faq">
    {faq_html(faqs)}
  </div>"""
        nums_t = "-".join(j["numeros"])
        title = titulo(f"Anguila {et} Hoy {d.day} de {MESES[d.month - 1]}: {nums_t}", "Resultados", "Números Ganadores")
        desc = (f"Anguila {et} de hoy en RD. Último sorteo ({d.day} de {MESES[d.month - 1]}): {nums}. "
                f"Historial de esta hora y su significado en la charada.")
        migas = [("Portal Dominicano", "/"), ("Anguila", "/anguila/"), (f"Anguila {et}", ruta)]
        ld = jsonld(BASE + ruta, f"Anguila {et} de hoy", desc, migas, extra=[faq_ld(BASE + ruta, faqs)],
                    fecha_mod=upd.isoformat(timespec="seconds"))
        escribir(ruta, pagina(ruta=ruta, title=title, desc=desc, h1=f"Anguila {et} de hoy",
                              sub=f"Resultados del {fecha_larga(hoy)}", chip=f"Sorteo diario a las {et} (hora RD)",
                              migas=migas, cuerpo=cuerpo, ld=ld, radio=True, aviso="anguila"))
    print(f"OK: {len(horas)} páginas de Anguila por hora")


if __name__ == "__main__":
    main()
