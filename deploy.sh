#!/usr/bin/env bash
# rsync local droplet/ to the server and install deps. Env file at
# /etc/flyingnode/env is set up manually on first install (see scripts/first_install.sh).
set -euo pipefail
HOST=root@REDACTED_SERVER_IP
KEY=~/.ssh/postinnator_do

ssh -i $KEY $HOST 'mkdir -p /root/flyingnode/droplet /root/flyingnode/logs'

rsync -az --delete -e "ssh -i $KEY" \
  --exclude '__pycache__' --exclude '*.pyc' --exclude 'tests/' \
  droplet/ "$HOST:/root/flyingnode/droplet/"

ssh -i $KEY $HOST 'bash -s' <<'REMOTE'
set -euo pipefail
cd /root/flyingnode
if [ ! -d venv ]; then
  python3 -m venv venv
fi
./venv/bin/pip install -q -r droplet/requirements.txt
REMOTE
echo "✓ synced to droplet"
