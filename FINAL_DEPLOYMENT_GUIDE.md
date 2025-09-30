# 🎯 최종 배포 가이드 (기존 제거 → 새 설치)

## ✅ GitHub 업로드 완료

**Repository:** https://github.com/jilee1212/freqtrade-future

---

## 📋 서버 정보

```
IP: 141.164.42.93
Username: linuxuser
Password: (귀하의 비밀번호)
OS: Ubuntu 24.04 LTS
RAM: 1GB ⚠️ (Swap 메모리 추가 필요)
```

---

## 🚀 PuTTY로 배포 (복사해서 실행)

### 1️⃣ PuTTY 접속

```
Host: 141.164.42.93
Port: 22
Username: linuxuser
```

### 2️⃣ 전체 명령어 실행 (한번에 복사)

PuTTY 창에 다음 명령어를 **전체 복사 붙여넣기** 하세요:

```bash
# ========================================
# 기존 프로젝트 완전 제거
# ========================================
echo "🔥 Step 1: 기존 프로젝트 제거 중..."
docker stop $(docker ps -aq) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true
docker volume prune -f
cd ~
rm -rf freqtrade-future freqtrade freqtrade-backup-*
echo "✅ 기존 프로젝트 제거 완료"
echo ""

# ========================================
# Swap 메모리 추가 (1GB RAM 서버 필수)
# ========================================
echo "💾 Step 2: Swap 메모리 추가 중..."
sudo dd if=/dev/zero of=/swapfile bs=1M count=2048 2>/dev/null
sudo chmod 600 /swapfile
sudo mkswap /swapfile 2>/dev/null
sudo swapon /swapfile
echo "✅ Swap 메모리 추가 완료"
free -h
echo ""

# ========================================
# 새 프로젝트 Clone
# ========================================
echo "📥 Step 3: GitHub에서 프로젝트 다운로드 중..."
cd ~
git clone https://github.com/jilee1212/freqtrade-future.git
cd freqtrade-future
echo "✅ 프로젝트 다운로드 완료"
echo ""

# ========================================
# 환경 변수 설정
# ========================================
echo "⚙️  Step 4: 환경 변수 설정 중..."
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
echo "✅ 환경 변수 설정 완료"
echo ""

# ========================================
# Docker 빌드
# ========================================
echo "🐳 Step 5: Docker 이미지 빌드 중... (10-15분 소요)"
echo "⏳ 잠시 기다려주세요..."
docker-compose -f docker-compose.full.yml build

if [ $? -eq 0 ]; then
    echo "✅ Docker 빌드 완료"
else
    echo "❌ Docker 빌드 실패"
    exit 1
fi
echo ""

# ========================================
# 컨테이너 시작
# ========================================
echo "🚀 Step 6: 서비스 시작 중..."
docker-compose -f docker-compose.full.yml up -d
sleep 30
echo "✅ 서비스 시작 완료"
echo ""

# ========================================
# 상태 확인
# ========================================
echo "📊 Step 7: 서비스 상태 확인"
docker-compose -f docker-compose.full.yml ps
echo ""

# ========================================
# 헬스 체크
# ========================================
echo "🏥 Step 8: 헬스 체크"
echo ""
echo "Backend API:"
curl -s http://localhost:5000/api/health || echo "❌ Backend 응답 없음"
echo ""
echo ""
echo "Freqtrade:"
curl -s http://localhost:8080/api/v1/ping || echo "❌ Freqtrade 응답 없음"
echo ""
echo ""

# ========================================
# 완료
# ========================================
echo "=========================================="
echo "✅ 배포 완료!"
echo "=========================================="
echo ""
echo "🌐 서비스 접속:"
echo "  Frontend:  http://141.164.42.93:3000"
echo "  Backend:   http://141.164.42.93:5000"
echo "  Freqtrade: http://141.164.42.93:8080"
echo ""
echo "📝 로그 확인:"
echo "  docker-compose -f docker-compose.full.yml logs -f"
echo ""
```

---

## ✅ 배포 후 확인

### 브라우저에서 접속 테스트

1. **Frontend:** http://141.164.42.93:3000
   - 모던 Next.js UI가 보여야 함

2. **Backend API:** http://141.164.42.93:5000/api/health
   - `{"status":"healthy","timestamp":"..."}` 응답

3. **Freqtrade UI:** http://141.164.42.93:8080
   - 기존 Freqtrade UI

### 서버에서 로그 확인

```bash
cd ~/freqtrade-future
docker-compose -f docker-compose.full.yml logs -f

# 종료: Ctrl+C
```

---

## 🔧 문제 해결

### Frontend 빌드 실패 (메모리 부족)

```bash
# Swap 확인
free -h

# Swap이 없다면 추가
sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 다시 빌드
cd ~/freqtrade-future
docker-compose -f docker-compose.full.yml build frontend
docker-compose -f docker-compose.full.yml up -d
```

### 컨테이너가 시작 안됨

```bash
# 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs

# 재시작
docker-compose -f docker-compose.full.yml restart

# 완전 재시작
docker-compose down
docker-compose -f docker-compose.full.yml up -d
```

### 포트 충돌

```bash
# 포트 확인
sudo netstat -tulpn | grep -E ':(3000|5000|8080)'

# 모든 Docker 컨테이너 중지
docker stop $(docker ps -aq)

# 다시 시작
cd ~/freqtrade-future
docker-compose -f docker-compose.full.yml up -d
```

---

## 📊 유용한 명령어

```bash
# 프로젝트 폴더로 이동
cd ~/freqtrade-future

# 서비스 시작
docker-compose -f docker-compose.full.yml up -d

# 서비스 중지
docker-compose -f docker-compose.full.yml down

# 상태 확인
docker-compose ps

# 로그 보기
docker-compose logs -f

# 특정 서비스 재시작
docker-compose restart frontend
docker-compose restart backend

# 메모리 사용량
free -h
docker stats

# 디스크 사용량
df -h
```

---

## 🎯 배포 체크리스트

- [ ] PuTTY로 linuxuser@141.164.42.93 접속
- [ ] 위 전체 명령어 복사 붙여넣기 실행
- [ ] 빌드 완료까지 대기 (10-15분)
- [ ] `docker-compose ps`로 3개 컨테이너 실행 확인
- [ ] http://141.164.42.93:3000 접속 확인
- [ ] http://141.164.42.93:5000/api/health 응답 확인
- [ ] http://141.164.42.93:8080 접속 확인

---

## 🔥 빠른 재배포 (나중에)

코드 업데이트 시:

```bash
cd ~/freqtrade-future
git pull
docker-compose -f docker-compose.full.yml up -d --build
```

---

## 📞 지원

- **상세 가이드:** [DEPLOY_CLEAN_INSTALL.md](DEPLOY_CLEAN_INSTALL.md)
- **GitHub:** https://github.com/jilee1212/freqtrade-future
- **로그:** `docker-compose logs -f`

---

**배포 소요 시간:** 15-20분
**난이도:** ⭐⭐☆☆☆ (중급)
**Status:** 🟢 Ready to Deploy