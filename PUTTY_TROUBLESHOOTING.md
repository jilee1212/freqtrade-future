# 🔧 PuTTY 창이 꺼질 때 해결 방법

## 🔍 원인 분석

PuTTY 창이 갑자기 꺼지는 주요 원인:

1. **서버 연결 끊김** - 네트워크 문제
2. **명령어 오류** - 잘못된 명령어 실행
3. **권한 문제** - sudo 비밀번호 오류
4. **세션 타임아웃** - 오랜 시간 미사용

---

## ✅ 즉시 해결 방법

### 1단계: 다시 접속

**PuTTY 재실행:**
```
Host: 141.164.42.93
Port: 22
Username: linuxuser
Password: (입력)
```

### 2단계: 현재 상태 확인

```bash
# 현재 위치 확인
pwd

# 파일 확인
ls -la

# Docker 상태 확인
docker ps -a

# 실행 중인 프로세스 확인
docker-compose ps 2>/dev/null || echo "docker-compose 없음"
```

---

## 🎯 단계별 안전한 배포 방법

PuTTY가 꺼지는 것을 방지하기 위해 **단계별로 나눠서** 실행하세요.

### ✅ Step 1: 기존 제거 및 확인

```bash
# 1-1. 현재 Docker 컨테이너 확인
docker ps -a

# 1-2. 컨테이너 중지
docker stop $(docker ps -aq) 2>/dev/null || echo "중지할 컨테이너 없음"

# 1-3. 컨테이너 제거
docker rm $(docker ps -aq) 2>/dev/null || echo "제거할 컨테이너 없음"

# 1-4. 볼륨 정리
docker volume prune -f

# 1-5. 기존 폴더 제거
cd ~
rm -rf freqtrade-future freqtrade freqtrade-backup-*

# 1-6. 확인
ls -la | grep freq
```

**예상 결과:** freqtrade 관련 폴더가 없어야 함

---

### ✅ Step 2: Swap 메모리 추가

```bash
# 2-1. 현재 메모리 확인
free -h

# 2-2. Swap 파일 생성 (비밀번호 입력 필요)
sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
```

**비밀번호 입력:** `[sudo] password for linuxuser:` → 비밀번호 입력

```bash
# 2-3. Swap 설정
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 2-4. 확인
free -h
```

**예상 결과:** Swap: 2.0Gi 표시되어야 함

---

### ✅ Step 3: Git Clone

```bash
# 3-1. 홈 디렉토리로 이동
cd ~
pwd

# 3-2. GitHub에서 Clone
git clone https://github.com/jilee1212/freqtrade-future.git

# 3-3. 확인
ls -la freqtrade-future

# 3-4. 프로젝트 폴더로 이동
cd freqtrade-future
pwd
```

**예상 결과:** `/home/linuxuser/freqtrade-future`

---

### ✅ Step 4: 환경 변수 설정

```bash
# 4-1. Backend 환경 변수
cat > backend/.env << 'EOF'
PORT=5000
FREQTRADE_URL=http://freqtrade:8080
FREQTRADE_USERNAME=freqtrade
FREQTRADE_PASSWORD=futures2024
FLASK_ENV=production
EOF

# 4-2. 확인
cat backend/.env

# 4-3. Frontend 환경 변수
cat > frontend/.env.production << 'EOF'
NEXT_PUBLIC_API_URL=http://141.164.42.93:5000
NEXT_PUBLIC_WS_URL=ws://141.164.42.93:5000
NEXT_PUBLIC_FREQTRADE_URL=http://141.164.42.93:8080
EOF

# 4-4. 확인
cat frontend/.env.production
```

**예상 결과:** 환경 변수 내용이 표시됨

---

### ✅ Step 5: Docker 빌드 (가장 오래 걸림)

**⚠️ 중요:** 이 단계에서 PuTTY가 꺼질 수 있으므로 `screen` 사용 추천!

#### 방법 A: screen 사용 (추천)

```bash
# screen 설치 (없다면)
sudo apt install -y screen

# screen 세션 시작
screen -S deploy

# Docker 빌드 실행
docker-compose -f docker-compose.full.yml build
```

**PuTTY가 꺼져도 괜찮습니다!**

다시 접속 후:
```bash
# 세션 재접속
screen -r deploy
```

#### 방법 B: 일반 실행

```bash
# 프로젝트 폴더에 있는지 확인
pwd
# /home/linuxuser/freqtrade-future 여야 함

# Docker 빌드 (10-15분 소요)
docker-compose -f docker-compose.full.yml build
```

**빌드 진행 상황:**
- Backend: 2-3분
- Frontend: 10-12분 (Next.js 빌드)
- Freqtrade: 이미지 다운로드

---

### ✅ Step 6: 컨테이너 시작

```bash
# 6-1. 시작
docker-compose -f docker-compose.full.yml up -d

# 6-2. 대기
sleep 30

# 6-3. 상태 확인
docker-compose ps
```

**예상 결과:**
```
NAME                    STATUS
freqtrade               Up 30 seconds
freqtrade-backend       Up 30 seconds
freqtrade-frontend      Up 30 seconds
```

---

### ✅ Step 7: 검증

```bash
# 7-1. Backend 테스트
curl http://localhost:5000/api/health

# 7-2. Freqtrade 테스트
curl http://localhost:8080/api/v1/ping

# 7-3. 로그 확인
docker-compose logs --tail=50
```

---

## 🔥 PuTTY가 꺼졌을 때 복구 방법

### 케이스 1: 빌드 중 꺼진 경우

```bash
# 1. 다시 접속
# Host: 141.164.42.93, Username: linuxuser

# 2. 프로젝트 폴더로 이동
cd ~/freqtrade-future

# 3. 빌드 상태 확인
docker images | grep freqtrade

# 4-a. 이미지가 있으면 (빌드 완료됨)
docker-compose -f docker-compose.full.yml up -d

# 4-b. 이미지가 없으면 (빌드 실패)
docker-compose -f docker-compose.full.yml build
```

### 케이스 2: Clone 중 꺼진 경우

```bash
# 1. 다시 접속

# 2. 확인
cd ~
ls -la | grep freq

# 3-a. freqtrade-future 폴더가 있으면
cd freqtrade-future
ls -la

# 3-b. freqtrade-future 폴더가 없으면
git clone https://github.com/jilee1212/freqtrade-future.git
cd freqtrade-future
```

### 케이스 3: 시작 중 꺼진 경우

```bash
# 1. 다시 접속

# 2. 프로젝트 폴더로 이동
cd ~/freqtrade-future

# 3. 컨테이너 상태 확인
docker-compose ps

# 4. 시작
docker-compose -f docker-compose.full.yml up -d
```

---

## 🛡️ PuTTY 끊김 방지 방법

### 방법 1: screen 사용 (가장 안전)

```bash
# screen 설치
sudo apt install -y screen

# screen 세션 시작
screen -S deploy

# 배포 작업 수행
# (이제 PuTTY가 꺼져도 작업이 계속됨)

# 세션 나가기 (작업은 계속 실행)
Ctrl+A, D

# 다시 접속 후 세션 복구
screen -r deploy
```

### 방법 2: nohup 사용

```bash
# 백그라운드로 빌드 실행
nohup docker-compose -f docker-compose.full.yml build > build.log 2>&1 &

# 진행 상황 확인
tail -f build.log
```

### 방법 3: PuTTY 설정 변경

PuTTY 설정 창에서:
```
Connection → Seconds between keepalives: 30 입력
Connection → Enable TCP keepalives 체크
```

---

## 📱 대체 방법: Windows Terminal 사용

### Windows Terminal (더 안정적)

```powershell
# Windows Terminal 또는 PowerShell에서
ssh linuxuser@141.164.42.93
```

**장점:**
- 연결이 더 안정적
- 복사/붙여넣기 편리
- 창이 잘 안 꺼짐

---

## 🎯 현재 상태 확인 및 계속 진행

### 1. 다시 접속

```bash
# PuTTY 재실행
Host: 141.164.42.93
Username: linuxuser
```

### 2. 어디까지 완료되었는지 확인

```bash
# 홈 디렉토리 확인
cd ~
ls -la

# freqtrade-future 폴더 확인
ls -la freqtrade-future 2>/dev/null && echo "✅ Clone 완료" || echo "❌ Clone 필요"

# Docker 이미지 확인
docker images | grep freqtrade && echo "✅ 빌드 완료" || echo "❌ 빌드 필요"

# 컨테이너 확인
docker ps && echo "✅ 실행 중" || echo "❌ 시작 필요"
```

### 3. 필요한 단계부터 계속 진행

위 **단계별 안전한 배포 방법**에서 필요한 단계부터 실행하세요.

---

## 🆘 긴급 연락처

### 문제가 계속되면

1. **서버 재부팅**
   - Vultr 웹사이트에서 Restart

2. **screen으로 재시도**
   ```bash
   screen -S deploy
   # 배포 명령어 실행
   ```

3. **단계별로 천천히 실행**
   - 위의 Step 1-7 순서대로

---

## 📋 빠른 체크리스트

현재 상황 파악:

- [ ] PuTTY 재접속 완료
- [ ] `cd ~/freqtrade-future` 실행
- [ ] `ls -la` 로 파일 확인
- [ ] `docker ps` 로 컨테이너 확인
- [ ] 어느 단계에서 끊겼는지 확인
- [ ] 해당 단계부터 재실행

---

**즉시 해야 할 것:**

1. **PuTTY 다시 실행** → 141.164.42.93 접속
2. **현재 상태 확인:** `cd ~ && ls -la && docker ps -a`
3. **결과 알려주세요** - 어디까지 완료되었는지 확인 가능합니다!

---

**더 안정적인 방법:**
```bash
# screen 사용 (PuTTY 꺼져도 작업 계속됨)
sudo apt install -y screen
screen -S deploy
# 이제 배포 명령어 실행
```