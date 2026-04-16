#!/usr/bin/env bash
# One-shot install on a fresh droplet. Run after deploy.sh once. Requires
# TRAVELPAYOUTS_TOKEN and TRAVELPAYOUTS_MARKER in the calling shell.
set -euo pipefail

: "${TRAVELPAYOUTS_TOKEN:?required}"
: "${TRAVELPAYOUTS_MARKER:?required}"

HOST=root@REDACTED_SERVER_IP
KEY=~/.ssh/postinnator_do

ssh -i "$KEY" "$HOST" TRAVELPAYOUTS_TOKEN="$TRAVELPAYOUTS_TOKEN" \
  TRAVELPAYOUTS_MARKER="$TRAVELPAYOUTS_MARKER" 'bash -s' <<'REMOTE'
set -euo pipefail

mkdir -p /etc/flyingnode
UNSUB_SECRET=$(openssl rand -hex 16)

cat > /etc/flyingnode/env <<ENV
TRAVELPAYOUTS_TOKEN=${TRAVELPAYOUTS_TOKEN}
TRAVELPAYOUTS_MARKER=${TRAVELPAYOUTS_MARKER}
BREVO_API_KEY=REDACTED_BREVO_KEY
BREVO_SENDER_EMAIL=REDACTED_EMAIL
BREVO_SENDER_NAME=flyingnode
PUBLIC_SITE_URL=https://flyingnode.duckdns.org
SUBSCRIBE_UNSUB_SECRET=${UNSUB_SECRET}
FLYINGNODE_DB=/root/flyingnode/flyingnode.db
PYTHONPATH=/root/flyingnode
ENV
chmod 600 /etc/flyingnode/env

cd /root/flyingnode
set -a; . /etc/flyingnode/env; set +a

# init DB + seed
./venv/bin/python -c "from droplet import db; conn=db.connect('$FLYINGNODE_DB'); db.init_schema(conn); db.seed_from_csv(conn,'droplet/seeds/airports.csv','droplet/seeds/routes.csv'); print('db ready, airports:', conn.execute('SELECT COUNT(*) FROM airports').fetchone()[0], 'routes:', conn.execute('SELECT COUNT(*) FROM routes').fetchone()[0])"

# bootstrap baselines
./venv/bin/python -m droplet.bootstrap

# install systemd service
cp droplet/flyingnode-api.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now flyingnode-api

# install nginx vhost (HTTP-only for now; certbot upgrades to HTTPS)
cp droplet/nginx-site.conf /etc/nginx/sites-available/flyingnode
ln -sf /etc/nginx/sites-available/flyingnode /etc/nginx/sites-enabled/flyingnode
nginx -t && systemctl reload nginx

# certbot (idempotent)
if ! [ -d /etc/letsencrypt/live/flyingnode.duckdns.org ]; then
  certbot --nginx -d flyingnode.duckdns.org --non-interactive --agree-tos \
    -m REDACTED_EMAIL --redirect
fi

# install cron (idempotent: replace any existing flyingnode block)
( crontab -l 2>/dev/null | grep -v '/root/flyingnode/' || true
  cat <<CRON
# flyingnode
0 */6 * * * cd /root/flyingnode && /root/flyingnode/venv/bin/python -m droplet.poller >> /root/flyingnode/logs/poller.log 2>&1
0 2 * * * cd /root/flyingnode && /root/flyingnode/venv/bin/python -m droplet.baseline >> /root/flyingnode/logs/baseline.log 2>&1
30 2 * * * cd /root/flyingnode && /root/flyingnode/venv/bin/python -m droplet.digest >> /root/flyingnode/logs/digest.log 2>&1
CRON
) | crontab -

echo ""
echo "✓ install done"
echo "   API: curl -s http://127.0.0.1:8081/health"
systemctl status flyingnode-api --no-pager | head -5
REMOTE
