#!/bin/bash
# Vultr 자동 배포 스크립트 (비밀번호 입력 없이)
# nosignup.kr 도메인 연결 포함

set -e

SERVER="linuxuser@141.164.42.93"
DOMAIN="nosignup.kr"
EMAIL="admin@nosignup.kr"  # SSL 인증서용 이메일

echo "=========================================="
echo "🚀 Vultr 자동 배포 + 도메인 연결"
echo "=========================================="
echo ""
echo "서버: $SERVER"
echo "도메인: $DOMAIN"
echo ""

# Step 1: 서버에 SSH 접속하여 전체 배포 스크립트 실행
ssh -o StrictHostKeyChecking=no $SERVER 'bash -s' << 'ENDSSH'

set -e

echo "=========================================="
echo "Phase 1: 서버 환경 준비"
echo "=========================================="

# 1-1. Docker 공식 저장소 추가 및 설치
echo "🐳 Docker 설치 중..."
sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Docker GPG 키 추가
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg --yes

# Docker 저장소 추가
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Docker 설치
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin docker-compose

# Docker 서비스 시작
sudo systemctl start docker
sudo systemctl enable docker

# 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER

echo "✅ Docker 설치 완료"

# 1-2. Swap 메모리 추가 (1GB RAM 대응)
echo "💾 Swap 메모리 추가 중..."
if [ ! -f /swapfile ]; then
    sudo dd if=/dev/zero of=/swapfile bs=1M count=2048 status=progress
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo "✅ Swap 메모리 추가 완료"
else
    echo "ℹ️  Swap 메모리 이미 존재"
fi

free -h

echo ""
echo "=========================================="
echo "Phase 2: 기존 프로젝트 제거"
echo "=========================================="

# 2-1. Docker 컨테이너 중지 및 제거
echo "🔥 기존 Docker 컨테이너 제거 중..."
sudo docker stop $(sudo docker ps -aq) 2>/dev/null || true
sudo docker rm $(sudo docker ps -aq) 2>/dev/null || true
sudo docker volume prune -f || true

# 2-2. 기존 프로젝트 폴더 제거 (권한 문제 해결)
echo "🔥 기존 프로젝트 폴더 제거 중..."
cd ~
if [ -d "freqtrade-future" ]; then
    # user_data/backtest_results 권한 문제 해결
    sudo chmod -R 777 freqtrade-future/user_data 2>/dev/null || true
    rm -rf freqtrade-future
fi
rm -rf freqtrade freqtrade-backup-* 2>/dev/null || true

echo "✅ 기존 프로젝트 제거 완료"

echo ""
echo "=========================================="
echo "Phase 3: 새 프로젝트 배포"
echo "=========================================="

# 3-1. GitHub Clone
echo "📥 GitHub에서 프로젝트 다운로드 중..."
cd ~
git clone https://github.com/jilee1212/freqtrade-future.git
cd freqtrade-future

echo "✅ Clone 완료"

# 3-2. 환경 변수 설정 (도메인 반영)
echo "⚙️  환경 변수 설정 중..."

cat > backend/.env << 'EOF'
PORT=5000
FREQTRADE_URL=http://freqtrade:8080
FREQTRADE_USERNAME=freqtrade
FREQTRADE_PASSWORD=futures2024
FLASK_ENV=production
EOF

cat > frontend/.env.production << 'EOF'
NEXT_PUBLIC_API_URL=https://nosignup.kr/api
NEXT_PUBLIC_WS_URL=wss://nosignup.kr/api
NEXT_PUBLIC_FREQTRADE_URL=https://nosignup.kr/freqtrade
EOF

echo "✅ 환경 변수 설정 완료"

# 3-3. Docker 빌드 (newgrp로 권한 즉시 적용)
echo "🐳 Docker 이미지 빌드 중... (10-15분 소요)"
sg docker -c "docker-compose -f docker-compose.full.yml build"

if [ $? -eq 0 ]; then
    echo "✅ Docker 빌드 완료"
else
    echo "❌ Docker 빌드 실패"
    exit 1
fi

# 3-4. 컨테이너 시작
echo "🚀 컨테이너 시작 중..."
sg docker -c "docker-compose -f docker-compose.full.yml up -d"

sleep 30

# 3-5. 상태 확인
echo "📊 컨테이너 상태:"
sg docker -c "docker-compose ps"

echo "✅ 프로젝트 배포 완료"

echo ""
echo "=========================================="
echo "Phase 4: Nginx + SSL 설정"
echo "=========================================="

# 4-1. Nginx 설치
echo "🌐 Nginx 설치 중..."
sudo apt-get install -y nginx

# 4-2. Nginx 설정 파일 생성
echo "⚙️  Nginx 설정 파일 생성 중..."
sudo tee /etc/nginx/sites-available/nosignup.kr > /dev/null << 'NGINX_EOF'
server {
    listen 80;
    server_name nosignup.kr www.nosignup.kr;

    # Frontend (Next.js)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Freqtrade UI
    location /freqtrade {
        rewrite ^/freqtrade(/.*)$ $1 break;
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX_EOF

# 4-3. Nginx 설정 활성화
sudo ln -sf /etc/nginx/sites-available/nosignup.kr /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 4-4. Nginx 설정 테스트 및 재시작
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

echo "✅ Nginx 설정 완료"

# 4-5. Certbot 설치 및 SSL 인증서 발급
echo "🔐 SSL 인증서 발급 중..."
sudo apt-get install -y certbot python3-certbot-nginx

# SSL 인증서 자동 발급 및 Nginx 설정 업데이트
sudo certbot --nginx -d nosignup.kr -d www.nosignup.kr --non-interactive --agree-tos -m admin@nosignup.kr --redirect

echo "✅ SSL 인증서 발급 완료"

# 4-6. SSL 자동 갱신 설정 확인
sudo systemctl status certbot.timer --no-pager || true

echo ""
echo "=========================================="
echo "Phase 5: 방화벽 설정"
echo "=========================================="

# UFW 방화벽 설정
echo "🛡️  방화벽 설정 중..."
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw --force enable

echo "✅ 방화벽 설정 완료"

echo ""
echo "=========================================="
echo "✅ 배포 완료!"
echo "=========================================="
echo ""
echo "🌐 서비스 접속 URL:"
echo "  Frontend:  https://nosignup.kr"
echo "  Backend:   https://nosignup.kr/api/health"
echo "  Freqtrade: https://nosignup.kr/freqtrade"
echo ""
echo "📊 상태 확인:"
sg docker -c "docker-compose ps"
echo ""
echo "📝 로그 확인:"
echo "  docker-compose -f docker-compose.full.yml logs -f"
echo ""
echo "🔐 SSL 인증서:"
echo "  자동 갱신 설정 완료"
echo "  유효기간: 90일 (자동 갱신)"
echo ""

ENDSSH

echo ""
echo "=========================================="
echo "🎉 Vultr 배포 완료!"
echo "=========================================="
echo ""
echo "🌐 접속 URL:"
echo "  https://nosignup.kr"
echo ""
echo "⏰ DNS 전파 대기 중..."
echo "  (최대 1-2시간 소요 가능)"
echo ""
echo "📝 다음 단계:"
echo "  1. DNS 설정 확인: nosignup.kr A 레코드 → 141.164.42.93"
echo "  2. DNS 전파 확인: nslookup nosignup.kr"
echo "  3. 브라우저에서 https://nosignup.kr 접속"
echo ""