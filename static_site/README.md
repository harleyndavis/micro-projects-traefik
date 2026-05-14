# static_site

An nginx container serving the `www.<host>` landing page. It hosts the shared `site.css` stylesheet that the `url_shortener` templates load cross-origin, so both services stay visually consistent without duplicating CSS.

## What it serves

- `www.<DOMAIN>` — the main landing page (`html/index.html`)
- `www.<DOMAIN>/css/site.css` — shared stylesheet (consumed by url_shortener templates)

All files under `html/` are served read-only; no build step is needed.

## Quick Start

From the repo root:

```bash
make up-static
```

Or directly from `static_site/`:

```bash
docker compose --env-file .env up -d
```

## Configuration

Copy the example env file:

```bash
cp .env.example .env
```

`.env.example` contains:

```env
DOMAIN=dev.localhost
CERT_RESOLVER=
```

These mirror the values in `traefik/.env`. For local dev the defaults work as-is. For production, set both to match your Traefik stack.

| Variable | Local | Production |
|---|---|---|
| `DOMAIN` | `dev.localhost` | `yourdomain.com` |
| `CERT_RESOLVER` | *(empty)* | `letsencrypt` |

## Prerequisites

- The `proxy` Docker network must exist (created automatically when the Traefik stack starts)
- Traefik must be running to route `www.<host>` to this container

## Logs

```bash
make logs-static
# or
docker compose logs -f static_site
```
