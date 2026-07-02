# Zima OS (CasaOS) Deployment Guide

Kairos v3.1.0 includes a production-leaning `docker-compose.yml` file located at the repository root. This makes it straightforward to deploy on Zima OS (CasaOS) or any other Docker-based homelab environment.

## Prerequisites
- Zima OS / CasaOS installed and running on your local network.
- Access to the Zima OS terminal or file system (via SSH or Files app).
- Git installed on your Zima OS machine (or you can manually copy the repository files).

## Initial Setup

1. **Clone the Repository to Zima OS**
   SSH into your Zima OS device or use the terminal.
   ```sh
   git clone https://github.com/your-username/kairos.git /DATA/AppData/kairos
   cd /DATA/AppData/kairos
   ```

2. **Create Data Directory**
   Ensure the `data` directory exists for SQLite persistence.
   ```sh
   mkdir -p data
   ```

3. **Configure Environment Variables & Security Hardening (Optional but Recommended)**
   Copy the provided Zima OS environment example:
   ```sh
   cp .env.zima.example .env
   ```
   Edit `.env` and replace `<ZIMA_IP>` with your actual NAS IP address (e.g., `192.168.1.100`) so the dashboard can communicate with the API over the LAN:
   ```text
   NEXT_PUBLIC_KAIROS_API_URL=http://192.168.1.100:8000
   ```

   To secure your Kairos instance from unauthorized access on your local area network (LAN), you can configure a local API key:
   - Edit `.env` and set `KAIROS_API_KEY` to a strong secret key (e.g., `KAIROS_API_KEY=your_secure_key`).
   - Set `NEXT_PUBLIC_KAIROS_API_KEY` to the exact same value (e.g., `NEXT_PUBLIC_KAIROS_API_KEY=your_secure_key`) so the dashboard can authenticate.

   > [!IMPORTANT]
   > **LAN Security Warning**: This local API key authentication is designed for private local network (LAN) security. The key is transmitted from the browser to the API. It is **not** designed for exposure over the public internet, which would require HTTPS and reverse proxies. Never expose the dashboard or API ports directly to the internet without proper TLS encryption and standard edge routing.
   > Replace placeholder API keys, dashboard keys, operator tokens, and webhook URLs with deployment-specific values before exposing Kairos beyond local development.
   > Restrict `CORS_ORIGINS` to the exact dashboard origins before exposing Kairos beyond a private LAN.

4. **Deploy with Docker Compose**
   Start the services in detached mode:
   ```sh
   docker compose up -d --build
   ```

5. **Verify the Deployment**
    - **Check Containers**: `docker compose ps`
    - **Check API Health**: From another device on your network, open `http://<ZIMA_IP>:8000/health`. You should see version `3.1.0` in the returned JSON.
    - **Open Dashboard**: From another device, open `http://<ZIMA_IP>:3000`.
    - **Review Approvals**: Use the Approval Management card to view and inspect approval requests. Approving requests remains metadata-only and does not execute commands, call connectors, trigger n8n/Hermes/OpenClaw, call cloud providers, or mutate domain data.
    - **Controlled n8n Trigger**: If enabled privately, save the operator token in the dashboard's browser-local token field, then trigger only approved n8n workflow approvals from the approval detail pane or `POST /api/v1/approvals/{approval_id}/trigger-n8n`. Do not place operator tokens or webhook URLs in dashboard variables.
    - **Workflow Run History**: Use the Workflow Runs card to inspect sanitized trigger history and latest run status.
    - **Production Acceptance Baseline**: v3.0.0 was accepted after verifying API and dashboard availability, Swagger dual auth, n8n env wiring, production webhook reachability, `trigger-n8n` success, and a sanitized `WorkflowRun` with `status=succeeded`.
    - **Verified End-to-End Flow**: `Approval approved -> trigger-n8n -> n8n webhook -> WorkflowRun succeeded`.

## Stopping and Restarting

To stop the containers without losing data:
```sh
docker compose down
```

To restart them:
```sh
docker compose up -d
```

## Updating Kairos

To update to the latest version while keeping your data:
```sh
cd /DATA/AppData/kairos
git pull
docker compose up -d --build
```
Your projects, tasks, and memories will persist across updates because they are stored in the mounted `data` volume.

## Backing Up and Restoring

### Backup Automation via Cron
Kairos stores all your data in a local SQLite file. You can run manual backups:
```sh
./scripts/backup-sqlite.sh
```
This script saves database backups in `backups/` using UTC timestamps, and enforces a retention policy keeping exactly the latest 14 backups.

To automate database backups on your Zima OS host, you can set up a system cron job:
1. Open the cron editor on the Zima OS host via SSH:
   ```sh
   crontab -e
   ```
2. Add a cron job to run the backup script daily (e.g., at 2:00 AM):
   ```text
   0 2 * * * /DATA/AppData/kairos/scripts/backup-sqlite.sh >> /DATA/AppData/kairos/backups/backup.log 2>&1
   ```
3. Save and close the editor. The script logs backup execution success, failures, and retention cleanup directly to stdout (redirected to `backup.log` in this example).

### Restore
To restore from a backup:
1. Stop the containers: `docker compose down`
2. Replace the active database file: `cp backups/kairos-local_TIMESTAMP.sqlite3 data/kairos-local.sqlite3`
3. Restart the containers: `docker compose up -d`

## Operations Monitoring & Logs

### Docker Log Locations
By default, Docker container logs are outputted directly to standard output/error and captured by the `json-file` driver. To view logs:
- **API logs**: `docker compose logs -f kairos-api` (or `docker logs -f kairos-api`)
- **Dashboard logs**: `docker compose logs -f kairos-dashboard` (or `docker logs -f kairos-dashboard`)

These logs follow a structured, unified formatting: `[TIMESTAMP] [LEVEL] [LOGGER] MESSAGE` to make parsing straightforward.

### Operational Endpoints
- **Health check (`/health` / `/api/v1/health`)**: Public endpoints confirming service version, uptime, database connectivity, and docker environment.
- **Readiness check (`/ready` / `/api/v1/ready`)**: Verifies filesystem write accessibility (e.g., database path, backups directory, data directory) and database responsiveness.
- **Metrics check (`/metrics` / `/api/v1/metrics`)**: Exposes JSON stats covering uptime, request counts, and HTTP status code distribution (2xx, 3xx, 4xx, 5xx).

---

## Operational Checklist

For a production Zima OS deployment, verify:
- [ ] **Docker Log Rotation**: Logging drivers limits (`max-size: 10m`, `max-file: 3`) are active in `docker-compose.yml` to prevent filling Zima OS system disk.
- [ ] **Backups Cron Job**: The backup cron job is registered, active, and permissions on `scripts/backup-sqlite.sh` are set to executable.
- [ ] **LAN Access API Keys**: `KAIROS_API_KEY` (in API service environment) and `NEXT_PUBLIC_KAIROS_API_KEY` (in dashboard environment) are configured and matching.
- [ ] **Readiness status**: Accessing `http://<ZIMA_IP>:8000/ready` returns `"status": "ready"`.
- [ ] **Approval safety**: Approval Management loads or shows a safety-gated unavailable state when `KAIROS_APPROVAL_GATE_ENABLED=false`; no execution layer is enabled by approvals.
- [ ] **Restart Policy**: Restart policies (`unless-stopped`) are defined for all containers in the compose file.

## Advanced Deployment Options

For advanced homelab setups, you can deploy Kairos behind a reverse proxy or within Portainer:
- Refer to the [Configuration & Secrets Guide](configuration.md) to manage environment variables, validate settings, and perform secret rotation.
- Refer to the [Reverse Proxy & HTTPS Setup Guide](reverse-proxy.md) to set up local DNS routing (e.g., `kairos.local`) with TLS certificates.
- Refer to the [Portainer Stack Deployment Guide](portainer.md) to deploy Kairos via a Portainer stack configuration with named volume persistence.

## Known Limitations

- **Local API Key Security**: While Kairos now supports local API key authentication, it does not include full user accounts or fine-grained role-based permissions.
- **LAN-Only Recommended**: Even with API key authentication enabled, **do not** expose Kairos ports directly to the public internet. It is designed for private local network (LAN) access. Any remote access should be managed via a secure VPN (like Tailscale) or behind a hardened reverse proxy with HTTPS.
