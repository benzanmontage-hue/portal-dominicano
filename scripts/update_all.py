#!/usr/bin/env python3
"""Actualizar todos los datos del portal y regenerar las páginas.

Lo ejecuta GitHub Actions (.github/workflows/actualizar.yml) varias veces al día.
1. Descarga los datos (lotería, noticias, divisas...). Si una fuente falla, las demás siguen.
2. Guarda el historial de lotería, regenera las páginas SEO, la portada y el sitemap.

Uso local:  python3 scripts/update_all.py          (solo actualiza archivos)
            python3 scripts/update_all.py --push   (además hace commit y push, modo servidor antiguo)
Sale con código 1 si falló la lotería (la fuente principal) o la generación de páginas.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SCRAPERS = [
    "scripts/scrape_loteria.py",
    "scripts/scrape_tendencias.py",
    "scripts/scrape_radio.py",
    "scripts/scrape_noticias.py",
    "scripts/scrape_divisas.py",
    "scripts/scrape_economia.py",
    "scripts/scrape_eventos.py",
    "scripts/scrape_lidom.py",
    "scripts/scrape_combustibles.py",
]
GENERADORES = [
    "scripts/archivar_loteria.py",
    "scripts/generate_archivo.py",
    "scripts/generate_landing.py",
    "scripts/generate_juegos.py",
    "scripts/generate_sections.py",
    "scripts/generate_info.py",
    "scripts/generate_lidom.py",
    "scripts/generate_combustibles.py",
    "scripts/generate_anguila.py",
    "scripts/generate_suenos.py",
    "scripts/tarjeta.py",
    "scripts/prerender_home.py",
    "scripts/build_sitemap.py",
]
CRITICOS = {"scripts/scrape_loteria.py", *GENERADORES}


def run(cmd):
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=300)


def main():
    errores = []
    for s in SCRAPERS + GENERADORES:
        try:
            r = run([sys.executable, s])
            ok, err = r.returncode == 0, r.stderr.strip()[-300:]
        except subprocess.TimeoutExpired:
            ok, err = False, "timeout"
        print(("OK   " if ok else "FALLO") + " " + s)
        if not ok:
            print("      " + err.replace("\n", "\n      "))
            errores.append(s)

    if "--push" in sys.argv:
        run(["git", "add", "-A"])
        run(["git", "commit", "-q", "-m", "auto-update datos (cron)"])
        r = run(["git", "push", "-q", "origin", "main"])
        if r.returncode != 0:
            print("ERROR push:", r.stderr.strip()[-200:])
            return 1

    return 1 if any(e in CRITICOS for e in errores) else 0


if __name__ == "__main__":
    sys.exit(main())
