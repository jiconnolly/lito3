# -*- coding: utf-8 -*-
"""Genera "el libro del club": el sitio del Centro Atlético Lito.

Uso: python3 build.py

La portada es la tapa de un tomo encuadernado; cada sección del sitio es un
capítulo de ese libro. Cabecera, colofón y metadatos se comparten desde acá:
para cambiar cualquier texto institucional hay que editar este archivo y volver
a correrlo, no los HTML sueltos, porque el script los sobreescribe.
"""
import json
import os
import re
from html.parser import HTMLParser

SITIO = "Centro Atlético Lito"
DOMINIO = "calito.uy"

# Dónde vive el sitio publicado. Las redes (WhatsApp, Instagram, X, LinkedIn)
# exigen URL absoluta en og:image: con ruta relativa muchas no muestran nada o
# se quedan con lo último que cachearon. Cambiar por "https://calito.uy" el día
# que el dominio propio apunte acá.
SITIO_URL = "https://jiconnolly.github.io/lito3"

# Versión de los assets de marca. Los scrapers de redes y el favicon del
# navegador cachean por URL y no se enteran de que el archivo cambió: subir
# este número cada vez que se reemplaza el escudo, el favicon o la imagen de
# compartir fuerza a todos a buscar la nueva.
V = "3"
BASE = os.path.dirname(os.path.abspath(__file__))

# Mientras el contenido no esté aprobado por el club, las páginas van con
# noindex. Poner en False y regenerar antes de publicar.
NOINDEX = True

# Los capítulos del libro, en orden de lectura.
CAPITULOS = [
    ("club.html", "El club", "I", "De 1917 a hoy"),
    ("plantel.html", "Plantel", "II", "Primer equipo y formativas"),
    ("fixture.html", "Fixture y tabla", "III", "Domingo a domingo"),
    ("noticias.html", "Noticias", "IV", "Partes de prensa"),
    ("galeria.html", "Galería", "V", "Fotos del plantel y los partidos"),
    ("proyecto.html", "El próximo capítulo", "VI", "La cancha nueva"),
    ("socios.html", "Hacete socio", "VII", "Cuotas y alta"),
    ("contacto.html", "Contacto", "VIII", "Sede, prensa y marca"),
]



# ---------------------------------------------------------------- traducción

# El sitio se genera dos veces: español en la raíz e inglés en /en/. La
# traducción no es un buscar-y-reemplazar sobre el HTML —eso rompe atributos y
# pisa pedazos de palabra—: se recorre el marcado y se cambian sólo los nodos
# de texto y los atributos que el visitante llega a leer.
ATRIBUTOS_VISIBLES = ("alt", "title", "placeholder", "aria-label", "content")
# La letra del himno queda en español: es la canción del club, no una leyenda.
SIN_TRADUCIR = ("cancion-letra", "himno-hoja")
# Nombres propios y valores técnicos: iguales en los dos idiomas.
FIJAS = {
    "Centro Atlético Lito", "Lito", "ENAS", "English", "es_UY", "website",
    "noindex, nofollow", "summary_large_image", "width=device-width, initial-scale=1",
    # El propio botón de idioma: lo reescribe main() al pasar la página a inglés.
    "EN", "English", "Read this page in English",
}


class Traductor(HTMLParser):
    def __init__(self, mapa):
        super().__init__(convert_charrefs=False)
        self.mapa = mapa
        self.salida = []
        self.faltan = []
        self.crudo = 0        # dentro de script/style no se toca nada
        self.profundidad = 0  # cuántas etiquetas abiertas llevamos
        self.literal = None   # profundidad a la que empezó la letra del himno

    def _tag(self, tag, attrs, cierra=False):
        partes = ["<" + tag]
        for k, v in attrs:
            if v is None:
                partes.append(" " + k)
                continue
            if k in ATRIBUTOS_VISIBLES and k != "content":
                v = self.traducir(v)
            elif k == "content" and not v.startswith(("http", "#", "width=")):
                v = self.traducir(v)
            partes.append(f' {k}="{html_escape(v)}"')
        partes.append("/>" if cierra else ">")
        return "".join(partes)

    def traducir(self, texto):
        clave = " ".join(texto.split())
        if not clave:
            return texto
        if clave in self.mapa:
            return texto.replace(clave, self.mapa[clave]) if texto.strip() == clave else self.mapa[clave]
        if self.hay_que_traducir(clave):
            self.faltan.append(clave)
        return texto

    @staticmethod
    def hay_que_traducir(clave):
        """Números romanos, colores, marcas y direcciones se escriben igual en
        los dos idiomas: no son frases pendientes."""
        if not re.search(r"[a-záéíóúñü]", clave, re.I):
            return False
        if re.fullmatch(r"[IVX]+", clave):
            return False
        if clave.startswith(("#", "@", "http")) or "@" in clave:
            return False
        return clave not in FIJAS

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.crudo += 1
        if self.literal is None and any(c in (dict(attrs).get("class") or "") for c in SIN_TRADUCIR):
            self.literal = self.profundidad
        self.profundidad += 1
        self.salida.append(self._tag(tag, attrs))

    def handle_startendtag(self, tag, attrs):
        self.salida.append(self._tag(tag, attrs, cierra=True))

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.crudo = max(0, self.crudo - 1)
        self.profundidad = max(0, self.profundidad - 1)
        # La zona literal termina cuando se cierra la etiqueta que la abrió.
        if self.literal is not None and self.profundidad <= self.literal:
            self.literal = None
        self.salida.append(f"</{tag}>")

    def handle_data(self, data):
        if self.crudo or self.literal is not None or not data.strip():
            self.salida.append(data)
            return
        original = data
        limpio = " ".join(data.split())
        traducido = self.traducir(limpio)
        # Un & suelto en la traducción tiene que salir escapado, o el HTML
        # queda inválido ("Fixtures & Table").
        traducido = re.sub(r"&(?![a-zA-Z#][a-zA-Z0-9]*;)", "&amp;", traducido)
        if traducido == limpio:
            self.salida.append(original)
        else:
            izq = original[: len(original) - len(original.lstrip())]
            der = original[len(original.rstrip()):]
            self.salida.append(izq + traducido + der)

    def handle_entityref(self, name): self.salida.append(f"&{name};")
    def handle_charref(self, name): self.salida.append(f"&#{name};")
    def handle_comment(self, data): self.salida.append(f"<!--{data}-->")
    def handle_decl(self, decl): self.salida.append(f"<!{decl}>")


def html_escape(v):
    return v.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def a_ingles(html, mapa):
    """Devuelve la página en inglés y la lista de frases que quedaron sin traducir."""
    t = Traductor(mapa)
    t.feed(html)
    salida = "".join(t.salida)
    # En /en/ las páginas cuelgan de un subdirectorio: los assets y los datos
    # están un nivel más arriba. Los enlaces entre capítulos quedan igual,
    # porque las nueve páginas en inglés viven juntas.
    salida = salida.replace('="assets/', '="../assets/').replace('="data/', '="../data/')
    salida = salida.replace('<html lang="es-UY">', '<html lang="en">')
    salida = salida.replace('property="og:locale" content="es_UY"', 'property="og:locale" content="en"')
    return salida, t.faltan


LETRA_HIMNO = """<p><span class="inicial">L</span>ito querido,<br>
              cuadro invencible,<br>
              fuerte, aguerrido e irresistible.</p>
            <p>Siempre Centro Lito adelante,<br>
              triunfante, triunfante,<br>
              porque tiene garra y corazón,<br>
              campeón, campeón.</p>
            <p>Que proclaman tus parciales,<br>
              que son inmortales,<br>
              tu gloria y honor.</p>"""


def encabezado_html(titulo, descripcion, archivo=""):
    robots = '<meta name="robots" content="noindex, nofollow">\n' if NOINDEX else ""
    return f"""<!DOCTYPE html>
<html lang="es-UY">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titulo} · {SITIO}</title>
<meta name="description" content="{descripcion}">
{robots}<link rel="canonical" href="{SITIO_URL}/{archivo}">
<link rel="alternate" hreflang="es" href="{SITIO_URL}/{archivo}">
<link rel="alternate" hreflang="en" href="{SITIO_URL}/en/{archivo}">
<link rel="alternate" hreflang="x-default" href="{SITIO_URL}/{archivo}">
<meta property="og:title" content="{titulo} · {SITIO}">
<meta property="og:description" content="{descripcion}">
<meta property="og:type" content="website">
<meta property="og:locale" content="es_UY">
<meta property="og:site_name" content="{SITIO}">
<meta property="og:url" content="{SITIO_URL}/{archivo}">
<meta property="og:image" content="{SITIO_URL}/assets/img/og.png?v={V}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Escudo del {SITIO}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{SITIO_URL}/assets/img/og.png?v={V}">
<meta name="theme-color" content="#0F1A40">
<link rel="icon" href="assets/img/favicon.png?v={V}">
<link rel="apple-touch-icon" href="assets/img/escudo-180.png?v={V}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@300;400;500;600;700&family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Pinyon+Script&family=Manrope:wght@400;500;600;700&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/css/main.css">
</head>
<body>
<a class="saltar" href="#contenido">Ir al contenido</a>
"""


NAV_CORTO = {
    "El club": "Club",
    "Fixture y tabla": "Fixture",
    "El próximo capítulo": "Próximo capítulo",
    "Hacete socio": "Socios",
}


def cabecera_hoja(actual):
    """Cornisa de las páginas interiores: escudo chico y los capítulos.

    Sin enlace a la portada: el escudo de la izquierda ya lleva ahí, y con
    ocho capítulos cada palabra de más manda la cornisa a dos líneas."""
    enlaces = "\n".join(
        '        <a href="{h}"{a}>{t}</a>'.format(
            h=h, t=NAV_CORTO.get(t, t), a=' aria-current="page"' if h == actual else ""
        )
        for h, t, _, _ in CAPITULOS
    )
    return f"""
<header class="cabecera">
  <div class="marco cabecera-fila">
    <a class="marca" href="index.html">
      <img src="assets/img/escudo.png" alt="" width="720" height="879">
      <span class="marca-texto">Centro Atlético Lito
        <small>Montevideo · 1917</small>
      </span>
    </a>
    <a class="idioma" href="en/{actual}" hreflang="en" lang="en" aria-label="Read this page in English" data-idioma>EN</a>
    <button class="menu-boton" aria-expanded="false" aria-controls="menu-principal">Capítulos</button>
    <nav class="menu" id="menu-principal" aria-label="Capítulos del libro">
{enlaces}
    </nav>
  </div>
</header>

<main id="contenido" class="hoja">
"""


def portadilla(romano, titulo, bajada):
    return f"""<section class="portadilla">
  <div class="marco">
    <p class="romano-grande">Capítulo {romano}</p>
    <h1>{titulo}</h1>
    <p class="plomo">{bajada}</p>
    <div class="filete-cap"></div>
  </div>
</section>
"""


def folio(romano, titulo):
    return f"""<p class="folio"><i></i> {romano} · {titulo} · Centro Atlético Lito <i></i></p>
"""


def colofon():
    enlaces_capitulos = "\n".join(
        f'          <li><a href="{h}">{t}</a></li>' for h, t, _, _ in CAPITULOS[:4]
    )
    return f"""</main>

<footer class="pie">
  <div class="marco">
    <div class="pie-grilla">
      <div class="pie-escudo">
        <img src="assets/img/escudo.png" alt="" width="720" height="879" loading="lazy">
        <div>
          <strong>Centro Atlético Lito</strong><br>
          Arroyo Seco, Montevideo, Uruguay.<br>
          Fundado el 24 de julio de 1917.<br>
          Primera Divisional C · AUF.
        </div>
      </div>
      <div>
        <h4>Capítulos</h4>
        <ul>
{enlaces_capitulos}
        </ul>
      </div>
      <div>
        <h4>Hinchada</h4>
        <ul>
          <li><a href="socios.html">Hacete socio</a></li>
          <li><a href="socios.html#cuotas">Cuotas</a></li>
          <li><a href="contacto.html">Contacto</a></li>
          <li><a href="contacto.html#prensa">Prensa y marca</a></li>
          <li><a href="club.html#himno">El himno</a></li>
        </ul>
      </div>
      <div>
        <h4>Seguinos</h4>
        <ul>
          <li><a href="https://instagram.com/centroatleticolito" rel="noopener">Instagram</a></li>
          <li><a href="https://www.facebook.com/groups/707943076074966" rel="noopener">Facebook</a></li>
          <li><a href="mailto:marca@{DOMINIO}">marca@{DOMINIO}</a></li>
        </ul>
      </div>
    </div>
    <div class="pie-legal">
      <span>© <span data-anio>2026</span> Centro Atlético Lito · {DOMINIO}</span>
      <span>Identidad visual según Manual de Marca, edición 2026</span>
    </div>
  </div>
</footer>

<script src="assets/js/main.js"></script>
</body>
</html>
"""


AVISO_EJEMPLO = """      <p class="nota" data-aviso-ejemplo hidden>
        Datos de ejemplo. Cargar la información oficial antes de publicar el sitio.
      </p>
"""


# ============================================================
# Portada: la tapa del libro
# ============================================================

def pagina_portada():
    indice = "\n".join(f"""        <li>
          <a href="{h}">
            <span class="romano">{r}</span>
            <span class="titulo">{t}</span>
            <span class="apunte">{a}</span>
          </a>
        </li>""" for h, t, r, a in CAPITULOS)

    return f"""
<main id="contenido" class="portada-editorial">
<section class="portada-viva" aria-labelledby="titulo-portada">
  <img class="portada-foto" src="assets/img/galeria/partido-5.jpg" alt="El plantel de Lito sale del túnel hacia la cancha" width="1200" height="1500" fetchpriority="high">
  <div class="portada-cornisa">
    <span>El libro del club · Tomo 1917</span>
    <span class="portada-cornisa-fin">
      <a class="idioma idioma--portada" href="en/index.html" hreflang="en" lang="en" aria-label="Read this page in English" data-idioma>EN</a>
      <a href="socios.html">Hacete socio ↗</a>
    </span>
  </div>
  <div class="portada-relato">
    <img class="portada-escudo" src="assets/img/escudo.png" alt="Escudo del Centro Atlético Lito" width="720" height="879">
    <p class="cintilla">1917 · Montevideo</p>
    <h1 id="titulo-portada"><span>Centro Atlético</span>Lito</h1>
    <p class="portada-lema">Garra y Corazón</p>
    <p class="portada-bajada">Un barrio. Una camiseta.<br>Una historia que sigue en la cancha.</p>
    <div class="acciones">
      <a class="boton" href="#libro" data-entrada>Abrir el libro <span aria-hidden="true">↓</span></a>
      <a class="portada-fixture" href="fixture.html">Fixture y resultados ↗</a>
    </div>
  </div>
  <div class="portada-pie">
    <span>De Arroyo Seco desde 1917.</span>
    <span>Archivo histórico / Fútbol vivo</span>
  </div>
</section>

<section class="actualidad-portada" aria-label="Actualidad deportiva">
  <div class="marco">
    <div class="encabezado-seccion">
      <div>
        <p class="cintilla">El club, hoy</p>
        <h2>La próxima página<br>se juega en la cancha.</h2>
      </div>
      <nav class="atajos" aria-label="Información deportiva">
        <a href="fixture.html">Fixture</a>
        <a href="fixture.html#tabla">Tabla</a>
        <a href="fixture.html#resultados">Resultados</a>
      </nav>
    </div>
    <div data-partidos="proximo"><p>Consultá la programación en <a href="fixture.html">Fixture y tabla</a>.</p></div>
  </div>
</section>

<section id="libro" class="entrada-indice">
  <p class="cintilla">Ocho capítulos. Una misma camiseta.</p>
  <h2>Entrá en nuestra historia.</h2>
  <p>Elegí un capítulo del libro.</p>
</section>

<div class="escena" data-escena>
  <button class="abrir-libro" type="button" data-abrir>Abrir el libro del club</button>
  <div class="camara" data-camara>
    <div class="tablero"></div>
    <div class="mesa">
      <div class="sombra"></div>
      <div class="libro" data-libro>

      <span class="cara-lomo" aria-hidden="true"></span>
      <span class="cara-cabeza" aria-hidden="true"></span>
      <span class="cara-canto" aria-hidden="true"></span>
      <div class="contratapa" aria-hidden="true"></div>

    <div class="hoja-indice">
      <h1>El libro del club</h1>
      <p class="sello">Centro Atlético Lito · Montevideo · 1917</p>
      <div class="regla"></div>
      <ul class="indice">
{indice}
      </ul>
      <p class="indice-pie">
        <span>Tomo del club · 2026</span>
        <a href="socios.html">Hacete socio</a>
      </p>
      <div class="marcas">
        <img src="assets/img/marcas/auf.png" alt="Asociación Uruguaya de Fútbol" width="111" height="180" loading="lazy">
        <img src="assets/img/marcas/mgr.png" alt="MGR Sport" width="342" height="110" loading="lazy">
        <img src="assets/img/marcas/enas.png" alt="ENAS" width="509" height="100" loading="lazy">
        <img src="assets/img/marcas/pinuccio.png" alt="Pinuccio Trattoria" width="279" height="130" loading="lazy">
      </div>
    </div>

    <div class="tapa">
      <span class="cara cara-frente" aria-hidden="true">
        <span class="grabado-arriba">Centro Atlético<b class="nombre">Lito</b></span>
        <img class="escudo-tapa" src="assets/img/escudo-tapa.png" alt="Escudo del Centro Atlético Lito" width="760" height="911" fetchpriority="high">
        <span class="lema">Garra y Corazón</span>
        <span class="grabado-abajo">Montevideo · 1917</span>
      </span>
      <span class="cara cara-dorso">
        <div class="cancion">
          <p class="cancion-rotulo">Canción oficial</p>
          <div class="cancion-letra">
            """ + LETRA_HIMNO + """
          </div>
          <p class="cancion-pie">Centro Atlético Lito · Montevideo · 1917</p>
        </div>
      </span>
    </div>

    <div class="hoja-vuelta" aria-hidden="true"></div>

      </div>
    </div>
  </div>

  </div>
</div>
"""


# ============================================================
# Capítulos
# ============================================================

def hueco(rotulo, proporcion="4 / 5", archivo=None, alt="", credito=""):
    """Un lugar reservado para una foto que todavía no existe.

    Cuando la foto llegue, se pasa el archivo por `archivo` y este mismo
    llamado la dibuja: no hay que tocar el marcado alrededor. Sin archivo
    dibuja un marco discreto con el rótulo de lo que va ahí."""
    pie = f'<figcaption>{credito}</figcaption>' if credito else ""
    if archivo:
        return (f'<figure class="hueco"><img src="{archivo}" alt="{alt or rotulo}" loading="lazy">'
                f'{pie}</figure>')
    return (f'<figure class="hueco hueco--vacio" style="aspect-ratio:{proporcion}">'
            f'<span class="hueco-rotulo">{rotulo}</span></figure>')


def momento(anio, titulo, bajada, ancla):
    """Cabecera de uno de los cuatro grandes momentos del club."""
    return f"""
<section class="momento" id="{ancla}">
  <div class="marco momento-fila">
    <p class="momento-anio">{anio}</p>
    <div>
      <h2 class="momento-titulo">{titulo}</h2>
      <p class="momento-bajada">{bajada}</p>
    </div>
  </div>
</section>
"""


def cierre():
    """La última página del libro. Va sólo en los capítulos que cierran el
    arco narrativo, no en todos, para que no se gaste."""
    return """
<section class="cierre">
  <div class="marco">
    <p class="cierre-frase">La historia ya está escrita.<br><em>El próximo capítulo, no.</em></p>
    <img class="cierre-escudo" src="assets/img/escudo.png" alt="" width="720" height="879" loading="lazy">
    <p class="cierre-firma">Centro Atlético Lito<span>1917 — Montevideo</span></p>
    <p class="cierre-accion"><a class="boton" href="socios.html">Sé parte del próximo capítulo</a></p>
  </div>
</section>
"""


def himno():
    return """
<section class="seccion himno" id="himno">
  <div class="marco himno-marco">
    <p class="cintilla">Canción oficial</p>
    <h2>El himno de Lito</h2>
    <div class="himno-hoja">
      <div class="cancion-letra">
        """ + LETRA_HIMNO + """
      </div>
      <p class="cancion-pie">Centro Atlético Lito · Montevideo · 1917</p>
    </div>
    <div class="reproductor" data-himno-audio>
      <span class="reproductor-icono" aria-hidden="true">&#9654;</span>
      <span>La grabación se sube acá cuando el club la tenga.</span>
    </div>
  </div>
</section>
"""


def cap_club():
    return portadilla("I", "El club", "Nacimos el 24 de julio de 1917 en un café de Arroyo Seco. Desaparecimos, volvimos, y estamos escribiendo lo que sigue.") + """
<nav class="riel" aria-label="Los cuatro momentos del club">
  <div class="marco riel-fila">
    <a href="#nacimos"><b>1917</b><span>Nacimos</span></a>
    <a href="#historia"><b>1921</b><span>Hicimos historia</span></a>
    <a href="#volvimos"><b>2022</b><span>Volvimos</span></a>
    <a href="#proximo"><b>2026</b><span>El próximo capítulo</span></a>
  </div>
</nav>
<section class="seccion historia-rapida" aria-label="La historia en siete hitos">
  <div class="marco">
    <p class="cintilla">Más de un siglo, de un vistazo</p>
    <h2>Hay historias que no se apagan.</h2>
    <ol class="timeline-visual">
      <li><b>1917</b><h3>Nace Lito</h3><p>24 de julio. Un café de Arroyo Seco se convierte en club.</p></li>
      <li><b>1920</b><h3>Campeón de Intermedia</h3><p>El segundo ascenso al hilo abre la puerta a Primera.</p></li>
      <li><b>1921</b><h3>Entre los grandes</h3><p>Lito llega al Campeonato Uruguayo de Primera División.</p></li>
      <li><b>1922–23</b><h3>Campañas históricas</h3><p>Quinto puesto en ambas temporadas.</p></li>
      <li><b>1947</b><h3>El silencio</h3><p>Se interrumpe la participación oficial. El vínculo con el barrio permanece.</p></li>
      <li><b>2022</b><h3>El regreso a AUF</h3><p>La azulgrana vuelve a competir en la Divisional D.</p></li>
      <li><b>2023</b><h3>Campeón otra vez</h3><p>Título de la Divisional D y ascenso.</p></li>
    </ol>
  </div>
</section>
""" + momento("1917", "Nacimos", "En un café de Arroyo Seco, con el nombre del hombre del mostrador.", "nacimos") + """
<section class="seccion">
  <div class="marco">
    <div class="rejilla rejilla--2">
      <div class="prosa">
        <p class="capitular">El nombre salió del mostrador. Manuel Semino era «Lito» para todo el barrio, y su café, en Agraciada y Santa Fe, era el punto de encuentro de Arroyo Seco. Cuando el 24 de julio de 1917 los que paraban ahí decidieron fundar el club, le pusieron el nombre del café.</p>
        <details class="lectura-archivo">
          <summary>Seguí leyendo: los primeros colores</summary>
          <p>La primera camiseta fue azul eléctrico con vivos rojos y pantalón blanco, con el escudo sobre el pecho izquierdo. De ahí viene el apodo: la azulgrana de Arroyo Seco. La de hoy sigue esa línea: azul francia, cuello rojo y vivo rojo en las mangas.</p>
          <p>Un club nace de un barrio antes que de un acta. Lito no se mudó nunca: la misma cuadrícula de calles que llevaba al café lleva hoy a la cancha.</p>
        </details>
      </div>
      <div>
        <figure class="foto-album" style="margin:0">
          <img src="assets/img/historia/cafe-lito.jpg" alt="El café de la esquina de Agraciada y Santa Fe, donde se fundó el club" width="471" height="352" loading="lazy">
        </figure>
        <p class="epigrafe">El café de Agraciada y Santa Fe. De ese mostrador salió el nombre.</p>
      </div>
    </div>
  </div>
</section>

<section class="lamina acta">
  <div class="marco claro acta-fila">
    <div>
      <p class="cintilla">Acta N.º 1</p>
      <h2>La noche en que empezó todo</h2>
      <p class="prosa">A las diez de la noche del 24 de julio de 1917, bajo la presidencia ad hoc de Juan Pérez (hijo), la asamblea aprueba por unanimidad formar «un centro con fines deportivos y recreativos». El libro de actas del club abre con esa página.</p>
      <p class="epigrafe epigrafe--claro">Acta fundacional. Original en el archivo del club.</p>
    </div>
    <figure class="hueco">
      <img src="assets/img/historia/acta-1917.png" alt="Primera página del libro de actas del club: el acta de fundación del 24 de julio de 1917" loading="lazy">
    </figure>
  </div>
</section>

<section class="seccion barrio">
  <div class="marco">
    <p class="cintilla">El barrio</p>
    <h2>De Arroyo Seco<br>desde 1917.</h2>
    <p class="prosa">Entre el puerto y la Rambla, de calles cortas y galpones bajos. El club se fundó a metros de acá y nunca se fue.</p>
    <figure class="barrio-panorama">
      <img src="assets/img/proyecto/terreno.jpg" alt="El predio de Lito entre las calles y galpones de Arroyo Seco" loading="lazy">
      <figcaption>La cancha, las calles, el barrio. Arroyo Seco, Montevideo.</figcaption>
    </figure>
    <p class="prosa">El café de Agraciada y Santa Fe fue el punto de encuentro. La cancha sigue siendo una forma de encontrarnos.</p>
    <div class="barrio-grilla">
""" + hueco("Calle de Arroyo Seco", "3 / 4") + hueco("Esquina del barrio", "3 / 4") + hueco("Fachadas y arquitectura", "3 / 4") + hueco("Un lugar de la historia del club", "3 / 4") + """
    </div>
    <p class="epigrafe">Cuatro lugares reservados para fotos reales del barrio. Se cargan pasándole el archivo al mismo bloque; no hay que tocar el diseño.</p>
  </div>
</section>
""" + momento("1921", "Hicimos historia", "Ocho temporadas en la Primera del fútbol uruguayo y tres campeones del mundo formados acá.", "historia") + """
<section class="seccion">
  <div class="marco">
    <div class="rejilla rejilla--2">
      <div class="prosa">
        <p>Afiliado a la AUF, Lito ganó la Divisional Extra en 1919 y la Intermedia en 1920. Dos ascensos al hilo lo dejaron en el Campeonato Uruguayo de 1921, y ahí se mantuvo hasta 1928. Sus mejores temporadas fueron 1922 y 1923: quinto puesto, entre los grandes.</p>
        <details class="lectura-archivo">
          <summary>Del amateurismo a los años de silencio</summary>
        <p>Cuando el fútbol se profesionalizó en 1932, el club siguió amateur y jugó en el ascenso hasta desaparecer de la competencia oficial cerca de 1947. Desde 1952 volvió a jugar en la Federación Uruguaya de Fútbol Amateur, impulsado por los hijos de Vicente Cappuccio: dos campeonatos y dos subcampeonatos. Dejó de competir en 1960. Después, silencio.</p>
        </details>
      </div>
      <div class="archivo archivo--pila">
""" + hueco("Archivo", "4 / 3", "assets/img/historia/plantel-1920.jpg", "El plantel de Lito en 1920", "1920. El año del ascenso: campeón de la Divisional Intermedia.") + hueco("Archivo", "4 / 3", "assets/img/historia/plantel-1921.jpg", "El plantel de Lito en 1921, con la bandera del club", "1921. El debut en la Primera del fútbol uruguayo.") + """
      </div>
    </div>
  </div>
</section>

<section class="lamina campeones" id="archivo">
  <div class="marco claro">
    <p class="cintilla">Archivo histórico · Los campeones</p>
    <h2>Antes de ser campeones del mundo,<br>fueron de Lito.</h2>
    <p class="prosa campeones-bajada">Nasazzi. Castro. Cea. Tres nombres de nuestra historia que también son historia del fútbol mundial.</p>
    <div class="campeones-grilla">
      <article class="campeon">
""" + hueco("Retrato · José Nasazzi", "4 / 5", "assets/img/historia/nasazzi.jpg", "Retrato de José Nasazzi") + """
        <h3>José Nasazzi</h3>
        <p class="detalle">Debutó en Lito. Capitán de Uruguay.</p>
      </article>
      <article class="campeon">
""" + hueco("Retrato · Héctor «Manco» Castro", "4 / 5", "assets/img/historia/castro.jpg", "Retrato de Héctor «Manco» Castro") + """
        <h3>Héctor «Manco» Castro</h3>
        <p class="detalle">Debutó en Lito.</p>
      </article>
      <article class="campeon">
""" + hueco("Retrato · Pedro Cea", "4 / 5", "assets/img/historia/cea.jpg", "Retrato de Pedro Cea") + """
        <h3>Pedro Cea</h3>
        <p class="detalle">Pasó por Lito.</p>
      </article>
    </div>
    <div class="campeones-pie">
""" + hueco("Uruguay campeón, 1930", "3 / 2", "assets/img/historia/uruguay-1930.jpg", "El equipo de Uruguay campeón del mundo en 1930", "Uruguay, campeón del mundo en 1930.") + hueco("Archivo", "4 / 3", "assets/img/historia/archivo-1.jpg", "Fotografía de archivo del fútbol uruguayo de la época", "Archivo · pie de foto a confirmar") + """
    </div>
  </div>
</section>

<section class="seccion escision">
  <div class="marco">
    <p class="cintilla">La escisión</p>
    <h2>Dos Lito a la vez</h2>
    <p class="prosa">Durante el cisma del fútbol uruguayo, Lito fue uno de los tres clubes que presentaron dos equipos en las competencias paralelas. La única forma de distinguirlos era el escudo de la camiseta. De los dos, el que llegó hasta hoy es el redondo.</p>
    <div class="escision-fila">
      <article class="escision-lado">
""" + hueco("Escudo del Lito redondo", "1 / 1", "assets/img/escudo.png", "Escudo del Lito redondo, el de la AUF: blasón de cuarteles rojos y azules con la pelota al centro") + """
        <h3>Lito redondo</h3>
        <p class="detalle">El equipo de la AUF. Es el escudo que el club sigue usando hoy.</p>
      </article>
      <p class="escision-versus">vs.</p>
      <article class="escision-lado">
""" + hueco("Escudo del Lito cuadrado", "1 / 1", "assets/img/historia/escudo-cuadrado.png", "Escudo del Lito cuadrado: cruz roja en aspa sobre fondo azul, con las iniciales C A L y el año 1917") + """
        <h3>Lito cuadrado</h3>
        <p class="detalle">El equipo de la Federación. Escudo de ángulos rectos.</p>
      </article>
    </div>
  </div>
</section>

<section class="seccion">
  <div class="marco">
    <div class="rejilla rejilla--2">
      <div>
        <p class="cintilla">Archivo</p>
        <h2>La línea de tiempo</h2>
        <ul class="cronologia cronologia--compacta">
          <li><b>1917</b><span><strong>Fundación.</strong> El 24 de julio, en el Café Lito de Agraciada y Santa Fe.</span></li>
          <li><b>1919</b><span><strong>Divisional Extra.</strong> Primer título y primer ascenso.</span></li>
          <li><b>1920</b><span><strong>Divisional Intermedia.</strong> Segundo título al hilo y salto a Primera.</span></li>
          <li><b>1921</b><span><strong>Primera División.</strong> Debut en el Campeonato Uruguayo; se mantiene hasta 1928.</span></li>
          <li><b>1932</b><span><strong>Llega el profesionalismo.</strong> Lito sigue amateur y juega en el ascenso.</span></li>
          <li><b>1947</b><span><strong>Se apaga.</strong> Desaparece de la competencia oficial.</span></li>
          <li><b>1952</b><span><strong>La Federación.</strong> Vuelve al amateurismo hasta 1960.</span></li>
          <li><b>2022</b><span><strong>El regreso.</strong> De vuelta en la AUF, en la Divisional D.</span></li>
          <li><b>2023</b><span><strong>Campeón.</strong> Final ganada 2 a 0 y ascenso.</span></li>
        </ul>
      </div>
      <div>
        <p class="cintilla">Palmarés</p>
        <h2>Lo ganado</h2>
        <ul class="cronologia cronologia--compacta">
          <li><b>2023</b><span><strong>Divisional D.</strong> Campeón.</span></li>
          <li><b>2022</b><span><strong>Divisional D.</strong> Campeón de la fase regular.</span></li>
          <li><b>1920</b><span><strong>Divisional Intermedia.</strong> Campeón.</span></li>
          <li><b>1919</b><span><strong>Divisional Extra.</strong> Campeón.</span></li>
        </ul>
        <p class="aviso-formulario" style="margin-top:14px">Más dos campeonatos y dos subcampeonatos en la Federación, entre 1952 y 1960.</p>
        <div class="archivo" style="margin-top:26px">
""" + hueco("Archivo", "3 / 4", "assets/img/historia/archivo-2.jpg", "José Nasazzi en andas después de la final del Mundial de 1930", "José Nasazzi, el «Mariscal». De Lito a capitán del primer campeón del mundo. Uruguay, 1930.") + """
        </div>
      </div>
    </div>
  </div>
</section>
""" + momento("2022", "Volvimos", "Setenta y cinco años después del último partido oficial.", "volvimos") + """
<section class="regreso">
  <div class="regreso-foto" role="presentation"></div>
  <div class="marco regreso-cuerpo">
    <p class="regreso-antetitulo">75 años después</p>
    <p class="regreso-titulo">Lito volvió.</p>
    <ol class="regreso-hitos">
      <li><b>2022</b><span>Regreso a la competición AUF.</span></li>
      <li><b>2023</b><span>Campeón de la Divisional D.</span></li>
      <li><b>2026</b><span>Una nueva etapa.</span></li>
    </ol>
  </div>
</section>

<section class="seccion">
  <div class="marco">
    <div class="rejilla rejilla--2">
      <div>
        <p class="cintilla">Hoy</p>
        <h2>El Lito de ahora</h2>
        <p class="prosa">Primera Divisional C, plantel de primera y formativas trabajando todo el año. La cancha, la tribuna y el domingo volvieron a ser del barrio.</p>
        <div class="acciones">
          <a class="boton" href="plantel.html">Ver el plantel</a>
          <a class="boton boton--fantasma" href="fixture.html">Fixture y tabla</a>
        </div>
      </div>
      <div>
        <p class="cintilla">En números</p>
        <h2>El paso por las divisionales</h2>
        <dl class="datos">
          <div><dt>Primera División</dt><dd>6 temporadas · 1921 a 1928</dd></div>
          <div><dt>Segunda División</dt><dd>12 temporadas · 1920 y 1929 a 1941</dd></div>
          <div><dt>Tercera División</dt><dd>8 temporadas · 1918-1919, 1942-1945 y desde 2024</dd></div>
          <div><dt>Cuarta División</dt><dd>3 temporadas · 1946 y 2022-2023</dd></div>
          <div><dt>Mejor puesto en Primera</dt><dd>Quinto, en 1922 y en 1923</dd></div>
          <div><dt>Registro en Primera</dt><dd>168 partidos: 53 ganados, 50 empatados, 65 perdidos</dd></div>
        </dl>
      </div>
    </div>
  </div>
</section>
""" + momento("2026", "El próximo capítulo", "Una cancha propia en Arroyo Seco y un club que quiere crecer sin dejar de ser del barrio.", "proximo") + """
<section class="lamina">
  <div class="marco claro">
    <div class="rejilla rejilla--2">
      <div>
        <p class="cintilla">Lo que viene</p>
        <h2>El terreno ya existe</h2>
        <p class="prosa">Sobre el predio que el club usa hoy hay un proyecto de cancha, tribunas e instalaciones deportivas para el barrio. Está dibujado, no construido: el capítulo VI lo muestra entero.</p>
        <p><a class="boton boton--oro" href="proyecto.html">Ver el proyecto</a></p>
      </div>
      <div>
        <figure class="hueco">
          <img src="assets/img/proyecto/terreno.jpg" alt="Vista aérea del predio actual del Centro Atlético Lito en Arroyo Seco" loading="lazy">
          <figcaption>El predio hoy, desde el aire.</figcaption>
        </figure>
      </div>
    </div>
  </div>
</section>

<section class="seccion">
  <div class="marco">
    <p class="cintilla">Sede y cancha</p>
    <h2>Dónde late el club</h2>
    <div class="rejilla rejilla--2">
      <dl class="datos">
        <div><dt>Barrio</dt><dd>Arroyo Seco, Montevideo</dd></div>
        <div><dt>Apodo</dt><dd>La azulgrana de Arroyo Seco</dd></div>
        <div><dt>Fundación</dt><dd>24 de julio de 1917</dd></div>
        <div><dt>Categoría</dt><dd>Primera Divisional C</dd></div>
      </dl>
      <dl class="datos">
        <div><dt>Afiliación</dt><dd>Asociación Uruguaya de Fútbol (AUF)</dd></div>
        <div><dt>Dirección</dt><dd>A confirmar</dd></div>
        <div><dt>Cancha</dt><dd>A confirmar</dd></div>
        <div><dt>Presidencia</dt><dd>Rodolfo Neme</dd></div>
      </dl>
    </div>
  </div>
</section>

<section class="seccion">
  <div class="marco">
    <p class="cintilla">Indumentaria</p>
    <h2>La camiseta es el escudo en movimiento</h2>
    <p class="prosa">El conjunto oficial de local: camiseta azul francia con cuello rojo y vivo rojo en las mangas, y pantalón blanco con vivo rojo en el ruedo.</p>
    <figure class="hueco indumentaria">
      <img src="assets/img/fotos/indumentaria.jpg" alt="Lámina del equipo oficial: camiseta azul con cuello y vivos rojos, con pantalón blanco y con pantalón azul, y detalles de cuello, escudo, manga y espalda" width="1536" height="1024" loading="lazy">
      <figcaption>Lámina de referencia del equipo oficial, temporada 2025/26.</figcaption>
    </figure>
    <div class="rejilla rejilla--3" style="margin-top:26px">
      <article class="camiseta">
        <div class="muestra" style="background:#1b3fa8"><i style="background:linear-gradient(180deg,var(--rojo) 0 7%,transparent 7% 26%,var(--rojo) 26% 30%,transparent 30%)"></i></div>
        <div class="rotulo"><h4>Camiseta</h4><p class="detalle">Azul francia · cuello y mangas con vivo rojo</p></div>
      </article>
      <article class="camiseta">
        <div class="muestra" style="background:var(--hueso)"><i style="background:linear-gradient(180deg,transparent 0 84%,var(--rojo) 84% 88%,transparent 88%)"></i></div>
        <div class="rotulo"><h4>Pantalón</h4><p class="detalle">Blanco · vivo rojo en el ruedo</p></div>
      </article>
      <article class="camiseta">
        <div class="muestra" style="background:linear-gradient(180deg,#1b3fa8 0 58%,var(--hueso) 58%)"><i style="background:linear-gradient(180deg,var(--rojo) 0 5%,transparent 5% 16%,var(--rojo) 16% 19%,transparent 19% 92%,var(--rojo) 92% 96%,transparent 96%)"></i></div>
        <div class="rotulo"><h4>Conjunto de local</h4><p class="detalle">Azul y rojo · Nuestra camiseta</p></div>
      </article>
    </div>
  </div>
</section>

<section class="seccion">
  <div class="marco">
    <div class="rejilla rejilla--2">
      <div>
        <p class="cintilla">Institucional</p>
        <h2>Comisión directiva</h2>
        <p class="prosa">La vida institucional también se construye entre socios.</p>
        <dl class="datos">
          <div><dt>Presidencia</dt><dd>Rodolfo Neme</dd></div>
          <div><dt>Vicepresidencia</dt><dd>A confirmar</dd></div>
          <div><dt>Secretaría</dt><dd>A confirmar</dd></div>
          <div><dt>Tesorería</dt><dd>A confirmar</dd></div>
          <div><dt>Vocales</dt><dd>A confirmar</dd></div>
        </dl>
      </div>
      <div>
        <p class="cintilla">Identidad</p>
        <h2>El escudo es la firma del club</h2>
        <p class="prosa">Blasón de cuarteles en rojo y azul, con las iniciales del club, la pelota al centro y el año de fundación al pie. El azul y el rojo vienen de la primera camiseta, la de 1917.</p>
        <div class="rejilla rejilla--4" style="margin-top:18px">
          <div style="background:var(--azul);color:var(--hueso);padding:14px"><span class="mono">Azul Lito</span><br><span class="mono" style="color:var(--oro)">#1C2C6B</span></div>
          <div style="background:var(--rojo);color:var(--hueso);padding:14px"><span class="mono">Rojo Lito</span><br><span class="mono">#D12C3E</span></div>
          <div style="background:var(--hueso-80);color:var(--tinta);padding:14px"><span class="mono">Hueso</span><br><span class="mono">#F4EFE6</span></div>
          <div style="border:1px solid var(--oro);color:var(--tinta);padding:14px"><span class="mono" style="color:var(--oro-80)">Oro Lito</span><br><span class="mono">#D4A85A</span></div>
        </div>
        <p class="aviso-formulario" style="margin-top:14px">Uso de marca y archivos vectoriales: <a href="mailto:marca@calito.uy">marca@calito.uy</a></p>
      </div>
    </div>
  </div>
</section>
""" + himno() + cierre() + folio("I", "El club")


def cap_proyecto():
    return portadilla("VI", "El próximo capítulo", "Una cancha propia en Arroyo Seco. Todavía no está construida: esto es el proyecto.") + """
<section class="seccion">
  <div class="marco">
    <div class="rejilla rejilla--2">
      <div class="prosa">
        <p class="cintilla">El punto de partida</p>
        <h2>Hoy: el lugar donde empieza todo.</h2>
        <p>Lito juega y entrena en Arroyo Seco, sobre un predio que el club viene usando y ordenando. Cancha principal, canchas auxiliares y las instalaciones que sostienen el día a día.</p>
        <p>Sobre ese mismo terreno está dibujado el proyecto de la cancha nueva.</p>
      </div>
      <div>
        <figure class="hueco">
          <img src="assets/img/proyecto/terreno.jpg" alt="Vista aérea del predio actual del club en Arroyo Seco" loading="lazy">
          <figcaption>HOY · Vista aérea del predio actual.</figcaption>
        </figure>
      </div>
    </div>
  </div>
</section>

<section class="lamina proyecto-futuro">
  <div class="marco claro">
    <p class="marbete">Proyecto · no construido</p>
    <p class="cintilla">La cancha que viene</p>
    <h2>Mañana: un lugar para crecer.</h2>
    <p class="prosa">Cancha con tribunas, instalaciones deportivas y espacio abierto para el barrio. Las imágenes que siguen son renders del proyecto: muestran una intención, no una obra terminada ni una fecha.</p>
    <div class="renders renders--principal">
""" + hueco("Render · vista aérea de la cancha", "16 / 9", "assets/img/proyecto/render-1.jpg",
            "Render aéreo del proyecto: la cancha, las tribunas y el barrio, con la bahía de fondo",
            "La cancha y las tribunas, con la bahía de fondo. Una de ellas lleva el nombre de Pedro Cea.") + """
    </div>
    <div class="renders">
""" + hueco("Render · el frente sobre la calle", "16 / 9", "assets/img/proyecto/render-2.jpg",
            "Render del frente del proyecto sobre la calle, con la plaza y el muro del año de fundación",
            "El frente sobre la calle y la plaza de acceso.") + hueco("Render · interior de las instalaciones", "16 / 9", "assets/img/proyecto/render-3.jpg",
            "Render del interior de las instalaciones, con la cancha del otro lado del vidrio",
            "El interior, con la cancha del otro lado del vidrio.") + """
    </div>
  </div>
</section>

<section class="seccion">
  <div class="marco">
    <p class="cintilla">Qué significa</p>
    <h2>Una cancha es una sede</h2>
    <div class="rejilla rejilla--3" style="margin-top:26px">
      <article class="tarjeta tarjeta--borde-oro"><h3>Para el plantel</h3><p>Jugar de local en el barrio, con vestuarios y cancha propios.</p></article>
      <article class="tarjeta tarjeta--borde-oro"><h3>Para las formativas</h3><p>Un lugar fijo donde entrenar todo el año.</p></article>
      <article class="tarjeta tarjeta--borde-oro"><h3>Para el barrio</h3><p>Espacio deportivo abierto en Arroyo Seco.</p></article>
    </div>
    <p class="aviso-formulario" style="margin-top:26px">El proyecto está en desarrollo. Plazos, etapas y financiación se publican acá cuando el club los confirme.</p>
  </div>
</section>

<section class="franja-cierre">
  <div class="marco">
    <div>
      <h2>Bancá el próximo capítulo</h2>
      <p>La cuota social sostiene el club mientras el proyecto avanza.</p>
    </div>
    <a class="boton boton--oro" href="socios.html">Hacete socio</a>
  </div>
</section>
""" + cierre() + folio("VI", "El próximo capítulo")


def cap_plantel():
    return portadilla("II", "Plantel", "Los que llevan nuestra camiseta. Primer equipo, cuerpo técnico y formativas.") + """
<section class="seccion">
  <div class="marco">
    <figure class="plantel-portada">
      <img src="assets/img/galeria/plantel-2.jpg" alt="El primer equipo de Lito antes del partido" width="1500" height="1200" loading="eager">
    </figure>
    <p class="prosa" style="margin-bottom:26px">Primer equipo del Centro Atlético Lito, temporada 2026. Los puestos sin nombre están a confirmar.</p>
    <div data-plantel><p class="cargando">Cargando plantel…</p></div>
  </div>
</section>

<section class="lamina">
  <div class="marco claro">
    <div class="rejilla rejilla--2">
      <div>
        <p class="cintilla">Cuerpo técnico</p>
        <h2>Quién dirige</h2>
        <dl class="datos" data-cuerpo-tecnico><div><dt>Cargando…</dt><dd></dd></div></dl>
      </div>
      <div>
        <figure class="foto-album" style="margin:0;background:rgba(244,239,230,.1)">
          <img src="assets/img/fotos/plantel.jpg" alt="Plantel del Centro Atlético Lito" width="1400" height="1120" loading="lazy">
        </figure>
      </div>
    </div>
  </div>
</section>

<section class="seccion">
  <div class="marco">
    <div class="formativas-fila">
      <div>
        <p class="cintilla">Formativas</p>
        <h2>Las divisiones del club</h2>
        <p class="prosa">Lito trabaja con categorías juveniles todo el año. Para sumarse hay que escribir al club con nombre, edad y categoría.</p>
      </div>
      <img class="mascota" src="assets/img/historia/mascota.png" alt="Mascota del Centro Atlético Lito: un chico de camiseta azulgrana pateando una pelota" loading="lazy">
    </div>
    <div class="rejilla rejilla--3" style="margin-top:26px">
      <article class="tarjeta tarjeta--borde-oro"><h3>Juveniles</h3><p>Consultá al club por categorías y horarios de entrenamiento.</p></article>
      <article class="tarjeta tarjeta--borde-oro"><h3>Baby fútbol</h3><p>Consultá al club por categorías y horarios de entrenamiento.</p></article>
      <article class="tarjeta tarjeta--borde-oro"><h3>Pruebas de jugadores</h3><p>Consultá las próximas convocatorias por <a href="contacto.html">contacto</a>.</p></article>
    </div>
  </div>
</section>
""" + folio("II", "Plantel")


def cap_fixture():
    return portadilla("III", "Fixture y tabla", "Partidos, resultados y posiciones. Se actualiza después de cada fecha.") + """
<section class="seccion">
  <div class="marco">
    <nav class="atajos" aria-label="Secciones deportivas">
      <a href="#proximos">Fixture</a>
      <a href="#tabla">Tabla</a>
      <a href="#resultados">Resultados</a>
    </nav>
    <p class="cintilla">Próximo partido · Primera Divisional C</p>
    <div class="rejilla rejilla--2">
      <div data-partidos="proximo"><p class="cargando">Cargando…</p></div>
      <div>
        <p class="cintilla">Último resultado registrado</p>
        <div data-partidos="ultimo"><p class="cargando">Cargando…</p></div>
      </div>
    </div>
  </div>
</section>

<section class="seccion">
  <div class="marco">
    <p class="cintilla">Próximas fechas</p>
    <div class="lista-partidos" data-partidos="proximos"><p class="cargando">Cargando…</p></div>
  </div>
</section>

<section class="seccion">
  <div class="marco">
    <p class="cintilla">Resultados</p>
    <h2>Últimos partidos</h2>
    <div class="lista-partidos" data-partidos="resultados" style="margin-top:22px"><p class="cargando">Cargando…</p></div>
  </div>
</section>

<section class="seccion" id="tabla">
  <div class="marco">
    <p class="cintilla">Posiciones</p>
    <h2>Tabla</h2>
    <p class="nota" data-aviso-ejemplo hidden style="margin-top:20px">
      Tabla de ejemplo. Cargar las posiciones oficiales antes de publicar.
    </p>
    <div data-tabla="completa" style="margin-top:22px"><p class="cargando">Cargando…</p></div>
  </div>
</section>
""" + folio("III", "Fixture y tabla")


def cap_noticias():
    return portadilla("IV", "Noticias", "Partes de prensa, anuncios y novedades del club.") + """
<section class="seccion">
  <div class="marco">
""" + AVISO_EJEMPLO + """    <div class="rejilla rejilla--3" data-noticias="0" style="margin-top:26px"><p class="cargando">Cargando…</p></div>
  </div>
</section>

<section class="franja-cierre">
  <div class="marco">
    <div>
      <h2>¿Sos prensa?</h2>
      <p>Acreditaciones, fotos y uso de marca: marca@calito.uy</p>
    </div>
    <a class="boton boton--oro" href="contacto.html#prensa">Escribir al club</a>
  </div>
</section>
""" + folio("IV", "Noticias")


def cap_galeria():
    return portadilla("V", "Galería", "El álbum del club: el plantel, los entrenamientos y los domingos de cancha.") + """
<section class="seccion">
  <div class="marco">
    <div data-galeria><p class="cargando">Cargando fotos…</p></div>
""" + AVISO_EJEMPLO + """  </div>
</section>

<section class="lamina">
  <div class="marco claro">
    <p class="cintilla">Mandanos tus fotos</p>
    <h2>El álbum lo hacemos entre todos</h2>
    <p class="prosa">Si tenés fotos del plantel, de un partido o de la hinchada, mandalas y las sumamos al álbum. Pedimos el archivo original, sin filtros ni recortes, y el dato de quién la sacó para dar el crédito.</p>
    <p class="prosa"><a class="boton boton--fantasma" href="mailto:prensa@""" + DOMINIO + """?subject=Fotos%20para%20la%20galer%C3%ADa">Enviar fotos a prensa@""" + DOMINIO + """</a></p>
  </div>
</section>

<dialog class="visor" data-visor>
  <form method="dialog"><button class="visor-cerrar" aria-label="Cerrar">&times;</button></form>
  <figure>
    <img alt="" data-visor-img>
    <figcaption data-visor-pie></figcaption>
  </figure>
</dialog>
""" + folio("V", "Galería")


def cap_socios():
    return portadilla("VII", "Hacete socio", "Ser de Lito es llevar el barrio con vos. Ser socio es ayudar a que esta historia siga.") + """
<section class="lamina estandarte">
  <div class="marco claro estandarte-fila">
    <figure class="estandarte-foto">
      <img src="assets/img/fotos/escudo-camiseta.jpg" alt="El escudo de Lito bordado en la camiseta de juego" width="1120" height="1400" loading="lazy">
    </figure>
    <div class="estandarte-texto">
      <p class="cintilla">El escudo</p>
      <h2 class="estandarte-lema">El escudo no se hereda.<br>Se sostiene.</h2>
      <p class="prosa">La cuota social paga la cancha, los viajes y las formativas, que es lo que hace que esa camiseta salga a jugar cada domingo.</p>
      <p><a class="boton boton--oro" href="#cuotas">Quiero ser parte</a></p>
    </div>
  </div>
</section>

<section class="seccion" id="cuotas">
  <div class="marco">
    <p class="cintilla">Categorías</p>
    <h2>Tu lugar en el club.</h2>
    <p class="prosa">Cada socio ayuda a sostener la camiseta, el fútbol y el encuentro en el barrio.</p>
    <div class="rejilla rejilla--3 pertenencia">
      <article class="tarjeta"><p class="cintilla">01 · Identidad</p><h3>Llevar los colores</h3><p>Ser parte de una historia que empezó en 1917.</p></article>
      <article class="tarjeta"><p class="cintilla">02 · Comunidad</p><h3>Sostener al club</h3><p>Acompañar a quienes hacen posible cada día de cancha.</p></article>
      <article class="tarjeta"><p class="cintilla">03 · Futuro</p><h3>Escribir lo que viene</h3><p>Ayudar a construir el próximo capítulo de Lito.</p></article>
    </div>
    <div class="consulta-cuotas">
      <h3>Categorías, beneficios y cuotas</h3>
      <p>Escribinos para conocer las opciones de asociación y los importes vigentes.</p>
      <a class="boton" href="mailto:socios@""" + DOMINIO + """?subject=Quiero%20ser%20socio%20de%20Lito">Consultar al club ↗</a>
    </div>
  </div>
</section>

<section class="seccion">
  <div class="marco">
    <div class="rejilla rejilla--2">
      <div>
        <p class="cintilla">Alta de socio</p>
        <h2>Sumate</h2>
        <p class="prosa">Dejanos tu consulta en un correo. El club te orienta sobre la categoría, la cuota y los pasos para asociarte.</p>
        <form class="formulario" data-sin-backend="socios@""" + DOMINIO + """">
          <div class="campo"><label for="nombre">Nombre y apellido</label><input id="nombre" name="nombre" type="text" autocomplete="name" required></div>
          <div class="campo-doble">
            <div class="campo"><label for="correo">Correo</label><input id="correo" name="correo" type="email" autocomplete="email" required></div>
            <div class="campo"><label for="telefono">Teléfono</label><input id="telefono" name="telefono" type="tel" autocomplete="tel"></div>
          </div>
          <div class="campo">
            <label for="categoria">Categoría</label>
            <select id="categoria" name="categoria"><option>Quiero conocer las categorías</option></select>
          </div>
          <div class="campo"><label for="mensaje">Comentario</label><textarea id="mensaje" name="mensaje"></textarea></div>
          <button class="boton" type="submit">Preparar correo</button>
          <p class="aviso-formulario">Se abrirá tu aplicación de correo para que revises y envíes el mensaje.</p>
          <p class="aviso-formulario" data-respuesta role="status" hidden></p>
          <p class="aviso-formulario">No incluyas documentos ni datos de pago en tu consulta.</p>
        </form>
      </div>
      <div>
        <figure class="foto-album" style="margin:0">
          <img src="assets/img/galeria/partido-4.jpg" alt="Jugadores de Lito en el abrazo del gol" width="1200" height="1500" loading="lazy">
        </figure>
      </div>
    </div>
  </div>
</section>
""" + folio("VII", "Hacete socio")


def cap_contacto():
    return portadilla("VIII", "Contacto", "Sede, prensa, formativas y uso de marca. Escribinos y te respondemos.") + """
<section class="seccion">
  <div class="marco">
    <div class="rejilla rejilla--2">
      <div>
        <p class="cintilla">Datos</p>
        <h2>Dónde encontrarnos</h2>
        <dl class="datos">
          <div><dt>Sede</dt><dd>Arroyo Seco, Montevideo, Uruguay<br><span class="mono">Dirección exacta a confirmar</span></dd></div>
          <div><dt>Correo</dt><dd><a href="mailto:marca@calito.uy">marca@calito.uy</a></dd></div>
          <div><dt>Teléfono</dt><dd>A confirmar</dd></div>
          <div><dt>Instagram</dt><dd><a href="https://instagram.com/centroatleticolito" rel="noopener">@centroatleticolito</a></dd></div>
          <div><dt>Facebook</dt><dd><a href="https://www.facebook.com/groups/707943076074966" rel="noopener">Grupo del club</a></dd></div>
          <div><dt>Horario de sede</dt><dd>A confirmar</dd></div>
        </dl>

        <div id="prensa" style="margin-top:36px">
          <p class="cintilla">Prensa y marca</p>
          <h3>Acreditaciones y archivos</h3>
          <p class="prosa">Para acreditaciones de prensa, fotos institucionales, archivos vectoriales del escudo o autorizaciones de uso de marca: <a href="mailto:marca@calito.uy">marca@calito.uy</a>.</p>
          <p class="aviso-formulario">El escudo no se estira, no se rota y no cambia de color fuera de paleta. Manual de marca, edición 2026.</p>
        </div>
      </div>
      <div>
        <p class="cintilla">Formulario</p>
        <h2>Escribinos</h2>
        <form class="formulario" data-sin-backend="marca@calito.uy">
          <div class="campo"><label for="c-nombre">Nombre</label><input id="c-nombre" name="nombre" type="text" autocomplete="name" required></div>
          <div class="campo"><label for="c-correo">Correo</label><input id="c-correo" name="correo" type="email" autocomplete="email" required></div>
          <div class="campo">
            <label for="c-motivo">Motivo</label>
            <select id="c-motivo" name="motivo"><option>Consulta general</option><option>Socios</option><option>Formativas</option><option>Prensa</option><option>Sponsors</option></select>
          </div>
          <div class="campo"><label for="c-mensaje">Mensaje</label><textarea id="c-mensaje" name="mensaje" required></textarea></div>
          <button class="boton" type="submit">Preparar correo</button>
          <p class="aviso-formulario">Se abrirá tu aplicación de correo para que revises y envíes el mensaje.</p>
          <p class="aviso-formulario" data-respuesta hidden></p>
        </form>
      </div>
    </div>
  </div>
</section>
""" + folio("VIII", "Contacto")


CUERPOS = {
    "club.html": cap_club,
    "plantel.html": cap_plantel,
    "fixture.html": cap_fixture,
    "noticias.html": cap_noticias,
    "galeria.html": cap_galeria,
    "proyecto.html": cap_proyecto,
    "socios.html": cap_socios,
    "contacto.html": cap_contacto,
}

DESCRIPCIONES = {
    "club.html": "Historia, sede, camiseta y comisión directiva del Centro Atlético Lito, fundado en 1917 en Montevideo.",
    "plantel.html": "Plantel y cuerpo técnico del Centro Atlético Lito, temporada 2026.",
    "fixture.html": "Próximos partidos, resultados y tabla de posiciones del Centro Atlético Lito.",
    "noticias.html": "Noticias, partes de prensa y anuncios del Centro Atlético Lito.",
    "galeria.html": "Fotos del plantel y de los partidos del Centro Atlético Lito.",
    "proyecto.html": "El proyecto de cancha e instalaciones del Centro Atlético Lito en Arroyo Seco.",
    "socios.html": "Categorías de socio, cuotas y alta en el Centro Atlético Lito.",
    "contacto.html": "Datos de contacto, prensa y uso de marca del Centro Atlético Lito.",
}


def main():
    mapa = json.load(open(os.path.join(BASE, "data", "i18n-en.json"), encoding="utf-8"))
    mapa.pop("_nota", None)

    paginas = {}

    # Portada: la tapa. Sin cornisa ni colofón, para no romper la ilusión.
    paginas["index.html"] = (
        encabezado_html("El libro del club", "Sitio oficial del Centro Atlético Lito: historia, plantel, fixture, noticias y socios. Montevideo, desde 1917.", "")
        + pagina_portada()
        + '\n</main>\n<script src="assets/js/main.js"></script>\n</body>\n</html>\n'
    )

    for archivo, titulo, _romano, _apunte in CAPITULOS:
        paginas[archivo] = (
            encabezado_html(titulo, DESCRIPCIONES[archivo], archivo)
            + cabecera_hoja(archivo)
            + CUERPOS[archivo]()
            + colofon()
        )

    carpeta_en = os.path.join(BASE, "en")
    os.makedirs(carpeta_en, exist_ok=True)
    faltantes = []

    for archivo, html in paginas.items():
        with open(os.path.join(BASE, archivo), "w", encoding="utf-8") as f:
            f.write(html)

        ingles, faltan = a_ingles(html, mapa)
        # El toggle apunta al mismo capítulo en el otro idioma.
        ingles = ingles.replace(f'href="en/{archivo}"', f'href="../{archivo}"')
        ingles = ingles.replace('href="en/index.html"', 'href="../index.html"')
        ingles = ingles.replace(">EN<", ">ES<").replace(">English<", ">Español<")
        ingles = ingles.replace('aria-label="Read this page in English"', 'aria-label="Leer esta página en español"')
        # La canónica y la og:url de la versión inglesa apuntan a /en/; los
        # alternate hreflang, en cambio, siguen nombrando a las dos.
        propia = f"{SITIO_URL}/{archivo}"
        propia_en = f"{SITIO_URL}/en/{archivo}"
        ingles = ingles.replace(f'<link rel="canonical" href="{propia}">', f'<link rel="canonical" href="{propia_en}">')
        ingles = ingles.replace(f'<meta property="og:url" content="{propia}">', f'<meta property="og:url" content="{propia_en}">')
        with open(os.path.join(carpeta_en, archivo), "w", encoding="utf-8") as f:
            f.write(ingles)
        faltantes += faltan
        print("escrito", archivo, "+ en/" + archivo)

    # Aviso, no error: el sitio se genera igual, pero conviene saber qué quedó
    # en español dentro de la versión en inglés.
    pendientes = sorted({f for f in faltantes})
    if pendientes:
        print(f"\n{len(pendientes)} frases sin traducir en data/i18n-en.json:")
        for f in pendientes:
            print("  ·", f[:100])


if __name__ == "__main__":
    main()
