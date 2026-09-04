#!/usr/bin/env bash
set -euo pipefail

# FlashView installer for Raspberry Pi 4 (Raspberry Pi OS 64-bit, Bookworm)
# Usage: bash setup_pi.sh  (run from the repo root on the Pi)

APP_DIR="${APP_DIR:-/home/sma/flashview}"
MEDIA_DIR="${MEDIA_DIR:-/media/usb/movies}"
PORT="${PORT:-8000}"

echo "==> Installing system packages (ffmpeg, python venv)"
sudo apt-get update
sudo apt-get install -y ffmpeg python3-venv ca-certificates curl

echo "==> Creating venv and installing Python dependencies from requirements.txt"
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

echo "==> Building frontend"
cd "$APP_DIR/frontend"
if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
  npm ci && npm run build
else
  echo "!! node/npm not found — building the frontend requires Node >= 18."
  echo "   Install it with:  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt-get install -y nodejs"
  exit 1
fi

echo "==> Writing configuration"
mkdir -p "$APP_DIR/backend/data"
if [ ! -f "$APP_DIR/backend/.env" ]; then
  cat > "$APP_DIR/backend/.env" <<EOF
MEDIA_DIR=$MEDIA_DIR
DATA_DIR=$APP_DIR/backend/data
PORT=$PORT
AUTO_RESCAN=true
EOF
fi

echo "==> Mount hint"
echo "   (1) Plug in your USB drive"
echo "   (2) Find its device with: lsblk"
echo "   (3) Mount and enable auto-mount, for example:"
echo "       sudo mkdir -p $MEDIA_DIR"
echo "       UUID=\$(sudo blkid -s UUID -o value /dev/sda1)"
echo "       echo \"UUID=\$UUID $MEDIA_DIR vfat defaults,noatime,uid=sma,gid=sma 0 0\" | sudo tee -a /etc/fstab"

echo "==> Installing systemd service"
sudo cp "$APP_DIR/deploy/flashview.service" /etc/systemd/system/flashview.service
sudo systemctl daemon-reload
sudo systemctl enable flashview.service
sudo systemctl restart flashview.service

echo
echo "==> Done!"
echo "    Open:      http://<raspberry-pi-ip>:$PORT"
echo "    Status:    systemctl status flashview"
echo "    Logs:      journalctl -u flashview -f"
echo "    Rescan:    curl -X POST http://<raspberry-pi-ip>:$PORT/api/library/rescan?force=true"