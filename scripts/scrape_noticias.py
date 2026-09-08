#!/usr/bin/env python3
"""Descargar noticias de República Dominicana (Google News RSS) a JSON.

Fuente: https://news.google.com/rss/search?q=...&hl=es-419&gl=DO&ceid=DO:es-419
Produce data/noticias.json con una lista de noticias en español.
"""
import json
import re
import urllib.request
import urllib.parse
import datetime
from datetime import timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

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


def domain_of(url):
    m = re.search(r"https?://([^/]+)", url)
    return m.group(1) if m else ""


def fetch_image(link):
    """Obtener imagen del artículo vía Microlink (API de preview, sin key)."""
    try:
        url = "https://api.microlink.io/?url=" + urllib.parse.quote(link)
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=8) as r:
            d = json.loads(r.read().decode("utf-8", errors="ignore"))
        img = d.get("data", {}).get("image", {}).get("url")
        return img or ""
    except Exception:
        return ""


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
        "enlace": link,
        "dominio": domain_of(clean_google_link(link)),
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
    noticias = noticias[:15]

    # extraer imágenes en paralelo (solo las 15 primeras, con timeout)
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {ex.submit(fetch_image, n["enlace"]): n for n in noticias}
        for fut in as_completed(futures):
            n = futures[fut]
            n["imagen"] = fut.result()

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
    con_img = sum(1 for n in noticias if n.get("imagen"))
    print(f"OK: {len(noticias)} noticias ({con_img} con imagen) -> {path}")
    for n in noticias[:10]:
        print(f"  [{'✓' if n.get('imagen') else '✗'}] {n['titulo'][:55]}")


if __name__ == "__main__":
    main()
