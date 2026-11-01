#!/usr/bin/env python3
"""Avisos al móvil: envía una notificación a quien la pidió cuando salen números nuevos.

Uso: scripts/notificar.py RESULTADOS_ANTERIORES.json
  Compara data/resultados.json con la copia de antes de esta actualización; los sorteos
  principales de hoy que cambiaron se avisan a los suscritos a esa lotería.

Las suscripciones están en Cloudflare KV (las guarda functions/api/avisos.js). La clave para
firmar los avisos (VAPID) también vive ahí, en la entrada "_vapid": se crea sola la primera vez.
Cifrado y firma según los estándares de Web Push (RFC 8291 y RFC 8292), solo con `cryptography`.
"""
import base64
import concurrent.futures
import datetime
import json
import os
import struct
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comun import (ROOT, TZ_RD, SLUG_COMPANIA, NOMBRE_COMPANIA, JUEGO_PRINCIPAL, limpiar,  # noqa: E402
                   parse_fecha, minutos_juego)

KV_ID = "5cf813d3fdf144918ccc3def59d2d679"
SUJETO = "https://portaldominicana.net"
ETIQUETA = {"Lotería Nacional": "Quiniela noche", "Lotería Real Noche": "Real Noche", "Quiniela Real": "Quiniela Real",
            "Quiniela Loteka Noche": "Quiniela noche", "Quiniela Loteka Día": "Quiniela día",
            "Primera Noche": "Primera noche", "La Primera Día": "Primera día", "La Suerte 12:30": "Sorteo 12:30 PM",
            "La Suerte 18:00": "Sorteo 6:00 PM", "Quiniela Leidsa": "Quiniela"}

# Hora aproximada (minutos) de los sorteos sin hora en el nombre; solo para saber cuál es el último del día.
ORDEN_DIA = {"La Primera Día": 720, "Quiniela Real": 775, "Quiniela Loteka Día": 780, "Gana Más": 870,
             "Quiniela Loteka Noche": 1195, "Quiniela Loteka": 1195, "Primera Noche": 1200, "Quiniela Leidsa": 1255,
             "Lotería Nacional": 1255, "Lotería Real Noche": 1260}


# ---------- utilidades ----------
def b64u(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def de_b64u(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def hkdf(salt, ikm, info, largo):
    return HKDF(algorithm=hashes.SHA256(), length=largo, salt=salt, info=info).derive(ikm)


def pub_bytes(clave_publica):
    return clave_publica.public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)


# ---------- Web Push ----------
def cifrar(datos, p256dh, auth):
    """Cuerpo cifrado aes128gcm (RFC 8291) para la suscripción dada."""
    ua_pub = de_b64u(p256dh)
    ua_clave = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), ua_pub)
    propia = ec.generate_private_key(ec.SECP256R1())
    as_pub = pub_bytes(propia.public_key())
    compartido = propia.exchange(ec.ECDH(), ua_clave)
    ikm = hkdf(de_b64u(auth), compartido, b"WebPush: info\x00" + ua_pub + as_pub, 32)
    sal = os.urandom(16)
    cek = hkdf(sal, ikm, b"Content-Encoding: aes128gcm\x00", 16)
    nonce = hkdf(sal, ikm, b"Content-Encoding: nonce\x00", 12)
    cifrado = AESGCM(cek).encrypt(nonce, datos + b"\x02", None)
    return sal + struct.pack(">I", 4096) + bytes([len(as_pub)]) + as_pub + cifrado


def descifrar(cuerpo, ua_privada, auth):
    """Solo para la prueba local: lo que hace el navegador al recibir el aviso."""
    sal, n = cuerpo[:16], cuerpo[20]
    as_pub = cuerpo[21:21 + n]
    ua_pub = pub_bytes(ua_privada.public_key())
    compartido = ua_privada.exchange(ec.ECDH(), ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), as_pub))
    ikm = hkdf(auth, compartido, b"WebPush: info\x00" + ua_pub + as_pub, 32)
    cek = hkdf(sal, ikm, b"Content-Encoding: aes128gcm\x00", 16)
    nonce = hkdf(sal, ikm, b"Content-Encoding: nonce\x00", 12)
    return AESGCM(cek).decrypt(nonce, cuerpo[21 + n:], None).rstrip(b"\x00")[:-1]


def cabecera_vapid(endpoint, privada, pub_b64):
    u = urllib.parse.urlparse(endpoint)
    h = b64u(json.dumps({"typ": "JWT", "alg": "ES256"}).encode())
    c = b64u(json.dumps({"aud": f"{u.scheme}://{u.netloc}", "exp": int(time.time()) + 12 * 3600, "sub": SUJETO}).encode())
    r, s = decode_dss_signature(privada.sign(f"{h}.{c}".encode(), ec.ECDSA(hashes.SHA256())))
    return f"vapid t={h}.{c}.{b64u(r.to_bytes(32, 'big') + s.to_bytes(32, 'big'))}, k={pub_b64}"


def enviar(sub, datos, privada, pub_b64):
    """Devuelve el código HTTP del servicio de avisos (201 = entregado; 404/410 = suscripción caducada)."""
    req = urllib.request.Request(sub["e"], data=cifrar(datos, sub["p"], sub["a"]), method="POST", headers={
        "Authorization": cabecera_vapid(sub["e"], privada, pub_b64), "Content-Encoding": "aes128gcm",
        "Content-Type": "application/octet-stream", "TTL": "7200", "Urgency": "high"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


# ---------- Cloudflare KV ----------
def kv(metodo, ruta, cuerpo=None, tipo="application/json"):
    base = f"https://api.cloudflare.com/client/v4/accounts/{os.environ['CLOUDFLARE_ACCOUNT_ID']}/storage/kv/namespaces/{KV_ID}"
    req = urllib.request.Request(base + ruta, data=cuerpo, method=metodo,
                                 headers={"Authorization": "Bearer " + os.environ["CLOUDFLARE_API_TOKEN"], "Content-Type": tipo})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def clave_vapid():
    """(privada, pública_b64). La crea y la guarda en KV la primera vez."""
    st, cuerpo = kv("GET", "/values/_vapid")
    if st == 200:
        d = de_b64u(cuerpo.decode().strip())
        privada = ec.derive_private_key(int.from_bytes(d, "big"), ec.SECP256R1())
        return privada, b64u(pub_bytes(privada.public_key()))
    if st != 404:
        raise RuntimeError(f"no se pudo leer la clave en Cloudflare KV (HTTP {st}): {cuerpo[:200]!r}")
    privada = ec.generate_private_key(ec.SECP256R1())
    pub = b64u(pub_bytes(privada.public_key()))
    d = b64u(privada.private_numbers().private_value.to_bytes(32, "big"))
    st, cuerpo = kv("PUT", "/bulk", json.dumps([{"key": "_vapid", "value": d, "metadata": {"pub": pub}}]).encode())
    if st != 200:
        raise RuntimeError(f"no se pudo guardar la clave en Cloudflare KV (HTTP {st}): {cuerpo[:200]!r}")
    print("avisos: clave VAPID creada")
    return privada, pub


def suscripciones():
    subs, cursor = [], ""
    while True:
        st, cuerpo = kv("GET", "/keys?limit=1000" + (f"&cursor={urllib.parse.quote(cursor)}" if cursor else ""))
        if st != 200:
            raise RuntimeError(f"no se pudieron leer las suscripciones (HTTP {st})")
        d = json.loads(cuerpo)
        for k in d.get("result", []):
            m = k.get("metadata") or {}
            if k["name"] != "_vapid" and m.get("e") and m.get("l"):
                subs.append({"k": k["name"], **m})
        cursor = (d.get("result_info") or {}).get("cursor") or ""
        if not cursor:
            return subs


# ---------- qué hay de nuevo ----------
def avisables(comp, juego):
    j = limpiar(juego)
    return j in JUEGO_PRINCIPAL.get(comp, []) or (comp == "Anguila" and j.startswith("Anguila ") and minutos_juego(j) is not None)


def nuevos(previo, actual, hoy):
    """Un aviso por lotería como máximo: el sorteo nuevo más tardío de hoy."""
    if not previo.get("juegos"):  # sin datos anteriores no se sabe qué es nuevo: no avisar
        return []
    antes = {(j["compania"], limpiar(j["juego"])): (j.get("fecha"), j.get("numeros")) for j in previo.get("juegos", [])}
    mejor = {}
    for j in actual.get("juegos", []):
        comp, juego = j["compania"], limpiar(j["juego"])
        if comp not in SLUG_COMPANIA or not avisables(comp, juego) or not j.get("numeros"):
            continue
        if parse_fecha(j.get("fecha")) != hoy or antes.get((comp, juego)) == (j.get("fecha"), j.get("numeros")):
            continue
        slug = SLUG_COMPANIA[comp]
        nums = " · ".join(j["numeros"])
        if comp == "Anguila":
            from generate_anguila import slug_hora, etiqueta
            mins = minutos_juego(juego)
            url, sub = f"/anguila/{slug_hora(mins)}/", f"Anguila {etiqueta(mins)}"
        else:
            url, sub = f"/{slug}/", ETIQUETA.get(juego, juego)
        orden = minutos_juego(juego) or ORDEN_DIA.get(juego, 0)
        if slug in mejor and mejor[slug][0] > orden:
            continue
        mejor[slug] = (orden, {"title": f"{NOMBRE_COMPANIA[comp]}: {nums}",
                           "body": f"{sub} de hoy. Toca para ver todos los resultados.",
                           "url": url, "tag": f"{slug}-{juego}"})
    return [(slug, m) for slug, (_o, m) in mejor.items()]


def main():
    if not os.environ.get("CLOUDFLARE_API_TOKEN") or not os.environ.get("CLOUDFLARE_ACCOUNT_ID"):
        print("avisos: sin credenciales de Cloudflare; se omite")
        return 0
    try:
        privada, pub = clave_vapid()
    except Exception as e:
        print(f"::warning::Avisos al móvil: {e}")
        return 1
    if len(sys.argv) < 2:
        return 0
    try:
        previo = json.load(open(sys.argv[1], encoding="utf-8"))
    except Exception:
        previo = {}
    actual = json.load(open(os.path.join(ROOT, "data", "resultados.json"), encoding="utf-8"))
    hoy = datetime.datetime.now(TZ_RD).date()
    novedades = nuevos(previo, actual, hoy)
    if not novedades:
        return 0
    subs = suscripciones()
    tareas = [(s, msg) for slug, msg in novedades for s in subs if slug in s["l"]]
    print(f"avisos: {len(novedades)} sorteo(s) nuevo(s), {len(subs)} suscripción(es), {len(tareas)} aviso(s)")
    if not tareas:
        return 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
        codigos = list(ex.map(lambda t: enviar(t[0], json.dumps(t[1], ensure_ascii=False).encode(), privada, pub), tareas))
    caducadas = {t[0]["k"] for t, c in zip(tareas, codigos) if c in (404, 410)}
    for k in caducadas:
        kv("DELETE", f"/values/{k}")
    ok = sum(1 for c in codigos if 200 <= c < 300)
    print(f"avisos: {ok} entregado(s), {len(caducadas)} suscripción(es) caducada(s) borrada(s), "
          f"{len(codigos) - ok - sum(1 for c in codigos if c in (404, 410))} con error")
    return 0


if __name__ == "__main__":
    if "--prueba" in sys.argv:  # prueba local del cifrado y la firma
        ua = ec.generate_private_key(ec.SECP256R1())
        auth = os.urandom(16)
        msg = json.dumps({"title": "Leidsa: 99 · 87 · 52"}, ensure_ascii=False).encode()
        assert descifrar(cifrar(msg, b64u(pub_bytes(ua.public_key())), b64u(auth)), ua, auth) == msg
        k = ec.generate_private_key(ec.SECP256R1())
        print("cifrado OK;", cabecera_vapid("https://fcm.googleapis.com/fcm/send/x", k, b64u(pub_bytes(k.public_key())))[:60], "…")
        sys.exit(0)
    sys.exit(main())
