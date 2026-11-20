#!/usr/bin/env python3
"""Páginas de confianza: /acerca/ (qué es el sitio y de dónde salen los datos), /privacidad/ y
/juego-responsable/. Google y los buscadores con IA valoran que un sitio diga quién es, de dónde
saca la información y cómo trata los datos de los visitantes.
"""
from comun import BASE
from plantilla import pagina, jsonld, escribir

PAGINAS = [
    ("acerca", "Acerca de Portal Dominicano", "Acerca de Portal Dominicano",
     "Qué es Portal Dominicano, de dónde salen los resultados de la lotería y los demás datos, cada cuánto se actualizan y qué no hacemos.",
     """  <p class="intro"><strong>Portal Dominicano</strong> es un sitio informativo, gratuito e independiente con los resultados de las loterías que se juegan en República Dominicana y otros datos útiles del día: dólar, combustibles, Lidom y radio dominicana en vivo.</p>
  <h2 class="sect"><span class="bar"></span> Qué no somos</h2>
  <p class="intro">No somos una lotería ni una banca, <strong>no vendemos jugadas</strong> y no estamos afiliados a ninguna de las loterías que publicamos. No damos «números para jugar» ni pronósticos: los sorteos son al azar.</p>
  <h2 class="sect"><span class="bar"></span> De dónde salen los datos</h2>
  <ul class="resumen-txt">
    <li><strong>Lotería:</strong> resultados públicos de los sorteos, recopilados por <a href="https://loteriasdominicanas.com" rel="noopener">loteriasdominicanas.com</a>. Guardamos nuestro propio archivo día a día para las páginas por fecha, el historial y las estadísticas.</li>
    <li><strong>Dólar y euro:</strong> tasas de referencia del mercado internacional (open.er-api.com); el precio en tu banco o casa de cambio puede ser distinto.</li>
    <li><strong>Combustibles:</strong> precios semanales que fija el Ministerio de Industria, Comercio y Mipymes (MICM).</li>
    <li><strong>Lidom:</strong> calendario, marcadores y posiciones oficiales de la liga (MLB Stats API).</li>
    <li><strong>Radio:</strong> emisoras dominicanas del directorio abierto Radio Browser; solo incluimos las que comprobamos que suenan.</li>
    <li><strong>Tabla de sueños:</strong> la charada tradicional del 00 al 99.</li>
  </ul>
  <h2 class="sect"><span class="bar"></span> Cada cuánto se actualiza</h2>
  <p class="intro">El sitio revisa las fuentes cada 10 minutos de 7:00 AM a 1:00 AM (hora RD) y publica los números en cuanto aparecen. Cada página muestra la hora de su última actualización.</p>
  <h2 class="sect"><span class="bar"></span> Errores</h2>
  <p class="intro">Copiamos los números de forma automática y puede haber errores o retrasos. <strong>Verifica siempre tus números con la fuente oficial</strong> de cada lotería antes de cobrar un premio.</p>
  <p class="intro"><a href="/privacidad/">Política de privacidad</a> · <a href="/juego-responsable/">Juego responsable</a></p>"""),
    ("privacidad", "Política de Privacidad — Portal Dominicano", "Política de privacidad",
     "Qué datos guarda Portal Dominicano: sin registro ni cuentas; preferencias en tu navegador; avisos al móvil solo si los activas. No vendemos datos.",
     """  <p class="intro">Portal Dominicano se usa sin registrarse. No pedimos nombre, correo ni teléfono.</p>
  <h2 class="sect"><span class="bar"></span> Lo que se guarda en tu navegador</h2>
  <p class="intro">Algunas preferencias se guardan solo en tu propio navegador (almacenamiento local): tus loterías favoritas, la última emisora de radio que escuchaste y las loterías de las que pediste avisos. Puedes borrarlas borrando los datos del sitio en tu navegador.</p>
  <h2 class="sect"><span class="bar"></span> Avisos al móvil</h2>
  <p class="intro">Si activas los avisos, tu navegador nos da una dirección técnica para enviarte notificaciones, junto con las loterías que elegiste. La guardamos en Cloudflare solo para mandarte esos avisos. Al quitar los avisos (o si la dirección caduca) se borra. No contiene tu nombre ni tu número.</p>
  <h2 class="sect"><span class="bar"></span> Estadísticas de visitas</h2>
  <p class="intro">Podemos medir cuántas personas visitan cada página con las estadísticas de Cloudflare, que no usan cookies de seguimiento ni crean un perfil tuyo.</p>
  <h2 class="sect"><span class="bar"></span> Servicios de terceros</h2>
  <p class="intro">La radio se escucha directamente desde los servidores de cada emisora, y los enlaces a otros sitios llevan a páginas con sus propias políticas. No vendemos ni compartimos datos de los visitantes.</p>
  <p class="intro"><a href="/acerca/">Acerca de Portal Dominicano</a> · <a href="/juego-responsable/">Juego responsable</a></p>"""),
    ("juego-responsable", "Juego Responsable — Lotería en República Dominicana", "Juego responsable",
     "La lotería es un juego de azar: consejos para jugar con responsabilidad, señales de alerta y por qué ningún número tiene más probabilidad de salir.",
     """  <p class="intro">La lotería es un <strong>juego de azar</strong>. Cada sorteo es independiente: ningún número «está por salir», ni la charada, ni las estadísticas de números que más salen cambian la probabilidad del próximo sorteo.</p>
  <h2 class="sect"><span class="bar"></span> Para jugar con responsabilidad</h2>
  <ul class="resumen-txt">
    <li>Juega solo dinero que puedas perder sin afectar la comida, el alquiler o las deudas.</li>
    <li>Decide antes cuánto vas a gastar a la semana y no lo pases.</li>
    <li>No juegues para recuperar lo que perdiste.</li>
    <li>No pidas prestado para jugar.</li>
    <li>La lotería es entretenimiento, no una forma de ganar dinero.</li>
    <li>Los menores de edad no deben jugar.</li>
  </ul>
  <h2 class="sect"><span class="bar"></span> Señales de alerta</h2>
  <p class="intro">Si juegas más de lo que planeabas, escondes lo que gastas, te endeudas por jugar o te sientes mal cuando no juegas, habla con alguien de confianza o busca ayuda profesional con tu médico o un psicólogo.</p>
  <p class="intro"><a href="/acerca/">Acerca de Portal Dominicano</a> · <a href="/privacidad/">Política de privacidad</a></p>"""),
]


def main():
    for slug, title, h1, desc, cuerpo in PAGINAS:
        ruta = f"/{slug}/"
        migas = [("Portal Dominicano", "/"), (h1, ruta)]
        escribir(ruta, pagina(ruta=ruta, title=title, desc=desc, h1=h1, migas=migas, cuerpo=cuerpo,
                              ld=jsonld(BASE + ruta, h1, desc, migas)))
    print(f"OK: {len(PAGINAS)} páginas de confianza")


if __name__ == "__main__":
    main()
