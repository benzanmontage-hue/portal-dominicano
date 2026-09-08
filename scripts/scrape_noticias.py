#!/usr/bin/env python3
"""Descargar noticias de República Dominicana (Google News RSS) a JSON.

Fuente: https://news.google.com/rss/search?q=...&hl=es-419&gl=DO&ceid=DO:es-419
Produce data/noticias.json con una lista de noticias en español.
"""
import json
import re
import urllib.request
import datetime
from datetime import timezone, timedelta

QUERIES = [
    "República Dominicana",
    "Santo Domingo",
]
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def fetch_rss(query):
    import urllib.parse
    q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl=es-419&gl=DO&ceid=DO:es-419"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8")


def strip_tags(s):
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"&[a-zA-Z]+;|&#\d+;", " ", s).strip()


def clean_google_link(link):
    # google news links wrap the real url after "url="
    m = re.search(r"url=([^&]+)", link)
    return m.group(1) if m else link


def parse_item(it):
    title = strip_tags(re.search(r"<title>([^<]+)</title>", it).group(1))
    # title often ends with " - Source"; the source is in <source>
    link = re.search(r"<link>([^<]+)</link>", it).group(1)
    src = re.search(r'<source[^>]*url="([^"]+)"[^>]*>([^<]+)</source>', it)
    source = src.group(2) if src else ""
    pubdate = re.search(r"<pubDate>([^<]+)</pubDate>", it)
    date = pubdate.group(1) if pubdate else ""
    return {
        "titulo": title,
        "fuente": source,
        "enlace": clean_google_link(link),
        "fecha": date,
    }


def main():
    seen = set()
    noticias = []
    for q in QUERIES:
        try:
            xml = fetch_rss(q)
        except Exception:
            continue
        for it in re.findall(r"<item>(.*?)</item>", xml, re.DOTALL):
            try:
                n = parse_item(it)
            except Exception:
                continue
            key = n["titulo"][:80]
            if key in seen:
                continue
            seen.add(key)
            noticias.append(n)

    # quitar duplicados por fuente similar, limitar
    noticias = noticias[:30]

    now = datetime.datetime.now(timezone(timedelta(hours=-4)))
    out = {
        "updated": now.isoformat(),
        "hora": now.strftime("%H:%M"),
        "fecha": now.strftime("%d/%m/%Y"),
        "total": len(noticias),
        "noticias": noticias,
    }

    path = "/opt/data/home/portal-dominicano/data/noticias.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"OK: {len(noticias)} noticias -> {path}")
    for n in noticias[:10]:
        print(f"  [{n['fuente'][:20]}] {n['titulo'][:60]}")


if __name__ == "__main__":
    main()
