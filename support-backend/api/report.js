const ALLOWED_DIAGNOSTICS = new Set([
  'app_version', 'build', 'os', 'theme', 'page', 'update_channel',
  'roblox_running', 'roblox_version_folder', 'cpu_percent', 'ram_percent',
  'screen', 'tk_scaling', 'spotify_detected', 'safe_start'
]);

const rateBuckets = globalThis.__zkstrapRateBuckets || new Map();
globalThis.__zkstrapRateBuckets = rateBuckets;

function cleanText(value, max = 1200) {
  let text = String(value ?? '');
  text = text.replace(/https:\/\/(?:canary\.|ptb\.)?discord(?:app)?\.com\/api\/webhooks\/\S+/gi, '[redacted]');
  text = text.replace(/C:\\Users\\[^\\\s]+/gi, '%USERPROFILE%');
  text = text.replace(/\b(?:\d{1,3}\.){3}\d{1,3}\b/g, '[ip-redacted]');
  text = text.replace(/\b(authorization|cookie|token|password|senha)\s*[:=]\s*[^\s,;]+/gi, '$1=[redacted]');
  return text.slice(0, max);
}

function getIp(req) {
  const raw = String(req.headers['x-forwarded-for'] || req.socket?.remoteAddress || 'unknown');
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

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ ok: false, error: 'method_not_allowed' });
  }

  const webhook = process.env.DISCORD_WEBHOOK_URL;
  if (!webhook || !/^https:\/\/(?:canary\.|ptb\.)?discord(?:app)?\.com\/api\/webhooks\//i.test(webhook)) {
    return res.status(503).json({ ok: false, error: 'support_not_configured' });
  }

  const contentLength = Number(req.headers['content-length'] || 0);
  if (contentLength > 16_384) {
    return res.status(413).json({ ok: false, error: 'payload_too_large' });
  }

  const ip = getIp(req);
  if (!allowRequest(ip)) {
    return res.status(429).json({ ok: false, error: 'rate_limited' });
  }

  let body = req.body;
  if (typeof body === 'string') {
    try { body = JSON.parse(body); } catch { body = null; }
  }
  if (!body || typeof body !== 'object' || Array.isArray(body)) {
    return res.status(400).json({ ok: false, error: 'invalid_json' });
  }
  if (body.source !== 'zkstrap-client') {
    return res.status(400).json({ ok: false, error: 'invalid_source' });
  }

  const type = cleanText(body.type || 'Feedback', 60);
  const title = cleanText(body.title || '', 140);
  const message = cleanText(body.message || '', 3500).trim();
  const appVersion = cleanText(body.app_version || '', 40);
  if (message.length < 5) {
    return res.status(400).json({ ok: false, error: 'message_too_short' });
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

  try {
    const upstream = await fetch(webhook, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(discordPayload)
    });
    if (!upstream.ok) {
      return res.status(502).json({ ok: false, error: 'discord_delivery_failed' });
    }
    return res.status(200).json({ ok: true });
  } catch {
    return res.status(502).json({ ok: false, error: 'delivery_failed' });
  }
}
