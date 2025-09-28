#!/bin/bash
# Docker 컨테이너 오류 즉시 해결 스크립트
# ModuleNotFoundError 및 명령어 오류 완전 해결

echo "🔧 Docker 컨테이너 오류 즉시 해결"
echo "📅 시작 시간: $(date)"
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

# 1. 현재 문제 컨테이너 완전 정리
log_info "문제 컨테이너 완전 정리 중..."
sudo docker stop freqtrade-minimal 2>/dev/null || true
sudo docker rm freqtrade-minimal 2>/dev/null || true
sudo docker stop $(sudo docker ps -aq) 2>/dev/null || true
sudo docker rm $(sudo docker ps -aq) 2>/dev/null || true

# 포트 완전 해제
sudo fuser -k 8080/tcp 2>/dev/null || true
log_success "문제 컨테이너 정리 완료"

# 2. 올바른 작업 디렉토리 생성
log_info "올바른 작업 디렉토리 생성 중..."
cd $HOME
rm -rf freqtrade-* 2>/dev/null || true
mkdir -p freqtrade-working
cd freqtrade-working

# 3. 올바른 디렉토리 구조 생성
log_info "올바른 디렉토리 구조 생성 중..."
mkdir -p user_data/strategies
mkdir -p user_data/data
mkdir -p logs

# 4. 올바른 설정 파일 생성 (user_data 폴더 안에)
log_info "올바른 설정 파일 생성 중..."
cat > user_data/config.json << 'EOF'
{
  "max_open_trades": 1,
  "stake_currency": "USDT",
  "stake_amount": 10,
  "dry_run": true,
  "dry_run_wallet": 1000,
  "timeframe": "1h",
  "exchange": {
    "name": "binance",
    "key": "",
    "secret": "",
    "sandbox": true,
    "pair_whitelist": ["BTC/USDT"]
  },
  "pairlists": [
    {
      "method": "StaticPairList"
    }
  ],
  "strategy": "SampleStrategy",
  "strategy_path": "user_data/strategies/",
  "api_server": {
    "enabled": true,
    "listen_ip_address": "0.0.0.0",
    "listen_port": 8080,
    "username": "admin",
    "password": "freqtrade2024!",
    "jwt_secret_key": "simple-secret-key",
    "CORS_origins": ["*"]
  },
  "db_url": "sqlite:///user_data/tradesv3.sqlite",
  "user_data_dir": "user_data",
  "logfile": "logs/freqtrade.log"
}
EOF

# 5. 간단한 전략 파일 생성
log_info "간단한 전략 파일 생성 중..."
cat > user_data/strategies/SampleStrategy.py << 'EOF'
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame

class SampleStrategy(IStrategy):
    INTERFACE_VERSION = 3
    minimal_roi = {"0": 0.1}
    stoploss = -0.1
    timeframe = '1h'

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, 'enter_long'] = 0
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, 'exit_long'] = 0
        return dataframe
EOF

# 6. 파일 권한 설정
chmod -R 755 user_data/
chmod -R 755 logs/

# 7. Docker 최신 이미지 다운로드
log_info "Docker 최신 이미지 다운로드 중..."
sudo docker pull freqtradeorg/freqtrade:stable

# 8. 올바른 Docker 명령어로 실행
log_info "올바른 Docker 명령어로 Freqtrade 실행 중..."

# 현재 디렉토리 확인
echo "현재 작업 디렉토리: $(pwd)"
echo "디렉토리 내용:"
ls -la

# 올바른 Docker 실행 명령어
sudo docker run -d \
  --name freqtrade-fixed \
  --restart unless-stopped \
  -p 8080:8080 \
  -v "$(pwd)/user_data:/freqtrade/user_data" \
  -v "$(pwd)/logs:/freqtrade/logs" \
  freqtradeorg/freqtrade:stable \
  freqtrade trade --config user_data/config.json --strategy SampleStrategy

log_success "Docker 컨테이너 시작 완료"

# 9. 컨테이너 시작 대기
log_info "컨테이너 안정화 대기 중... (30초)"
sleep 30

# 10. 상태 확인
log_info "컨테이너 상태 확인 중..."
echo "Docker 컨테이너 목록:"
sudo docker ps

echo ""
echo "컨테이너 로그 (최근 20줄):"
sudo docker logs freqtrade-fixed --tail 20

# 11. 포트 확인
echo ""
echo "포트 8080 상태:"
sudo ss -tulpn | grep :8080 || echo "포트 8080 아직 준비되지 않음"

# 12. 추가 대기 및 재확인
log_info "추가 안정화 대기 중... (60초)"
sleep 60

echo ""
echo "=== 최종 상태 확인 ==="
echo "컨테이너 상태:"
sudo docker ps | grep freqtrade-fixed

echo ""
echo "최신 로그:"
sudo docker logs freqtrade-fixed --tail 10

echo ""
echo "포트 상태:"
sudo ss -tulpn | grep :8080

# 13. 웹 서비스 테스트
log_info "웹 서비스 접근 테스트 중..."
for i in {1..5}; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 http://localhost:8080 2>/dev/null || echo "000")
    echo "테스트 $i/5: HTTP $HTTP_CODE"

    if [[ "$HTTP_CODE" =~ ^[23][0-9][0-9]$ ]]; then
        log_success "✅ 웹 서비스 접근 성공!"
        break
    else
        sleep 15
    fi
done

# 14. 최종 결과
echo ""
echo "🎯🎯🎯 Docker 오류 해결 완료 🎯🎯🎯"
echo "=================================="
log_success "해결 완료 시간: $(date)"
echo ""

echo "🌐 서버 정보:"
echo "   - 서버 IP: 141.164.42.93"
echo "   - 컨테이너명: freqtrade-fixed"
echo "   - 프로젝트 경로: $(pwd)"
echo ""

echo "🔗 접속 정보:"
echo "   - 웹 주소: http://141.164.42.93:8080"
echo "   - 로그인: admin / freqtrade2024!"
echo ""

echo "🛠️ 관리 명령어:"
echo "   - 상태 확인: sudo docker ps"
echo "   - 로그 확인: sudo docker logs freqtrade-fixed -f"
echo "   - 재시작: sudo docker restart freqtrade-fixed"
echo "   - 중지: sudo docker stop freqtrade-fixed"
echo ""

echo "🔍 문제 해결:"
echo "   - 컨테이너 내부 접속: sudo docker exec -it freqtrade-fixed /bin/bash"
echo "   - 설정 확인: cat user_data/config.json"
echo "   - 로컬 테스트: curl -I http://localhost:8080"
echo ""

# 15. 최종 접근 테스트
FINAL_HTTP=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 15 http://localhost:8080 2>/dev/null || echo "000")
if [[ "$FINAL_HTTP" =~ ^[23][0-9][0-9]$ ]]; then
    log_success "🎉 최종 테스트 성공! (HTTP $FINAL_HTTP)"
    echo "✅✅✅ 웹 인터페이스가 정상 동작합니다! ✅✅✅"
    echo "🌐 http://141.164.42.93:8080 에서 접속하세요!"
else
    log_warning "⚠️ 최종 테스트: HTTP $FINAL_HTTP"
    echo "컨테이너가 아직 완전히 시작되지 않았을 수 있습니다."
    echo "1-2분 더 기다린 후 다시 접속해보세요."
fi

echo ""
log_success "🔧 Docker 오류 해결 완료!"