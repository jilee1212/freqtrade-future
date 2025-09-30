#!/bin/bash

# Freqtrade Future - Production Deployment Script
# Deploy to Vultr server: 141.164.42.93

set -e

echo "🚀 Starting deployment to Vultr server..."

SERVER="root@141.164.42.93"
PROJECT_DIR="/root/freqtrade-future"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Step 1: Building Docker images locally...${NC}"
docker-compose -f docker-compose.full.yml build

echo -e "${BLUE}Step 2: Saving Docker images...${NC}"
docker save -o /tmp/freqtrade-images.tar \
  freqtrade-future-backend \
  freqtrade-future-frontend

echo -e "${BLUE}Step 3: Uploading to server...${NC}"
scp /tmp/freqtrade-images.tar $SERVER:/tmp/
scp docker-compose.full.yml $SERVER:$PROJECT_DIR/
scp backend/.env.example $SERVER:$PROJECT_DIR/backend/.env
scp user_data/config_futures.json $SERVER:$PROJECT_DIR/user_data/

echo -e "${BLUE}Step 4: Loading images on server...${NC}"
ssh $SERVER << 'ENDSSH'
cd /tmp
docker load -i freqtrade-images.tar
rm freqtrade-images.tar
ENDSSH

echo -e "${BLUE}Step 5: Starting services...${NC}"
ssh $SERVER << 'ENDSSH'
cd /root/freqtrade-future
docker-compose -f docker-compose.full.yml down
docker-compose -f docker-compose.full.yml up -d
docker-compose -f docker-compose.full.yml ps
ENDSSH

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo -e "${YELLOW}Services:${NC}"
echo "  - Freqtrade UI:  http://141.164.42.93:8080"
echo "  - Backend API:   http://141.164.42.93:5000"
echo "  - Frontend:      http://141.164.42.93:3000"

# Cleanup
rm /tmp/freqtrade-images.tar

echo -e "${GREEN}🎉 All done!${NC}"