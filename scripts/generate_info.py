#!/usr/bin/env python3
"""Páginas informativas: /horarios-loterias/ y /feriados/.

Horarios: solo los que coinciden en varias fuentes (verificados el 18-oct-2026 con
loteriasdominicanas.com/pagina/horarios, rdparty.com y El Caribe). Donde las fuentes no
coinciden se indica el rango o se omite. Los sitios oficiales no se pudieron consultar.

Feriados: 2026 según el anuncio del Ministerio de Trabajo (nov 2025); 2027 calculado con la
Ley 139-97 (pendiente de confirmación oficial).
"""
import datetime

from comun import BASE, MESES, DIAS, esc, TZ_RD, SLUG_COMPANIA
from plantilla import pagina, jsonld, faq_ld, faq_html, escribir

# (compañía, juego, días, hora)  — hora en texto, hora RD
HORARIOS = [
    ("Anguila", "Sorteos cada hora", "Todos los días", "8:00 AM a 10:00 PM"),
    ("Anguila", "La Cuarteta", "Todos los días", "10:00 AM, 1:00 PM, 6:00 PM y 9:00 PM"),
    ("La Primera", "La Primera Día y El Quinielón Día", "Todos los días", "12:00 PM"),
    ("La Suerte", "La Suerte Día", "Todos los días", "12:30 PM"),
    ("Loteria Real", "Quiniela Real", "Todos los días", "12:55 PM"),
    ("Loteria Real", "Pega 4 Real", "Lunes a sábado", "12:55 PM"),
    ("Nacional", "Gana Más", "Todos los días", "2:30 PM"),
    ("Nacional", "Juega + Pega +", "Lunes a sábado", "2:30 PM"),
    ("La Suerte", "La Suerte Tarde", "Todos los días", "6:00 PM"),
    ("Nacional", "Lotería Nacional (domingo)", "Domingo", "6:00 PM"),
    ("Nacional", "Billetes Domingo", "Domingos seleccionados", "6:00 PM"),
    ("Loteka", "Quiniela Loteka, Mega Chances y Toca 3", "Todos los días", "7:55 PM"),
    ("Loteka", "MegaLotto", "Lunes y jueves", "7:55 PM"),
    ("La Primera", "Primera Noche, El Quinielón Noche y Loto 5", "Todos los días", "8:00 PM"),
    ("Nacional", "Lotería Nacional (noche)", "Lunes a sábado", "Entre 8:50 y 9:00 PM"),
    ("Leidsa", "Quiniela Leidsa, Pega 3 Más, Loto Pool y Super Kino TV", "Lunes a sábado", "8:55 PM"),
    ("Leidsa", "Quiniela Leidsa (domingo)", "Domingo", "3:55 PM"),
    ("Leidsa", "Loto - Super Loto Más", "Miércoles y sábado", "8:55 PM"),
]
NOMBRE = {"Nacional": "Lotería Nacional", "Loteria Real": "Lotería Real", "Anguila": "Anguila", "Loteka": "Loteka",
          "La Primera": "La Primera", "La Suerte": "La Suerte", "Leidsa": "Leidsa"}

# (fecha, nombre, fecha original si se traslada, nota)
FERIADOS = {
    2026: [("2026-01-01", "Año Nuevo", None), ("2026-01-05", "Día de los Santos Reyes", "2026-01-06"),
           ("2026-01-21", "Día de la Altagracia", None), ("2026-01-26", "Día de Duarte", None),
           ("2026-02-27", "Día de la Independencia", None), ("2026-04-03", "Viernes Santo", None),
           ("2026-05-04", "Día del Trabajo", "2026-05-01"), ("2026-06-04", "Corpus Christi", None),
           ("2026-08-16", "Día de la Restauración", None), ("2026-09-24", "Día de las Mercedes", None),
           ("2026-11-09", "Día de la Constitución", "2026-11-06"), ("2026-12-25", "Navidad", None)],
    2027: [("2027-01-01", "Año Nuevo", None), ("2027-01-04", "Día de los Santos Reyes", "2027-01-06"),
           ("2027-01-21", "Día de la Altagracia", None), ("2027-01-25", "Día de Duarte", "2027-01-26"),
           ("2027-02-27", "Día de la Independencia", None), ("2027-03-26", "Viernes Santo", None),
           ("2027-05-01", "Día del Trabajo", None), ("2027-05-27", "Corpus Christi", None),
           ("2027-08-16", "Día de la Restauración", None), ("2027-09-24", "Día de las Mercedes", None),
           ("2027-11-06", "Día de la Constitución", None), ("2027-12-25", "Navidad", None)],
}
OFICIAL = {2026: True, 2027: False}


def d(f):
    return datetime.date.fromisoformat(f)


def larga(x):
    return f"{DIAS[x.weekday()]} {x.day} de {MESES[x.month - 1]} de {x.year}"


def horarios(hoy):
    ruta = "/horarios-loterias/"
    filas = "".join(
        f'<tr><td><a href="/{SLUG_COMPANIA[c]}/">{esc(NOMBRE[c])}</a></td><td>{esc(j)}</td><td>{esc(dias)}</td>'
        f'<td class="n">{esc(h)}</td></tr>' for c, j, dias, h in HORARIOS)
    faqs = [
        ("¿A qué hora juega la Lotería Nacional?", "Gana Más juega a las 2:30 PM todos los días. La Lotería Nacional de la noche juega de lunes a sábado entre las 8:50 y las 9:00 PM, y el domingo a las 6:00 PM."),
        ("¿A qué hora juega Leidsa?", "La Quiniela Leidsa juega de lunes a sábado a las 8:55 PM y el domingo a las 3:55 PM. El Loto (Super Loto Más) juega miércoles y sábado a las 8:55 PM."),
        ("¿A qué hora juega Loteka?", "Loteka sortea todos los días a las 7:55 PM. MegaLotto juega lunes y jueves."),
        ("¿A qué hora juega La Primera?", "La Primera Día juega a las 12:00 PM y la Primera Noche a las 8:00 PM, todos los días."),
        ("¿A qué hora juega La Suerte?", "La Suerte tiene dos sorteos diarios: 12:30 PM y 6:00 PM."),
        ("¿A qué hora juega la Lotería Real?", "La Quiniela Real juega todos los días a las 12:55 PM."),
        ("¿A qué hora juega Anguila?", "Anguila sortea cada hora desde las 8:00 AM hasta las 10:00 PM. La Cuarteta juega a las 10:00 AM, 1:00 PM, 6:00 PM y 9:00 PM."),
    ]
    cuerpo = f"""  <p class="intro">Horarios de los sorteos de las loterías dominicanas en <strong>hora de República Dominicana</strong>, ordenados del más temprano al más tarde. En días feriados algunos horarios cambian.</p>
  <h2 class="sect"><span class="bar"></span> Horarios de los sorteos</h2>
  <div class="tabla-wrap"><table><thead><tr><th>Lotería</th><th>Sorteo</th><th>Días</th><th>Hora RD</th></tr></thead><tbody>{filas}</tbody></table></div>
  <p class="nota">En Nueva York y Miami la hora es la misma que en RD durante el horario de verano de EE. UU. (marzo–noviembre) y una hora menos el resto del año. Horarios contrastados en varias fuentes; confírmalos siempre con la lotería oficial.</p>
  <h2 class="sect"><span class="bar"></span> Preguntas frecuentes</h2>
  <div class="faq">
    {faq_html(faqs)}
  </div>"""
    title = "Horarios de las Loterías Dominicanas — Hora de cada Sorteo"
    desc = "¿A qué hora juega cada lotería? Horarios de Lotería Nacional, Leidsa, Loteka, Real, La Primera, La Suerte y Anguila en hora de República Dominicana."
    migas = [("Portal Dominicano", "/"), ("Horarios de las loterías", ruta)]
    ld = jsonld(BASE + ruta, "Horarios de las loterías dominicanas", desc, migas, extra=[faq_ld(BASE + ruta, faqs)])
    escribir(ruta, pagina(ruta=ruta, title=title, desc=desc, h1="Horarios de las loterías dominicanas",
                          sub="Hora de República Dominicana (UTC-4)", migas=migas, cuerpo=cuerpo, ld=ld))


def feriados(hoy):
    ruta = "/feriados/"
    todos = [(d(f), n, d(o) if o else None, y) for y, l in FERIADOS.items() for f, n, o in l]
    prox = next(((f, n, o, y) for f, n, o, y in todos if f >= hoy), None)
    bloques = []
    for y, lista in FERIADOS.items():
        filas = []
        for f, n, o in lista:
            fd = d(f)
            nota = f"Trasladado del {larga(d(o)).split(' de ' + str(fd.year))[0]}" if o else ""
            pasado = ' style="opacity:.6"' if fd < hoy else ""
            filas.append(f"<tr{pasado}><td>{esc(larga(fd).capitalize())}</td><td>{esc(n)}</td><td>{esc(nota)}</td></tr>")
        aviso = ("Calendario anunciado por el Ministerio de Trabajo." if OFICIAL[y] else
                 "Calculado según la Ley 139-97; el Ministerio de Trabajo aún no ha publicado el calendario oficial.")
        bloques.append(f'  <h2 class="sect" id="feriados-{y}"><span class="bar"></span> Días feriados {y}</h2>\n'
                       f'  <div class="tabla-wrap"><table><thead><tr><th>Fecha</th><th>Feriado</th><th>Nota</th></tr></thead>'
                       f'<tbody>{"".join(filas)}</tbody></table></div>\n  <p class="nota">{aviso}</p>')
    prox_txt = ""
    if prox:
        f, n, o, y = prox
        faltan = (f - hoy).days
        cuando = "hoy" if faltan == 0 else ("mañana" if faltan == 1 else f"en {faltan} días")
        prox_txt = (f'  <div class="resumen-txt"><strong>Próximo feriado:</strong> {esc(n)}, {esc(larga(f))} ({cuando})'
                    + (f". Se celebra el {esc(larga(o))} pero el descanso pasa al lunes." if o else ".") + "</div>")
    faqs = [
        ("¿Cuál es el próximo día feriado en República Dominicana?",
         f"El próximo feriado es {prox[1]}, el {larga(prox[0])}." if prox else "Consulta la tabla de feriados."),
        ("¿Por qué algunos feriados se mueven al lunes?",
         "La Ley 139-97 manda trasladar al lunes los feriados que caen de martes a viernes (al lunes anterior si caen martes o miércoles, al siguiente si caen jueves o viernes). No se trasladan Año Nuevo, Altagracia, Independencia, Mercedes, Navidad, Viernes Santo ni Corpus Christi."),
        ("¿Cuándo es Semana Santa en 2027?", "En 2027 el Viernes Santo es el 26 de marzo."),
    ]
    cuerpo = f"""  <p class="intro">Calendario de <strong>días feriados de República Dominicana</strong> 2026 y 2027, con los feriados que se trasladan al lunes según la Ley 139-97.</p>
{prox_txt}
{chr(10).join(bloques)}
  <h2 class="sect"><span class="bar"></span> Preguntas frecuentes</h2>
  <div class="faq">
    {faq_html(faqs)}
  </div>
  <p class="nota">Fuentes: anuncio del Ministerio de Trabajo para 2026 (vía El Caribe) y Ley 139-97. Verifica cambios de último momento con el Ministerio de Trabajo.</p>"""
    title = "Días Feriados 2026 y 2027 en República Dominicana — Calendario"
    desc = "Calendario de días feriados en República Dominicana 2026 y 2027: fechas, feriados que se mueven al lunes y el próximo feriado."
    migas = [("Portal Dominicano", "/"), ("Días feriados", ruta)]
    ld = jsonld(BASE + ruta, "Días feriados de República Dominicana", desc, migas, extra=[faq_ld(BASE + ruta, faqs)])
    escribir(ruta, pagina(ruta=ruta, title=title, desc=desc, h1="Días feriados en República Dominicana",
                          sub="Calendario 2026 y 2027", migas=migas, cuerpo=cuerpo, ld=ld))


def main():
    hoy = datetime.datetime.now(TZ_RD).date()
    horarios(hoy)
    feriados(hoy)
    print("OK: /horarios-loterias/ y /feriados/")


if __name__ == "__main__":
    main()
