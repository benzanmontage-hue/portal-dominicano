#!/usr/bin/env python3
"""Página /lidom/: juegos de hoy, tabla de posiciones, resultados recientes y próximos juegos.

Lee data/lidom.json (scripts/scrape_lidom.py, fuente MLB Stats API).
"""
import datetime

from comun import BASE, MESES, DIAS, esc, cargar_json, TZ_RD
from plantilla import pagina, jsonld, faq_ld, faq_html, escribir

ACENTOS = {"Aguilas Cibaenas": "Águilas Cibaeñas", "Aguilas": "Águilas"}


def nom(n):
    return ACENTOS.get(n, n)


def d(f):
    return datetime.date.fromisoformat(f)


def hora12(hhmm):
    h, m = map(int, hhmm.split(":"))
    return f"{h % 12 or 12}:{m:02d} {'AM' if h < 12 else 'PM'}"


def racha(code):
    if not code:
        return ""
    return ("G" if code[0] == "W" else "P" if code[0] == "L" else code[0]) + code[1:]


def fila_juego(j, mostrar_fecha=False):
    v, l = esc(nom(j["visitante"])), esc(nom(j["local"]))
    cv, cl = j.get("carreras_v"), j.get("carreras_l")
    if j["estado"] == "Final" and cv is not None:
        gan_v = cv > cl
        marcador = (f'<span class="{"gan" if gan_v else ""}">{v} {cv}</span> – '
                    f'<span class="{"gan" if not gan_v else ""}">{l} {cl}</span>')
        est = "Final"
    elif j["estado"] == "Live":
        marcador = f"{v} {cv if cv is not None else 0} – {l} {cl if cl is not None else 0}"
        est = "En vivo"
    else:
        marcador = f"{v} vs. {l}"
        est = "Pospuesto" if "Postponed" in j.get("detalle", "") else hora12(j["hora"])
    cuando = f"{DIAS[d(j['fecha']).weekday()][:3]} {d(j['fecha']).day} {MESES[d(j['fecha']).month - 1][:3]} · " if mostrar_fecha else ""
    return (f'<li class="juego"><div class="j-m">{marcador}</div>'
            f'<div class="j-s">{cuando}{esc(est)}{" · " + esc(j["estadio"]) if j.get("estadio") else ""}</div></li>')


def main():
    L = cargar_json("lidom.json")
    if not L or not L.get("tabla"):
        print("lidom: sin datos, no se genera la página")
        return
    ahora = datetime.datetime.now(TZ_RD)
    hoy = ahora.date().isoformat()
    upd = datetime.datetime.fromisoformat(L["updated"]).astimezone(TZ_RD)
    juegos = sorted(L.get("juegos", []), key=lambda j: (j["fecha"], j["hora"]))
    de_hoy = [j for j in juegos if j["fecha"] == hoy]
    futuros = [j for j in juegos if j["fecha"] > hoy]
    pasados = [j for j in juegos if j["fecha"] < hoy and j["estado"] == "Final"]

    tabla = L["tabla"]
    filas = "".join(
        f'<tr><td>{t["pos"]}</td><td><strong>{esc(nom(t["nombre"]))}</strong></td><td class="n">{t["g"]}</td>'
        f'<td class="n">{t["p"]}</td><td class="n">{esc(t["pct"])}</td><td class="n">{esc(t["dif"])}</td>'
        f'<td>{esc(racha(t["racha"]))}</td></tr>' for t in tabla)

    if de_hoy:
        bloque_hoy = '<ul class="juegos-l">' + "".join(fila_juego(j) for j in de_hoy) + "</ul>"
    else:
        sig = futuros[0]["fecha"] if futuros else None
        bloque_hoy = '<p class="intro">Hoy no hay juegos programados.' + (
            f' Los próximos son el {esc(DIAS[d(sig).weekday()])} {d(sig).day} de {MESES[d(sig).month - 1]}.' if sig else "") + "</p>"

    recientes = []
    for f in sorted({j["fecha"] for j in pasados}, reverse=True)[:5]:
        df = d(f)
        recientes.append(f'<h3 class="sub-h">{DIAS[df.weekday()].capitalize()} {df.day} de {MESES[df.month - 1]}</h3>'
                         '<ul class="juegos-l">' + "".join(fila_juego(j) for j in pasados if j["fecha"] == f) + "</ul>")
    proximos = '<ul class="juegos-l">' + "".join(fila_juego(j, True) for j in futuros[:9]) + "</ul>" if futuros else \
        '<p class="intro">No hay más juegos programados por ahora.</p>'

    lider = tabla[0]
    empatados = [t for t in tabla if t["pct"] == lider["pct"]]
    if len(empatados) > 1:
        lider_txt = ("Están empatados en el primer lugar " + ", ".join(nom(t["nombre"]) for t in empatados[:-1])
                     + f" y {nom(empatados[-1]['nombre'])}, con récord de {lider['g']}-{lider['p']}.")
    else:
        lider_txt = f"{nom(lider['nombre'])} va primero con récord de {lider['g']}-{lider['p']}."
    fin_reg = L.get("fin_regular")
    temp = f"{L['temporada']}-{str(int(L['temporada']) + 1)[2:]}" if str(L.get("temporada", "")).isdigit() else L.get("temporada", "")
    faqs = [
        ("¿Quién va primero en Lidom?", lider_txt + f" Tabla actualizada el {upd.day} de {MESES[upd.month - 1]}."),
        ("¿Cuáles son los equipos de Lidom?",
         "Los seis equipos son " + ", ".join(nom(t["nombre"]) for t in tabla[:-1]) + f" y {nom(tabla[-1]['nombre'])}."),
    ]
    if fin_reg:
        faqs.append(("¿Cuándo termina la serie regular de Lidom?",
                     f"La serie regular de la temporada {temp} termina el {d(fin_reg).day} de {MESES[d(fin_reg).month - 1]} de {d(fin_reg).year}; "
                     "después vienen el Round Robin y la Serie Final."))
    ultimo = pasados[-1] if pasados else None
    if ultimo:
        faqs.append(("¿Cómo quedó el último juego de Lidom?",
                     f"{nom(ultimo['visitante'])} {ultimo['carreras_v']}, {nom(ultimo['local'])} {ultimo['carreras_l']} "
                     f"({DIAS[d(ultimo['fecha']).weekday()]} {d(ultimo['fecha']).day} de {MESES[d(ultimo['fecha']).month - 1]})."))

    hoy_d = ahora.date()
    cuerpo = f"""  <p class="intro">Resultados de <strong>Lidom hoy</strong>, juegos del día y <strong>tabla de posiciones</strong> de la temporada {esc(temp)} del béisbol invernal dominicano. {esc(lider_txt)}</p>
  <p class="upd">Actualizado: {upd.strftime('%d/%m/%Y')} {hora12(upd.strftime('%H:%M'))} (hora RD)</p>
  <h2 class="sect"><span class="bar"></span> Juegos de hoy, {DIAS[hoy_d.weekday()]} {hoy_d.day} de {MESES[hoy_d.month - 1]}</h2>
  {bloque_hoy}
  <h2 class="sect"><span class="bar"></span> Tabla de posiciones</h2>
  <div class="tabla-wrap"><table><thead><tr><th>#</th><th>Equipo</th><th>G</th><th>P</th><th>PCT</th><th>Dif.</th><th>Racha</th></tr></thead><tbody>{filas}</tbody></table></div>
  <h2 class="sect"><span class="bar"></span> Resultados recientes</h2>
  {''.join(recientes) or '<p class="intro">Aún no hay resultados.</p>'}
  <h2 class="sect"><span class="bar"></span> Próximos juegos</h2>
  {proximos}
  <p class="nota">Horas en hora de República Dominicana. Datos: MLB Stats API; verifica con la liga oficial (Lidom).</p>
  <h2 class="sect"><span class="bar"></span> Preguntas frecuentes</h2>
  <div class="faq">
    {faq_html(faqs)}
  </div>"""
    ruta = "/lidom/"
    title = f"Lidom Hoy: Resultados, Juegos y Tabla de Posiciones {temp}"
    desc = (f"Resultados de Lidom de hoy, juegos del día y tabla de posiciones de la temporada {temp}: "
            "Licey, Águilas, Escogido, Estrellas, Toros y Gigantes.")
    migas = [("Portal Dominicano", "/"), ("Lidom", ruta)]
    ld = jsonld(BASE + ruta, "Lidom hoy: resultados y tabla de posiciones", desc, migas,
                extra=[faq_ld(BASE + ruta, faqs)], fecha_mod=L["updated"])
    escribir(ruta, pagina(ruta=ruta, title=title, desc=desc, h1="Lidom hoy: resultados y tabla de posiciones",
                          sub=f"Béisbol invernal dominicano · Temporada {temp}", migas=migas, cuerpo=cuerpo, ld=ld))
    print("OK: /lidom/")


if __name__ == "__main__":
    main()
