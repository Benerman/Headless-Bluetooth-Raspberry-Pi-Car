#!/bin/bash
# Copies unit files into /etc/systemd/system and enables+starts them.
set -e
BASE="/home/benerman/bt_app"
SERVICE_DIR="$BASE/systemd"

if [ ! -d "$SERVICE_DIR" ]; then
  echo "Missing $SERVICE_DIR"
  exit 1
fi

# stop services if already running to avoid replace issues (ignore failures)
sudo systemctl stop headless-bt-web.service 2>/dev/null || true
sudo systemctl stop headless-bt-on.service 2>/dev/null || true
sudo systemctl stop headless-bt-autoconnect.service 2>/dev/null || true

# copy unit files
sudo cp "$SERVICE_DIR"/headless-bt-*.service /etc/systemd/system/ 2>/dev/null || true

# ensure ownership and permissions
for f in /etc/systemd/system/headless-bt-*.service; do
  if [ -e "$f" ]; then
    sudo chown root:root "$f"
    sudo chmod 644 "$f"
  fi
done

# reload systemd and enable/start services if present
sudo systemctl daemon-reload

# enable and start known services if their unit files exist
for svc in headless-bt-on.service headless-bt-web.service headless-bt-autoconnect.service; do
  if [ -f "/etc/systemd/system/$svc" ]; then
    sudo systemctl enable --now "$svc"
    echo "Enabled and started $svc"
  else
    echo "Unit file for $svc not found; skipping enable/start"
  fi
done

# show brief status
echo "Service statuses:"
for svc in headless-bt-on.service headless-bt-web.service headless-bt-autoconnect.service; do
  if systemctl list-units --type=service --all | grep -q "$svc"; then
    sudo systemctl --no-pager status "$svc" --lines=5 || true
  fi
done

echo "Install script finished."
