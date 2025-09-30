#!/bin/bash
# Freqtrade Future 배포 문제 자동 수정 스크립트
# 사용법: bash fix_deployment.sh

set -e

echo "🔧 Freqtrade Future 배포 문제 자동 수정 시작..."
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

# Root 권한 확인
if [ "$EUID" -ne 0 ]; then
    log_error "이 스크립트는 root 권한이 필요합니다"
    echo "다음 명령어로 실행하세요: sudo bash fix_deployment.sh"
    exit 1
fi

ORIGINAL_USER="${SUDO_USER:-$USER}"
log_info "실행 사용자: $ORIGINAL_USER"
echo ""

# 1. 시스템 업데이트
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  시스템 업데이트"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_info "시스템 패키지 업데이트 중..."
export DEBIAN_FRONTEND=noninteractive
apt update -y >/dev/null 2>&1
apt upgrade -y >/dev/null 2>&1
log_success "시스템 업데이트 완료"
echo ""

# 2. Docker 설치 및 설정
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  Docker 설치 및 설정"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! command -v docker &> /dev/null; then
    log_info "Docker 설치 중..."

    # Docker GPG 키 및 저장소 추가
    apt install -y ca-certificates curl gnupg lsb-release >/dev/null 2>&1
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg 2>/dev/null

    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Docker 설치
    apt update >/dev/null 2>&1
    apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin >/dev/null 2>&1

    log_success "Docker 설치 완료: $(docker --version)"
else
    log_success "Docker가 이미 설치되어 있습니다: $(docker --version)"
fi

# Docker 서비스 시작
log_info "Docker 서비스 시작 중..."
systemctl enable docker >/dev/null 2>&1
systemctl start docker
log_success "Docker 서비스 실행 중"

# Docker 그룹에 사용자 추가
log_info "사용자를 Docker 그룹에 추가 중..."
usermod -aG docker "$ORIGINAL_USER"
log_success "Docker 권한 설정 완료"
echo ""

# 3. 기존 컨테이너 정리
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  기존 컨테이너 정리"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

log_info "기존 Freqtrade 컨테이너 중지 및 제거 중..."
docker ps -a --filter "name=freqtrade" --format "{{.Names}}" | while read container; do
    if [ -n "$container" ]; then
        log_info "  └─ 중지: $container"
        docker stop "$container" >/dev/null 2>&1 || true
        docker rm "$container" >/dev/null 2>&1 || true
    fi
done

# 미사용 컨테이너 정리
docker container prune -f >/dev/null 2>&1 || true
log_success "컨테이너 정리 완료"
echo ""

# 4. 프로젝트 디렉토리 확인 및 설정
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  프로젝트 디렉토리 설정"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PROJECT_DIR="/opt/freqtrade-futures"

# 기존 디렉토리 확인
POSSIBLE_DIRS=(
    "/opt/freqtrade-futures"
    "/home/$ORIGINAL_USER/freqtrade-future"
    "/home/$ORIGINAL_USER/freqtrade-future-phase10"
    "/home/freqtrade/freqtrade-future"
)

FOUND_DIR=""
for dir in "${POSSIBLE_DIRS[@]}"; do
    if [ -d "$dir" ] && [ -f "$dir/docker-compose.yml" ]; then
        FOUND_DIR="$dir"
        log_success "기존 프로젝트 발견: $dir"
        break
    fi
done

if [ -n "$FOUND_DIR" ]; then
    PROJECT_DIR="$FOUND_DIR"
    log_info "기존 프로젝트 사용: $PROJECT_DIR"
else
    log_info "새 프로젝트 디렉토리 생성 중..."

    if [ -d "$PROJECT_DIR" ]; then
        # 백업
        BACKUP_DIR="/backup/freqtrade_$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$(dirname $BACKUP_DIR)"
        mv "$PROJECT_DIR" "$BACKUP_DIR"
        log_info "기존 디렉토리 백업: $BACKUP_DIR"
    fi

    mkdir -p "$PROJECT_DIR"
    cd "$PROJECT_DIR"

    log_info "GitHub에서 프로젝트 클론 중..."
    if command -v git &> /dev/null; then
        sudo -u "$ORIGINAL_USER" git clone https://github.com/jilee1212/freqtrade-future.git . 2>/dev/null || {
            log_warning "Git clone 실패, 압축 파일 다운로드 중..."
            curl -L https://github.com/jilee1212/freqtrade-future/archive/master.tar.gz | tar xz --strip-components=1
        }
    else
        log_info "Git이 없음, 압축 파일 다운로드 중..."
        curl -L https://github.com/jilee1212/freqtrade-future/archive/master.tar.gz | tar xz --strip-components=1
    fi

    log_success "프로젝트 다운로드 완료"
fi

chown -R "$ORIGINAL_USER:$ORIGINAL_USER" "$PROJECT_DIR"
log_success "프로젝트 디렉토리: $PROJECT_DIR"
echo ""

# 5. 환경 설정 파일 생성
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  환경 설정 파일 생성"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$PROJECT_DIR"

if [ ! -f ".env" ]; then
    log_info ".env 파일 생성 중..."
    cat > .env << 'EOF'
# Binance API (테스트넷)
BINANCE_API_KEY=16sriPIRmf6AE4AHdNP2N6vSaymm3VHMGm4oJ9gGmrf4GcxhaaG0NG59vF632JaJ
BINANCE_API_SECRET=tk4XVhMB5AOH6Q3YSwLHetKy97TwdmkfiQRB0gkvCLqeqQyZ1RhwkcVfbz6WxFHt

# FreqUI 인증
JWT_SECRET_KEY=freqtrade_jwt_secret_key_change_in_production_2024
API_USERNAME=admin
API_PASSWORD=freqtrade2024!

# 시스템 설정
TZ=Asia/Seoul
FREQTRADE_ENV=production
EOF
    chown "$ORIGINAL_USER:$ORIGINAL_USER" .env
    chmod 600 .env
    log_success ".env 파일 생성 완료"
else
    log_success ".env 파일이 이미 존재합니다"
fi
echo ""

# 6. 필요한 디렉토리 생성
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6️⃣  필요한 디렉토리 생성"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

mkdir -p "$PROJECT_DIR/user_data/logs"
mkdir -p "$PROJECT_DIR/user_data/data"
mkdir -p "$PROJECT_DIR/user_data/strategies"
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "/var/log/freqtrade"

chown -R "$ORIGINAL_USER:$ORIGINAL_USER" "$PROJECT_DIR/user_data"
chown -R "$ORIGINAL_USER:$ORIGINAL_USER" "$PROJECT_DIR/logs"
chown -R "$ORIGINAL_USER:$ORIGINAL_USER" "/var/log/freqtrade"

log_success "디렉토리 구조 생성 완료"
echo ""

# 7. 스왑 파일 설정 (메모리 부족 대비)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7️⃣  스왑 메모리 설정"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

MEMORY_MB=$(free -m | awk '/^Mem:/{print $2}')
log_info "시스템 메모리: ${MEMORY_MB}MB"

if [ "$MEMORY_MB" -lt 2000 ]; then
    if ! swapon --show | grep -q "/swapfile"; then
        log_info "스왑 파일 생성 중 (2GB)..."
        fallocate -l 2G /swapfile 2>/dev/null || dd if=/dev/zero of=/swapfile bs=1M count=2048 2>/dev/null
        chmod 600 /swapfile
        mkswap /swapfile >/dev/null 2>&1
        swapon /swapfile
        echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab >/dev/null
        echo 'vm.swappiness=10' | tee -a /etc/sysctl.conf >/dev/null
        sysctl -p >/dev/null 2>&1
        log_success "스왑 파일 생성 완료"
    else
        log_success "스왑이 이미 활성화되어 있습니다"
    fi
else
    log_info "메모리가 충분합니다. 스왑 생략"
fi
echo ""

# 8. 방화벽 설정
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "8️⃣  방화벽 설정"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v ufw &> /dev/null; then
    log_info "UFW 방화벽 설정 중..."
    ufw --force enable >/dev/null 2>&1
    ufw allow 22/tcp comment 'SSH' >/dev/null 2>&1
    ufw allow 80/tcp comment 'HTTP' >/dev/null 2>&1
    ufw allow 443/tcp comment 'HTTPS' >/dev/null 2>&1
    ufw allow 8080/tcp comment 'FreqUI' >/dev/null 2>&1
    ufw allow 5000/tcp comment 'Dashboard' >/dev/null 2>&1
    log_success "방화벽 설정 완료"
else
    log_warning "UFW가 설치되지 않음. 수동으로 포트를 열어주세요: 8080, 5000, 80, 443"
fi
echo ""

# 9. Docker Compose 시작
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "9️⃣  Docker Compose 시작"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$PROJECT_DIR"

log_info "Docker 이미지 다운로드 중..."
sudo -u "$ORIGINAL_USER" docker compose pull 2>/dev/null || {
    log_warning "일부 이미지 다운로드 실패, 계속 진행합니다..."
}

log_info "Docker Compose 서비스 시작 중..."
sudo -u "$ORIGINAL_USER" docker compose up -d

log_info "서비스 시작 대기 중 (30초)..."
sleep 30

# 서비스 상태 확인
log_info "서비스 상태 확인 중..."
docker compose ps

RUNNING_COUNT=$(docker compose ps --format json 2>/dev/null | grep -c "running" || echo "0")
if [ "$RUNNING_COUNT" -gt 0 ]; then
    log_success "Docker 서비스가 정상적으로 실행 중입니다 ($RUNNING_COUNT개 컨테이너)"
else
    log_warning "일부 서비스가 시작되지 않았을 수 있습니다"
    log_info "로그 확인: cd $PROJECT_DIR && docker compose logs"
fi
echo ""

# 10. 서비스 연결 테스트
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔟 서비스 연결 테스트"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

sleep 5

log_info "FreqUI 접속 테스트..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080 | grep -q "200\|302\|401"; then
    log_success "FreqUI 접속 가능 (포트 8080)"
else
    log_warning "FreqUI 접속 불가. 로그를 확인하세요."
fi

log_info "웹 대시보드 접속 테스트..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 | grep -q "200\|302"; then
    log_success "웹 대시보드 접속 가능 (포트 5000)"
else
    log_warning "웹 대시보드 접속 불가"
fi
echo ""

# 11. systemd 서비스 등록
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣1️⃣ systemd 서비스 등록"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

log_info "systemd 서비스 생성 중..."
cat > /etc/systemd/system/freqtrade-futures.service << EOF
[Unit]
Description=Freqtrade Futures Trading Bot
Requires=docker.service
After=docker.service

[Service]
Type=forking
User=$ORIGINAL_USER
Group=docker
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
ExecReload=/usr/bin/docker compose restart
TimeoutStartSec=300
TimeoutStopSec=120
RestartSec=30
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable freqtrade-futures >/dev/null 2>&1
log_success "systemd 서비스 등록 완료"
echo ""

# 12. 최종 정보 출력
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 배포 수정 완료!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "IP_확인_불가")

log_success "배포 완료 시간: $(date)"
echo ""

echo "🌐 서버 정보:"
echo "   - 서버 IP: $SERVER_IP"
echo "   - 프로젝트: $PROJECT_DIR"
echo "   - 운영체제: $(lsb_release -ds 2>/dev/null)"
echo ""

echo "🔗 접속 정보:"
echo "   - FreqUI: http://$SERVER_IP:8080"
echo "   - 웹 대시보드: http://$SERVER_IP:5000"
echo "   - 로그인:"
echo "     * Username: admin"
echo "     * Password: freqtrade2024!"
echo ""

echo "📊 실행 중인 서비스:"
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || docker ps
echo ""

echo "🛠️ 유용한 명령어:"
echo "   - 서비스 상태: sudo systemctl status freqtrade-futures"
echo "   - 로그 확인: cd $PROJECT_DIR && docker compose logs -f"
echo "   - 서비스 재시작: sudo systemctl restart freqtrade-futures"
echo "   - 진단 실행: bash diagnose_server.sh"
echo ""

log_success "✅ 모든 수정이 완료되었습니다!"
echo "🌐 웹 브라우저에서 http://$SERVER_IP:8080 에 접속하세요!"
echo ""