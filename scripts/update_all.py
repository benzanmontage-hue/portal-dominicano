#!/usr/bin/env python3
"""Actualizar todos los datos del portal y subir a GitHub (cron runner).

Corre los 3 scrapers (lotería, tendencias, radio), hace commit y push.
Silencioso si todo OK; imprime error si algo falla (para alerta del cron).
"""
import subprocess
import sys

BASE = "/opt/data/home/portal-dominicano"
SCRIPTS = [
    "scripts/scrape_loteria.py",
    "scripts/scrape_tendencias.py",
    "scripts/scrape_radio.py",
    "scripts/scrape_noticias.py",
]


def run(cmd, cwd=BASE):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def main():
    errors = []
    for s in SCRIPTS:
        r = run([sys.executable, s])
        if r.returncode != 0:
            errors.append(f"{s}: {r.stderr.strip()[-200:]}")

    if errors:
        print("ERROR scrapers:")
        for e in errors:
            print(" -", e)
        return 1

    # push solo si hay cambios
    r = run(["git", "add", "-A"])
    r = run(["git", "commit", "-q", "-m", "auto-update datos (cron)"])
    # exit 1 del commit = nada que commitear -> OK
    r = run(["git", "push", "-q", "origin", "main"])
    if r.returncode != 0:
        print("ERROR push:", r.stderr.strip()[-200:])
        return 1

    # silencio si todo OK (cron no_agent: stdout vacío = sin mensaje)
    return 0


if __name__ == "__main__":
    sys.exit(main())
