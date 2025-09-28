# 🚀 원클릭 Phase 10 배포 가이드

## 📋 서버 정보
- **IP**: 141.164.42.93 (Seoul, Korea)
- **사양**: 1 vCPU, 1GB RAM, 25GB NVMe SSD
- **사용자**: linuxuser
- **목표**: nosignup.kr 도메인 연결

## ⚡ 원클릭 배포 명령어

서버에 SSH 접속 후 다음 **한 줄 명령어**만 실행하면 모든 배포가 완료됩니다:

```bash
curl -sSL https://raw.githubusercontent.com/jilee1212/freqtrade-future/master/remote_deploy.sh | bash
```

## 🔄 배포 과정 (자동 진행)

### 1단계: 시스템 준비 (2-3분)
- 기존 Freqtrade 프로세스 정리
- 기존 프로젝트 안전 백업
- 시스템 패키지 업데이트
- Docker 설치 및 설정

### 2단계: 프로젝트 설정 (2-3분)
- GitHub에서 Phase 10 코드 다운로드
- 환경 변수 및 설정 파일 생성
- 디렉토리 구조 생성
- 방화벽 설정

### 3단계: 서비스 시작 (3-5분)
- Freqtrade Docker 컨테이너 실행
- 포트 8080 노출
- 웹 서비스 상태 확인
- 자동 시작 서비스 등록

### 4단계: 배포 완료 확인 (1분)
- 서비스 상태 검증
- 웹 인터페이스 응답 테스트
- 최종 배포 결과 출력

## 📊 배포 완료 후 화면

배포가 성공적으로 완료되면 다음과 같은 메시지가 표시됩니다:

```
🎉🎉🎉 Phase 10 Freqtrade Future 배포 완료! 🎉🎉🎉
============================================================

🌐 서버 정보:
   - 서버 IP: 141.164.42.93
   - 위치: Seoul, Korea
   - 프로젝트 경로: /home/linuxuser/freqtrade-future-phase10

🔗 접속 정보:
   - 웹 인터페이스: http://141.164.42.93:8080
   - 로그인 정보:
     ✅ Username: admin
     ✅ Password: freqtrade2024!

📊 현재 서비스 상태:
freqtrade-phase10   freqtradeorg/freqtrade:stable   Up X minutes   0.0.0.0:8080->8080/tcp

📋 Phase 10 주요 기능:
   ✅ AI 위험 관리 시스템
   ✅ Ross Cameron RSI 전략
   ✅ 실시간 웹 대시보드
   ✅ 프로덕션 모니터링
   ✅ 안전 및 컴플라이언스
   ✅ 자동 백업 시스템
```

## 🌐 웹 인터페이스 접속

### 1. 브라우저에서 접속
```
http://141.164.42.93:8080
```

### 2. 로그인
- **Username**: `admin`
- **Password**: `freqtrade2024!`

### 3. Phase 10 기능 확인
- ✅ **실시간 대시보드**: 차트 및 데이터 업데이트
- ✅ **AI 위험 관리**: 동적 레버리지 시스템
- ✅ **Ross Cameron RSI**: 전략 신호 생성
- ✅ **모니터링 시스템**: 성능 지표 및 알림

## 🔗 nosignup.kr 도메인 연결

### DNS 설정
도메인 관리 패널에서 다음 설정을 추가하세요:

```
Type: A
Name: @ (또는 비워둠)
Value: 141.164.42.93
TTL: 300 (5분)

Type: CNAME (선택사항)
Name: www
Value: nosignup.kr
```

### DNS 전파 확인
```bash
# 로컬에서 확인
nslookup nosignup.kr

# 온라인 도구
# https://www.whatsmydns.net/
```

### SSL 인증서 설정 (선택사항)
DNS 전파 완료 후 서버에서 실행:
```bash
sudo apt install snapd
sudo snap install --classic certbot
sudo certbot --nginx -d nosignup.kr -d www.nosignup.kr
```

## 🛠️ 유용한 관리 명령어

### 서비스 관리
```bash
# 컨테이너 상태 확인
sudo docker ps

# 로그 실시간 확인
sudo docker logs freqtrade-phase10 -f

# 컨테이너 재시작
sudo docker restart freqtrade-phase10

# 서비스 중지
sudo docker stop freqtrade-phase10

# 서비스 시작
sudo docker start freqtrade-phase10
```

### 시스템 모니터링
```bash
# 시스템 리소스 확인
htop

# 메모리 사용량
free -h

# 디스크 사용량
df -h

# 네트워크 포트 확인
sudo ss -tulpn | grep :8080

# 웹 서비스 테스트
curl -I http://141.164.42.93:8080
```

### 프로젝트 관리
```bash
# 프로젝트 폴더로 이동
cd /home/linuxuser/freqtrade-future-phase10

# 환경 변수 확인
cat .env

# 설정 파일 확인
cat user_data/config_production.json

# 로그 파일 확인
tail -f logs/freqtrade.log
```

## 🚨 문제 해결

### 일반적인 문제

#### 1. 웹 인터페이스 접속 불가
```bash
# 컨테이너 상태 확인
sudo docker ps | grep freqtrade

# 포트 확인
sudo ss -tulpn | grep :8080

# 방화벽 확인
sudo ufw status

# 컨테이너 로그 확인
sudo docker logs freqtrade-phase10
```

#### 2. 메모리 부족 오류
```bash
# 메모리 사용량 확인
free -h

# 스왑 파일 생성 (1GB RAM 환경)
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

#### 3. Docker 컨테이너 실행 실패
```bash
# Docker 서비스 상태
sudo systemctl status docker

# Docker 서비스 재시작
sudo systemctl restart docker

# 컨테이너 강제 재생성
sudo docker stop freqtrade-phase10
sudo docker rm freqtrade-phase10
# 원클릭 배포 스크립트 재실행
```

### 완전 재배포
문제가 지속되는 경우 원클릭 스크립트를 다시 실행하면 됩니다:
```bash
curl -sSL https://raw.githubusercontent.com/jilee1212/freqtrade-future/master/remote_deploy.sh | bash
```

## ✅ 배포 성공 체크리스트

- [ ] **원클릭 스크립트 실행**: 에러 없이 완료
- [ ] **Docker 컨테이너 실행**: `sudo docker ps`에서 freqtrade-phase10 Up 상태
- [ ] **포트 8080 열림**: `sudo ss -tulpn | grep :8080` 확인
- [ ] **웹 인터페이스 접속**: http://141.164.42.93:8080 정상 응답
- [ ] **로그인 성공**: admin/freqtrade2024! 로그인 가능
- [ ] **Phase 10 기능 동작**: 대시보드, 차트, 데이터 표시
- [ ] **도메인 연결**: nosignup.kr DNS 설정 (선택사항)
- [ ] **SSL 인증서**: HTTPS 접속 (선택사항)

## 📈 예상 성능

### 1GB RAM 환경 최적화
- **메모리 사용량**: ~400-600MB
- **CPU 사용률**: ~10-30%
- **응답 시간**: <1초
- **동시 접속**: 5-10명

### 거래 성능
- **지원 거래쌍**: 3개 (BTC, ETH, BNB)
- **최대 동시 거래**: 3개
- **주문 처리 시간**: ~50ms
- **데이터 업데이트**: 5분 간격

## 🎯 다음 단계

### 1. 실제 거래 설정
```bash
# 프로젝트 폴더로 이동
cd /home/linuxuser/freqtrade-future-phase10

# 환경 변수 수정 (실제 API 키)
nano .env

# 설정 파일 수정
nano user_data/config_production.json

# 서비스 재시작
sudo docker restart freqtrade-phase10
```

### 2. 모니터링 강화
- Grafana + Prometheus 설정
- 텔레그램 봇 연동
- 이메일 알림 설정

### 3. 백업 자동화
- 일일 데이터 백업
- 설정 파일 버전 관리
- 클라우드 백업 연동

---

## 🎉 축하합니다!

**원클릭 명령어 한 줄로 Phase 10까지 완성된 Freqtrade Future 시스템이 배포되었습니다!**

**접속 주소**: http://141.164.42.93:8080 (admin/freqtrade2024!)
**도메인 연결 후**: https://nosignup.kr

이제 전문가 수준의 AI 기반 선물 거래 시스템을 사용할 수 있습니다! 🚀