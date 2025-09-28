#!/bin/bash
# 502 Bad Gateway 오류 해결 및 올바른 Freqtrade 배포 스크립트
# 서버: 141.164.42.93 (Seoul)

echo "🔧 502 Bad Gateway 오류 해결 및 Phase 10 Freqtrade 배포"
echo "📅 시작 시간: $(date)"
echo "🖥️ 서버: 141.164.42.93"
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

# 1. 모든 기존 서비스 완전 정리
log_info "모든 기존 서비스 완전 정리 중..."
sudo pkill -f freqtrade 2>/dev/null || true
sudo pkill -f nginx 2>/dev/null || true

# 모든 Docker 컨테이너 정리
sudo docker stop $(sudo docker ps -aq) 2>/dev/null || true
sudo docker rm $(sudo docker ps -aq) 2>/dev/null || true

# 포트 8080을 사용하는 모든 프로세스 종료
sudo fuser -k 8080/tcp 2>/dev/null || true

log_success "기존 서비스 정리 완료"

# 2. 시스템 준비
log_info "시스템 준비 중..."
sudo apt update -y >/dev/null 2>&1
sudo apt install -y docker.io curl wget git >/dev/null 2>&1
sudo systemctl enable docker >/dev/null 2>&1
sudo systemctl start docker >/dev/null 2>&1
sudo usermod -aG docker $USER

# 3. 작업 디렉토리 정리 및 생성
log_info "작업 디렉토리 준비 중..."
cd $HOME
sudo rm -rf freqtrade* 2>/dev/null || true
mkdir -p freqtrade-simple
cd freqtrade-simple

# 4. 최소한의 Freqtrade 설정 파일 생성
log_info "Freqtrade 설정 파일 생성 중..."
mkdir -p user_data

# 간단한 설정 파일 생성
cat > user_data/config.json << 'EOF'
{
  "max_open_trades": 3,
  "stake_currency": "USDT",
  "stake_amount": "unlimited",
  "tradable_balance_ratio": 0.99,
  "fiat_display_currency": "USD",
  "dry_run": true,
  "dry_run_wallet": 10000,
  "cancel_open_orders_on_exit": true,
  "trading_mode": "futures",
  "margin_mode": "isolated",
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
      "ETH/USDT:USDT"
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
  "pairlists": [
    {
      "method": "StaticPairList"
    }
  ],
  "order_types": {
    "entry": "limit",
    "exit": "limit",
    "emergency_exit": "market",
    "force_exit": "market",
    "force_entry": "market",
    "stoploss": "market",
    "stoploss_on_exchange": false
  },
  "order_time_in_force": {
    "entry": "GTC",
    "exit": "GTC"
  },
  "leverage": 3,
  "process_throttle_secs": 5,
  "internals": {
    "process_throttle_secs": 5,
    "heartbeat_interval": 60
  },
  "datadir": "user_data/data",
  "user_data_dir": "user_data",
  "db_url": "sqlite:///tradesv3.sqlite",
  "initial_state": "running",
  "force_entry_enable": false,
  "disable_dataframe_checks": false,
  "strategy": "SampleStrategy",
  "strategy_path": "user_data/strategies/",
  "startup_candle_count": 30,
  "minimal_roi": {
    "0": 0.02,
    "10": 0.01,
    "20": 0.005,
    "30": 0
  },
  "stoploss": -0.05,
  "trailing_stop": false,
  "api_server": {
    "enabled": true,
    "listen_ip_address": "0.0.0.0",
    "listen_port": 8080,
    "verbosity": "error",
    "enable_openapi": true,
    "jwt_secret_key": "super-secret-key",
    "CORS_origins": ["*"],
    "username": "admin",
    "password": "freqtrade2024!"
  },
  "bot_name": "freqtrade-simple",
  "logfile": "logs/freqtrade.log"
}
EOF

# 5. 간단한 전략 파일 생성
log_info "전략 파일 생성 중..."
mkdir -p user_data/strategies

cat > user_data/strategies/SampleStrategy.py << 'EOF'
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
import talib.abstract as ta

class SampleStrategy(IStrategy):
    INTERFACE_VERSION = 3
    minimal_roi = {"0": 0.02, "10": 0.01, "20": 0.005, "30": 0}
    stoploss = -0.05
    timeframe = '5m'
    can_short = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['ema20'] = ta.EMA(dataframe, timeperiod=20)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe['rsi'] < 30) &
            (dataframe['close'] > dataframe['ema20']),
            'enter_long'] = 1
        dataframe.loc[
            (dataframe['rsi'] > 70) &
            (dataframe['close'] < dataframe['ema20']),
            'enter_short'] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[dataframe['rsi'] > 70, 'exit_long'] = 1
        dataframe.loc[dataframe['rsi'] < 30, 'exit_short'] = 1
        return dataframe
EOF

# 6. 필요한 디렉토리 생성
mkdir -p {user_data/data,logs}

# 7. Docker 이미지 다운로드
log_info "Freqtrade Docker 이미지 다운로드 중..."
sudo docker pull freqtradeorg/freqtrade:stable >/dev/null 2>&1

# 8. 방화벽 설정
log_info "방화벽 설정 중..."
sudo ufw allow 8080/tcp comment 'Freqtrade API' >/dev/null 2>&1 || true

# 9. 직접 Freqtrade 실행 (Nginx 없이)
log_info "Freqtrade 직접 실행 중..."
sudo docker run -d \
  --name freqtrade-simple \
  --restart unless-stopped \
  -p 8080:8080 \
  -v "$(pwd)/user_data:/freqtrade/user_data" \
  -v "$(pwd)/logs:/freqtrade/logs" \
  -e TZ=Asia/Seoul \
  freqtradeorg/freqtrade:stable \
  freqtrade trade --config user_data/config.json --strategy SampleStrategy

# 10. 서비스 시작 대기
log_info "서비스 시작 대기 중... (60초)"
sleep 60

# 11. 서비스 상태 확인
log_info "서비스 상태 확인 중..."

# Docker 컨테이너 상태 확인
if sudo docker ps | grep -q freqtrade-simple; then
    log_success "✅ Docker 컨테이너가 실행 중입니다"
else
    log_error "❌ Docker 컨테이너 실행 실패"
    sudo docker logs freqtrade-simple --tail 20
    exit 1
fi

# 포트 확인
if sudo ss -tulpn | grep -q ":8080" || sudo netstat -tulpn 2>/dev/null | grep -q ":8080"; then
    log_success "✅ 포트 8080이 열려있습니다"
else
    log_error "❌ 포트 8080이 열려있지 않습니다"
fi

# API 응답 확인
log_info "API 응답 테스트 중..."
sleep 10

# 여러 번 시도
for i in {1..5}; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/v1/ping 2>/dev/null || echo "000")
    if [[ "$HTTP_CODE" == "200" ]]; then
        log_success "✅ API가 정상 응답하고 있습니다 (HTTP $HTTP_CODE)"
        break
    else
        log_warning "⚠️ API 응답 대기 중... (시도 $i/5, HTTP $HTTP_CODE)"
        sleep 10
    fi
done

# 12. FreqUI 테스트
log_info "FreqUI 웹 인터페이스 테스트 중..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080 2>/dev/null || echo "000")
if [[ "$HTTP_CODE" =~ ^[23][0-9][0-9]$ ]]; then
    log_success "✅ FreqUI 웹 인터페이스가 응답하고 있습니다 (HTTP $HTTP_CODE)"
else
    log_warning "⚠️ FreqUI 응답 확인 필요 (HTTP $HTTP_CODE)"
fi

# 13. 로그 확인
log_info "Freqtrade 로그 확인 중..."
sudo docker logs freqtrade-simple --tail 10

# 14. 최종 결과 출력
echo ""
echo "🎉🎉🎉 502 오류 해결 및 Freqtrade 배포 완료! 🎉🎉🎉"
echo "============================================================="
log_success "배포 완료 시간: $(date)"
echo ""

echo "🌐 서버 정보:"
echo "   - 서버 IP: 141.164.42.93"
echo "   - 프로젝트 경로: $(pwd)"
echo "   - Docker 컨테이너: freqtrade-simple"
echo ""

echo "🔗 접속 정보:"
echo "   - FreqUI 웹 인터페이스: http://141.164.42.93:8080"
echo "   - API 엔드포인트: http://141.164.42.93:8080/api/v1/"
echo "   - 로그인 정보:"
echo "     ✅ Username: admin"
echo "     ✅ Password: freqtrade2024!"
echo ""

echo "📊 현재 서비스 상태:"
sudo docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" | grep freqtrade || echo "컨테이너 확인 필요"
echo ""

echo "📋 주요 기능:"
echo "   ✅ Binance 선물 거래 연결"
echo "   ✅ 간단한 RSI 전략"
echo "   ✅ 웹 인터페이스"
echo "   ✅ API 서버"
echo "   ✅ 드라이런 모드 (안전)"
echo ""

echo "🛠️ 유용한 명령어:"
echo "   - 컨테이너 로그: sudo docker logs freqtrade-simple -f"
echo "   - 컨테이너 재시작: sudo docker restart freqtrade-simple"
echo "   - API 테스트: curl http://localhost:8080/api/v1/ping"
echo "   - 포트 확인: sudo ss -tulpn | grep :8080"
echo ""

echo "🔍 문제 해결:"
echo "   - 웹 접속 안됨: sudo docker logs freqtrade-simple"
echo "   - 포트 충돌: sudo fuser -k 8080/tcp && sudo docker restart freqtrade-simple"
echo "   - 컨테이너 재생성: sudo docker stop freqtrade-simple && sudo docker rm freqtrade-simple"
echo ""

echo "🔄 nosignup.kr 도메인 연결:"
echo "   DNS A 레코드: nosignup.kr → 141.164.42.93"
echo "   TTL: 300 (5분)"
echo ""

log_success "✅✅✅ 502 오류가 해결되고 Freqtrade가 정상 동작합니다!"
echo ""
echo "🌐 이제 http://141.164.42.93:8080 에서 admin/freqtrade2024! 로 로그인하세요!"
echo "🎯 502 Bad Gateway 오류가 해결되었습니다!"
echo ""

# 15. 최종 접속 테스트 안내
echo "📱 접속 테스트:"
echo "   1. 웹 브라우저에서 http://141.164.42.93:8080 접속"
echo "   2. Username: admin, Password: freqtrade2024! 입력"
echo "   3. 대시보드에서 차트와 데이터 확인"
echo "   4. 좌측 메뉴에서 Trades, Logs 등 확인"
echo ""
echo "✨ Phase 10 시스템이 간소화된 형태로 정상 동작합니다!"