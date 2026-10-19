#!/usr/bin/env python3
"""Utilidades compartidas por los generadores del Portal Dominicano."""
import datetime
import html
import json
import os
import re
from datetime import timezone, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://portaldominicana.net"
TZ_RD = timezone(timedelta(hours=-4))  # República Dominicana: UTC-4, sin horario de verano

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

# slug de cada compañía (tal como viene en data/resultados.json)
SLUG_COMPANIA = {
    "Nacional": "loteria-nacional",
    "Loteria Real": "loteria-real",
    "Anguila": "anguila",
    "Loteka": "loteka",
    "La Primera": "la-primera",
    "La Suerte": "la-suerte",
    "Leidsa": "leidsa",
}
NOMBRE_COMPANIA = {
    "Nacional": "Lotería Nacional",
    "Loteria Real": "Lotería Real",
    "Anguila": "Anguila",
    "Loteka": "Loteka",
    "La Primera": "La Primera",
    "La Suerte": "La Suerte",
    "Leidsa": "Leidsa",
}
ORDEN_COMPANIAS = ["Nacional", "Anguila", "Loteria Real", "Loteka", "La Primera", "La Suerte", "Leidsa"]

# juego estrella de cada compañía (va primero)
JUEGO_PRINCIPAL = {
    "Nacional": ["Lotería Nacional", "Gana Más"],
    "Loteria Real": ["Lotería Real Noche", "Quiniela Real"],
    "Loteka": ["Quiniela Loteka Noche", "Quiniela Loteka Día", "Quiniela Loteka"],
    "La Primera": ["Primera Noche", "La Primera Día"],
    "La Suerte": ["La Suerte 12:30", "La Suerte 18:00"],
    "Leidsa": ["Quiniela Leidsa"],
}

SECCIONES = [
    ("lidom", "Lidom"), ("combustibles", "Combustibles"), ("mlb", "MLB"), ("traductor", "Traductor"), ("tiempo-santo-domingo", "Clima"),
    ("dolar-hoy", "Dólar hoy"), ("economia-rd", "Economía"), ("noticias-rd", "Noticias"),
    ("eventos-rd", "Eventos"),
]


def esc(s):
    return html.escape(str(s), quote=True)


def limpiar(s):
    """Quita espacios dobles de los nombres que vienen de la API ("Anguila 8:00  AM")."""
    return re.sub(r"\s+", " ", str(s)).strip()


def cargar_json(nombre, defecto=None):
    try:
        with open(os.path.join(ROOT, "data", nombre), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return defecto


def parse_fecha(s):
    """Devuelve date (fecha del sorteo) a partir de '2026-10-07T04:00:00.000Z' o '2026-10-07'.

    La API usa la medianoche de RD expresada en UTC (04:00Z), así que basta con la parte de fecha.
    """
    if not s:
        return None
    try:
        return datetime.date.fromisoformat(str(s)[:10])
    except ValueError:
        return None


def fecha_larga(d, con_dia=True, con_anio=True):
    """date -> 'martes 7 de octubre de 2026'."""
    if not d:
        return ""
    txt = f"{d.day} de {MESES[d.month - 1]}"
    if con_anio:
        txt += f" de {d.year}"
    if con_dia:
        txt = f"{DIAS[d.weekday()]} {txt}"
    return txt


def actualizado_rd(resultados):
    """datetime de la última actualización en hora RD."""
    try:
        return datetime.datetime.fromisoformat(resultados["updated"]).astimezone(TZ_RD)
    except Exception:
        return datetime.datetime.now(TZ_RD)


def hora_12(dt):
    h = dt.hour % 12 or 12
    return f"{h}:{dt.minute:02d} {'AM' if dt.hour < 12 else 'PM'}"


def minutos_juego(nombre):
    """Minutos desde medianoche si el nombre trae hora ("Anguila 1:00 PM", "La Suerte 18:00")."""
    m = re.search(r"(\d{1,2}):(\d{2})\s*(AM|PM)?", nombre, re.I)
    if not m:
        return None
    h, mi, ap = int(m.group(1)), int(m.group(2)), (m.group(3) or "").upper()
    if ap == "PM" and h != 12:
        h += 12
    if ap == "AM" and h == 12:
        h = 0
    return h * 60 + mi


def ordenar_juegos(compania, juegos):
    principal = JUEGO_PRINCIPAL.get(compania, [])

    def clave(j):
        nombre = limpiar(j["juego"])
        rank = principal.index(nombre) if nombre in principal else 99
        mins = minutos_juego(nombre)
        return (rank, mins if mins is not None else 9999, nombre)

    return sorted(juegos, key=clave)


def balls_html(numeros):
    gold = " gold" if len(numeros) <= 4 else ""
    return "".join(f'<span class="ball{gold}">{esc(n)}</span>' for n in numeros)


MIN_SORTEOS_FECHA = 12  # días con menos sorteos guardados no tienen página propia (evita páginas pobres)


def sorteos_por_fecha(archivo):
    """{'2026-10-17': [(compania, juego, [numeros]), ...]} a partir de data/archivo.json."""
    por_fecha = {}
    for clave, lista in (archivo.get("sorteos") or {}).items():
        comp, juego = clave.split("|", 1)
        for s in lista:
            por_fecha.setdefault(s["fecha"], []).append((comp, juego, s["numeros"]))
    return por_fecha


def fechas_con_pagina(archivo):
    """Fechas (ISO, ascendente) que tienen página /resultados/AAAA-MM-DD/."""
    return sorted(f for f, l in sorteos_por_fecha(archivo).items() if len(l) >= MIN_SORTEOS_FECHA)


def titulo(*partes, maximo=65):
    """Une partes con ' — ' y descarta las finales mientras el título pase de `maximo` caracteres."""
    partes = [x for x in partes if x]
    while len(partes) > 1 and len(" — ".join(partes)) > maximo:
        partes.pop()
    return " — ".join(partes)
