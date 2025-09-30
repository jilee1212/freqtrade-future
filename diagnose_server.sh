#!/bin/bash
# Vultr 서버 진단 스크립트
# 서버 연결 후 이 스크립트를 실행하세요: bash diagnose_server.sh

echo "🔍 Freqtrade Future 서버 진단 시작..."
echo "=================================================="
echo ""

# 색상 설정
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

# 1. 시스템 정보
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  시스템 정보"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_info "현재 사용자: $(whoami)"
log_info "현재 디렉토리: $(pwd)"
log_info "서버 IP: $(curl -s ifconfig.me 2>/dev/null || echo '확인 불가')"
log_info "운영체제: $(lsb_release -ds 2>/dev/null || cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo ""

# 2. 메모리 상태
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  메모리 및 디스크 상태"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
free -h
echo ""
df -h / | tail -1
echo ""
if swapon --show 2>/dev/null | grep -q "/"; then
    log_success "스왑 활성화됨"
    swapon --show
else
    log_warning "스왑이 비활성화되어 있습니다"
fi
echo ""

# 3. Docker 상태
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  Docker 상태"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if command -v docker &> /dev/null; then
    log_success "Docker 설치됨: $(docker --version)"

    if systemctl is-active --quiet docker; then
        log_success "Docker 서비스 실행 중"
    else
        log_error "Docker 서비스가 실행되지 않음"
    fi

    echo ""
    log_info "실행 중인 컨테이너:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || log_warning "실행 중인 컨테이너 없음"

    echo ""
    log_info "모든 컨테이너 (중지 포함):"
    docker ps -a --format "table {{.Names}}\t{{.Status}}" 2>/dev/null
else
    log_error "Docker가 설치되지 않음"
fi
echo ""

# 4. 프로젝트 디렉토리 확인
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  프로젝트 디렉토리"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

POSSIBLE_DIRS=(
    "/opt/freqtrade-futures"
    "$HOME/freqtrade-future"
    "$HOME/freqtrade-future-phase10"
    "$HOME/freqtrade"
    "/home/freqtrade/freqtrade-future"
)

PROJECT_DIR=""
for dir in "${POSSIBLE_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        log_success "발견: $dir"
        PROJECT_DIR="$dir"

        if [ -f "$dir/docker-compose.yml" ]; then
            log_success "  └─ docker-compose.yml 있음"
        else
            log_warning "  └─ docker-compose.yml 없음"
        fi

        if [ -f "$dir/.env" ]; then
            log_success "  └─ .env 파일 있음"
        else
            log_warning "  └─ .env 파일 없음"
        fi
    fi
done

if [ -z "$PROJECT_DIR" ]; then
    log_error "프로젝트 디렉토리를 찾을 수 없습니다"
fi
echo ""

# 5. 포트 상태
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  포트 상태"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
PORTS=(8080 5000 80 443 3000 9090 6379)
for port in "${PORTS[@]}"; do
    if netstat -tuln 2>/dev/null | grep -q ":$port "; then
        log_success "포트 $port: LISTENING"
        netstat -tuln | grep ":$port " | head -1
    else
        log_warning "포트 $port: NOT LISTENING"
    fi
done
echo ""

# 6. 방화벽 상태
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6️⃣  방화벽 상태"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if command -v ufw &> /dev/null; then
    if ufw status | grep -q "Status: active"; then
        log_info "UFW 방화벽 활성화됨"
        ufw status numbered | grep -E "(8080|5000|80|443)"
    else
        log_warning "UFW 방화벽 비활성화됨"
    fi
else
    log_info "UFW가 설치되지 않음"
fi
echo ""

# 7. Freqtrade 프로세스
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7️⃣  Freqtrade 프로세스"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if ps aux | grep -i freqtrade | grep -v grep | head -5; then
    log_success "Freqtrade 프로세스 발견됨"
else
    log_warning "실행 중인 Freqtrade 프로세스 없음"
fi
echo ""

# 8. 최근 로그 확인
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "8️⃣  최근 로그 (마지막 10줄)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

LOG_PATHS=(
    "/var/log/freqtrade/freqtrade.log"
    "$PROJECT_DIR/logs/freqtrade.log"
    "$PROJECT_DIR/user_data/logs/freqtrade.log"
)

FOUND_LOG=false
for log_path in "${LOG_PATHS[@]}"; do
    if [ -f "$log_path" ]; then
        log_success "로그 파일 발견: $log_path"
        echo "마지막 10줄:"
        tail -10 "$log_path"
        FOUND_LOG=true
        break
    fi
done

if [ "$FOUND_LOG" = false ]; then
    log_warning "로그 파일을 찾을 수 없습니다"

    if [ -n "$PROJECT_DIR" ]; then
        log_info "Docker 로그 확인 시도..."
        cd "$PROJECT_DIR"
        docker compose logs --tail=10 2>/dev/null || log_warning "Docker Compose 로그 없음"
    fi
fi
echo ""

# 9. 진단 요약
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "9️⃣  진단 요약 및 권장 사항"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

ISSUES_FOUND=false

# Docker 체크
if ! command -v docker &> /dev/null; then
    log_error "Docker가 설치되지 않음 → fix_deployment.sh 실행 필요"
    ISSUES_FOUND=true
elif ! systemctl is-active --quiet docker; then
    log_error "Docker 서비스 중지됨 → 'sudo systemctl start docker' 실행"
    ISSUES_FOUND=true
fi

# 프로젝트 디렉토리 체크
if [ -z "$PROJECT_DIR" ]; then
    log_error "프로젝트 디렉토리 없음 → fix_deployment.sh 실행 필요"
    ISSUES_FOUND=true
fi

# 컨테이너 체크
if command -v docker &> /dev/null; then
    RUNNING_CONTAINERS=$(docker ps -q 2>/dev/null | wc -l)
    if [ "$RUNNING_CONTAINERS" -eq 0 ]; then
        log_error "실행 중인 컨테이너 없음 → Docker Compose 시작 필요"
        ISSUES_FOUND=true
    fi
fi

# 포트 체크
if ! netstat -tuln 2>/dev/null | grep -q ":8080 "; then
    log_error "포트 8080이 열려있지 않음 → 서비스 시작 필요"
    ISSUES_FOUND=true
fi

# 메모리 체크
MEMORY_MB=$(free -m | awk '/^Mem:/{print $2}')
if [ "$MEMORY_MB" -lt 1500 ] && ! swapon --show 2>/dev/null | grep -q "/"; then
    log_warning "메모리가 부족하고 스왑이 없음 → 스왑 추가 권장"
fi

echo ""
if [ "$ISSUES_FOUND" = false ]; then
    log_success "✅ 주요 문제가 발견되지 않았습니다"
    echo ""
    log_info "서비스 접속 테스트:"
    echo "  curl -I http://localhost:8080"
else
    log_error "❌ 문제가 발견되었습니다"
    echo ""
    log_info "수정 방법:"
    echo "  1. 자동 수정: bash fix_deployment.sh"
    echo "  2. 수동 확인: 위의 오류 메시지 참조"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_success "진단 완료!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"