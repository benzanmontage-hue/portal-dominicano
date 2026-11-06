#!/usr/bin/env python3
"""Guardar un historial propio de resultados (data/archivo.json).

Cada ejecución toma los resultados actuales de data/resultados.json y los añade al
archivo, una entrada por (compañía, juego, fecha). Así el sitio acumula días anteriores
reales aunque la API solo devuelva el último sorteo de cada juego.
Se conservan los últimos DIAS_GUARDAR días.
"""
import datetime
import json
import os

from comun import ROOT, cargar_json, limpiar, parse_fecha, TZ_RD

DIAS_GUARDAR = 450  # más de un año: las páginas por fecha no deben desaparecer
ARCHIVO = os.path.join(ROOT, "data", "archivo.json")


def archivar(fuente, destino, dias):
    res = cargar_json(fuente, {}) or {}
    arch = cargar_json(destino, {}) or {}
    sorteos = arch.get("sorteos", {})  # "Compania|Juego" -> [{fecha, numeros}]

    limite = (datetime.datetime.now(TZ_RD).date() - datetime.timedelta(days=dias)).isoformat()
    nuevos = 0
    for j in (res.get("juegos") or []) + (res.get("historial") or []):
        d = parse_fecha(j.get("fecha"))
        nums = [str(n) for n in j.get("numeros") or []]
        if not d or not nums or d.isoformat() < limite:
            continue
        clave = j["compania"] + "|" + limpiar(j["juego"])
        lista = sorteos.setdefault(clave, [])
        f = d.isoformat()
        existente = next((x for x in lista if x["fecha"] == f), None)
        if existente:
            existente["numeros"] = nums  # corrección de la fuente
        else:
            lista.append({"fecha": f, "numeros": nums})
            nuevos += 1

    for clave in list(sorteos):
        lista = sorted((x for x in sorteos[clave] if x["fecha"] >= limite),
                       key=lambda x: x["fecha"], reverse=True)
        if lista:
            sorteos[clave] = lista
        else:
            del sorteos[clave]

    out = {"actualizado": datetime.datetime.now(TZ_RD).isoformat(timespec="seconds"),
           "sorteos": dict(sorted(sorteos.items()))}
    with open(os.path.join(ROOT, "data", destino), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"{destino}: {nuevos} sorteos nuevos, {len(sorteos)} juegos")


def main():
    archivar("resultados.json", "archivo.json", DIAS_GUARDAR)
    archivar("resultados_otras.json", "archivo_otras.json", 120)  # Americanas, LoteDom, King…


if __name__ == "__main__":
    main()
