export const config = { runtime: 'edge' };

const ALLOWED_DIAGNOSTICS = new Set([
  'app_version', 'build', 'os', 'theme', 'page', 'update_channel',
  'roblox_running', 'roblox_version_folder', 'cpu_percent', 'ram_percent',
  'screen', 'tk_scaling', 'spotify_detected', 'safe_start'
]);

const rateBuckets = globalThis.__zkstrapRateBuckets || new Map();
globalThis.__zkstrapRateBuckets = rateBuckets;

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': 'no-store',
      'x-content-type-options': 'nosniff'
    }
  });
}

function cleanText(value, max = 1200) {
  let text = String(value ?? '');
  text = text.replace(/https:\/\/(?:canary\.|ptb\.)?discord(?:app)?\.com\/api\/webhooks\/\S+/gi, '[redacted]');
  text = text.replace(/C:\\Users\\[^\\\s]+/gi, '%USERPROFILE%');
  text = text.replace(/\b(?:\d{1,3}\.){3}\d{1,3}\b/g, '[ip-redacted]');
  text = text.replace(/\b(authorization|cookie|token|password|senha)\s*[:=]\s*[^\s,;]+/gi, '$1=[redacted]');
  return text.slice(0, max);
}

function getIp(req) {
  const raw = String(req.headers.get('x-forwarded-for') || 'unknown');
  return raw.split(',')[0].trim().slice(0, 80);
}

function allowRequest(ip) {
  const now = Date.now();
  const windowMs = 60_000;
  const max = 4;
  const bucket = rateBuckets.get(ip) || [];
  const fresh = bucket.filter(t => now - t < windowMs);
  if (fresh.length >= max) {
    rateBuckets.set(ip, fresh);
    return false;
  }
  fresh.push(now);
  rateBuckets.set(ip, fresh);
  if (rateBuckets.size > 2000) {
    for (const [key, times] of rateBuckets) {
      if (!times.some(t => now - t < windowMs)) rateBuckets.delete(key);
    }
  }
  return true;
}

function diagnosticLines(input) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) return [];
  const out = [];
  for (const [key, value] of Object.entries(input)) {
    if (!ALLOWED_DIAGNOSTICS.has(key)) continue;
    out.push(`**${cleanText(key, 40)}:** ${cleanText(value, 220)}`);
  }
  return out.slice(0, 16);
}

export default async function handler(req) {
  if (req.method !== 'POST') {
    return json({ ok: false, error: 'method_not_allowed' }, 405);
  }

  const webhook = process.env.DISCORD_WEBHOOK_URL;
  if (!webhook || !/^https:\/\/(?:canary\.|ptb\.)?discord(?:app)?\.com\/api\/webhooks\//i.test(webhook)) {
    return json({ ok: false, error: 'support_not_configured' }, 503);
  }

  const contentLength = Number(req.headers.get('content-length') || 0);
  if (contentLength > 16_384) {
    return json({ ok: false, error: 'payload_too_large' }, 413);
  }

  const ip = getIp(req);
  if (!allowRequest(ip)) {
    return json({ ok: false, error: 'rate_limited' }, 429);
  }

  let body;
  try {
    body = await req.json();
  } catch {
    return json({ ok: false, error: 'invalid_json' }, 400);
  }
  if (!body || typeof body !== 'object' || Array.isArray(body)) {
    return json({ ok: false, error: 'invalid_json' }, 400);
  }
  if (body.source !== 'zkstrap-client') {
    return json({ ok: false, error: 'invalid_source' }, 400);
  }

  const type = cleanText(body.type || 'Feedback', 60);
  const title = cleanText(body.title || '', 140);
  const message = cleanText(body.message || '', 3500).trim();
  const appVersion = cleanText(body.app_version || '', 40);
  if (message.length < 5) {
    return json({ ok: false, error: 'message_too_short' }, 400);
  }

  const diag = diagnosticLines(body.diagnostics);
  const logs = Array.isArray(body.recent_logs)
    ? body.recent_logs.slice(-14).map(v => cleanText(v, 700)).filter(Boolean)
    : [];

  const fields = [];
  if (title) fields.push({ name: 'Título', value: title, inline: false });
  fields.push({ name: 'Relato', value: message.slice(0, 1024), inline: false });
  if (diag.length) fields.push({ name: 'Diagnóstico', value: diag.join('\n').slice(0, 1024), inline: false });
  if (logs.length) fields.push({ name: 'Logs recentes', value: `\`\`\`\n${logs.join('\n').slice(0, 900)}\n\`\`\``, inline: false });

  const discordPayload = {
    username: 'ZKStrap Support',
    allowed_mentions: { parse: [] },
    embeds: [{
      title: `🐛 ${type}`,
      description: appVersion ? `ZKStrap v${appVersion}` : 'ZKStrap',
      fields,
      timestamp: new Date().toISOString(),
      footer: { text: 'Relatório enviado pelo cliente ZKStrap' }
    }]
  };

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 6000);
  try {
    const upstream = await fetch(webhook + '?wait=true', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(discordPayload),
      signal: controller.signal
    });
    if (!upstream.ok) {
      return json({ ok: false, error: 'discord_delivery_failed', status: upstream.status }, 502);
    }
    return json({ ok: true }, 200);
  } catch (err) {
    return json({ ok: false, error: err && err.name === 'AbortError' ? 'discord_timeout' : 'delivery_failed' }, 502);
  } finally {
    clearTimeout(timer);
  }
}
