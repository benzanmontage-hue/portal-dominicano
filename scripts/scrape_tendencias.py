#!/usr/bin/env python3
"""Descargar tendencias de búsqueda de Google (República Dominicana) a JSON.

Fuente: https://trends.google.com/trending/rss?geo=DO  (gratis, sin clave)

Produce data/tendencias.json con:
  {
    "updated": "ISO",
    "hora": "HH:MM",
    "pais": "República Dominicana",
    "tendencias": [ { "termino": "...", "trafico": "20000+", "noticia": "...", "enlace": "...", "imagen": "..." } ]
  }
"""
import json
import re
import urllib.request
import datetime
from datetime import timezone, timedelta

RSS_URL = "https://trends.google.com/trending/rss?geo=DO"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def fetch_rss():
    req = urllib.request.Request(RSS_URL, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8")


def strip_tags(s):
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"&[a-zA-Z]+;|&#\d+;", " ", s).strip()


def parse(xml):
    items = re.findall(r"<item>(.*?)</item>", xml, re.DOTALL)
    out = []
    for it in items:
        def grab(pat, dotall=False):
            flags = re.DOTALL if dotall else 0
            m = re.search(pat, it, flags)
            return m.group(1) if m else ""

        termino = strip_tags(grab(r"<title>([^<]+)</title>"))
        trafico = strip_tags(grab(r"<ht:approx_traffic>([^<]+)</ht:approx_traffic>"))
        noticia = strip_tags(grab(r"<ht:news_item_title>([^<]+)</ht:news_item_title>"))
        enlace = strip_tags(grab(r"<ht:news_item_url>([^<]+)</ht:news_item_url>"))
        imagen = strip_tags(grab(r"<ht:picture>([^<]+)</ht:picture>"))
        # enlace también puede venir como <link> después del news_item
        if not enlace:
            enlace = strip_tags(grab(r"<ht:news_item_url>([^<]+)</ht:news_item_url>"))
        out.append({
            "termino": termino,
            "trafico": trafico,
            "noticia": noticia,
            "enlace": enlace,
            "imagen": imagen,
        })
    return out


def main():
    xml = fetch_rss()
    tendencias = parse(xml)

    now = datetime.datetime.now(timezone(timedelta(hours=-4)))
    out = {
        "updated": now.isoformat(),
        "hora": now.strftime("%H:%M"),
        "fecha": now.strftime("%d/%m/%Y"),
        "pais": "República Dominicana",
        "total": len(tendencias),
        "tendencias": tendencias,
    }

    path = "/opt/data/home/portal-dominicano/data/tendencias.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"OK: {len(tendencias)} tendencias -> {path}")
    for t in tendencias:
        print(f"  [{t['trafico']:>8}] {t['termino']}")


if __name__ == "__main__":
    main()
