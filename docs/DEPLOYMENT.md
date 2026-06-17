<!-- generated-by: gsd-doc-writer -->
# Deployment Documentation

This document describes how to deploy the Sports TV App backend to production.

## Deployment Targets

The backend FastAPI service supports two main deployment strategies:
1. **AWS EC2 (Docker Compose) - Currently Active:** Packs the application, Python dependencies, and Playwright browsers inside a Docker container. Easiest for managing Playwright dependencies and running on standard virtual servers.
2. **Render (Native Python & Postgres) - Alternative:** Automatically provisions builds and PostgreSQL databases based on [render.yaml](file:///D:/projects/sports_tv/render.yaml).

---

## 1. AWS EC2 Deployment (Docker Compose)

### Host Server Setup
To deploy on an AWS EC2 instance (Ubuntu 22.04 LTS or newer), configure the instance to allow incoming HTTP traffic on port **80**.

During launch, you can use this User Data script to initialize the host:
```bash
#!/bin/bash
apt-get update
apt-get install -y docker.io docker-compose git
systemctl start docker
systemctl enable docker
git clone https://github.com/sanket-gr/sports_tv.git /app
cd /app/backend
docker-compose up -d
```

### Pulling Updates to the EC2 Server
When you push new backend features or fixes to GitHub, update the server with these commands:
```bash
# 1. Navigate to the project root
cd /app

# 2. Fetch the latest code changes from GitHub
sudo git fetch --all
sudo git reset --hard origin/main

# 3. Rebuild and restart the container
cd /app/backend
sudo docker compose down
sudo docker compose build --no-cache
sudo docker compose up -d
```

<!-- VERIFY: AWS EC2 public IPv4 address and Security Group port 80 rule -->

---

## 2. Render Deployment (Native Python + Postgres)

Render uses the [render.yaml](file:///D:/projects/sports_tv/render.yaml) file to define the build pipeline:

* **Build Command:** `pip install -r requirements.txt && playwright install chromium && playwright install-deps chromium` (Installs python packages, Playwright binaries, and Linux system dependencies).
* **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
* **Database:** Automatically spins up a PostgreSQL database instance and injects the `DATABASE_URL` environment variable.

To deploy:
1. Connect your GitHub repository to **Render**.
2. Create a new Blueprints project. Render will read `render.yaml` and provision the database and web service automatically.

---

## Production Environment Setup

Ensure the following variables are configured in your production environment (e.g. under the `environment` section of `docker-compose.yml` or Render dashboard):
* `ENVIRONMENT=production` (Enables JSON logging format)
* `DATABASE_URL=sqlite:///./db/sports_tv.db` (For persistent SQLite Docker storage) or your PostgreSQL connection string.

<!-- VERIFY: Database backup schedules and volume mount permissions -->

---

## Monitoring and Logs

* **AWS/Docker Logs:** Monitor application console outputs and scraping processes:
  ```bash
  sudo docker compose logs -f
  ```
* **Production Logs Format:** When `ENVIRONMENT=production` is active, the app uses `pythonjsonlogger` to format logs as structured JSON, making them ready for cloud log aggregators (CloudWatch, Datadog, etc.).

## Rollback Procedure

If a deployed version causes errors in production:
1. Revert the commit on GitHub.
2. Log into the EC2 server and pull the stable commit:
   ```bash
   cd /app
   sudo git pull
   cd /app/backend
   sudo docker compose down
   sudo docker compose up -d --build
   ```
