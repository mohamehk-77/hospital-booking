#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

if [ ! -f Dockerfile ] || [ ! -f docker-compose.prod.yml ]; then
  echo "Run this script from the hospital-booking repository." >&2
  exit 1
fi

echo "==> Installing system packages"
sudo apt-get update -y
sudo apt-get install -y ca-certificates curl git openssl ufw

if ! command -v docker >/dev/null 2>&1; then
  echo "==> Installing Docker"
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER" || true
fi

echo "==> Configuring firewall"
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

if [ ! -f .env.prod ]; then
  echo
  read -r -p "DuckDNS domain (e.g. radyhospital.duckdns.org): " DOMAIN
  DOMAIN="${DOMAIN:-radyhospital.duckdns.org}"

  SECRET_KEY="$(openssl rand -hex 32)"
  POSTGRES_PASSWORD="$(openssl rand -hex 16)"

  umask 077
  cat > .env.prod <<EOF
DOMAIN=$DOMAIN
SECRET_KEY=$SECRET_KEY
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
EOF
  echo "==> Wrote .env.prod (keep it private)"
else
  echo "==> Using existing .env.prod"
fi

DOMAIN_VALUE="$(grep '^DOMAIN=' .env.prod | cut -d= -f2-)"

echo "==> Building and starting the stack"
sudo docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build

echo "==> Waiting for the app"
sleep 8
sudo docker compose --env-file .env.prod -f docker-compose.prod.yml ps

echo "==> Seeding clinics, doctors and schedules (idempotent)"
sudo docker compose --env-file .env.prod -f docker-compose.prod.yml exec -T app python -m scripts.seed_rady || true

cat <<EOF

Done. Open: https://$DOMAIN_VALUE

Next:
  sudo docker compose --env-file .env.prod -f docker-compose.prod.yml exec app python -m scripts.create_admin

Then change the seeded doctor passwords before real use.
Caddy may take a minute to obtain the HTTPS certificate:
  sudo docker compose --env-file .env.prod -f docker-compose.prod.yml logs -f caddy
EOF
