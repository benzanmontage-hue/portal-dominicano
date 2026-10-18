#!/usr/bin/env python3
"""Tarjeta de imagen con los resultados del momento: compartir/resultados-hoy.png (1200×1200).

Sirve para compartir en el canal de WhatsApp, Facebook, Telegram e Instagram, y como
imagen de vista previa de la portada. Usa la misma selección que el resumen de la portada.
También escribe data/tarjeta.txt con el texto del mensaje para copiar y pegar.
"""
import os
import re

from PIL import Image, ImageDraw, ImageFont

from comun import ROOT, NOMBRE_COMPANIA, MESES, DIAS, cargar_json, limpiar, parse_fecha, actualizado_rd, hora_12, minutos_juego
from prerender_home import RESUMEN, etiqueta, fecha_rel

AZUL, ROJO, TINTA, GRIS, FONDO, BLANCO = "#002D62", "#CE1126", "#0B1B33", "#4A5A72", "#F2F4F8", "#FFFFFF"
FUENTES = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"]
FUENTES_REG = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/dejavu/DejaVuSans.ttf"]


def fuente(tam, negrita=True):
    for p in (FUENTES if negrita else FUENTES_REG):
        if os.path.exists(p):
            return ImageFont.truetype(p, tam)
    return ImageFont.load_default(size=tam)


def filas(res):
    juegos = res.get("juegos", [])
    hoy = actualizado_rd(res).date()
    out = []
    for comp, cands in RESUMEN:
        js = [j for j in juegos if j["compania"] == comp]
        if cands:
            ops = [(j, m) for g, m in cands for j in js if limpiar(j["juego"]) == g]
        else:
            ops = [(j, minutos_juego(limpiar(j["juego"])) or 0) for j in js if re.match(r"^Anguila \d", limpiar(j["juego"]))]
        if not ops:
            continue
        j, _ = max(ops, key=lambda o: ((o[0].get("fecha") or "")[:10], o[1]))
        d = parse_fecha(j.get("fecha"))
        out.append((NOMBRE_COMPANIA[comp], f"{etiqueta(j['juego'])} · {fecha_rel(d, hoy)}", j["numeros"], d == hoy))
    return out


def main():
    res = cargar_json("resultados.json", {}) or {}
    datos = filas(res)
    if not datos:
        print("tarjeta: sin datos")
        return
    upd = actualizado_rd(res)
    hoy = upd.date()
    W = H = 1200
    img = Image.new("RGB", (W, H), FONDO)
    dr = ImageDraw.Draw(img)

    # cabecera
    dr.rectangle([0, 0, W, 190], fill=AZUL)
    for x, y, c in [(60, 52, BLANCO), (96, 52, ROJO), (60, 88, ROJO), (96, 88, BLANCO)]:
        dr.rounded_rectangle([x, y, x + 30, y + 30], radius=5, fill=c)
    dr.text((150, 50), "Lotería de hoy", font=fuente(56), fill=BLANCO)
    fecha_txt = f"{DIAS[hoy.weekday()].capitalize()} {hoy.day} de {MESES[hoy.month - 1]} · {hora_12(upd)} (hora RD)"
    dr.text((152, 122), fecha_txt, font=fuente(30, False), fill="#C9D4E5")
    dr.rectangle([0, 190, W, 202], fill=ROJO)

    # filas
    y0, alto = 236, 122
    f_nom, f_sub, f_num, f_hoy = fuente(40), fuente(26, False), fuente(40), fuente(22)
    for i, (nombre, sub, nums, es_hoy) in enumerate(datos[:7]):
        y = y0 + i * alto
        dr.rounded_rectangle([40, y, W - 40, y + alto - 14], radius=22, fill=BLANCO)
        dr.text((76, y + 16), nombre, font=f_nom, fill=TINTA)
        dr.text((78, y + 66), sub, font=f_sub, fill=GRIS)
        if es_hoy:
            ancho = dr.textlength(nombre, font=f_nom)
            bx = 76 + ancho + 16
            dr.rounded_rectangle([bx, y + 24, bx + 78, y + 56], radius=8, fill=ROJO)
            dr.text((bx + 12, y + 27), "HOY", font=f_hoy, fill=BLANCO)
        # bolas alineadas a la derecha
        tam, gap = 84, 12
        x = W - 76 - len(nums) * tam - (len(nums) - 1) * gap
        for n in nums:
            dr.rounded_rectangle([x, y + 12, x + tam, y + 12 + tam], radius=18, fill=AZUL)
            tw = dr.textlength(n, font=f_num)
            dr.text((x + (tam - tw) / 2, y + 12 + 18), n, font=f_num, fill=BLANCO)
            x += tam + gap

    # pie
    dr.text((60, H - 82), "portaldominicana.net", font=fuente(36), fill=AZUL)
    aviso = "Informativo. Verifica con la fuente oficial. +18"
    dr.text((W - 60 - dr.textlength(aviso, font=fuente(24, False)), H - 74), aviso, font=fuente(24, False), fill=GRIS)

    os.makedirs(os.path.join(ROOT, "compartir"), exist_ok=True)
    img.save(os.path.join(ROOT, "compartir", "resultados-hoy.png"), optimize=True)

    lineas = [f"🇩🇴 *Lotería de hoy* — {DIAS[hoy.weekday()]} {hoy.day} de {MESES[hoy.month - 1]}, {hora_12(upd)}", ""]
    lineas += [f"*{n}* ({s}): {' - '.join(nums)}" for n, s, nums, _ in datos]
    lineas += ["", "Todos los sorteos: https://portaldominicana.net/", "Informativo. Verifica con la fuente oficial."]
    with open(os.path.join(ROOT, "data", "tarjeta.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")
    with open(os.path.join(ROOT, "data", "tarjeta_numeros.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(f"{n}|{s}|{'-'.join(nums)}" for n, s, nums, _ in datos) + "\n")
    print("OK: compartir/resultados-hoy.png + data/tarjeta.txt")


if __name__ == "__main__":
    main()
