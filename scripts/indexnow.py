#!/usr/bin/env python3
"""Avisar a Bing (y otros buscadores con IndexNow) de las páginas que cambiaron en el último commit.

Uso en GitHub Actions, después del push:  python3 scripts/indexnow.py
La clave está publicada en /083a3d8379dfc13565f3534796fb7b10.txt (requisito de IndexNow). No necesita cuenta.
"""
import json
import subprocess
import sys
import urllib.request

KEY = "083a3d8379dfc13565f3534796fb7b10"
HOST = "portaldominicana.net"


def main():
    r = subprocess.run(["git", "diff", "--name-only", "HEAD~1", "HEAD"], capture_output=True, text=True)
    urls = []
    for f in r.stdout.split():
        if f.endswith("index.html") and not f.startswith(("data/", "scripts/")):
            ruta = f[: -len("index.html")]
            urls.append(f"https://{HOST}/{ruta}")
    if not urls:
        print("IndexNow: sin páginas cambiadas")
        return 0
    cuerpo = json.dumps({"host": HOST, "key": KEY, "keyLocation": f"https://{HOST}/{KEY}.txt",
                         "urlList": urls[:1000]}).encode("utf-8")
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=cuerpo,
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            print(f"IndexNow: {len(urls)} URLs enviadas, respuesta {resp.status}")
    except Exception as e:  # no es crítico
        print(f"IndexNow: no se pudo enviar ({e})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
