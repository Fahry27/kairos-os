# Cloudflare Tunnel Remote Access

Kairos uses Cloudflare Tunnel to provide secure remote access without exposing ports publicly. This document explains how to set it up.

## Prerequisites

1. A Cloudflare account
2. A domain name managed in Cloudflare
3. Cloudflare Zero Trust configured

## Setup Instructions

1. Go to the **Cloudflare Zero Trust** dashboard.
2. Navigate to **Networks** -> **Tunnels**.
3. Create a new tunnel (select **Cloudflared** as the connector type).
4. Name your tunnel (e.g., `kairos-zimaos`).
5. Copy the generated Tunnel Token.

## Configuration

In your deployment environment (e.g., ZimaOS), you need to provide the Tunnel Token to the docker-compose setup.
Create or update your `.env` file in the root of the Kairos repository:

```env
CLOUDFLARE_TUNNEL_TOKEN=your-tunnel-token-here
```

## Routing Configuration (Cloudflare Dashboard)

Once the tunnel is connected (the `kairos-cloudflared` container is running), you must add public hostnames for your services:

1. In the Tunnel settings, go to the **Public Hostname** tab.
2. Add a hostname for the Dashboard:
   - Subdomain: `kairos` (or whatever you prefer)
   - Domain: `yourdomain.com`
   - Service: `http://kairos-dashboard:3000`
3. (Optional) Add a hostname for the API if you want it accessible directly:
   - Subdomain: `kairos-api`
   - Domain: `yourdomain.com`
   - Service: `http://kairos-api:8000`

## Verification

Run the following command to ensure the `cloudflared` service starts without errors:
```bash
docker compose logs -f cloudflared
```
You should see output indicating that the connection to Cloudflare's edge was successful.
