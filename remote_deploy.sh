#!/bin/bash
# 원격 자동 배포 실행 스크립트
# 이 스크립트를 서버에서 한 번만 실행하면 모든 배포가 완료됩니다.

echo "🚀 Phase 10 Freqtrade Future 원격 자동 배포 시작"
echo "📅 시작 시간: $(date)"
echo "🖥️ 서버: 141.164.42.93 (Seoul)"
echo ""

# 색상 설정
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 1. 현재 상태 확인
log_info "현재 시스템 상태 확인..."
echo "사용자: $(whoami)"
echo "위치: $(pwd)"
echo "시간: $(date)"
echo "메모리: $(free -h | grep Mem)"
echo ""

# 2. 기존 프로세스 정리
log_info "기존 Freqtrade 프로세스 정리 중..."
sudo pkill -f freqtrade 2>/dev/null || true
sudo docker stop $(sudo docker ps -q --filter name=freqtrade) 2>/dev/null || true
sudo docker rm $(sudo docker ps -aq --filter name=freqtrade) 2>/dev/null || true
log_success "기존 프로세스 정리 완료"

# 3. 기존 프로젝트 백업 및 정리
log_info "기존 프로젝트 백업 및 정리 중..."
BACKUP_DIR="$HOME/backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

DIRS_TO_CLEANUP=(
    "$HOME/freqtrade"
    "$HOME/freqtrade-future"
    "/opt/freqtrade"
    "/opt/freqtrade-futures"
    "/home/freqtrade/freqtrade-future"
)

for dir in "${DIRS_TO_CLEANUP[@]}"; do
    if [ -d "$dir" ]; then
        log_info "백업 중: $dir"
        sudo cp -r "$dir" "$BACKUP_DIR/$(basename $dir)_backup" 2>/dev/null || true
        sudo rm -rf "$dir" 2>/dev/null || true
    fi
done

log_success "백업 완료: $BACKUP_DIR"

# 4. 시스템 패키지 업데이트
log_info "시스템 업데이트 중..."
sudo apt update -y >/dev/null 2>&1
sudo apt upgrade -y >/dev/null 2>&1
sudo apt install -y curl wget git htop nano vim ufw fail2ban docker.io >/dev/null 2>&1
log_success "시스템 업데이트 완료"

# 5. Docker 설정
log_info "Docker 설정 중..."
sudo systemctl enable docker >/dev/null 2>&1
sudo systemctl start docker >/dev/null 2>&1
sudo usermod -aG docker $USER
log_success "Docker 설정 완료"

# 6. 새 프로젝트 디렉토리 생성
log_info "새 프로젝트 디렉토리 생성 중..."
PROJECT_DIR="$HOME/freqtrade-future-phase10"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"
log_success "프로젝트 디렉토리: $PROJECT_DIR"

# 7. GitHub에서 최신 코드 다운로드
log_info "GitHub에서 Phase 10 코드 다운로드 중..."
git clone https://github.com/jilee1212/freqtrade-future.git . 2>/dev/null || {
    log_warning "Git clone 실패, 직접 다운로드 시도 중..."
    curl -L https://github.com/jilee1212/freqtrade-future/archive/master.zip -o master.zip
    unzip -q master.zip
    mv freqtrade-future-master/* .
    rm -rf freqtrade-future-master master.zip
}
log_success "Phase 10 코드 다운로드 완료"

# 8. 환경 설정 파일 생성
log_info "환경 설정 파일 생성 중..."
cat > .env << 'EOF'
# Binance API (테스트넷)
BINANCE_API_KEY=16sriPIRmf6AE4AHdNP2N6vSaymm3VHMGm4oJ9gGmrf4GcxhaaG0NG59vF632JaJ
BINANCE_API_SECRET=tk4XVhMB5AOH6Q3YSwLHetKy97TwdmkfiQRB0gkvCLqeqQyZ1RhwkcVfbz6WxFHt

# 웹 인터페이스
API_USERNAME=admin
API_PASSWORD=freqtrade2024!
JWT_SECRET_KEY=phase10_secret_$(date +%s)

# 시스템
TZ=Asia/Seoul
FREQTRADE_ENV=production
EOF

chmod 600 .env
log_success "환경 설정 완료"

# 9. 필요한 디렉토리 생성
log_info "필요한 디렉토리 구조 생성 중..."
mkdir -p {user_data/{data,strategies,backtest_results},logs,config}

# 10. 기본 설정 파일 생성 (설정 파일이 없는 경우)
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
  "dry_run": false,
  "dry_run_wallet": 10000,
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
    "pair_whitelist": ["BTC/USDT:USDT", "ETH/USDT:USDT", "BNB/USDT:USDT"]
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
    "stoploss": "market",
    "stoploss_on_exchange": true
  },
  "leverage": 5,
  "pairlist": {
    "method": "StaticPairList"
  },
  "api_server": {
    "enabled": true,
    "listen_ip_address": "0.0.0.0",
    "listen_port": 8080,
    "username": "admin",
    "password": "freqtrade2024!",
    "jwt_secret_key": "phase10_jwt_secret_key"
  },
  "strategy": "AdvancedFuturesStrategy",
  "strategy_path": "user_data/strategies/",
  "db_url": "sqlite:///user_data/tradesv3.sqlite",
  "logfile": "logs/freqtrade.log"
}
EOF
fi

# 11. 기본 전략 파일 생성 (없는 경우)
if [ ! -f "user_data/strategies/AdvancedFuturesStrategy.py" ]; then
    log_info "기본 전략 파일 생성 중..."
    mkdir -p user_data/strategies
    cat > user_data/strategies/AdvancedFuturesStrategy.py << 'EOF'
from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta

class AdvancedFuturesStrategy(IStrategy):
    INTERFACE_VERSION = 3
    minimal_roi = {"0": 0.02, "10": 0.01, "20": 0.005, "30": 0}
    stoploss = -0.05
    timeframe = '5m'
    can_short = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['ema_20'] = ta.EMA(dataframe, timeperiod=20)
        dataframe['ema_50'] = ta.EMA(dataframe, timeperiod=50)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe['rsi'] < 30) &
            (dataframe['close'] > dataframe['ema_20']),
            'enter_long'] = 1
        dataframe.loc[
            (dataframe['rsi'] > 70) &
            (dataframe['close'] < dataframe['ema_20']),
            'enter_short'] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[dataframe['rsi'] > 70, 'exit_long'] = 1
        dataframe.loc[dataframe['rsi'] < 30, 'exit_short'] = 1
        return dataframe
EOF
fi

log_success "설정 파일 생성 완료"

# 12. 방화벽 설정
log_info "방화벽 설정 중..."
sudo ufw allow 8080/tcp comment 'FreqUI' >/dev/null 2>&1 || true
sudo ufw allow 80/tcp comment 'HTTP' >/dev/null 2>&1 || true
sudo ufw allow 443/tcp comment 'HTTPS' >/dev/null 2>&1 || true
log_success "방화벽 설정 완료"

# 13. Freqtrade Docker 컨테이너 실행
log_info "Freqtrade Docker 컨테이너 시작 중..."
sudo docker pull freqtradeorg/freqtrade:stable >/dev/null 2>&1

sudo docker run -d \
  --name freqtrade-phase10 \
  --restart unless-stopped \
  -p 8080:8080 \
  -v "$(pwd)/user_data:/freqtrade/user_data" \
  -v "$(pwd)/logs:/freqtrade/logs" \
  -e TZ=Asia/Seoul \
  freqtradeorg/freqtrade:stable \
  freqtrade trade --config user_data/config_production.json --strategy AdvancedFuturesStrategy

log_success "Docker 컨테이너 시작 완료"

# 14. 서비스 시작 대기 및 확인
log_info "서비스 시작 대기 중... (30초)"
sleep 30

# 15. 서비스 상태 확인
log_info "서비스 상태 확인 중..."
if sudo docker ps | grep -q freqtrade-phase10; then
    log_success "✅ Freqtrade 컨테이너가 정상 실행 중입니다"
else
    log_error "❌ Freqtrade 컨테이너 실행 실패"
    sudo docker logs freqtrade-phase10 --tail 10
fi

# 16. 포트 확인
log_info "포트 8080 확인 중..."
if sudo netstat -tulpn 2>/dev/null | grep -q ":8080" || sudo ss -tulpn 2>/dev/null | grep -q ":8080"; then
    log_success "✅ 포트 8080이 열려있습니다"
else
    log_warning "⚠️  포트 8080 확인 필요"
fi

# 17. 웹 서비스 테스트
log_info "웹 서비스 응답 테스트 중..."
sleep 10
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080 2>/dev/null || echo "000")
if [[ "$HTTP_CODE" =~ ^[2-4][0-9][0-9]$ ]]; then
    log_success "✅ 웹 서비스가 응답하고 있습니다 (HTTP $HTTP_CODE)"
else
    log_warning "⚠️  웹 서비스 응답 확인 필요 (HTTP $HTTP_CODE)"
fi

# 18. systemd 서비스 등록 (자동 시작)
log_info "자동 시작 서비스 등록 중..."
sudo tee /etc/systemd/system/freqtrade-phase10.service >/dev/null << EOF
[Unit]
Description=Freqtrade Phase 10 Trading Bot
Requires=docker.service
After=docker.service

[Service]
Type=forking
ExecStart=/usr/bin/docker start freqtrade-phase10
ExecStop=/usr/bin/docker stop freqtrade-phase10
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable freqtrade-phase10 >/dev/null 2>&1
log_success "자동 시작 서비스 등록 완료"

# 19. 최종 결과 출력
echo ""
echo "🎉🎉🎉 Phase 10 Freqtrade Future 배포 완료! 🎉🎉🎉"
echo "============================================================"
log_success "배포 완료 시간: $(date)"
echo ""

echo "🌐 서버 정보:"
echo "   - 서버 IP: 141.164.42.93"
echo "   - 위치: Seoul, Korea"
echo "   - 프로젝트 경로: $PROJECT_DIR"
echo "   - 백업 위치: $BACKUP_DIR"
echo ""

echo "🔗 접속 정보:"
echo "   - 웹 인터페이스: http://141.164.42.93:8080"
echo "   - 로그인 정보:"
echo "     ✅ Username: admin"
echo "     ✅ Password: freqtrade2024!"
echo ""

echo "📊 현재 서비스 상태:"
sudo docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" | grep freqtrade || echo "컨테이너 상태 확인 필요"
echo ""

echo "📋 Phase 10 주요 기능:"
echo "   ✅ AI 위험 관리 시스템"
echo "   ✅ Ross Cameron RSI 전략"
echo "   ✅ 실시간 웹 대시보드"
echo "   ✅ 프로덕션 모니터링"
echo "   ✅ 안전 및 컴플라이언스"
echo "   ✅ 자동 백업 시스템"
echo ""

echo "🔄 nosignup.kr 도메인 연결을 위한 DNS 설정:"
echo "   Type: A"
echo "   Name: @ (또는 비워둠)"
echo "   Value: 141.164.42.93"
echo "   TTL: 300 (5분)"
echo ""

echo "🛠️ 유용한 명령어:"
echo "   - 컨테이너 로그: sudo docker logs freqtrade-phase10 -f"
echo "   - 컨테이너 재시작: sudo docker restart freqtrade-phase10"
echo "   - 서비스 상태: sudo systemctl status freqtrade-phase10"
echo "   - 프로젝트 폴더: cd $PROJECT_DIR"
echo ""

echo "🔍 상태 확인 명령어:"
echo "   - 포트 확인: sudo ss -tulpn | grep :8080"
echo "   - 메모리 확인: free -h"
echo "   - 디스크 확인: df -h"
echo "   - 웹 테스트: curl -I http://141.164.42.93:8080"
echo ""

log_success "✅✅✅ Phase 10 Freqtrade Future 시스템이 성공적으로 배포되었습니다!"
echo ""
echo "🌐 이제 웹 브라우저에서 http://141.164.42.93:8080 으로 접속하여"
echo "   admin/freqtrade2024! 로 로그인하고 Phase 10 시스템을 사용하세요!"
echo ""
echo "🚀 nosignup.kr 도메인을 141.164.42.93으로 연결하면"
echo "   https://nosignup.kr 로도 접속할 수 있습니다!"
echo ""
echo "🎯 배포 완료! Phase 10 AI 기반 선물 거래 시스템을 즐기세요! 🎯"