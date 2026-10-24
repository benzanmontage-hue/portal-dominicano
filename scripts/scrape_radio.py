#!/usr/bin/env python3
"""Emisoras de radio dominicanas para el reproductor (data/radio.json).

Fuente: Radio Browser (radio-browser.info, gratis). En cada actualización:
  - toma las emisoras de RD ordenadas por popularidad (clics);
  - usa solo enlaces https (el navegador bloquea audio http en una página https);
  - evita enlaces con permiso temporal (?zt=…), que caducan en segundos: usa el enlace base;
  - quita repetidas (mismo nombre o mismo enlace) y emisoras que no son de RD;
  - prueba que cada emisora responda con audio antes de incluirla.
Si las pruebas fallan casi todas (problema de red), conserva la lista anterior.
"""
import datetime
import json
import os
import re
import sys
import unicodedata
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVIDORES = ["de1.api.radio-browser.info", "de2.api.radio-browser.info", "fi1.api.radio-browser.info"]
RUTA = "/json/stations/bycountrycodeexact/DO?hidebroken=true&order=clickcount&reverse=true&limit=400"
UA = {"User-Agent": "portaldominicana.net/1.0 (+https://portaldominicana.net)"}
MAXIMO = 40

# Emisoras muy conocidas: van primero si están y funcionan (orden de esta lista).
PREFERIDAS = ["zol 106", "la bakana", "kq 94", "disco 106", "dominicana fm", "amor fm", "la rocka", "la nueva 106",
              "escandalo 102", "be 99", "canal 105", "comando 88", "super q", "la 91", "la mega", "rumba 98",
              "z 101", "cdn radio", "bachata", "criolla 106", "estelar 106"]
EXCLUIR = re.compile(r"islam|quran|cor[aá]n|abdul|mp3islam", re.I)


def norm(t):
    t = unicodedata.normalize("NFKD", t.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def clave_nombre(nombre):
    """'Disco 89 88.9 FM' y 'Disco 88.9' -> misma clave aproximada (sin 'fm', puntos ni espacios dobles)."""
    t = norm(nombre)
    t = re.sub(r"\b(fm|am|radio|en vivo|online|rd|santo domingo)\b", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def enlace(s):
    """Enlace https estable, o '' si no hay."""
    resuelto = s.get("url_resolved") or ""
    base = s.get("url") or ""
    for u in ([base, resuelto] if "zt=" in resuelto else [resuelto, base]):
        if u.startswith("https://") and "zt=" not in u:
            return u
    return ""


def suena(url):
    """True si el enlace responde con audio en pocos segundos."""
    try:
        req = urllib.request.Request(url, headers={**UA, "Icy-MetaData": "0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            tipo = (r.headers.get("Content-Type") or "").lower()
            datos = r.read(2048)
            if not datos:
                return False
            return any(x in tipo for x in ("audio", "mpeg", "aac", "ogg", "octet-stream")) or tipo == ""
    except Exception:
        return False


def main():
    previo = {}
    try:
        previo = json.load(open(os.path.join(ROOT, "data", "radio.json"), encoding="utf-8"))
    except Exception:
        pass
    ahora = datetime.datetime.now(datetime.timezone.utc)
    try:
        hace = ahora - datetime.datetime.fromisoformat(previo.get("actualizado", ""))
        if hace < datetime.timedelta(hours=6) and "--forzar" not in sys.argv:
            print(f"radio: lista renovada hace {int(hace.total_seconds() // 60)} min; no hace falta")
            return 0
    except ValueError:
        pass
    estaciones = None
    for srv in SERVIDORES:
        try:
            req = urllib.request.Request("https://" + srv + RUTA, headers=UA)
            with urllib.request.urlopen(req, timeout=25) as r:
                estaciones = json.loads(r.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"radio: {srv} no respondió ({e})")
    if not estaciones:
        print("radio: sin respuesta de Radio Browser; se conserva la lista anterior")
        return 1

    candidatas, vistos_n, vistos_u = [], set(), set()
    for s in estaciones:
        nombre = re.sub(r"\s+", " ", (s.get("name") or "")).strip()
        url = enlace(s)
        if not nombre or not url or EXCLUIR.search(nombre + " " + (s.get("tags") or "")):
            continue
        kn = clave_nombre(nombre)
        if kn in vistos_n or url in vistos_u:
            continue
        vistos_n.add(kn)
        vistos_u.add(url)
        tags = [t.strip() for t in (s.get("tags") or "").split(",") if t.strip()][:3]
        candidatas.append({"nombre": nombre, "url": url, "codec": (s.get("codec") or "").upper(),
                           "bitrate": s.get("bitrate") or 0, "favicon": s.get("favicon") or "",
                           "tags": tags, "clics": s.get("clickcount") or 0})

    def prioridad(e):
        n = norm(e["nombre"])
        for i, p in enumerate(PREFERIDAS):
            if p in n:
                return (0, i, -e["clics"])
        return (1, 0, -e["clics"])

    candidatas.sort(key=prioridad)
    candidatas = candidatas[:90]  # probar las mejores; sobra margen para las que fallen

    with ThreadPoolExecutor(max_workers=16) as ex:
        ok = list(ex.map(lambda e: suena(e["url"]), candidatas))
    buenas = [e for e, b in zip(candidatas, ok) if b][:MAXIMO]
    print(f"radio: {len(candidatas)} candidatas, {sum(ok)} responden, se guardan {len(buenas)}")
    if len(buenas) < 10:
        print("radio: muy pocas emisoras responden; se conserva la lista anterior")
        return 1

    with open(os.path.join(ROOT, "data", "radio.json"), "w", encoding="utf-8") as f:
        json.dump({"actualizado": ahora.isoformat(timespec="seconds"), "total": len(buenas), "emisoras": buenas},
                  f, ensure_ascii=False, indent=1)
    for e in buenas[:15]:
        print(f"  {e['nombre'][:40]:42s} {e['codec']} {e['bitrate']} clics={e['clics']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
