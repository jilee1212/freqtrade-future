# 🚨 Freqtrade Future 배포 문제 빠른 해결 가이드

## 📋 현재 상황
- ❌ 로컬 환경: Docker 미설치, 서비스 미실행
- ❌ Vultr 서버: 웹사이트 접속 불가
- 🎯 목표: Vultr 서버에서 FreqUI 정상 작동

---

## 🔧 3단계 빠른 해결 방법

### ✅ 1단계: Vultr 서버 접속

```bash
# SSH로 Vultr 서버 접속
ssh linuxuser@141.164.42.93

# 또는 root로 접속 (권한 있는 경우)
ssh root@141.164.42.93
```

---

### ✅ 2단계: 진단 스크립트 실행

```bash
# 진단 스크립트 다운로드 및 실행
curl -o diagnose_server.sh https://raw.githubusercontent.com/jilee1212/freqtrade-future/master/diagnose_server.sh
bash diagnose_server.sh
```

**진단 결과 확인:**
- ✅ Docker 설치 여부
- ✅ 컨테이너 실행 상태
- ✅ 포트 8080 리스닝 여부
- ✅ 프로젝트 디렉토리 존재
- ✅ 로그 파일 확인

---

### ✅ 3단계: 자동 수정 실행

진단에서 문제가 발견되면 자동 수정 스크립트 실행:

```bash
# 수정 스크립트 다운로드 및 실행
curl -o fix_deployment.sh https://raw.githubusercontent.com/jilee1212/freqtrade-future/master/fix_deployment.sh
sudo bash fix_deployment.sh
```

**자동 수정 내용:**
1. ✅ Docker 설치 및 설정
2. ✅ 기존 컨테이너 정리
3. ✅ 프로젝트 다운로드/업데이트
4. ✅ 환경 변수 설정
5. ✅ 스왑 메모리 추가 (1GB RAM 대응)
6. ✅ 방화벽 포트 개방
7. ✅ Docker Compose 시작
8. ✅ systemd 서비스 등록
9. ✅ 서비스 연결 테스트

---

## 🌐 접속 확인

수정 완료 후 다음 주소로 접속:

```
http://141.164.42.93:8080
```

**로그인 정보:**
- Username: `admin`
- Password: `freqtrade2024!`

---

## 🐛 수동 문제 해결

### 문제 1: Docker 서비스가 실행되지 않음

```bash
# Docker 서비스 시작
sudo systemctl start docker
sudo systemctl enable docker
sudo systemctl status docker
```

### 문제 2: 컨테이너가 실행되지 않음

```bash
# 프로젝트 디렉토리로 이동
cd /opt/freqtrade-futures
# 또는
cd ~/freqtrade-future

# Docker Compose 재시작
docker compose down
docker compose pull
docker compose up -d

# 상태 확인
docker compose ps
docker compose logs -f
```

### 문제 3: 포트 8080이 열려있지 않음

```bash
# 포트 확인
sudo netstat -tuln | grep 8080

# 방화벽 확인 및 설정
sudo ufw status
sudo ufw allow 8080/tcp
sudo ufw reload
```

### 문제 4: 메모리 부족

```bash
# 메모리 확인
free -h

# 스왑 추가 (2GB)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 문제 5: 로그 확인

```bash
# Docker Compose 로그
cd /opt/freqtrade-futures
docker compose logs -f freqtrade-bot

# 시스템 로그
sudo journalctl -u freqtrade-futures -f

# 개별 컨테이너 로그
docker logs freqtrade-futures-bot
```

---

## 📊 서비스 상태 확인 명령어

```bash
# 전체 시스템 상태
sudo systemctl status freqtrade-futures

# Docker 컨테이너 상태
docker ps -a

# Docker Compose 상태
cd /opt/freqtrade-futures && docker compose ps

# 포트 리스닝 상태
sudo netstat -tuln | grep -E "8080|5000|80|443"

# 메모리 사용량
free -h
docker stats

# 디스크 사용량
df -h
```

---

## 🔄 완전 재설치 (최후의 수단)

모든 방법이 실패한 경우:

```bash
# 1. 모든 컨테이너 및 이미지 삭제
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)
docker rmi $(docker images -q)

# 2. 프로젝트 디렉토리 삭제
sudo rm -rf /opt/freqtrade-futures
sudo rm -rf ~/freqtrade-future*

# 3. 자동 수정 스크립트 재실행
curl -o fix_deployment.sh https://raw.githubusercontent.com/jilee1212/freqtrade-future/master/fix_deployment.sh
sudo bash fix_deployment.sh
```

---

## 📞 추가 지원

### GitHub 저장소
- https://github.com/jilee1212/freqtrade-future

### 로그 수집 (문제 보고 시)

```bash
# 진단 정보 수집
{
    echo "=== 시스템 정보 ==="
    uname -a
    free -h
    df -h

    echo "=== Docker 정보 ==="
    docker --version
    docker ps -a
    docker compose ps

    echo "=== 포트 상태 ==="
    sudo netstat -tuln | grep -E "8080|5000"

    echo "=== 로그 ==="
    docker compose logs --tail=50
} > diagnostic_report.txt

# 파일 확인
cat diagnostic_report.txt
```

---

## ✅ 성공 확인 체크리스트

- [ ] SSH로 Vultr 서버 접속 성공
- [ ] `diagnose_server.sh` 실행 완료
- [ ] `fix_deployment.sh` 실행 완료
- [ ] Docker 서비스 실행 중
- [ ] 컨테이너 Up 상태 확인
- [ ] 포트 8080 리스닝 중
- [ ] 웹 브라우저에서 http://141.164.42.93:8080 접속 성공
- [ ] admin/freqtrade2024! 로그인 성공
- [ ] FreqUI 대시보드 표시됨

---

## 🎉 예상 결과

성공 시 다음과 같이 표시됩니다:

```
🎉 배포 수정 완료!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌐 서버 정보:
   - 서버 IP: 141.164.42.93
   - 프로젝트: /opt/freqtrade-futures
   - 운영체제: Ubuntu 24.04 LTS

🔗 접속 정보:
   - FreqUI: http://141.164.42.93:8080
   - 웹 대시보드: http://141.164.42.93:5000
   - 로그인:
     * Username: admin
     * Password: freqtrade2024!

📊 실행 중인 서비스:
NAME                        STATUS              PORTS
freqtrade-futures-bot       Up 2 minutes        0.0.0.0:8080->8080/tcp
futures-web-dashboard       Up 2 minutes        0.0.0.0:5000->5000/tcp
```

---

## 🚀 다음 단계

1. **도메인 연결** (선택사항)
   - nosignup.kr DNS A 레코드: 141.164.42.93

2. **실제 API 키 설정**
   ```bash
   cd /opt/freqtrade-futures
   nano .env
   # BINANCE_API_KEY와 BINANCE_API_SECRET 수정
   docker compose restart
   ```

3. **SSL 인증서 설정** (도메인 연결 후)
   ```bash
   sudo certbot --nginx -d nosignup.kr
   ```

4. **모니터링 설정**
   - Grafana: http://141.164.42.93:3000
   - Prometheus: http://141.164.42.93:9090

---

**💡 Tip:** 스크립트 실행 중 오류가 발생하면 `sudo bash -x fix_deployment.sh`로 디버그 모드로 실행하여 어느 단계에서 문제가 발생하는지 확인할 수 있습니다.