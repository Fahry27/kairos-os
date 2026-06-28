# Portainer Stack Deployment Guide

This guide explains how to deploy Kairos v1.9.0 as a Docker Stack inside Portainer.

## Prerequisites
- Portainer instance running and managed.
- Network connection between Portainer nodes and the rest of your local area network (LAN).

## Step-by-Step Stack Deployment

### 1. Configure the Stack
Because Portainer Stacks are deployed in a virtual context, relative bind mounts like `./data:/app/data` will fail or map to arbitrary host paths. To prevent this, you should modify the volume mount to use a Docker-managed named volume.

1. Open Portainer and go to **Stacks** > **Add stack**.
2. Name the stack (e.g., `kairos`).
3. Under the **Web editor**, copy the contents of the main [docker-compose.yml](file:///Users/fahry/Projects/kairos/docker-compose.yml).
4. Edit the volume config for the `kairos-api` service:
   ```yaml
       volumes:
         # Comment out the direct direct bind mount:
         # - ./data:/app/data
         # Uncomment the named volume mount:
         - kairos_data:/app/data
   ```
5. Scroll to the bottom of the editor and uncomment the root-level volume definitions:
   ```yaml
   volumes:
     kairos_data:
       name: kairos_data
   ```

### 2. Configure Environment Variables
In the Portainer Web editor, you can add Environment Variables below the compose box. Add these key-value configurations:

| Variable | Recommended Value | Description |
| :--- | :--- | :--- |
| `KAIROS_API_KEY` | `your-secure-key` | Protects the API routes (projects, tasks, memories) |
| `NEXT_PUBLIC_KAIROS_API_KEY` | `your-secure-key` | Must match `KAIROS_API_KEY` above |
| `NEXT_PUBLIC_KAIROS_API_URL` | `http://<API_CONTAINER_IP>:8000` | Replace with the actual LAN IP or stack container name |

For a complete reference of all required and optional environment variables (including CORS settings, root path prefixes, and startup validation audits), please refer to the [Configuration & Secrets Guide](configuration.md).

> [!NOTE]
> Within the same Portainer stack, services share a default network. You can set `NEXT_PUBLIC_KAIROS_API_URL` to `http://kairos-api:8000` for container-to-container communication. However, since the dashboard client runs in the user's browser, **you must use the external LAN IP/hostname of the host machine** (e.g., `http://192.168.1.100:8000` or `http://kairos-api.local:8000`) so the client browser can resolve it.

### 3. Deploy the Stack
Click **Deploy the stack**. Portainer will pull the images, construct the network, create the named volume, and run the containers.

---

## Updating and Redeploying

To update the stack to a newer version of Kairos:
1. Go to **Stacks** > **kairos** > **Editor**.
2. Update any configurations or environment variables.
3. Turn on the **Update the stack** toggle.
4. Check **Prune obsolete volumes** if needed, but **DO NOT** delete the active `kairos_data` volume to avoid losing your database.
5. Click **Update** to trigger an image pull and containers restart.

---

## Troubleshooting

### 1. CORS Origin Errors
If you see console errors in the browser when writing or reading from the API:
- Configure `CORS_ORIGINS` environment variable on the `kairos-api` service to explicitly include the domain/IP of the dashboard.
- Example: `CORS_ORIGINS='["http://192.168.1.100:3000","http://kairos.local"]'`.

### 2. Accessing Logs
- Go to **Containers** in Portainer.
- Click the logs icon next to `kairos-api` or `kairos-dashboard`.
- Unified logs will be visible in standard structured format: `[TIMESTAMP] [LEVEL] [LOGGER] MESSAGE`.

### 3. Database is locked / Read-Only Errors
If SQLite prints database lock errors:
- Ensure only one instance of the `kairos-api` container is running (do not scale the service above 1 replica since SQLite does not support concurrent write operations across multiple running instances).
