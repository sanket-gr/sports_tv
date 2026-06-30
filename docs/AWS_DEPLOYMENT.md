# AWS Deployment Guide — Sports TV Backend

This document covers how to deploy the backend (FastAPI + FlareSolverr) to AWS.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│  AWS ECS Task  (or EC2 Docker Compose)                   │
│                                                          │
│  ┌──────────────────┐    http://localhost:8191           │
│  │  sportstv_backend│ ──────────────────────────────────►│
│  │  (FastAPI)       │                                    │
│  │  :8000           │◄─────────── cookies + html ────────│
│  └──────────────────┘                                    │
│                          ┌──────────────────────┐        │
│                          │  flaresolverr         │        │
│                          │  (CF bypass sidecar)  │        │
│                          │  :8191               │        │
│                          └──────────────────────┘        │
└──────────────────────────────────────────────────────────┘
```

---

## Option 1 — EC2 with Docker Compose (Simplest)

### 1. Launch an EC2 instance
- AMI: Amazon Linux 2023 or Ubuntu 22.04
- Instance type: **t3.small** minimum (FlareSolverr needs ~512 MB RAM)
- Security group: open port 80 inbound (and 8191 if you want to debug FlareSolverr directly)

### 2. Install Docker Engine + Compose plugin (Ubuntu/Debian)
```bash
# Remove any old versions
sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# Install prerequisites
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg

# Add Docker's official GPG key + repo
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu \
$(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine + Compose plugin
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start Docker and add your user to the docker group (re-login after this)
sudo systemctl enable --now docker
sudo usermod -aG docker ubuntu
newgrp docker   # apply group change without re-login
```

> **Note**: The modern command is `docker compose` (with a space, as a plugin), NOT `docker-compose` (hyphen, the old standalone tool). Both work identically otherwise.

### 3. Clone and start
```bash
git clone <your-repo-url> sports_tv
cd sports_tv/backend

# Use 'docker compose' (plugin syntax — no hyphen)
docker compose pull        # pulls latest flaresolverr image
docker compose up -d       # starts both containers

# Watch logs
docker compose logs -f
```

---

## Option 2 — AWS ECS (Two-Container Task)

### Task Definition (JSON snippet)
Add both containers to your ECS task definition:

```json
{
  "containerDefinitions": [
    {
      "name": "flaresolverr",
      "image": "ghcr.io/flaresolverr/flaresolverr:latest",
      "portMappings": [{ "containerPort": 8191, "protocol": "tcp" }],
      "environment": [
        { "name": "LOG_LEVEL", "value": "info" }
      ],
      "essential": true
    },
    {
      "name": "backend",
      "image": "<your-ecr-repo>/sports-tv-backend:latest",
      "portMappings": [{ "containerPort": 8000, "protocol": "tcp" }],
      "dependsOn": [{ "containerName": "flaresolverr", "condition": "START" }],
      "environment": [
        { "name": "FLARESOLVERR_URL",  "value": "http://localhost:8191" },
        { "name": "DATABASE_URL",       "value": "<your-db-connection-string>" },
        { "name": "ADMIN_USERNAME",     "value": "admin" },
        { "name": "ADMIN_PASSWORD",     "value": "<secure-password>" }
      ],
      "essential": true
    }
  ],
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048"
}
```

> **Note**: Both containers share `localhost` when using `awsvpc` network mode in a single task, so `http://localhost:8191` resolves correctly.

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `FLARESOLVERR_URL` | ✅ on AWS | `http://localhost:8191` | URL of the FlareSolverr instance |
| `DATABASE_URL` | ✅ | `sqlite:///./db/sports_tv.db` | SQLAlchemy DB connection string |
| `ADMIN_USERNAME` | ⚠️ | _(none — no auth)_ | Admin panel username |
| `ADMIN_PASSWORD` | ⚠️ | _(none — no auth)_ | Admin panel password |
| `SCRAPER_PROXY` | ❌ | _(none)_ | Optional residential proxy (`http://user:pass@host:port`) as extra bypass layer |

---

## Verifying FlareSolverr is Working

```bash
# From the EC2 instance or another container in the same task
curl -s -X POST http://localhost:8191/v1 \
  -H "Content-Type: application/json" \
  -d '{"cmd": "request.get", "url": "https://partner.nonamejose.sx/", "maxTimeout": 60000}' \
  | python3 -m json.tool | head -30
```

Expected response contains `"status": "ok"` and a `solution.cookies` array.

---

## Troubleshooting

### No HLS found even with FlareSolverr running
- Check FlareSolverr logs: `docker logs sportstv_flaresolverr`
- If you see `"status": "error"` with a Turnstile/CAPTCHA message, the stream site upgraded to Cloudflare Turnstile which FlareSolverr cannot bypass automatically. In this case, add `SCRAPER_PROXY` to use a residential IP.
- Increase `maxTimeout` in `flaresolverr_client.py` if the challenge is slow.

### FlareSolverr container exits immediately
- It needs `SYS_ADMIN` capability on some Linux kernels for Chrome sandbox. Add to your docker-compose:
  ```yaml
  cap_add:
    - SYS_ADMIN
  ```

### Render.com
Render does not support multi-container deployments on a single service. Workarounds:
1. Deploy FlareSolverr as a separate Render **Private Service**, then set `FLARESOLVERR_URL` to its internal URL.
2. Switch to EC2 or ECS (recommended for production streaming use-cases).
