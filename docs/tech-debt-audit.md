# Tech Debt Audit — Traefik Reverse-Proxy Stack

**Date:** 2026-04-30
**Scope:** Architecture · Documentation · Infrastructure
**Team size:** 1–3 engineers
**Files reviewed:** `traefik/docker-compose.yml`, `traefik/README.md`

---

## Scoring method

Priority = (Impact + Risk) × (6 − Effort)

Each dimension is scored 1–5. Effort is inverted — lower effort means higher priority score.

---

## Prioritized debt inventory

### 1. No `.gitignore` covering secrets — Priority 40

**Category:** Infrastructure · **Risk:** Critical

`letsencrypt/acme.json` (written by Traefik at runtime) contains private TLS keys. `dynamic/dashboard-users.htpasswd` contains hashed admin credentials. Neither appears to be gitignored. A single accidental `git add .` pushes both to remote.

**Fix:** Add a `.gitignore` at the repo root covering:

```
traefik/letsencrypt/
traefik/certs/
traefik/dynamic/dashboard-users.htpasswd
```

**Business case:** A leaked private key means the TLS certificate must be revoked and reissued — downtime plus incident response for a 10-minute fix.

---

### 2. Watchtower not yet integrated — Priority 28

**Category:** Infrastructure

Without Watchtower, image updates require manual SSH + `docker compose pull && docker compose up -d` per service. For a 1–3 person team this compounds fast across multiple microservices.

**Fix:** Add a `watchtower` service block to `docker-compose.yml`. Scope it to labelled containers only (`--label-enable`) so it only monitors services explicitly opted in.

**Business case:** Unpatched base images are the most common CVE vector in self-hosted stacks. Automating updates closes that gap with no ongoing toil.

---

### 3. No container health checks — Priority 25

**Category:** Infrastructure · Architecture

Neither `traefik` nor `whoami` define a `healthcheck` block. Docker cannot distinguish a hung Traefik process from a healthy one. Traefik v3 exposes a native health endpoint.

**Fix:** Add to the `traefik` service:

```yaml
healthcheck:
  test: ["CMD", "traefik", "healthcheck", "--ping"]
  interval: 30s
  timeout: 5s
  retries: 3
```

Enable the ping endpoint with `--ping` in the command block.

**Business case:** A silently-hung reverse proxy takes every service behind it down with it. Health checks enable automatic recovery.

---

### 4. Dashboard exposed with only basic auth — Priority 24

**Category:** Architecture · Infrastructure

The Traefik dashboard is reachable from the public internet. No rate limiting is configured, meaning brute-force attempts against the basic auth are unconstrained.

**Fix:** Add an `ipallowlist` middleware restricting dashboard access to known operator IPs, or add a `ratelimit` middleware as a fallback for dynamic IP environments.

```yaml
- "traefik.http.middlewares.dashboard-ipallow.ipallowlist.sourcerange=YOUR.IP.RANGE/32"
- "traefik.http.routers.dashboard.middlewares=dashboard-auth@docker,dashboard-ipallow@docker"
```

**Business case:** The dashboard exposes the full routing topology and is a reconnaissance target. IP allowlisting is the highest signal-to-noise mitigation available.

---

### 5. No backup strategy for `acme.json` — Priority 24

**Category:** Infrastructure

Let's Encrypt rate-limits issuance to 5 certificates per registered domain per week. If `acme.json` is lost (VPS destroyed, accidental deletion), recovery takes days, not minutes.

**Fix:** Schedule a nightly cron job on the VPS that copies `acme.json` to off-host storage (S3, Backblaze B2, or a secondary server). Document the restore procedure in `docs/runbook.md`.

**Business case:** Without a backup, certificate recovery time is measured in days due to Let's Encrypt rate limits.

---

### 6. Docker socket mounted directly — Priority 21

**Category:** Architecture

`/var/run/docker.sock` is mounted read-only, which limits write access. However, read access to the socket still exposes container metadata, environment variables, and labels across the entire Docker host.

**Fix:** Insert `tecnativa/docker-socket-proxy` between Traefik and the socket. Expose only the APIs Traefik needs:

```yaml
socket-proxy:
  image: tecnativa/docker-socket-proxy
  environment:
    CONTAINERS: 1
    NETWORKS: 1
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock:ro
```

Update `--providers.docker.endpoint` to point at the proxy instead of the socket.

**Business case:** If Traefik were compromised, direct socket access is the path to full host takeover. The socket proxy enforces least-privilege.

---

### 7. Network comment says overlay, config uses bridge — Priority 20

**Category:** Architecture · Documentation

Line 10 of `docker-compose.yml` describes the `proxy` network as an "overlay network for inter-container communication across nodes," but no `driver: overlay` is set and Swarm mode is not in use. The network is a plain bridge.

**Fix:** Either update the comment to reflect single-host bridge reality, or add `driver: overlay` with a note that Swarm mode is a prerequisite.

**Business case:** A new contributor reading this comment will make incorrect assumptions about the deployment topology, leading to wasted debugging time.

---

### 8. Referenced docs do not exist — Priority 20

**Category:** Documentation

The README references `docs/production-hardening.md` (line 239) and `docs/automating-deployment-summary.md` (line 247). Neither file appears to exist in the repository.

**Fix:** Create stub versions of both files now, or remove the references until the content is written. The production hardening checklist in particular is what a new operator needs before going live.

**Business case:** Dead links in a README erode trust in the document and cause operators to skip hardening steps.

---

### 9. CI/CD GitHub Actions pipeline — Priority 16

**Category:** Infrastructure

No automated pipeline exists for building and publishing Docker images. Manual image builds mean the operator is the deployment bottleneck and every deploy carries human-error risk.

**Fix:** Design before building: agree on image naming conventions, registry (GHCR is the natural fit), branch strategy for triggering builds, and how Watchtower will poll for new tags. Implement as a `build-and-push.yml` Actions workflow.

**Business case:** With Actions + GHCR + Watchtower wired up, a `git push` to `main` fully deploys — zero manual steps.

---

### 10. `whoami` test service in the base compose — Priority 15

**Category:** Architecture

The `whoami` container validates routing during setup but is not a production service. Leaving it in the main `docker-compose.yml` means it runs in production unless explicitly removed.

**Fix:** Move to a `docker-compose.dev.yml` overlay, included only for local development and validation.

**Business case:** Reduces unnecessary attack surface in production and makes the base compose file a cleaner template for adding real services.

---

### 11. No runbooks for common operations — Priority 15

**Category:** Documentation

There are no documented procedures for cert rotation, adding a new service behind Traefik, updating the Traefik version, or restoring from an `acme.json` backup.

**Fix:** Create `docs/runbook.md` with sections for each operation. Start with the restore procedure (tied to item 5) and adding a new service (the most common recurring task).

**Business case:** Without runbooks, operations are tribal knowledge. On a 1–3 person team, that creates a single point of failure.

---

### 12. Prometheus metrics enabled, no scraper configured — Priority 12

**Category:** Infrastructure

`--metrics.prometheus=true` is set, but nothing is scraping the metrics endpoint. The data is being generated and discarded.

**Fix:** Either add a lightweight Prometheus + Grafana stack (another compose file) or remove the flag until monitoring is actually set up, to avoid the false sense of observability.

**Business case:** Enabling metrics without consuming them provides no operational benefit and slightly increases the attack surface.

---

### 13. Informal phrasing in README — Priority 10

**Category:** Documentation

Phrases like "Quick and dirty way" (line 70) and a default dev password of `choose-good-password` documented in plain text (line 105) reduce the document's credibility as a reference template.

**Fix:** Replace informal phrasing with neutral instructional language. Remove the plaintext dev password from the README.

**Business case:** Minor polish, but a README is often the first thing a new collaborator reads.

---

## Phased remediation plan

### Phase 1 — This week (2–3 hours, do these before anything else)

- Add `.gitignore` covering `letsencrypt/`, `certs/`, and `htpasswd` *(30 min)*
- Add health checks to `traefik` and `whoami` *(30 min)*
- Set up `acme.json` nightly backup cron on the VPS *(45 min)*
- Fix or stub the missing docs (`production-hardening.md`, `automating-deployment-summary.md`) *(45 min)*
- Fix the network comment *(5 min)*

### Phase 2 — Next sprint (alongside Watchtower + CI planning)

- Add Watchtower service to `docker-compose.yml`
- Add IP allowlist or rate-limit middleware to the dashboard router
- Move `whoami` to `docker-compose.dev.yml`
- Start `docs/runbook.md` — restore procedure and add-a-service walkthrough

### Phase 3 — After CI/CD is wired up

- Implement GitHub Actions build-and-push pipeline (GHCR)
- Validate Watchtower picks up new image tags end-to-end
- Add Docker socket proxy (highest risk of breaking service discovery — safer to do when a deployment pipeline exists to push fixes quickly)
- Add Prometheus scraper or remove the metrics flag

---

*Audit produced by Claude · Cowork mode · 2026-04-30*
