#!/usr/bin/env python3
"""Páginas de las demás loterías que se juegan en RD: Americanas, New York, Florida, LoteDom,
King Lottery y Haití Bolet (búsquedas como «new york tarde hoy» o «king lottery hoy»).

Lee data/resultados_otras.json (lo escribe scrape_loteria.py) y data/archivo_otras.json
(historial propio, lo escribe archivar_loteria.py).
"""
import datetime
import re

from comun import BASE, TZ_RD, esc, limpiar, parse_fecha, fecha_larga, cargar_json, hora_12, minutos_juego, titulo
from plantilla import pagina, jsonld, faq_ld, faq_html, escribir

# slug, nombre, h1, [(compañía de la fuente, juegos principales en orden o None = todos[, solo])], texto
OTRAS = [
    ("americanas", "Loterías Americanas", "Loterías Americanas de Hoy",
     [("Americanas", ["New York Tarde", "New York Noche", "Florida Día", "Florida Noche", "Georgia Día",
                      "Georgia Tarde", "Georgia Noche", "New Jersey Día", "New Jersey Noche"])],
     "Resultados de las <strong>loterías americanas</strong> que se juegan en las bancas de República Dominicana: "
     "<strong>New York</strong> tarde y noche, <strong>Florida</strong> día y noche, <strong>Georgia</strong>, "
     "<strong>New Jersey</strong>, <strong>Powerball</strong> y <strong>Mega Millions</strong>."),
    ("new-york", "New York", "New York Tarde y Noche de Hoy",
     [("Americanas", ["New York Tarde", "New York Noche"], True), ("Nueva York", None)],
     "Números ganadores de <strong>New York tarde</strong> y <strong>New York noche</strong> como se juegan en las "
     "bancas dominicanas, más los sorteos de la lotería de Nueva York: <strong>Numbers</strong>, <strong>Win 4</strong>, "
     "<strong>Take 5</strong> y <strong>New York Lotto</strong>."),
    ("florida", "Florida", "Florida Día y Noche de Hoy",
     [("Americanas", ["Florida Día", "Florida Noche"], True), ("Florida", None)],
     "Números ganadores de <strong>Florida día</strong> y <strong>Florida noche</strong> como se juegan en las bancas "
     "dominicanas, más los sorteos de la lotería de Florida: <strong>Pick 2, 3, 4 y 5</strong>, "
     "<strong>Fantasy 5</strong> y <strong>Florida Lotto</strong>."),
    ("lotedom", "LoteDom", "LoteDom de Hoy",
     [("LoteDom", ["Quiniela LoteDom", "LoteDom Noche", "El Quemaito Mayor", "El Quemaito Noche"])],
     "Resultados de <strong>LoteDom</strong>: <strong>Quiniela LoteDom</strong>, LoteDom noche, "
     "<strong>El Quemaito Mayor</strong>, <strong>Agarra 4</strong> y <strong>Super Palé</strong>."),
    ("king-lottery", "King Lottery", "King Lottery de Hoy",
     [("King Lottery", ["King Lottery Día", "King Lottery Noche"])],
     "Resultados de <strong>King Lottery</strong> día y noche, <strong>Philipsburg</strong>, "
     "<strong>Loto Pool</strong>, <strong>Pick 3</strong> y <strong>Pick 4</strong>."),
    ("haiti-bolet", "Haití Bolet", "Haití Bolet de Hoy",
     [("Haiti Bolet", None)],
     "Resultados de <strong>Haití Bolet</strong> de todos los sorteos del día, de la mañana a la noche."),
]
DIAS_VIGENTE = 21     # juegos sin sorteo en este tiempo no se muestran (la fuente deja algunos sin actualizar)
DIAS_HISTORIAL = 14


def ancla(nombre):
    t = limpiar(nombre).lower()
    for a, b in zip("áéíóúñ", "aeioun"):
        t = t.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def juegos_de(fuentes, todos, hoy):
    out = []
    for comp, principales, *solo in fuentes:  # solo=True: de esa compañía, únicamente los principales
        js = [j for j in todos if j["compania"] == comp]
        vigentes = [j for j in js if (d := parse_fecha(j.get("fecha"))) and (hoy - d).days <= DIAS_VIGENTE]
        if principales:
            orden = {n: i for i, n in enumerate(principales)}
            prim = sorted((j for j in vigentes if limpiar(j["juego"]) in orden), key=lambda j: orden[limpiar(j["juego"])])
            resto = [] if solo and solo[0] else [j for j in vigentes if limpiar(j["juego"]) not in orden]
        else:
            prim, resto = [], vigentes
        resto.sort(key=lambda j: (minutos_juego(limpiar(j["juego"])) or 0, limpiar(j["juego"])))
        out += [(j, True) for j in prim] + [(j, False) for j in resto]
    return out


def tarjetas(juegos, hoy):
    from generate_landing import charada_linea
    from comun import balls_html
    html = []
    for j, _p in juegos:
        d = parse_fecha(j.get("fecha"))
        meta = fecha_larga(d, con_anio=False) if d else ""
        if d and d < hoy:
            meta += ' · <span class="ant">sorteo anterior</span>'
        html.append(f'<article class="lot-card" id="{ancla(j["juego"])}"><h3>{esc(limpiar(j["juego"]))}</h3>'
                    f'<div class="lot-meta">{meta}</div><div class="nums">{balls_html(j["numeros"])}</div>'
                    f'{charada_linea(j["numeros"])}</article>')
    return "\n    ".join(html)


def historial(juegos, archivo, hoy):
    claves = {f'{j["compania"]}|{limpiar(j["juego"])}': limpiar(j["juego"]) for j, prin in juegos if prin}
    if not claves:
        claves = {f'{j["compania"]}|{limpiar(j["juego"])}': limpiar(j["juego"]) for j, _ in juegos[:6]}
    limite = (hoy - datetime.timedelta(days=DIAS_HISTORIAL)).isoformat()
    filas = []
    for clave, nombre in claves.items():
        for s in archivo.get("sorteos", {}).get(clave, []):
            if s["fecha"] >= limite:
                filas.append((s["fecha"], nombre, s["numeros"]))
    if len({f[0] for f in filas}) < 2:  # aún no hay días anteriores guardados
        return ""
    orden = {n: i for i, n in enumerate(claves.values())}
    filas.sort(key=lambda f: (f[0], -orden.get(f[1], 0)), reverse=True)
    trs = "".join(f'<tr><td>{esc(fecha_larga(parse_fecha(f), con_anio=False))}</td><td>{esc(n)}</td>'
                  f'<td class="n">{esc(" - ".join(nums))}</td></tr>' for f, n, nums in filas[:60])
    return ('  <h2 class="sect"><span class="bar"></span> Sorteos de los últimos días</h2>\n'
            '  <div class="tabla-wrap"><table><thead><tr><th>Fecha</th><th>Sorteo</th><th>Números</th></tr></thead>'
            f'<tbody>{trs}</tbody></table></div>')


def main():
    datos = cargar_json("resultados_otras.json", {}) or {}
    archivo = cargar_json("archivo_otras.json", {}) or {}
    todos = datos.get("juegos") or []
    if not todos:
        print("otras loterías: sin datos todavía")
        return
    try:
        upd = datetime.datetime.fromisoformat(datos["updated"]).astimezone(TZ_RD)
    except Exception:
        upd = datetime.datetime.now(TZ_RD)
    hoy = upd.date()
    hechas = 0
    for slug, nombre, h1, fuentes, texto in OTRAS:
        juegos = juegos_de(fuentes, todos, hoy)
        if not juegos:
            continue
        ruta = f"/{slug}/"
        prin = [j for j, p in juegos if p] or [j for j, _ in juegos]
        # el sorteo más reciente de los principales (para título y descripción)
        p0 = max(prin, key=lambda j: (parse_fecha(j.get("fecha")), minutos_juego(limpiar(j["juego"])) or 0,
                                      -prin.index(j)))
        nums0 = "-".join(p0["numeros"])
        otras = " ".join(f'<a href="/{s}/">{esc(n)}</a>' for s, n, *_ in OTRAS if s != slug)
        resumen = "".join(
            f'<li><a href="#{ancla(j["juego"])}"><strong>{esc(limpiar(j["juego"]))}</strong></a>: '
            f'<span class="nw">{esc(" - ".join(j["numeros"]))}</span> '
            f'({esc(fecha_larga(parse_fecha(j.get("fecha")), con_anio=False))})</li>' for j in prin[:9])
        faqs = [(f"¿Qué números salieron en {limpiar(j['juego'])}?",
                 f"En el último sorteo de {limpiar(j['juego'])} ({fecha_larga(parse_fecha(j.get('fecha')))}) "
                 f"salieron los números {' - '.join(j['numeros'])}.") for j in prin[:3]]
        faqs.append((f"¿Cada cuánto se actualizan los resultados de {nombre}?",
                     "Portal Dominicano revisa los resultados cada 20 minutos durante todo el día. "
                     "Verifica siempre tus números con la fuente oficial antes de cobrar un premio."))
        cuerpo = f"""  <p class="intro">{texto}</p>
  <p class="upd">Actualizado: {upd.strftime('%d/%m/%Y')} {hora_12(upd)} (hora RD)</p>
  <h2 class="sect"><span class="bar"></span> Últimos resultados</h2>
  <ul class="resumen-txt">{resumen}</ul>
  <h2 class="sect"><span class="bar"></span> Todos los sorteos</h2>
  <div class="loteria-grid">
    {tarjetas(juegos, hoy)}
  </div>
{historial(juegos, archivo, hoy)}
  <h2 class="sect"><span class="bar"></span> Más loterías</h2>
  <nav class="otras" aria-label="Más loterías">{otras}</nav>
  <h2 class="sect"><span class="bar"></span> Preguntas frecuentes</h2>
  <div class="faq">
    {faq_html(faqs)}
  </div>
  <p class="nota">Portal informativo, no vendemos jugadas. Los resultados vienen de fuentes públicas; verifica siempre con la fuente oficial.</p>"""
        title = titulo(f"{h1}: {nums0}", "Resultados", "Números Ganadores")
        if len(title) > 65 or len(p0["numeros"]) > 4:
            title = titulo(f"{h1}: Resultados", "Números Ganadores", "Portal Dominicano")
        desc = (f"{h1} en República Dominicana. Último sorteo de {limpiar(p0['juego'])}: {' - '.join(p0['numeros'])}. "
                f"Todos los sorteos e historial, actualizado cada 20 minutos.")
        migas = [("Portal Dominicano", "/"), (nombre, ruta)]
        ld = jsonld(BASE + ruta, h1, desc, migas, extra=[faq_ld(BASE + ruta, faqs)])
        escribir(ruta, pagina(ruta=ruta, title=title, desc=desc, h1=h1, sub=f"Resultados del {fecha_larga(hoy)}",
                              migas=migas, cuerpo=cuerpo, ld=ld, radio=True))
        hechas += 1
    print(f"OK: {hechas} páginas de otras loterías")


if __name__ == "__main__":
    main()
