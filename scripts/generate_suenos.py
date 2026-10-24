#!/usr/bin/env python3
"""Tabla de sueños (charada): /suenos/ y una página por sueño (/suenos/muerto/ …).

Cada página de sueño, además del número y sus otros significados, muestra datos propios:
cuántas veces salió ese número en las loterías dominicanas en los días guardados y cuándo
fue la última vez. El índice traduce a la charada los números de hoy.
Lee scripts/charada.py, data/resultados.json y data/archivo.json.
"""
import datetime

from comun import (BASE, MESES, ORDEN_COMPANIAS, NOMBRE_COMPANIA, esc, limpiar, cargar_json, parse_fecha,
                   fecha_larga, actualizado_rd, fechas_con_pagina, titulo, TZ_RD)
from charada import CHARADA, slug, jugada, de_jugada
from plantilla import pagina, jsonld, faq_ld, faq_html, escribir
from prerender_home import RESUMEN

AVISO = ("La charada es una tradición popular para traducir sueños a números. "
         "Los sorteos son al azar: ningún sueño ni tabla aumenta la probabilidad de ganar. Juega con responsabilidad (+18).")

CSS_BUSCA = ('<style>.busca{width:100%;min-height:48px;border:1.5px solid var(--border);border-radius:12px;padding:0 14px;'
             'font:inherit;font-size:1rem;background:var(--card);color:var(--txt);margin-bottom:12px}'
             '.charada td:first-child{font-weight:800;font-variant-numeric:tabular-nums;width:60px}</style>')


def apariciones(archivo):
    """{'08': [(fecha, compania, juego, [numeros]), ...]} solo de quinielas (3 números de 2 cifras)."""
    out = {}
    for clave, lista in (archivo.get("sorteos") or {}).items():
        comp, juego = clave.split("|", 1)
        for s in lista:
            nums = s["numeros"]
            if len(nums) != 3 or not all(len(n) == 2 and n.isdigit() for n in nums):
                continue
            for n in set(nums):
                out.setdefault(n, []).append((s["fecha"], comp, juego, nums))
    for n in out:
        out[n].sort(key=lambda x: x[0], reverse=True)
    return out


def dias_guardados(archivo):
    """Días con resultados completos guardados y el primero de ellos (inicio de los registros)."""
    completas = fechas_con_pagina(archivo)
    if completas:
        return len(completas), completas[0]
    fechas = sorted({s["fecha"] for l in (archivo.get("sorteos") or {}).values() for s in l})
    return len(fechas), (fechas[-1] if fechas else None)


def pagina_sueno(n, ap, n_dias, desde, con_pagina, upd):
    principal, otros = CHARADA[n]
    jug = jugada(n)
    ruta = f"/suenos/{slug(principal)}/"
    lista = ap.get(jug, [])
    ultimo = lista[0] if lista else None
    otros_txt = ", ".join(o.lower() for o in otros)

    if ultimo:
        f, comp, juego, _ = ultimo
        dato = (f"Desde el {esc(fecha_larga(parse_fecha(desde), con_anio=False))} (inicio de nuestros registros), el <strong>{jug}</strong> salió "
                f"<strong>{len(lista)} {'vez' if len(lista) == 1 else 'veces'}</strong> en las quinielas dominicanas. "
                f"La última vez fue el {esc(fecha_larga(parse_fecha(f)))} en {esc(limpiar(juego))} ({esc(NOMBRE_COMPANIA.get(comp, comp))}).")
    else:
        dato = f"Desde el {esc(fecha_larga(parse_fecha(desde), con_anio=False))} (inicio de nuestros registros), el {jug} no ha salido en las quinielas dominicanas."

    filas = []
    for f, comp, juego, nums in lista[:12]:
        txt = esc(fecha_larga(parse_fecha(f), con_anio=False))
        celda = f'<a href="/resultados/{f}/">{txt}</a>' if f in con_pagina else txt
        resaltado = " - ".join(f"<strong>{x}</strong>" if x == jug else x for x in nums)
        filas.append(f"<tr><td>{celda}</td><td>{esc(limpiar(juego))}</td><td class=\"n\">{resaltado}</td></tr>")
    tabla = ('<div class="tabla-wrap"><table><thead><tr><th>Fecha</th><th>Sorteo</th><th>Números</th></tr></thead>'
             f'<tbody>{"".join(filas)}</tbody></table></div>') if filas else ""

    vecinos = []
    for m in (n - 1, n + 1):
        if m in CHARADA:
            vecinos.append(f'<a href="/suenos/{slug(CHARADA[m][0])}/">{jugada(m)} {esc(CHARADA[m][0])}</a>')
    faqs = [
        (f"¿Qué número es {principal.lower()} en la charada?",
         f"En la charada, {principal.lower()} es el {n}" + (" (en la quiniela se juega como 00)" if n == 100 else "")
         + (f". El {jug} también se asocia con {otros_txt}." if otros else ".")),
        (f"¿Qué número jugar si soñé con {principal.lower()}?",
         f"Según la tabla de sueños tradicional, soñar con {principal.lower()} corresponde al {jug}. "
         "Recuerda que los sorteos son al azar."),
        (f"¿Cuándo salió el {jug} por última vez?",
         (f"El {jug} salió por última vez el {fecha_larga(parse_fecha(ultimo[0]))} en {limpiar(ultimo[2])}." if ultimo
          else f"No ha salido en las quinielas desde el {fecha_larga(parse_fecha(desde), con_anio=False)}.")),
    ]
    cuerpo = f"""  <p class="intro">En la charada (tabla de sueños), soñar con <strong>{esc(principal.lower())}</strong> corresponde al número <strong>{jug}</strong>{f' (el {n} de la charada)' if n == 100 else ''}.{f' Ese número también representa: {esc(otros_txt)}.' if otros else ''}</p>
  <div class="resumen-txt" style="font-size:1.05rem"><strong style="font-size:2rem;display:block;font-variant-numeric:tabular-nums">{jug}</strong>{esc(principal)}</div>
  <h2 class="sect"><span class="bar"></span> ¿Ha salido el {jug} en la quiniela?</h2>
  <p class="intro">{dato}</p>
  {tabla}
  <p class="nota">{esc(AVISO)}</p>
  <h2 class="sect"><span class="bar"></span> Números vecinos en la charada</h2>
  <nav class="otras" aria-label="Números vecinos">{' '.join(vecinos)} <a href="/suenos/">Tabla de sueños completa</a></nav>
  <h2 class="sect"><span class="bar"></span> Preguntas frecuentes</h2>
  <div class="faq">
    {faq_html(faqs)}
  </div>"""
    title = titulo(f"Soñar con {principal}: Número {jug}", "Charada y Tabla de Sueños")
    desc = (f"Soñar con {principal.lower()}: en la charada es el número {jug}"
            + (f" (también {otros_txt})" if otros else "") + ". Mira cuándo salió el "
            + f"{jug} por última vez en la lotería dominicana.")
    migas = [("Portal Dominicano", "/"), ("Tabla de sueños", "/suenos/"), (principal, ruta)]
    ld = jsonld(BASE + ruta, f"Soñar con {principal.lower()}: número {jug}", desc, migas,
                extra=[faq_ld(BASE + ruta, faqs)], fecha_mod=upd.isoformat(timespec="seconds"))
    escribir(ruta, pagina(ruta=ruta, title=title, desc=desc, h1=f"Soñar con {principal.lower()}: número {jug}",
                          sub="Charada y tabla de sueños", migas=migas, cuerpo=cuerpo, ld=ld))


def pagina_indice(res, n_dias, upd):
    ruta = "/suenos/"
    filas = "".join(
        f'<tr><td>{jugada(n)}</td><td><a href="/suenos/{slug(p)}/">{esc(p)}</a></td><td>{esc(", ".join(o))}</td></tr>'
        for n, (p, o) in CHARADA.items())
    hoy = []
    juegos = res.get("juegos", [])
    for comp, cands in RESUMEN:
        js = {limpiar(j["juego"]): j for j in juegos if j["compania"] == comp}
        if cands:
            ops = [js[g] for g, _m in cands if g in js]
        else:
            ops = [j for g, j in js.items() if g.startswith("Anguila ") and g[8:9].isdigit()]
        if not ops:
            continue
        j = max(ops, key=lambda x: (x.get("fecha") or "")[:10])
        partes = []
        for x in j["numeros"]:
            m = de_jugada(x)
            if m:
                partes.append(f'<a href="/suenos/{slug(CHARADA[m][0])}/">{x} {esc(CHARADA[m][0].lower())}</a>')
        if partes:
            hoy.append(f"<li><strong>{esc(NOMBRE_COMPANIA[comp])}</strong> ({esc(limpiar(j['juego']))}): {' · '.join(partes)}</li>")
    faqs = [
        ("¿Qué es la charada?", "Es una tabla tradicional que asigna una figura o significado a cada número del 1 al 100. En República Dominicana se usa para traducir sueños a números de la quiniela."),
        ("¿Qué número es el muerto?", "En la charada, el muerto es el 08; el muerto grande es el 64."),
        ("¿Qué número es el dinero?", "El dinero es el 38; la mariposa (02) y el majá (21) también se asocian con dinero."),
        ("¿Cómo se juega el 100 en la quiniela?", "La quiniela dominicana usa números del 00 al 99, así que el 100 de la charada se juega como 00."),
    ]
    cuerpo = f"""{CSS_BUSCA}
  <p class="intro">Busca tu sueño y encuentra su número en la <strong>charada</strong>, la tabla de sueños que se usa en República Dominicana para la quiniela. Cada sueño tiene su página con los días en que salió su número.</p>
  <h2 class="sect"><span class="bar"></span> Los números de hoy en la charada</h2>
  <ul class="resumen-txt">{''.join(hoy)}</ul>
  <h2 class="sect"><span class="bar"></span> Tabla de sueños del 00 al 99</h2>
  <label for="busca" class="nota" style="display:block;margin-bottom:6px">Escribe lo que soñaste o un número</label>
  <input id="busca" class="busca" type="search" placeholder="Ej.: muerto, dinero, 38" autocomplete="off">
  <div class="tabla-wrap"><table class="charada" id="tablaCharada"><thead><tr><th>Número</th><th>Sueño</th><th>Otros significados</th></tr></thead><tbody>{filas}</tbody></table></div>
  <p class="nota">{esc(AVISO)} Fuentes de la tabla: periodicocubano.com y directoriocubano.info.</p>
  <h2 class="sect"><span class="bar"></span> Preguntas frecuentes</h2>
  <div class="faq">
    {faq_html(faqs)}
  </div>
  <script>
  (function(){{
    var i=document.getElementById('busca'), rows=document.querySelectorAll('#tablaCharada tbody tr');
    function norm(s){{return s.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g,'');}}
    i.addEventListener('input',function(){{var q=norm(i.value.trim());
      rows.forEach(function(r){{r.style.display=!q||norm(r.textContent).indexOf(q)>-1?'':'none';}});}});
  }})();
  </script>"""
    title = "Tabla de Sueños y Charada Dominicana: Números del 00 al 99"
    desc = "Tabla de sueños (charada) con el número de cada sueño para la quiniela: muerto 08, dinero 38, caballo 01 y más. Busca tu sueño y mira cuándo salió su número."
    migas = [("Portal Dominicano", "/"), ("Tabla de sueños", ruta)]
    ld = jsonld(BASE + ruta, "Tabla de sueños y charada", desc, migas, extra=[faq_ld(BASE + ruta, faqs)],
                fecha_mod=upd.isoformat(timespec="seconds"))
    escribir(ruta, pagina(ruta=ruta, title=title, desc=desc, h1="Tabla de sueños: la charada del 00 al 99",
                          sub="Qué número jugar según lo que soñaste", migas=migas, cuerpo=cuerpo, ld=ld))


def main():
    res = cargar_json("resultados.json", {}) or {}
    archivo = cargar_json("archivo.json", {}) or {}
    upd = actualizado_rd(res) if res else datetime.datetime.now(TZ_RD)
    ap = apariciones(archivo)
    n_dias, desde = dias_guardados(archivo)
    con_pagina = set(fechas_con_pagina(archivo))
    for n in CHARADA:
        pagina_sueno(n, ap, n_dias, desde, con_pagina, upd)
    pagina_indice(res, n_dias, upd)
    print(f"OK: tabla de sueños + {len(CHARADA)} páginas de sueños")


if __name__ == "__main__":
    main()
