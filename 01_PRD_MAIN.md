# Binance USDT Perpetual Freqtrade AI 시스템 PRD

## 🎯 프로젝트 개요

### 목표
Binance USDT Perpetual Futures 전용 Freqtrade AI 자동매매 시스템 구축
- **선물 거래 특화**: 레버리지, 마진 모드, 자금 조달 수수료 활용
- **AI 리스크 관리**: 레버리지 고려 포지션 계산
- **로스 카메론 전략**: 롱/숏 양방향 RSI 전략
- **완벽한 에이전틱 코딩**: 단계별 검증 기반 개발

### 시스템 구성
- **핵심 엔진**: Freqtrade v2024.12+ (Futures 모드)
- **거래소**: Binance USDT Perpetual Futures
- **API 엔드포인트**: `fapi.binance.com` (72개 엔드포인트 활용)
- **테스트 환경**: `testnet.binancefuture.com`
- **웹 인터페이스**: FreqUI + 선물 거래 전용 기능
- **배포 환경**: Vultr 서버 (새로운 인스턴스)

---

## 🏗️ Phase 1: 개발 환경 설정

### 1.1 시스템 요구사항
```bash
# Python 버전 확인 (3.9+ 필수)
python3 --version

# 시스템 메모리 확인 (최소 4GB 권장)
free -h

# 선물 거래 특화 패키지 확인
curl -I https://fapi.binance.com/fapi/v1/ping
```

### 1.2 새 프로젝트 초기화
```bash
# 새 프로젝트 디렉토리 생성
mkdir binance-futures-freqtrade
cd binance-futures-freqtrade

# Python 가상환경 생성
python3 -m venv .venv
source .venv/bin/activate

# Freqtrade 설치 (Futures 지원)
pip install freqtrade[complete]
freqtrade install-ui
```

### 1.3 프로젝트 구조 설정
```
binance-futures-freqtrade/
├── user_data/
│   ├── strategies/           # 선물 전용 전략들
│   ├── hyperopts/           # 하이퍼옵트 설정
│   ├── data/                # USDT Perpetual 데이터
│   ├── logs/                # 거래 로그
│   └── config_futures.json  # 선물 거래 설정
├── docs/                    # 프로젝트 문서
├── scripts/                 # 자동화 스크립트
├── tests/                   # 테스트 파일
├── monitoring/              # 모니터링 도구
└── deployment/              # 배포 설정
```

---

## ⚙️ Phase 2: Binance Futures API 연동

### 2.1 테스트넷 계정 설정
1. **테스트넷 접속**: https://testnet.binancefuture.com/
2. **GitHub 로그인**: OAuth 인증
3. **테스트 자금 충전**: 무료 USDT 지급
4. **API 키 생성**:
   - Futures Trading 권한 활성화
   - IP 제한 설정 (선택)
   - 출금 권한 비활성화

### 2.2 선물 거래 기본 설정
```json
{
  "max_open_trades": 3,
  "stake_currency": "USDT",
  "stake_amount": "unlimited",
  "tradable_balance_ratio": 0.99,
  "fiat_display_currency": "USD",
  "dry_run": false,
  "dry_run_wallet": 10000,
  "trading_mode": "futures",
  "margin_mode": "isolated",
  "exchange": {
    "name": "binance",
    "key": "testnet_api_key",
    "secret": "testnet_api_secret",
    "sandbox": true,
    "ccxt_config": {
      "enableRateLimit": true,
      "sandbox": true,
      "urls": {
        "api": {
          "public": "https://testnet.binancefuture.com",
          "private": "https://testnet.binancefuture.com"
        }
      },
      "options": {
        "defaultType": "future"
      }
    }
  }
}
```

### 2.3 API 엔드포인트 매핑
**binance_futures_links.json 기반 핵심 엔드포인트:**
- 마켓 데이터: `/fapi/v1/ticker/24hr`, `/fapi/v1/depth`
- 계좌 정보: `/fapi/v2/account`, `/fapi/v2/balance`
- 주문 관리: `/fapi/v1/order`, `/fapi/v1/allOrders`
- 포지션 정보: `/fapi/v2/positionRisk`
- 자금 조달: `/fapi/v1/fundingRate`

---

## 🤖 Phase 3: AI 리스크 관리 시스템 (선물 특화)

### 3.1 선물 AI 리스크 전략 구현
**핵심 특징:**
- 레버리지 고려 포지션 계산
- 동적 레버리지 조정
- 자금 조달 수수료 활용
- 마진 모드별 리스크 관리

**주요 메서드:**
```python
def custom_stake_amount(self, pair, current_time, current_rate, 
                       proposed_stake, min_stake, max_stake, 
                       entry_tag, side, **kwargs):
    """선물 거래 전용 AI 포지션 크기 계산"""
    
    balance = self.wallets.get_total_stake_amount()
    risk_percentage = 1.0  # 선물 거래는 더 보수적
    leverage = self.leverage(pair, current_time, current_rate, 3, 10, entry_tag, side)
    
    # 레버리지 고려한 실제 리스크 계산
    risk_amount = balance * (risk_percentage / 100)
    effective_stop_distance = abs(self.stoploss) * leverage
    position_size = risk_amount / effective_stop_distance
    
    return min(position_size, max_stake)

def leverage(self, pair, current_time, current_rate, 
            proposed_leverage, max_leverage, entry_tag, side, **kwargs):
    """AI 기반 동적 레버리지 계산"""
    
    # 변동성 기반 레버리지 조정
    volatility = self.calculate_volatility(pair)
    
    if volatility > 0.05:    # 고변동성
        return min(2, max_leverage)
    elif volatility > 0.03:  # 중변동성
        return min(5, max_leverage)
    else:                    # 저변동성
        return min(10, max_leverage)
```

### 3.2 리스크 매개변수
- `risk_percentage`: 0.5-2.0% (선물 거래는 보수적)
- `max_leverage`: 1-10x (동적 조정)
- `margin_mode`: "isolated" (포지션별 독립 마진)
- `stoploss`: -0.02 ~ -0.05 (2-5%)

---

## 📈 Phase 4: 로스 카메론 RSI 전략 (선물 최적화)

### 4.1 전략 개요
**로스 카메론 RSI 반전 전략 + 선물 거래 최적화:**
- RSI 과매도/과매수 구간 활용
- 볼린저밴드 확장/수축 패턴
- 롱/숏 양방향 거래
- 자금 조달 수수료 고려

### 4.2 핵심 지표
```python
def populate_indicators(self, dataframe, metadata):
    # 기본 RSI 지표
    dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
    
    # 볼린저밴드
    bb = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2, nbdevdn=2)
    dataframe['bb_upper'] = bb['upperband']
    dataframe['bb_lower'] = bb['lowerband']
    dataframe['bb_percent'] = (dataframe['close'] - dataframe['bb_lower']) / (dataframe['bb_upper'] - dataframe['bb_lower'])
    
    # 선물 거래 특화 지표
    dataframe['funding_rate'] = self.get_funding_rate(metadata['pair'])
    dataframe['mark_price'] = dataframe['close']  # 실제로는 API에서 가져옴
    dataframe['long_short_ratio'] = self.get_long_short_ratio(metadata['pair'])
    
    return dataframe
```

### 4.3 진입/청산 조건
**롱 포지션:**
- RSI < 30 (과매도)
- 볼린저밴드 하단 근처
- 자금 조달료 음수 (롱에 유리)

**숏 포지션:**
- RSI > 70 (과매수)
- 볼린저밴드 상단 근처
- 자금 조달료 양수 (숏에 유리)

---

## 🔗 Phase 5: 고급 선물 거래 기능

### 5.1 자금 조달 수수료 활용
```python
def analyze_funding_rate(self, pair):
    """자금 조달 수수료 분석"""
    
    current_funding = self.get_current_funding_rate(pair)
    
    # 높은 양의 자금 조달료 = 숏 포지션 유리
    if current_funding > 0.01:  # 1%
        return "short_favorable"
    
    # 높은 음의 자금 조달료 = 롱 포지션 유리  
    elif current_funding < -0.01:  # -1%
        return "long_favorable"
    
    return "neutral"
```

### 5.2 포지션 모드 관리
- **One-way Mode**: 기본 모드 (롱/숏 동시 불가)
- **Hedge Mode**: 고급 모드 (롱/숏 동시 가능)
- **마진 모드**: Isolated vs Cross 선택

### 5.3 리스크 관리 고도화
- **ADL(Auto-Deleveraging)**: 자동 감량 시스템 대응
- **강제 청산**: 청산 가격 모니터링
- **포지션 크기 제한**: 최대 노출 한도 설정

---

## 📊 Phase 6: 백테스팅 및 최적화

### 6.1 선물 데이터 다운로드
```bash
# USDT Perpetual 데이터 다운로드
freqtrade download-data \
  --exchange binance \
  --trading-mode futures \
  --timeframes 15m 1h 4h \
  --pairs BTCUSDT ETHUSDT ADAUSDT SOLUSDT BNBUSDT \
  --days 90 \
  --config user_data/config_futures.json
```

### 6.2 백테스팅 실행
```bash
# AI 리스크 전략 백테스팅
freqtrade backtesting \
  --config user_data/config_futures.json \
  --strategy FuturesAIRiskStrategy \
  --trading-mode futures \
  --timerange 20241001-20241201 \
  --breakdown day

# 로스 카메론 전략 백테스팅
freqtrade backtesting \
  --config user_data/config_futures.json \
  --strategy RossCameronFuturesStrategy \
  --trading-mode futures \
  --timerange 20241001-20241201 \
  --breakdown day
```

### 6.3 하이퍼옵트 최적화
```bash
# 선물 거래 특화 하이퍼옵트
freqtrade hyperopt \
  --config user_data/config_futures.json \
  --strategy FuturesAIRiskStrategy \
  --hyperopt-loss SortinoHyperOptLoss \
  --spaces buy sell roi stoploss \
  --epochs 500 \
  --trading-mode futures
```

---

## 💻 Phase 7: 웹 인터페이스 (선물 특화)

### 7.1 FreqUI 선물 기능
- **포지션 모니터링**: 실시간 PnL, 마진 비율
- **자금 조달 수수료**: 다음 수수료 시간 및 비율
- **레버리지 관리**: 포지션별 레버리지 확인
- **청산 가격**: 강제 청산 임계점 모니터링

### 7.2 API 서버 설정
```json
{
  "api_server": {
    "enabled": true,
    "listen_ip_address": "0.0.0.0",
    "listen_port": 8080,
    "verbosity": "error",
    "jwt_secret_key": "futures-trading-secret",
    "username": "freqtrade",
    "password": "futures2024"
  }
}
```

### 7.3 대시보드 기능
- 실시간 포지션 현황
- 자금 조달 수수료 내역
- 레버리지별 수익률 분석
- 마진 사용률 모니터링

---

## 📱 Phase 8: 텔레그램 알림 (선물 특화)

### 8.1 선물 거래 알림 설정
```json
{
  "telegram": {
    "enabled": true,
    "token": "your_bot_token",
    "chat_id": "your_chat_id",
    "notification_settings": {
      "entry": "on",
      "exit": "on",
      "entry_fill": "on",
      "exit_fill": "on",
      "position_update": "on",
      "funding_rate": "on",
      "margin_call": "on",
      "liquidation_warning": "on"
    }
  }
}
```

### 8.2 알림 메시지 예시
- **포지션 진입**: "🔵 LONG BTCUSDT 3x leverage, Size: $1000"
- **자금 조달**: "💰 Funding Rate: +0.01% in 2 hours"
- **마진 경고**: "⚠️ Margin ratio below 20%"
- **청산 경고**: "🚨 Liquidation price approaching: $45,000"

---

## 🚀 Phase 9: Vultr 서버 배포

### 9.1 서버 사양
- **CPU**: 2 vCPU (선물 거래는 더 많은 계산 필요)
- **RAM**: 4GB (레버리지 계산 및 실시간 데이터 처리)
- **Storage**: 80GB NVMe (과거 데이터 저장)
- **Location**: Seoul, Korea (지연시간 최소화)

### 9.2 배포 자동화
```bash
# 배포 스크립트
#!/bin/bash
# scripts/deploy_futures.sh

# 환경 변수 로드
source .env

# 가상환경 활성화
source .venv/bin/activate

# 선물 거래 모드 확인
freqtrade show-config --config user_data/config_futures.json | grep "trading_mode"

# 테스트넷 연결 확인
freqtrade test-pairlist --config user_data/config_futures.json

# 서비스 시작
systemctl start freqtrade-futures
```

### 9.3 Nginx 설정 (선물 특화)
```nginx
server {
    listen 80;
    server_name futures.nosignup.kr;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        
        # WebSocket 지원 (실시간 데이터)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    location /api/v1/futures/ {
        proxy_pass http://127.0.0.1:8080;
        # 선물 API 전용 헤더
        proxy_set_header X-Trading-Mode "futures";
    }
}
```

---

## 🔧 Phase 10: 고급 자동화 및 모니터링

### 10.1 리스크 모니터링
```python
# scripts/risk_monitor.py
class FuturesRiskMonitor:
    def __init__(self):
        self.max_margin_ratio = 0.8  # 80% 마진 사용률 제한
        self.max_drawdown = 0.15     # 15% 최대 손실
        
    def check_margin_ratio(self):
        """마진 비율 확인"""
        positions = self.get_positions()
        for pos in positions:
            if pos['margin_ratio'] > self.max_margin_ratio:
                self.send_alert(f"High margin ratio: {pos['symbol']}")
    
    def check_funding_costs(self):
        """자금 조달 비용 모니터링"""
        for position in self.get_open_positions():
            if position['funding_cost'] > position['unrealized_pnl'] * 0.1:
                self.send_alert(f"High funding cost: {position['symbol']}")
```

### 10.2 성과 분석 도구
```python
# monitoring/futures_analytics.py
def analyze_futures_performance(trades_data):
    """선물 거래 성과 분석"""
    
    metrics = {
        'total_trades': len(trades_data),
        'long_trades': len([t for t in trades_data if t['side'] == 'long']),
        'short_trades': len([t for t in trades_data if t['side'] == 'short']),
        'avg_leverage': np.mean([t['leverage'] for t in trades_data]),
        'funding_fees': sum([t.get('funding_fees', 0) for t in trades_data]),
        'liquidations': len([t for t in trades_data if t.get('liquidated', False)])
    }
    
    return metrics
```

### 10.3 자동 백업 시스템
```bash
# scripts/backup_futures.sh
#!/bin/bash

BACKUP_DIR="/backup/futures-$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# 설정 파일 백업
cp user_data/config_futures.json $BACKUP_DIR/

# 전략 파일 백업
cp -r user_data/strategies/ $BACKUP_DIR/

# 거래 데이터 백업
cp -r user_data/data/ $BACKUP_DIR/

# 로그 백업 (최근 7일)
find user_data/logs/ -name "*.log" -mtime -7 -exec cp {} $BACKUP_DIR/ \;

echo "Backup completed: $BACKUP_DIR"
```

---

## 📋 최종 검증 체크리스트

### ✅ 핵심 기능 검증
- [ ] **Binance Futures API**: 테스트넷 연결 성공
- [ ] **선물 거래 모드**: `trading_mode: futures` 설정 확인
- [ ] **AI 리스크 관리**: 레버리지 고려 포지션 계산 정상
- [ ] **로스 카메론 전략**: 롱/숏 양방향 신호 생성 확인
- [ ] **자금 조달 수수료**: 실시간 수수료 데이터 수집
- [ ] **백테스팅**: 선물 데이터로 성공적 실행
- [ ] **웹 인터페이스**: 선물 거래 정보 표시
- [ ] **텔레그램 알림**: 포지션 변경 알림 수신
- [ ] **서버 배포**: 24시간 무중단 운영
- [ ] **모니터링**: 실시간 리스크 추적

### ⚠️ 주요 위험 요소
1. **레버리지 리스크**: 높은 레버리지로 인한 빠른 손실 가능
2. **자금 조달 수수료**: 포지션 유지 비용 누적
3. **강제 청산**: 마진 부족시 자동 청산
4. **API 제한**: 요청 한도 초과시 거래 중단
5. **시장 변동성**: 급격한 가격 변동시 슬리피지 증가

### 🎯 성공 지표
- **안정성**: 24시간 무중단 운영
- **수익성**: 백테스팅 대비 80% 이상 성과 유지
- **리스크 관리**: AI 시스템이 설정한 손실 한도 준수
- **효율성**: 자금 조달 수수료 최적화
- **확장성**: 다중 전략 동시 운영 가능

---

## 🔮 향후 확장 계획

### Phase 11-15 (선택사항)
- **Phase 11**: 다중 거래소 연동 (Bybit, OKX)
- **Phase 12**: 기관투자자용 API 연동
- **Phase 13**: 머신러닝 기반 가격 예측
- **Phase 14**: 크로스 마진 고급 전략
- **Phase 15**: DeFi 프로토콜 연동

### 기술적 고도화
- **실시간 스트리밍**: WebSocket 기반 초저지연 거래
- **멀티 스레딩**: 동시 다중 전략 실행
- **클라우드 확장**: AWS/GCP 멀티 리전 배포
- **AI 모델**: 강화학습 기반 전략 최적화

---

## 🎉 결론

이 PRD는 **Binance USDT Perpetual Futures 전용** Freqtrade AI 자동매매 시스템 구축을 위한 완전한 설계 문서입니다.

**핵심 특징:**
- ✅ **선물 거래 특화**: 레버리지, 마진, 자금 조달 수수료 완전 활용
- ✅ **AI 리스크 관리**: 선물 거래 리스크 고려한 지능형 포지션 계산
- ✅ **로스 카메론 전략**: 검증된 RSI 반전 전략의 선물 거래 최적화
- ✅ **완전 자동화**: 테스트넷부터 실거래까지 단계별 자동화
- ✅ **에이전틱 코딩**: 단계별 검증 기반 체계적 개발

**다음 단계**: 02_AGENTIC_CODING_GUIDE.md로 구체적인 개발 방법론 정의