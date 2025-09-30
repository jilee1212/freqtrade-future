# 🔌 PuTTY 접속 가이드

Windows에서 Vultr 서버에 PuTTY로 접속하는 방법입니다.

---

## 📥 1단계: PuTTY 다운로드 (없다면)

### PuTTY 설치 확인

시작 메뉴에서 "PuTTY" 검색

- **있으면:** 바로 2단계로
- **없으면:** 아래에서 다운로드

### PuTTY 다운로드

**공식 사이트:**
https://www.putty.org/

**다운로드 링크:**
https://the.earth.li/~sgtatham/putty/latest/w64/putty.exe

**또는 설치 버전:**
https://the.earth.li/~sgtatham/putty/latest/w64/putty-64bit-0.81-installer.msi

---

## 🚀 2단계: PuTTY 실행

### 방법 1: 시작 메뉴
```
시작 → "PuTTY" 검색 → PuTTY 실행
```

### 방법 2: 다운로드한 파일
```
다운로드 폴더 → putty.exe 더블클릭
```

---

## ⚙️ 3단계: 서버 접속 설정

PuTTY 창이 열리면:

### 기본 설정 화면

```
┌─────────────────────────────────────┐
│ PuTTY Configuration                 │
├─────────────────────────────────────┤
│                                     │
│ Host Name (or IP address)           │
│ ┌─────────────────────────────────┐ │
│ │ 141.164.42.93                   │ │ ← 여기에 입력
│ └─────────────────────────────────┘ │
│                                     │
│ Port         Connection type        │
│ ┌──────┐     ○ Raw                 │
│ │ 22   │     ○ Telnet              │ ← 22 확인
│ └──────┘     ● SSH                 │ ← SSH 선택
│              ○ Serial              │
│                                     │
│              [Open]                 │ ← 클릭
└─────────────────────────────────────┘
```

### 입력 내용

1. **Host Name:** `141.164.42.93`
2. **Port:** `22`
3. **Connection type:** `SSH` (선택)
4. **[Open]** 버튼 클릭

---

## 🔐 4단계: 보안 경고 (처음 접속 시)

### 첫 접속 시 나타나는 창

```
┌─────────────────────────────────────────┐
│ PuTTY Security Alert                    │
├─────────────────────────────────────────┤
│ The server's host key is not cached    │
│ in the registry...                      │
│                                         │
│ Do you trust this host?                 │
│                                         │
│   [Accept]  [Connect Once]  [Cancel]   │
└─────────────────────────────────────────┘
```

**"Accept"** 또는 **"예(Y)"** 클릭

---

## 👤 5단계: 로그인

### 검은 터미널 창이 나타남

```
login as: _
```

**1. Username 입력:**
```
login as: linuxuser
```
Enter 키 입력

**2. Password 입력:**
```
linuxuser@141.164.42.93's password: _
```
비밀번호 입력 (화면에 표시 안됨, 정상입니다!)
Enter 키 입력

**⚠️ 주의:** 비밀번호 입력 시 화면에 아무것도 표시되지 않지만 정상입니다!

---

## ✅ 6단계: 접속 성공

### 접속 성공 시 화면

```
Welcome to Ubuntu 24.04 LTS (GNU/Linux 6.8.0-45-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

Last login: Mon Sep 30 12:34:56 2024 from xxx.xxx.xxx.xxx

linuxuser@vultr:~$ _
```

이제 명령어를 입력할 수 있습니다! 🎉

---

## 📋 배포 명령어 실행

### 방법 1: 전체 스크립트 복사 붙여넣기 (추천)

1. **[FINAL_DEPLOYMENT_GUIDE.md](FINAL_DEPLOYMENT_GUIDE.md)** 파일 열기

2. **2️⃣ 전체 명령어 실행** 섹션의 스크립트 전체 복사
   - 맨 위부터 맨 아래까지 전체 선택
   - `Ctrl+C` 복사

3. **PuTTY 창에서 붙여넣기**
   - **마우스 오른쪽 클릭** (자동으로 붙여넣기됨)
   - 또는 `Shift+Insert`

4. **Enter 키 입력**

5. **sudo 비밀번호 입력** (Swap 메모리 생성 시)
   ```
   [sudo] password for linuxuser: _
   ```
   비밀번호 입력 → Enter

6. **15-20분 대기** (Docker 빌드 중)

### 방법 2: 단계별 실행

각 명령어를 하나씩 복사해서 실행

---

## 🎨 PuTTY 사용 팁

### 복사 & 붙여넣기

**복사:**
- PuTTY 창에서 텍스트 드래그 → 자동 복사

**붙여넣기:**
- **마우스 오른쪽 클릭** (가장 쉬움)
- 또는 `Shift+Insert`

### 화면 스크롤

- **마우스 휠** 위/아래
- 또는 `Shift+PageUp` / `Shift+PageDown`

### 명령어 취소

- `Ctrl+C` - 현재 실행 중인 명령어 중단

### 로그 종료

- `Ctrl+C` - 로그 보기 종료 (docker-compose logs -f)

### 세션 저장 (다음에 빠르게 접속)

PuTTY 설정 창에서:
1. Host Name: `141.164.42.93` 입력
2. Port: `22` 입력
3. **Saved Sessions** 칸에 이름 입력 (예: "Vultr-Seoul")
4. **[Save]** 버튼 클릭
5. 다음부터는 저장된 세션 더블클릭으로 바로 접속!

---

## 🔧 문제 해결

### 1. "Connection refused" 에러

**원인:**
- 서버가 꺼져있음
- 방화벽이 SSH(22번 포트) 차단

**해결:**
1. Vultr 웹사이트에서 서버 상태 확인
2. 서버 재시작
3. 방화벽 설정 확인

### 2. "Access denied" 또는 비밀번호 오류

**원인:**
- 비밀번호가 틀림
- Username이 틀림

**해결:**
1. Username 확인: `linuxuser`
2. 비밀번호 재확인 (Vultr 웹사이트)
3. Caps Lock 확인

### 3. "Network error: Connection timed out"

**원인:**
- 인터넷 연결 문제
- 서버 IP가 틀림

**해결:**
1. 인터넷 연결 확인
2. IP 주소 확인: `141.164.42.93`
3. 잠시 후 재시도

### 4. 한글이 깨져서 보임

**해결:**
1. PuTTY 설정 창 열기
2. **Window → Translation**
3. **Remote character set:** `UTF-8` 선택
4. **[Apply]** 클릭

---

## 📱 대체 방법: Windows Terminal (선택사항)

Windows 11이나 최신 Windows 10이라면 기본 제공:

### Windows Terminal 사용

1. **시작 → "Terminal" 또는 "PowerShell" 검색**

2. **다음 명령어 입력:**
```powershell
ssh linuxuser@141.164.42.93
```

3. **비밀번호 입력**

더 깔끔하고 복사/붙여넣기가 편리합니다!

---

## 🎯 빠른 체크리스트

배포 실행 전:

- [ ] PuTTY 다운로드 및 설치
- [ ] PuTTY 실행
- [ ] Host Name: `141.164.42.93` 입력
- [ ] Port: `22` 확인
- [ ] Connection type: `SSH` 선택
- [ ] **[Open]** 클릭
- [ ] Username: `linuxuser` 입력
- [ ] 비밀번호 입력
- [ ] 접속 성공!
- [ ] [FINAL_DEPLOYMENT_GUIDE.md](FINAL_DEPLOYMENT_GUIDE.md) 열기
- [ ] 배포 스크립트 복사
- [ ] PuTTY에 **마우스 오른쪽 클릭**으로 붙여넣기
- [ ] Enter 키
- [ ] 15-20분 대기
- [ ] http://141.164.42.93:3000 접속 확인!

---

## 📸 스크린샷 가이드

### 1. PuTTY 설정 화면
```
┌──────────────────────────────────────────┐
│ PuTTY Configuration                      │
├──────────────────────────────────────────┤
│ Category:                                │
│  ├─ Session                              │
│  ├─ Terminal                             │
│  ├─ Window                               │
│  └─ Connection                           │
│                                          │
│ Basic options for your PuTTY session    │
│                                          │
│ Specify the destination you want to     │
│ connect to                               │
│                                          │
│ Host Name (or IP address)                │
│ ┌────────────────────────────────────┐   │
│ │ 141.164.42.93                      │   │ ← 입력
│ └────────────────────────────────────┘   │
│                                          │
│ Port: 22        Connection type: SSH     │ ← 확인
│                                          │
│                        [Open]            │ ← 클릭
└──────────────────────────────────────────┘
```

### 2. 로그인 화면
```
┌──────────────────────────────────────────┐
│ login as: linuxuser                      │ ← 입력
│ linuxuser@141.164.42.93's password:      │ ← 비밀번호 입력
│                                          │
│ Welcome to Ubuntu 24.04 LTS              │
│                                          │
│ linuxuser@vultr:~$                       │ ← 성공!
└──────────────────────────────────────────┘
```

---

## 🌟 다음 단계

PuTTY 접속 성공 후:

1. **배포 스크립트 실행**
   - [FINAL_DEPLOYMENT_GUIDE.md](FINAL_DEPLOYMENT_GUIDE.md) 참조

2. **15-20분 대기**
   - Docker 빌드 중

3. **접속 확인**
   - http://141.164.42.93:3000

4. **완료!** 🎉

---

**접속 정보:**
- IP: 141.164.42.93
- Port: 22
- Username: linuxuser
- Password: (귀하의 비밀번호)

**PuTTY 다운로드:** https://www.putty.org/

**도움이 필요하면:** [FINAL_DEPLOYMENT_GUIDE.md](FINAL_DEPLOYMENT_GUIDE.md) 참조