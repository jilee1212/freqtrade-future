# Vultr VPS 설정 가이드
## Phase 8: 클라우드 인프라 구축

### 🚀 서버 스펙 권장사항

#### **프로덕션 환경**
- **CPU**: 4 vCPUs 이상
- **RAM**: 8GB 이상
- **Storage**: 160GB SSD 이상
- **Bandwidth**: 4TB/월 이상
- **OS**: Ubuntu 22.04 LTS

#### **개발/테스트 환경**
- **CPU**: 2 vCPUs
- **RAM**: 4GB
- **Storage**: 80GB SSD
- **Bandwidth**: 3TB/월
- **OS**: Ubuntu 22.04 LTS

### 📋 Vultr 서버 생성 단계

#### **1. Vultr 계정 생성**
1. [Vultr.com](https://vultr.com) 회원가입
2. 결제 방법 등록 ($10-50 충전 권장)
3. API 키 생성 (선택사항)

#### **2. 서버 인스턴스 생성**
```bash
# Vultr 대시보드에서 설정
Server Type: Cloud Compute - Regular Performance
Location: Tokyo, Japan (한국과 가까운 지역)
Operating System: Ubuntu 22.04 x64
Server Size: $24/month (4 vCPU, 8GB RAM, 160GB SSD)
```

#### **3. SSH 키 설정**
```bash
# 로컬에서 SSH 키 생성
ssh-keygen -t rsa -b 4096 -C "freqtrade@yourdomain.com"

# 공개키를 Vultr에 추가
cat ~/.ssh/id_rsa.pub
```

#### **4. 방화벽 설정**
```bash
# Vultr 방화벽 그룹 생성
- SSH (22) - 본인 IP만 허용
- HTTP (80) - 전체 허용
- HTTPS (443) - 전체 허용
- Dashboard (5000) - 본인 IP만 허용
- Grafana (3000) - 본인 IP만 허용
```

### 🔧 서버 초기 설정

#### **1. 서버 접속**
```bash
# Vultr에서 제공하는 IP로 접속
ssh root@YOUR_SERVER_IP
```

#### **2. 사용자 계정 생성**
```bash
# 새 사용자 생성
adduser freqtrade

# sudo 권한 부여
usermod -aG sudo freqtrade

# SSH 키 복사
mkdir -p /home/freqtrade/.ssh
cp ~/.ssh/authorized_keys /home/freqtrade/.ssh/
chown -R freqtrade:freqtrade /home/freqtrade/.ssh
chmod 700 /home/freqtrade/.ssh
chmod 600 /home/freqtrade/.ssh/authorized_keys
```

#### **3. 보안 설정**
```bash
# SSH 설정 강화
nano /etc/ssh/sshd_config

# 다음 설정 변경:
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
Port 22  # 원한다면 다른 포트로 변경

# SSH 서비스 재시작
systemctl restart sshd
```

#### **4. 방화벽 설정**
```bash
# UFW 방화벽 설정
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 5000/tcp
ufw allow 3000/tcp
ufw allow 9090/tcp
ufw --force enable
```

### 📦 애플리케이션 배포

#### **1. 의존성 설치**
```bash
# freqtrade 사용자로 전환
su - freqtrade

# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 필수 패키지 설치
sudo apt install -y git curl wget htop iotop nethogs ncdu \
    build-essential libffi-dev libssl-dev python3-pip
```

#### **2. Docker 설치**
```bash
# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker freqtrade

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 재로그인 (Docker 그룹 반영)
exit && ssh freqtrade@YOUR_SERVER_IP
```

#### **3. 프로젝트 배포**
```bash
# 프로젝트 디렉토리 생성
sudo mkdir -p /opt/freqtrade-futures
sudo chown freqtrade:freqtrade /opt/freqtrade-futures

# 프로젝트 클론 (GitHub Repository 필요)
git clone https://github.com/yourusername/freqtrade-futures.git /opt/freqtrade-futures
cd /opt/freqtrade-futures

# 또는 파일 업로드
scp -r ./freqtrade_future/* freqtrade@YOUR_SERVER_IP:/opt/freqtrade-futures/
```

#### **4. 환경 설정**
```bash
cd /opt/freqtrade-futures

# 프로덕션 환경 파일 복사
cp .env.production .env

# 환경 변수 설정 (중요한 값들 변경)
nano .env

# 필수 변경 항목:
FREQTRADE_API_PASSWORD=강한_패스워드
FLASK_SECRET_KEY=랜덤_시크릿_키
GRAFANA_ADMIN_PASSWORD=강한_패스워드
BINANCE_API_KEY=실제_바이낸스_키
BINANCE_SECRET_KEY=실제_바이낸스_시크릿
TELEGRAM_BOT_TOKEN=텔레그램_봇_토큰
TELEGRAM_CHAT_ID=텔레그램_채팅_ID
```

#### **5. SSL 인증서 설정**
```bash
# Let's Encrypt 설치
sudo apt install certbot

# 도메인이 있는 경우
sudo certbot certonly --standalone -d yourdomain.com

# 인증서 복사
sudo mkdir -p /opt/freqtrade-futures/nginx/ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /opt/freqtrade-futures/nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /opt/freqtrade-futures/nginx/ssl/
sudo chown -R freqtrade:freqtrade /opt/freqtrade-futures/nginx/ssl

# 자동 갱신 설정
sudo crontab -e
# 다음 라인 추가:
0 2 * * * certbot renew --quiet
```

### 🚀 서비스 시작

#### **1. 애플리케이션 빌드 및 시작**
```bash
cd /opt/freqtrade-futures

# Docker 이미지 빌드
docker-compose build

# 서비스 시작
docker-compose up -d

# 서비스 상태 확인
docker-compose ps
```

#### **2. 헬스 체크**
```bash
# 웹 대시보드 확인
curl -f http://localhost:5000/health

# API 확인
curl -u freqtrade:패스워드 http://localhost:8080/api/v1/ping
```

#### **3. 로그 확인**
```bash
# 모든 서비스 로그 확인
docker-compose logs -f

# 특정 서비스 로그 확인
docker-compose logs -f freqtrade-bot
docker-compose logs -f web-dashboard
```

### 📊 모니터링 설정

#### **1. 접속 URL**
```bash
# 웹 대시보드
http://YOUR_SERVER_IP:5000

# Grafana
http://YOUR_SERVER_IP:3000
ID: admin / PW: .env 파일의 GRAFANA_ADMIN_PASSWORD

# Prometheus
http://YOUR_SERVER_IP:9090
```

#### **2. 자동화 설정**
```bash
# 자동 백업 설정
chmod +x scripts/backup.sh
chmod +x scripts/restore.sh

# Cron 작업 추가
crontab -e

# 다음 라인들 추가:
0 2 * * * /opt/freqtrade-futures/scripts/backup.sh
0 0 * * 0 docker system prune -f  # 주간 정리
```

### 🔐 보안 체크리스트

#### **✅ 필수 보안 설정**
- [ ] SSH 키 기반 인증 설정
- [ ] Root 로그인 비활성화
- [ ] 방화벽 (UFW) 활성화
- [ ] 강한 패스워드 설정
- [ ] SSL/TLS 인증서 설치
- [ ] API 키 환경변수 보호
- [ ] 정기 백업 설정
- [ ] 모니터링 알림 설정

#### **⚠️ 주의사항**
1. **API 키 보안**: 절대 코드에 하드코딩하지 말 것
2. **포트 접근 제한**: 필요한 포트만 열기
3. **정기 업데이트**: 시스템 및 애플리케이션 업데이트
4. **백업 확인**: 정기적으로 백업 복원 테스트
5. **로그 모니터링**: 이상 활동 감지

### 📞 문제 해결

#### **일반적인 문제들**

**1. Docker 권한 오류**
```bash
sudo usermod -aG docker $USER
# 재로그인 필요
```

**2. 포트 접근 불가**
```bash
# 방화벽 확인
sudo ufw status

# 포트 열기
sudo ufw allow 5000/tcp
```

**3. SSL 인증서 오류**
```bash
# 인증서 확인
sudo certbot certificates

# 수동 갱신
sudo certbot renew
```

**4. 메모리 부족**
```bash
# 메모리 사용량 확인
free -h
docker stats

# 스왑 메모리 추가 (필요시)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 📈 성능 최적화

#### **1. 서버 성능 튜닝**
```bash
# 시스템 리소스 모니터링
htop
iotop
nethogs

# Docker 리소스 제한 설정 (docker-compose.yml)
```

#### **2. 데이터베이스 최적화**
```bash
# SQLite 성능 튜닝
# user_data/config_futures.json에서 데이터베이스 설정 조정
```

#### **3. 네트워크 최적화**
```bash
# CDN 설정 (선택사항)
# Nginx 캐싱 설정
# Gzip 압축 활성화
```

---

**🎯 완료 후 확인사항:**
1. 웹 대시보드 정상 접속
2. Freqtrade API 동작 확인
3. 텔레그램 알림 테스트
4. 백업 시스템 테스트
5. 모니터링 대시보드 확인

**📞 지원:**
- GitHub Issues: 기술적 문제
- Telegram: 운영 관련 알림
- Grafana: 성능 모니터링