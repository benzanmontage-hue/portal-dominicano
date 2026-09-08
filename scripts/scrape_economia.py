#!/usr/bin/env python3
"""Descargar indicadores económicos de República Dominicana (Banco Mundial) a JSON.

Fuente: https://api.worldbank.org/v2/country/DO/indicator/... (gratis, sin clave)

Produce data/economia.json con desempleo, deuda externa, PIB per cápita e inflación.
"""
import json
import urllib.request
import datetime
from datetime import timezone, timedelta

UA = {"User-Agent": "Mozilla/5.0"}

INDICADORES = [
    {"id": "SL.UEM.TOTL.ZS", "clave": "desempleo", "nombre": "Desempleo", "unidad": "%", "deci": 1},
    {"id": "DT.DOD.DECT.GN.ZS", "clave": "deuda_ext", "nombre": "Deuda externa (% del ING)", "unidad": "%", "deci": 1},
    {"id": "NY.GDP.PCAP.CD", "clave": "pib_pc", "nombre": "PIB per cápita", "unidad": "USD", "deci": 0},
    {"id": "FP.CPI.TOTL.ZG", "clave": "inflacion", "nombre": "Inflación anual", "unidad": "%", "deci": 1},
]


def fetch_indicator(ind_id):
    url = f"https://api.worldbank.org/v2/country/DO/indicator/{ind_id}?format=json&per_page=6"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        d = json.loads(r.read().decode("utf-8"))
    rows = d[1] if len(d) > 1 else []
    return rows


def main():
    out = {
        "updated": datetime.datetime.now(timezone(timedelta(hours=-4))).isoformat(),
        "fecha": datetime.datetime.now(timezone(timedelta(hours=-4))).strftime("%d/%m/%Y"),
        "indicadores": [],
    }
    for ind in INDICADORES:
        try:
            rows = fetch_indicator(ind["id"])
            # tomar el último valor no nulo
            serie = []
            for r in rows:
                if r.get("value") is not None:
                    serie.append({"año": r["date"], "valor": round(float(r["value"]), ind["deci"])})
            ultimo = serie[0] if serie else None
            out["indicadores"].append({
                "clave": ind["clave"],
                "nombre": ind["nombre"],
                "unidad": ind["unidad"],
                "ultimo": ultimo,
                "historial": serie[:6],
            })
            if ultimo:
                print(f"  {ind['nombre']}: {ultimo['valor']} {ind['unidad']} ({ultimo['año']})")
        except Exception as e:
            print(f"  ERROR {ind['clave']}: {e}")
            out["indicadores"].append({
                "clave": ind["clave"], "nombre": ind["nombre"], "unidad": ind["unidad"],
                "ultimo": None, "historial": [],
            })

    path = "/opt/data/home/portal-dominicano/data/economia.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"OK -> {path}")


if __name__ == "__main__":
    main()
