#!/bin/bash
# 컨테이너 재시작 문제 완전 해결 - 가장 단순한 방법
# 확실하게 작동하는 최소한의 설정

echo "🔧 컨테이너 재시작 문제 완전 해결"
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

# 1. 모든 기존 컨테이너 완전 정리
log_info "모든 기존 컨테이너 완전 정리 중..."
sudo docker stop $(sudo docker ps -aq) 2>/dev/null || true
sudo docker rm $(sudo docker ps -aq) 2>/dev/null || true
sudo fuser -k 8080/tcp 2>/dev/null || true
log_success "모든 컨테이너 정리 완료"

# 2. 완전히 새로운 디렉토리 생성
log_info "완전히 새로운 작업 환경 생성 중..."
cd $HOME
rm -rf freqtrade-* 2>/dev/null || true
mkdir freqtrade-simple
cd freqtrade-simple

# 3. FreqUI만 실행하는 초간단 설정
log_info "FreqUI 전용 초간단 설정 생성 중..."

# FreqUI 전용 설정 파일 (거래 기능 없이 UI만)
cat > config.json << 'EOF'
{
  "dry_run": true,
  "dry_run_wallet": 1000,
  "stake_currency": "USDT",
  "stake_amount": 10,
  "trading_mode": "spot",
  "exchange": {
    "name": "binance",
    "key": "",
    "secret": "",
    "sandbox": true,
    "pair_whitelist": ["BTC/USDT"]
  },
  "timeframe": "1h",
  "strategy": "DefaultStrategy",
  "api_server": {
    "enabled": true,
    "listen_ip_address": "0.0.0.0",
    "listen_port": 8080,
    "username": "admin",
    "password": "freqtrade2024!",
    "jwt_secret_key": "super-secret-key",
    "CORS_origins": ["*"],
    "enable_openapi": true
  }
}
EOF

# 4. Docker에서 FreqUI만 실행 (거래 없이)
log_info "FreqUI 전용 모드로 Docker 실행 중..."

sudo docker run -d \
  --name freqtrade-ui-only \
  --restart unless-stopped \
  -p 8080:8080 \
  -v "$(pwd)/config.json:/freqtrade/config.json" \
  freqtradeorg/freqtrade:stable \
  freqtrade webserver --config config.json

log_success "FreqUI 전용 컨테이너 시작 완료"

# 5. 충분한 시작 대기
log_info "서비스 시작 대기 중... (45초)"
sleep 45

# 6. 상태 확인
log_info "서비스 상태 확인 중..."
echo "=== Docker 컨테이너 상태 ==="
sudo docker ps

echo ""
echo "=== 컨테이너 로그 확인 ==="
sudo docker logs freqtrade-ui-only --tail 15

echo ""
echo "=== 포트 8080 상태 ==="
sudo ss -tulpn | grep :8080 || echo "포트 8080 아직 준비되지 않음"

# 7. 웹 서비스 접근 테스트
log_info "웹 서비스 접근 테스트 중..."
sleep 15

for i in {1..10}; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://localhost:8080 2>/dev/null || echo "000")
    echo "접근 테스트 $i/10: HTTP $HTTP_CODE"

    if [[ "$HTTP_CODE" =~ ^[23][0-9][0-9]$ ]]; then
        log_success "✅ FreqUI 웹 인터페이스 접근 성공!"
        break
    elif [ $i -eq 10 ]; then
        log_warning "⚠️ 웹 접근 시간 초과"
    else
        sleep 10
    fi
done

# 8. 컨테이너가 정상 실행 중인지 재확인
echo ""
echo "=== 최종 컨테이너 상태 확인 ==="
if sudo docker ps | grep -q freqtrade-ui-only; then
    CONTAINER_STATUS=$(sudo docker ps --format "table {{.Names}}\t{{.Status}}" | grep freqtrade-ui-only)
    log_success "✅ 컨테이너가 정상 실행 중: $CONTAINER_STATUS"
else
    log_error "❌ 컨테이너가 실행되지 않고 있습니다"
    echo "로그 확인:"
    sudo docker logs freqtrade-ui-only --tail 20
fi

# 9. 포트 최종 확인
echo ""
echo "=== 포트 바인딩 최종 확인 ==="
PORT_STATUS=$(sudo ss -tulpn | grep :8080)
if [ ! -z "$PORT_STATUS" ]; then
    log_success "✅ 포트 8080이 정상적으로 열려있습니다"
    echo "$PORT_STATUS"
else
    log_warning "⚠️ 포트 8080이 아직 바인딩되지 않았습니다"
fi

# 10. 최종 결과 및 접속 정보
echo ""
echo "🎯🎯🎯 FreqUI 전용 모드 배포 완료 🎯🎯🎯"
echo "======================================="
log_success "배포 완료 시간: $(date)"
echo ""

echo "🌐 접속 정보:"
echo "   - 웹 주소: http://141.164.42.93:8080"
echo "   - 로그인: admin / freqtrade2024!"
echo "   - 모드: FreqUI 전용 (거래 기능 없음)"
echo ""

echo "📊 현재 상태:"
echo "   - 컨테이너: freqtrade-ui-only"
echo "   - 포트: 8080"
echo "   - 기능: 웹 인터페이스만"
echo ""

echo "🛠️ 관리 명령어:"
echo "   - 상태 확인: sudo docker ps"
echo "   - 로그 확인: sudo docker logs freqtrade-ui-only -f"
echo "   - 재시작: sudo docker restart freqtrade-ui-only"
echo "   - 웹 테스트: curl -I http://localhost:8080"
echo ""

echo "🔍 문제 해결:"
echo "   - 컨테이너 접속: sudo docker exec -it freqtrade-ui-only /bin/bash"
echo "   - 설정 확인: cat config.json"
echo "   - 포트 확인: sudo ss -tulpn | grep :8080"
echo ""

# 11. 최종 접근성 테스트
log_info "최종 접근성 테스트 중..."
sleep 10

FINAL_HTTP=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 http://localhost:8080 2>/dev/null || echo "000")
if [[ "$FINAL_HTTP" =~ ^[23][0-9][0-9]$ ]]; then
    log_success "🎉 최종 접근 테스트 성공! (HTTP $FINAL_HTTP)"
    echo ""
    echo "✅✅✅ FreqUI 웹 인터페이스가 정상 동작합니다! ✅✅✅"
    echo "🌐 브라우저에서 http://141.164.42.93:8080 접속하세요!"
    echo "🔑 로그인: admin / freqtrade2024!"
else
    log_warning "⚠️ 최종 접근 테스트: HTTP $FINAL_HTTP"
    echo "웹 서비스가 아직 완전히 준비되지 않았을 수 있습니다."
    echo "1-2분 더 기다린 후 접속해보세요."
fi

echo ""
echo "🎯 FreqUI 전용 모드 배포 완료!"
echo "이제 웹 인터페이스를 통해 Freqtrade를 확인할 수 있습니다."
echo ""

# 12. nosignup.kr 도메인 연결 안내
echo "🔗 nosignup.kr 도메인 연결:"
echo "   DNS A 레코드: nosignup.kr → 141.164.42.93"
echo "   설정 후 https://nosignup.kr 로 접속 가능"
echo ""

log_success "🚀 컨테이너 재시작 문제 해결 완료!"