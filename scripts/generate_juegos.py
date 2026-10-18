#!/usr/bin/env python3
"""Páginas por juego: /super-pale/, /gana-mas/, /loto-leidsa/, /pega-3-mas/, /la-cuarteta/...

La gente busca por juego («super palé hoy», «gana más de hoy»), no solo por lotería.
Cada página muestra el último sorteo, el historial del juego (con enlace a cada fecha)
y preguntas frecuentes con los números reales. Lee data/resultados.json y data/archivo.json.
"""
import datetime

from comun import (BASE, SLUG_COMPANIA, NOMBRE_COMPANIA, esc, limpiar, cargar_json, parse_fecha,
                   fecha_larga, actualizado_rd, hora_12, minutos_juego, fechas_con_pagina, MESES)
from generate_landing import render_cards
from plantilla import pagina, jsonld, faq_ld, faq_html, escribir

# slug, nombre, h1, [(compañía, juego)]
JUEGOS = [
    ("super-pale", "Super Palé", "Super Palé de Hoy", [("Leidsa", "Super Palé"), ("Loteria Real", "Super Palé")]),
    ("gana-mas", "Gana Más", "Gana Más de Hoy", [("Nacional", "Gana Más")]),
    ("loto-leidsa", "Loto Leidsa", "Loto Leidsa de Hoy (Super Loto Más)", [("Leidsa", "Loto - Super Loto Más")]),
    ("pega-3-mas", "Pega 3 Más", "Pega 3 Más de Hoy", [("Leidsa", "Pega 3 Más")]),
    ("loto-pool", "Loto Pool", "Loto Pool de Hoy", [("Leidsa", "Loto Pool"), ("Loteria Real", "Loto Pool"), ("Loteria Real", "Loto Pool Noche")]),
    ("super-kino-tv", "Super Kino TV", "Super Kino TV de Hoy", [("Leidsa", "Super Kino TV")]),
    ("la-cuarteta", "La Cuarteta", "La Cuarteta de Hoy (Anguila)", [("Anguila", "La Cuarteta 10:00 AM"), ("Anguila", "La Cuarteta 1:00 PM"), ("Anguila", "La Cuarteta 6:00 PM"), ("Anguila", "La Cuarteta 9:00 PM")]),
    ("mega-chances", "Mega Chances", "Mega Chances de Hoy (Loteka)", [("Loteka", "Mega Chances")]),
    ("megalotto", "MegaLotto", "MegaLotto de Hoy (Loteka)", [("Loteka", "MegaLotto")]),
    ("toca-3", "Toca 3", "Toca 3 de Hoy (Loteka)", [("Loteka", "Toca 3")]),
    ("loto-real", "Loto Real", "Loto Real de Hoy", [("Loteria Real", "Loto Real")]),
    ("juega-pega-mas", "Juega + Pega +", "Juega + Pega + de Hoy", [("Nacional", "Juega + Pega +")]),
    ("loto-5", "Loto 5", "Loto 5 de Hoy (La Primera)", [("La Primera", "Loto 5")]),
    ("el-quinielon", "El Quinielón", "El Quinielón de Hoy (La Primera)", [("La Primera", "El Quinielón Día"), ("La Primera", "El Quinielón Noche")]),
]


def lista_txt(xs):
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " y " + xs[-1]


def render_juego(slug, nombre, h1, claves, res, archivo):
    upd = actualizado_rd(res)
    hoy = upd.date()
    ruta = f"/{slug}/"
    url = BASE + ruta
    actuales = []
    for comp, juego in claves:
        for j in res.get("juegos", []):
            if j["compania"] == comp and limpiar(j["juego"]) == juego:
                actuales.append(j)
    if not actuales:
        return False
    actuales.sort(key=lambda j: (claves.index((j["compania"], limpiar(j["juego"])))))
    companias = []
    for comp, _ in claves:
        if NOMBRE_COMPANIA[comp] not in companias:
            companias.append(NOMBRE_COMPANIA[comp])

    # historial del juego
    con_pagina = set(fechas_con_pagina(archivo))
    mostrados = {(a["compania"], limpiar(a["juego"]), (a.get("fecha") or "")[:10]) for a in actuales}
    filas = []
    for comp, juego in claves:
        for s in (archivo.get("sorteos") or {}).get(f"{comp}|{juego}", []):
            if (comp, juego, s["fecha"]) in mostrados:
                continue
            filas.append((s["fecha"], comp, juego, s["numeros"]))
    filas.sort(key=lambda f: (f[0], -(minutos_juego(f[2]) or 0)), reverse=True)
    tabla = ""
    if filas:
        trs = []
        for f, comp, juego, nums in filas[:40]:
            txt = esc(fecha_larga(parse_fecha(f), con_anio=False))
            celda = f'<a href="/resultados/{f}/">{txt}</a>' if f in con_pagina else txt
            sorteo = juego if len(claves) > 1 else NOMBRE_COMPANIA[comp]
            if len({c for c, _ in claves}) > 1:
                sorteo = f"{juego} ({NOMBRE_COMPANIA[comp]})"
            trs.append(f'<tr><td>{celda}</td><td>{esc(sorteo)}</td><td class="n">{esc(" - ".join(nums))}</td></tr>')
        tabla = (f'  <h2 class="sect"><span class="bar"></span> Resultados anteriores de {esc(nombre)}</h2>\n'
                 '  <div class="tabla-wrap"><table><thead><tr><th>Fecha</th><th>Sorteo</th><th>Números</th></tr></thead>'
                 f'<tbody>{"".join(trs)}</tbody></table></div>')

    ult = max(actuales, key=lambda a: ((a.get('fecha') or '')[:10], minutos_juego(limpiar(a['juego'])) or 0))
    du = parse_fecha(ult.get("fecha"))
    nums_ult = " - ".join(ult["numeros"])
    faqs = [
        (f"¿Cuáles son los números de {nombre} de hoy?",
         f"En el último sorteo de {limpiar(ult['juego'])} ({NOMBRE_COMPANIA[ult['compania']]}), del {fecha_larga(du)}, "
         f"salieron los números {nums_ult}. Actualizado el {fecha_larga(hoy)} a las {hora_12(upd)} (hora RD)."),
        (f"¿Qué lotería sortea {nombre}?",
         f"{nombre} se sortea en {lista_txt(companias)}. En esta página publicamos {len(actuales)} "
         f"sorteo{'s' if len(actuales) > 1 else ''} de {nombre}: {lista_txt([limpiar(a['juego']) for a in actuales])}."),
        ("¿Dónde veo los resultados de días anteriores?",
         "Más abajo está la tabla con los sorteos anteriores de este juego, y en «Resultados por fecha» tienes todos los sorteos de cada día."),
        (f"¿Puedo jugar {nombre} en Portal Dominicano?",
         "No. Portal Dominicano es un sitio informativo: no vendemos jugadas. Verifica siempre con la fuente oficial."),
    ]
    enlaces_comp = " ".join(f'<a href="/{SLUG_COMPANIA[c]}/">{esc(NOMBRE_COMPANIA[c])}</a>'
                            for c in dict.fromkeys(c for c, _ in claves))
    cuerpo = f"""  <p class="intro">Consulta los <strong>resultados de {esc(nombre)} de hoy</strong> en República Dominicana, con los números ganadores del último sorteo y los de días anteriores. {esc(nombre)} se sortea en {esc(lista_txt(companias))}.</p>
  <p class="upd">Actualizado: {upd.strftime('%d/%m/%Y')} {hora_12(upd)} (hora RD)</p>
  <h2 class="sect"><span class="bar"></span> Último sorteo de {esc(nombre)}</h2>
  <div class="loteria-grid">
    {render_cards(actuales, hoy)}
  </div>
{tabla}
  <h2 class="sect"><span class="bar"></span> Preguntas frecuentes sobre {esc(nombre)}</h2>
  <div class="faq">
    {faq_html(faqs)}
  </div>
  <h2 class="sect"><span class="bar"></span> Ver la lotería completa</h2>
  <nav class="otras" aria-label="Loterías de este juego">{enlaces_comp} <a href="/resultados/">Resultados por fecha</a></nav>"""

    title = f"{nombre} de Hoy, {du.day} de {MESES[du.month - 1]}: {nums_ult} — Resultados"
    desc = (f"Resultados de {nombre} de hoy en República Dominicana ({lista_txt(companias)}). "
            f"Último sorteo: {nums_ult}. Números ganadores e historial de días anteriores.")
    migas = [("Portal Dominicano", "/"), ("Lotería de hoy", "/#loteria"), (nombre, ruta)]
    ld = jsonld(url, h1, desc, migas, extra=[faq_ld(url, faqs)], fecha_mod=upd.isoformat(timespec="seconds"))
    escribir(ruta, pagina(ruta=ruta, title=title, desc=desc, h1=h1, sub=f"Resultados del {fecha_larga(hoy)}",
                          chip=f"Lotería: {lista_txt(companias)}", migas=migas, cuerpo=cuerpo, ld=ld))
    return True


def main():
    res = cargar_json("resultados.json", {}) or {}
    archivo = cargar_json("archivo.json", {}) or {}
    hechos = [slug for slug, nombre, h1, claves in JUEGOS if render_juego(slug, nombre, h1, claves, res, archivo)]
    print(f"OK: {len(hechos)} páginas por juego")


if __name__ == "__main__":
    main()
