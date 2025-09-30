# 🚀 수동 배포 가이드 (Manual Deployment Guide)

Windows 환경에서 Vultr 서버로 배포하는 단계별 가이드입니다.

## 사전 준비

### 1. 필요한 도구 설치 확인

```powershell
# Git Bash 또는 Windows Terminal 사용
# SSH 클라이언트 확인
ssh -V

# Docker Desktop 실행 확인 (로컬 테스트용)
docker --version
```

### 2. 현재 로컬 서버 중지

```bash
# 현재 실행 중인 개발 서버들을 모두 중지
# Ctrl+C로 종료하거나
taskkill /F /IM node.exe
taskkill /F /IM python.exe
```

## 배포 방법 선택

### 방법 1: FileZilla/WinSCP 사용 (추천)

#### Step 1: 파일 업로드 준비

업로드할 파일 목록:
```
freqtrade-future/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
├── frontend/
│   ├── src/ (전체 폴더)
│   ├── public/ (전체 폴더)
│   ├── package.json
│   ├── package-lock.json
│   ├── next.config.ts
│   ├── tsconfig.json
│   ├── postcss.config.mjs
│   ├── components.json
│   ├── Dockerfile
│   └── .env.production
├── docker-compose.full.yml
└── user_data/
    └── config_futures.json
```

#### Step 2: FileZilla로 업로드

1. FileZilla 실행
2. 연결 정보:
   - Host: `sftp://141.164.42.93`
   - Username: `root`
   - Password: (서버 비밀번호)
   - Port: `22`

3. 원격 경로로 이동: `/root/freqtrade-future/`

4. 위 파일들을 드래그 앤 드롭으로 업로드

#### Step 3: PuTTY로 서버 접속 후 실행

1. PuTTY 실행
2. Host: `141.164.42.93`, Port: `22`
3. 접속 후 다음 명령어 실행:

```bash
cd /root/freqtrade-future

# 기존 컨테이너 중지
docker-compose down

# 새 이미지 빌드
docker-compose -f docker-compose.full.yml build

# 서비스 시작
docker-compose -f docker-compose.full.yml up -d

# 상태 확인
docker-compose -f docker-compose.full.yml ps

# 로그 확인
docker-compose -f docker-compose.full.yml logs -f
```

### 방법 2: Git 사용

#### Step 1: Git 저장소 설정 (로컬)

```bash
cd c:/Users/jilee/freqtrade-future

# Git 초기화 (아직 안했다면)
git init

# .gitignore 생성
cat > .gitignore << 'EOF'
node_modules/
.next/
*.log
.env.local
.DS_Store
__pycache__/
*.pyc
user_data/hyperopt_results/
user_data/plot/
EOF

# 파일 추가
git add .
git commit -m "Add full stack deployment files"

# GitHub/GitLab에 푸시
# git remote add origin <your-repo-url>
# git push -u origin master
```

#### Step 2: 서버에서 Clone

```bash
# PuTTY로 서버 접속 후
cd /root
git clone <your-repo-url> freqtrade-future-new

# 환경 파일 복사 (기존 설정 백업)
cp freqtrade-future/user_data/config_futures.json freqtrade-future-new/user_data/

cd freqtrade-future-new

# 빌드 및 실행
docker-compose -f docker-compose.full.yml build
docker-compose -f docker-compose.full.yml up -d
```

### 방법 3: Docker Hub 사용 (가장 빠름)

#### Step 1: Docker Hub에 이미지 푸시 (로컬)

```bash
# Docker Hub 로그인
docker login

# 이미지 빌드 및 태그
docker build -t your-username/freqtrade-backend:latest ./backend
docker build -t your-username/freqtrade-frontend:latest ./frontend

# 푸시
docker push your-username/freqtrade-backend:latest
docker push your-username/freqtrade-frontend:latest
```

#### Step 2: docker-compose 수정

`docker-compose.hub.yml` 파일 생성:
```yaml
version: '3.8'

services:
  freqtrade:
    image: freqtradeorg/freqtrade:stable
    container_name: freqtrade
    restart: always
    ports:
      - "8080:8080"
    volumes:
      - ./user_data:/freqtrade/user_data
    command: >
      trade
      --logfile /freqtrade/user_data/logs/freqtrade.log
      --db-url sqlite:////freqtrade/user_data/tradesv3.sqlite
      --config /freqtrade/user_data/config_futures.json
      --strategy EMAStrategy

  backend:
    image: your-username/freqtrade-backend:latest
    container_name: freqtrade-backend
    restart: always
    ports:
      - "5000:5000"
    environment:
      - PORT=5000
      - FREQTRADE_URL=http://freqtrade:8080
      - FREQTRADE_USERNAME=freqtrade
      - FREQTRADE_PASSWORD=futures2024
      - FLASK_ENV=production
    depends_on:
      - freqtrade

  frontend:
    image: your-username/freqtrade-frontend:latest
    container_name: freqtrade-frontend
    restart: always
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
    depends_on:
      - backend
```

#### Step 3: 서버에서 실행

```bash
# PuTTY로 서버 접속
cd /root/freqtrade-future

# docker-compose.hub.yml 업로드 후
docker-compose -f docker-compose.hub.yml pull
docker-compose -f docker-compose.hub.yml up -d
```

## 배포 후 확인

### 1. 서비스 상태 확인

```bash
# 컨테이너 상태
docker ps

# 로그 확인
docker-compose -f docker-compose.full.yml logs backend
docker-compose -f docker-compose.full.yml logs frontend
docker-compose -f docker-compose.full.yml logs freqtrade
```

### 2. 브라우저에서 접속

- **프론트엔드:** http://141.164.42.93:3000
- **백엔드 API:** http://141.164.42.93:5000/api/health
- **Freqtrade UI:** http://141.164.42.93:8080

### 3. API 테스트

로컬 PowerShell에서:
```powershell
# 백엔드 헬스 체크
curl http://141.164.42.93:5000/api/health

# 백엔드 상태
curl http://141.164.42.93:5000/api/status

# 프론트엔드
curl http://141.164.42.93:3000
```

또는 브라우저에서:
- http://141.164.42.93:5000/api/health
- http://141.164.42.93:5000/api/status
- http://141.164.42.93:3000

## 문제 해결

### Frontend 빌드 실패

```bash
# 서버에서 로그 확인
docker-compose logs frontend

# 메모리 부족 시 - 로컬에서 빌드 후 이미지 전송
docker build -t freqtrade-frontend ./frontend
docker save freqtrade-frontend > frontend-image.tar
# FileZilla로 frontend-image.tar 업로드
# 서버에서:
docker load < frontend-image.tar
```

### Backend API 연결 오류

```bash
# Freqtrade 컨테이너 접근 테스트
docker exec -it freqtrade-backend curl http://freqtrade:8080/api/v1/status

# 환경변수 확인
docker exec freqtrade-backend env | grep FREQTRADE
```

### 포트 충돌

```bash
# 포트 사용 확인
netstat -tulpn | grep -E ':(3000|5000|8080)'

# 기존 컨테이너 완전 제거
docker-compose down -v
docker system prune -a
```

## 롤백 (이전 버전으로 되돌리기)

```bash
# 새 버전 중지
docker-compose -f docker-compose.full.yml down

# 기존 Freqtrade만 재시작
docker-compose -f docker-compose.simple.yml up -d
```

## 성능 최적화

### Nginx 리버스 프록시 설정 (선택사항)

```bash
# Nginx 설치
apt update && apt install -y nginx

# 설정 파일 생성
nano /etc/nginx/sites-available/freqtrade
```

```nginx
server {
    listen 80;
    server_name 141.164.42.93;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Freqtrade UI
    location /freqtrade {
        proxy_pass http://localhost:8080;
    }
}
```

```bash
# 설정 활성화
ln -s /etc/nginx/sites-available/freqtrade /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

## 보안 강화

```bash
# 방화벽 설정
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# Docker 내부 포트만 사용 시
ufw deny 3000
ufw deny 5000
ufw deny 8080
```

## 자동 재시작 설정

```yaml
# docker-compose.full.yml에 추가
services:
  freqtrade:
    restart: always
  backend:
    restart: always
  frontend:
    restart: always
```

## 로그 관리

```bash
# 로그 크기 제한
cat > /etc/docker/daemon.json << 'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

systemctl restart docker
```

## 백업 스크립트

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/root/backups"

mkdir -p $BACKUP_DIR

# 데이터 백업
tar -czf $BACKUP_DIR/freqtrade-data-$DATE.tar.gz \
  /root/freqtrade-future/user_data

# 오래된 백업 삭제 (7일 이상)
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: freqtrade-data-$DATE.tar.gz"
```

```bash
# 매일 자동 백업 (crontab)
crontab -e
# 추가:
0 2 * * * /root/backup.sh
```

---

**배포 완료 후 확인사항:**
- [ ] Frontend 접속 확인 (http://141.164.42.93:3000)
- [ ] Backend API 응답 확인 (http://141.164.42.93:5000/api/health)
- [ ] Freqtrade UI 접속 확인 (http://141.164.42.93:8080)
- [ ] 실시간 데이터 업데이트 확인
- [ ] 로그 모니터링 설정
- [ ] 백업 스크립트 실행 확인

**다음 단계:**
1. SSL 인증서 설정 (Let's Encrypt)
2. 도메인 연결
3. 모니터링 도구 설치 (Grafana/Prometheus)
4. 알림 설정 (Telegram/Discord)