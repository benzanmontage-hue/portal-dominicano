#!/usr/bin/env python3
"""Escribir los datos del día directamente en index.html (portada).

Rellena las zonas marcadas con <!--XXX:INICIO ...--> / <!--XXX:FIN-->:
  RESUMEN  último sorteo de cada lotería (una fila por lotería)
  ANGUILA  sorteos de Anguila de hoy, hora por hora
  LOTERIA  todos los juegos (dentro de "Ver todos los juegos de hoy")
  DOLAR    acceso rápido al precio del dólar
Así Google lo lee sin ejecutar JavaScript. En el navegador, el JavaScript de la
portada vuelve a dibujar estas zonas con los datos más recientes (misma lógica).
También rellena la fecha de la sección y el texto "Actualizado".
"""
import os
import re

from comun import (ROOT, ORDEN_COMPANIAS, SLUG_COMPANIA, NOMBRE_COMPANIA, esc, limpiar,
                   cargar_json, parse_fecha, actualizado_rd, hora_12, ordenar_juegos,
                   balls_html, minutos_juego, MESES, DIAS)

INDEX = os.path.join(ROOT, "index.html")

# Orden y candidatos del resumen: (compañía, juegos principales con su hora aprox. en minutos).
# Se muestra el sorteo más reciente entre los candidatos. Anguila: el último sorteo horario.
# Debe coincidir con RES_LOT en index.html.
RESUMEN = [
    ("Nacional", [("Gana Más", 870), ("Lotería Nacional", 1250)]),
    ("Anguila", None),
    ("Loteria Real", [("Quiniela Real", 775), ("Lotería Real Noche", 1260)]),
    ("Loteka", [("Quiniela Loteka Día", 780), ("Quiniela Loteka Noche", 1195)]),
    ("La Primera", [("La Primera Día", 720), ("Primera Noche", 1200)]),
    ("La Suerte", [("La Suerte 12:30", 750), ("La Suerte 18:00", 1080)]),
    ("Leidsa", [("Quiniela Leidsa", 1255)]),
]
ETIQUETA = {
    "Lotería Nacional": "Quiniela noche", "Gana Más": "Gana Más",
    "Quiniela Real": "Quiniela Real", "Lotería Real Noche": "Real Noche",
    "Quiniela Loteka Día": "Quiniela Día", "Quiniela Loteka Noche": "Quiniela Noche",
    "La Primera Día": "Primera Día", "Primera Noche": "Primera Noche",
    "La Suerte 12:30": "Sorteo 12:30 PM", "La Suerte 18:00": "Sorteo 6:00 PM",
    "Quiniela Leidsa": "Quiniela",
}
DIAS_C = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]

CHEV = ('<svg class="chev" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>')


def fecha_corta(d):
    return f"{d.day} {MESES[d.month - 1][:3]}" if d else ""


def fecha_rel(d, hoy):
    if d == hoy:
        return "hoy"
    return f"{DIAS_C[d.weekday()]} {d.day} {MESES[d.month - 1][:3]}" if d else ""


def hora_anguila(nombre):
    n = limpiar(nombre)
    return n.replace("La Cuarteta", "Cuarteta") if n.startswith("La Cuarteta") else re.sub(r"^Anguila\s*", "", n)


def etiqueta(nombre):
    n = limpiar(nombre)
    return ETIQUETA.get(n) or (hora_anguila(n) if n.startswith("Anguila") else n)


from generate_anguila import slug_hora  # noqa: E402


def zona(html, nombre, contenido):
    patron = re.compile(r"(<!--" + nombre + r":INICIO[^>]*-->)(.*?)(<!--" + nombre + r":FIN-->)", re.S)
    if not patron.search(html):
        raise SystemExit(f"index.html no tiene las marcas <!--{nombre}:INICIO--> / <!--{nombre}:FIN-->")
    return patron.sub(lambda m: m.group(1) + "\n" + contenido + "\n" + m.group(3), html, count=1)


def resumen(juegos, hoy):
    filas = []
    for comp, cands in RESUMEN:
        js = [j for j in juegos if j["compania"] == comp]
        if cands:
            opciones = [(j, mins) for g, mins in cands for j in js if limpiar(j["juego"]) == g]
        else:
            opciones = [(j, minutos_juego(limpiar(j["juego"])) or 0) for j in js
                        if re.match(r"^Anguila \d", limpiar(j["juego"]))]
        if not opciones:
            continue
        j, _ = max(opciones, key=lambda o: ((o[0].get("fecha") or "")[:10], o[1]))
        d = parse_fecha(j.get("fecha"))
        badge = '<span class="res-hoy">HOY</span>' if d == hoy else ""
        nums = "".join(f'<span class="nb">{esc(n)}</span>' for n in j["numeros"])
        filas.append(
            f'<a class="res-row" href="{SLUG_COMPANIA[comp]}/" data-comp="{esc(comp)}">'
            f'<div class="res-info"><div class="res-nom">{esc(NOMBRE_COMPANIA[comp])}{badge}</div>'
            f'<div class="res-juego">{esc(etiqueta(j["juego"]))} · {fecha_rel(d, hoy)}</div></div>'
            f'<div class="res-nums">{nums}</div>{CHEV}</a>'
        )
    return "\n".join(filas)


def anguila(juegos, hoy):
    ang = [j for j in juegos if j["compania"] == "Anguila"]
    ang.sort(key=lambda j: (minutos_juego(limpiar(j["juego"])) or 0, limpiar(j["juego"])))
    out = []
    for j in ang:
        salio = parse_fecha(j.get("fecha")) == hoy
        valor = " · ".join(esc(n) for n in j["numeros"]) if salio else "Pendiente"
        mins = minutos_juego(limpiar(j["juego"]))
        es_hora = limpiar(j["juego"]).startswith("Anguila ") and mins is not None
        tag, cierre = (f'a class="ang{"" if salio else " pend"}" href="anguila/{slug_hora(mins)}/"', "a") if es_hora else \
                      (f'div class="ang{"" if salio else " pend"}"', "div")
        out.append(f'<{tag}><div class="ang-h">{esc(hora_anguila(j["juego"]))}</div>'
                   f'<div class="ang-n">{valor}</div></{cierre}>')
    return "\n".join(out)


def enlace_juego(comp, juego):
    from generate_juegos import JUEGOS
    n = limpiar(juego)
    for slug, _nom, _h, claves in JUEGOS:
        if (comp, n) in claves:
            return f'<a href="{slug}/">{esc(n)}</a>'
    return esc(n)


def titulo_y_descr(html, res, hoy):
    """Título y descripción de la portada con la fecha y los números del día (mejora el clic en Google)."""
    mes = MESES[hoy.month - 1]
    title = f"Lotería de Hoy {hoy.day} de {mes.capitalize()}: Resultados RD | Portal Dominicano"
    partes = []
    for comp, cands in RESUMEN:
        if comp == "Anguila" or not cands:
            continue
        js = {limpiar(j["juego"]): j for j in res.get("juegos", []) if j["compania"] == comp}
        ops = [js[g] for g, _m in cands if g in js]
        if ops:
            j = max(ops, key=lambda x: ((x.get("fecha") or "")[:10], [g for g, _m in cands].index(limpiar(x["juego"]))))
            partes.append(f"{NOMBRE_COMPANIA[comp].replace('Lotería ', '')} {'-'.join(j['numeros'])}")
    desc = (f"Lotería de hoy en RD, últimos resultados: " + ", ".join(partes[:4])
            + ". Todas las loterías, Anguila hora por hora, dólar, combustibles y Lidom.")
    html = re.sub(r"<title>[^<]*</title>", lambda m: f"<title>{esc(title)}</title>", html, count=1)
    for patron, valor in [(r'(<meta name="description" content=")[^"]*(")', desc),
                          (r'(<meta property="og:title" content=")[^"]*(")', title),
                          (r'(<meta property="og:description" content=")[^"]*(")', desc),
                          (r'(<meta name="twitter:title" content=")[^"]*(")', title),
                          (r'(<meta name="twitter:description" content=")[^"]*(")', desc)]:
        html = re.sub(patron, lambda m: m.group(1) + esc(valor) + m.group(2), html, count=1)
    return html


def todos(juegos, hoy):
    por_comp = {}
    for j in juegos:
        por_comp.setdefault(j["compania"], []).append(j)
    partes = []
    for comp in ORDEN_COMPANIAS:
        lista = por_comp.get(comp)
        if not lista:
            continue
        partes.append(f'<div class="lot-comp" data-comp="{esc(comp)}"><a href="{SLUG_COMPANIA[comp]}/">{esc(NOMBRE_COMPANIA[comp])}</a></div>')
        for j in ordenar_juegos(comp, lista):
            d = parse_fecha(j.get("fecha"))
            meta = f'<span class="lot-fecha">{fecha_corta(d)}</span>' if d else ""
            if d and d < hoy:
                meta += '<span class="lot-dia">día anterior</span>'
            partes.append(
                f'<div class="lot-card" data-comp="{esc(comp)}" data-numeros="{esc(",".join(j["numeros"]))}">'
                f'<div class="game">{enlace_juego(comp, j["juego"])}</div>'
                + (f'<div class="lot-meta">{meta}</div>' if meta else "")
                + f'<div class="nums">{balls_html(j["numeros"])}</div></div>'
            )
    return "\n".join(partes)


def dolar():
    dv = cargar_json("divisas.json", {}) or {}
    conv = {(c.get("codigo"), c.get("a")): c.get("valor") for c in dv.get("conversiones", [])}
    usd, eur = conv.get(("USD", "DOP")) or dv.get("dop_por_usd"), conv.get(("EUR", "DOP"))
    if not usd:
        return '<span class="tile-k">Dólar hoy</span><span class="tile-t">Tasa de cambio</span><span class="tile-s">USD, euro y más</span>'
    sub = f'<span class="tile-s">Euro: RD${eur:.2f}</span>' if eur else '<span class="tile-s">Peso dominicano</span>'
    return f'<span class="tile-k">Dólar hoy</span><span class="tile-v">RD${usd:.2f}</span>{sub}'


def tile_combustibles():
    c = cargar_json("combustibles.json", {}) or {}
    p = c.get("precios") or {}
    if not p.get("premium"):
        return '<span class="tile-k">Combustibles</span><span class="tile-t">Precios de la semana</span><span class="tile-s">Gasolina, gasoil y GLP</span>'
    reg = f'<span class="tile-s">Regular: RD${p["regular"]:.2f}</span>' if p.get("regular") else ""
    return f'<span class="tile-k">Gasolina premium</span><span class="tile-v">RD${p["premium"]:.2f}</span>{reg}'


def tile_lidom(hoy):
    L = cargar_json("lidom.json", {}) or {}
    tabla = L.get("tabla") or []
    if not tabla:
        return '<span class="tile-k">Lidom</span><span class="tile-t">Béisbol invernal</span><span class="tile-s">Resultados y posiciones</span>'
    lider = tabla[0]
    nombre = {"Aguilas Cibaenas": "Águilas Cibaeñas"}.get(lider.get("nombre"), lider.get("nombre") or lider["equipo"])
    n_hoy = sum(1 for j in L.get("juegos", []) if j.get("fecha") == hoy.isoformat())
    sub = f"{n_hoy} juego{'s' if n_hoy != 1 else ''} hoy" if n_hoy else "Resultados y posiciones"
    empatados = sum(1 for t in tabla if t.get("pct") == lider.get("pct"))
    if empatados > 1:
        return (f'<span class="tile-k">Lidom</span><span class="tile-t">{empatados} equipos empatados en el 1.º ({lider["g"]}-{lider["p"]})</span>'
                f'<span class="tile-s">{sub}</span>')
    return (f'<span class="tile-k">Lidom · líder</span><span class="tile-t">{esc(nombre)} ({lider["g"]}-{lider["p"]})</span>'
            f'<span class="tile-s">{sub}</span>')


def main():
    res = cargar_json("resultados.json", {}) or {}
    juegos = res.get("juegos", [])
    upd = actualizado_rd(res)
    hoy = upd.date()
    with open(INDEX, encoding="utf-8") as f:
        html = f.read()
    html = zona(html, "RESUMEN", resumen(juegos, hoy))
    html = titulo_y_descr(html, res, hoy)
    html = zona(html, "ANGUILA", anguila(juegos, hoy))
    html = zona(html, "LOTERIA", todos(juegos, hoy))
    html = zona(html, "DOLAR", dolar())
    html = zona(html, "COMBUSTIBLES", tile_combustibles())
    html = zona(html, "LIDOM", tile_lidom(hoy))
    try:
        with open(os.path.join(ROOT, "data", "tarjeta.txt"), encoding="utf-8") as f:
            texto = f.read().strip()
    except FileNotFoundError:
        texto = "Resultados de la lotería de hoy: https://portaldominicana.net/"
    from urllib.parse import quote
    html = zona(html, "COMPARTIR",
                f'<a class="btn-wa" href="https://wa.me/?text={quote(texto)}" target="_blank" rel="noopener">Compartir resultados por WhatsApp</a>'
                '<a class="btn-img" href="compartir/resultados-hoy.png" download>Descargar imagen</a>')
    fecha_txt = f"{DIAS[hoy.weekday()].capitalize()} {hoy.day} de {MESES[hoy.month - 1]}"
    html = re.sub(r'(<span class="meta" id="loteria-fecha">)[^<]*(</span>)',
                  lambda m: m.group(1) + fecha_txt + m.group(2), html, count=1)
    html = re.sub(r'(id="updated">)[^<]*(<)',
                  lambda m: m.group(1) + f"{fecha_txt} · Actualizado a las {hora_12(upd)} (hora RD)" + m.group(2),
                  html, count=1)
    with open(INDEX, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"OK: portada con resumen, Anguila y {len(juegos)} juegos escritos en el HTML")


if __name__ == "__main__":
    main()
