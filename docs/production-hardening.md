# Production Hardening Notes

This document covers practical security improvements for the Traefik VPS setup in this repository. It is intentionally biased toward small self-hosted deployments that want better security without turning into a full platform engineering project.

The current stack is a reasonable starting point, but it still exposes a public reverse proxy, mounts the Docker socket, and includes a demo service. If the deployment matters, treat the items below as a hardening backlog rather than optional reading.

## Highest-Value Easy Lifts

### 1. Restrict Dashboard Access By IP

The Traefik dashboard should not be broadly internet-accessible. Basic auth helps, but it should not be the only control.

An easy lift is to add an IP allowlist middleware so only your home IP, office IP, VPN subnet, or bastion can reach the dashboard router.

Example labels for the `traefik` service:

```yaml
labels:
  - "traefik.http.middlewares.dashboard-allow.ipallowlist.sourcerange=203.0.113.10/32,198.51.100.0/24"
  - "traefik.http.routers.dashboard.middlewares=dashboard-allow@docker,dashboard-auth@docker"
```

Notes:

- Replace the example CIDRs with real trusted source ranges.
- If your public IP changes often, put the dashboard behind a VPN instead of chasing allowlist updates.
- If you later place Traefik behind another proxy or CDN, make sure you understand which source IP Traefik actually sees before relying on IP rules.

### 2. Lock Down Host Firewall Rules

On the VPS, expose only what must be public:

- `80/tcp` for the ACME HTTP challenge or redirect handling
- `443/tcp` for HTTPS traffic
- `22/tcp` only from trusted admin IPs if possible

Example `ufw` shape:

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow from YOUR_PUBLIC_IP to any port 22 proto tcp
sudo ufw enable
```

Do the same at the cloud firewall or security-group layer. The VPS firewall and the provider firewall should agree.

### 3. Remove Demo Routes From Real Deployments

The `whoami` service is useful for validating routing, but it should not stay enabled on a real public deployment unless you actively need it.

If you are deploying an actual app, remove the `whoami` service and its public route from the production stack.

### 4. Use A Separate Dashboard Hostname

The current stack supports both `dashboard.example.com` and `example.com/dashboard`. For a real deployment, it is cleaner to keep the dashboard on a dedicated hostname and avoid exposing it on the main site hostname at all.

That reduces accidental discovery and keeps operational endpoints separate from user-facing traffic.

## Docker And Traefik Risks

### Docker Socket Exposure

This stack mounts `/var/run/docker.sock` into Traefik as read-only, which is better than read-write, but it is still a sensitive capability. Access to the Docker API is effectively high-privilege access to the host.

Practical guidance:

- Keep the host dedicated to Docker workloads when possible.
- Keep membership in the `docker` group extremely limited.
- Do not expose the Docker daemon over TCP unless it is protected with SSH or mutual TLS.
- Consider a Docker socket proxy later if you want tighter mediation between Traefik and the Docker API.

### Keep Traefik Current

Reverse proxies are internet-facing software. Keep the Traefik image updated and review release notes before major-version upgrades.

It is also worth periodically rebuilding and redeploying even when your app has not changed, so the host and image layers do not drift behind on security fixes.

### Reduce Container Privileges Where Possible

The Traefik service already sets `no-new-privileges:true`, which is a good baseline. For app containers you add later, also consider:

- Running as a non-root user where the image supports it
- Dropping unnecessary Linux capabilities
- Using a read-only filesystem where the app permits it
- Mounting only the volumes the app actually needs
- Setting memory and CPU limits so one container cannot exhaust the host

Not every app tolerates all of these, but they are worth evaluating rather than defaulting to a wide-open runtime profile.

## VPS And Linux Hardening

### SSH Hygiene

At minimum:

- Disable password authentication once key-based SSH access works
- Disable direct root login over SSH
- Use a dedicated non-root admin user with `sudo`
- Consider `fail2ban` or SSH rate limiting if the host is publicly reachable

### Keep The Base System Patched

The containers are only part of the security story. Regularly apply security updates to the VPS itself.

For Ubuntu, unattended security upgrades are often a reasonable default for a small server.

### Protect Files On Disk

Review permissions for deployment-sensitive files:

- `.env`
- `traefik/dynamic/dashboard-users.htpasswd`
- `traefik/letsencrypt/acme.json`

In particular, `acme.json` should not be world-readable. Restrict it to the deployment user and preserve it across restarts or host rebuilds.

## DNS, TLS, And Exposure Management

### Keep Port 80 Open For ACME

If you stay with Let's Encrypt's HTTP challenge flow, port `80` must remain reachable enough for certificate issuance and renewal.

If you later move behind a CDN, load balancer, or stricter firewall layout, re-check that certificate renewal still works.

### Add Monitoring For Certificate And Endpoint Failures

Do not rely on manual spot checks. Add at least lightweight monitoring for:

- TLS certificate expiration
- Reverse proxy availability
- Unexpected container restarts
- VPS disk usage, especially if logs or images accumulate

### Consider DNS CAA Records

CAA records can limit which certificate authorities may issue certificates for your domain. If you use Let's Encrypt, add a CAA record that explicitly allows it.

This is not mandatory for the stack to work, but it is a useful defense-in-depth control.

## A Reasonable Hardening Order

If you want a short implementation order for this repo, do these first:

1. Restrict SSH by IP at the cloud firewall and host firewall.
2. Add a Traefik IP allowlist or VPN gate for the dashboard.
3. Remove the public `whoami` route from real deployments.
4. Tighten file permissions for `.env`, `dashboard-users.htpasswd`, and `acme.json`.
5. Enable automatic security updates on the VPS.
6. Add basic uptime and certificate-expiry monitoring.

## References

- Traefik middleware docs: IP allow lists
- Docker Engine security overview
- Docker guidance on protecting daemon access
- Ubuntu firewall documentation
- Let's Encrypt operational documentation