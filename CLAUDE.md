# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Micro Projects with Traefik** is an infrastructure-as-code starter stack built around Traefik v3.x as a reverse proxy. It supports both local development (mkcert self-signed certs) and production VPS deployment (Let's Encrypt), controlled entirely by `.env` values — no changes to `docker-compose.yml` are needed between environments.

## Starting the Stack

All commands run from `traefik/`.

**Local development (first-time cert setup):**
```bash
mkcert -install
mkcert -cert-file traefik/certs/dev.localhost.pem \
       -key-file traefik/certs/dev.localhost-key.pem \
       dev.localhost "*.dev.localhost" ::1
```

**Start (using the example env):**
```bash
cd traefik
docker compose --env-file .env.example up -d
```

**Or with your own `.env`:**
```bash
cp traefik/.env.example traefik/.env
# edit .env, then:
docker compose -f traefik/docker-compose.yml up -d
```

**Verify / Logs:**
```bash
docker compose -f traefik/docker-compose.yml ps
docker compose -f traefik/docker-compose.yml logs -f traefik
```

## Architecture

```
traefik/
├── docker-compose.yml        # Traefik + whoami; all routing via Docker labels
├── .env.example              # Toggle local↔production via these three vars
├── certs/                    # mkcert certs (gitignored *.pem)
├── dynamic/
│   ├── tls.yaml              # File-provider TLS cert paths (local dev only)
│   └── dashboard-users.htpasswd
└── letsencrypt/              # acme.json written here at runtime (gitignored)
```

### Dual-mode configuration

The same `docker-compose.yml` handles both environments. The three `.env` keys determine behavior:

| Key | Local dev | Production |
|---|---|---|
| `TRAEFIK_DASHBOARD_HOST` | `dev.localhost` | `yourdomain.com` |
| `ACME_EMAIL` | *(empty)* | `you@example.com` |
| `CERT_RESOLVER` | *(empty)* | `letsencrypt` |

When `CERT_RESOLVER` is empty, Traefik uses the static cert from `dynamic/tls.yaml`. When set to `letsencrypt`, it uses the ACME resolver and ignores the file provider cert.

### Adding a new service

Add it to `docker-compose.yml` (or a new compose file that extends the `proxy` network) with Traefik labels, for example:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.myapp.rule=Host(`myapp.${TRAEFIK_DASHBOARD_HOST}`)"
  - "traefik.http.routers.myapp.entrypoints=websecure"
  - "traefik.http.routers.myapp.tls.certresolver=${CERT_RESOLVER}"
networks:
  - proxy
```

Services that don't declare `traefik.enable=true` are invisible to Traefik (Docker provider `exposedByDefault: false`).

The `example-app/` directory is the intended location for the first microservice added to the stack.

## Production Hardening

See `docs/production-hardening.md` for the full checklist (IP allowlist for dashboard, ufw rules, Docker socket exposure, SSH hygiene, etc.).

## CI/CD Pattern

See `docs/automating-deployment-summary.md` for the GitHub Actions + Watchtower pipeline. Workflow triggers on semantic version tags (`*.*.*`), publishes to `ghcr.io`, and Watchtower auto-deploys on the VPS.
