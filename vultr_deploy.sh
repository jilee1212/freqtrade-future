#!/bin/bash
# Vultr 서버 자동 배포 스크립트
# GitHub: https://github.com/jilee1212/freqtrade-future.git

set -e  # 오류 발생시 스크립트 중단

echo "🚀 Vultr 서버 Freqtrade Future 자동 배포 시작..."
echo "📅 배포 시작 시간: $(date)"
echo ""

# 색상 코드 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
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

# 1. 시스템 환경 체크
log_info "시스템 환경 확인 중..."
if [ "$(id -u)" = "0" ]; then
    log_info "Root 사용자로 실행 중"
else
    log_error "이 스크립트는 root 권한이 필요합니다"
    exit 1
fi

# OS 확인
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [ "$ID" != "ubuntu" ]; then
        log_error "이 스크립트는 Ubuntu에서만 실행됩니다"
        exit 1
    fi
    log_success "Ubuntu $VERSION_ID 확인됨"
else
    log_error "지원하지 않는 운영체제입니다"
    exit 1
fi

# 2. 시스템 업데이트
log_info "시스템 패키지 업데이트 중..."
export DEBIAN_FRONTEND=noninteractive
apt update > /dev/null 2>&1
apt upgrade -y > /dev/null 2>&1
log_success "시스템 업데이트 완료"

# 3. 필수 패키지 설치
log_info "필수 패키지 설치 중..."
apt install -y curl wget git htop nano vim ufw fail2ban \
    software-properties-common apt-transport-https \
    ca-certificates gnupg lsb-release tree > /dev/null 2>&1
log_success "기본 패키지 설치 완료"

# 4. Docker 설치
log_info "Docker 설치 중..."
if ! command -v docker &> /dev/null; then
    # Docker GPG 키 추가
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

    # Docker 저장소 추가
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Docker 설치
    apt update > /dev/null 2>&1
    apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin > /dev/null 2>&1

    # Docker 서비스 시작
    systemctl enable docker
    systemctl start docker
    log_success "Docker 설치 및 서비스 시작 완료"
else
    log_success "Docker가 이미 설치되어 있습니다"
fi

# 5. freqtrade 사용자 생성
log_info "freqtrade 사용자 생성 중..."
if ! id "freqtrade" &>/dev/null; then
    adduser --disabled-password --gecos "" freqtrade
    usermod -aG sudo,docker freqtrade

    # sudo 비밀번호 없이 실행 설정
    echo "freqtrade ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/freqtrade
    chmod 440 /etc/sudoers.d/freqtrade
    log_success "freqtrade 사용자 생성 및 sudo NOPASSWD 설정 완료"
else
    log_success "freqtrade 사용자가 이미 존재합니다"
    usermod -aG docker freqtrade
fi

# 6. 방화벽 설정
log_info "방화벽 설정 중..."
ufw --force reset > /dev/null 2>&1
ufw default deny incoming > /dev/null 2>&1
ufw default allow outgoing > /dev/null 2>&1
ufw allow 22/tcp comment 'SSH' > /dev/null 2>&1
ufw allow 80/tcp comment 'HTTP' > /dev/null 2>&1
ufw allow 443/tcp comment 'HTTPS' > /dev/null 2>&1
ufw allow 8080/tcp comment 'FreqUI' > /dev/null 2>&1
echo "y" | ufw enable > /dev/null 2>&1
log_success "방화벽 설정 완료"

# 7. 프로젝트 디렉토리 생성
log_info "프로젝트 디렉토리 설정 중..."
mkdir -p /opt/freqtrade-futures
mkdir -p /var/log/freqtrade
mkdir -p /backup/freqtrade
chown -R freqtrade:freqtrade /opt/freqtrade-futures
chown -R freqtrade:freqtrade /var/log/freqtrade
chown -R freqtrade:freqtrade /backup/freqtrade
log_success "디렉토리 구조 생성 완료"

# 8. 스왑 파일 생성 (메모리 최적화)
log_info "스왑 파일 생성 중..."
if [ ! -f /swapfile ]; then
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile > /dev/null 2>&1
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo 'vm.swappiness=10' >> /etc/sysctl.conf
    log_success "2GB 스왑 파일 생성 완료"
else
    log_success "스왑 파일이 이미 존재합니다"
fi

# 9. 시간대 설정
log_info "시간대 설정 중..."
timedatectl set-timezone Asia/Seoul
log_success "시간대를 Asia/Seoul로 설정 완료"

# 10. fail2ban 설정
log_info "fail2ban 설정 중..."
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
ignoreip = 127.0.0.1/8 ::1

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
EOF

systemctl enable fail2ban > /dev/null 2>&1
systemctl start fail2ban > /dev/null 2>&1
log_success "fail2ban 보안 설정 완료"

# 11. GitHub에서 프로젝트 클론
log_info "GitHub에서 프로젝트 클론 중..."
cd /opt/freqtrade-futures
if [ -d ".git" ]; then
    log_info "기존 Git 저장소 업데이트 중..."
    sudo -u freqtrade git pull origin main
else
    log_info "새로운 저장소 클론 중..."
    sudo -u freqtrade git clone https://github.com/jilee1212/freqtrade-future.git .
fi
log_success "GitHub 프로젝트 클론 완료"

# 12. 환경 변수 설정 파일 생성
log_info "환경 변수 설정 중..."
if [ ! -f .env ]; then
    sudo -u freqtrade cat > .env << 'EOF'
# Binance API 설정 (테스트넷)
BINANCE_API_KEY=16sriPIRmf6AE4AHdNP2N6vSaymm3VHMGm4oJ9gGmrf4GcxhaaG0NG59vF632JaJ
BINANCE_API_SECRET=tk4XVhMB5AOH6Q3YSwLHetKy97TwdmkfiQRB0gkvCLqeqQyZ1RhwkcVfbz6WxFHt

# FreqUI 인증 설정
JWT_SECRET_KEY=your_jwt_secret_key_here_change_in_production
API_USERNAME=admin
API_PASSWORD=freqtrade2024!
WS_TOKEN=your_websocket_token_here

# 텔레그램 설정 (선택사항)
TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# 데이터베이스 설정
DB_PASSWORD=freqtrade_db_password_2024

# 시스템 설정
TZ=Asia/Seoul
FREQTRADE_ENV=production
EOF
    chown freqtrade:freqtrade .env
    chmod 600 .env
    log_success "환경 변수 설정 파일 생성 완료"
else
    log_success "환경 변수 설정 파일이 이미 존재합니다"
fi

# 13. Docker Compose 실행
log_info "Docker Compose 서비스 시작 중..."
sudo -u freqtrade docker compose pull
sudo -u freqtrade docker compose up -d

# 서비스 시작 대기
log_info "서비스 시작 대기 중..."
sleep 30

# 14. 서비스 상태 확인
log_info "서비스 상태 확인 중..."
if sudo -u freqtrade docker compose ps | grep -q "Up"; then
    log_success "Docker 서비스가 정상적으로 실행 중입니다"
else
    log_warning "일부 서비스가 실행되지 않았을 수 있습니다"
fi

# 15. systemd 서비스 등록
log_info "systemd 서비스 등록 중..."
cat > /etc/systemd/system/freqtrade-futures.service << 'EOF'
[Unit]
Description=Freqtrade Futures Trading Bot
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

systemctl daemon-reload
systemctl enable freqtrade-futures
log_success "systemd 서비스 등록 완료"

# 16. 모니터링 스크립트 실행 권한 설정
log_info "모니터링 스크립트 권한 설정 중..."
find /opt/freqtrade-futures -name "*.py" -exec chmod +x {} \;
find /opt/freqtrade-futures -name "*.sh" -exec chmod +x {} \;
log_success "스크립트 권한 설정 완료"

# 17. 서버 정보 출력
echo ""
echo "🎉 Vultr 서버 배포 완료!"
echo "=================================================="
log_success "배포 완료 시간: $(date)"
echo ""

# 서버 IP 확인
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "IP 확인 실패")
echo "🌐 서버 정보:"
echo "   - 서버 IP: $SERVER_IP"
echo "   - 운영체제: Ubuntu $(lsb_release -rs)"
echo "   - Docker 버전: $(docker --version | cut -d' ' -f3 | cut -d',' -f1)"
echo ""

echo "🔗 접속 정보:"
echo "   - FreqUI 웹 인터페이스: http://$SERVER_IP:8080"
echo "   - SSH 접속: ssh freqtrade@$SERVER_IP"
echo "   - 로그인 정보:"
echo "     * Username: admin"
echo "     * Password: freqtrade2024!"
echo ""

echo "📊 서비스 상태:"
sudo -u freqtrade docker compose ps
echo ""

echo "📋 다음 단계:"
echo "   1. 웹 브라우저에서 http://$SERVER_IP:8080 접속"
echo "   2. admin/freqtrade2024! 로 로그인"
echo "   3. 실제 API 키로 환경 변수 업데이트"
echo "   4. nosignup.kr 도메인 연결 (DNS A 레코드: $SERVER_IP)"
echo "   5. SSL 인증서 설정"
echo ""

echo "🛠️ 유용한 명령어:"
echo "   - 서비스 상태: sudo systemctl status freqtrade-futures"
echo "   - 로그 확인: cd /opt/freqtrade-futures && docker compose logs -f"
echo "   - 서비스 재시작: sudo systemctl restart freqtrade-futures"
echo "   - 모니터링: cd /opt/freqtrade-futures && ./production_monitor.py"
echo ""

log_success "✅ 모든 배포 과정이 완료되었습니다!"
echo "🚀 이제 nosignup.kr 도메인을 $SERVER_IP 로 연결하시면 바로 사용 가능합니다!"