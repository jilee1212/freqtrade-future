# 🔄 기존 서버 정리 및 Phase 10 새로운 배포 가이드

## 서버 정보
- **IP**: 141.164.42.93 (Seoul, Korea)
- **사양**: 1 vCPU, 1GB RAM, 25GB NVMe SSD
- **OS**: Ubuntu 24.04 LTS x64
- **사용자**: linuxuser
- **생성일**: 5일 전

## 🎯 배포 목표
기존 서버에서 이전 프로젝트를 안전하게 백업하고 새로운 **Phase 10 완성된 Freqtrade Future 시스템**을 배포합니다.

## 📋 배포 단계

### 1단계: 서버 접속
```bash
# SSH 접속
ssh linuxuser@141.164.42.93

# 비밀번호 입력 (기존 설정된 비밀번호)
```

### 2단계: 자동 정리 및 배포 스크립트 실행
```bash
# 배포 스크립트 다운로드
curl -sSL https://raw.githubusercontent.com/jilee1212/freqtrade-future/master/server_cleanup_and_deploy.sh -o cleanup_deploy.sh

# 실행 권한 부여
chmod +x cleanup_deploy.sh

# 자동 배포 실행 (10-15분 소요)
./cleanup_deploy.sh
```

### 3단계: 배포 과정 모니터링
스크립트 실행 중 다음과 같은 단계들이 진행됩니다:

```
🔍 기존 Vultr 서버 정리 및 Phase 10 새로운 배포 시작...

[INFO] 현재 시스템 상태 확인 중...
[INFO] 기존 Freqtrade 프로세스 확인 중...
[WARNING] 기존 Freqtrade 프로세스 발견됨 (있는 경우)
[INFO] 기존 Freqtrade 프로세스 종료 중...
[SUCCESS] 실행 중인 Freqtrade 프로세스 없음

[INFO] 기존 Docker 컨테이너 확인 중...
[WARNING] 기존 Freqtrade Docker 컨테이너 발견됨 (있는 경우)
[INFO] 기존 Freqtrade 컨테이너 정리 중...
[SUCCESS] 기존 컨테이너 정리 완료

[INFO] 기존 프로젝트 디렉토리 확인 중...
[WARNING] 기존 프로젝트 발견: /home/linuxuser/freqtrade (있는 경우)
[INFO] 기존 프로젝트 백업 중...
[SUCCESS] 백업 완료: /home/linuxuser/backup_20250928_210000

[INFO] 시스템 패키지 업데이트 중...
[SUCCESS] 시스템 업데이트 완료

[INFO] Docker 설치 확인 중...
[SUCCESS] Docker 설치 완료

[INFO] 새로운 Phase 10 프로젝트 클론 중...
[SUCCESS] GitHub 프로젝트 클론 완료

[INFO] Docker Compose 서비스 시작 중...
[SUCCESS] Docker 서비스가 정상적으로 실행 중입니다
```

### 4단계: 배포 완료 확인
배포가 성공적으로 완료되면 다음과 같은 정보가 표시됩니다:

```
🎉 기존 서버 정리 및 Phase 10 새로운 배포 완료!
==================================================

🌐 서버 정보:
   - 서버 IP: 141.164.42.93
   - 위치: Seoul, Korea
   - 사양: 1 vCPU, 1GB RAM, 25GB SSD
   - 운영체제: Ubuntu 24.04
   - Docker 버전: 24.x.x

🔗 접속 정보:
   - FreqUI 웹 인터페이스: http://141.164.42.93:8080
   - SSH 접속: ssh linuxuser@141.164.42.93
   - FreqTrade 사용자: ssh freqtrade@141.164.42.93
   - 로그인 정보:
     * Username: admin
     * Password: freqtrade2024!

📊 현재 서비스 상태:
NAME                    IMAGE                           STATUS
freqtrade-futures       freqtradeorg/freqtrade:stable   Up X minutes
freqtrade-nginx         nginx:alpine                    Up X minutes

💾 백업 정보:
   - 기존 프로젝트 백업: /home/linuxuser/backup_YYYYMMDD_HHMMSS
   - 백업된 프로젝트: [기존 프로젝트 목록]
```

## 🌐 웹 인터페이스 접속

### 5단계: Phase 10 시스템 확인
1. **웹 브라우저에서 접속**: http://141.164.42.93:8080
2. **로그인**:
   - Username: `admin`
   - Password: `freqtrade2024!`
3. **Phase 10 기능 확인**:
   - ✅ **실시간 대시보드**: 차트 및 데이터 업데이트
   - ✅ **AI 위험 관리**: 동적 레버리지 시스템
   - ✅ **Ross Cameron RSI**: 전략 신호 생성
   - ✅ **모니터링 시스템**: 성능 지표 및 알림
   - ✅ **안전 시스템**: 회로차단기 동작 확인

## 🔧 nosignup.kr 도메인 연결

### 6단계: DNS 설정
도메인 관리 패널에서 다음 설정:
```
Type: A
Name: @ (또는 비워둠)
Value: 141.164.42.93
TTL: 300 (5분)

Type: CNAME (선택사항)
Name: www
Value: nosignup.kr
```

### 7단계: SSL 인증서 설정 (선택사항)
```bash
# 서버에서 실행
ssh freqtrade@141.164.42.93

# SSL 인증서 발급 (DNS 전파 완료 후)
sudo certbot --nginx -d nosignup.kr -d www.nosignup.kr
```

## 📊 시스템 모니터링

### 주요 모니터링 명령어
```bash
# 서비스 상태 확인
sudo systemctl status freqtrade-futures

# Docker 컨테이너 상태
cd /opt/freqtrade-futures
docker compose ps

# 실시간 로그 확인
docker compose logs -f freqtrade

# 시스템 리소스 확인
htop
free -h
df -h

# 프로덕션 모니터링 실행
./production_monitor.py
```

### 성능 최적화 (1GB RAM 환경)
```bash
# 메모리 사용량 확인
free -h

# 스왑 사용량 확인
swapon --show

# Docker 메모리 사용량
docker stats

# 불필요한 서비스 중지 (필요시)
sudo systemctl stop apache2 nginx mysql
```

## 🚨 문제 해결

### 일반적인 문제
1. **메모리 부족 오류**
   ```bash
   # 스왑 파일 확인
   swapon --show

   # 추가 스왑 생성 (필요시)
   sudo fallocate -l 1G /swapfile2
   sudo chmod 600 /swapfile2
   sudo mkswap /swapfile2
   sudo swapon /swapfile2
   ```

2. **Docker 서비스 실패**
   ```bash
   # 로그 확인
   docker compose logs freqtrade

   # 서비스 재시작
   docker compose restart

   # 완전 재배포 (필요시)
   docker compose down
   docker compose pull
   docker compose up -d
   ```

3. **웹 접속 불가**
   ```bash
   # 포트 확인
   sudo netstat -tulpn | grep :8080

   # 방화벽 확인
   sudo ufw status

   # Nginx 상태 확인
   docker compose logs nginx
   ```

### 백업 데이터 복구 (필요시)
```bash
# 백업 디렉토리 확인
ls -la /home/linuxuser/backup_*

# 기존 설정 복구 (필요한 부분만)
cp /home/linuxuser/backup_*/freqtrade_config.json /opt/freqtrade-futures/user_data/
cp /home/linuxuser/backup_*/freqtrade_env /opt/freqtrade-futures/.env

# 서비스 재시작
cd /opt/freqtrade-futures
docker compose restart
```

## ✅ 배포 완료 체크리스트

- [ ] **기존 프로젝트 백업**: 안전하게 백업됨
- [ ] **새로운 시스템 배포**: GitHub에서 Phase 10 코드 클론
- [ ] **Docker 서비스 실행**: 모든 컨테이너 Up 상태
- [ ] **웹 인터페이스 접속**: http://141.164.42.93:8080 정상 동작
- [ ] **Phase 10 기능 확인**: AI 시스템, 전략, 모니터링 동작
- [ ] **시스템 모니터링**: 리소스 사용량 정상 범위
- [ ] **도메인 연결**: nosignup.kr → 141.164.42.93 DNS 설정
- [ ] **SSL 인증서**: HTTPS 접속 가능 (선택사항)

## 🎯 예상 결과

### 배포 후 접속 가능한 주소
- **임시 접속**: http://141.164.42.93:8080
- **도메인 접속**: https://nosignup.kr (DNS 전파 및 SSL 설정 후)

### Phase 10 완성된 기능들
- **🤖 AI 위험 관리**: 실시간 레버리지 최적화
- **📈 Ross Cameron RSI**: 검증된 선물 거래 전략
- **📊 실시간 대시보드**: WebSocket 기반 실시간 업데이트
- **🔔 모니터링 시스템**: 성능 지표 및 알림
- **🛡️ 안전 시스템**: 회로차단기 및 비상 정지
- **💾 자동 백업**: 데이터 손실 방지
- **📋 컴플라이언스**: 규제 준수 시스템

## 📞 지원

문제 발생시 확인 사항:
1. **서비스 로그**: `docker compose logs -f`
2. **시스템 리소스**: `htop`, `free -h`, `df -h`
3. **네트워크 연결**: `curl -I http://141.164.42.93:8080`
4. **GitHub 이슈**: https://github.com/jilee1212/freqtrade-future/issues

---

## 🎉 축하합니다!

**기존 서버에서 Phase 10까지 완성된 Freqtrade Future 시스템이 성공적으로 배포되었습니다!**

이제 **nosignup.kr**을 통해 전문가 수준의 AI 기반 선물 거래 시스템을 사용할 수 있습니다! 🚀