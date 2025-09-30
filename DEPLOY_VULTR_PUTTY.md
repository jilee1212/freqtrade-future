# 🚀 Vultr 서버 배포 가이드 (PuTTY 사용)

GitHub에 코드가 업로드되었으므로, PuTTY로 서버에 접속하여 배포하면 됩니다.

## ✅ GitHub 업로드 완료

**Repository:** https://github.com/jilee1212/freqtrade-future

최신 커밋:
- 🚀 Initial commit: Full stack Freqtrade Future with Next.js 14 + Flask API
- 📝 Add comprehensive README

---

## 📋 배포 단계

### 1단계: PuTTY로 서버 접속

```
Host: 141.164.42.93
Port: 22
Username: root
```

### 2단계: 기존 프로젝트 백업

```bash
# 현재 위치 확인
pwd

# 기존 프로젝트가 있다면 백업
cd /root

# Docker 컨테이너 중지
cd freqtrade-future
docker-compose down
# 또는
docker-compose -f docker-compose.simple.yml down

# 백업 생성
cd /root
mv freqtrade-future freqtrade-backup-$(date +%Y%m%d_%H%M%S)

# 백업 확인
ls -la
```

### 3단계: 새 프로젝트 Clone

```bash
# GitHub에서 Clone
cd /root
git clone https://github.com/jilee1212/freqtrade-future.git

# 프로젝트 폴더로 이동
cd freqtrade-future

# 파일 확인
ls -la
```

### 4단계: 중요 파일 복사 (선택사항)

백업에서 데이터 복사 (백업이 있다면):

```bash
# user_data 복사
cp -r ../freqtrade-backup-*/user_data/* ./user_data/

# 환경 변수 복사 (있다면)
cp ../freqtrade-backup-*/backend/.env ./backend/.env 2>/dev/null || true
```

### 5단계: 환경 변수 설정

**backend/.env 생성:**

```bash
nano backend/.env
```

다음 내용 입력:
```env
PORT=5000
FREQTRADE_URL=http://freqtrade:8080
FREQTRADE_USERNAME=freqtrade
FREQTRADE_PASSWORD=futures2024
FLASK_ENV=production
```

저장: `Ctrl+X`, `Y`, `Enter`

**frontend/.env.production 생성:**

```bash
nano frontend/.env.production
```

다음 내용 입력:
```env
NEXT_PUBLIC_API_URL=http://141.164.42.93:5000
NEXT_PUBLIC_WS_URL=ws://141.164.42.93:5000
NEXT_PUBLIC_FREQTRADE_URL=http://141.164.42.93:8080
```

저장: `Ctrl+X`, `Y`, `Enter`

### 6단계: Docker 빌드

```bash
# 프로젝트 폴더에 있는지 확인
pwd
# /root/freqtrade-future 여야 함

# Docker 이미지 빌드 (10-15분 소요)
docker-compose -f docker-compose.full.yml build

# 빌드 진행 상황 확인
# Frontend 빌드가 오래 걸릴 수 있음 (Next.js)
```

### 7단계: 컨테이너 시작

```bash
# 백그라운드로 시작
docker-compose -f docker-compose.full.yml up -d

# 상태 확인
docker-compose -f docker-compose.full.yml ps
```

예상 출력:
```
NAME                    STATUS              PORTS
freqtrade               Up 10 seconds       0.0.0.0:8080->8080/tcp
freqtrade-backend       Up 10 seconds       0.0.0.0:5000->5000/tcp
freqtrade-frontend      Up 10 seconds       0.0.0.0:3000->3000/tcp
```

### 8단계: 로그 확인

```bash
# 모든 서비스 로그
docker-compose -f docker-compose.full.yml logs -f

# 특정 서비스 로그
docker-compose logs frontend
docker-compose logs backend
docker-compose logs freqtrade

# 로그 종료: Ctrl+C
```

### 9단계: 헬스 체크

```bash
# Backend API 테스트
curl http://localhost:5000/api/health

# Freqtrade 테스트
curl http://localhost:8080/api/v1/ping

# 프로세스 확인
docker ps
```

---

## 🌐 배포 완료 후 접속

브라우저에서:
- **Frontend:** http://141.164.42.93:3000
- **Backend API:** http://141.164.42.93:5000/api/health
- **Freqtrade UI:** http://141.164.42.93:8080

---

## 🔧 문제 해결

### Frontend 빌드 실패 (메모리 부족)

```bash
# 서버 메모리 확인
free -h

# 스왑 메모리 추가
dd if=/dev/zero of=/swapfile bs=1M count=2048
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile

# 다시 빌드
docker-compose -f docker-compose.full.yml build frontend
```

### 포트 충돌

```bash
# 사용 중인 포트 확인
netstat -tulpn | grep -E ':(3000|5000|8080)'

# 기존 컨테이너 모두 제거
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)

# 다시 시작
docker-compose -f docker-compose.full.yml up -d
```

### Backend 연결 오류

```bash
# Backend 로그 확인
docker-compose logs backend

# Freqtrade 접근 테스트
docker exec -it freqtrade-backend curl http://freqtrade:8080/api/v1/status

# Backend 재시작
docker-compose restart backend
```

### Frontend 로딩 느림

```bash
# Frontend 로그 확인
docker-compose logs frontend

# 재시작
docker-compose restart frontend
```

---

## 📊 유용한 명령어

### Docker 관리

```bash
# 서비스 시작
docker-compose -f docker-compose.full.yml up -d

# 서비스 중지
docker-compose -f docker-compose.full.yml down

# 특정 서비스 재시작
docker-compose restart frontend
docker-compose restart backend
docker-compose restart freqtrade

# 모든 서비스 재시작
docker-compose restart

# 상태 확인
docker-compose ps

# 리소스 사용량
docker stats

# 로그 보기
docker-compose logs -f

# 컨테이너 쉘 접속
docker exec -it freqtrade-frontend sh
docker exec -it freqtrade-backend bash
```

### Git 업데이트

나중에 코드 업데이트 시:

```bash
cd /root/freqtrade-future

# 최신 코드 받기
git pull

# 다시 빌드 및 재시작
docker-compose -f docker-compose.full.yml up -d --build
```

### 백업 및 복원

```bash
# 데이터 백업
tar -czf backup-$(date +%Y%m%d).tar.gz user_data/

# 복원
tar -xzf backup-YYYYMMDD.tar.gz

# 백업 목록
ls -lh /root/freqtrade-backup-*
```

---

## 🛡️ 보안 설정 (배포 후)

### 1. 방화벽 설정

```bash
# UFW 설치 및 설정
apt update
apt install -y ufw

# 필요한 포트만 열기
ufw allow 22/tcp    # SSH
ufw allow 3000/tcp  # Frontend
ufw allow 5000/tcp  # Backend
ufw allow 8080/tcp  # Freqtrade

# 활성화
ufw enable

# 상태 확인
ufw status
```

### 2. Freqtrade 비밀번호 변경

```bash
# config 파일 수정
nano user_data/config_futures.json

# api_server 섹션에서 비밀번호 변경
# "password": "new_secure_password"

# 재시작
docker-compose restart freqtrade
```

### 3. SSL 인증서 (선택사항)

```bash
# Nginx 설치
apt install -y nginx certbot python3-certbot-nginx

# 도메인이 있다면
certbot --nginx -d yourdomain.com
```

---

## 📝 체크리스트

배포 후 확인사항:

- [ ] Frontend 접속 확인 (http://141.164.42.93:3000)
- [ ] Backend API 응답 확인 (http://141.164.42.93:5000/api/health)
- [ ] Freqtrade UI 접속 확인 (http://141.164.42.93:8080)
- [ ] Dashboard 차트 로딩 확인
- [ ] 실시간 데이터 업데이트 확인
- [ ] Docker 컨테이너 상태 확인 (`docker-compose ps`)
- [ ] 로그에 에러 없는지 확인 (`docker-compose logs`)
- [ ] 메모리/CPU 사용량 확인 (`docker stats`)

---

## 🎯 간단 명령어 모음

**배포 완료 후 자주 사용하는 명령어:**

```bash
# 프로젝트 폴더로 이동
cd /root/freqtrade-future

# 상태 확인
docker-compose ps

# 로그 보기
docker-compose logs -f

# 재시작
docker-compose restart

# 중지
docker-compose down

# 시작
docker-compose up -d

# 업데이트 (나중에)
git pull && docker-compose up -d --build
```

---

**배포 소요 시간:**
- Clone: 1-2분
- Docker 빌드: 10-15분
- 시작: 1-2분
- **총 소요: 약 15-20분**

**배포 완료 후:**
http://141.164.42.93:3000 접속하여 새로운 모던 UI를 확인하세요! 🎉