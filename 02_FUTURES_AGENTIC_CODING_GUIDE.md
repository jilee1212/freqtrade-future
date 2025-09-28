# 🛠️ Binance Futures AI 시스템 에이전틱 코딩 가이드

[![Agentic Coding](https://img.shields.io/badge/Agentic%20Coding-Verified%20Development-blue.svg)](https://github.com/your-repo)
[![Phase Based](https://img.shields.io/badge/Development-10%20Phase%20Structure-green.svg)](https://github.com/your-repo)
[![Test Driven](https://img.shields.io/badge/Approach-Test%20Driven-orange.svg)](https://github.com/your-repo)

> **검증 기반 체계적 개발 방법론**  
> 선물거래 AI 시스템을 위한 단계별 구현 및 검증 가이드

---

## 🎯 에이전틱 코딩이란?

**에이전틱 코딩(Agentic Coding)**은 AI 에이전트처럼 작동하는 체계적 개발 방법론입니다.

### 🔥 핵심 원칙

1. **📋 Phase 기반 구조**: 10단계로 나누어 순차적 개발
2. **✅ 검증 우선**: 각 단계마다 기능 검증 후 다음 단계 진행
3. **🔄 점진적 개선**: 작은 단위로 개발하고 즉시 테스트
4. **📝 실시간 문서화**: 모든 변경사항을 즉시 기록
5. **🎯 목표 지향**: 각 Phase별 명확한 성공 기준 설정

### 💡 왜 에이전틱 코딩인가?

| 기존 개발 방식 | **에이전틱 코딩** |
|-------------|-------------|
| 한번에 모든 기능 구현 | 단계별 점진적 구현 |
| 마지막에 통합 테스트 | 매 단계마다 검증 |
| 문서화 뒤로 미룸 | 실시간 문서화 |
| 버그 발견이 늦음 | 조기 버그 발견 및 수정 |

---

## 🗺️ 10단계 Phase 로드맵

### 📊 Phase 개요 및 우선순위

| Phase | 제목 | 중요도 | 예상 시간 | 의존성 |
|-------|------|--------|----------|---------|
| **Phase 1** | 개발 환경 설정 | 🔥🔥🔥 | 2시간 | - |
| **Phase 2** | Binance Futures API 연동 | 🔥🔥🔥 | 3시간 | Phase 1 |
| **Phase 3** | AI 리스크 관리 시스템 | 🔥🔥🔥 | 4시간 | Phase 2 |
| **Phase 4** | 로스 카메론 RSI 전략 | 🔥🔥 | 3시간 | Phase 3 |
| **Phase 5** | 고급 선물 거래 기능 | 🔥🔥 | 4시간 | Phase 4 |
| **Phase 6** | 백테스팅 및 최적화 | 🔥🔥 | 5시간 | Phase 5 |
| **Phase 7** | 웹 인터페이스 | 🔥 | 3시간 | Phase 6 |
| **Phase 8** | 텔레그램 알림 | 🔥 | 2시간 | Phase 7 |
| **Phase 9** | Vultr 서버 배포 | 🔥 | 4시간 | Phase 8 |
| **Phase 10** | 고급 자동화 및 모니터링 | 🔥 | 6시간 | Phase 9 |

**⏱️ 총 예상 시간: 36시간 (4-5일)**

---

## 🚀 Phase 1: 개발 환경 설정

### 🎯 목표
- Python 3.9+ 환경 구축
- Freqtrade 2024.12+ 설치
- 선물거래 전용 프로젝트 구조 생성

### 📋 구현 단계

#### 1.1 시스템 요구사항 확인
```bash
# Python 버전 확인 (3.9+ 필수)
python3 --version
# 출력 예시: Python 3.11.5

# 시스템 메모리 확인 (최소 4GB 권장)
free -h
# 출력 예시: Mem: 7.7Gi

# 선물 거래 API 연결 테스트
curl -I https://fapi.binance.com/fapi/v1/ping
# 출력 예시: HTTP/2 200
```

#### 1.2 프로젝트 초기화
```bash
# 새 프로젝트 디렉토리 생성
mkdir binance-futures-freqtrade
cd binance-futures-freqtrade

# Python 가상환경 생성
python3 -m venv .venv
source .venv/bin/activate

# 가상환경 활성화 확인
which python
# 출력: /path/to/binance-futures-freqtrade/.venv/bin/python
```

#### 1.3 Freqtrade 설치 및 검증
```bash
# Freqtrade 설치 (Futures 지원)
pip install freqtrade[complete]

# 설치 확인
freqtrade --version
# 출력 예시: freqtrade 2024.12

# FreqUI 설치
freqtrade install-ui

# 설치 확인
ls -la ~/.freqtrade/
# 출력: freqUI 디렉토리 확인
```

#### 1.4 프로젝트 구조 생성
```bash
# 선물거래 전용 디렉토리 구조 생성
mkdir -p user_data/{strategies,hyperopts,data,logs}
mkdir -p docs scripts tests monitoring deployment

# 구조 확인
tree -L 2
```

### ✅ Phase 1 검증 체크리스트

- [ ] Python 3.9+ 설치 및 확인
- [ ] 가상환경 생성 및 활성화
- [ ] Freqtrade 최신 버전 설치
- [ ] FreqUI 설치 완료
- [ ] 프로젝트 디렉토리 구조 생성
- [ ] Binance Futures API 연결 가능

### 🚨 Phase 1 문제 해결

**문제: Python 버전이 3.9 미만**
```bash
# 해결책: pyenv로 Python 최신 버전 설치
curl https://pyenv.run | bash
pyenv install 3.11.5
pyenv global 3.11.5
```

**문제: Freqtrade 설치 실패**
```bash
# 해결책: 시스템 의존성 설치
sudo apt-get update
sudo apt-get install python3-dev python3-pip build-essential
pip install --upgrade pip setuptools wheel
```

---

## 🔌 Phase 2: Binance Futures API 연동

### 🎯 목표
- Binance Testnet 계정 생성 및 API 키 설정
- 선물거래 전용 Freqtrade 설정
- 72개 Futures API 엔드포인트 연결 확인

### 📋 구현 단계

#### 2.1 Binance Testnet 계정 설정
```bash
# 1. 테스트넷 접속
# URL: https://testnet.binancefuture.com/

# 2. GitHub OAuth 로그인

# 3. 테스트 자금 충전 (무료 USDT)
# 웹사이트에서 "Get Test Funds" 클릭

# 4. API 키 생성
# API Management > Create API Key
# Futures Trading 권한 활성화
```

#### 2.2 선물거래 설정 파일 생성
```bash
# 설정 파일 생성
nano user_data/config_futures.json
```

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
    "key": "your_testnet_api_key",
    "secret": "your_testnet_api_secret",
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
  },
  "pairlists": [
    {
      "method": "StaticPairList",
      "pairs": ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
    }
  ]
}
```

#### 2.3 API 연결 테스트
```bash
# 설정 검증
freqtrade test-pairlist --config user_data/config_futures.json

# 계좌 정보 확인
freqtrade show-trades --config user_data/config_futures.json

# 선물 거래 모드 확인
freqtrade show-config --config user_data/config_futures.json | grep "trading_mode"
# 출력: "trading_mode": "futures"
```

#### 2.4 핵심 API 엔드포인트 테스트
```python
# scripts/test_api_endpoints.py
import ccxt
import json

def test_binance_futures_api():
    """Binance Futures API 연결 테스트"""
    
    with open('user_data/config_futures.json', 'r') as f:
        config = json.load(f)
    
    exchange = ccxt.binance({
        'apiKey': config['exchange']['key'],
        'secret': config['exchange']['secret'],
        'sandbox': True,
        'options': {'defaultType': 'future'}
    })
    
    # 핵심 엔드포인트 테스트
    tests = {
        'server_time': lambda: exchange.fetch_time(),
        'account_info': lambda: exchange.fetch_balance(),
        'positions': lambda: exchange.fetch_positions(),
        'tickers': lambda: exchange.fetch_ticker('BTCUSDT'),
        'funding_rate': lambda: exchange.fetch_funding_rate('BTCUSDT')
    }
    
    results = {}
    for test_name, test_func in tests.items():
        try:
            result = test_func()
            results[test_name] = "✅ SUCCESS"
            print(f"{test_name}: ✅ SUCCESS")
        except Exception as e:
            results[test_name] = f"❌ FAILED: {str(e)}"
            print(f"{test_name}: ❌ FAILED: {str(e)}")
    
    return results

if __name__ == "__main__":
    test_binance_futures_api()
```

### ✅ Phase 2 검증 체크리스트

- [ ] Binance Testnet 계정 생성
- [ ] API 키 생성 및 Futures Trading 권한 확인
- [ ] 테스트 USDT 충전 완료
- [ ] config_futures.json 설정 완료
- [ ] `trading_mode: futures` 설정 확인
- [ ] API 연결 테스트 성공
- [ ] 핵심 엔드포인트 응답 확인

---

## 🤖 Phase 3: AI 리스크 관리 시스템

### 🎯 목표
- 레버리지 고려 AI 포지션 계산 시스템 구현
- 동적 레버리지 조정 알고리즘 개발
- 선물거래 전용 리스크 매개변수 설정

### 📋 구현 단계

#### 3.1 AI 리스크 기본 전략 클래스 생성
```python
# user_data/strategies/FuturesAIRiskStrategy.py
import freqtrade.vendor.qtpylib.indicators as qtpylib
import numpy as np
import pandas as pd
from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter
import talib.abstract as ta

class FuturesAIRiskStrategy(IStrategy):
    """선물거래 전용 AI 리스크 관리 전략"""
    
    # 전략 메타데이터
    INTERFACE_VERSION = 3
    timeframe = '15m'
    can_short = True  # 숏 포지션 활성화
    
    # 선물거래 전용 매개변수
    minimal_roi = {"0": 0.05, "30": 0.03, "60": 0.01, "120": 0}
    stoploss = -0.05  # 5% 스탑로스
    
    # AI 리스크 매개변수
    risk_percentage = DecimalParameter(0.5, 2.0, default=1.0, space="buy")
    max_leverage = IntParameter(1, 10, default=5, space="buy")
    volatility_threshold = DecimalParameter(0.02, 0.08, default=0.04, space="buy")
    
    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """선물거래 특화 지표 생성"""
        
        # 기본 지표
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['ema_fast'] = ta.EMA(dataframe, timeperiod=12)
        dataframe['ema_slow'] = ta.EMA(dataframe, timeperiod=26)
        
        # 변동성 지표 (레버리지 계산용)
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=14)
        dataframe['volatility'] = dataframe['atr'] / dataframe['close']
        
        # 볼린저밴드
        bb = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2, nbdevdn=2)
        dataframe['bb_upper'] = bb['upperband']
        dataframe['bb_lower'] = bb['lowerband']
        dataframe['bb_percent'] = (dataframe['close'] - dataframe['bb_lower']) / (dataframe['bb_upper'] - dataframe['bb_lower'])
        
        return dataframe
    
    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """진입 신호 (롱/숏)"""
        
        # 롱 진입 조건
        dataframe.loc[
            (dataframe['rsi'] < 30) &
            (dataframe['close'] < dataframe['bb_lower']) &
            (dataframe['ema_fast'] > dataframe['ema_slow']),
            'enter_long'] = 1
        
        # 숏 진입 조건  
        dataframe.loc[
            (dataframe['rsi'] > 70) &
            (dataframe['close'] > dataframe['bb_upper']) &
            (dataframe['ema_fast'] < dataframe['ema_slow']),
            'enter_short'] = 1
            
        return dataframe
    
    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """청산 신호"""
        
        # 롱 청산
        dataframe.loc[
            (dataframe['rsi'] > 60) |
            (dataframe['close'] > dataframe['bb_upper']),
            'exit_long'] = 1
        
        # 숏 청산
        dataframe.loc[
            (dataframe['rsi'] < 40) |
            (dataframe['close'] < dataframe['bb_lower']),
            'exit_short'] = 1
            
        return dataframe
```

#### 3.2 AI 포지션 크기 계산 구현
```python
def custom_stake_amount(self, pair: str, current_time, current_rate: float, 
                       proposed_stake: float, min_stake: float, max_stake: float, 
                       entry_tag: str, side: str, **kwargs) -> float:
    """선물거래 전용 AI 포지션 크기 계산"""
    
    # 현재 잔고 가져오기
    balance = self.wallets.get_total_stake_amount()
    
    # 변동성 기반 리스크 조정
    dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
    current_volatility = dataframe['volatility'].iloc[-1]
    
    # 동적 레버리지 계산
    optimal_leverage = self.calculate_optimal_leverage(current_volatility)
    
    # 리스크 기반 포지션 크기 계산
    risk_amount = balance * (self.risk_percentage.value / 100)
    effective_stop_distance = abs(self.stoploss) * optimal_leverage
    
    if effective_stop_distance > 0:
        position_size = risk_amount / effective_stop_distance
    else:
        position_size = min_stake
    
    # 최소/최대 제한 적용
    position_size = max(min_stake, min(position_size, max_stake))
    
    self.logger.info(f"AI Position Calc - Pair: {pair}, Volatility: {current_volatility:.4f}, "
                    f"Leverage: {optimal_leverage}, Position: {position_size:.2f}")
    
    return position_size

def calculate_optimal_leverage(self, volatility: float) -> int:
    """변동성 기반 최적 레버리지 계산"""
    
    if volatility > 0.06:      # 초고변동성 (>6%)
        return min(2, self.max_leverage.value)
    elif volatility > 0.04:    # 고변동성 (4-6%)
        return min(3, self.max_leverage.value)
    elif volatility > 0.02:    # 중변동성 (2-4%)
        return min(5, self.max_leverage.value)
    else:                      # 저변동성 (<2%)
        return min(8, self.max_leverage.value)

def leverage(self, pair: str, current_time, current_rate: float, 
            proposed_leverage: int, max_leverage: int, entry_tag: str, 
            side: str, **kwargs) -> float:
    """Freqtrade 레버리지 콜백"""
    
    dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
    current_volatility = dataframe['volatility'].iloc[-1]
    
    return self.calculate_optimal_leverage(current_volatility)
```

#### 3.3 리스크 모니터링 시스템
```python
def custom_exit(self, pair: str, trade, current_time, current_rate: float,
               current_profit: float, **kwargs) -> str:
    """AI 기반 동적 청산 관리"""
    
    # 마진 비율 확인
    margin_ratio = self.get_margin_ratio(pair)
    if margin_ratio > 0.8:  # 80% 이상 마진 사용시
        return "margin_risk"
    
    # 레버리지 기반 손익 확인
    leverage = trade.leverage or 1
    effective_profit = current_profit * leverage
    
    # 고레버리지 포지션 보호
    if leverage >= 5 and current_profit < -0.02:  # 2% 손실
        return "high_leverage_protection"
    
    # 자금 조달 수수료 고려
    funding_cost = self.get_funding_cost(pair, trade)
    if funding_cost > abs(current_profit) * 0.5:  # 수수료가 손익의 50% 초과
        return "funding_cost_exit"
    
    return None

def get_margin_ratio(self, pair: str) -> float:
    """현재 마진 사용률 계산"""
    try:
        positions = self.exchange._api.futures_account()
        for position in positions['positions']:
            if position['symbol'] == pair.replace('/', ''):
                maintenance_margin = float(position['maintMargin'])
                margin_balance = float(position['marginBalance'])
                if margin_balance > 0:
                    return maintenance_margin / margin_balance
        return 0.0
    except Exception:
        return 0.0
```

### ✅ Phase 3 검증 체크리스트

- [ ] FuturesAIRiskStrategy 클래스 생성
- [ ] custom_stake_amount 메서드 구현
- [ ] 동적 레버리지 계산 로직 완성
- [ ] 변동성 기반 리스크 조정 구현
- [ ] 마진 비율 모니터링 기능 추가
- [ ] 백테스팅으로 리스크 계산 검증

### 🧪 Phase 3 테스트
```bash
# AI 리스크 전략 백테스팅
freqtrade backtesting \
  --config user_data/config_futures.json \
  --strategy FuturesAIRiskStrategy \
  --timerange 20241001-20241101 \
  --breakdown day
```

---

## 📈 Phase 4: 로스 카메론 RSI 전략

### 🎯 목표
- 로스 카메론의 RSI 반전 전략을 선물거래에 최적화
- 롱/숏 양방향 신호 생성 시스템 구현
- 자금 조달 수수료를 고려한 진입/청산 로직

### 📋 구현 단계

#### 4.1 로스 카메론 전략 기본 구조
```python
# user_data/strategies/RossCameronFuturesStrategy.py
from freqtrade.strategy import IStrategy
import talib.abstract as ta
import pandas as pd

class RossCameronFuturesStrategy(FuturesAIRiskStrategy):
    """로스 카메론 RSI 전략 - 선물거래 최적화"""
    
    # 전략 메타데이터
    INTERFACE_VERSION = 3
    timeframe = '15m'
    can_short = True
    
    # 로스 카메론 매개변수
    rsi_overbought = IntParameter(65, 80, default=70, space="sell")
    rsi_oversold = IntParameter(20, 35, default=30, space="buy")
    bb_deviation = DecimalParameter(1.8, 2.5, default=2.0, space="buy")
    
    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """로스 카메론 지표 + 선물거래 특화"""
        
        # 부모 클래스 지표 상속
        dataframe = super().populate_indicators(dataframe, metadata)
        
        # 로스 카메론 핵심 지표
        dataframe['rsi_14'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['rsi_7'] = ta.RSI(dataframe, timeperiod=7)
        
        # 다중 시간대 RSI
        dataframe['rsi_slow'] = ta.RSI(dataframe, timeperiod=21)
        
        # 볼린저밴드 (동적 편차)
        bb = ta.BBANDS(dataframe, timeperiod=20, nbdevup=self.bb_deviation.value, 
                      nbdevdn=self.bb_deviation.value)
        dataframe['bb_upper'] = bb['upperband']
        dataframe['bb_middle'] = bb['middleband']
        dataframe['bb_lower'] = bb['lowerband']
        dataframe['bb_width'] = (dataframe['bb_upper'] - dataframe['bb_lower']) / dataframe['bb_middle']
        
        # 가격 위치 (볼린저밴드 내)
        dataframe['bb_percent'] = (dataframe['close'] - dataframe['bb_lower']) / \
                                 (dataframe['bb_upper'] - dataframe['bb_lower'])
        
        # 선물거래 특화 지표
        dataframe['funding_rate'] = self.get_funding_rate_indicator(metadata['pair'])
        dataframe['long_short_ratio'] = self.get_long_short_ratio(metadata['pair'])
        
        # 거래량 확인
        dataframe['volume_sma'] = ta.SMA(dataframe['volume'], timeperiod=20)
        dataframe['volume_ratio'] = dataframe['volume'] / dataframe['volume_sma']
        
        return dataframe
    
    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """로스 카메론 진입 신호 (선물 최적화)"""
        
        # 롱 진입 - RSI 과매도 + 볼밴 하단 + 자금조달료 고려
        long_conditions = [
            # 핵심 RSI 조건
            (dataframe['rsi_14'] < self.rsi_oversold.value),
            (dataframe['rsi_7'] < self.rsi_oversold.value + 5),
            
            # 볼린저밴드 조건
            (dataframe['close'] <= dataframe['bb_lower']),
            (dataframe['bb_percent'] < 0.2),  # 하위 20% 구간
            
            # 거래량 확인
            (dataframe['volume_ratio'] > 1.2),  # 평균 대비 20% 이상
            
            # 선물거래 특화 조건
            (dataframe['funding_rate'] < 0),  # 음수 자금조달료 (롱 유리)
            
            # 추가 필터
            (dataframe['bb_width'] > 0.02),  # 충분한 변동성
        ]
        
        dataframe.loc[
            self.combine_conditions(long_conditions),
            'enter_long'
        ] = 1
        
        # 숏 진입 - RSI 과매수 + 볼밴 상단 + 자금조달료 고려
        short_conditions = [
            # 핵심 RSI 조건
            (dataframe['rsi_14'] > self.rsi_overbought.value),
            (dataframe['rsi_7'] > self.rsi_overbought.value - 5),
            
            # 볼린저밴드 조건
            (dataframe['close'] >= dataframe['bb_upper']),
            (dataframe['bb_percent'] > 0.8),  # 상위 80% 구간
            
            # 거래량 확인
            (dataframe['volume_ratio'] > 1.2),
            
            # 선물거래 특화 조건
            (dataframe['funding_rate'] > 0.001),  # 양수 자금조달료 (숏 유리)
            
            # 추가 필터
            (dataframe['bb_width'] > 0.02),
        ]
        
        dataframe.loc[
            self.combine_conditions(short_conditions),
            'enter_short'
        ] = 1
        
        return dataframe
    
    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """로스 카메론 청산 신호"""
        
        # 롱 청산 - RSI 회복 또는 볼밴 중간선 도달
        dataframe.loc[
            (
                (dataframe['rsi_14'] > 50) |
                (dataframe['close'] > dataframe['bb_middle']) |
                (dataframe['bb_percent'] > 0.6)
            ),
            'exit_long'
        ] = 1
        
        # 숏 청산 - RSI 하락 또는 볼밴 중간선 도달
        dataframe.loc[
            (
                (dataframe['rsi_14'] < 50) |
                (dataframe['close'] < dataframe['bb_middle']) |
                (dataframe['bb_percent'] < 0.4)
            ),
            'exit_short'
        ] = 1
        
        return dataframe
    
    def combine_conditions(self, conditions: list) -> pd.Series:
        """조건들을 AND로 결합"""
        result = conditions[0]
        for condition in conditions[1:]:
            result = result & condition
        return result
```

#### 4.2 선물거래 특화 헬퍼 메서드
```python
def get_funding_rate_indicator(self, pair: str) -> pd.Series:
    """자금 조달 수수료 지표 생성"""
    try:
        # 실제 API에서 자금조달료 가져오기
        funding_rate = self.exchange.fetch_funding_rate(pair)
        current_rate = funding_rate['fundingRate']
        
        # 시리즈로 변환 (임시 구현)
        return pd.Series([current_rate] * 1000)  # 실제로는 historical 데이터 필요
        
    except Exception:
        # 기본값 반환
        return pd.Series([0.0] * 1000)

def get_long_short_ratio(self, pair: str) -> pd.Series:
    """롱/숏 비율 지표"""
    try:
        # Binance Futures API에서 롱/숏 비율 가져오기
        # 실제 구현에서는 historical 데이터 필요
        return pd.Series([1.0] * 1000)  # 중립 비율
        
    except Exception:
        return pd.Series([1.0] * 1000)

def custom_entry_price(self, pair: str, current_time, proposed_rate: float, 
                      entry_tag: str, side: str, **kwargs) -> float:
    """로스 카메론 스타일 진입가 최적화"""
    
    dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
    
    if side == "long":
        # 볼린저밴드 하단 근처에서 진입
        bb_lower = dataframe['bb_lower'].iloc[-1]
        return min(proposed_rate, bb_lower * 1.001)  # 0.1% 위
        
    elif side == "short":
        # 볼린저밴드 상단 근처에서 진입
        bb_upper = dataframe['bb_upper'].iloc[-1]
        return max(proposed_rate, bb_upper * 0.999)  # 0.1% 아래
    
    return proposed_rate

def custom_exit_price(self, pair: str, trade, current_time, proposed_rate: float, 
                     current_profit: float, **kwargs) -> float:
    """수익 최적화 청산가 계산"""
    
    dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
    bb_middle = dataframe['bb_middle'].iloc[-1]
    
    # 볼린저밴드 중간선에서 청산 목표
    if trade.is_short:
        return min(proposed_rate, bb_middle)
    else:
        return max(proposed_rate, bb_middle)
```

### ✅ Phase 4 검증 체크리스트

- [ ] 로스 카메론 RSI 전략 클래스 완성
- [ ] 롱/숏 양방향 진입 조건 구현
- [ ] 볼린저밴드 + RSI 조합 로직 완성
- [ ] 자금 조달 수수료 고려 조건 추가
- [ ] 거래량 필터링 구현
- [ ] 백테스팅으로 전략 성능 검증

### 🧪 Phase 4 테스트
```bash
# 로스 카메론 전략 백테스팅
freqtrade backtesting \
  --config user_data/config_futures.json \
  --strategy RossCameronFuturesStrategy \
  --timerange 20241001-20241201 \
  --breakdown day week
```

---

## 🔧 Phase 5: 고급 선물 거래 기능

### 🎯 목표
- 자금 조달 수수료 수익 창출 시스템
- 포지션 모드 관리 (One-way/Hedge)
- ADL 및 강제 청산 방지 시스템

### 📋 구현 단계

#### 5.1 자금 조달 수수료 활용 시스템
```python
# user_data/strategies/modules/funding_rate_manager.py
import requests
import time
from datetime import datetime, timedelta

class FundingRateManager:
    """자금 조달 수수료 관리 시스템"""
    
    def __init__(self, exchange):
        self.exchange = exchange
        self.funding_threshold = 0.01  # 1% 이상 수수료
        
    def get_current_funding_rate(self, pair: str) -> float:
        """현재 자금 조달 수수료 조회"""
        try:
            funding_info = self.exchange.fetch_funding_rate(pair)
            return funding_info['fundingRate']
        except Exception as e:
            print(f"Funding rate fetch error: {e}")
            return 0.0
    
    def get_next_funding_time(self, pair: str) -> datetime:
        """다음 자금 조달 시간 계산"""
        try:
            funding_info = self.exchange.fetch_funding_rate(pair)
            return datetime.fromtimestamp(funding_info['fundingTimestamp'] / 1000)
        except Exception:
            # 기본값: 8시간마다 (Binance 기준)
            now = datetime.now()
            next_funding = now.replace(minute=0, second=0, microsecond=0)
            while next_funding.hour not in [0, 8, 16]:
                next_funding += timedelta(hours=1)
            if next_funding <= now:
                next_funding += timedelta(hours=8)
            return next_funding
    
    def analyze_funding_opportunity(self, pair: str) -> dict:
        """자금 조달료 수익 기회 분석"""
        
        current_rate = self.get_current_funding_rate(pair)
        next_time = self.get_next_funding_time(pair)
        time_to_funding = (next_time - datetime.now()).total_seconds() / 3600
        
        analysis = {
            'pair': pair,
            'funding_rate': current_rate,
            'next_funding_time': next_time,
            'hours_to_funding': time_to_funding,
            'recommendation': 'neutral'
        }
        
        # 높은 양의 수수료 = 숏 포지션 유리
        if current_rate > self.funding_threshold:
            analysis['recommendation'] = 'short_favorable'
            analysis['expected_income'] = current_rate  # 8시간당 수익률
            
        # 높은 음의 수수료 = 롱 포지션 유리
        elif current_rate < -self.funding_threshold:
            analysis['recommendation'] = 'long_favorable' 
            analysis['expected_income'] = abs(current_rate)
            
        return analysis
    
    def should_hold_for_funding(self, pair: str, side: str) -> bool:
        """자금 조달료 수익을 위해 포지션 유지 여부 판단"""
        
        analysis = self.analyze_funding_opportunity(pair)
        
        # 수익성 있는 자금 조달료이고 시간이 2시간 이내
        if (analysis['hours_to_funding'] < 2 and 
            abs(analysis['funding_rate']) > 0.005):  # 0.5% 이상
            
            if side == 'long' and analysis['recommendation'] == 'long_favorable':
                return True
            elif side == 'short' and analysis['recommendation'] == 'short_favorable':
                return True
                
        return False
```

#### 5.2 포지션 모드 관리
```python
# user_data/strategies/modules/position_manager.py
class PositionManager:
    """포지션 모드 및 마진 관리"""
    
    def __init__(self, exchange):
        self.exchange = exchange
        
    def set_position_mode(self, hedge_mode: bool = False):
        """포지션 모드 설정 (One-way/Hedge)"""
        try:
            # Binance Futures API
            if hedge_mode:
                self.exchange._api.futures_change_position_mode(dualSidePosition=True)
                print("✅ Hedge mode activated (Long/Short 동시 가능)")
            else:
                self.exchange._api.futures_change_position_mode(dualSidePosition=False)
                print("✅ One-way mode activated (기본 모드)")
                
        except Exception as e:
            print(f"Position mode change error: {e}")
    
    def set_margin_mode(self, pair: str, margin_type: str = "ISOLATED"):
        """마진 모드 설정"""
        try:
            symbol = pair.replace('/', '')
            self.exchange._api.futures_change_margin_type(
                symbol=symbol, 
                marginType=margin_type
            )
            print(f"✅ {pair} margin mode set to {margin_type}")
            
        except Exception as e:
            if "No need to change margin type" in str(e):
                print(f"ℹ️  {pair} already in {margin_type} mode")
            else:
                print(f"Margin mode change error: {e}")
    
    def adjust_leverage(self, pair: str, leverage: int):
        """레버리지 조정"""
        try:
            symbol = pair.replace('/', '')
            result = self.exchange._api.futures_change_leverage(
                symbol=symbol,
                leverage=leverage
            )
            print(f"✅ {pair} leverage set to {leverage}x")
            return result
            
        except Exception as e:
            print(f"Leverage adjustment error: {e}")
            return None
    
    def get_position_risk(self, pair: str = None) -> dict:
        """포지션 리스크 정보 조회"""
        try:
            positions = self.exchange._api.futures_position_information()
            
            if pair:
                symbol = pair.replace('/', '')
                for pos in positions:
                    if pos['symbol'] == symbol:
                        return self._format_position_risk(pos)
            else:
                # 모든 활성 포지션 리스크
                active_positions = []
                for pos in positions:
                    if float(pos['positionAmt']) != 0:
                        active_positions.append(self._format_position_risk(pos))
                return active_positions
                
        except Exception as e:
            print(f"Position risk fetch error: {e}")
            return {}
    
    def _format_position_risk(self, position: dict) -> dict:
        """포지션 리스크 정보 포맷팅"""
        
        position_amt = float(position['positionAmt'])
        mark_price = float(position['markPrice'])
        liquidation_price = float(position['liquidationPrice'])
        margin_ratio = float(position['marginRatio'])
        
        return {
            'symbol': position['symbol'],
            'side': 'LONG' if position_amt > 0 else 'SHORT',
            'size': abs(position_amt),
            'entry_price': float(position['entryPrice']),
            'mark_price': mark_price,
            'liquidation_price': liquidation_price,
            'unrealized_pnl': float(position['unRealizedProfit']),
            'margin_ratio': margin_ratio,
            'liquidation_distance': abs(mark_price - liquidation_price) / mark_price if liquidation_price > 0 else 1.0,
            'leverage': int(1 / margin_ratio) if margin_ratio > 0 else 1
        }
```

#### 5.3 리스크 모니터링 및 알림 시스템
```python
# user_data/strategies/modules/risk_monitor.py
import time
import threading
from datetime import datetime

class RiskMonitor:
    """실시간 리스크 모니터링"""
    
    def __init__(self, position_manager, telegram_bot=None):
        self.position_manager = position_manager
        self.telegram_bot = telegram_bot
        self.monitoring = False
        
        # 위험 임계값
        self.liquidation_warning_threshold = 0.15  # 15% 이내
        self.margin_ratio_warning = 0.8  # 80% 이상
        
    def start_monitoring(self, interval: int = 30):
        """리스크 모니터링 시작"""
        self.monitoring = True
        thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        thread.daemon = True
        thread.start()
        print("🔍 Risk monitoring started")
    
    def stop_monitoring(self):
        """리스크 모니터링 중지"""
        self.monitoring = False
        print("⏹️  Risk monitoring stopped")
    
    def _monitor_loop(self, interval: int):
        """모니터링 루프"""
        while self.monitoring:
            try:
                self._check_all_positions()
                time.sleep(interval)
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(60)  # 에러 시 1분 대기
    
    def _check_all_positions(self):
        """모든 포지션 위험도 확인"""
        positions = self.position_manager.get_position_risk()
        
        if isinstance(positions, list):
            for position in positions:
                self._check_position_risk(position)
    
    def _check_position_risk(self, position: dict):
        """개별 포지션 위험도 확인"""
        symbol = position['symbol']
        liquidation_distance = position['liquidation_distance']
        margin_ratio = position['margin_ratio']
        
        # 강제 청산 경고
        if liquidation_distance < self.liquidation_warning_threshold:
            warning_msg = (
                f"🚨 LIQUIDATION WARNING\n"
                f"Symbol: {symbol}\n"
                f"Distance to liquidation: {liquidation_distance:.2%}\n"
                f"Current margin ratio: {margin_ratio:.2%}\n"
                f"Action: Consider reducing position or adding margin"
            )
            self._send_alert(warning_msg)
        
        # 마진 비율 경고
        elif margin_ratio > self.margin_ratio_warning:
            warning_msg = (
                f"⚠️ HIGH MARGIN USAGE\n"
                f"Symbol: {symbol}\n"
                f"Margin ratio: {margin_ratio:.2%}\n"
                f"Recommendation: Monitor closely"
            )
            self._send_alert(warning_msg)
    
    def _send_alert(self, message: str):
        """알림 발송"""
        print(f"ALERT: {message}")
        
        if self.telegram_bot:
            try:
                self.telegram_bot.send_message(message)
            except Exception as e:
                print(f"Telegram alert failed: {e}")
```

### ✅ Phase 5 검증 체크리스트

- [ ] FundingRateManager 클래스 구현
- [ ] 자금 조달료 분석 로직 완성
- [ ] PositionManager로 포지션 모드 관리
- [ ] 레버리지 동적 조정 기능
- [ ] RiskMonitor로 실시간 위험 감지
- [ ] 강제 청산 경고 시스템 구현

---

## 📊 Phase 6: 백테스팅 및 최적화

### 🎯 목표
- 선물거래 데이터 다운로드 및 백테스팅 실행
- 하이퍼파라미터 최적화
- 전략 성능 분석 및 리포트 생성

### 📋 구현 단계

#### 6.1 선물거래 데이터 다운로드
```bash
# 스크립트 생성: scripts/download_futures_data.sh
#!/bin/bash

echo "🔄 Downloading Binance Futures data..."

# 주요 USDT Perpetual 페어
PAIRS="BTCUSDT ETHUSDT ADAUSDT SOLUSDT BNBUSDT AVAXUSDT MATICUSDT DOTUSDT LINKUSDT LTCUSDT"

# 다중 시간대 데이터
TIMEFRAMES="15m 1h 4h 1d"

# 90일 데이터 다운로드
freqtrade download-data \
  --exchange binance \
  --trading-mode futures \
  --timeframes $TIMEFRAMES \
  --pairs $PAIRS \
  --days 90 \
  --config user_data/config_futures.json \
  --data-format-ohlcv json

echo "✅ Data download completed"

# 데이터 확인
freqtrade list-data \
  --config user_data/config_futures.json \
  --trading-mode futures
```

#### 6.2 백테스팅 실행 스크립트
```python
# scripts/run_backtests.py
import subprocess
import json
import os
from datetime import datetime, timedelta

class FuturesBacktester:
    """선물거래 백테스팅 자동화"""
    
    def __init__(self):
        self.config_path = "user_data/config_futures.json"
        self.results_dir = "user_data/backtest_results"
        os.makedirs(self.results_dir, exist_ok=True)
    
    def run_strategy_backtest(self, strategy_name: str, timerange: str = None):
        """개별 전략 백테스팅"""
        
        if not timerange:
            # 기본: 최근 60일
            end_date = datetime.now()
            start_date = end_date - timedelta(days=60)
            timerange = f"{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}"
        
        cmd = [
            "freqtrade", "backtesting",
            "--config", self.config_path,
            "--strategy", strategy_name,
            "--trading-mode", "futures",
            "--timerange", timerange,
            "--breakdown", "day",
            "--export", "trades",
            "--export-filename", f"{self.results_dir}/{strategy_name}_{timerange}.json"
        ]
        
        print(f"🔄 Running backtest for {strategy_name}...")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            
            if result.returncode == 0:
                print(f"✅ {strategy_name} backtest completed")
                self._parse_backtest_results(strategy_name, result.stdout)
                return True
            else:
                print(f"❌ {strategy_name} backtest failed:")
                print(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⏱️  {strategy_name} backtest timed out")
            return False
    
    def run_all_strategies(self):
        """모든 전략 백테스팅"""
        strategies = [
            "FuturesAIRiskStrategy",
            "RossCameronFuturesStrategy"
        ]
        
        results = {}
        for strategy in strategies:
            results[strategy] = self.run_strategy_backtest(strategy)
        
        return results
    
    def _parse_backtest_results(self, strategy_name: str, output: str):
        """백테스팅 결과 파싱"""
        lines = output.split('\n')
        results = {}
        
        # 핵심 지표 추출
        for line in lines:
            if "Total Profit" in line:
                results['total_profit'] = line.split(':')[-1].strip()
            elif "Total trade count" in line:
                results['total_trades'] = line.split(':')[-1].strip()
            elif "Win %" in line:
                results['win_rate'] = line.split(':')[-1].strip()
            elif "Max Drawdown" in line:
                results['max_drawdown'] = line.split(':')[-1].strip()
            elif "Sharpe Ratio" in line:
                results['sharpe_ratio'] = line.split(':')[-1].strip()
        
        # 결과 저장
        result_file = f"{self.results_dir}/{strategy_name}_summary.json"
        with open(result_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"📊 {strategy_name} Results:")
        for key, value in results.items():
            print(f"  {key}: {value}")

if __name__ == "__main__":
    backtester = FuturesBacktester()
    backtester.run_all_strategies()
```

#### 6.3 하이퍼파라미터 최적화
```bash
# scripts/run_hyperopt.sh
#!/bin/bash

echo "🔧 Starting hyperparameter optimization..."

STRATEGY="RossCameronFuturesStrategy"
TIMERANGE="20241001-20241201"

# 선물거래 특화 하이퍼옵트
freqtrade hyperopt \
  --config user_data/config_futures.json \
  --strategy $STRATEGY \
  --hyperopt-loss SortinoHyperOptLoss \
  --spaces buy sell roi stoploss \
  --epochs 200 \
  --trading-mode futures \
  --timerange $TIMERANGE \
  --min-trades 50 \
  --print-all

echo "✅ Hyperopt completed"

# 최적 파라미터 적용
freqtrade hyperopt-show \
  --config user_data/config_futures.json \
  --strategy $STRATEGY \
  --print-json > user_data/hyperopt_results/${STRATEGY}_best_params.json
```

#### 6.4 성과 분석 도구
```python
# scripts/analyze_performance.py
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

class PerformanceAnalyzer:
    """백테스팅 성과 분석"""
    
    def __init__(self, results_dir: str = "user_data/backtest_results"):
        self.results_dir = Path(results_dir)
        
    def load_trade_data(self, strategy_name: str) -> pd.DataFrame:
        """거래 데이터 로드"""
        
        # 가장 최근 거래 파일 찾기
        trade_files = list(self.results_dir.glob(f"{strategy_name}_*-trades.json"))
        if not trade_files:
            print(f"No trade data found for {strategy_name}")
            return pd.DataFrame()
        
        latest_file = sorted(trade_files)[-1]
        
        with open(latest_file, 'r') as f:
            data = json.load(f)
        
        return pd.DataFrame(data)
    
    def analyze_futures_performance(self, strategy_name: str) -> dict:
        """선물거래 성과 상세 분석"""
        
        trades_df = self.load_trade_data(strategy_name)
        
        if trades_df.empty:
            return {}
        
        # 기본 통계
        total_trades = len(trades_df)
        long_trades = len(trades_df[trades_df['is_short'] == False])
        short_trades = len(trades_df[trades_df['is_short'] == True])
        
        # 수익성 분석
        profitable_trades = len(trades_df[trades_df['profit_abs'] > 0])
        win_rate = profitable_trades / total_trades if total_trades > 0 else 0
        
        # 레버리지 분석
        avg_leverage = trades_df['leverage'].mean() if 'leverage' in trades_df.columns else 1
        max_leverage = trades_df['leverage'].max() if 'leverage' in trades_df.columns else 1
        
        # 수익 분석
        total_profit = trades_df['profit_abs'].sum()
        avg_profit_per_trade = trades_df['profit_abs'].mean()
        best_trade = trades_df['profit_abs'].max()
        worst_trade = trades_df['profit_abs'].min()
        
        # 기간 분석
        trades_df['open_date'] = pd.to_datetime(trades_df['open_date'])
        trades_df['close_date'] = pd.to_datetime(trades_df['close_date'])
        trades_df['duration_hours'] = (trades_df['close_date'] - trades_df['open_date']).dt.total_seconds() / 3600
        avg_duration = trades_df['duration_hours'].mean()
        
        # 자금 조달료 분석 (추정)
        funding_fees = 0
        if 'funding_fees' in trades_df.columns:
            funding_fees = trades_df['funding_fees'].sum()
        
        return {
            'strategy': strategy_name,
            'total_trades': total_trades,
            'long_trades': long_trades,
            'short_trades': short_trades,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'avg_profit_per_trade': avg_profit_per_trade,
            'best_trade': best_trade,
            'worst_trade': worst_trade,
            'avg_leverage': avg_leverage,
            'max_leverage': max_leverage,
            'avg_duration_hours': avg_duration,
            'funding_fees': funding_fees,
            'net_profit': total_profit - abs(funding_fees)
        }
    
    def create_performance_report(self, strategy_name: str):
        """성과 리포트 생성"""
        
        analysis = self.analyze_futures_performance(strategy_name)
        
        if not analysis:
            print("No data to analyze")
            return
        
        # 텍스트 리포트
        report = f"""
🚀 {strategy_name} Performance Report
{'='*50}

📊 Trade Statistics:
  Total Trades: {analysis['total_trades']}
  Long Trades: {analysis['long_trades']} ({analysis['long_trades']/analysis['total_trades']:.1%})
  Short Trades: {analysis['short_trades']} ({analysis['short_trades']/analysis['total_trades']:.1%})
  Win Rate: {analysis['win_rate']:.2%}

💰 Profitability:
  Total Profit: ${analysis['total_profit']:.2f}
  Avg Profit/Trade: ${analysis['avg_profit_per_trade']:.2f}
  Best Trade: ${analysis['best_trade']:.2f}
  Worst Trade: ${analysis['worst_trade']:.2f}

⚖️ Leverage Analysis:
  Average Leverage: {analysis['avg_leverage']:.1f}x
  Maximum Leverage: {analysis['max_leverage']:.1f}x

⏱️ Duration:
  Average Trade Duration: {analysis['avg_duration_hours']:.1f} hours

💸 Futures Specific:
  Estimated Funding Fees: ${analysis['funding_fees']:.2f}
  Net Profit (after fees): ${analysis['net_profit']:.2f}
        """
        
        print(report)
        
        # 리포트 파일 저장
        report_file = self.results_dir / f"{strategy_name}_report.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"📄 Report saved to {report_file}")

if __name__ == "__main__":
    analyzer = PerformanceAnalyzer()
    
    strategies = ["FuturesAIRiskStrategy", "RossCameronFuturesStrategy"]
    for strategy in strategies:
        analyzer.create_performance_report(strategy)
```

### ✅ Phase 6 검증 체크리스트

- [ ] 선물거래 데이터 다운로드 완료
- [ ] 전략별 백테스팅 실행 성공
- [ ] 하이퍼파라미터 최적화 수행
- [ ] 성과 분석 리포트 생성
- [ ] 레버리지별 수익률 분석
- [ ] 자금 조달료 영향 분석

---

## 🎯 다음 Phase 미리보기

### Phase 7-10 요약

| Phase | 핵심 내용 | 예상 시간 |
|-------|-----------|----------|
| **Phase 7** | FreqUI 웹 인터페이스 + 선물 특화 대시보드 | 3시간 |
| **Phase 8** | 텔레그램 봇 + 선물거래 전용 알림 | 2시간 |
| **Phase 9** | Vultr 서버 배포 + 서울 리전 최적화 | 4시간 |
| **Phase 10** | 고급 모니터링 + 자동 백업 시스템 | 6시간 |

---

## ✅ 에이전틱 코딩 원칙 준수

### 🔄 매 Phase 후 체크사항

1. **✅ 기능 검증**: 구현한 기능이 정상 작동하는가?
2. **🧪 테스트 실행**: 백테스팅/유닛테스트 통과하는가?
3. **📝 문서 업데이트**: 변경사항이 문서화되었는가?
4. **🚀 점진적 배포**: 테스트넷에서 검증 완료했는가?
5. **🔄 다음 Phase 준비**: 의존성과 요구사항 확인했는가?

### 🎯 성공 기준

- **각 Phase별 95% 이상 검증 체크리스트 완료**
- **테스트넷에서 24시간 이상 안정적 작동**
- **백테스팅 결과 양수 수익률 달성**
- **실시간 모니터링 시스템 정상 작동**

---

<div align="center">

**🛠️ 지금 Phase 1부터 시작하여 체계적으로 구현해보세요! 🛠️**

[![Start Phase 1](https://img.shields.io/badge/Start%20Phase%201-🚀%20환경%20설정-success?style=for-the-badge&logo=python)](../scripts/phase1_setup.sh)

</div>