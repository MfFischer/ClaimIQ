#!/bin/bash
# ─── Quick redeploy script ────────────────────────────────────────────────────
# Run after pushing code changes to update the live VPS.
# Usage: bash deploy/redeploy.sh

set -e
APP_DIR="/var/www/claimiq"

echo "🔄 Redeploying ClaimIQ..."

# Pull latest (if using git)
# cd $APP_DIR && git pull

# Restart backend
sudo systemctl restart claimiq-backend
echo "✅ Backend restarted"

# Rebuild + restart frontend
cd $APP_DIR/frontend
npm run build
sudo systemctl restart claimiq-frontend
echo "✅ Frontend rebuilt and restarted"

# Check status
sudo systemctl status claimiq-backend  --no-pager -l | tail -3
sudo systemctl status claimiq-frontend --no-pager -l | tail -3

echo "✅ Redeploy complete"
