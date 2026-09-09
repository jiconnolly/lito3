# El libro del club — Centro Atlético Lito

Sitio estático, sin build de Node ni dependencias. Se publica tal cual desde
GitHub Pages y más adelante puede migrar a Cloudflare Workers.

La web está armada como un **tomo encuadernado de 1917**, apoyado sobre la barra
del bar donde nació el club. Al tocar el escudo la toma se acerca, se endereza y
el libro se abre sobre el índice de capítulos. Todo es CSS 3D, no video: el
escudo es el PNG del manual y nunca se deforma, como exige el capítulo 07 del
brandbook.

Identidad visual según el **Manual de Marca, edición 2026 (v1.0)**: paleta,
tipografías y tono de voz salen de ahí. El hueso del manual (#F4EFE6) hace de
papel y el azul profundo de cuero. La única adición al sistema tipográfico es
**EB Garamond**, para la prosa larga; los datos, tablas y formularios siguen en
Manrope, y los titulares en Oswald, como manda el manual.

## Estructura

```
index.html          La tapa: escudo, apertura del libro e índice de capítulos
club.html           Capítulo I — historia, sede, camiseta, comisión, identidad
plantel.html        Capítulo II — plantel, cuerpo técnico y formativas
fixture.html        Capítulo III — partidos, resultados y tabla
noticias.html       Capítulo IV — listado de noticias
galeria.html        Capítulo V — álbum de fotos del plantel y los partidos
proyecto.html       Capítulo VI — el proyecto de cancha e instalaciones
socios.html         Capítulo VII — cuotas y alta de socio
contacto.html       Capítulo VIII — contacto, prensa y uso de marca

assets/css/main.css Hoja de estilos única
assets/js/main.js   Apertura del libro, menú, partidos, tabla, plantel, noticias y galería
assets/img/         Escudo, favicon, imagen para redes y fotos
assets/img/texturas Fondo de la portada, cuero de la tapa y papel de las hojas
assets/img/marcas   AUF y sponsors, al pie del índice
assets/img/galeria  Las fotos del álbum
assets/img/historia Archivo y retratos históricos
assets/img/proyecto El predio actual y los tres renders del proyecto
data/*.json         Datos editables
worker/api.js       Worker de Cloudflare (todavía sin publicar)
build.py            Regenera las nueve páginas desde plantillas compartidas
```

Las páginas comparten cabecera y pie. **Para cambiar el menú, el pie, los textos
o los metadatos hay que editar `build.py` y correr `python3 build.py`**, no los
HTML sueltos: el script los sobreescribe.

## Actualizar datos

| Qué | Dónde |
| --- | --- |
| Tabla de posiciones | `data/tabla.json` |
| Próximos partidos y resultados | `data/partidos.json` |
| Plantel y cuerpo técnico | `data/plantel.json` — los jugadores sin `nombre` se muestran como "a confirmar" |
| Noticias | `data/noticias.json` |
| Galería | `data/fotos.json` — ver más abajo |

Los archivos con `"ejemplo": true` muestran un aviso visible en el sitio
("datos de ejemplo"). Al cargar la información real hay que sacar esa clave.

## Los huecos: fotos que todavía no existen

Varios bloques tienen un lugar reservado para una foto que el club todavía no
mandó: el barrio, los retratos de Castro y Cea, los dos escudos históricos, los
renders del proyecto. Todos usan la misma función de `build.py`:

```python
hueco("Retrato · Pedro Cea", "4 / 5")                       # marco vacío
hueco("Retrato · Pedro Cea", "4 / 5",
      "assets/img/historia/cea.jpg", "Retrato de Pedro Cea")  # ya con la foto
```

Sin archivo dibuja un marco discreto con el rótulo de lo que va ahí. Para
cargar la foto se deja el archivo en `assets/img/` y se le pasa la ruta como
tercer argumento al mismo llamado: no hay que tocar nada del marcado alrededor.
La proporción es la del marco vacío; cuando la foto está, manda la foto.

## Sumar una foto al álbum

Dos pasos, sin tocar HTML:

1. Dejar el archivo en `assets/img/galeria/`. Conviene JPG apaisado, más o
   menos 1600 px de ancho, bien comprimido: la grilla lo recorta a 3:2 y el
   visor lo muestra grande, así que archivos de más de 400 kB sólo hacen lenta
   la página.
2. Agregar la entrada en el grupo que corresponda de `data/fotos.json`:

```json
{ "archivo": "assets/img/galeria/partido-4.jpg",
  "pie": "Lito 2 – Albion 1",
  "fecha": "2026-09-14",
  "foco": "50% 80%" }
```

`pie` es lo que se lee debajo de la foto y también el texto alternativo, así
que conviene que describa la escena. `fecha` va en formato `AAAA-MM-DD` y se
puede dejar vacía (`""`) si no se sabe. El orden de las fotos dentro del grupo
es el orden del archivo: la primera de la lista es la primera del álbum.

`foco` es opcional. La grilla recorta cada foto a 4:3, y en una vertical eso
puede comerse las cabezas o los pies: con `foco` se elige qué parte se
conserva (`"50% 88%"` baja el encuadre, `"50% 20%"` lo sube). El visor siempre
muestra la foto entera, sin recortar.

Los grupos que están son **Plantel** y **Partidos**; para abrir uno nuevo
(por ejemplo "Formativas" o "Hinchada") se agrega otro objeto con `titulo`,
`bajada` y `fotos`. Un grupo sin fotos no se dibuja.

El grupo **Partidos** está vacío a la espera de fotos: un grupo sin fotos no se
dibuja, así que la sección no muestra un hueco.

## La vista previa al compartir el link

Las redes no leen el sitio cada vez: guardan una copia de la imagen y el título
la primera vez que alguien pega el link, y se quedan con eso. Por eso, después
de cambiar el escudo o `assets/img/og.png`, hay que **subir en uno el `V` de
`build.py`** y volver a correrlo: eso cambia la URL de la imagen
(`og.png?v=3`) y obliga a WhatsApp, X y compañía a buscarla de nuevo. Sin eso
se sigue viendo el logo viejo aunque el archivo esté cambiado.

`SITIO_URL` también vive en `build.py` y tiene que ser la dirección real del
sitio: las redes exigen URL absoluta en `og:image` y con ruta relativa muchas
no muestran nada. Hoy apunta a GitHub Pages; el día que `calito.uy` apunte al
sitio hay que cambiarlo ahí.

Para forzar el refresco a mano:

- Facebook, Instagram y **WhatsApp** comparten caché:
  <https://developers.facebook.com/tools/debug/> → pegar el link → *Scrape Again*.
- X: <https://cards-dev.twitter.com/validator>.
- LinkedIn: <https://www.linkedin.com/post-inspector/>.

Ojo: mientras `NOINDEX` esté en `True` hay plataformas (LinkedIn, Slack) que
directamente no arman la vista previa.

## El arco narrativo

El capítulo I está ordenado en cuatro momentos —1917 nacimos, 1921 hicimos
historia, 2022 volvimos, 2026 el próximo capítulo— y el riel de arriba del
capítulo es el índice de ese relato. Los cuatro se generan con `momento()`, así
que agregar o cambiar uno es una línea.

"El próximo capítulo" es la idea que ata el regreso del club, el Lito de hoy y
el proyecto de cancha. Aparece como capítulo VI, como último momento del
capítulo I y en el cierre del libro; no conviene repetirla más que eso.

El cierre (`cierre()`) es la última página del libro y va sólo en los dos
capítulos que cierran el arco: I y VI. Si se pone en todos, deja de significar.

## Antes de publicar

- [ ] Reemplazar las fotos de `assets/img/fotos/` que siguen siendo placeholders (sede, hinchada, noticias).
- [ ] Cargar fotos de partidos en el grupo "Partidos" de `data/fotos.json`.
- [ ] Confirmar el pie de `assets/img/historia/archivo-1.jpg` (la jugada).
- [ ] Cargar cuatro fotos reales de Arroyo Seco (nada de banco de imágenes).
- [ ] Cargar dirección de la sede, cancha, teléfono y horarios en `build.py`
      (páginas `club.html` y `contacto.html`). El manual de marca indica
      Av. Carlos María Ramírez s/n — confirmar cuál corresponde.
- [ ] Cargar la comisión directiva y los hitos de la historia.
- [ ] Confirmar los importes de las cuotas con tesorería.
- [ ] Cargar plantel, fixture y tabla reales; sacar `"ejemplo": true`.
- [ ] Confirmar los usuarios de Instagram, X y Facebook del pie.
- [ ] Poner `NOINDEX = False` en `build.py` y regenerar: hasta entonces todas
      las páginas van con `noindex, nofollow`.

## Formularios

Los formularios de socios y contacto todavía no envían nada: muestran un aviso
con la dirección de correo. Para activarlos hay que publicar el Worker.

## Pasar a datos en vivo y formularios reales

1. `wrangler kv namespace create DATOS` y `wrangler kv namespace create ENVIOS`
2. `wrangler deploy` con `worker/api.js`
3. En `assets/js/main.js`, poner `ORIGEN_VIVO = '/api'`

El Worker sirve `tabla` y `partidos` desde KV y guarda los envíos de los
formularios, sin exponer claves ni correos en el HTML.

## La apertura del libro

La tapa se abre con `transform: rotateY()`. Detalles que conviene no romper:

- **El estado por defecto es "abierto".** Sin JavaScript, con
  `prefers-reduced-motion` o si falla algo, el índice se lee igual. El JS agrega
  la clase `cerrado` para armar la ceremonia.
- **Cerrado en cada visita.** Cada vez que se entra a la portada el libro
  aparece cerrado.
- **Sin carteles.** La portada no lleva ninguna indicación escrita: toda la
  escena abre el libro con un toque, en cualquier punto. La tapa sigue siendo un
  `<button>` con su etiqueta accesible, así que con teclado se llega con Tab y
  se abre con Enter.
- **Dos tiempos.** Primero el libro se endereza (1,05 s) y recién después gira
  la tapa (1,4 s, con 0,62 s de espera). Si se tocan esos tiempos en el CSS hay
  que mantener la espera de la tapa por encima de la duración del enderezado, o
  la tapa se abre mientras el libro todavía está de costado.
- **Es la cámara la que se mueve, no el libro.** Todo lo que se ve —el plano del
  fondo y el libro— vive dentro de `.camara`. Si se anima el libro por separado,
  el ojo lo lee como un objeto flotando sobre una postal.
- **Profundidad.** El fondo está en `translateZ(-520px)` con la escala que
  compensa la perspectiva a esa distancia: por eso el libro crece más rápido que
  el fondo al acercarse la toma. La sombra de contacto vive apenas detrás del
  libro (`translateZ(-12px)`).
- **Nada decorativo intercepta clicks.** Las caras del tomo y la hoja que se da
  vuelta llevan `pointer-events: none`, y el índice no lleva `translateZ`
  negativo: si se corre hacia atrás queda detrás del propio contenedor y sus
  enlaces dejan de recibir clicks.
- **El pasaje al capítulo.** Al elegir un capítulo se pasa una hoja, la cámara
  entra y un velo del color del papel toma la pantalla; el capítulo arranca con
  un fundido desde ese mismo color, así la costura entre las dos páginas no se
  ve. Si se cambia `--papel` hay que mirar que las dos puntas sigan coincidiendo.
- **El tomo tiene cuerpo.** `.cara-lomo`, `.cara-cabeza` y `.cara-canto` son
  caras reales rotadas 90°, y `--grosor` define el espesor. Al girar la toma se
  ve el canto de las hojas; el lomo con sus nervios queda del lado opuesto.
- **El índice son enlaces reales**, no botones de JavaScript: funcionan con
  teclado, con el buscador y con el botón "atrás".

## La guarda con la canción

La letra de la canción oficial va en la contracara de la tapa (`.cara-dorso`),
que es la página izquierda cuando el libro se abre. Dos cosas la sostienen:

- **La tapa no es un `<button>`.** La canción es contenido, y dentro de un
  control quedaría como parte del nombre accesible del botón, además de tapada
  por el `aria-hidden` que llevaba al abrirse. El teclado se resuelve con
  `.abrir-libro`, un botón que sólo aparece al enfocarlo.
- **En pantalla angosta manda el índice.** Las dos páginas del pliego no entran
  en un teléfono sin achicar la tipografía por debajo de lo legible, así que
  bajo 760 px la cámara vuelve a centrar el índice y la guarda queda fuera de
  cuadro. Si la canción tiene que leerse en el celular, hay que darle un segundo
  lugar en el capítulo del club.

## Las marcas del índice

Los logos del pie del índice (`assets/img/marcas/`) van **sobre fondo blanco a
propósito**, no recortados: se aplican con `mix-blend-mode: multiply`, así el
blanco desaparece y el papel se ve a través. Quedan impresos en la hoja en vez
de pegados encima, y el escudo de la AUF conserva sus blancos internos, que un
recorte por transparencia le comería.

Dos cosas que rompen esto y no son obvias:

- **Nunca poner `opacity` en `.marcas`.** El contenedor con opacidad aísla el
  grupo y anula el `mix-blend-mode` de los hijos: los logos vuelven a aparecer
  con su recuadro blanco. La opacidad va en cada `img`.
- **Un logo con transparencia hay que aplanarlo sobre blanco**, no convertirlo
  y listo: al pasar de RGBA a RGB sin componer, el fondo transparente se vuelve
  negro y el logo termina como un rectángulo oscuro.

## Las texturas

Tres fotografías sostienen la escena. Se cambian reemplazando el archivo, sin
tocar el CSS:

| Archivo | Dónde se usa | Cómo conviene que sea |
| --- | --- | --- |
| `fondo.jpg` | Fondo de la portada | Apaisada y oscura en los bordes, con una superficie clara donde apoyar el libro |
| `tapa.jpg` | Tapa y contratapa | Cuero fotografiado de frente, con su filete impreso. El escudo y las letras se componen encima en CSS |
| `lomo.jpg` | Lomo del tomo | Lomo con nervios, de frente y vertical; se recorta a `cover` sobre una cara de 58 px |
| `cuero.jpg` | (sin uso hoy) | Quedó de la etapa anterior; el troquel del escudo ya toma su grano de `tapa.jpg` |
| `papel.jpg` | Hojas y guarda | **Tiene que repetir sin costura**: se repite en mosaico de 520 px |

El papel del repositorio es un mosaico espejado y llevado al hueso del manual
(`#F4EFE6`), para que la trama no cante y el color siga siendo el de la marca.
Si se reemplaza por una foto cruda, el mosaico se va a notar.

**El filete de la tapa es rojo, y no venía así.** La fotografía original tenía
el filete dorado; se lo pasó a rojo Lito por matiz: se toma la máscara de los
amarillos con saturación (matiz 33°–68°, S > .26, V > .30), se les fija el
matiz del rojo del manual y se les conserva el valor, para que el gastado y los
raspones del oro original sigan leyéndose en el rojo. Las esquinas peladas del
cuero quedan fuera de la máscara por ser más anaranjadas y menos saturadas. Si
se cambia la foto de tapa hay que rehacer esa conversión.

**La tapa trae su propio filete.** Por eso `.cara-frente` no dibuja
ningún marco y el contenido va con `padding: 13% 14% 12.5%`, que es lo que lo
mantiene dentro del filete de la foto. Si se cambia la foto de tapa hay que
volver a medir ese padding contra el nuevo marco.

## Reglas de marca que el sitio respeta

- El escudo no se estira, no se rota, no cambia de color ni lleva efectos.
- Área de protección: una unidad X (1/12 del ancho) libre alrededor del escudo.
- Tamaño mínimo en pantalla: 32 px (16 px para favicon).
- Paleta: azul `#1C2C6B`, rojo `#D12C3E`, oro `#D4A85A`, hueso `#F4EFE6`.
  Proporción de referencia: 55 azul · 25 hueso · 12 rojo · 8 oro.
- Tipografías: Oswald (display), Manrope (texto), JetBrains Mono (etiquetas).
- Tono: frases cortas, una idea por pieza, datos al pie en mono, sin emoji.

Consultas de marca y archivos vectoriales: marca@calito.uy

## Ver el sitio localmente

```
python3 -m http.server 8000
```

Y abrir http://localhost:8000
