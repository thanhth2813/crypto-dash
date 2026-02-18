# CD Pipeline — Setup Guide

## GitHub Repository Secrets

Go to: **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Description | Example |
|--------|-------------|---------|
| `SSH_PRIVATE_KEY` | Private SSH key for VPS access | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `VPS_HOST` | VPS IP or hostname | `123.45.67.89` |
| `VPS_USER` | SSH username | `ubuntu` |
| `VPS_PORT` | SSH port (default 22) | `22` |
| `VPS_DEPLOY_PATH` | App directory on VPS | `/opt/crypto-dash` |

## VPS Initial Setup

Run once on the VPS:

```bash
# 1. Install Docker + Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 2. Clone repo
sudo mkdir -p /opt/crypto-dash
sudo chown $USER:$USER /opt/crypto-dash
cd /opt/crypto-dash
git clone https://github.com/thanhth2813/crypto-dash.git .

# 3. Create .env from example
cp .env.example .env
# → Edit .env with production values (strong passwords, secrets)

# 4. Add deploy user's SSH public key to authorized_keys
# (use the corresponding public key of SSH_PRIVATE_KEY secret)
```

## How CD Works

```
push to main
     │
     ▼
build-push job
  ├── Build backend image → ghcr.io/thanhth2813/crypto-dash-backend:<sha>
  └── Build frontend image → ghcr.io/thanhth2813/crypto-dash-frontend:<sha>
     │
     ▼
deploy job (SSH to VPS)
  ├── git pull (latest docker-compose.yml)
  ├── docker compose pull (new images)
  ├── docker compose up -d
  ├── health check → curl localhost/api/health (5 retries × 10s)
  │     ├── PASS → save image tag, exit 0
  │     └── FAIL → rollback to previous tag, exit 1
```

## Rollback

Automatic: if health check fails after deploy, CD reverts to the last known-good image tag.

Manual rollback:
```bash
ssh user@vps
cd /opt/crypto-dash
export IMAGE_TAG=<previous-sha>
docker compose up -d
```

## Image Registry

Images are stored at:
- `ghcr.io/thanhth2813/crypto-dash-backend:<sha>`
- `ghcr.io/thanhth2813/crypto-dash-frontend:<sha>`
