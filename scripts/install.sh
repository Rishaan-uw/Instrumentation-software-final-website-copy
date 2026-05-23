#!/usr/bin/env bash
# Installs the Husky science console on a Raspberry Pi.
#
# Usage:
#   sudo ./scripts/install.sh /opt/husky-science
#
# What it does:
#   1. Copies the repo into the install directory.
#   2. Creates a Python venv and installs requirements.
#   3. Builds the React frontend into frontend/dist.
#   4. Installs and enables the systemd service.

set -euo pipefail

INSTALL_DIR="${1:-/opt/husky-science}"
SERVICE_USER="${SERVICE_USER:-pi}"

if [[ $EUID -ne 0 ]]; then
  echo "Run as root (sudo)."
  exit 1
fi

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Installing into ${INSTALL_DIR}"
mkdir -p "${INSTALL_DIR}"
rsync -a --delete \
  --exclude='.git' \
  --exclude='frontend/node_modules' \
  --exclude='frontend/dist' \
  --exclude='spectroscopy_logs' \
  "${REPO_DIR}/" "${INSTALL_DIR}/"

cd "${INSTALL_DIR}"

echo "Creating Python venv"
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

if command -v npm >/dev/null 2>&1; then
  echo "Building React frontend"
  pushd frontend >/dev/null
  npm install
  npm run build
  popd >/dev/null
else
  echo "WARNING: npm not found. Install Node 18+ and run 'cd frontend && npm install && npm run build'."
fi

chown -R "${SERVICE_USER}:${SERVICE_USER}" "${INSTALL_DIR}"

echo "Installing systemd unit"
sed "s|@@INSTALL_DIR@@|${INSTALL_DIR}|g; s|@@USER@@|${SERVICE_USER}|g" \
  scripts/husky-science.service > /etc/systemd/system/husky-science.service

systemctl daemon-reload
systemctl enable husky-science.service

cat <<EOF

Done. Next steps:
  1. Edit ${INSTALL_DIR}/.env to set HUSKY_TOKEN, HUSKY_CAMERAS, HUSKY_CHEM_SOURCE.
  2. systemctl start husky-science
  3. Open http://<pi-hostname>:8000 from the base station.

EOF
