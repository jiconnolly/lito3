/* ============================================================
   CENTRO ATLÉTICO LITO — comportamiento del sitio
   ============================================================ */

/* Origen de datos.
   Vacío = los JSON estáticos de /data (GitHub Pages).
   Cuando el Worker de Cloudflare esté publicado, poner acá su base
   (por ejemplo '/api') y el sitio pasa a datos en vivo sin tocar el HTML. */
/* ---------- Idioma ----------
   Las páginas en inglés viven en /en/ y sólo se distinguen por <html lang>.
   Los textos que escribe el JavaScript no pasan por el traductor de build.py,
   así que viven acá. */

const IDIOMA = (document.documentElement.lang || 'es').slice(0, 2) === 'en' ? 'en' : 'es';
/* En /en/ los datos están un nivel más arriba. */
const RAIZ = IDIOMA === 'en' ? '../' : '';

const TEXTOS = {
  es: {
    meses: ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'set', 'oct', 'nov', 'dic'],
    dias: ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado'],
    falla: que => `No se pudieron cargar ${que}. Recargá la página.`,
    partidos: 'los partidos', posiciones: 'las posiciones', plantel: 'el plantel',
    noticias: 'las noticias', fotos: 'las fotos',
    sinPartidos: 'Sin partidos programados.',
    aConfirmar: 'A confirmar', fichaPendiente: 'Ficha pendiente', horaAConfirmar: 'a confirmar',
    club: 'Club', sinFotos: 'Todavía no hay fotos cargadas en el álbum.',
    gano: 'Ganó', empato: 'Empató', perdio: 'Perdió',
    puestos: { Arqueros: 'Arqueros', Defensas: 'Defensas', Mediocampistas: 'Mediocampistas', Delanteros: 'Delanteros' },
    tablaCorta: ['#', 'Equipo', 'PJ', 'DG', 'Pts'],
    tablaLarga: ['#', 'Equipo', 'PJ', 'G', 'E', 'P', 'GF', 'GC', 'DG', 'Pts', 'Últimos 5'],
    fecha: 'fecha', actualizado: 'actualizado', fuente: 'fuente',
    asuntoSocio: 'Quiero ser socio de Lito',
    asuntoConsulta: 'Consulta al Centro Atlético Lito',
    correoListo: (enlace, correo) => `Tu mensaje está preparado. Revisalo y envialo desde tu aplicación de correo. Si no se abrió, <a href="${enlace}">abrí el correo acá</a> o escribí a ${correo}.`
  },
  en: {
    meses: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
    dias: ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
    falla: que => `Could not load ${que}. Please reload the page.`,
    partidos: 'the matches', posiciones: 'the standings', plantel: 'the squad',
    noticias: 'the news', fotos: 'the photographs',
    sinPartidos: 'No matches scheduled.',
    aConfirmar: 'To be confirmed', fichaPendiente: 'Details pending', horaAConfirmar: 'time to be confirmed',
    club: 'Club', sinFotos: 'No photographs in the album yet.',
    gano: 'Won', empato: 'Drew', perdio: 'Lost',
    puestos: { Arqueros: 'Goalkeepers', Defensas: 'Defenders', Mediocampistas: 'Midfielders', Delanteros: 'Forwards' },
    tablaCorta: ['#', 'Team', 'P', 'GD', 'Pts'],
    tablaLarga: ['#', 'Team', 'P', 'W', 'D', 'L', 'GF', 'GA', 'GD', 'Pts', 'Last 5'],
    fecha: 'round', actualizado: 'updated', fuente: 'source',
    asuntoSocio: 'I want to join Lito',
    asuntoConsulta: 'Enquiry to Centro Atlético Lito',
    correoListo: (enlace, correo) => `Your message is ready. Check it and send it from your email app. If it did not open, <a href="${enlace}">open the email here</a> or write to ${correo}.`
  }
};

const T = TEXTOS[IDIOMA];

/* Las etapas de un torneo son vocabulario, no nombres propios: se traducen.
   Lo que no está en la tabla pasa tal cual, que es lo correcto para el nombre
   de la competencia. */
const ETAPAS_EN = {
  'Fase regular': 'Regular season',
  'Zona de grupos': 'Group stage',
  'Torneo Final': 'Final tournament',
  'Torneo Inicial': 'Opening tournament',
  'Semifinal': 'Semi-final',
  'Final': 'Final',
  'Cuartos de final': 'Quarter-final',
  'Octavos de final': 'Round of 16'
};

function termino(texto) {
  if (IDIOMA !== 'en' || !texto) return texto || '';
  return String(texto)
    .split(' · ')
    .map(parte => ETAPAS_EN[parte] || parte.replace(/^Fecha (\d+)$/, 'Round $1'))
    .join(' · ');
}

const ORIGEN_VIVO = '';

const RUTAS = {
  tabla:    ORIGEN_VIVO ? ORIGEN_VIVO + '/tabla'    : RAIZ + 'data/tabla.json',
  partidos: ORIGEN_VIVO ? ORIGEN_VIVO + '/partidos' : RAIZ + 'data/partidos.json',
  plantel:  RAIZ + 'data/plantel.json',
  noticias: RAIZ + 'data/noticias.json',
  fotos:    RAIZ + 'data/fotos.json'
};

const CLUB = 'Lito';
const MESES = T.meses;
const DIAS = T.dias;

function leerFecha(iso) {
  const [a, m, d] = String(iso).split('-').map(Number);
  return new Date(a, m - 1, d);
}

function fechaCorta(iso) {
  const f = leerFecha(iso);
  return `${String(f.getDate()).padStart(2, '0')} ${MESES[f.getMonth()]} ${f.getFullYear()}`;
}

function fechaLarga(iso) {
  const f = leerFecha(iso);
  return IDIOMA === 'en'
    ? `${DIAS[f.getDay()]} ${f.getDate()} ${MESES[f.getMonth()]}`
    : `${DIAS[f.getDay()]} ${f.getDate()} de ${MESES[f.getMonth()]}`;
}

function esc(t) {
  return String(t == null ? '' : t).replace(/[&<>"']/g, c => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

async function traer(ruta) {
  const r = await fetch(ruta, { cache: 'no-store' });
  if (!r.ok) throw new Error('No se pudo leer ' + ruta);
  return r.json();
}

function falla(destino, que) {
  destino.innerHTML = `<p class="error-datos">${esc(T.falla(que))}</p>`;
}

/* ---------- Menú ---------- */

function menu() {
  const boton = document.querySelector('.menu-boton');
  const lista = document.querySelector('.menu');
  if (!boton || !lista) return;
  boton.addEventListener('click', () => {
    const abierto = lista.classList.toggle('abierto');
    boton.setAttribute('aria-expanded', String(abierto));
  });
}

/* ---------- La tapa del libro ----------
   Por defecto el libro está abierto: así se lee sin JS y con
   prefers-reduced-motion. Con JS y movimiento permitido, el libro aparece
   cerrado y perfilado cada vez que se entra a la portada. */
function libro() {
  const tomo = document.querySelector('[data-libro]');
  if (!tomo) return;

  const escena = tomo.closest('.escena');
  const camara = escena && escena.querySelector('[data-camara]');
  const quieto = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!quieto) {
    tomo.classList.add('cerrado');
    if (escena) escena.classList.add('lejos');
    if (camara) camara.classList.add('lejos');
  }

  const boton = escena && escena.querySelector('.abrir-libro');
  const guardarBoton = () => { if (boton) boton.hidden = true; };

  const abrir = () => {
    if (!tomo.classList.contains('cerrado')) return;
    tomo.classList.remove('cerrado');
    if (escena) escena.classList.remove('lejos');
    if (camara) camara.classList.remove('lejos');
    guardarBoton();
    const primero = tomo.querySelector('.indice a');
    if (primero) setTimeout(() => primero.focus({ preventScroll: true }), 2600);
  };

  tomo.querySelectorAll('[data-abrir]').forEach(b => b.addEventListener('click', abrir));
  // La escena entera abre el libro: el cartel de "tocá acá" sobraba.
  if (escena) escena.addEventListener('click', abrir);

  // Al elegir un capítulo, se pasa la hoja antes de ir a la página.
  if (escena && !quieto) {
    tomo.querySelectorAll('.indice a').forEach(a => {
      a.addEventListener('click', ev => {
        if (ev.button !== 0 || ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey) return;
        ev.preventDefault();
        escena.classList.add('pasando');
        setTimeout(() => { window.location.href = a.getAttribute('href'); }, 640);
      });
    });
  }

  // Al volver con el botón "atrás", la portada no debe quedar en pleno pasaje.
  window.addEventListener('pageshow', () => {
    if (escena) escena.classList.remove('pasando');
  });
  if (!tomo.classList.contains('cerrado')) guardarBoton();
}

/* ---------- Aviso de datos de ejemplo ---------- */

function avisoEjemplo(d) {
  if (!d.ejemplo) return;
  document.querySelectorAll('[data-aviso-ejemplo]').forEach(n => { n.hidden = false; });
}

/* ---------- Próximo partido y resultados ---------- */

function tarjetaPartido(p, claseExtra) {
  const marcador = p.golesLocal != null
    ? `<span class="partido-marcador">${p.golesLocal}–${p.golesVisitante}</span>`
    : '<span class="partido-vs">VS</span>';
  const pie = [
    p.hora ? `${fechaLarga(p.fecha)} · ${p.hora}` : fechaLarga(p.fecha),
    p.cancha || '',
    p.detalle || ''
  ].filter(Boolean).join(' · ');

  return `<article class="partido ${claseExtra || ''}">
      <p class="competencia">${esc(termino(p.competencia))}</p>
      <div class="partido-equipos">
        <span class="partido-equipo">${esc(p.local)}</span>
        ${marcador}
        <span class="partido-equipo der">${esc(p.visitante)}</span>
      </div>
      <p class="partido-pie">${esc(pie)}</p>
    </article>`;
}

async function partidos() {
  const destinos = document.querySelectorAll('[data-partidos]');
  if (!destinos.length) return;
  let d;
  try {
    d = await traer(RUTAS.partidos);
  } catch (e) {
    destinos.forEach(x => falla(x, T.partidos));
    return;
  }

  avisoEjemplo(d);

  destinos.forEach(destino => {
    const modo = destino.dataset.partidos;

    if (modo === 'proximo') {
      const p = d.proximos && d.proximos[0];
      destino.innerHTML = p
        ? tarjetaPartido(p)
        : `<p class="cargando">${T.sinPartidos}</p>`;
      return;
    }

    if (modo === 'ultimo') {
      destino.innerHTML = d.ultimo
        ? tarjetaPartido(d.ultimo, 'partido--hueso')
        : '<p class="cargando">Sin resultados cargados.</p>';
      return;
    }

    if (modo === 'proximos') {
      destino.innerHTML = (d.proximos || []).map(p => `
        <article class="fila-partido ${p.condicion === 'local' ? 'local' : ''}">
          <p class="fecha">${esc(fechaCorta(p.fecha))}<br>${esc(p.hora || T.horaAConfirmar)}</p>
          <p class="cruce">${esc(p.local)} <span class="partido-vs">vs</span> ${esc(p.visitante)}</p>
          <p class="dato">${esc(termino(p.competencia))}<br>${esc(p.cancha || '')}</p>
        </article>`).join('') || `<p class="cargando">${T.sinPartidos}</p>`;
      return;
    }

    if (modo === 'resultados') {
      destino.innerHTML = (d.resultados || []).map(p => {
        const nuestro = p.local === CLUB ? p.golesLocal - p.golesVisitante : p.golesVisitante - p.golesLocal;
        const signo = nuestro > 0 ? 'G' : nuestro === 0 ? 'E' : 'P';
        return `<article class="fila-partido">
          <p class="fecha">${esc(fechaCorta(p.fecha))}<br>${esc(termino(p.competencia))}</p>
          <p class="cruce">${esc(p.local)} <span class="partido-vs">${p.golesLocal}–${p.golesVisitante}</span> ${esc(p.visitante)}</p>
          <p class="dato"><span class="forma"><i class="${signo}">${signo}</i></span></p>
        </article>`;
      }).join('') || '<p class="cargando">Sin resultados cargados.</p>';
    }
  });
}

/* ---------- Tabla de posiciones ---------- */

function filaTabla(e, resumida) {
  const forma = (e.forma || []).map(r =>
    `<i class="${r}" title="${r === 'G' ? T.gano : r === 'E' ? T.empato : T.perdio}">${r}</i>`).join('');
  const largas = resumida ? '' :
    `<td>${e.g}</td><td>${e.e}</td><td>${e.p}</td><td>${e.gf}</td><td>${e.gc}</td>`;

  return `<tr class="${e.esNosotros ? 'fila-nuestra' : ''}">
      <td>${e.pos}</td>
      <td>${esc(e.equipo)}</td>
      <td>${e.pj}</td>${largas}
      <td>${e.dg > 0 ? '+' : ''}${e.dg}</td>
      <td class="pts">${e.pts}</td>
      ${resumida ? '' : `<td><span class="forma">${forma}</span></td>`}
    </tr>`;
}

async function tabla() {
  const destinos = document.querySelectorAll('[data-tabla]');
  if (!destinos.length) return;

  let d;
  try {
    d = await traer(RUTAS.tabla);
  } catch (e) {
    destinos.forEach(x => falla(x, T.posiciones));
    return;
  }

  avisoEjemplo(d);

  destinos.forEach(destino => pintarTabla(destino, d));
}

function pintarTabla(destino, d) {
  const resumida = destino.dataset.tabla === 'resumida';

  const encabezados = resumida
    ? T.tablaCorta
    : T.tablaLarga;

  const equipos = resumida
    ? d.equipos.slice(0, 6)
    : d.equipos;

  destino.innerHTML = `
    <div class="tabla-envoltorio">
      <table class="posiciones">
        <caption class="sr-only">Posiciones del ${esc(d.torneo)}</caption>
        <thead><tr>${encabezados.map(h => `<th scope="col">${h}</th>`).join('')}</tr></thead>
        <tbody>${equipos.map(e => filaTabla(e, resumida)).join('')}</tbody>
      </table>
    </div>
    <p class="aviso-formulario" style="margin-top:12px">${esc(d.torneo)} · ${T.fecha} ${d.fecha_jugada} · ${T.actualizado} ${esc(fechaCorta(d.actualizado))} · ${T.fuente} ${esc(d.fuente || 'AUF')}</p>`;
}

/* ---------- Plantel ---------- */

async function plantel() {
  const destino = document.querySelector('[data-plantel]');
  if (!destino) return;

  let d;
  try {
    d = await traer(RUTAS.plantel);
  } catch (e) {
    falla(destino, T.plantel);
    return;
  }

  const puestos = ['Arqueros', 'Defensas', 'Mediocampistas', 'Delanteros'];
  destino.innerHTML = puestos.map(puesto => {
    const grupo = d.jugadores.filter(j => j.puesto === puesto);
    if (!grupo.length) return '';
    return `<section class="grupo-plantel">
        <p class="cintilla">${esc(T.puestos[puesto] || puesto)}</p>
        <div class="rejilla rejilla--3">
          ${grupo.map(j => `
            <article class="jugador ${j.nombre ? '' : 'jugador--vacante'}">
              <span class="numero">${j.numero != null ? j.numero : '—'}</span>
              <span>
                <span class="nombre">${esc(j.nombre || T.aConfirmar)}</span><br>
                <span class="detalle">${esc(j.nacimiento || T.fichaPendiente)}</span>
              </span>
            </article>`).join('')}
        </div>
      </section>`;
  }).join('');

  const ct = document.querySelector('[data-cuerpo-tecnico]');
  if (ct) {
    ct.innerHTML = d.cuerpoTecnico.map(m => `
      <div><dt>${esc(m.rol)}</dt><dd>${esc(m.nombre || T.aConfirmar)}</dd></div>`).join('');
  }
}

/* ---------- Noticias ---------- */

async function noticias() {
  const destinos = document.querySelectorAll('[data-noticias]');
  if (!destinos.length) return;

  let d;
  try {
    d = await traer(RUTAS.noticias);
  } catch (e) {
    destinos.forEach(x => falla(x, T.noticias));
    return;
  }

  avisoEjemplo(d);

  destinos.forEach(destino => pintarNoticias(destino, d));
}

function pintarNoticias(destino, d) {
  const limite = Number(destino.dataset.noticias) || 0;
  const notas = limite ? d.notas.slice(0, limite) : d.notas;
  destino.innerHTML = notas.map(n => `
    <article class="noticia">
      <img src="${esc(n.imagen)}" alt="" loading="lazy" width="1000" height="640">
      <div class="noticia-cuerpo">
        <p class="fecha">${esc(fechaCorta(n.fecha))}</p>
        <h3>${n.enlace ? `<a href="${esc(n.enlace)}">${esc(n.titulo)}</a>` : esc(n.titulo)}</h3>
        <p>${esc(n.bajada)}</p>
        <p class="etiqueta">${esc(n.etiqueta || T.club)}</p>
      </div>
    </article>`).join('');
}


/* ---------- Galería ----------
   El álbum del club. Las fotos se cargan desde data/fotos.json: para sumar
   una hay que dejar el archivo en assets/img/galeria/ y agregar la entrada
   en ese JSON. Nada de esto toca el HTML, que lo reescribe build.py. */

async function galeria() {
  const destino = document.querySelector('[data-galeria]');
  if (!destino) return;

  let d;
  try {
    d = await traer(RUTAS.fotos);
  } catch (e) {
    falla(destino, T.fotos);
    return;
  }

  avisoEjemplo(d);

  const grupos = (d.grupos || []).filter(g => (g.fotos || []).length);
  if (!grupos.length) {
    destino.innerHTML = `<p class="nota">${T.sinFotos}</p>`;
    return;
  }

  destino.innerHTML = grupos.map(g => `
    <section class="grupo-galeria">
      <p class="cintilla">${esc(g.titulo)}</p>
      ${g.bajada ? `<p class="prosa">${esc(g.bajada)}</p>` : ''}
      <div class="galeria">
        ${g.fotos.map(f => `
          <figure class="postal">
            <button type="button" data-foto="${esc(f.archivo)}" data-pie="${esc(f.pie || '')}">
              <img src="${esc(f.archivo)}" alt="${esc(f.pie || g.titulo)}" loading="lazy">
            </button>
            <figcaption>
              <span>${esc(f.pie || '')}</span>
              ${f.fecha ? `<i>${esc(fechaCorta(f.fecha))}</i>` : ''}
            </figcaption>
          </figure>`).join('')}
      </div>
    </section>`).join('');

  visor(destino);
}

/* Visor: agranda una foto sin sacar a nadie de la página. */
function visor(destino) {
  const caja = document.querySelector('[data-visor]');
  if (!caja || !caja.showModal) return;

  const img = caja.querySelector('[data-visor-img]');
  const pie = caja.querySelector('[data-visor-pie]');

  destino.addEventListener('click', ev => {
    const boton = ev.target.closest('[data-foto]');
    if (!boton) return;
    img.src = boton.dataset.foto;
    img.alt = boton.dataset.pie || '';
    pie.textContent = boton.dataset.pie || '';
    caja.showModal();
  });

  /* Clic en el fondo del visor: cerrar. */
  caja.addEventListener('click', ev => {
    if (ev.target === caja) caja.close();
  });
}

/* ---------- Formularios (sin backend todavía) ---------- */

function formularios() {
  document.querySelectorAll('form[data-sin-backend]').forEach(f => {
    f.addEventListener('submit', ev => {
      ev.preventDefault();
      const aviso = f.querySelector('[data-respuesta]');
      if (!aviso) return;
      /* Sin backend, el formulario arma el correo con lo que se escribió y
         abre el cliente de mail: el mensaje sale igual, y el visitante ve lo
         que manda antes de mandarlo. */
      const correo = f.dataset.sinBackend || 'marca@calito.uy';
      const cuerpo = Array.from(new FormData(f), ([campo, valor]) => `${campo}: ${valor}`).join('\n');
      const asunto = f.querySelector('#categoria') ? T.asuntoSocio : T.asuntoConsulta;
      const enlace = `mailto:${correo}?subject=${encodeURIComponent(asunto)}&body=${encodeURIComponent(cuerpo)}`;
      aviso.hidden = false;
      aviso.innerHTML = T.correoListo(esc(enlace), esc(correo));
      window.location.href = enlace;
    });
  });
}

/* ---------- Año en el pie ---------- */

function anio() {
  document.querySelectorAll('[data-anio]').forEach(n => { n.textContent = new Date().getFullYear(); });
}

libro();
menu();
anio();
formularios();
partidos();
tabla();
plantel();
noticias();
galeria();

/* Aparición al entrar en pantalla. Es un adorno: si no hay JavaScript, si el
   navegador no trae IntersectionObserver o si el sistema pide menos
   movimiento, el contenido se ve igual, porque la clase que lo atenúa la
   agrega este mismo script. */
if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches && 'IntersectionObserver' in window) {
  const observador = new IntersectionObserver(entradas => entradas.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('en-vista'); observador.unobserve(e.target); }
  }), { threshold: 0.12 });
  document.querySelectorAll('.timeline-visual li, .campeon, .renders, .momento, .barrio-panorama').forEach(n => {
    n.classList.add('revelar');
    observador.observe(n);
  });
}
