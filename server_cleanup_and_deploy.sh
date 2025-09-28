#!/bin/bash
# 기존 서버 정리 및 새로운 Phase 10 시스템 배포 스크립트
# 서버: 141.164.42.93 (Seoul)
# 사용자: linuxuser

set -e

echo "🔍 기존 Vultr 서버 정리 및 Phase 10 새로운 배포 시작..."
echo "📅 시작 시간: $(date)"
echo "🖥️  서버: 141.164.42.93 (Seoul, 1GB RAM)"
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

# 1. 현재 시스템 상태 확인
log_info "현재 시스템 상태 확인 중..."
echo "현재 사용자: $(whoami)"
echo "현재 디렉토리: $(pwd)"
echo "시스템 정보: $(uname -a)"
echo "메모리 사용량:"
free -h
echo ""

# 2. 기존 Freqtrade 관련 프로세스 확인
log_info "기존 Freqtrade 프로세스 확인 중..."
if pgrep -f "freqtrade" > /dev/null; then
    log_warning "기존 Freqtrade 프로세스 발견됨"
    ps aux | grep -i freqtrade | grep -v grep || true

    # 기존 프로세스 종료
    log_info "기존 Freqtrade 프로세스 종료 중..."
    sudo pkill -f freqtrade || true
    sleep 5
else
    log_success "실행 중인 Freqtrade 프로세스 없음"
fi

# 3. 기존 Docker 컨테이너 확인 및 정리
log_info "기존 Docker 컨테이너 확인 중..."
if command -v docker &> /dev/null; then
    if docker ps -a | grep -q freqtrade; then
        log_warning "기존 Freqtrade Docker 컨테이너 발견됨"
        docker ps -a | grep freqtrade || true

        # 컨테이너 중지 및 제거
        log_info "기존 Freqtrade 컨테이너 정리 중..."
        docker stop $(docker ps -q --filter name=freqtrade) 2>/dev/null || true
        docker rm $(docker ps -aq --filter name=freqtrade) 2>/dev/null || true
        log_success "기존 컨테이너 정리 완료"
    else
        log_success "Freqtrade 관련 컨테이너 없음"
    fi
else
    log_info "Docker가 설치되지 않음 - 새로 설치 예정"
fi

# 4. 기존 프로젝트 디렉토리 확인 및 백업
log_info "기존 프로젝트 디렉토리 확인 중..."
BACKUP_DIR="/home/linuxuser/backup_$(date +%Y%m%d_%H%M%S)"

# 일반적인 Freqtrade 설치 위치들 확인
POSSIBLE_DIRS=(
    "/home/linuxuser/freqtrade"
    "/home/linuxuser/freqtrade_futures"
    "/home/linuxuser/freqtrade-future"
    "/opt/freqtrade"
    "/opt/freqtrade-futures"
    "/root/freqtrade"
)

FOUND_PROJECTS=()
for dir in "${POSSIBLE_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        log_warning "기존 프로젝트 발견: $dir"
        FOUND_PROJECTS+=("$dir")
    fi
done

if [ ${#FOUND_PROJECTS[@]} -gt 0 ]; then
    log_info "기존 프로젝트 백업 중..."
    mkdir -p "$BACKUP_DIR"

    for project in "${FOUND_PROJECTS[@]}"; do
        project_name=$(basename "$project")
        log_info "백업 중: $project -> $BACKUP_DIR/$project_name"
        cp -r "$project" "$BACKUP_DIR/$project_name" 2>/dev/null || true

        # 설정 파일만 별도 백업
        if [ -f "$project/user_data/config.json" ]; then
            cp "$project/user_data/config.json" "$BACKUP_DIR/${project_name}_config.json" 2>/dev/null || true
        fi
        if [ -f "$project/.env" ]; then
            cp "$project/.env" "$BACKUP_DIR/${project_name}_env" 2>/dev/null || true
        fi
    done

    log_success "백업 완료: $BACKUP_DIR"

    # 기존 디렉토리 제거
    log_info "기존 프로젝트 디렉토리 제거 중..."
    for project in "${FOUND_PROJECTS[@]}"; do
        sudo rm -rf "$project" 2>/dev/null || true
        log_info "제거됨: $project"
    done
else
    log_success "기존 프로젝트 없음 - 새로 설치 진행"
fi

# 5. 시스템 패키지 업데이트
log_info "시스템 패키지 업데이트 중..."
sudo apt update > /dev/null 2>&1
sudo apt upgrade -y > /dev/null 2>&1
log_success "시스템 업데이트 완료"

# 6. 필수 패키지 설치
log_info "필수 패키지 설치 중..."
sudo apt install -y curl wget git htop nano vim ufw fail2ban \
    software-properties-common apt-transport-https \
    ca-certificates gnupg lsb-release tree > /dev/null 2>&1
log_success "필수 패키지 설치 완료"

# 7. Docker 설치 (필요한 경우)
log_info "Docker 설치 확인 중..."
if ! command -v docker &> /dev/null; then
    log_info "Docker 설치 중..."

    # Docker GPG 키 추가
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

    # Docker 저장소 추가
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Docker 설치
    sudo apt update > /dev/null 2>&1
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin > /dev/null 2>&1

    # Docker 서비스 시작
    sudo systemctl enable docker
    sudo systemctl start docker

    # 사용자를 docker 그룹에 추가
    sudo usermod -aG docker linuxuser

    log_success "Docker 설치 완료"
else
    log_success "Docker가 이미 설치되어 있습니다"

    # 사용자가 docker 그룹에 있는지 확인
    if ! groups linuxuser | grep -q docker; then
        sudo usermod -aG docker linuxuser
        log_info "linuxuser를 docker 그룹에 추가했습니다"
    fi
fi

# 8. freqtrade 사용자 생성 (이미 있으면 스킵)
log_info "freqtrade 사용자 확인 중..."
if ! id "freqtrade" &>/dev/null; then
    log_info "freqtrade 사용자 생성 중..."
    sudo adduser --disabled-password --gecos "" freqtrade
    sudo usermod -aG sudo,docker freqtrade

    # sudo 비밀번호 없이 실행 설정
    echo "freqtrade ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/freqtrade > /dev/null
    sudo chmod 440 /etc/sudoers.d/freqtrade
    log_success "freqtrade 사용자 생성 완료"
else
    log_success "freqtrade 사용자가 이미 존재합니다"
    sudo usermod -aG docker freqtrade
fi

# 9. 방화벽 설정
log_info "방화벽 설정 중..."
sudo ufw --force reset > /dev/null 2>&1
sudo ufw default deny incoming > /dev/null 2>&1
sudo ufw default allow outgoing > /dev/null 2>&1
sudo ufw allow 22/tcp comment 'SSH' > /dev/null 2>&1
sudo ufw allow 80/tcp comment 'HTTP' > /dev/null 2>&1
sudo ufw allow 443/tcp comment 'HTTPS' > /dev/null 2>&1
sudo ufw allow 8080/tcp comment 'FreqUI' > /dev/null 2>&1
echo "y" | sudo ufw enable > /dev/null 2>&1
log_success "방화벽 설정 완료"

# 10. 프로젝트 디렉토리 생성
log_info "프로젝트 디렉토리 설정 중..."
sudo mkdir -p /opt/freqtrade-futures
sudo mkdir -p /var/log/freqtrade
sudo mkdir -p /backup/freqtrade
sudo chown -R freqtrade:freqtrade /opt/freqtrade-futures
sudo chown -R freqtrade:freqtrade /var/log/freqtrade
sudo chown -R freqtrade:freqtrade /backup/freqtrade
log_success "디렉토리 구조 생성 완료"

# 11. 스왑 파일 생성/확인 (1GB RAM 환경 최적화)
log_info "스왑 파일 확인 중..."
if [ ! -f /swapfile ]; then
    log_info "스왑 파일 생성 중..."
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile > /dev/null 2>&1
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab > /dev/null
    echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf > /dev/null
    log_success "2GB 스왑 파일 생성 완료"
else
    log_success "스왑 파일이 이미 존재합니다"
    swapon --show
fi

# 12. 시간대 설정
log_info "시간대 설정 중..."
sudo timedatectl set-timezone Asia/Seoul
log_success "시간대를 Asia/Seoul로 설정 완료"

# 13. GitHub에서 새로운 프로젝트 클론
log_info "GitHub에서 새로운 Phase 10 프로젝트 클론 중..."
cd /opt/freqtrade-futures
sudo -u freqtrade git clone https://github.com/jilee1212/freqtrade-future.git .
log_success "GitHub 프로젝트 클론 완료"

# 14. 환경 변수 설정 파일 생성
log_info "환경 변수 설정 중..."
sudo -u freqtrade cat > .env << 'EOF'
# Binance API 설정 (테스트넷)
BINANCE_API_KEY=16sriPIRmf6AE4AHdNP2N6vSaymm3VHMGm4oJ9gGmrf4GcxhaaG0NG59vF632JaJ
BINANCE_API_SECRET=tk4XVhMB5AOH6Q3YSwLHetKy97TwdmkfiQRB0gkvCLqeqQyZ1RhwkcVfbz6WxFHt

# FreqUI 인증 설정
JWT_SECRET_KEY=phase10_jwt_secret_key_2024_freqtrade_futures
API_USERNAME=admin
API_PASSWORD=freqtrade2024!
WS_TOKEN=phase10_websocket_token_secure

# 텔레그램 설정 (선택사항)
TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# 데이터베이스 설정
DB_PASSWORD=freqtrade_db_password_2024_secure

# 시스템 설정
TZ=Asia/Seoul
FREQTRADE_ENV=production
EOF

sudo chown freqtrade:freqtrade .env
sudo chmod 600 .env
log_success "환경 변수 설정 완료"

# 15. 스크립트 실행 권한 설정
log_info "스크립트 권한 설정 중..."
sudo find /opt/freqtrade-futures -name "*.py" -exec chmod +x {} \;
sudo find /opt/freqtrade-futures -name "*.sh" -exec chmod +x {} \;
sudo chown -R freqtrade:freqtrade /opt/freqtrade-futures
log_success "스크립트 권한 설정 완료"

# 16. Docker Compose 실행
log_info "Docker Compose 서비스 시작 중..."
sudo -u freqtrade docker compose pull
sudo -u freqtrade docker compose up -d

# 서비스 시작 대기
log_info "서비스 시작 대기 중..."
sleep 30

# 17. 서비스 상태 확인
log_info "서비스 상태 확인 중..."
if sudo -u freqtrade docker compose ps | grep -q "Up"; then
    log_success "Docker 서비스가 정상적으로 실행 중입니다"
else
    log_warning "일부 서비스가 실행되지 않았을 수 있습니다"
fi

# 18. systemd 서비스 등록
log_info "systemd 서비스 등록 중..."
sudo cat > /etc/systemd/system/freqtrade-futures.service << 'EOF'
[Unit]
Description=Freqtrade Futures Trading Bot - Phase 10
Requires=docker.service
After=docker.service

[Service]
Type=forking
User=freqtrade
Group=docker
WorkingDirectory=/opt/freqtrade-futures
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
ExecReload=/usr/bin/docker compose restart
TimeoutStartSec=300
TimeoutStopSec=120
RestartSec=30
Restart=always
EnvironmentFile=/opt/freqtrade-futures/.env

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable freqtrade-futures
log_success "systemd 서비스 등록 완료"

# 19. 최종 정리 및 확인
echo ""
echo "🎉 기존 서버 정리 및 Phase 10 새로운 배포 완료!"
echo "=================================================="
log_success "배포 완료 시간: $(date)"
echo ""

# 서버 정보 출력
echo "🌐 서버 정보:"
echo "   - 서버 IP: 141.164.42.93"
echo "   - 위치: Seoul, Korea"
echo "   - 사양: 1 vCPU, 1GB RAM, 25GB SSD"
echo "   - 운영체제: Ubuntu $(lsb_release -rs)"
echo "   - Docker 버전: $(docker --version | cut -d' ' -f3 | cut -d',' -f1)"
echo ""

echo "🔗 접속 정보:"
echo "   - FreqUI 웹 인터페이스: http://141.164.42.93:8080"
echo "   - SSH 접속: ssh linuxuser@141.164.42.93"
echo "   - FreqTrade 사용자: ssh freqtrade@141.164.42.93"
echo "   - 로그인 정보:"
echo "     * Username: admin"
echo "     * Password: freqtrade2024!"
echo ""

echo "📊 현재 서비스 상태:"
sudo -u freqtrade docker compose ps
echo ""

echo "💾 백업 정보:"
if [ ${#FOUND_PROJECTS[@]} -gt 0 ]; then
    echo "   - 기존 프로젝트 백업: $BACKUP_DIR"
    echo "   - 백업된 프로젝트: ${FOUND_PROJECTS[*]}"
else
    echo "   - 백업된 기존 프로젝트 없음 (신규 설치)"
fi
echo ""

echo "📋 Phase 10 주요 기능:"
echo "   ✅ Master Integration Controller"
echo "   ✅ AI Risk Management System"
echo "   ✅ Ross Cameron RSI Strategy"
echo "   ✅ Real-time Web Dashboard"
echo "   ✅ Production Monitoring"
echo "   ✅ Safety & Compliance"
echo "   ✅ Automated Maintenance"
echo ""

echo "🔄 다음 단계:"
echo "   1. 웹 브라우저에서 http://141.164.42.93:8080 접속"
echo "   2. admin/freqtrade2024! 로 로그인"
echo "   3. Phase 10 시스템 동작 확인"
echo "   4. nosignup.kr 도메인을 141.164.42.93으로 연결"
echo "   5. SSL 인증서 설정 (선택사항)"
echo ""

echo "🛠️ 유용한 명령어:"
echo "   - 서비스 상태: sudo systemctl status freqtrade-futures"
echo "   - 로그 확인: cd /opt/freqtrade-futures && docker compose logs -f"
echo "   - 모니터링: cd /opt/freqtrade-futures && ./production_monitor.py"
echo "   - 서비스 재시작: sudo systemctl restart freqtrade-futures"
echo ""

log_success "✅ 기존 서버 정리 및 Phase 10 새로운 배포가 성공적으로 완료되었습니다!"
echo "🌐 이제 http://141.164.42.93:8080 또는 nosignup.kr (DNS 연결 후)로 접속하여"
echo "   완전한 Phase 10 Freqtrade Future 시스템을 사용할 수 있습니다!"