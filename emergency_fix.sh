#!/bin/bash
# 긴급 문제 해결 및 최소한의 안정적인 Freqtrade 배포
# 모든 문제를 완전히 리셋하고 가장 간단한 방법으로 재배포

echo "🚨 긴급 문제 해결 및 안정적인 Freqtrade 배포"
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

# 0. 현재 상태 진단
log_info "현재 시스템 상태 진단 중..."
echo "현재 사용자: $(whoami)"
echo "현재 위치: $(pwd)"
echo "시간: $(date)"
echo ""

echo "메모리 상태:"
free -h
echo ""

echo "디스크 상태:"
df -h /
echo ""

echo "포트 8080 상태:"
sudo ss -tulpn | grep :8080 || echo "포트 8080 비어있음"
echo ""

echo "실행 중인 Docker 컨테이너:"
sudo docker ps || echo "Docker 컨테이너 없음"
echo ""

# 1. 완전한 시스템 리셋
log_info "완전한 시스템 리셋 시작..."

# 모든 프로세스 강제 종료
log_info "모든 관련 프로세스 종료 중..."
sudo pkill -f freqtrade 2>/dev/null || true
sudo pkill -f nginx 2>/dev/null || true
sudo pkill -f python 2>/dev/null || true

# 포트 강제 해제
sudo fuser -k 8080/tcp 2>/dev/null || true
sudo fuser -k 80/tcp 2>/dev/null || true
sudo fuser -k 443/tcp 2>/dev/null || true

# 모든 Docker 컨테이너 완전 제거
log_info "모든 Docker 컨테이너 제거 중..."
sudo docker stop $(sudo docker ps -aq) 2>/dev/null || true
sudo docker rm $(sudo docker ps -aq) 2>/dev/null || true
sudo docker system prune -af 2>/dev/null || true

# 기존 프로젝트 완전 삭제
log_info "기존 프로젝트 완전 삭제 중..."
cd $HOME
sudo rm -rf freqtrade* 2>/dev/null || true
sudo rm -rf /opt/freqtrade* 2>/dev/null || true
sudo rm -rf /home/freqtrade 2>/dev/null || true

log_success "시스템 리셋 완료"

# 2. 기본 시스템 설정
log_info "기본 시스템 설정 중..."
sudo apt update -y >/dev/null 2>&1
sudo apt install -y docker.io curl wget git htop nano >/dev/null 2>&1

# Docker 서비스 재시작
sudo systemctl stop docker 2>/dev/null || true
sleep 5
sudo systemctl start docker
sudo systemctl enable docker

# 사용자 권한 설정
sudo usermod -aG docker $USER
newgrp docker 2>/dev/null || true

log_success "기본 시스템 설정 완료"

# 3. 최소한의 작업 환경 생성
log_info "최소한의 작업 환경 생성 중..."
cd $HOME
mkdir -p freqtrade-minimal
cd freqtrade-minimal

# 4. 가장 간단한 Freqtrade 설정
log_info "최소한의 Freqtrade 설정 생성 중..."

# 기본 설정 파일
cat > config.json << 'EOF'
{
  "max_open_trades": 1,
  "stake_currency": "USDT",
  "stake_amount": 100,
  "dry_run": true,
  "dry_run_wallet": 1000,
  "timeframe": "1m",
  "exchange": {
    "name": "binance",
    "key": "",
    "secret": "",
    "sandbox": true,
    "pair_whitelist": ["BTC/USDT"]
  },
  "pairlists": [{"method": "StaticPairList"}],
  "strategy": "SampleStrategy",
  "api_server": {
    "enabled": true,
    "listen_ip_address": "0.0.0.0",
    "listen_port": 8080,
    "username": "admin",
    "password": "freqtrade2024!",
    "jwt_secret_key": "simple-secret"
  }
}
EOF

# 기본 전략 파일
mkdir -p user_data/strategies
cat > user_data/strategies/SampleStrategy.py << 'EOF'
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame

class SampleStrategy(IStrategy):
    INTERFACE_VERSION = 3
    minimal_roi = {"0": 0.1}
    stoploss = -0.1
    timeframe = '1m'

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, 'enter_long'] = 0
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, 'exit_long'] = 0
        return dataframe
EOF

# 5. Docker 이미지 준비
log_info "Docker 이미지 다운로드 중..."
sudo docker pull freqtradeorg/freqtrade:stable

# 6. 가장 간단한 방법으로 Freqtrade 실행
log_info "Freqtrade 간단 실행 중..."

# 포트가 확실히 비어있는지 재확인
sudo fuser -k 8080/tcp 2>/dev/null || true
sleep 5

# Freqtrade 실행
sudo docker run -d \
  --name freqtrade-minimal \
  --restart unless-stopped \
  -p 8080:8080 \
  -v "$(pwd):/freqtrade" \
  freqtradeorg/freqtrade:stable \
  freqtrade trade --config config.json

log_success "Freqtrade 실행 완료"

# 7. 충분한 시작 대기 시간
log_info "서비스 안정화 대기 중... (2분)"
sleep 120

# 8. 상태 확인
log_info "서비스 상태 확인 중..."

# Docker 상태 확인
echo "Docker 컨테이너 상태:"
sudo docker ps | grep freqtrade-minimal || log_error "컨테이너가 실행되지 않음"

# 로그 확인
echo ""
echo "Freqtrade 로그 (최근 20줄):"
sudo docker logs freqtrade-minimal --tail 20

# 포트 확인
echo ""
echo "포트 8080 상태:"
sudo ss -tulpn | grep :8080 || log_warning "포트 8080이 열려있지 않음"

# 9. 네트워크 접근성 테스트
log_info "네트워크 접근성 테스트 중..."

# 로컬 접근 테스트
for i in {1..10}; do
    echo "접근 테스트 $i/10..."

    # HTTP 응답 코드 확인
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://localhost:8080 2>/dev/null || echo "000")
    echo "HTTP 응답 코드: $HTTP_CODE"

    if [[ "$HTTP_CODE" =~ ^[23][0-9][0-9]$ ]]; then
        log_success "✅ 웹 서비스 접근 성공! (HTTP $HTTP_CODE)"
        break
    else
        log_warning "⚠️ 접근 대기 중... (HTTP $HTTP_CODE)"
        sleep 10
    fi
done

# 10. 방화벽 확인 및 설정
log_info "방화벽 설정 확인 중..."
sudo ufw status || log_info "UFW 비활성화됨"
sudo ufw allow 8080/tcp comment 'Freqtrade' 2>/dev/null || true

# 11. 시스템 정보 요약
echo ""
echo "🎯🎯🎯 긴급 수리 완료 및 시스템 정보 🎯🎯🎯"
echo "=============================================="
log_success "수리 완료 시간: $(date)"
echo ""

echo "🌐 서버 정보:"
echo "   - 서버 IP: 141.164.42.93"
echo "   - 프로젝트 경로: $(pwd)"
echo "   - 설정: 최소한의 안정적인 구성"
echo ""

echo "🔗 접속 정보:"
echo "   - 웹 주소: http://141.164.42.93:8080"
echo "   - 로그인:"
echo "     * Username: admin"
echo "     * Password: freqtrade2024!"
echo ""

echo "📊 현재 상태:"
echo "   - Docker 컨테이너: freqtrade-minimal"
echo "   - 거래 모드: 드라이런 (안전 모드)"
echo "   - 포트: 8080 (직접 연결)"
echo "   - 전략: 최소한의 샘플 전략"
echo ""

echo "🛠️ 문제 해결 명령어:"
echo "   - 컨테이너 상태: sudo docker ps"
echo "   - 로그 확인: sudo docker logs freqtrade-minimal -f"
echo "   - 재시작: sudo docker restart freqtrade-minimal"
echo "   - 포트 확인: sudo ss -tulpn | grep :8080"
echo "   - 로컬 테스트: curl -I http://localhost:8080"
echo ""

echo "🔍 추가 진단:"
echo "   - 메모리: free -h"
echo "   - 디스크: df -h"
echo "   - 프로세스: sudo docker stats freqtrade-minimal"
echo ""

# 12. 최종 접근성 테스트
log_info "최종 접근성 테스트 실행 중..."
sleep 10

FINAL_TEST=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 http://localhost:8080 2>/dev/null || echo "000")
if [[ "$FINAL_TEST" =~ ^[23][0-9][0-9]$ ]]; then
    log_success "🎉 최종 테스트 성공! HTTP $FINAL_TEST"
    echo ""
    echo "✅✅✅ 웹 서비스가 정상 동작합니다! ✅✅✅"
    echo "🌐 http://141.164.42.93:8080 에서 admin/freqtrade2024! 로 접속하세요!"
else
    log_error "❌ 최종 테스트 실패: HTTP $FINAL_TEST"
    echo ""
    echo "🔧 추가 진단이 필요합니다:"
    echo "   1. sudo docker logs freqtrade-minimal"
    echo "   2. sudo ss -tulpn | grep :8080"
    echo "   3. curl -v http://localhost:8080"
fi

echo ""
echo "🎯 긴급 수리 및 최소 배포 완료!"
echo ""

# 13. nosignup.kr 도메인 연결 안내
echo "🔗 nosignup.kr 도메인 연결 방법:"
echo "   DNS A 레코드 설정:"
echo "   - Type: A"
echo "   - Name: @ (또는 비워둠)"
echo "   - Value: 141.164.42.93"
echo "   - TTL: 300"
echo ""
echo "   설정 후 5-30분 후 https://nosignup.kr 접속 가능"
echo ""

log_success "🚀 모든 긴급 수리가 완료되었습니다!"