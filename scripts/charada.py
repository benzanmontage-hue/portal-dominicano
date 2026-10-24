#!/usr/bin/env python3
"""La charada (tabla de sueños): número -> significado tradicional.

Fuentes (consultadas el 24-oct-2026), que coinciden en casi todos los números:
  https://www.periodicocubano.com/numeros-de-la-bolita-o-charada-cubana/
  https://www.directoriocubano.info/numeros-de-la-charada-cubana/
Se dejaron fuera acepciones ofensivas o referidas a personas o política.
En la quiniela dominicana (00–99) el 100 de la charada se juega como 00.
"""
import re
import unicodedata

# número: (significado principal, [otros significados])
CHARADA = {
    1: ("Caballo", ["Tintero"]), 2: ("Mariposa", ["Dinero", "Hombre"]), 3: ("Marinero", ["Niño chiquito", "Taza"]),
    4: ("Gato", ["Diente", "Boca"]), 5: ("Monja", ["Mar", "Carta"]), 6: ("Jicotea", ["Tortuga"]),
    7: ("Caracol", []), 8: ("Muerto", ["Calabaza"]), 9: ("Elefante", ["Lengua"]),
    10: ("Pescado grande", ["Malla"]), 11: ("Gallo", ["Fosforera"]), 12: ("Ramera", ["Cometa grande"]),
    13: ("Pavo real", ["Niño grande"]), 14: ("Cementerio de noche", ["Gato tigre", "Enamorados"]),
    15: ("Perro", ["Niña bonita", "Cuchara"]), 16: ("Toro", ["Mujer santa", "Vestido"]),
    17: ("San Lázaro", ["Luna", "Camisón"]), 18: ("Pescado chico", ["Palma"]), 19: ("Lombriz", ["Bandera", "Mesa grande"]),
    20: ("Gato fino", ["Tibor"]), 21: ("Majá", ["Culebra", "Dinero"]), 22: ("Sapo", ["Lirio"]),
    23: ("Vapor", ["Barco", "Escalera"]), 24: ("Paloma", ["Cocina"]), 25: ("Piedra fina", ["Casa nueva", "Sol"]),
    26: ("Anguila", ["Médico"]), 27: ("Avispa", ["Canario"]), 28: ("Chivo", []),
    29: ("Ratón", ["Jutía"]), 30: ("Camarón", ["Almanaque"]), 31: ("Venado", ["Zapato"]),
    32: ("Cochino", ["Puerco chiquito", "Mula"]), 33: ("Tiñosa", ["Madre", "Santo"]), 34: ("Mono", []),
    35: ("Araña", ["Bombillo"]), 36: ("Cachimba", ["Pipa", "Bodega"]), 37: ("Bruja", ["Gallina prieta", "Hormiga"]),
    38: ("Dinero", ["Macao", "Carro"]), 39: ("Conejo", ["Culebra", "Baile"]), 40: ("Cura", ["Sangre", "Cantina"]),
    41: ("Lagartija", []), 42: ("Pato", ["País lejano", "España"]), 43: ("Alacrán", ["Puerta"]),
    44: ("Año del cuero", ["Mal tiempo"]), 45: ("Tiburón", ["Presidente"]), 46: ("Guagua", ["Humo"]),
    47: ("Pájaro", ["Escolta"]), 48: ("Cucaracha", ["Abanico", "Barbería"]), 49: ("Borracho", ["Percha"]),
    50: ("Policía", ["Agua", "Alcalde"]), 51: ("Soldado", ["Sereno"]), 52: ("Bicicleta", ["Abogado"]),
    53: ("Luz eléctrica", ["Beso"]), 54: ("Flores", ["Cañón"]), 55: ("Cangrejo", ["Murciélago"]),
    56: ("Merengue", ["Reina", "Camisa"]), 57: ("Cama", ["Telegrama"]), 58: ("Retrato", ["Cuchillo"]),
    59: ("Loco", ["Langosta"]), 60: ("Payaso", ["Huevo"]), 61: ("Caballo grande", ["Arroz"]),
    62: ("Matrimonio", ["Robo"]), 63: ("Asesino", ["Bandolero"]), 64: ("Muerto grande", ["Muerto vivo", "Escándalo"]),
    65: ("Comida", ["Conejo"]), 66: ("Pareja", ["Tarro"]), 67: ("Puñalada", ["Hospital"]),
    68: ("Cementerio", ["Riña"]), 69: ("Pozo", ["Piano"]), 70: ("Coco", ["Camisa"]),
    71: ("Río", ["Cocodrilo"]), 72: ("Buey", ["Collar"]), 73: ("Maleta", ["Edificio", "Oso"]),
    74: ("Papalote", ["Chichigua", "Militar"]), 75: ("Corbata", ["Guitarra"]), 76: ("Bailarina", ["Fábrica"]),
    77: ("Muletas", ["Billetes"]), 78: ("Ataúd", ["Sarcófago", "Rey"]), 79: ("Tren", ["Lagarto"]),
    80: ("Médico viejo", ["Paraguas"]), 81: ("Teatro", ["Ingenio"]), 82: ("Madre", ["León", "Batea"]),
    83: ("Tragedia", ["Bastón"]), 84: ("Sangre", ["Banquero"]), 85: ("Espejo", ["Reloj"]),
    86: ("Tijeras", ["Manguera"]), 87: ("Plátano", ["Piojo", "Árbol grande"]), 88: ("Espejuelos", ["Gusano"]),
    89: ("Mucha agua", ["Casa vieja", "Cometa"]), 90: ("Viejo", ["Caramelos"]), 91: ("Alpargata", []),
    92: ("Puerco grande", ["Avión", "Globo"]), 93: ("Sortija", ["Vaca", "Leche"]), 94: ("Machete", []),
    95: ("Guerra", ["Perro grande", "Corte de justicia"]), 96: ("Zapato viejo", ["Maletas"]),
    97: ("Mosquito", ["Grillo", "Preso"]), 98: ("Piano", ["Santo"]), 99: ("Serrucho", ["Carbonero"]),
    100: ("Inodoro", ["Automóvil", "Huevos"]),
}


def slug(texto):
    t = unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def jugada(n):
    """Número de la charada (1–100) -> como se juega en la quiniela ('01'…'99', '00')."""
    return "00" if n == 100 else f"{n:02d}"


def de_jugada(s):
    """'00'…'99' -> número de la charada (1–100), o None si no es de dos cifras."""
    s = str(s).strip()
    if not re.fullmatch(r"\d{2}", s):
        return None
    return 100 if s == "00" else int(s)


def significado(s):
    """('Conejo', '/suenos/conejo/') para una jugada '39', o (None, None)."""
    n = de_jugada(s)
    if n is None:
        return None, None
    nombre = CHARADA[n][0]
    return nombre, f"/suenos/{slug(nombre)}/"
