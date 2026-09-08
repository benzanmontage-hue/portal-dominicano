#!/usr/bin/env python3
"""Descargar emisoras de radio dominicanas a JSON (Radio Browser API, gratis).

Produce data/radio.json con una lista curada de emisoras FM con stream válido.
"""
import json
import urllib.request

API = "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/DO?hidebroken=true&limit=100"
UA = {"User-Agent": "portal-dominicano/1.0"}

# Emisoras más conocidas (prioridad alta si aparecen)
TOP = {
    "Zol 106.5": 0, "La Bakana": 1, "KQ 94.9": 2, "Disco 106.1": 3,
    "Dominicana FM 98.9 y 99.9 FM": 4, "Amor FM 91.9": 5, "La Rocka 91.7": 6,
    "La Nueva 106.9 FM": 7, "Escandalo 102.5": 8, "BE 99.7": 9,
    "Canal 105.1 FM": 10, "Comando 88 FM Santiago": 11, "Bendicion95.1 FM": 12,
    "Criolla 106.1 FM": 13, "Bachata Radio": 14,
}


def main():
    req = urllib.request.Request(API, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        stations = json.loads(r.read().decode("utf-8"))

    out = []
    for s in stations:
        name = (s.get("name") or "").strip()
        url = s.get("url_resolved") or s.get("url") or ""
        if not name or not url:
            continue
        # skip AM / religioso a largo plazo? keep but mark; keep all FM-ish
        if not name.lower().endswith("fm") and "fm" not in name.lower() and "radio" not in name.lower():
            pass
        out.append({
            "nombre": name,
            "url": url,
            "codec": (s.get("codec") or "").upper(),
            "bitrate": s.get("bitrate") or 0,
            "favicon": s.get("favicon") or "",
        })

    # orden: conocidas primero, luego por nombre
    def key(st):
        n = st["nombre"]
        for k, idx in TOP.items():
            if k.lower() in n.lower():
                return (0, idx, n)
        return (1, 0, n)

    out.sort(key=key)
    out = out[:40]

    path = "/opt/data/home/portal-dominicano/data/radio.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"total": len(out), "emisoras": out}, f, ensure_ascii=False, indent=2)
    print(f"OK: {len(out)} emisoras -> {path}")
    for s in out[:20]:
        print(f"  {s['nombre'][:40]:42s} | {s['codec']} {s['bitrate']}")


if __name__ == "__main__":
    main()
