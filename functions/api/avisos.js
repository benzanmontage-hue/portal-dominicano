// Avisos al móvil (notificaciones web). Guarda en Cloudflare KV (binding AVISOS) qué loterías
// quiere recibir cada navegador. El envío lo hace scripts/notificar.py cuando salen números nuevos.
//   GET    /api/avisos  -> { clave }  clave pública (VAPID) para suscribirse
//   POST   /api/avisos  { subscription, loterias: [...] }  alta o cambio (lista vacía = baja)
//   DELETE /api/avisos  { endpoint }  baja
const LOTERIAS = ['loteria-nacional', 'anguila', 'loteria-real', 'loteka', 'la-primera', 'la-suerte', 'leidsa'];
// Solo servicios de notificaciones reales de los navegadores.
const HOSTS = [/^fcm\.googleapis\.com$/, /^android\.googleapis\.com$/, /(^|\.)push\.services\.mozilla\.com$/,
               /^web\.push\.apple\.com$/, /\.push\.apple\.com$/, /\.notify\.windows\.com$/];

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), { status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' } });
}
async function clave(endpoint) {
  const h = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(endpoint));
  return [...new Uint8Array(h)].map(b => b.toString(16).padStart(2, '0')).join('');
}
function endpointValido(e) {
  if (typeof e !== 'string' || e.length > 700) return false;
  try { const u = new URL(e); return u.protocol === 'https:' && HOSTS.some(r => r.test(u.hostname)); } catch (_) { return false; }
}

export async function onRequestGet({ env }) {
  const r = await env.AVISOS.getWithMetadata('_vapid');
  const pub = r && r.metadata && r.metadata.pub;
  return pub ? json({ clave: pub }) : json({ error: 'Los avisos se están preparando; prueba en unos minutos.' }, 503);
}

export async function onRequestPost({ request, env }) {
  let d;
  try { d = await request.json(); } catch (_) { return json({ error: 'Datos no válidos' }, 400); }
  const s = d && d.subscription;
  if (!s || !endpointValido(s.endpoint) || !s.keys || typeof s.keys.p256dh !== 'string' || typeof s.keys.auth !== 'string'
      || s.keys.p256dh.length > 120 || s.keys.auth.length > 40) {
    return json({ error: 'Suscripción no válida' }, 400);
  }
  const lots = [...new Set((Array.isArray(d.loterias) ? d.loterias : []).filter(x => LOTERIAS.includes(x)))];
  const k = await clave(s.endpoint);
  if (!lots.length) { await env.AVISOS.delete(k); return json({ ok: true, loterias: [] }); }
  await env.AVISOS.put(k, '1', { metadata: { e: s.endpoint, p: s.keys.p256dh, a: s.keys.auth, l: lots, t: Date.now() } });
  return json({ ok: true, loterias: lots });
}

export async function onRequestDelete({ request, env }) {
  let d;
  try { d = await request.json(); } catch (_) { return json({ error: 'Datos no válidos' }, 400); }
  if (!d || !endpointValido(d.endpoint)) return json({ error: 'Datos no válidos' }, 400);
  await env.AVISOS.delete(await clave(d.endpoint));
  return json({ ok: true });
}
