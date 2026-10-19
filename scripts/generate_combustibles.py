#!/usr/bin/env python3
"""Página /combustibles/: precios de la semana, cambio frente a la semana anterior e historial.

Lee data/combustibles.json y data/combustibles_historial.json (scripts/scrape_combustibles.py).
"""
import datetime

from comun import BASE, MESES, esc, cargar_json, TZ_RD
from plantilla import pagina, jsonld, faq_ld, faq_html, escribir
from scrape_combustibles import PRODUCTOS


def d(f):
    return datetime.date.fromisoformat(f)


def rango(ini, fin):
    if ini.month == fin.month:
        return f"{ini.day} al {fin.day} de {MESES[fin.month - 1]} de {fin.year}"
    return f"{ini.day} de {MESES[ini.month - 1]} al {fin.day} de {MESES[fin.month - 1]} de {fin.year}"


def rd(v):
    return f"RD${v:,.2f}"


def main():
    c = cargar_json("combustibles.json")
    hist = cargar_json("combustibles_historial.json", {}) or {}
    if not c or not c.get("precios"):
        print("combustibles: sin datos, no se genera la página")
        return
    ini, fin = d(c["inicio"]), d(c["fin"])
    hoy = datetime.datetime.now(TZ_RD).date()
    precios = c["precios"]
    semanas = sorted(hist)
    previa = None
    if c["inicio"] in semanas and semanas.index(c["inicio"]) > 0:
        previa = hist[semanas[semanas.index(c["inicio"]) - 1]]["precios"]

    filas, cambios = [], []
    for clave, nombre, _p, unidad, _r in PRODUCTOS:
        if clave not in precios:
            continue
        v = precios[clave]
        cambio = "—"
        if previa and clave in previa:
            dif = round(v - previa[clave], 2)
            if dif > 0:
                cambio = f"Sube {rd(dif)}"
                cambios.append(f"{nombre} sube {rd(dif)}")
            elif dif < 0:
                cambio = f"Baja {rd(-dif)}"
                cambios.append(f"{nombre} baja {rd(-dif)}")
            else:
                cambio = "Sin cambio"
        filas.append(f'<tr><td>{esc(nombre)}</td><td class="n">{rd(v)}</td><td>{esc(unidad)}</td><td>{esc(cambio)}</td></tr>')

    if previa is None:
        resumen_cambio = ""
    elif cambios:
        resumen_cambio = " Cambios frente a la semana anterior: " + "; ".join(cambios) + "."
    else:
        resumen_cambio = " Todos los precios se mantienen igual que la semana anterior."
    vieja = ""
    if hoy > fin:
        vieja = ('<p class="resumen-txt"><strong>Atención:</strong> estos son los precios de la semana pasada. '
                 'El MICM anuncia los nuevos precios los viernes por la tarde; esta página se actualiza sola.</p>')

    lead = (f"Esta semana la <strong>gasolina premium</strong> cuesta <strong>{rd(precios['premium'])}</strong> por galón "
            f"y la <strong>regular {rd(precios['regular'])}</strong>.") if "premium" in precios and "regular" in precios else ""

    # historial (últimas 10 semanas)
    cols = [(k, n) for k, n, *_ in PRODUCTOS if k != "gnv"]
    th = "".join(f"<th>{esc(n.replace('Gasolina ', 'Gas. ').replace(' (GLP)', ''))}</th>" for _k, n in cols)
    hfilas = []
    for s in reversed(semanas[-10:]):
        h = hist[s]
        celdas = "".join(f'<td class="n">{rd(h["precios"][k]) if k in h["precios"] else "—"}</td>' for k, _n in cols)
        hfilas.append(f"<tr><td>{d(s).day} {MESES[d(s).month - 1][:3]} – {d(h['fin']).day} {MESES[d(h['fin']).month - 1][:3]}</td>{celdas}</tr>")

    sem_txt = rango(ini, fin)
    faqs = [
        ("¿Cuánto cuesta la gasolina esta semana en República Dominicana?",
         f"Del {sem_txt}, la gasolina premium cuesta {rd(precios.get('premium', 0))} y la regular {rd(precios.get('regular', 0))} por galón; "
         f"el gasoil óptimo {rd(precios.get('gasoil_optimo', 0))} y el regular {rd(precios.get('gasoil_regular', 0))}."),
        ("¿Cuánto cuesta el gas (GLP) esta semana?", f"El gas licuado de petróleo (GLP) cuesta {rd(precios['glp'])} por galón." if "glp" in precios else "Consulta la tabla de precios."),
        ("¿Cuándo cambian los precios de los combustibles?",
         "El Ministerio de Industria, Comercio y Mipymes (MICM) anuncia los precios cada viernes por la tarde. Rigen desde el sábado hasta el viernes siguiente."),
    ]
    cuerpo = f"""  <p class="intro">{lead}{esc(resumen_cambio)} Precios oficiales fijados por el MICM para la semana del {esc(sem_txt)}.</p>
  {vieja}
  <h2 class="sect"><span class="bar"></span> Precios de esta semana</h2>
  <div class="tabla-wrap"><table><thead><tr><th>Combustible</th><th>Precio</th><th>Por</th><th>Cambio</th></tr></thead><tbody>{''.join(filas)}</tbody></table></div>
  <h2 class="sect"><span class="bar"></span> Historial de precios</h2>
  <div class="tabla-wrap"><table><thead><tr><th>Semana</th>{th}</tr></thead><tbody>{''.join(hfilas)}</tbody></table></div>
  <p class="nota">Precios por galón. Fuente: Ministerio de Industria, Comercio y Mipymes (MICM), vía prestocombustibles.com. Verifica siempre con el MICM.</p>
  <h2 class="sect"><span class="bar"></span> Preguntas frecuentes</h2>
  <div class="faq">
    {faq_html(faqs)}
  </div>"""
    ruta = "/combustibles/"
    titulo_sem = f"{ini.day} al {fin.day} de {MESES[fin.month - 1].capitalize()}" if ini.month == fin.month else \
        f"{ini.day} de {MESES[ini.month - 1].capitalize()} al {fin.day} de {MESES[fin.month - 1].capitalize()}"
    title = f"Precio de la Gasolina Hoy RD: Semana del {titulo_sem}"
    desc = (f"Precios de los combustibles en República Dominicana del {sem_txt}: gasolina premium {rd(precios.get('premium', 0))}, "
            f"regular {rd(precios.get('regular', 0))}, gasoil y GLP. Cambios e historial semanal.")
    migas = [("Portal Dominicano", "/"), ("Combustibles", ruta)]
    ld = jsonld(BASE + ruta, "Precios de los combustibles en RD", desc, migas, extra=[faq_ld(BASE + ruta, faqs)],
                fecha_mod=c.get("updated"))
    escribir(ruta, pagina(ruta=ruta, title=title, desc=desc, h1="Precios de los combustibles en RD",
                          sub=f"Semana del {sem_txt}", chip="Precios oficiales del MICM", migas=migas, cuerpo=cuerpo, ld=ld))
    print("OK: /combustibles/")


if __name__ == "__main__":
    main()
