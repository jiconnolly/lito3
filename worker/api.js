/**
 * Centro Atlético Lito — Worker de Cloudflare (todavía sin publicar).
 *
 * Cubre dos necesidades que GitHub Pages no puede resolver solo:
 *   1. Servir tabla y partidos desde KV, para poder actualizarlos sin
 *      hacer un commit en el repositorio.
 *   2. Recibir los formularios de socios y contacto sin exponer un correo
 *      ni una clave en el HTML.
 *
 * Publicación:
 *   wrangler kv namespace create DATOS
 *   wrangler kv namespace create ENVIOS
 *   wrangler deploy
 *
 * Después, en assets/js/main.js poner ORIGEN_VIVO = 'https://<worker>/api'
 * (o '/api' si el Worker queda en el mismo dominio).
 */

const ORIGENES = [
  'https://calito.uy',
  'https://www.calito.uy'
];

function cors(request) {
  const origen = request.headers.get('Origin') || '';
  return {
    'Access-Control-Allow-Origin': ORIGENES.includes(origen) ? origen : ORIGENES[0],
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Vary': 'Origin'
  };
}

function json(datos, request, estado = 200, cache = 300) {
  return new Response(JSON.stringify(datos), {
    status: estado,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': `public, max-age=${cache}`,
      ...cors(request)
    }
  });
}

async function guardarEnvio(env, tipo, request) {
  const cuerpo = await request.json().catch(() => null);
  if (!cuerpo || !cuerpo.correo || !cuerpo.nombre) {
    return json({ ok: false, error: 'faltan datos' }, request, 400, 0);
  }
  const clave = `${tipo}:${Date.now()}:${crypto.randomUUID()}`;
  await env.ENVIOS.put(clave, JSON.stringify({
    tipo,
    recibido: new Date().toISOString(),
    ip: request.headers.get('CF-Connecting-IP') || '',
    datos: cuerpo
  }), { expirationTtl: 60 * 60 * 24 * 180 });
  return json({ ok: true }, request, 200, 0);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const ruta = url.pathname.replace(/^\/api/, '');

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: cors(request) });
    }

    if (request.method === 'GET' && (ruta === '/tabla' || ruta === '/partidos')) {
      const guardado = await env.DATOS.get(ruta.slice(1), 'json');
      if (!guardado) return json({ error: 'sin datos cargados' }, request, 404, 0);
      return json(guardado, request);
    }

    if (request.method === 'POST' && ruta === '/socios') {
      return guardarEnvio(env, 'socio', request);
    }

    if (request.method === 'POST' && ruta === '/contacto') {
      return guardarEnvio(env, 'contacto', request);
    }

    return json({ error: 'ruta desconocida' }, request, 404, 0);
  }
};
