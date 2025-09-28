# 🚀 Vultr 단계별 배포 가이드

## 현재 상황
✅ **GitHub 레포지토리**: https://github.com/jilee1212/freqtrade-future.git (푸시 완료)
✅ **자동 배포 스크립트**: vultr_deploy.sh 준비 완료
✅ **Phase 10 시스템**: 모든 구성요소 완성

## 1단계: Vultr 서버 생성

### 1.1 Vultr 계정 생성
1. **웹사이트 접속**: https://www.vultr.com/
2. **계정 생성**: 이메일 또는 GitHub/Google 연동
3. **결제 정보 등록**: 신용카드 등록 ($10 크레딧 보너스)

### 1.2 서버 인스턴스 생성
```yaml
서버 설정:
  Choose Server: Regular Cloud Compute

  Server Location:
    Region: Asia
    Location: Seoul, Korea (권장)

  Server Image:
    Operating System: Ubuntu 24.04 LTS x64

  Server Size:
    권장: 1 vCPU, 2GB RAM, 55GB NVMe SSD ($12/월)
    절약: 1 vCPU, 1GB RAM, 25GB NVMe SSD ($6/월)

  Additional Features:
    ✅ Auto Backups (+20% 비용, 권장)
    ✅ IPv6
    ❌ Private Networking (불필요)
    ❌ Block Storage (불필요)

  SSH Keys: (선택사항 - 나중에 설정 가능)

  Server Hostname: freqtrade-futures-prod
  Server Label: Freqtrade-Future-Production
```

### 1.3 서버 생성 완료 대기
- **소요 시간**: 2-3분
- **이메일 확인**: root 계정 비밀번호 수신
- **서버 상태**: "Running" 확인

## 2단계: 서버 접속 및 자동 배포

### 2.1 SSH 접속
```bash
# 서버 IP는 Vultr 대시보드에서 확인
ssh root@YOUR_SERVER_IP

# 예시: ssh root@141.164.42.93
# 비밀번호는 이메일로 받은 정보 입력
```

### 2.2 자동 배포 스크립트 실행
```bash
# 1. 배포 스크립트 다운로드
curl -sSL https://raw.githubusercontent.com/jilee1212/freqtrade-future/master/vultr_deploy.sh -o vultr_deploy.sh

# 2. 실행 권한 부여
chmod +x vultr_deploy.sh

# 3. 자동 배포 시작 (5-10분 소요)
./vultr_deploy.sh
```

### 2.3 배포 진행 상황 확인
스크립트 실행 중 다음과 같은 진행 상황이 표시됩니다:
```
🚀 Vultr 서버 Freqtrade Future 자동 배포 시작...
[INFO] 시스템 환경 확인 중...
[SUCCESS] Ubuntu 24.04 확인됨
[INFO] 시스템 패키지 업데이트 중...
[SUCCESS] 시스템 업데이트 완료
[INFO] 필수 패키지 설치 중...
[SUCCESS] 기본 패키지 설치 완료
[INFO] Docker 설치 중...
[SUCCESS] Docker 설치 및 서비스 시작 완료
[INFO] freqtrade 사용자 생성 중...
[SUCCESS] freqtrade 사용자 생성 및 sudo NOPASSWD 설정 완료
[INFO] 방화벽 설정 중...
[SUCCESS] 방화벽 설정 완료
[INFO] GitHub에서 프로젝트 클론 중...
[SUCCESS] GitHub 프로젝트 클론 완료
[INFO] Docker Compose 서비스 시작 중...
[SUCCESS] Docker 서비스가 정상적으로 실행 중입니다
```

## 3단계: 배포 완료 확인

### 3.1 배포 성공 메시지 확인
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

📊 서비스 상태:
NAME                  IMAGE                        STATUS
freqtrade-futures     freqtradeorg/freqtrade:stable   Up X minutes
```

### 3.2 웹 인터페이스 접속 테스트
1. **브라우저에서 접속**: `http://YOUR_SERVER_IP:8080`
2. **로그인**:
   - Username: `admin`
   - Password: `freqtrade2024!`
3. **대시보드 확인**: Phase 10 시스템 정상 동작 확인

### 3.3 시스템 상태 확인
```bash
# freqtrade 사용자로 전환
su - freqtrade

# 서비스 상태 확인
cd /opt/freqtrade-futures
docker compose ps

# 로그 확인
docker compose logs -f freqtrade

# 시스템 모니터링
./production_monitor.py
```

## 4단계: nosignup.kr 도메인 연결

### 4.1 DNS 설정
도메인 관리 패널에서 A 레코드 추가:
```
Type: A
Name: @ (또는 비워둠)
Value: YOUR_SERVER_IP
TTL: 300 (5분)
```

### 4.2 CNAME 레코드 추가 (선택사항)
```
Type: CNAME
Name: www
Value: nosignup.kr
```

### 4.3 DNS 전파 확인
```bash
# 로컬에서 확인
nslookup nosignup.kr

# 또는 온라인 도구 사용
# https://www.whatsmydns.net/
```

## 5단계: SSL 인증서 설정

### 5.1 Let's Encrypt 인증서 설치
```bash
# 서버에서 실행
ssh freqtrade@YOUR_SERVER_IP

# Certbot 설치 (이미 설치되어 있음)
sudo snap install --classic certbot

# SSL 인증서 발급
sudo certbot --nginx -d nosignup.kr -d www.nosignup.kr

# 자동 갱신 설정 확인
sudo systemctl status snap.certbot.renew.timer
```

### 5.2 Nginx 설정 업데이트
인증서가 설치되면 자동으로 HTTPS 리다이렉트가 설정됩니다.

## 6단계: 최종 확인 및 테스트

### 6.1 전체 시스템 확인
```bash
# 시스템 상태
sudo systemctl status freqtrade-futures

# Docker 서비스
docker compose ps

# 네트워크 연결
curl -I https://nosignup.kr

# API 테스트
curl -s https://fapi.binance.com/fapi/v1/ping
```

### 6.2 Phase 10 기능 테스트
1. **웹 대시보드**: https://nosignup.kr
2. **실시간 모니터링**: 차트 및 데이터 업데이트 확인
3. **AI 위험 관리**: 동적 레버리지 시스템 작동 확인
4. **Ross Cameron RSI**: 전략 신호 생성 확인
5. **텔레그램 알림**: 봇 연결 및 알림 수신 확인

### 6.3 보안 및 성능 확인
```bash
# 방화벽 상태
sudo ufw status

# 메모리 사용량
free -h

# 디스크 사용량
df -h

# 네트워크 연결
ss -tulpn | grep :8080
```

## 7단계: 실제 거래 설정 (선택사항)

### 7.1 API 키 업데이트
```bash
# 환경 변수 파일 편집
cd /opt/freqtrade-futures
nano .env

# 실제 Binance API 키로 교체
BINANCE_API_KEY=your_real_api_key
BINANCE_API_SECRET=your_real_secret_key

# 서비스 재시작
docker compose restart
```

### 7.2 거래 설정 조정
```bash
# 프로덕션 설정 확인
nano user_data/config_production.json

# 주요 설정:
# - "dry_run": false (실제 거래)
# - "stake_amount": 적절한 금액 설정
# - "max_open_trades": 동시 거래 수 제한
# - 리스크 관리 파라미터 조정
```

## 배포 완료 체크리스트

- [ ] **Vultr 서버 생성**: Ubuntu 24.04, 적절한 사양 선택
- [ ] **자동 배포 실행**: vultr_deploy.sh 스크립트 성공적 실행
- [ ] **웹 인터페이스 접속**: http://SERVER_IP:8080 정상 동작
- [ ] **시스템 상태 확인**: 모든 Docker 컨테이너 Up 상태
- [ ] **도메인 연결**: nosignup.kr → SERVER_IP DNS 설정
- [ ] **SSL 인증서**: HTTPS 접속 가능
- [ ] **Phase 10 기능**: 모든 시스템 정상 동작
- [ ] **보안 설정**: 방화벽, fail2ban 활성화
- [ ] **모니터링**: 실시간 모니터링 및 알림 시스템 동작
- [ ] **백업 시스템**: 자동 백업 스케줄 설정

## 문제 해결

### 일반적인 문제
1. **메모리 부족**: 스왑 파일 증가 또는 서버 업그레이드
2. **Docker 서비스 실패**: `docker compose logs` 로 에러 확인
3. **웹 접속 불가**: 방화벽 설정 및 포트 8080 확인
4. **SSL 인증 실패**: DNS 전파 완료 후 재시도

### 지원 리소스
- **GitHub 이슈**: https://github.com/jilee1212/freqtrade-future/issues
- **Freqtrade 문서**: https://www.freqtrade.io/en/stable/
- **Vultr 지원**: https://my.vultr.com/support/

---

## 🎉 축하합니다!

**Phase 10까지 완성된 Freqtrade Future 시스템이 성공적으로 배포되었습니다!**

**접속 주소**: https://nosignup.kr (DNS 전파 후)

이제 전문가 수준의 AI 기반 선물 거래 시스템을 사용할 수 있습니다! 🚀