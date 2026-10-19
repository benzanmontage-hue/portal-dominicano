#!/usr/bin/env python3
"""Descargar la tabla de posiciones y los juegos de Lidom (béisbol invernal dominicano).

Fuente: MLB Stats API (statsapi.mlb.com), liga 131 = LIDOM, sportId 17 = ligas invernales.
Escribe data/lidom.json. Si la temporada no está activa, guarda lo que haya.
"""
import datetime
import json
import os
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://statsapi.mlb.com/api/v1"
LIGA = 131
UA = {"User-Agent": "Mozilla/5.0 (portaldominicana.net)"}
TZ_RD = datetime.timezone(datetime.timedelta(hours=-4))


def get(path):
    req = urllib.request.Request(API + path, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    ahora = datetime.datetime.now(TZ_RD)
    hoy = ahora.date()
    liga = (get(f"/league/{LIGA}").get("leagues") or [{}])[0]
    temporada = liga.get("season") or str(hoy.year)
    fechas = liga.get("seasonDateInfo") or {}
    inicio = fechas.get("regularSeasonStartDate") or (hoy - datetime.timedelta(days=30)).isoformat()
    fin_regular = fechas.get("regularSeasonEndDate")
    fin_temporada = fechas.get("seasonEndDate") or fechas.get("postSeasonEndDate")

    st = get(f"/standings?leagueId={LIGA}&season={temporada}")
    tabla = []
    for rec in st.get("records", []):
        for t in rec.get("teamRecords", []):
            tabla.append({
                "id": t["team"]["id"], "equipo": t["team"]["name"],
                "g": t.get("wins", 0), "p": t.get("losses", 0),
                "pct": t.get("winningPercentage", ""), "dif": t.get("gamesBack", "-"),
                "racha": (t.get("streak") or {}).get("streakCode", ""),
                "pos": int(t.get("leagueRank") or t.get("sportRank") or 99),
            })
    tabla.sort(key=lambda x: x["pos"])

    desde = max(datetime.date.fromisoformat(inicio), hoy - datetime.timedelta(days=10))
    hasta = hoy + datetime.timedelta(days=4)
    sch = get(f"/schedule?sportId=17&leagueId={LIGA}&startDate={desde}&endDate={hasta}&hydrate=team")
    juegos, nombres = [], {}
    for d in sch.get("dates", []):
        for g in d.get("games", []):
            utc = datetime.datetime.fromisoformat(g["gameDate"].replace("Z", "+00:00"))
            rd = utc.astimezone(TZ_RD)
            a, h = g["teams"]["away"], g["teams"]["home"]
            for lado in (a, h):
                nombres[lado["team"]["id"]] = lado["team"]["name"]
            juegos.append({
                "id": g.get("gamePk"), "fecha": rd.date().isoformat(), "hora": rd.strftime("%H:%M"),
                "estado": g["status"].get("abstractGameState", ""), "detalle": g["status"].get("detailedState", ""),
                "visitante": a["team"]["name"], "visitante_id": a["team"]["id"], "carreras_v": a.get("score"),
                "local": h["team"]["name"], "local_id": h["team"]["id"], "carreras_l": h.get("score"),
                "estadio": (g.get("venue") or {}).get("name", ""),
                "serie": g.get("seriesDescription") or g.get("gameType", ""),
            })
    for t in tabla:  # nombre completo ("Tigres del Licey") cuando lo conocemos
        t["nombre"] = nombres.get(t["id"], t["equipo"])

    out = {"updated": ahora.isoformat(timespec="seconds"), "temporada": temporada,
           "inicio": inicio, "fin_regular": fin_regular, "fin_temporada": fin_temporada,
           "tabla": tabla, "juegos": juegos,
           "fuente": "MLB Stats API (statsapi.mlb.com)"}
    with open(os.path.join(ROOT, "data", "lidom.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"OK lidom: {len(tabla)} equipos, {len(juegos)} juegos")


if __name__ == "__main__":
    main()
