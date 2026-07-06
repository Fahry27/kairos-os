# Deploying Kairos to kairosos.xyz

This guide covers deploying Kairos behind your custom domain using Docker Compose
and Cloudflare Tunnel.

## Prerequisites

- A domain name (e.g., `kairosos.xyz`) with DNS managed by Cloudflare
- A server or machine running Docker and Docker Compose
- Git installed

## Step 1: Clone and Configure

```bash
git clone https://github.com/Fahry27/kairos-os.git
cd kairos-os
```

Copy and edit the environment file:

```bash
cp .env.example .env
```

Set these variables in `.env`:

```bash
# Optional: if API and dashboard are on the same domain, leave empty
# The dashboard will auto-detect the API from window.location.origin
NEXT_PUBLIC_KAIROS_API_URL=

# Optional API key for protected access
KAIROS_API_KEY=your-secure-random-key

# Production mode
APP_ENV=production

# For Cloudflare Tunnel deployment
CLOUDFLARE_TUNNEL_TOKEN=your-tunnel-token
```

## Step 2: Set Up Cloudflare Tunnel

1. Go to [Cloudflare Zero Trust](https://one.dash.cloudflare.com/)
2. Navigate to **Networks → Tunnels**
3. Click **Create a tunnel**
4. Name it `kairos`
5. Choose **Docker** as the environment
6. Copy the tunnel token shown
7. Set `CLOUDFLARE_TUNNEL_TOKEN` in your `.env` file

In the Cloudflare Tunnel configuration (Public Hostname tab):

| Subdomain | Service |
|---|---|
| `kairosos.xyz` | `http://kairos-dashboard:3000` |
| (or reverse-proxy both services through one domain) | |

## Step 3: Start Kairos

```bash
docker compose up -d
```

The dashboard will be available at `http://localhost:3000` locally, and at
your domain if Cloudflare Tunnel is configured.

## API URL Resolution

The dashboard resolves the API URL in this order:

1. `NEXT_PUBLIC_KAIROS_API_URL` environment variable
2. `window.location.origin` (auto-detect, works when served from the same origin)
3. Falls back to `http://localhost:8000`

For `kairosos.xyz` with both services behind the same domain (recommended),
leave `NEXT_PUBLIC_KAIROS_API_URL` empty and use a reverse proxy or tunnel
to route:

- `/` → dashboard (port 3000)
- `/api/*` → API (port 8000)

## CORS Configuration

The API allows these origins by default:

```
http://localhost:3000
http://127.0.0.1:3000
https://kairosos.xyz
https://www.kairosos.xyz
```

Override via `CORS_ORIGINS` in `.env` if you use a different domain.

## Provider Configuration

After deployment, configure AI providers in Settings → AI:

1. Open the dashboard
2. Go to **Settings → AI**
3. Click **Configure** on any provider
4. Paste your API key

Provider keys are stored in your browser's localStorage only and never sent
to the Kairos server.

## Health Check

```bash
# API health
curl http://localhost:8000/health

# Provider status
curl http://localhost:8000/api/v1/ai/provider-router/providers
```
