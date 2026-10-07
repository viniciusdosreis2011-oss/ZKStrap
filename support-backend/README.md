# ZKStrap Support Proxy

Server-side endpoint for ZKStrap bug reports.

## Deployment

Deploy this folder as a Vercel project with **Root Directory** set to `support-backend`.

Create one server-side environment variable:

- `DISCORD_WEBHOOK_URL` — the private Discord webhook used only by the server.

Never place the webhook in `docs/feedback.json`, the desktop client, a GitHub commit, a screenshot, or a public log.

After deployment, set `docs/feedback.json` to:

```json
{
  "enabled": true,
  "endpoint": "https://YOUR-VERCEL-DOMAIN/api/report"
}
```

The public client only receives the proxy URL. The proxy validates payload size/source, rate-limits per forwarded IP on each running instance, allows only a fixed diagnostics field list, sanitizes logs, and forwards the final report to Discord.
