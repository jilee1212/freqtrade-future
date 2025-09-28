# 🚀 Vultr 서버 배포 가이드

## Phase 10 완성된 Freqtrade Future 시스템 배포

### 1단계: Vultr 계정 생성 및 서버 생성

#### Vultr 계정 생성
1. [Vultr.com](https://www.vultr.com/) 접속
2. 계정 생성 (GitHub/Google 연동 가능)
3. 신용카드 등록 ($10 크레딧 보너스)

#### 서버 생성
```yaml
서버 설정:
  Type: Regular Cloud Compute
  Location: Seoul, Korea (권장) 또는 Tokyo, Japan
  OS: Ubuntu 24.04 LTS x64
  Size:
    - 기본: 1 vCPU, 2GB RAM, 55GB NVMe ($12/월)
    - 절약: 1 vCPU, 1GB RAM, 25GB NVMe ($6/월)
  Additional Features:
    ✅ Auto Backups (+20% 비용, 권장)
    ✅ IPv6
```

### 2단계: 서버 초기 설정

#### SSH 접속
```bash
# 서버 생성 후 이메일로 받은 정보로 접속
ssh root@YOUR_SERVER_IP

# 비밀번호는 이메일로 전송됨
```

#### 자동 배포 스크립트 실행
```bash
# 배포 스크립트 다운로드
curl -sSL https://raw.githubusercontent.com/jilee1212/freqtrade-future/main/vultr_deploy.sh -o vultr_deploy.sh

# 실행 권한 부여
chmod +x vultr_deploy.sh

# 자동 배포 실행 (약 5-10분 소요)
./vultr_deploy.sh
```

### 3단계: 배포 확인

배포가 완료되면 다음 정보가 표시됩니다:

```
🎉 Vultr 서버 배포 완료!
==================================================
🌐 서버 정보:
   - 서버 IP: XXX.XXX.XXX.XXX
   - 운영체제: Ubuntu 24.04
   - Docker 버전: 24.x.x

🔗 접속 정보:
   - FreqUI 웹 인터페이스: http://XXX.XXX.XXX.XXX:8080
   - SSH 접속: ssh freqtrade@XXX.XXX.XXX.XXX
   - 로그인 정보:
     * Username: admin
     * Password: freqtrade2024!
```

### 4단계: 웹 인터페이스 접속

1. 웹 브라우저에서 `http://YOUR_SERVER_IP:8080` 접속
2. 로그인 정보:
   - **Username**: `admin`
   - **Password**: `freqtrade2024!`
3. Phase 10 완성된 시스템 확인:
   - ✅ 실시간 대시보드
   - ✅ AI 위험 관리 시스템
   - ✅ Ross Cameron RSI 전략
   - ✅ 모니터링 시스템
   - ✅ 백업 및 안전 시스템

### 5단계: nosignup.kr 도메인 연결

#### DNS 설정
1. 도메인 관리 패널 접속
2. A 레코드 추가:
   ```
   Type: A
   Name: @ (또는 비워둠)
   Value: YOUR_SERVER_IP
   TTL: 300 (5분)
   ```
3. CNAME 레코드 추가 (선택사항):
   ```
   Type: CNAME
   Name: www
   Value: nosignup.kr
   ```

#### SSL 인증서 설정 (Let's Encrypt)
```bash
# 서버에 SSH 접속
ssh freqtrade@YOUR_SERVER_IP

# SSL 인증서 자동 설정 스크립트 실행
sudo certbot --nginx -d nosignup.kr -d www.nosignup.kr
```

### 6단계: 실제 API 키 설정

#### 환경 변수 업데이트
```bash
# 서버에서 환경 변수 파일 편집
cd /opt/freqtrade-futures
nano .env

# 실제 Binance API 키로 교체
BINANCE_API_KEY=your_real_api_key
BINANCE_API_SECRET=your_real_api_secret

# 서비스 재시작
docker compose restart
```

### 7단계: 시스템 모니터링

#### 기본 모니터링 명령어
```bash
# 시스템 상태 확인
sudo systemctl status freqtrade-futures

# 실시간 로그 확인
cd /opt/freqtrade-futures
docker compose logs -f freqtrade

# 성능 모니터링
./production_monitor.py

# 시스템 리소스 확인
htop
```

## 배포 후 확인 사항

### ✅ 체크리스트

- [ ] **서버 접속 가능**: SSH로 freqtrade@SERVER_IP 접속
- [ ] **웹 인터페이스 동작**: http://SERVER_IP:8080 접속 가능
- [ ] **Docker 컨테이너 실행**: `docker compose ps` 모든 서비스 Up
- [ ] **API 연결 확인**: Binance API 연결 정상
- [ ] **로그 확인**: 에러 없이 정상 동작
- [ ] **도메인 연결**: nosignup.kr → SERVER_IP 연결
- [ ] **SSL 인증서**: HTTPS 접속 가능
- [ ] **모니터링 시스템**: 실시간 알림 동작
- [ ] **백업 시스템**: 자동 백업 스케줄 동작

### 🚨 트러블슈팅

#### 메모리 부족 오류
```bash
# 스왑 메모리 확인
free -h

# 스왑 추가 (필요시)
sudo fallocate -l 2G /swapfile2
sudo chmod 600 /swapfile2
sudo mkswap /swapfile2
sudo swapon /swapfile2
```

#### 서비스 재시작
```bash
# Docker 컨테이너 재시작
cd /opt/freqtrade-futures
docker compose restart

# 시스템 서비스 재시작
sudo systemctl restart freqtrade-futures
```

#### 로그 확인
```bash
# Freqtrade 로그
docker compose logs freqtrade

# 시스템 로그
sudo journalctl -u freqtrade-futures -f

# 에러 로그만 확인
docker compose logs freqtrade | grep -i error
```

## 성능 최적화

### 권장 업그레이드
- **기본 운영**: 1 vCPU, 2GB RAM ($12/월)
- **고성능 운영**: 2 vCPU, 4GB RAM ($24/월)
- **대규모 운영**: 4 vCPU, 8GB RAM ($48/월)

### 모니터링 강화
```bash
# Grafana + Prometheus 설정
cd /opt/freqtrade-futures/monitoring
docker compose -f docker-compose.monitoring.yml up -d
```

## 보안 강화

### 추가 보안 설정
```bash
# SSH 키 기반 인증만 허용
sudo nano /etc/ssh/sshd_config
# PasswordAuthentication no

# 방화벽 강화
sudo ufw delete allow 8080
sudo ufw allow from YOUR_IP to any port 8080

# 정기 보안 업데이트
sudo apt update && sudo apt upgrade -y
```

## 유지보수

### 일일 확인 사항
- 시스템 리소스 사용률
- 트레이딩 성과 및 에러 로그
- 백업 상태 확인

### 주간 유지보수
- 시스템 패키지 업데이트
- Docker 이미지 업데이트
- 로그 파일 정리

### 월간 검토
- 성능 최적화 검토
- 보안 설정 점검
- 백업 복구 테스트

---

## 🎉 축하합니다!

**Phase 10까지 완성된 Freqtrade Future 시스템이 성공적으로 배포되었습니다!**

이제 다음 URL로 접속하여 시스템을 사용할 수 있습니다:
- **임시 접속**: `http://YOUR_SERVER_IP:8080`
- **도메인 접속**: `https://nosignup.kr` (DNS 전파 후)

### 주요 기능
- ✅ **AI 위험 관리**: 동적 레버리지 및 포지션 크기 최적화
- ✅ **Ross Cameron RSI 전략**: 검증된 선물 거래 전략
- ✅ **실시간 모니터링**: 웹 대시보드 및 텔레그램 알림
- ✅ **자동 백업**: 데이터 손실 방지
- ✅ **안전 시스템**: 회로차단기 및 비상 정지
- ✅ **컴플라이언스**: 규제 준수 시스템

### 다음 단계
1. **실제 거래 시작**: 테스트넷에서 메인넷으로 전환
2. **전략 최적화**: 백테스팅 결과 기반 매개변수 조정
3. **포트폴리오 확장**: 추가 거래 쌍 및 전략 추가

**성공적인 거래를 위해 항상 리스크 관리를 우선시하세요!** 🚀