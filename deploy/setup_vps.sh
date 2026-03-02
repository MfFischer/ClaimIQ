#!/bin/bash
# ─── ClaimIQ VPS Deployment Script ───────────────────────────────────────────
# Run once on a fresh Ubuntu 22.04 VPS to set up everything.
# Usage: bash deploy/setup_vps.sh
# After running, visit http://YOUR_VPS_IP to see ClaimIQ live.

set -e

APP_DIR="/var/www/claimiq"
DOMAIN="YOUR_DOMAIN"   # ← change this to your domain or VPS IP

echo "════════════════════════════════════════"
echo " ClaimIQ VPS Setup"
echo "════════════════════════════════════════"

# ── 1. System packages ────────────────────────────────────────────────────────
echo "[1/8] Installing system packages..."
sudo apt update -qq
sudo apt install -y python3.11 python3.11-venv python3-pip \
  tesseract-ocr tesseract-ocr-deu tesseract-ocr-eng \
  libgl1-mesa-glx libglib2.0-0 \
  nginx nodejs npm git curl

# Verify Tesseract
tesseract --version
echo "Tesseract languages: $(tesseract --list-langs)"

# ── 2. Node / PM2 (or systemd) ────────────────────────────────────────────────
echo "[2/8] Setting up Node..."
node --version
npm install -g pm2 2>/dev/null || true

# ── 3. App directory ──────────────────────────────────────────────────────────
echo "[3/8] Setting up app directory..."
sudo mkdir -p $APP_DIR
sudo chown -R $USER:$USER $APP_DIR

# ── 4. Copy files (assumes you scp'd the project to /tmp/claimiq) ────────────
echo "[4/8] Copying project files..."
cp -r /tmp/claimiq/backend  $APP_DIR/
cp -r /tmp/claimiq/frontend $APP_DIR/

# ── 5. Backend setup ──────────────────────────────────────────────────────────
echo "[5/8] Setting up Python backend..."
cd $APP_DIR/backend
python3.11 -m venv venv
source venv/bin/activate
pip install --quiet -r requirements.txt

# Copy and configure .env
if [ ! -f .env ]; then
  cp .env.example .env
  echo ""
  echo "⚠️  IMPORTANT: Edit $APP_DIR/backend/.env and set:"
  echo "   GEMINI_API_KEY=your_key"
  echo "   APP_ENV=production"
  echo "   APP_CORS_ORIGINS=https://$DOMAIN"
  echo ""
fi

# Create uploads dir
mkdir -p uploads

# ── 6. Frontend build ─────────────────────────────────────────────────────────
echo "[6/8] Building Next.js frontend..."
cd $APP_DIR/frontend

# Set production API URL
echo "NEXT_PUBLIC_API_URL=https://$DOMAIN" > .env.local

npm install --quiet
npm run build

# ── 7. Systemd services ───────────────────────────────────────────────────────
echo "[7/8] Installing systemd services..."
sudo cp /tmp/claimiq/deploy/claimiq-backend.service  /etc/systemd/system/
sudo cp /tmp/claimiq/deploy/claimiq-frontend.service /etc/systemd/system/

# Fix paths in service files
sudo sed -i "s|/var/www/claimiq|$APP_DIR|g" /etc/systemd/system/claimiq-backend.service
sudo sed -i "s|/var/www/claimiq|$APP_DIR|g" /etc/systemd/system/claimiq-frontend.service
sudo sed -i "s|User=www-data|User=$USER|g" /etc/systemd/system/claimiq-backend.service
sudo sed -i "s|User=www-data|User=$USER|g" /etc/systemd/system/claimiq-frontend.service

sudo systemctl daemon-reload
sudo systemctl enable claimiq-backend claimiq-frontend
sudo systemctl start  claimiq-backend claimiq-frontend

# ── 8. Nginx ──────────────────────────────────────────────────────────────────
echo "[8/8] Configuring Nginx..."
sudo cp /tmp/claimiq/deploy/nginx.conf /etc/nginx/sites-available/claimiq
sudo sed -i "s/YOUR_DOMAIN/$DOMAIN/g" /etc/nginx/sites-available/claimiq
sudo ln -sf /etc/nginx/sites-available/claimiq /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

echo ""
echo "════════════════════════════════════════"
echo " ✅ ClaimIQ is live!"
echo ""
echo " App:     http://$DOMAIN"
echo " API:     http://$DOMAIN/api/v1"
echo " Health:  http://$DOMAIN/health"
echo " API docs: http://$DOMAIN/api/docs"
echo ""
echo " Next steps:"
echo "  1. Edit $APP_DIR/backend/.env — add GEMINI_API_KEY"
echo "  2. Run: sudo systemctl restart claimiq-backend"
echo "  3. Add SSL: sudo apt install certbot python3-certbot-nginx"
echo "              sudo certbot --nginx -d $DOMAIN"
echo "════════════════════════════════════════"
