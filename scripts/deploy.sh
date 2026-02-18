#!/usr/bin/env bash
# =============================================================
# deploy.sh — Reusable deploy script for crypto-dash
# Usage: ./scripts/deploy.sh [deploy_path]
# =============================================================
set -euo pipefail

DEPLOY_PATH="${1:-/root/projects/crypto-dash}"
HEALTH_URL="http://localhost/api/health"
HEALTH_RETRIES=6
HEALTH_INTERVAL=10

echo "========================================"
echo "  crypto-dash deploy — $(date -u)"
echo "  Path: $DEPLOY_PATH"
echo "========================================"

cd "$DEPLOY_PATH"

# --- 1. Pull latest code ---
echo "[1/4] git pull origin main..."
git fetch origin main
git reset --hard origin/main

# --- 2. Build images ---
echo "[2/4] docker compose build..."
docker compose build --pull

# --- 3. Start / update services ---
echo "[3/4] docker compose up -d..."
docker compose up -d --remove-orphans

# --- 4. Health check ---
echo "[4/4] Health check ($HEALTH_RETRIES attempts × ${HEALTH_INTERVAL}s)..."
for i in $(seq 1 $HEALTH_RETRIES); do
    sleep $HEALTH_INTERVAL
    if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
        echo "✅ Health check passed (attempt $i)"
        echo "========================================"
        echo "  Deploy SUCCESS — $(date -u)"
        echo "========================================"
        exit 0
    fi
    echo "  ⏳ Attempt $i/$HEALTH_RETRIES failed, retrying..."
done

echo "❌ Health check failed after $HEALTH_RETRIES attempts"
echo "   Check: docker compose logs"
exit 1
