# Reverse Proxy & HTTPS Deployment Guide

This guide explains how to secure and expose your Kairos v1.5.0 instance on your Local Area Network (LAN) behind a reverse proxy (e.g., Caddy or Traefik).

## Security Warning

> [!WARNING]
> **LAN-Only Recommended**: The current API key authentication is designed for private local network (LAN) access. Do **not** expose your Kairos dashboard or API ports directly to the public internet using port forwarding or public DNS routing before stronger security (like full OAuth/OAuth2, OpenID, or VPN gateways) is implemented.

---

## Reverse Proxy Routing Options

Because the dashboard runs client-side inside the user's web browser, the browser must be able to resolve both the dashboard and the API endpoints. The safest supported approach is routing them on separate domains or port addresses:

### Recommended Domain Allocation
- **Dashboard Domain**: `kairos.local` (proxies to port `3000`)
- **API Domain**: `kairos-api.local` (proxies to port `8000`)

---

## Configuration Examples

### 1. Caddy (Recommended)
Caddy automatically handles local TLS certificate generation using its internal local Certificate Authority (CA).

Add the following to your `Caddyfile` on your host or reverse proxy container:

```caddy
# Dashboard Router
kairos.local, kairos.fahry.local {
    reverse_proxy localhost:3000
}

# API Router
kairos-api.local {
    reverse_proxy localhost:8000
}
```

When you first navigate to `https://kairos.local`, your browser may show a certificate warning. Follow Caddy's prompts to trust Caddy's root CA on your local machine to enable green padlock HTTPS access on your LAN.

### 2. Traefik
Below is a dynamic configuration block (file provider) for Traefik routing to Kairos:

```yaml
http:
  routers:
    kairos-dashboard:
      rule: "Host(`kairos.local`) || Host(`kairos.fahry.local`)"
      service: dashboard-service
      entryPoints:
        - web
    kairos-api:
      rule: "Host(`kairos-api.local`)"
      service: api-service
      entryPoints:
        - web

  services:
    dashboard-service:
      loadBalancer:
        servers:
          - url: "http://localhost:3000"
    api-service:
      loadBalancer:
        servers:
          - url: "http://localhost:8000"
```

---

## Necessary Environment Variables

To ensure the backend understands request parameters and origins coming from a reverse proxy:

1. **Uvicorn Proxy Trust**:
   To trust the `X-Forwarded-For`, `X-Forwarded-Proto`, and `X-Forwarded-Host` headers passed by Caddy/Traefik, ensure the following are configured on the `kairos-api` service (active by default in `docker-compose.yml`):
   - `UVICORN_PROXY_HEADERS=true`
   - `UVICORN_FORWARDED_ALLOW_IPS=*`

2. **CORS Origins**:
   You must update the `CORS_ORIGINS` environment variable on `kairos-api` to accept requests originating from the dashboard's reverse proxy domains.
   - Example: `CORS_ORIGINS='["http://kairos.local","https://kairos.local","http://kairos.fahry.local","https://kairos.fahry.local"]'`

3. **Dashboard API Endpoint**:
   Ensure `NEXT_PUBLIC_KAIROS_API_URL` on `kairos-dashboard` points to the API domain address that is accessible to the user's browser:
   - Example: `NEXT_PUBLIC_KAIROS_API_URL=https://kairos-api.local` (or `http://kairos-api.local` if running over HTTP).
