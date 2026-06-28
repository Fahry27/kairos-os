# Zima OS (CasaOS) Deployment Guide

Kairos v1.1.0 includes a production-leaning `docker-compose.yml` file located at the repository root. This makes it straightforward to deploy on Zima OS (CasaOS) or any other Docker-based homelab environment.

## Deployment Steps

1. **Access your Zima OS Dashboard**
   Open your Zima OS dashboard in your browser.

2. **Open the App Center / Custom Install**
   Navigate to the option to install a custom app or use Docker Compose.

3. **Import `docker-compose.yml`**
   Copy the contents of the `docker-compose.yml` file from the root of this repository.

4. **Adjust Volumes (Optional)**
   The compose file maps `./data:/app/data` for the API. In Zima OS, you might want to map this to a specific location on your storage drive (e.g., `/DATA/AppData/kairos/data:/app/data`) to ensure persistent data is easily accessible and backed up.

5. **Deploy**
   Click deploy. Zima OS will pull the required images (or build them if configured to do so) and start the containers.

6. **Access Kairos**
   - The Kairos Dashboard will be available on port `3000`.
   - The Kairos API will be available on port `8000`.

## Updating

To update, simply pull the latest changes from the repository and recreate the containers in Zima OS. Because the SQLite database is stored in the mounted `data` volume, your projects, tasks, and memories will persist across updates.
