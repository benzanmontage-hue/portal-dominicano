#!/usr/bin/env python3
"""Precios semanales de combustibles en RD (fijados por el MICM cada viernes, vigentes sábado a viernes).

Fuente: https://www.prestocombustibles.com/precios-combustibles/ (publica la tabla del MICM).
Escribe data/combustibles.json y acumula data/combustibles_historial.json (una entrada por semana).

Solo se toman los productos de la lista PRODUCTOS. El kerosene se excluye a propósito: el
18-oct-2026 la fuente mostraba el precio de la semana anterior (387.20 en vez de 395.80).
Si la tabla no se puede leer o los precios no son razonables, no se cambia nada.
"""
import datetime
import html
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "https://www.prestocombustibles.com/precios-combustibles/"
UA = {"User-Agent": "Mozilla/5.0 (portaldominicana.net)"}
TZ_RD = datetime.timezone(datetime.timedelta(hours=-4))

# clave, nombre a mostrar, patrón en la fuente, unidad, rango razonable (RD$)
PRODUCTOS = [
    ("premium", "Gasolina Premium", r"Gasolina\s+Pr[eé]mium", "galón", (150, 700)),
    ("regular", "Gasolina Regular", r"Gasolina\s+Regular", "galón", (150, 700)),
    ("gasoil_optimo", "Gasoil Óptimo", r"Gasoil\s+[ÓO]ptimo", "galón", (120, 700)),
    ("gasoil_regular", "Gasoil Regular", r"Gasoil\s+Regular", "galón", (120, 700)),
    ("glp", "Gas Licuado (GLP)", r"Gas\s+Licuado\s+de\s+Petr[óo]leo(?:\s*\(GLP\))?", "galón", (50, 400)),
    ("gnv", "Gas Natural Vehicular (GNV)", r"Gas\s+Natural\s+Vehicular(?:\s*\(GNV\))?", "m³", (10, 150)),
]
MESES = {m: i + 1 for i, m in enumerate(["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
                                          "septiembre", "octubre", "noviembre", "diciembre"])}
MESES["setiembre"] = 9


def texto_pagina():
    req = urllib.request.Request(URL, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        crudo = r.read().decode("utf-8", errors="replace")
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", crudo, flags=re.S | re.I)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    return re.sub(r"\s+", " ", t)


def semana(t):
    m = re.search(r"Semana del\s+(\d{1,2})(?:\s+de)?(?:\s+([a-záéíóú]+))?\s+al\s+(\d{1,2})(?:\s+de)?\s+([a-záéíóú]+)\s+del?\s+(\d{4})",
                  t, re.I)
    if not m:
        return None
    d1, m1, d2, m2, y = m.groups()
    mes2 = MESES.get(m2.lower())
    mes1 = MESES.get((m1 or m2).lower())
    if not (mes1 and mes2):
        return None
    y2 = int(y)
    y1 = y2 - 1 if mes1 > mes2 else y2
    return datetime.date(y1, mes1, int(d1)), datetime.date(y2, mes2, int(d2))


def main():
    t = texto_pagina()
    sem = semana(t)
    if not sem:
        print("combustibles: no se encontró la semana en la página")
        return 1
    inicio, fin = sem
    precios = {}
    for clave, _n, patron, _u, (lo, hi) in PRODUCTOS:
        m = re.search(patron + r"\s*RD\$?\s*([\d,]+\.\d{1,2})", t, re.I)
        if not m:
            continue
        v = float(m.group(1).replace(",", ""))
        if lo <= v <= hi:
            precios[clave] = v
    if len(precios) < 4:
        print(f"combustibles: solo se leyeron {len(precios)} precios; no se actualiza")
        return 1
    hoy = datetime.datetime.now(TZ_RD).date()
    if (hoy - fin).days > 7:
        print(f"combustibles: la fuente muestra una semana vieja ({inicio}–{fin}); no se actualiza")
        return 1

    hist_path = os.path.join(ROOT, "data", "combustibles_historial.json")
    try:
        hist = json.load(open(hist_path, encoding="utf-8"))
    except Exception:
        hist = {}
    hist[inicio.isoformat()] = {"fin": fin.isoformat(), "precios": precios}
    hist = dict(sorted(hist.items())[-104:])
    with open(hist_path, "w", encoding="utf-8") as f:
        json.dump(hist, f, ensure_ascii=False, indent=1)

    out = {"updated": datetime.datetime.now(TZ_RD).isoformat(timespec="seconds"),
           "inicio": inicio.isoformat(), "fin": fin.isoformat(), "precios": precios,
           "fuente": "MICM, vía prestocombustibles.com"}
    with open(os.path.join(ROOT, "data", "combustibles.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"OK combustibles: semana {inicio}–{fin}, {len(precios)} precios")
    return 0


if __name__ == "__main__":
    sys.exit(main())
