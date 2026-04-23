# Automating Deployment to a VPS

> A DevOps Approach with GitHub Actions, Docker, Traefik, & Watchtower
>
> *Presented by David Slusser — August 20, 2025, Spokane Python User Group / Spokane Go User Group*
> *Original document found here: https://gamma.app/docs/Automating-Deployment-to-a-VPS-e01q5blgsrphcws?mode=doc*

---

## The Problem with Manual Deployments

Many developers still deploy to VPS servers using outdated, error-prone methods:

- **SSH Headaches** — Manually logging into servers for every deployment
- **Command Chaos** — Running `git pull`, `docker build` commands by hand
- **Service Struggles** — Restarting services manually, often causing downtime
- **Scale Barriers** — Process breaks down completely with multiple apps or servers

---

## The Solution Stack

| Tool | Role |
|------|------|
| **GitHub Actions** | Automated CI/CD pipeline triggered by code changes or tags |
| **Docker** | Containerization ensuring consistent environments from dev to prod |
| **Traefik** | Smart reverse proxy for routing traffic with automatic SSL |
| **Watchtower** | Container updater that pulls and deploys new images automatically |

---

## How It Works: The Full Pipeline

```
Push Code → Build Image → Push Image → Detect Update → Restart Container
```

This end-to-end automation eliminates manual server access, reduces human error, and enables rapid deployment cycles — often **under 2 minutes from commit to production**.

---

## CI/CD with GitHub Actions

### Trigger
Workflow activates when you push a **semantic version tag** matching `*.*.*` (e.g., `1.2.3`).

### Steps
1. **Authentication** — Securely logs into GitHub Container Registry using repository secrets
2. **Build Process** — Compiles application, runs tests, and builds optimized Docker image
3. **Push Operation** — Tags and pushes the image to `ghcr.io/username/repo:1.2.3`

### Key Features
- Only triggers on semantic version tags
- Handles login credentials securely via `secrets.GITHUB_TOKEN`
- Tags image with the version from the Git tag
- Supports `latest`, `dev`, and release candidate tags
- Auto-labels `latest` with semver

### Workflow File

```yaml
name: CI/CD Pipeline

on:
  push:
    tags: ['*.*.*']

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.ref_name }}
```

---

## Traefik: The Smart Reverse Proxy

### Why Traefik?
- Routes traffic to multiple websites/apps on a single VPS
- Dynamically configures itself based on Docker container labels
- Automatically handles SSL certificates with Let's Encrypt
- Provides health checks and load balancing
- Enables zero-downtime deployments during container updates

### Configuration

```yaml
services:
  traefik:
    image: traefik:v2.9
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./letsencrypt:/letsencrypt
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.dashboard.rule=Host(`traefik.example.com`)"
      - "traefik.http.routers.dashboard.service=api@internal"
      - "traefik.http.routers.dashboard.entrypoints=websecure"
      - "traefik.http.routers.dashboard.tls.certresolver=letsencrypt"
    restart: unless-stopped
```

### Key Configuration Points
- **Docker Socket Mount** — Allows Traefik to discover containers automatically
- **Ports 80 & 443** — Handles both HTTP and HTTPS traffic
- **LetsEncrypt Volume** — Persists SSL certificates across restarts
- **Labels** — Enable the optional admin dashboard

> Traefik's power comes from configuring routes automatically based on container labels — no manual nginx or Apache configuration needed.

---

## Watchtower: The Automated Updater

Watchtower runs as a background container on your VPS and handles the update loop:

1. **Continuous Monitoring** — Checks for image updates on a configurable interval (default: every 5 minutes)
2. **Image Detection** — When GitHub Actions pushes a new image to the registry, Watchtower detects the change
3. **Graceful Update** — Pulls the new image, gracefully stops the old container, and starts a new one with identical settings
4. **Cleanup** — Removes old, unused images to prevent disk space issues

---

## Putting It All Together

### Full `docker-compose.yml`

```yaml
version: '3'

services:
  # Traefik service (see above)

  watchtower:
    image: containrrr/watchtower
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    command: --interval 300 --cleanup
    restart: unless-stopped

  myapp:
    image: ghcr.io/username/myapp:latest
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.myapp.rule=Host(`app.example.com`)"
      - "traefik.http.routers.myapp.entrypoints=websecure"
      - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
    restart: unless-stopped
```

### End-to-End Deployment Flow

1. **Development** — Build your feature and tag a release: `git tag 1.0.1 && git push --tags`
2. **CI/CD** — GitHub Actions automatically builds and pushes a new image to `ghcr.io`
3. **Detection** — Watchtower notices the new image is available in the registry
4. **Deployment** — New container is deployed with zero manual intervention
5. **Routing** — Traefik automatically routes traffic to the new container

> This entire system requires **zero manual server interaction** after initial setup. Just tag your code and everything else happens automatically.

---

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com/)
- [Traefik Official Documentation](https://doc.traefik.io/traefik/)
- [Watchtower GitHub Repository](https://containrrr.dev/watchtower/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
