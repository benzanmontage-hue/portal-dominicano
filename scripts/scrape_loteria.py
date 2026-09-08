#!/usr/bin/env python3
"""Scrape Dominican lottery results from loteriasdominicanas.com API and write JSON.

Produces data/resultados.json with:
  {
    "updated": "ISO timestamp",
    "fecha": "DD/MM/YYYY",
    "juegos": [ { "compania": "...", "juego": "...", "numeros": ["97","50","37"] } ]
  }

Only keeps the popular games Dominicans actually search for (per search data):
Lotería Nacional, Lotería Real, Anguila, Loteka, La Primera, La Suerte, Leidsa.
"""
import json
import sys
import urllib.request
import datetime
from datetime import timezone, timedelta

API_BASE = "https://api.loteriasdominicanas.com/dominicana"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# The lotteries that matter (from Google search data for DR)
KEEP_COMPANIES = {
    "Nacional", "Loteria Real", "Anguila", "Loteka",
    "La Primera", "La Suerte", "Leidsa",
}

# game_id -> {company, game} (populated from sites/env)
GAME_MAP = {}


def fetch_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def build_game_map():
    env = fetch_json(f"{API_BASE}/sites/env")
    for c in env.get("siteCompanies", []):
        company = c.get("title", "")
        for g in c.get("siteGames", []):
            # the game_id that sessions reference lives at g["game_id"] (not g["_id"])
            gid = g.get("game_id") or g.get("_id")
            GAME_MAP[gid] = {"company": company, "game": g.get("title", "")}


def dr_now():
    """Dominican time (UTC-4, no DST)."""
    return datetime.datetime.now(timezone(timedelta(hours=-4)))


def main():
    build_game_map()

    now = dr_now()
    # sessions endpoint needs DR-midnight as UTC (04:00Z), format "YYYY-MM-DDT04:00:00.000Z"
    dr_date = now.strftime("%Y-%m-%d") + "T04:00:00.000Z"
    sessions = fetch_json(f"{API_BASE}/sessions?date={dr_date}")

    juegos = []
    for g in sessions:
        gid = g.get("game_id")
        info = GAME_MAP.get(gid)
        if not info:
            continue
        if info["company"] not in KEEP_COMPANIES:
            continue
        ls = g.get("lastSession") or {}
        score = ls.get("score")
        if not score:
            continue
        # score is list of lists; flatten
        flat = []
        for row in score:
            if isinstance(row, list):
                flat.extend(row)
            else:
                flat.append(row)
        # filter out non-numeric junk (e.g. session tokens leaking into scores)
        flat = [n for n in flat if str(n).strip().isdigit()]
        if not flat:
            continue
        date = ls.get("date", "")
        juegos.append({
            "compania": info["company"],
            "juego": info["game"],
            "numeros": flat,
            "fecha": date,
        })

    # Sort: Nacional first, then alphabetical
    order = {"Nacional": 0, "Loteria Real": 1, "Anguila": 2, "Loteka": 3,
             "La Primera": 4, "La Suerte": 5, "Leidsa": 6}
    juegos.sort(key=lambda j: (order.get(j["compania"], 99), j["juego"]))

    out = {
        "updated": now.isoformat(),
        "fecha": now.strftime("%d/%m/%Y"),
        "hora": now.strftime("%H:%M"),
        "total_juegos": len(juegos),
        "juegos": juegos,
    }

    path = "/opt/data/home/portal-dominicano/data/resultados.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"OK: {len(juegos)} juegos -> {path}")
    for j in juegos:
        print(f"  {j['compania']:15s} | {j['juego']:22s} | {'-'.join(j['numeros'])}")


if __name__ == "__main__":
    main()
