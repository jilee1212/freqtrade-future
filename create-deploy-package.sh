#!/bin/bash

# Deployment Package Creator for Git Bash on Windows

echo "========================================"
echo "Freqtrade Future - Deployment Package"
echo "========================================"
echo

# Create deployment folder
DEPLOY_DIR="deploy-package"
rm -rf $DEPLOY_DIR
mkdir -p $DEPLOY_DIR/backend
mkdir -p $DEPLOY_DIR/frontend
mkdir -p $DEPLOY_DIR/user_data

echo "[1/5] Copying backend files..."
cp backend/app.py $DEPLOY_DIR/backend/
cp backend/requirements.txt $DEPLOY_DIR/backend/
cp backend/Dockerfile $DEPLOY_DIR/backend/
cp backend/.env $DEPLOY_DIR/backend/

echo "[2/5] Copying frontend files..."
cp -r frontend/src $DEPLOY_DIR/frontend/
cp -r frontend/public $DEPLOY_DIR/frontend/
cp frontend/package.json $DEPLOY_DIR/frontend/
cp frontend/package-lock.json $DEPLOY_DIR/frontend/
cp frontend/next.config.ts $DEPLOY_DIR/frontend/
cp frontend/tsconfig.json $DEPLOY_DIR/frontend/
cp frontend/postcss.config.mjs $DEPLOY_DIR/frontend/
cp frontend/components.json $DEPLOY_DIR/frontend/
cp frontend/Dockerfile $DEPLOY_DIR/frontend/
cp frontend/.env.production $DEPLOY_DIR/frontend/

echo "[3/5] Copying configuration files..."
cp docker-compose.full.yml $DEPLOY_DIR/
cp user_data/config_futures.json $DEPLOY_DIR/user_data/

echo "[4/5] Creating deployment instructions..."
cat > $DEPLOY_DIR/UPLOAD_INSTRUCTIONS.txt << 'EOF'
=========================================
DEPLOYMENT INSTRUCTIONS
=========================================

1. Upload this entire folder to Vultr server:
   Location: /root/freqtrade-future/

2. Use FileZilla/WinSCP:
   Host: sftp://141.164.42.93
   User: root
   Port: 22

3. After upload, SSH into server (use PuTTY) and run:
   cd /root/freqtrade-future
   docker-compose -f docker-compose.full.yml build
   docker-compose -f docker-compose.full.yml up -d

4. Verify deployment:
   http://141.164.42.93:3000 - Frontend
   http://141.164.42.93:5000/api/health - Backend
   http://141.164.42.93:8080 - Freqtrade

=========================================
EOF

echo "[5/5] Creating package archive..."
tar -czf deploy-package.tar.gz $DEPLOY_DIR

echo
echo "========================================"
echo "Package created successfully!"
echo "========================================"
echo
echo "Created files:"
echo "  1. $DEPLOY_DIR/ - Deployment folder"
echo "  2. deploy-package.tar.gz - Compressed archive"
echo
echo "Upload options:"
echo "  A. Use FileZilla/WinSCP to upload $DEPLOY_DIR/* to server"
echo "  B. Upload deploy-package.tar.gz and extract on server"
echo
echo "See MANUAL_DEPLOYMENT.md for detailed guide"
echo "========================================"