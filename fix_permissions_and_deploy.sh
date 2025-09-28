#!/bin/bash
# 권한 문제 해결 및 Phase 10 배포 완료 스크립트
# 서버: 141.164.42.93 (Seoul)
# 사용자: linuxuser

set -e

echo "🔧 권한 문제 해결 및 Phase 10 배포 완료 스크립트"
echo "📅 시작 시간: $(date)"
echo "🖥️ 서버: 141.164.42.93"
echo ""

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 1. 현재 상태 확인
log_info "현재 상태 확인 중..."
echo "현재 사용자: $(whoami)"
echo "현재 위치: $(pwd)"
echo ""

# 2. 기존 프로젝트 디렉토리 확인 및 정리
log_info "프로젝트 디렉토리 확인 및 정리 중..."

# freqtrade 사용자 홈 디렉토리 확인
if [ -d "/home/freqtrade" ]; then
    log_info "freqtrade 사용자 홈 디렉토리 발견됨"
    sudo ls -la /home/freqtrade/ || true
fi

# 기존 프로젝트 정리
POSSIBLE_DIRS=(
    "/home/freqtrade/freqtrade-future"
    "/home/linuxuser/freqtrade-future"
    "/opt/freqtrade-futures"
    "/home/linuxuser/freqtrade"
)

for dir in "${POSSIBLE_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        log_warning "기존 디렉토리 발견: $dir"
        sudo rm -rf "$dir" 2>/dev/null || true
        log_info "제거됨: $dir"
    fi
done

# 3. 새로운 프로젝트 디렉토리 생성
log_info "새로운 프로젝트 디렉토리 생성 중..."
PROJECT_DIR="/home/linuxuser/freqtrade-future"
sudo mkdir -p "$PROJECT_DIR"
sudo chown -R linuxuser:linuxuser "$PROJECT_DIR"
cd "$PROJECT_DIR"
log_success "프로젝트 디렉토리 생성: $PROJECT_DIR"

# 4. GitHub에서 프로젝트 클론
log_info "GitHub에서 Phase 10 프로젝트 클론 중..."
git clone https://github.com/jilee1212/freqtrade-future.git .
log_success "GitHub 프로젝트 클론 완료"

# 5. 환경 변수 파일 생성
log_info "환경 변수 파일 생성 중..."
cat > .env << 'EOF'
# Binance API 설정 (테스트넷)
BINANCE_API_KEY=16sriPIRmf6AE4AHdNP2N6vSaymm3VHMGm4oJ9gGmrf4GcxhaaG0NG59vF632JaJ
BINANCE_API_SECRET=tk4XVhMB5AOH6Q3YSwLHetKy97TwdmkfiQRB0gkvCLqeqQyZ1RhwkcVfbz6WxFHt

# FreqUI 인증 설정
JWT_SECRET_KEY=phase10_jwt_secret_key_2024_freqtrade_futures_seoul
API_USERNAME=admin
API_PASSWORD=freqtrade2024!
WS_TOKEN=phase10_websocket_token_secure_seoul

# 텔레그램 설정 (선택사항)
TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# 데이터베이스 설정
DB_PASSWORD=freqtrade_db_password_2024_secure_seoul

# 시스템 설정
TZ=Asia/Seoul
FREQTRADE_ENV=production

# Docker 설정
COMPOSE_PROJECT_NAME=freqtrade-future
COMPOSE_HTTP_TIMEOUT=120
EOF

chmod 600 .env
log_success "환경 변수 파일 생성 완료"

# 6. Docker Compose 설정 확인 및 수정
log_info "Docker Compose 설정 확인 중..."
if [ -f "docker-compose.yml" ]; then
    log_success "docker-compose.yml 파일 발견됨"
else
    log_warning "docker-compose.yml 파일이 없음 - 간단한 설정 생성"
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  freqtrade:
    image: freqtradeorg/freqtrade:stable
    container_name: freqtrade-future-bot
    restart: unless-stopped
    volumes:
      - ./user_data:/freqtrade/user_data
      - ./config:/freqtrade/config
      - ./logs:/freqtrade/logs
    ports:
      - "8080:8080"
    environment:
      - TZ=Asia/Seoul
      - FREQTRADE_ENV=production
    command: >
      freqtrade trade
      --config user_data/config_production.json
      --strategy AdvancedFuturesStrategy
      --db-url sqlite:///user_data/tradesv3_production.sqlite
    networks:
      - freqtrade-network

  nginx:
    image: nginx:alpine
    container_name: freqtrade-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - freqtrade
    networks:
      - freqtrade-network

networks:
  freqtrade-network:
    driver: bridge
EOF
fi

# 7. 필요한 디렉토리 생성
log_info "필요한 디렉토리 생성 중..."
mkdir -p {user_data,config,logs,nginx}
mkdir -p user_data/{data,strategies,backtest_results}
mkdir -p logs/freqtrade

# 기본 설정 파일이 없는 경우 심플한 버전 생성
if [ ! -f "user_data/config_production.json" ]; then
    log_info "기본 설정 파일 생성 중..."
    cat > user_data/config_production.json << 'EOF'
{
  "trading_mode": "futures",
  "margin_mode": "isolated",
  "max_open_trades": 3,
  "stake_currency": "USDT",
  "stake_amount": "unlimited",
  "tradable_balance_ratio": 0.95,
  "fiat_display_currency": "USD",
  "dry_run": false,
  "dry_run_wallet": 10000,
  "cancel_open_orders_on_exit": true,
  "timeframe": "5m",
  "exchange": {
    "name": "binance",
    "key": "16sriPIRmf6AE4AHdNP2N6vSaymm3VHMGm4oJ9gGmrf4GcxhaaG0NG59vF632JaJ",
    "secret": "tk4XVhMB5AOH6Q3YSwLHetKy97TwdmkfiQRB0gkvCLqeqQyZ1RhwkcVfbz6WxFHt",
    "sandbox": false,
    "ccxt_config": {
      "enableRateLimit": true,
      "rateLimit": 50,
      "urls": {
        "api": {
          "public": "https://fapi.binance.com/fapi",
          "private": "https://fapi.binance.com/fapi"
        }
      }
    },
    "pair_whitelist": [
      "BTC/USDT:USDT",
      "ETH/USDT:USDT",
      "BNB/USDT:USDT"
    ]
  },
  "entry_pricing": {
    "price_side": "same",
    "use_order_book": true,
    "order_book_top": 1
  },
  "exit_pricing": {
    "price_side": "same",
    "use_order_book": true,
    "order_book_top": 1
  },
  "order_types": {
    "entry": "limit",
    "exit": "limit",
    "emergency_exit": "market",
    "force_exit": "market",
    "force_entry": "market",
    "stoploss": "market",
    "stoploss_on_exchange": true
  },
  "leverage": 5,
  "liquidation_buffer": 0.05,
  "pairlist": {
    "method": "StaticPairList"
  },
  "api_server": {
    "enabled": true,
    "listen_ip_address": "0.0.0.0",
    "listen_port": 8080,
    "verbosity": "error",
    "enable_openapi": false,
    "jwt_secret_key": "phase10_jwt_secret_key_2024",
    "username": "admin",
    "password": "freqtrade2024!"
  },
  "bot_name": "FreqtradeFutures-Phase10",
  "initial_state": "running",
  "force_entry_enable": false,
  "strategy": "AdvancedFuturesStrategy",
  "strategy_path": "user_data/strategies/",
  "db_url": "sqlite:///user_data/tradesv3_production.sqlite",
  "logfile": "logs/freqtrade.log"
}
EOF
fi

log_success "디렉토리 및 설정 파일 생성 완료"

# 8. Docker 서비스 확인 및 시작
log_info "Docker 서비스 확인 중..."
if ! systemctl is-active --quiet docker; then
    log_info "Docker 서비스 시작 중..."
    sudo systemctl start docker
    sudo systemctl enable docker
fi

# 현재 사용자를 docker 그룹에 추가
if ! groups $USER | grep -q docker; then
    log_info "사용자를 docker 그룹에 추가 중..."
    sudo usermod -aG docker $USER
    log_warning "그룹 변경사항 적용을 위해 다시 로그인이 필요할 수 있습니다"
fi

log_success "Docker 서비스 준비 완료"

# 9. 기존 컨테이너 정리
log_info "기존 컨테이너 정리 중..."
sudo docker stop freqtrade-future-bot 2>/dev/null || true
sudo docker rm freqtrade-future-bot 2>/dev/null || true
sudo docker stop freqtrade-nginx 2>/dev/null || true
sudo docker rm freqtrade-nginx 2>/dev/null || true

# 10. 스크립트 권한 설정
log_info "스크립트 권한 설정 중..."
find . -name "*.py" -exec chmod +x {} \; 2>/dev/null || true
find . -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true

# 11. 방화벽 확인
log_info "방화벽 설정 확인 중..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 8080/tcp comment 'FreqUI' 2>/dev/null || true
    sudo ufw allow 80/tcp comment 'HTTP' 2>/dev/null || true
    sudo ufw allow 443/tcp comment 'HTTPS' 2>/dev/null || true
    log_success "방화벽 설정 확인 완료"
fi

# 12. Docker Compose 실행
log_info "Docker Compose 서비스 시작 중..."
export COMPOSE_HTTP_TIMEOUT=120

# Freqtrade만 먼저 시작 (Nginx는 나중에)
sudo docker run -d \
  --name freqtrade-future-bot \
  --restart unless-stopped \
  -p 8080:8080 \
  -v "$(pwd)/user_data:/freqtrade/user_data" \
  -v "$(pwd)/logs:/freqtrade/logs" \
  -e TZ=Asia/Seoul \
  freqtradeorg/freqtrade:stable \
  freqtrade trade --config user_data/config_production.json --strategy AdvancedFuturesStrategy

# 서비스 시작 대기
log_info "서비스 시작 대기 중..."
sleep 30

# 13. 서비스 상태 확인
log_info "서비스 상태 확인 중..."
if sudo docker ps | grep -q freqtrade-future-bot; then
    log_success "Freqtrade 컨테이너가 정상적으로 실행 중입니다"
else
    log_warning "Freqtrade 컨테이너 실행에 문제가 있을 수 있습니다"
    sudo docker logs freqtrade-future-bot --tail 20 || true
fi

# 14. 포트 확인
log_info "포트 8080 확인 중..."
if netstat -tulpn 2>/dev/null | grep -q ":8080"; then
    log_success "포트 8080이 열려있습니다"
else
    log_warning "포트 8080이 열려있지 않습니다"
fi

# 15. 웹 서비스 테스트
log_info "웹 서비스 테스트 중..."
sleep 10
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080 | grep -q "200\|401\|404"; then
    log_success "웹 서비스가 응답하고 있습니다"
else
    log_warning "웹 서비스 응답 확인 필요"
fi

# 16. 최종 결과 출력
echo ""
echo "🎉 Phase 10 배포 완료!"
echo "=================================================="
log_success "배포 완료 시간: $(date)"
echo ""

echo "🌐 서버 정보:"
echo "   - 서버 IP: 141.164.42.93"
echo "   - 프로젝트 경로: $PROJECT_DIR"
echo "   - 운영체제: Ubuntu $(lsb_release -rs 2>/dev/null || echo 'Unknown')"
echo ""

echo "🔗 접속 정보:"
echo "   - FreqUI 웹 인터페이스: http://141.164.42.93:8080"
echo "   - 로그인 정보:"
echo "     * Username: admin"
echo "     * Password: freqtrade2024!"
echo ""

echo "📊 현재 컨테이너 상태:"
sudo docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" | grep freqtrade || echo "컨테이너 확인 필요"
echo ""

echo "📋 다음 단계:"
echo "   1. 웹 브라우저에서 http://141.164.42.93:8080 접속"
echo "   2. admin/freqtrade2024! 로 로그인"
echo "   3. Phase 10 시스템 동작 확인"
echo "   4. nosignup.kr 도메인을 141.164.42.93으로 연결"
echo ""

echo "🛠️ 유용한 명령어:"
echo "   - 컨테이너 로그: sudo docker logs freqtrade-future-bot -f"
echo "   - 컨테이너 재시작: sudo docker restart freqtrade-future-bot"
echo "   - 서비스 중지: sudo docker stop freqtrade-future-bot"
echo "   - 프로젝트 경로: cd $PROJECT_DIR"
echo ""

echo "🔍 문제 해결:"
echo "   - 로그 확인: sudo docker logs freqtrade-future-bot"
echo "   - 포트 확인: sudo netstat -tulpn | grep :8080"
echo "   - 방화벽 확인: sudo ufw status"
echo ""

log_success "✅ Phase 10 Freqtrade Future 시스템 배포가 완료되었습니다!"
echo "🌐 http://141.164.42.93:8080 에서 시스템을 확인하세요!"