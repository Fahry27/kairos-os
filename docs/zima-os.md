# Zima OS (CasaOS) Deployment Guide

Kairos v1.2.0 includes a production-leaning `docker-compose.yml` file located at the repository root. This makes it straightforward to deploy on Zima OS (CasaOS) or any other Docker-based homelab environment.

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

3. **Configure Environment Variables (Optional but Recommended)**
   Copy the provided Zima OS environment example:
   ```sh
   cp .env.zima.example .env
   ```
   Edit `.env` and replace `<ZIMA_IP>` with your actual NAS IP address (e.g., `192.168.1.100`) so the dashboard can communicate with the API over the LAN:
   ```text
   NEXT_PUBLIC_KAIROS_API_URL=http://192.168.1.100:8000
   ```

4. **Deploy with Docker Compose**
   Start the services in detached mode:
   ```sh
   docker compose up -d --build
   ```

5. **Verify the Deployment**
   - **Check Containers**: `docker compose ps`
   - **Check API Health**: From another device on your network, open `http://<ZIMA_IP>:8000/health`. You should see `{"status":"ok","service":"kairos-api","version":"1.2.0"}`.
   - **Open Dashboard**: From another device, open `http://<ZIMA_IP>:3000`.

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

### Backup
Kairos stores all your data in a local SQLite file. You can back it up easily using the provided script:
```sh
./scripts/backup-sqlite.sh
```
This will copy `data/kairos-local.sqlite3` into the `backups/` directory with a timestamp.

### Restore
To restore from a backup:
1. Stop the containers: `docker compose down`
2. Replace the active database file: `cp backups/kairos-local_TIMESTAMP.sqlite3 data/kairos-local.sqlite3`
3. Restart the containers: `docker compose up -d`

## Known Limitations

- **No Authentication**: The current version of Kairos does not have built-in user authentication.
- **LAN-Only Recommended**: Because there is no authentication, **do not** expose Kairos publicly to the internet via port forwarding or a reverse proxy. It is designed for private local network (LAN) access only. Future updates will introduce authentication for secure remote access.
