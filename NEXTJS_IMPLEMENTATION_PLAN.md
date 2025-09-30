# 🚀 Freqtrade Future - Next.js 완전 리뉴얼 계획

## 📋 프로젝트 개요

### 목표
기존 Flask + Jinja2 웹앱을 **Next.js 14 + TypeScript + shadcn/ui**로 완전히 현대화

### 아키텍처
```
┌─────────────────────────────────────────────────────────┐
│                    사용자 브라우저                       │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│           Next.js 14 Frontend (Port 3000)               │
│  ┌──────────────────────────────────────────────────┐  │
│  │  - Server Components (초기 로딩 최적화)          │  │
│  │  - Client Components (실시간 업데이트)          │  │
│  │  - shadcn/ui + Tailwind CSS                     │  │
│  │  - TradingView Charts                           │  │
│  │  - Socket.IO Client (실시간)                    │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────┬──────────────────┬───────────────────┘
                   │                  │
                   ▼                  ▼
    ┌──────────────────────┐  ┌──────────────────────┐
    │  Flask API (5000)    │  │  FreqUI (8080)       │
    │  - REST API          │  │  - Freqtrade API     │
    │  - WebSocket Server  │  │  - Trading Bot       │
    │  - DB Access         │  │                      │
    └──────────────────────┘  └──────────────────────┘
                   │                  │
                   ▼                  ▼
         ┌─────────────────────────────────┐
         │  Freqtrade Core + Binance API   │
         └─────────────────────────────────┘
```

---

## 🗂️ 새로운 프로젝트 구조

```
freqtrade-future/                    # 기존 루트 (백엔드)
├── frontend/                        # 🆕 Next.js 프론트엔드
│   ├── .next/                       # Next.js 빌드
│   ├── public/                      # 정적 파일
│   │   ├── favicon.ico
│   │   ├── logo.svg
│   │   └── images/
│   ├── src/
│   │   ├── app/                     # Next.js App Router
│   │   │   ├── layout.tsx           # 루트 레이아웃
│   │   │   ├── page.tsx             # 홈 (/)
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx         # 대시보드 (/dashboard)
│   │   │   ├── trading/
│   │   │   │   └── page.tsx         # 트레이딩 뷰 (/trading)
│   │   │   ├── strategies/
│   │   │   │   ├── page.tsx         # 전략 목록
│   │   │   │   └── [id]/page.tsx   # 전략 상세
│   │   │   ├── risk/
│   │   │   │   └── page.tsx         # 리스크 모니터
│   │   │   ├── backtest/
│   │   │   │   └── page.tsx         # 백테스트
│   │   │   ├── settings/
│   │   │   │   └── page.tsx         # 설정
│   │   │   └── api/                 # API Routes (선택)
│   │   │       └── [...routes]/route.ts
│   │   │
│   │   ├── components/              # 재사용 컴포넌트
│   │   │   ├── ui/                  # shadcn/ui 컴포넌트
│   │   │   │   ├── button.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   ├── dialog.tsx
│   │   │   │   ├── dropdown-menu.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   ├── select.tsx
│   │   │   │   ├── table.tsx
│   │   │   │   └── toast.tsx
│   │   │   │
│   │   │   ├── layout/              # 레이아웃 컴포넌트
│   │   │   │   ├── header.tsx
│   │   │   │   ├── sidebar.tsx
│   │   │   │   ├── footer.tsx
│   │   │   │   └── mobile-nav.tsx
│   │   │   │
│   │   │   ├── dashboard/           # 대시보드 컴포넌트
│   │   │   │   ├── stats-card.tsx
│   │   │   │   ├── equity-chart.tsx
│   │   │   │   ├── open-trades.tsx
│   │   │   │   ├── recent-trades.tsx
│   │   │   │   └── performance-metrics.tsx
│   │   │   │
│   │   │   ├── trading/             # 트레이딩 컴포넌트
│   │   │   │   ├── tradingview-chart.tsx
│   │   │   │   ├── order-book.tsx
│   │   │   │   ├── trade-form.tsx
│   │   │   │   ├── position-list.tsx
│   │   │   │   └── market-info.tsx
│   │   │   │
│   │   │   ├── strategies/          # 전략 컴포넌트
│   │   │   │   ├── strategy-card.tsx
│   │   │   │   ├── strategy-editor.tsx
│   │   │   │   ├── backtest-results.tsx
│   │   │   │   └── optimization-panel.tsx
│   │   │   │
│   │   │   ├── risk/                # 리스크 컴포넌트
│   │   │   │   ├── risk-gauge.tsx
│   │   │   │   ├── risk-breakdown.tsx
│   │   │   │   ├── alert-list.tsx
│   │   │   │   └── drawdown-chart.tsx
│   │   │   │
│   │   │   └── common/              # 공통 컴포넌트
│   │   │       ├── loading.tsx
│   │   │       ├── error-boundary.tsx
│   │   │       ├── real-time-indicator.tsx
│   │   │       └── theme-toggle.tsx
│   │   │
│   │   ├── lib/                     # 유틸리티 & 헬퍼
│   │   │   ├── utils.ts             # 공통 유틸
│   │   │   ├── api.ts               # API 클라이언트
│   │   │   ├── websocket.ts         # WebSocket 클라이언트
│   │   │   ├── hooks/               # Custom Hooks
│   │   │   │   ├── use-websocket.ts
│   │   │   │   ├── use-trades.ts
│   │   │   │   ├── use-balance.ts
│   │   │   │   └── use-strategies.ts
│   │   │   └── constants.ts         # 상수
│   │   │
│   │   ├── types/                   # TypeScript 타입
│   │   │   ├── trade.ts
│   │   │   ├── strategy.ts
│   │   │   ├── balance.ts
│   │   │   ├── risk.ts
│   │   │   └── api.ts
│   │   │
│   │   └── styles/                  # 글로벌 스타일
│   │       └── globals.css          # Tailwind + 커스텀 CSS
│   │
│   ├── .env.local                   # 환경 변수
│   ├── .eslintrc.json              # ESLint 설정
│   ├── .prettierrc                 # Prettier 설정
│   ├── components.json             # shadcn/ui 설정
│   ├── next.config.js              # Next.js 설정
│   ├── package.json
│   ├── tsconfig.json               # TypeScript 설정
│   ├── tailwind.config.ts          # Tailwind 설정
│   └── README.md
│
├── backend/                         # 🔄 기존 Flask 정리
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py               # REST API 엔드포인트
│   │   └── websocket.py            # WebSocket 핸들러
│   ├── services/
│   │   ├── freqtrade_client.py     # Freqtrade API 클라이언트
│   │   ├── trade_service.py
│   │   ├── strategy_service.py
│   │   └── risk_service.py
│   ├── models/
│   │   └── database.py
│   ├── app.py                      # Flask 앱
│   └── requirements.txt
│
├── user_data/                       # 기존 Freqtrade 데이터
├── ai_optimization/                 # 기존 AI 모듈
├── docker-compose.yml              # 🔄 수정 필요
├── Dockerfile                      # 🔄 수정 필요
└── docs/                           # 🆕 문서
    ├── 00_PROJECT_OVERVIEW.md
    ├── 01_FRONTEND_SETUP.md
    ├── 02_COMPONENT_GUIDE.md
    ├── 03_API_INTEGRATION.md
    ├── 04_DEPLOYMENT.md
    └── 05_DEVELOPMENT_GUIDE.md
```

---

## 📚 새로운 문서 구조

### 기존 문서 (유지)
- `01_PRD_MAIN.md` - 전체 프로젝트 PRD
- `02_FUTURES_AGENTIC_CODING_GUIDE.md` - 개발 가이드
- `03_FUTURES_AUTOMATION_SETUP.md` - 자동화 설정
- `04_FUTURES_TROUBLESHOOTING.md` - 문제 해결
- `05_FUTURES_VULTR_DEPLOYMENT.md` - 배포 가이드
- `06_BINANCE_FUTURES_API_REFERENCE.md` - API 레퍼런스
- `07_LEVERAGE_RISK_MANAGEMENT.md` - 리스크 관리
- `08_FUNDING_RATE_STRATEGY.md` - 펀딩 전략

### 새로운 프론트엔드 문서
```
docs/frontend/
├── 00_FRONTEND_OVERVIEW.md          # 프론트엔드 개요
├── 01_SETUP_GUIDE.md                # 설치 및 설정
├── 02_ARCHITECTURE.md               # 아키텍처 설명
├── 03_COMPONENT_LIBRARY.md          # 컴포넌트 라이브러리
├── 04_STATE_MANAGEMENT.md           # 상태 관리
├── 05_API_INTEGRATION.md            # API 통합
├── 06_WEBSOCKET_REALTIME.md         # 실시간 데이터
├── 07_STYLING_GUIDE.md              # 스타일 가이드
├── 08_TESTING.md                    # 테스트
├── 09_DEPLOYMENT.md                 # 배포
└── 10_MAINTENANCE.md                # 유지보수
```

---

## 🛠️ 기술 스택 상세

### Frontend
```json
{
  "framework": "Next.js 14.2.x (App Router)",
  "language": "TypeScript 5.x",
  "styling": {
    "css": "Tailwind CSS 3.4.x",
    "components": "shadcn/ui",
    "icons": "lucide-react"
  },
  "charts": {
    "financial": "TradingView Lightweight Charts",
    "general": "Recharts",
    "advanced": "Apache ECharts"
  },
  "state": {
    "server": "React Server Components",
    "client": "Zustand / React Context",
    "async": "TanStack Query (React Query)"
  },
  "realtime": "Socket.IO Client",
  "forms": "React Hook Form + Zod",
  "tables": "TanStack Table",
  "animations": "Framer Motion"
}
```

### Backend (기존 유지)
```json
{
  "framework": "Flask 3.x",
  "language": "Python 3.11+",
  "realtime": "Flask-SocketIO",
  "api": "REST + WebSocket",
  "cors": "Flask-CORS"
}
```

---

## 🚀 구현 로드맵

### Week 1: 프로젝트 셋업 및 기본 구조
- [ ] **Day 1-2: 프로젝트 초기화**
  - Next.js 프로젝트 생성
  - TypeScript 설정
  - shadcn/ui 설치 및 설정
  - Tailwind CSS 커스터마이징
  - 디렉토리 구조 생성
  - ESLint/Prettier 설정

- [ ] **Day 3-4: 기본 레이아웃 구현**
  - Header 컴포넌트
  - Sidebar 컴포넌트
  - Footer 컴포넌트
  - 반응형 네비게이션
  - 다크 모드 토글

- [ ] **Day 5-7: 홈페이지 & 대시보드**
  - 랜딩 페이지 디자인
  - 대시보드 레이아웃
  - Stats Cards 컴포넌트
  - 기본 차트 통합

### Week 2: 핵심 기능 구현
- [ ] **Day 8-10: API 통합**
  - API 클라이언트 설정
  - Freqtrade API 연동
  - WebSocket 연결
  - 실시간 데이터 스트리밍
  - React Query 설정

- [ ] **Day 11-12: 트레이딩 페이지**
  - TradingView 차트 통합
  - Order Book 컴포넌트
  - Trade Form
  - Position List

- [ ] **Day 13-14: 전략 관리**
  - 전략 목록 페이지
  - 전략 상세 페이지
  - 백테스트 결과 시각화
  - 최적화 패널

### Week 3: 고급 기능
- [ ] **Day 15-17: 리스크 모니터**
  - Risk Gauge 컴포넌트
  - Risk Breakdown 차트
  - Alert 시스템
  - Drawdown 분석

- [ ] **Day 18-19: 백테스트**
  - 백테스트 설정 UI
  - 결과 시각화
  - 비교 분석 도구

- [ ] **Day 20-21: 설정 & 프로필**
  - 사용자 설정 페이지
  - API 키 관리
  - 알림 설정
  - 테마 설정

### Week 4: 최적화 & 배포
- [ ] **Day 22-24: 성능 최적화**
  - 코드 스플리팅
  - 이미지 최적화
  - 캐싱 전략
  - SEO 최적화

- [ ] **Day 25-26: 테스트**
  - Unit Tests (Jest)
  - Integration Tests
  - E2E Tests (Playwright)

- [ ] **Day 27-28: 배포**
  - Docker 설정
  - Nginx 리버스 프록시
  - 프로덕션 환경 설정
  - CI/CD 파이프라인

---

## 📦 패키지 구성

### package.json
```json
{
  "name": "freqtrade-future-frontend",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-dropdown-menu": "^2.0.6",
    "@radix-ui/react-select": "^2.0.0",
    "@radix-ui/react-slot": "^1.0.2",
    "@radix-ui/react-toast": "^1.1.5",
    "@tanstack/react-query": "^5.28.0",
    "@tanstack/react-table": "^8.13.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "date-fns": "^3.3.0",
    "framer-motion": "^11.0.0",
    "lightweight-charts": "^4.1.0",
    "lucide-react": "^0.356.0",
    "recharts": "^2.12.0",
    "socket.io-client": "^4.7.0",
    "tailwind-merge": "^2.2.0",
    "zustand": "^4.5.0",
    "zod": "^3.22.0",
    "react-hook-form": "^7.51.0"
  },
  "devDependencies": {
    "@types/node": "^20.11.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "typescript": "^5.3.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "eslint": "^8.56.0",
    "eslint-config-next": "^14.2.0",
    "prettier": "^3.2.0",
    "prettier-plugin-tailwindcss": "^0.5.0"
  }
}
```

---

## 🎨 디자인 시스템

### 색상 팔레트
```typescript
// tailwind.config.ts
const colors = {
  // Dark Mode (Primary)
  background: {
    primary: '#0d1117',    // 메인 배경
    secondary: '#161b22',  // 카드 배경
    tertiary: '#21262d',   // 경계선
  },

  // Trading Colors
  trading: {
    long: '#10b981',       // 롱 포지션 (그린)
    short: '#ef4444',      // 숏 포지션 (레드)
    neutral: '#6b7280',    // 중립
  },

  // Accent
  primary: {
    DEFAULT: '#3b82f6',    // 블루
    hover: '#2563eb',
  },
  secondary: {
    DEFAULT: '#8b5cf6',    // 퍼플
    hover: '#7c3aed',
  },

  // Status
  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
  info: '#3b82f6',
}
```

### Typography
```typescript
const fonts = {
  sans: ['Inter', 'system-ui', 'sans-serif'],
  mono: ['JetBrains Mono', 'monospace'],
}

const fontSize = {
  xs: '0.75rem',      // 12px
  sm: '0.875rem',     // 14px
  base: '1rem',       // 16px
  lg: '1.125rem',     // 18px
  xl: '1.25rem',      // 20px
  '2xl': '1.5rem',    // 24px
  '3xl': '1.875rem',  // 30px
  '4xl': '2.25rem',   // 36px
}
```

---

## 🔌 API 인터페이스

### Flask API 엔드포인트 (필요한 것)
```python
# backend/api/routes.py

@app.route('/api/v1/status')
def get_status():
    """봇 상태 조회"""
    pass

@app.route('/api/v1/balance')
def get_balance():
    """잔고 조회"""
    pass

@app.route('/api/v1/trades')
def get_trades():
    """거래 내역"""
    pass

@app.route('/api/v1/open_trades')
def get_open_trades():
    """오픈 포지션"""
    pass

@app.route('/api/v1/profit')
def get_profit():
    """수익 통계"""
    pass

@app.route('/api/v1/strategies')
def get_strategies():
    """전략 목록"""
    pass

@app.route('/api/v1/backtest', methods=['POST'])
def run_backtest():
    """백테스트 실행"""
    pass

@app.route('/api/v1/risk')
def get_risk():
    """리스크 데이터"""
    pass
```

### WebSocket 이벤트
```python
# backend/api/websocket.py

@socketio.on('connect')
def handle_connect():
    """클라이언트 연결"""
    pass

@socketio.on('subscribe')
def handle_subscribe(data):
    """채널 구독"""
    # 채널: trades, balance, status, risk
    pass

# 서버 → 클라이언트 이벤트
# - trade_update
# - balance_update
# - status_update
# - risk_alert
# - new_signal
```

---

## 🐳 Docker 구성

### docker-compose.yml (업데이트)
```yaml
version: '3.8'

services:
  # Next.js Frontend
  frontend:
    build: ./frontend
    container_name: freqtrade-frontend
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:5000
      - NEXT_PUBLIC_WS_URL=ws://backend:5000
    depends_on:
      - backend
    networks:
      - freqtrade-network

  # Flask Backend
  backend:
    build: ./backend
    container_name: freqtrade-backend
    restart: unless-stopped
    ports:
      - "5000:5000"
    volumes:
      - ./user_data:/app/user_data
    environment:
      - FLASK_ENV=production
      - FREQTRADE_API_URL=http://freqtrade:8080
    depends_on:
      - freqtrade
    networks:
      - freqtrade-network

  # Freqtrade Bot (기존)
  freqtrade:
    image: freqtradeorg/freqtrade:stable
    container_name: freqtrade-bot
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - ./user_data:/freqtrade/user_data
    command: freqtrade webserver --config user_data/config_futures.json
    networks:
      - freqtrade-network

  # Nginx (리버스 프록시)
  nginx:
    image: nginx:alpine
    container_name: freqtrade-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
      - freqtrade
    networks:
      - freqtrade-network

networks:
  freqtrade-network:
    driver: bridge
```

---

## 📝 즉시 시작하기

### 1단계: Next.js 프로젝트 생성
```bash
# 로컬에서 실행
cd c:\Users\jilee\freqtrade-future

# Next.js 프로젝트 생성
npx create-next-app@latest frontend --typescript --tailwind --app --src-dir --import-alias "@/*"

cd frontend

# shadcn/ui 초기화
npx shadcn-ui@latest init

# 필수 패키지 설치
npm install @tanstack/react-query socket.io-client zustand
npm install lightweight-charts recharts lucide-react
npm install react-hook-form zod @hookform/resolvers
npm install framer-motion class-variance-authority clsx tailwind-merge
```

### 2단계: 프로젝트 구조 생성
```bash
# 디렉토리 생성
mkdir -p src/components/{ui,layout,dashboard,trading,strategies,risk,common}
mkdir -p src/lib/hooks
mkdir -p src/types
mkdir -p docs/frontend
```

### 3단계: 환경 변수 설정
```bash
# frontend/.env.local
cat > .env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://141.164.42.93:5000
NEXT_PUBLIC_WS_URL=ws://141.164.42.93:5000
NEXT_PUBLIC_FREQTRADE_URL=http://141.164.42.93:8080
EOF
```

### 4단계: 개발 서버 시작
```bash
npm run dev

# 브라우저에서: http://localhost:3000
```

---

## ✅ 체크리스트

### 준비 단계
- [ ] Node.js 18+ 설치 확인
- [ ] Git 설정
- [ ] VS Code 설치 및 확장 프로그램 설치
  - ESLint
  - Prettier
  - Tailwind CSS IntelliSense
  - TypeScript

### 개발 환경
- [ ] Next.js 프로젝트 생성
- [ ] shadcn/ui 설치
- [ ] 개발 서버 실행 확인
- [ ] Hot reload 동작 확인

### 백엔드 연동
- [ ] Flask API CORS 설정
- [ ] API 엔드포인트 테스트
- [ ] WebSocket 연결 테스트

---

## 🎯 최종 목표

완성 시 얻게 될 것:

✅ **최신 기술 스택**
- Next.js 14 Server Components
- TypeScript 완전 타입 안정성
- Tailwind CSS 모던 스타일링
- shadcn/ui 엔터프라이즈급 컴포넌트

✅ **뛰어난 성능**
- 초기 로딩: < 1초
- Time to Interactive: < 2초
- 100점 만점 Lighthouse 점수

✅ **완벽한 UX**
- 부드러운 애니메이션
- 실시간 업데이트
- 반응형 디자인
- 다크/라이트 모드

✅ **확장 가능한 구조**
- 컴포넌트 재사용
- 타입 안정성
- 테스트 가능
- 유지보수 용이

---

## 📞 다음 단계

1. **즉시 시작**: 위의 "즉시 시작하기" 섹션 따라하기
2. **단계별 가이드**: 각 Week별 태스크 진행
3. **실시간 지원**: 막히는 부분 있으면 즉시 질문

**지금 바로 시작하시겠습니까?**
제가 첫 번째 파일들을 생성해드릴까요?