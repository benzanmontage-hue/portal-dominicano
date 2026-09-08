#!/usr/bin/env python3
"""Descargar tipos de cambio (USD, EUR -> DOP y más) a JSON.

Fuente: https://open.er-api.com/v6/latest/USD (gratis, sin clave, actualiza cada 24h).

Produce data/divisas.json con las conversiones más relevantes para RD.
"""
import json
import urllib.request
import datetime
from datetime import timezone, timedelta

API = "https://open.er-api.com/v6/latest/USD"
UA = {"User-Agent": "Mozilla/5.0"}


def main():
    req = urllib.request.Request(API, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        d = json.loads(r.read().decode("utf-8"))

    rates = d.get("rates", {})
    dop = rates.get("DOP", 0)
    eur = rates.get("EUR", 0)  # 1 USD en EUR

    # conversiones relevantes para RD
    conversiones = [
        {"moneda": "Dólar (USD)", "codigo": "USD", "bandera": "🇺🇸",
         "a": "DOP", "valor": round(dop, 2), "texto": "1 USD = {:.2f} DOP".format(dop)},
        {"moneda": "Euro (EUR)", "codigo": "EUR", "bandera": "🇪🇺",
         "a": "DOP", "valor": round(dop / eur, 2), "texto": "1 EUR = {:.2f} DOP".format(dop / eur)},
        {"moneda": "Dólar (USD)", "codigo": "USD", "bandera": "🇺🇸",
         "a": "EUR", "valor": round(eur, 3), "texto": "1 USD = {:.3f} EUR".format(eur)},
        {"moneda": "Peso mexicano (MXN)", "codigo": "MXN", "bandera": "🇲🇽",
         "a": "DOP", "valor": round(dop / rates.get("MXN", 1), 2), "texto": "1 MXN = {:.2f} DOP".format(dop / rates.get("MXN", 1))},
        {"moneda": "Dólar canadiense (CAD)", "codigo": "CAD", "bandera": "🇨🇦",
         "a": "DOP", "valor": round(dop / rates.get("CAD", 1), 2), "texto": "1 CAD = {:.2f} DOP".format(dop / rates.get("CAD", 1))},
        {"moneda": "Libra (GBP)", "codigo": "GBP", "bandera": "🇬🇧",
         "a": "DOP", "valor": round(dop / rates.get("GBP", 1), 2), "texto": "1 GBP = {:.2f} DOP".format(dop / rates.get("GBP", 1))},
        {"moneda": "Peso colombiano (COP)", "codigo": "COP", "bandera": "🇨🇴",
         "a": "DOP", "valor": round(dop / rates.get("COP", 1), 3), "texto": "1 COP = {:.3f} DOP".format(dop / rates.get("COP", 1))},
    ]

    now = datetime.datetime.now(timezone(timedelta(hours=-4)))
    out = {
        "updated": now.isoformat(),
        "hora": now.strftime("%H:%M"),
        "fecha": now.strftime("%d/%m/%Y"),
        "fuente_updated": d.get("time_last_update_utc"),
        "dop_por_usd": round(dop, 2),
        "conversiones": conversiones,
    }

    path = "/opt/data/home/portal-dominicano/data/divisas.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"OK: USD = {dop} DOP -> {path}")


if __name__ == "__main__":
    main()
