# 🚀 Vultr 서버 새배포 (기존 제거 후)

**중요:** 기존 프로젝트를 백업 없이 **완전히 제거**하고 새로 설치합니다.

---

## 📋 서버 정보

```
Server: 141.164.42.93 (Seoul)
Username: linuxuser
OS: Ubuntu 24.04 LTS
RAM: 1GB (메모리 최적화 필요)
CPU: 1 vCPU
Storage: 25GB NVMe SSD
```

**⚠️ 주의:** 1GB RAM이므로 Frontend 빌드 시 메모리 부족 가능 → 해결 방법 포함

---

## 🔥 1단계: 기존 프로젝트 완전 제거

### PuTTY로 서버 접속
```
Host: 141.164.42.93
Port: 22
Username: linuxuser
```

### 기존 제거 명령어

```bash
# 1. 현재 실행 중인 모든 Docker 컨테이너 중지 및 제거
docker stop $(docker ps -aq) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true

# 2. Docker 이미지 모두 제거 (선택사항 - 깨끗한 설치)
docker rmi $(docker images -q) 2>/dev/null || true

# 3. Docker 볼륨 제거 (데이터 초기화)
docker volume prune -f

# 4. Docker 네트워크 정리
docker network prune -f

# 5. 기존 프로젝트 폴더 완전 삭제
cd ~
rm -rf freqtrade-future
rm -rf freqtrade
rm -rf freqtrade-backup-*

# 6. 확인
docker ps -a    # 빈 결과여야 함
ls -la ~        # freqtrade 관련 폴더 없어야 함
```

---

## 📥 2단계: 새 프로젝트 Clone

```bash
# 홈 디렉토리로 이동
cd ~

# GitHub에서 Clone
git clone https://github.com/jilee1212/freqtrade-future.git

# 프로젝트 폴더로 이동
cd freqtrade-future

# 파일 확인
ls -la
```

---

## ⚙️ 3단계: 환경 변수 설정

### Backend 환경 변수

```bash
nano backend/.env
```

**다음 내용 입력:**
```env
PORT=5000
FREQTRADE_URL=http://freqtrade:8080
FREQTRADE_USERNAME=freqtrade
FREQTRADE_PASSWORD=futures2024
FLASK_ENV=production
```

**저장:** `Ctrl+X` → `Y` → `Enter`

### Frontend 환경 변수

```bash
nano frontend/.env.production
```

**다음 내용 입력:**
```env
NEXT_PUBLIC_API_URL=http://141.164.42.93:5000
NEXT_PUBLIC_WS_URL=ws://141.164.42.93:5000
NEXT_PUBLIC_FREQTRADE_URL=http://141.164.42.93:8080
```

**저장:** `Ctrl+X` → `Y` → `Enter`

---

## 🐳 4단계: Docker 빌드 (메모리 최적화)

### ⚠️ 중요: 1GB RAM 서버 최적화

**문제:** Frontend 빌드 시 메모리 부족으로 실패 가능
**해결:** Swap 메모리 추가

```bash
# Swap 메모리 생성 (2GB)
sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Swap 확인
free -h
# Swap: 2.0Gi 로 표시되어야 함
```

### Docker 빌드 실행

```bash
# 프로젝트 폴더에 있는지 확인
pwd
# /home/linuxuser/freqtrade-future 여야 함

# Docker Compose 빌드 (10-15분 소요)
docker-compose -f docker-compose.full.yml build

# 빌드 진행 중...
# Frontend가 가장 오래 걸림 (Next.js 빌드)
```

**빌드 중 에러 발생 시:**
```bash
# 메모리 부족 에러 시
sudo swapon -s  # swap 확인
free -h         # 메모리 확인

# Docker 캐시 정리 후 재시도
docker system prune -f
docker-compose -f docker-compose.full.yml build --no-cache
```

---

## 🚀 5단계: 컨테이너 시작

```bash
# 백그라운드로 시작
docker-compose -f docker-compose.full.yml up -d

# 시작 대기 (약 30초)
echo "Starting containers..."
sleep 30

# 상태 확인
docker-compose -f docker-compose.full.yml ps
```

**예상 결과:**
```
NAME                    STATUS              PORTS
freqtrade               Up 10 seconds       0.0.0.0:8080->8080/tcp
freqtrade-backend       Up 10 seconds       0.0.0.0:5000->5000/tcp
freqtrade-frontend      Up 10 seconds       0.0.0.0:3000->3000/tcp
```

---

## 🔍 6단계: 로그 확인

```bash
# 모든 서비스 로그 확인
docker-compose -f docker-compose.full.yml logs -f

# 로그 종료: Ctrl+C

# 특정 서비스만 확인
docker-compose logs frontend   # Frontend 로그
docker-compose logs backend    # Backend 로그
docker-compose logs freqtrade  # Freqtrade 로그
```

---

## ✅ 7단계: 배포 검증

### 서버에서 테스트

```bash
# Backend 헬스 체크
curl http://localhost:5000/api/health
# 출력: {"status":"healthy","timestamp":"..."}

# Backend 상태 확인
curl http://localhost:5000/api/status
# 출력: {"status":"success","data":{...}}

# Freqtrade 테스트
curl http://localhost:8080/api/v1/ping
# 출력: {"status":"pong"}

# 프로세스 확인
docker ps
# 3개 컨테이너 실행 중이어야 함
```

### 로컬 PC에서 테스트 (브라우저)

- **Frontend:** http://141.164.42.93:3000
- **Backend API:** http://141.164.42.93:5000/api/health
- **Freqtrade UI:** http://141.164.42.93:8080

---

## 📊 배포 완료 확인사항

- [ ] Frontend 접속 확인 (http://141.164.42.93:3000)
- [ ] Dashboard 페이지 로딩 확인
- [ ] Backend API 응답 확인 (http://141.164.42.93:5000/api/health)
- [ ] Freqtrade UI 접속 확인 (http://141.164.42.93:8080)
- [ ] Docker 컨테이너 3개 모두 실행 중
- [ ] 로그에 심각한 에러 없음

---

## 🔧 문제 해결

### 1. Frontend 빌드 실패 (메모리 부족)

**증상:**
```
FATAL ERROR: Reached heap limit Allocation failed - JavaScript heap out of memory
```

**해결:**
```bash
# Swap이 활성화되었는지 확인
free -h

# Swap 추가 (위에서 안했다면)
sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 다시 빌드
docker-compose -f docker-compose.full.yml build frontend
```

### 2. 포트 충돌

**증상:**
```
Error starting userland proxy: listen tcp4 0.0.0.0:3000: bind: address already in use
```

**해결:**
```bash
# 포트 사용 확인
sudo netstat -tulpn | grep -E ':(3000|5000|8080)'

# 해당 프로세스 종료
sudo lsof -ti:3000 | xargs kill -9
sudo lsof -ti:5000 | xargs kill -9
sudo lsof -ti:8080 | xargs kill -9

# 다시 시작
docker-compose -f docker-compose.full.yml up -d
```

### 3. Backend가 Freqtrade에 연결 안됨

**증상:**
Backend 로그에 `Error fetching from Freqtrade: Connection refused`

**해결:**
```bash
# Freqtrade 컨테이너 상태 확인
docker logs freqtrade

# Freqtrade 재시작
docker-compose restart freqtrade

# Backend에서 Freqtrade 접근 테스트
docker exec -it freqtrade-backend curl http://freqtrade:8080/api/v1/status

# Backend 재시작
docker-compose restart backend
```

### 4. Frontend 로딩 느림 또는 안됨

**해결:**
```bash
# Frontend 로그 확인
docker logs freqtrade-frontend

# Frontend 재시작
docker-compose restart frontend

# 브라우저 캐시 삭제 후 재접속
# Ctrl+F5 (하드 리프레시)
```

---

## 🛠️ 유용한 명령어

### Docker 관리

```bash
# 프로젝트 폴더로 이동
cd ~/freqtrade-future

# 모든 서비스 시작
docker-compose -f docker-compose.full.yml up -d

# 모든 서비스 중지
docker-compose -f docker-compose.full.yml down

# 특정 서비스 재시작
docker-compose restart frontend
docker-compose restart backend
docker-compose restart freqtrade

# 상태 확인
docker-compose ps

# 리소스 사용량 (메모리/CPU)
docker stats

# 로그 보기
docker-compose logs -f

# 컨테이너 내부 접속
docker exec -it freqtrade-frontend sh
docker exec -it freqtrade-backend bash
docker exec -it freqtrade bash
```

### 시스템 모니터링

```bash
# 메모리 사용량
free -h

# 디스크 사용량
df -h

# CPU/메모리 실시간
htop

# Docker 이미지 크기
docker images

# Docker 디스크 사용량
docker system df
```

### 코드 업데이트 (나중에)

```bash
cd ~/freqtrade-future
git pull
docker-compose -f docker-compose.full.yml up -d --build
```

---

## 🛡️ 보안 설정 (배포 후)

### 방화벽 설정

```bash
# UFW 설치 및 설정
sudo apt update
sudo apt install -y ufw

# SSH 포트만 일단 허용
sudo ufw allow 22/tcp

# 서비스 포트 허용
sudo ufw allow 3000/tcp   # Frontend
sudo ufw allow 5000/tcp   # Backend
sudo ufw allow 8080/tcp   # Freqtrade

# 활성화
sudo ufw enable

# 상태 확인
sudo ufw status
```

### Freqtrade 비밀번호 변경

```bash
# 설정 파일 수정
nano ~/freqtrade-future/user_data/config_futures.json

# api_server 섹션에서 비밀번호 변경
# "password": "new_secure_password_here"

# 저장 후 재시작
cd ~/freqtrade-future
docker-compose restart freqtrade
```

---

## 📈 성능 최적화 (1GB RAM)

### Swap 영구 설정

```bash
# /etc/fstab에 추가하여 재부팅 후에도 유지
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 확인
cat /etc/fstab
```

### Docker 로그 크기 제한

```bash
# /etc/docker/daemon.json 생성
sudo nano /etc/docker/daemon.json
```

**내용:**
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

```bash
# Docker 재시작
sudo systemctl restart docker

# 컨테이너 재시작
cd ~/freqtrade-future
docker-compose -f docker-compose.full.yml up -d
```

---

## 🎯 전체 명령어 요약 (복사용)

```bash
# ========================================
# 1. 기존 완전 제거
# ========================================
docker stop $(docker ps -aq) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true
docker volume prune -f
cd ~
rm -rf freqtrade-future freqtrade freqtrade-backup-*

# ========================================
# 2. Swap 메모리 추가 (1GB RAM 서버 필수)
# ========================================
sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
free -h

# ========================================
# 3. 새 프로젝트 Clone
# ========================================
cd ~
git clone https://github.com/jilee1212/freqtrade-future.git
cd freqtrade-future

# ========================================
# 4. 환경 변수 설정
# ========================================
cat > backend/.env << 'EOF'
PORT=5000
FREQTRADE_URL=http://freqtrade:8080
FREQTRADE_USERNAME=freqtrade
FREQTRADE_PASSWORD=futures2024
FLASK_ENV=production
EOF

cat > frontend/.env.production << 'EOF'
NEXT_PUBLIC_API_URL=http://141.164.42.93:5000
NEXT_PUBLIC_WS_URL=ws://141.164.42.93:5000
NEXT_PUBLIC_FREQTRADE_URL=http://141.164.42.93:8080
EOF

# ========================================
# 5. Docker 빌드 및 시작
# ========================================
docker-compose -f docker-compose.full.yml build
docker-compose -f docker-compose.full.yml up -d

# ========================================
# 6. 확인
# ========================================
sleep 30
docker-compose ps
docker-compose logs -f
```

---

## 🌐 배포 완료!

### 접속 URL
- **모던 Frontend:** http://141.164.42.93:3000
- **Backend API:** http://141.164.42.93:5000/api/health
- **Freqtrade UI:** http://141.164.42.93:8080

### 배포 소요 시간
- 기존 제거: 2-3분
- Clone: 1분
- Swap 설정: 1분
- Docker 빌드: 10-15분
- **총 소요: 약 15-20분**

---

**Version:** 1.0.0
**Server:** linuxuser@141.164.42.93
**RAM:** 1GB (Swap 2GB 추가)
**Status:** 🟢 Ready for Clean Deployment