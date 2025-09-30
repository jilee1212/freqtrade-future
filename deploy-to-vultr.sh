#!/bin/bash

# Vultr 서버 배포 스크립트
# 기존 프로젝트 백업 후 새 프로젝트 배포

set -e

SERVER="root@141.164.42.93"
REPO_URL="https://github.com/jilee1212/freqtrade-future.git"
PROJECT_DIR="/root/freqtrade-future"
BACKUP_DIR="/root/freqtrade-backup-$(date +%Y%m%d_%H%M%S)"

echo "=========================================="
echo "Freqtrade Future - Vultr Deployment"
echo "=========================================="
echo ""

echo "🔗 Connecting to Vultr server: $SERVER"
echo ""

# SSH로 서버에 연결하여 배포 실행
ssh -o ConnectTimeout=10 $SERVER << 'ENDSSH'

echo "✅ Connected to server"
echo ""

# 1. 기존 프로젝트 백업
if [ -d "/root/freqtrade-future" ]; then
    echo "📦 Backing up existing project..."
    BACKUP_DIR="/root/freqtrade-backup-$(date +%Y%m%d_%H%M%S)"

    # Docker 중지
    cd /root/freqtrade-future
    if [ -f "docker-compose.yml" ]; then
        docker-compose down || true
    fi
    if [ -f "docker-compose.simple.yml" ]; then
        docker-compose -f docker-compose.simple.yml down || true
    fi

    # 백업
    cd /root
    mv freqtrade-future $BACKUP_DIR
    echo "✅ Backup created: $BACKUP_DIR"
else
    echo "ℹ️  No existing project found"
fi
echo ""

# 2. 새 프로젝트 Clone
echo "📥 Cloning new project from GitHub..."
cd /root
git clone https://github.com/jilee1212/freqtrade-future.git
cd freqtrade-future
echo "✅ Repository cloned successfully"
echo ""

# 3. 백업에서 중요 파일 복사 (있다면)
if [ -d "$BACKUP_DIR" ]; then
    echo "📋 Copying important files from backup..."

    # user_data 복사
    if [ -d "$BACKUP_DIR/user_data" ]; then
        cp -r $BACKUP_DIR/user_data/* ./user_data/ 2>/dev/null || true
        echo "  ✓ user_data copied"
    fi

    # .env 파일 복사 (있다면)
    if [ -f "$BACKUP_DIR/backend/.env" ]; then
        cp $BACKUP_DIR/backend/.env ./backend/.env
        echo "  ✓ backend/.env copied"
    fi
fi
echo ""

# 4. 환경 파일 생성 (없다면)
if [ ! -f "backend/.env" ]; then
    echo "📝 Creating backend/.env..."
    cat > backend/.env << 'EOF'
PORT=5000
FREQTRADE_URL=http://freqtrade:8080
FREQTRADE_USERNAME=freqtrade
FREQTRADE_PASSWORD=futures2024
FLASK_ENV=production
EOF
    echo "✅ backend/.env created"
fi

if [ ! -f "frontend/.env.production" ]; then
    echo "📝 Creating frontend/.env.production..."
    cat > frontend/.env.production << 'EOF'
NEXT_PUBLIC_API_URL=http://141.164.42.93:5000
NEXT_PUBLIC_WS_URL=ws://141.164.42.93:5000
NEXT_PUBLIC_FREQTRADE_URL=http://141.164.42.93:8080
EOF
    echo "✅ frontend/.env.production created"
fi
echo ""

# 5. Docker 이미지 빌드
echo "🐳 Building Docker images..."
docker-compose -f docker-compose.full.yml build
echo "✅ Docker images built successfully"
echo ""

# 6. 컨테이너 시작
echo "🚀 Starting containers..."
docker-compose -f docker-compose.full.yml up -d
echo "✅ Containers started"
echo ""

# 7. 상태 확인
echo "📊 Container status:"
docker-compose -f docker-compose.full.yml ps
echo ""

# 8. 헬스 체크
echo "🏥 Health check..."
sleep 10

echo "Checking backend..."
curl -s http://localhost:5000/api/health || echo "❌ Backend not responding yet"

echo ""
echo "Checking freqtrade..."
curl -s http://localhost:8080/api/v1/ping || echo "❌ Freqtrade not responding yet"

echo ""
echo "=========================================="
echo "✅ Deployment completed!"
echo "=========================================="
echo ""
echo "🌐 Services:"
echo "  Frontend:  http://141.164.42.93:3000"
echo "  Backend:   http://141.164.42.93:5000"
echo "  Freqtrade: http://141.164.42.93:8080"
echo ""
echo "📝 To view logs:"
echo "  docker-compose -f docker-compose.full.yml logs -f"
echo ""
echo "📦 Backup location:"
echo "  $BACKUP_DIR"
echo ""

ENDSSH

echo "🎉 Deployment script completed!"
echo ""
echo "Next steps:"
echo "1. Visit http://141.164.42.93:3000 to see the new frontend"
echo "2. Test API: curl http://141.164.42.93:5000/api/health"
echo "3. Monitor logs: ssh root@141.164.42.93 'cd /root/freqtrade-future && docker-compose logs -f'"