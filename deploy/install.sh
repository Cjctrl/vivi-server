#!/usr/bin/env bash
# V.I.V.I server installer (Ubuntu). Run as root from the deploy/ directory.
#
# Prereqs handled SEPARATELY (see RUNBOOK.md): NVIDIA driver, Ollama + models,
# Python venv, Node, Tailscale, Docker (for Qdrant). This script only creates
# the service user, the state dirs, the env file, and installs/links the units.
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then echo "Run as root (sudo)." >&2; exit 1; fi
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "==> 1/5  service user + state directories"
id vivi &>/dev/null || adduser --system --group --home /opt/vivi --shell /usr/sbin/nologin vivi
install -d -o vivi -g vivi /var/lib/vivi \
  /var/lib/vivi/knowledge_base \
  /var/lib/vivi/memory \
  /var/lib/vivi/data \
  /var/lib/vivi/db \
  /var/lib/vivi/qdrant \
  /var/lib/vivi/logs \
  /var/lib/vivi/sandbox
install -d -o root -g vivi -m 0750 /etc/vivi

echo "==> 2/5  environment file"
if [ ! -f /etc/vivi/vivi.env ]; then
  install -o root -g vivi -m 0640 "$HERE/vivi.env.example" /etc/vivi/vivi.env
  echo "    created /etc/vivi/vivi.env  — EDIT IT: set WS_SECRET, NEXUS_SECRET, TAILSCALE_BIND_IP"
else
  echo "    /etc/vivi/vivi.env already exists — left untouched"
fi

echo "==> 3/5  Ollama keep-alive override"
install -d /etc/systemd/system/ollama.service.d
install -m 0644 "$HERE/systemd/ollama.service.d/override.conf" \
  /etc/systemd/system/ollama.service.d/override.conf

echo "==> 4/5  systemd units"
install -m 0644 "$HERE"/systemd/vivi-qdrant.service \
                "$HERE"/systemd/vivi-nexus.service \
                "$HERE"/systemd/vivi-filewatcher.service \
                "$HERE"/systemd/vivi-zimkb.service \
                "$HERE"/systemd/vivi-gateway.service \
                "$HERE"/systemd/vivi-backup.service \
                "$HERE"/systemd/vivi-backup.timer \
                /etc/systemd/system/

echo "==> 5/5  reload"
systemctl daemon-reload

cat <<'EOF'

Installed. Remaining steps:
  1. Edit /etc/vivi/vivi.env   (WS_SECRET, NEXUS_SECRET, TAILSCALE_BIND_IP=$(tailscale ip -4))
  2. Confirm prereqs: nvidia-smi · ollama list · docker --version · node --version
  3. Start the stack (order is enforced by the units):
       systemctl enable --now vivi-qdrant vivi-nexus vivi-filewatcher vivi-zimkb vivi-gateway
  4. (optional) backups: edit /etc/vivi/backup.env then:
       systemctl enable --now vivi-backup.timer
  5. Smoke test — see deploy/RUNBOOK.md  (curl the /health endpoints)

Logs:  journalctl -u vivi-gateway -f
EOF
