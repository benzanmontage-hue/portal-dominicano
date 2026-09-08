#!/usr/bin/env python3
"""Descargar eventos próximos en República Dominicana a JSON.

Fuente: Google News RSS con búsquedas temáticas (conciertos, eventos, festival,
deporte, teatro). Gratis, sin clave.

Produce data/eventos.json.
"""
import json
import re
import urllib.request
import urllib.parse
import datetime
from datetime import timezone, timedelta

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

QUERIES = [
    "conciertos República Dominicana",
    "eventos Santo Domingo",
    "festival República Dominicana",
    "concierto Santo Domingo",
]

# palabras clave para detectar que es un evento (no una noticia genérica)
KEYWORDS = re.compile(
    r"concierto|conciertos|festival|evento|eventos|show|gira|tour|presentaci[oó]n|carnaval|"
    r"feria|espect[aá]culo|artista|en vivo|en directo|ticket|boletas|entradas", re.IGNORECASE)


def fetch_rss(query):
    q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl=es-419&gl=DO&ceid=DO:es-419"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8")


def strip_tags(s):
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"&[a-zA-Z]+;|&#\d+;", " ", s).strip()


def clean_google_link(link):
    m = re.search(r"url=([^&]+)", link)
    return m.group(1) if m else link


def main():
    seen = set()
    eventos = []
    for q in QUERIES:
        try:
            xml = fetch_rss(q)
        except Exception:
            continue
        for it in re.findall(r"<item>(.*?)</item>", xml, re.DOTALL):
            try:
                title = strip_tags(re.search(r"<title>([^<]+)</title>", it).group(1))
                link = re.search(r"<link>([^<]+)</link>", it).group(1)
                src = re.search(r'<source[^>]*>([^<]+)</source>', it)
                fuente = src.group(1) if src else ""
                pub = re.search(r"<pubDate>([^<]+)</pubDate>", it)
                fecha = pub.group(1) if pub else ""
            except Exception:
                continue
            # solo si el título parece un evento
            if not KEYWORDS.search(title):
                continue
            key = title[:70].lower()
            if key in seen:
                continue
            seen.add(key)
            eventos.append({
                "titulo": title,
                "fuente": fuente,
                "enlace": clean_google_link(link),
                "fecha": fecha,
            })

    # ordenar por fecha (más reciente primero) y limitar
    eventos = eventos[:12]

    now = datetime.datetime.now(timezone(timedelta(hours=-4)))
    out = {
        "updated": now.isoformat(),
        "hora": now.strftime("%H:%M"),
        "fecha": now.strftime("%d/%m/%Y"),
        "total": len(eventos),
        "eventos": eventos,
    }

    path = "/opt/data/home/portal-dominicano/data/eventos.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"OK: {len(eventos)} eventos -> {path}")
    for e in eventos[:8]:
        print(f"  [{e['fuente'][:15]}] {e['titulo'][:60]}")


if __name__ == "__main__":
    main()
