# 🔌 Binance Futures API 완전 활용 가이드

[![Binance Futures API](https://img.shields.io/badge/Binance-Futures%20API-yellow.svg)](https://binance-docs.github.io/apidocs/futures/en/)
[![72 Endpoints](https://img.shields.io/badge/Endpoints-72%20APIs-green.svg)](https://github.com/your-repo)
[![Python Examples](https://img.shields.io/badge/Examples-Python%20%2B%20JavaScript-blue.svg)](https://github.com/your-repo)

> **72개 Binance USDT Perpetual Futures API 완전 정복**  
> 선물거래 특화 기능 × 실무 예제 × 에러 처리 × 베스트 프랙티스

---

## 🎯 API 개요

### 📊 전체 API 구조 (72개 엔드포인트)

| 카테고리 | 엔드포인트 수 | 주요 기능 |
|----------|-------------|----------|
| **General Information** | 2개 | 기본 정보, 변경 로그 |
| **Market Data Endpoints** | 25개 | 시장 데이터, 가격 정보 |
| **Account/Trade Endpoints** | 24개 | 거래 실행, 계좌 관리 |
| **WebSocket Market Streams** | 14개 | 실시간 시장 데이터 |
| **User Data Streams** | 7개 | 실시간 계좌 이벤트 |

### 🔑 인증 및 기본 설정

```python
import ccxt
import hmac
import hashlib
import time
import requests

# Binance Futures API 기본 설정
class BinanceFuturesAPI:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        
        if testnet:
            self.base_url = "https://testnet.binancefuture.com"
        else:
            self.base_url = "https://fapi.binance.com"
        
        # CCXT 설정
        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'sandbox': testnet,
            'options': {'defaultType': 'future'},
            'urls': {
                'api': {
                    'public': self.base_url,
                    'private': self.base_url
                }
            }
        })
    
    def generate_signature(self, query_string: str) -> str:
        """HMAC SHA256 서명 생성"""
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def get_headers(self) -> dict:
        """API 헤더 생성"""
        return {
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/json'
        }
```

---

## 📋 Category 1: General Information (2개)

### 🔍 1.1 General Info

**용도**: API 버전, 제한사항, 규칙 확인

```python
def get_general_info(self):
    """일반 정보 조회"""
    
    # 방법 1: Direct API Call
    endpoint = f"{self.base_url}/fapi/v1/exchangeInfo"
    response = requests.get(endpoint)
    
    if response.status_code == 200:
        data = response.json()
        return {
            'timezone': data['timezone'],
            'server_time': data['serverTime'],
            'rate_limits': data['rateLimits'],
            'symbols_count': len(data['symbols']),
            'filters': data['symbols'][0]['filters']  # 첫 번째 심볼의 필터 예시
        }
    
    # 방법 2: CCXT 사용
    exchange_info = self.exchange.load_markets()
    return exchange_info

# 사용 예시
api = BinanceFuturesAPI(api_key, api_secret, testnet=True)
info = api.get_general_info()
print(f"지원 심볼 수: {info['symbols_count']}")
```

### 📅 1.2 Change Log

**용도**: API 변경 사항 추적

```python
def track_api_changes(self):
    """API 변경사항 모니터링"""
    
    # 실제로는 문서 페이지를 파싱하거나 별도 알림 시스템 구축
    change_log_url = "https://developers.binance.com/docs/derivatives/usds-margined-futures/change-log"
    
    # 버전 확인 로직
    current_version = self.exchange.version
    print(f"현재 API 버전: {current_version}")
    
    return {
        'current_version': current_version,
        'last_check': time.time(),
        'change_log_url': change_log_url
    }
```

---

## 📊 Category 2: Market Data Endpoints (25개)

### ⚡ 2.1 핵심 시장 데이터 (우선순위 높음)

#### 🔍 Exchange Information
```python
def get_exchange_info(self, symbol: str = None):
    """거래소 정보 및 심볼 상세"""
    
    endpoint = f"{self.base_url}/fapi/v1/exchangeInfo"
    response = requests.get(endpoint)
    data = response.json()
    
    if symbol:
        # 특정 심볼 정보
        for s in data['symbols']:
            if s['symbol'] == symbol:
                return {
                    'symbol': s['symbol'],
                    'status': s['status'],
                    'base_asset': s['baseAsset'],
                    'quote_asset': s['quoteAsset'],
                    'price_precision': s['pricePrecision'],
                    'quantity_precision': s['quantityPrecision'],
                    'filters': s['filters']
                }
    
    return data

# 실전 사용
info = api.get_exchange_info('BTCUSDT')
print(f"BTC 가격 정밀도: {info['price_precision']}")
```

#### 📈 Kline/Candlestick Data
```python
def get_klines(self, symbol: str, interval: str, limit: int = 500):
    """캔들스틱 데이터 조회"""
    
    # 방법 1: REST API
    endpoint = f"{self.base_url}/fapi/v1/klines"
    params = {
        'symbol': symbol,
        'interval': interval,  # 1m, 5m, 15m, 1h, 4h, 1d
        'limit': limit
    }
    
    response = requests.get(endpoint, params=params)
    klines = response.json()
    
    # 방법 2: CCXT (더 편리)
    ohlcv = self.exchange.fetch_ohlcv(symbol, interval, limit=limit)
    
    # 데이터 포맷팅
    formatted_data = []
    for kline in ohlcv:
        formatted_data.append({
            'timestamp': kline[0],
            'open': kline[1],
            'high': kline[2],
            'low': kline[3],
            'close': kline[4],
            'volume': kline[5]
        })
    
    return formatted_data

# 실전 활용
btc_1h = api.get_klines('BTCUSDT', '1h', 100)
current_price = btc_1h[-1]['close']
print(f"BTC 현재가: ${current_price:,.2f}")
```

#### 💰 24hr Ticker Price Change Statistics
```python
def get_24hr_ticker(self, symbol: str = None):
    """24시간 가격 변동 통계"""
    
    endpoint = f"{self.base_url}/fapi/v1/ticker/24hr"
    params = {}
    
    if symbol:
        params['symbol'] = symbol
    
    response = requests.get(endpoint, params=params)
    data = response.json()
    
    if symbol:
        return {
            'symbol': data['symbol'],
            'price_change': float(data['priceChange']),
            'price_change_percent': float(data['priceChangePercent']),
            'weighted_avg_price': float(data['weightedAvgPrice']),
            'last_price': float(data['lastPrice']),
            'volume': float(data['volume']),
            'quote_volume': float(data['quoteVolume']),
            'open_interest': float(data.get('openInterest', 0))
        }
    
    # 전체 시장 데이터
    return [
        {
            'symbol': item['symbol'],
            'price_change_percent': float(item['priceChangePercent']),
            'volume': float(item['volume'])
        }
        for item in data
    ]

# Top 변동률 심볼 찾기
all_tickers = api.get_24hr_ticker()
top_gainers = sorted(all_tickers, key=lambda x: x['price_change_percent'], reverse=True)[:5]
print("Top 5 상승 종목:")
for ticker in top_gainers:
    print(f"{ticker['symbol']}: +{ticker['price_change_percent']:.2f}%")
```

### 🎯 2.2 선물거래 특화 데이터

#### 💸 Mark Price & Funding Rate
```python
def get_mark_price_and_funding(self, symbol: str = None):
    """마크 가격 및 자금조달료 조회"""
    
    endpoint = f"{self.base_url}/fapi/v1/premiumIndex"
    params = {}
    
    if symbol:
        params['symbol'] = symbol
    
    response = requests.get(endpoint, params=params)
    data = response.json()
    
    if symbol:
        return {
            'symbol': data['symbol'],
            'mark_price': float(data['markPrice']),
            'index_price': float(data['indexPrice']),
            'funding_rate': float(data['lastFundingRate']),
            'next_funding_time': int(data['nextFundingTime']),
            'estimated_settle_price': float(data.get('estimatedSettlePrice', 0))
        }
    
    return data

def get_funding_rate_history(self, symbol: str, days: int = 7):
    """자금조달료 히스토리 조회"""
    
    endpoint = f"{self.base_url}/fapi/v1/fundingRate"
    
    end_time = int(time.time() * 1000)
    start_time = end_time - (days * 24 * 60 * 60 * 1000)
    
    params = {
        'symbol': symbol,
        'startTime': start_time,
        'endTime': end_time,
        'limit': 1000
    }
    
    response = requests.get(endpoint, params=params)
    data = response.json()
    
    # 통계 계산
    rates = [float(item['fundingRate']) for item in data]
    
    return {
        'symbol': symbol,
        'period_days': days,
        'total_funding_events': len(data),
        'avg_funding_rate': sum(rates) / len(rates) if rates else 0,
        'max_funding_rate': max(rates) if rates else 0,
        'min_funding_rate': min(rates) if rates else 0,
        'total_funding_cost': sum(rates),  # 8시간마다 지급
        'history': data[-10:]  # 최근 10개 이벤트
    }

# 자금조달료 분석
funding_info = api.get_mark_price_and_funding('BTCUSDT')
print(f"BTC 자금조달료: {funding_info['funding_rate']:.6f} ({funding_info['funding_rate']*100:.4f}%)")

funding_history = api.get_funding_rate_history('BTCUSDT', 30)
print(f"30일 평균 자금조달료: {funding_history['avg_funding_rate']:.6f}")
```

#### 📊 Open Interest & Long/Short Ratio
```python
def get_open_interest(self, symbol: str = None):
    """미결제 약정 조회"""
    
    endpoint = f"{self.base_url}/fapi/v1/openInterest"
    params = {}
    
    if symbol:
        params['symbol'] = symbol
    
    response = requests.get(endpoint, params=params)
    data = response.json()
    
    if symbol:
        return {
            'symbol': data['symbol'],
            'open_interest': float(data['openInterest']),
            'open_interest_value': float(data['openInterestValue'])
        }
    
    return data

def get_long_short_ratio(self, symbol: str, period: str = '5m'):
    """롱/숏 비율 조회"""
    
    endpoint = f"{self.base_url}/futures/data/globalLongShortAccountRatio"
    params = {
        'symbol': symbol,
        'period': period,  # 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d
        'limit': 30
    }
    
    response = requests.get(endpoint, params=params)
    data = response.json()
    
    if data:
        latest = data[-1]
        ratios = [float(item['longShortRatio']) for item in data]
        
        return {
            'symbol': symbol,
            'current_ratio': float(latest['longShortRatio']),
            'long_account': float(latest['longAccount']),
            'short_account': float(latest['shortAccount']),
            'avg_ratio': sum(ratios) / len(ratios),
            'trend': 'bullish' if ratios[-1] > ratios[0] else 'bearish',
            'history': data
        }
    
    return {}

# 시장 심리 분석
oi_data = api.get_open_interest('BTCUSDT')
ls_ratio = api.get_long_short_ratio('BTCUSDT', '1h')

print(f"BTC 미결제약정: {oi_data['open_interest']:,.0f} BTC")
print(f"롱/숏 비율: {ls_ratio['current_ratio']:.2f} ({'롱 우세' if ls_ratio['current_ratio'] > 1 else '숏 우세'})")
```

### 📦 2.3 Order Book & Trade Data

#### 📋 Order Book
```python
def get_order_book(self, symbol: str, limit: int = 100):
    """오더북 조회"""
    
    # 방법 1: REST API
    endpoint = f"{self.base_url}/fapi/v1/depth"
    params = {
        'symbol': symbol,
        'limit': limit  # 5, 10, 20, 50, 100, 500, 1000
    }
    
    response = requests.get(endpoint, params=params)
    data = response.json()
    
    # 방법 2: CCXT
    order_book = self.exchange.fetch_order_book(symbol, limit)
    
    # 분석 데이터 추가
    bids = [[float(price), float(qty)] for price, qty in data['bids']]
    asks = [[float(price), float(qty)] for price, qty in data['asks']]
    
    best_bid = bids[0][0] if bids else 0
    best_ask = asks[0][0] if asks else 0
    spread = best_ask - best_bid
    spread_percent = (spread / best_bid * 100) if best_bid > 0 else 0
    
    # 유동성 분석
    bid_liquidity = sum([qty for price, qty in bids[:10]])  # 상위 10개 호가
    ask_liquidity = sum([qty for price, qty in asks[:10]])
    
    return {
        'symbol': symbol,
        'last_update_id': data['lastUpdateId'],
        'best_bid': best_bid,
        'best_ask': best_ask,
        'spread': spread,
        'spread_percent': spread_percent,
        'bid_liquidity': bid_liquidity,
        'ask_liquidity': ask_liquidity,
        'bids': bids[:5],  # 상위 5개만
        'asks': asks[:5]   # 상위 5개만
    }

# 유동성 분석
book = api.get_order_book('BTCUSDT', 100)
print(f"BTC 스프레드: ${book['spread']:.2f} ({book['spread_percent']:.4f}%)")
print(f"매수 유동성: {book['bid_liquidity']:.2f} BTC")
```

#### 🔄 Recent Trades
```python
def get_recent_trades(self, symbol: str, limit: int = 100):
    """최근 거래 내역"""
    
    endpoint = f"{self.base_url}/fapi/v1/trades"
    params = {
        'symbol': symbol,
        'limit': limit
    }
    
    response = requests.get(endpoint, params=params)
    data = response.json()
    
    # 거래 분석
    total_volume = sum(float(trade['qty']) for trade in data)
    avg_price = sum(float(trade['price']) * float(trade['qty']) for trade in data) / total_volume if total_volume > 0 else 0
    
    buy_trades = [t for t in data if t['isBuyerMaker'] == False]  # Taker 매수
    sell_trades = [t for t in data if t['isBuyerMaker'] == True]   # Taker 매도
    
    buy_volume = sum(float(t['qty']) for t in buy_trades)
    sell_volume = sum(float(t['qty']) for t in sell_trades)
    
    return {
        'symbol': symbol,
        'trade_count': len(data),
        'total_volume': total_volume,
        'avg_price': avg_price,
        'buy_volume': buy_volume,
        'sell_volume': sell_volume,
        'buy_sell_ratio': buy_volume / sell_volume if sell_volume > 0 else float('inf'),
        'market_sentiment': 'bullish' if buy_volume > sell_volume else 'bearish',
        'recent_trades': data[-5:]  # 최근 5개 거래
    }

# 시장 활동 분석
trades = api.get_recent_trades('BTCUSDT', 200)
print(f"BTC 거래량: {trades['total_volume']:.2f} BTC")
print(f"매수/매도 비율: {trades['buy_sell_ratio']:.2f} ({'매수 우세' if trades['buy_sell_ratio'] > 1 else '매도 우세'})")
```

---

## 💼 Category 3: Account/Trade Endpoints (24개)

### 🔥 3.1 핵심 거래 기능 (필수)

#### 📝 New Order (신규 주문)
```python
def place_order(self, symbol: str, side: str, order_type: str, quantity: float, 
                price: float = None, stop_price: float = None, 
                reduce_only: bool = False, time_in_force: str = 'GTC'):
    """신규 주문 생성"""
    
    endpoint = f"{self.base_url}/fapi/v1/order"
    timestamp = int(time.time() * 1000)
    
    params = {
        'symbol': symbol,
        'side': side,  # BUY, SELL
        'type': order_type,  # MARKET, LIMIT, STOP_MARKET, STOP
        'quantity': quantity,
        'timestamp': timestamp
    }
    
    # 주문 타입별 추가 파라미터
    if order_type in ['LIMIT', 'STOP']:
        if price is None:
            raise ValueError("LIMIT/STOP 주문은 가격이 필요합니다")
        params['price'] = price
        params['timeInForce'] = time_in_force
    
    if order_type in ['STOP_MARKET', 'STOP']:
        if stop_price is None:
            raise ValueError("STOP 주문은 스톱 가격이 필요합니다")
        params['stopPrice'] = stop_price
    
    if reduce_only:
        params['reduceOnly'] = 'true'
    
    # 서명 생성
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    signature = self.generate_signature(query_string)
    params['signature'] = signature
    
    headers = self.get_headers()
    
    response = requests.post(endpoint, data=params, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"주문 실패: {response.text}")

# 사용 예시들
def place_market_buy(self, symbol: str, quantity: float):
    """시장가 매수"""
    return self.place_order(symbol, 'BUY', 'MARKET', quantity)

def place_limit_sell(self, symbol: str, quantity: float, price: float):
    """지정가 매도"""
    return self.place_order(symbol, 'SELL', 'LIMIT', quantity, price)

def place_stop_loss(self, symbol: str, quantity: float, stop_price: float):
    """스톱로스 주문"""
    return self.place_order(symbol, 'SELL', 'STOP_MARKET', quantity, stop_price=stop_price, reduce_only=True)

# 실전 거래 예시
try:
    # BTC 0.001개 시장가 매수
    order = api.place_market_buy('BTCUSDT', 0.001)
    print(f"주문 성공: {order['orderId']}")
    
    # 이익실현을 위한 지정가 매도 주문
    current_price = float(order['price'])
    target_price = current_price * 1.02  # 2% 상승 목표
    
    limit_order = api.place_limit_sell('BTCUSDT', 0.001, target_price)
    print(f"이익실현 주문: {limit_order['orderId']}")
    
except Exception as e:
    print(f"주문 실패: {e}")
```

#### 🔍 Query Order & All Orders
```python
def get_order(self, symbol: str, order_id: int = None, orig_client_order_id: str = None):
    """주문 조회"""
    
    endpoint = f"{self.base_url}/fapi/v1/order"
    timestamp = int(time.time() * 1000)
    
    params = {
        'symbol': symbol,
        'timestamp': timestamp
    }
    
    if order_id:
        params['orderId'] = order_id
    elif orig_client_order_id:
        params['origClientOrderId'] = orig_client_order_id
    else:
        raise ValueError("orderId 또는 origClientOrderId가 필요합니다")
    
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    signature = self.generate_signature(query_string)
    params['signature'] = signature
    
    headers = self.get_headers()
    response = requests.get(endpoint, params=params, headers=headers)
    
    if response.status_code == 200:
        order_data = response.json()
        return {
            'order_id': order_data['orderId'],
            'symbol': order_data['symbol'],
            'status': order_data['status'],
            'side': order_data['side'],
            'type': order_data['type'],
            'quantity': float(order_data['origQty']),
            'filled_quantity': float(order_data['executedQty']),
            'price': float(order_data['price']) if order_data['price'] != '0' else None,
            'avg_price': float(order_data['avgPrice']) if order_data['avgPrice'] != '0' else None,
            'time': order_data['time'],
            'update_time': order_data['updateTime']
        }
    else:
        raise Exception(f"주문 조회 실패: {response.text}")

def get_all_orders(self, symbol: str, limit: int = 100):
    """전체 주문 히스토리"""
    
    endpoint = f"{self.base_url}/fapi/v1/allOrders"
    timestamp = int(time.time() * 1000)
    
    params = {
        'symbol': symbol,
        'limit': limit,
        'timestamp': timestamp
    }
    
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    signature = self.generate_signature(query_string)
    params['signature'] = signature
    
    headers = self.get_headers()
    response = requests.get(endpoint, params=params, headers=headers)
    
    if response.status_code == 200:
        orders = response.json()
        
        # 주문 통계
        total_orders = len(orders)
        filled_orders = len([o for o in orders if o['status'] == 'FILLED'])
        cancelled_orders = len([o for o in orders if o['status'] == 'CANCELED'])
        
        return {
            'total_orders': total_orders,
            'filled_orders': filled_orders,
            'cancelled_orders': cancelled_orders,
            'fill_rate': filled_orders / total_orders if total_orders > 0 else 0,
            'orders': orders
        }
    else:
        raise Exception(f"주문 조회 실패: {response.text}")

# 주문 추적
order_status = api.get_order('BTCUSDT', order_id=12345)
print(f"주문 상태: {order_status['status']}")
print(f"체결률: {order_status['filled_quantity']}/{order_status['quantity']}")
```

#### ❌ Cancel Order & Cancel All
```python
def cancel_order(self, symbol: str, order_id: int = None, orig_client_order_id: str = None):
    """주문 취소"""
    
    endpoint = f"{self.base_url}/fapi/v1/order"
    timestamp = int(time.time() * 1000)
    
    params = {
        'symbol': symbol,
        'timestamp': timestamp
    }
    
    if order_id:
        params['orderId'] = order_id
    elif orig_client_order_id:
        params['origClientOrderId'] = orig_client_order_id
    else:
        raise ValueError("orderId 또는 origClientOrderId가 필요합니다")
    
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    signature = self.generate_signature(query_string)
    params['signature'] = signature
    
    headers = self.get_headers()
    response = requests.delete(endpoint, data=params, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"주문 취소 실패: {response.text}")

def cancel_all_orders(self, symbol: str):
    """모든 열린 주문 취소"""
    
    endpoint = f"{self.base_url}/fapi/v1/allOpenOrders"
    timestamp = int(time.time() * 1000)
    
    params = {
        'symbol': symbol,
        'timestamp': timestamp
    }
    
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    signature = self.generate_signature(query_string)
    params['signature'] = signature
    
    headers = self.get_headers()
    response = requests.delete(endpoint, data=params, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"전체 주문 취소 실패: {response.text}")

# 긴급 상황 대응
def emergency_cancel_all(self):
    """모든 심볼의 모든 주문 취소"""
    positions = self.get_positions()
    
    cancelled_orders = {}
    for position in positions:
        if position['position_amt'] != 0:  # 포지션이 있는 심볼만
            try:
                result = self.cancel_all_orders(position['symbol'])
                cancelled_orders[position['symbol']] = result
                print(f"{position['symbol']} 주문 취소 완료")
            except Exception as e:
                print(f"{position['symbol']} 주문 취소 실패: {e}")
    
    return cancelled_orders
```

### 💰 3.2 계좌 관리

#### 💼 Account Information
```python
def get_account_info(self):
    """계좌 정보 조회"""
    
    endpoint = f"{self.base_url}/fapi/v2/account"
    timestamp = int(time.time() * 1000)
    
    params = {'timestamp': timestamp}
    query_string = f"timestamp={timestamp}"
    signature = self.generate_signature(query_string)
    params['signature'] = signature
    
    headers = self.get_headers()
    response = requests.get(endpoint, params=params, headers=headers)
    
    if response.status_code == 200:
        account = response.json()
        
        # 핵심 정보 추출
        return {
            'total_wallet_balance': float(account['totalWalletBalance']),
            'total_unrealized_pnl': float(account['totalUnrealizedProfit']),
            'total_margin_balance': float(account['totalMarginBalance']),
            'total_position_initial_margin': float(account['totalPositionInitialMargin']),
            'total_open_order_initial_margin': float(account['totalOpenOrderInitialMargin']),
            'available_balance': float(account['availableBalance']),
            'max_withdraw_amount': float(account['maxWithdrawAmount']),
            'can_trade': account['canTrade'],
            'can_deposit': account['canDeposit'],
            'can_withdraw': account['canWithdraw'],
            'update_time': account['updateTime'],
            'assets': account['assets'],
            'positions': account['positions']
        }
    else:
        raise Exception(f"계좌 정보 조회 실패: {response.text}")

def get_balance(self):
    """간단한 잔고 조회"""
    
    endpoint = f"{self.base_url}/fapi/v2/balance"
    timestamp = int(time.time() * 1000)
    
    params = {'timestamp': timestamp}
    query_string = f"timestamp={timestamp}"
    signature = self.generate_signature(query_string)
    params['signature'] = signature
    
    headers = self.get_headers()
    response = requests.get(endpoint, params=params, headers=headers)
    
    if response.status_code == 200:
        balances = response.json()
        
        # USDT 잔고만 추출
        usdt_balance = None
        for balance in balances:
            if balance['asset'] == 'USDT':
                usdt_balance = {
                    'wallet_balance': float(balance['walletBalance']),
                    'unrealized_pnl': float(balance['unrealizedProfit']),
                    'margin_balance': float(balance['marginBalance']),
                    'available_balance': float(balance['availableBalance']),
                    'cross_unrealized_pnl': float(balance['crossUnrealizedPnl'])
                }
                break
        
        return {
            'usdt': usdt_balance,
            'all_balances': balances
        }
    else:
        raise Exception(f"잔고 조회 실패: {response.text}")

# 계좌 상태 모니터링
account = api.get_account_info()
print(f"총 지갑 잔고: ${account['total_wallet_balance']:,.2f}")
print(f"미실현 손익: ${account['total_unrealized_pnl']:,.2f}")
print(f"사용 가능 잔고: ${account['available_balance']:,.2f}")

if account['total_unrealized_pnl'] < -1000:  # $1000 이상 손실
    print("⚠️ 큰 손실 발생! 리스크 관리 필요")
```

#### 📊 Position Information
```python
def get_positions(self, symbol: str = None):
    """포지션 정보 조회"""
    
    endpoint = f"{self.base_url}/fapi/v2/positionRisk"
    timestamp = int(time.time() * 1000)
    
    params = {'timestamp': timestamp}
    if symbol:
        params['symbol'] = symbol
    
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    signature = self.generate_signature(query_string)
    params['signature'] = signature
    
    headers = self.get_headers()
    response = requests.get(endpoint, params=params, headers=headers)
    
    if response.status_code == 200:
        positions = response.json()
        
        # 활성 포지션만 필터링
        active_positions = []
        for pos in positions:
            position_amt = float(pos['positionAmt'])
            if position_amt != 0:
                mark_price = float(pos['markPrice'])
                entry_price = float(pos['entryPrice'])
                liquidation_price = float(pos['liquidationPrice'])
                
                # 포지션 분석
                pnl_percent = ((mark_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
                if position_amt < 0:  # 숏 포지션
                    pnl_percent = -pnl_percent
                
                liquidation_distance = abs(mark_price - liquidation_price) / mark_price if liquidation_price > 0 else 1.0
                
                active_positions.append({
                    'symbol': pos['symbol'],
                    'side': 'LONG' if position_amt > 0 else 'SHORT',
                    'size': abs(position_amt),
                    'entry_price': entry_price,
                    'mark_price': mark_price,
                    'liquidation_price': liquidation_price,
                    'unrealized_pnl': float(pos['unRealizedProfit']),
                    'pnl_percent': pnl_percent,
                    'margin_ratio': float(pos['marginRatio']),
                    'liquidation_distance_percent': liquidation_distance * 100,
                    'leverage': int(1 / float(pos['marginRatio'])) if float(pos['marginRatio']) > 0 else 1
                })
        
        return active_positions
    else:
        raise Exception(f"포지션 조회 실패: {response.text}")

# 포지션 모니터링
positions = api.get_positions()
for pos in positions:
    print(f"{pos['symbol']} {pos['side']}: {pos['pnl_percent']:+.2f}% (청산거리: {pos['liquidation_distance_percent']:.1f}%)")
```

### ⚖️ 3.3 레버리지 및 마진 관리

#### 🎚️ Change Initial Leverage
```python
def change_leverage(self, symbol: str, leverage: int):
    """레버리지 변경"""
    
    endpoint = f"{self.base_url}/fapi/v1/leverage"
    timestamp = int(time.time() * 1000)
    
    params = {
        'symbol': symbol,
        'leverage': leverage,
        'timestamp': timestamp
    }
    
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    signature = self.generate_signature(query_string)
    params['signature'] = signature
    
    headers = self.get_headers()
    response = requests.post(endpoint, data=params, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        return {
            'symbol': result['symbol'],
            'leverage': int(result['leverage']),
            'max_notional_value': float(result['maxNotionalValue'])
        }
    else:
        raise Exception(f"레버리지 변경 실패: {response.text}")

def change_margin_type(self, symbol: str, margin_type: str):
    """마진 타입 변경 (ISOLATED/CROSSED)"""
    
    endpoint = f"{self.base_url}/fapi/v1/marginType"
    timestamp = int(time.time() * 1000)
    
    params = {
        'symbol': symbol,
        'marginType': margin_type,  # ISOLATED, CROSSED
        'timestamp': timestamp
    }
    
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    signature = self.generate_signature(query_string)
    params['signature'] = signature
    
    headers = self.get_headers()
    response = requests.post(endpoint, data=params, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        # 이미 해당 타입인 경우 에러가 발생할 수 있음
        if "No need to change margin type" in response.text:
            return {'message': f'{symbol} 이미 {margin_type} 모드입니다'}
        else:
            raise Exception(f"마진 타입 변경 실패: {response.text}")

def modify_isolated_position_margin(self, symbol: str, amount: float, type: int):
    """격리 마진 조정"""
    
    endpoint = f"{self.base_url}/fapi/v1/positionMargin"
    timestamp = int(time.time() * 1000)
    
    params = {
        'symbol': symbol,
        'amount': amount,
        'type': type,  # 1: 마진 추가, 2: 마진 감소
        'timestamp': timestamp
    }
    
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    signature = self.generate_signature(query_string)
    params['signature'] = signature
    
    headers = self.get_headers()
    response = requests.post(endpoint, data=params, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"마진 조정 실패: {response.text}")

# 리스크 관리 예시
def optimize_leverage_by_volatility(self, symbol: str):
    """변동성 기반 레버리지 최적화"""
    
    # 24시간 변동성 계산
    ticker = self.get_24hr_ticker(symbol)
    volatility = abs(ticker['price_change_percent']) / 100
    
    # 변동성에 따른 레버리지 결정
    if volatility > 0.10:  # 10% 이상 변동성
        optimal_leverage = 2
    elif volatility > 0.05:  # 5-10% 변동성
        optimal_leverage = 5
    else:  # 5% 미만 변동성
        optimal_leverage = 10
    
    try:
        result = self.change_leverage(symbol, optimal_leverage)
        print(f"{symbol} 레버리지를 {optimal_leverage}x로 조정 (변동성: {volatility:.2%})")
        return result
    except Exception as e:
        print(f"레버리지 조정 실패: {e}")
        return None

# 사용 예시
api.optimize_leverage_by_volatility('BTCUSDT')
api.change_margin_type('BTCUSDT', 'ISOLATED')
```

---

## 🌐 Category 4: WebSocket Market Streams (14개)

### ⚡ 4.1 실시간 데이터 스트림

#### 📊 Individual Symbol Ticker Streams
```javascript
// JavaScript WebSocket 예시
const WebSocket = require('ws');

class BinanceFuturesWS {
    constructor(testnet = true) {
        this.baseWS = testnet ? 
            'wss://stream.binancefuture.com/ws/' :
            'wss://fstream.binance.com/ws/';
        this.connections = new Map();
    }
    
    subscribeTicker(symbol, callback) {
        const stream = `${symbol.toLowerCase()}@ticker`;
        const ws = new WebSocket(this.baseWS + stream);
        
        ws.on('message', (data) => {
            const ticker = JSON.parse(data);
            const formattedData = {
                symbol: ticker.s,
                price_change: parseFloat(ticker.P),
                price_change_percent: parseFloat(ticker.P),
                last_price: parseFloat(ticker.c),
                volume: parseFloat(ticker.v),
                count: parseInt(ticker.x)
            };
            callback(formattedData);
        });
        
        ws.on('error', (error) => {
            console.error('WebSocket error:', error);
        });
        
        this.connections.set(`ticker_${symbol}`, ws);
        return ws;
    }
    
    subscribeKline(symbol, interval, callback) {
        const stream = `${symbol.toLowerCase()}@kline_${interval}`;
        const ws = new WebSocket(this.baseWS + stream);
        
        ws.on('message', (data) => {
            const message = JSON.parse(data);
            const kline = message.k;
            
            const candleData = {
                symbol: kline.s,
                open_time: kline.t,
                close_time: kline.T,
                open: parseFloat(kline.o),
                high: parseFloat(kline.h),
                low: parseFloat(kline.l),
                close: parseFloat(kline.c),
                volume: parseFloat(kline.v),
                is_closed: kline.x  // 캔들 완성 여부
            };
            
            callback(candleData);
        });
        
        this.connections.set(`kline_${symbol}_${interval}`, ws);
        return ws;
    }
    
    subscribeOrderBook(symbol, levels, callback) {
        const stream = `${symbol.toLowerCase()}@depth${levels}@100ms`;
        const ws = new WebSocket(this.baseWS + stream);
        
        ws.on('message', (data) => {
            const orderBook = JSON.parse(data);
            
            const formattedBook = {
                symbol: symbol,
                last_update_id: orderBook.lastUpdateId,
                bids: orderBook.bids.map(([price, qty]) => [parseFloat(price), parseFloat(qty)]),
                asks: orderBook.asks.map(([price, qty]) => [parseFloat(price), parseFloat(qty)])
            };
            
            callback(formattedBook);
        });
        
        this.connections.set(`depth_${symbol}`, ws);
        return ws;
    }
    
    closeConnection(key) {
        const ws = this.connections.get(key);
        if (ws) {
            ws.close();
            this.connections.delete(key);
        }
    }
    
    closeAllConnections() {
        this.connections.forEach((ws, key) => {
            ws.close();
            this.connections.delete(key);
        });
    }
}

// 사용 예시
const wsClient = new BinanceFuturesWS(true);

// 실시간 가격 모니터링
wsClient.subscribeTicker('BTCUSDT', (data) => {
    console.log(`BTC 가격: $${data.last_price} (${data.price_change_percent:+.2f}%)`);
});

// 실시간 캔들 데이터
wsClient.subscribeKline('BTCUSDT', '1m', (data) => {
    if (data.is_closed) {
        console.log(`새 1분 캔들 완성: O:${data.open} H:${data.high} L:${data.low} C:${data.close}`);
    }
});

// 오더북 모니터링
wsClient.subscribeOrderBook('BTCUSDT', 20, (data) => {
    const bestBid = data.bids[0][0];
    const bestAsk = data.asks[0][0];
    const spread = bestAsk - bestBid;
    console.log(`스프레드: $${spread.toFixed(2)} (매수: $${bestBid}, 매도: $${bestAsk})`);
});
```

#### 🔄 Aggregate Trade Streams
```python
import asyncio
import websockets
import json

class BinanceFuturesWSAsync:
    def __init__(self, testnet=True):
        self.base_ws = 'wss://stream.binancefuture.com/ws/' if testnet else 'wss://fstream.binance.com/ws/'
        
    async def subscribe_agg_trades(self, symbol, callback):
        """실시간 통합 거래 데이터"""
        
        stream = f"{symbol.lower()}@aggTrade"
        uri = self.base_ws + stream
        
        async with websockets.connect(uri) as websocket:
            async for message in websocket:
                data = json.loads(message)
                
                trade_data = {
                    'symbol': data['s'],
                    'price': float(data['p']),
                    'quantity': float(data['q']),
                    'timestamp': data['T'],
                    'is_buyer_maker': data['m'],  # True면 매도, False면 매수
                    'trade_id': data['a']
                }
                
                await callback(trade_data)
    
    async def subscribe_mark_price(self, symbol, callback):
        """마크 가격 실시간 스트림"""
        
        stream = f"{symbol.lower()}@markPrice@1s"
        uri = self.base_ws + stream
        
        async with websockets.connect(uri) as websocket:
            async for message in websocket:
                data = json.loads(message)
                
                mark_data = {
                    'symbol': data['s'],
                    'mark_price': float(data['p']),
                    'index_price': float(data.get('i', 0)),
                    'funding_rate': float(data.get('r', 0)),
                    'next_funding_time': int(data.get('T', 0)),
                    'timestamp': data['E']
                }
                
                await callback(mark_data)
    
    async def multi_stream_subscribe(self, streams, callback):
        """다중 스트림 구독"""
        
        # 스트림 배열을 JSON으로 변환
        stream_names = '/'.join(streams)
        uri = f"{self.base_ws}{stream_names}"
        
        async with websockets.connect(uri) as websocket:
            async for message in websocket:
                data = json.loads(message)
                await callback(data)

# 비동기 사용 예시
async def trade_monitor(trade_data):
    """거래 모니터링 콜백"""
    side = "SELL" if trade_data['is_buyer_maker'] else "BUY"
    print(f"[{trade_data['symbol']}] {side} {trade_data['quantity']} @ ${trade_data['price']}")

async def mark_price_monitor(mark_data):
    """마크 가격 모니터링"""
    print(f"{mark_data['symbol']} 마크가격: ${mark_data['mark_price']:.2f}")

async def main():
    ws_client = BinanceFuturesWSAsync(testnet=True)
    
    # 다중 스트림 동시 실행
    await asyncio.gather(
        ws_client.subscribe_agg_trades('BTCUSDT', trade_monitor),
        ws_client.subscribe_mark_price('BTCUSDT', mark_price_monitor)
    )

# 실행
# asyncio.run(main())
```

### 📈 4.2 고급 스트림 활용

#### 📊 All Market Tickers Stream
```python
import json
import threading
from collections import defaultdict
import time

class MarketAnalyzer:
    def __init__(self):
        self.price_data = defaultdict(list)
        self.volume_data = defaultdict(list)
        self.max_history = 100  # 최근 100개 데이터만 보관
        
    def analyze_all_markets(self):
        """전체 시장 실시간 분석"""
        
        def process_ticker_data(data):
            if 'data' in data:
                ticker = data['data']
            else:
                ticker = data
                
            symbol = ticker['s']
            price = float(ticker['c'])
            volume = float(ticker['v'])
            change_percent = float(ticker['P'])
            
            # 데이터 저장
            self.price_data[symbol].append(price)
            self.volume_data[symbol].append(volume)
            
            # 메모리 관리
            if len(self.price_data[symbol]) > self.max_history:
                self.price_data[symbol].pop(0)
                self.volume_data[symbol].pop(0)
            
            # 이상 징후 감지
            if abs(change_percent) > 10:  # 10% 이상 변동
                print(f"🚨 급변동 감지: {symbol} {change_percent:+.2f}%")
                
            if volume > 1000000:  # 대량 거래 감지
                print(f"📊 대량거래: {symbol} {volume:,.0f}")
        
        # WebSocket 연결 (별도 스레드에서 실행)
        thread = threading.Thread(target=self._run_all_tickers_stream, args=(process_ticker_data,))
        thread.daemon = True
        thread.start()
        
        return thread
    
    def _run_all_tickers_stream(self, callback):
        """전체 티커 스트림 실행"""
        import websockets
        import asyncio
        
        async def stream_handler():
            uri = "wss://stream.binancefuture.com/ws/!ticker@arr"
            
            async with websockets.connect(uri) as websocket:
                async for message in websocket:
                    tickers = json.loads(message)
                    
                    for ticker in tickers:
                        callback(ticker)
        
        asyncio.run(stream_handler())
    
    def get_top_movers(self, limit=10):
        """상위 변동 종목 조회"""
        # 실시간 데이터에서 계산된 변동률 기준
        # 실제 구현에서는 최근 가격 데이터를 사용하여 계산
        pass
    
    def get_volume_leaders(self, limit=10):
        """거래량 상위 종목"""
        # 실시간 거래량 데이터 기준
        pass

# 시장 분석 시작
analyzer = MarketAnalyzer()
analyzer.analyze_all_markets()

# 분석 결과 주기적 출력
time.sleep(10)  # 데이터 수집 대기
# analyzer.get_top_movers()
```

---

## 📱 Category 5: User Data Streams (7개)

### 🔔 5.1 계좌 이벤트 스트림

#### 🔑 Start User Data Stream
```python
def start_user_data_stream(self):
    """사용자 데이터 스트림 시작"""
    
    endpoint = f"{self.base_url}/fapi/v1/listenKey"
    headers = self.get_headers()
    
    response = requests.post(endpoint, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return data['listenKey']
    else:
        raise Exception(f"사용자 데이터 스트림 시작 실패: {response.text}")

def keepalive_user_data_stream(self, listen_key: str):
    """사용자 데이터 스트림 연결 유지"""
    
    endpoint = f"{self.base_url}/fapi/v1/listenKey"
    headers = self.get_headers()
    params = {'listenKey': listen_key}
    
    response = requests.put(endpoint, headers=headers, params=params)
    
    if response.status_code == 200:
        return True
    else:
        print(f"연결 유지 실패: {response.text}")
        return False

def close_user_data_stream(self, listen_key: str):
    """사용자 데이터 스트림 종료"""
    
    endpoint = f"{self.base_url}/fapi/v1/listenKey"
    headers = self.get_headers()
    params = {'listenKey': listen_key}
    
    response = requests.delete(endpoint, headers=headers, params=params)
    
    if response.status_code == 200:
        return True
    else:
        print(f"스트림 종료 실패: {response.text}")
        return False

# 사용자 데이터 스트림 관리
listen_key = api.start_user_data_stream()
print(f"Listen Key: {listen_key}")
```

#### 📊 Event: Account Update & Order Update
```python
import asyncio
import websockets
import json
import threading
import time

class UserDataStreamHandler:
    def __init__(self, api_instance, testnet=True):
        self.api = api_instance
        self.base_ws = 'wss://stream.binancefuture.com/ws/' if testnet else 'wss://fstream.binance.com/ws/'
        self.listen_key = None
        self.is_running = False
        self.keepalive_thread = None
        
    async def start_user_stream(self, callbacks=None):
        """사용자 데이터 스트림 시작"""
        
        # Listen Key 획득
        self.listen_key = self.api.start_user_data_stream()
        print(f"사용자 스트림 시작: {self.listen_key}")
        
        # 기본 콜백 설정
        if callbacks is None:
            callbacks = {
                'account_update': self.default_account_callback,
                'order_update': self.default_order_callback,
                'margin_call': self.default_margin_callback
            }
        
        # Keep-alive 스레드 시작
        self.is_running = True
        self.keepalive_thread = threading.Thread(target=self._keepalive_loop)
        self.keepalive_thread.daemon = True
        self.keepalive_thread.start()
        
        # WebSocket 연결
        uri = f"{self.base_ws}{self.listen_key}"
        
        try:
            async with websockets.connect(uri) as websocket:
                print("✅ 사용자 데이터 스트림 연결됨")
                
                async for message in websocket:
                    data = json.loads(message)
                    await self.process_user_event(data, callbacks)
                    
        except Exception as e:
            print(f"사용자 스트림 오류: {e}")
        finally:
            self.stop_stream()
    
    async def process_user_event(self, data, callbacks):
        """사용자 이벤트 처리"""
        
        event_type = data.get('e')
        
        if event_type == 'ACCOUNT_UPDATE':
            # 계좌 업데이트 이벤트
            account_data = {
                'event_time': data['E'],
                'balances': [],
                'positions': []
            }
            
            # 잔고 변경
            if 'a' in data:
                for balance in data['a']['B']:
                    account_data['balances'].append({
                        'asset': balance['a'],
                        'wallet_balance': float(balance['wb']),
                        'cross_wallet_balance': float(balance['cw']),
                        'balance_change': float(balance['bc'])
                    })
                
                # 포지션 변경
                for position in data['a']['P']:
                    if float(position['pa']) != 0:  # 활성 포지션만
                        account_data['positions'].append({
                            'symbol': position['s'],
                            'position_amount': float(position['pa']),
                            'entry_price': float(position['ep']),
                            'unrealized_pnl': float(position['up']),
                            'margin_type': position['mt']
                        })
            
            await callbacks['account_update'](account_data)
            
        elif event_type == 'ORDER_TRADE_UPDATE':
            # 주문 업데이트 이벤트
            order_data = {
                'event_time': data['E'],
                'symbol': data['o']['s'],
                'order_id': data['o']['i'],
                'side': data['o']['S'],
                'order_type': data['o']['o'],
                'status': data['o']['X'],
                'quantity': float(data['o']['q']),
                'filled_quantity': float(data['o']['z']),
                'price': float(data['o']['p']) if data['o']['p'] != '0' else None,
                'avg_price': float(data['o']['ap']) if data['o']['ap'] != '0' else None,
                'commission': float(data['o']['n']),
                'commission_asset': data['o']['N'],
                'execution_type': data['o']['x'],
                'time_in_force': data['o']['f'],
                'is_reduce_only': data['o']['R']
            }
            
            await callbacks['order_update'](order_data)
            
        elif event_type == 'MARGIN_CALL':
            # 마진 콜 이벤트
            margin_data = {
                'event_time': data['E'],
                'cross_wallet_balance': float(data['cw']),
                'positions': []
            }
            
            for position in data['p']:
                margin_data['positions'].append({
                    'symbol': position['s'],
                    'side': position['ps'],
                    'position_amount': float(position['pa']),
                    'margin_type': position['mt'],
                    'isolated_wallet': float(position['iw']),
                    'mark_price': float(position['mp']),
                    'unrealized_pnl': float(position['up']),
                    'maintenance_margin_required': float(position['mm'])
                })
            
            await callbacks['margin_call'](margin_data)
    
    async def default_account_callback(self, data):
        """기본 계좌 업데이트 콜백"""
        print(f"💼 계좌 업데이트 - 시간: {data['event_time']}")
        
        for balance in data['balances']:
            if abs(balance['balance_change']) > 0:
                print(f"  💰 {balance['asset']}: {balance['balance_change']:+.4f} (잔고: {balance['wallet_balance']:.4f})")
        
        for position in data['positions']:
            pnl_color = "🟢" if position['unrealized_pnl'] >= 0 else "🔴"
            print(f"  📊 {position['symbol']}: {position['unrealized_pnl']:+.4f} USDT {pnl_color}")
    
    async def default_order_callback(self, data):
        """기본 주문 업데이트 콜백"""
        status_emoji = {
            'NEW': '🆕',
            'FILLED': '✅',
            'PARTIALLY_FILLED': '🔄',
            'CANCELED': '❌',
            'REJECTED': '⛔'
        }
        
        emoji = status_emoji.get(data['status'], '❓')
        print(f"{emoji} 주문 업데이트: {data['symbol']} {data['side']} {data['status']}")
        
        if data['status'] == 'FILLED':
            print(f"  💵 체결가: ${data['avg_price']:.2f}, 수량: {data['filled_quantity']}")
            print(f"  💸 수수료: {data['commission']} {data['commission_asset']}")
    
    async def default_margin_callback(self, data):
        """기본 마진 콜 콜백"""
        print(f"🚨 마진 콜 발생! - 시간: {data['event_time']}")
        print(f"💰 Cross Wallet Balance: {data['cross_wallet_balance']:.4f} USDT")
        
        for position in data['positions']:
            print(f"⚠️ {position['symbol']}: 유지마진 {position['maintenance_margin_required']:.4f} USDT 필요")
    
    def _keepalive_loop(self):
        """Keep-alive 루프 (30초마다 실행)"""
        while self.is_running:
            time.sleep(30)
            if self.listen_key:
                success = self.api.keepalive_user_data_stream(self.listen_key)
                if success:
                    print("🔄 User stream keep-alive 성공")
                else:
                    print("❌ User stream keep-alive 실패")
                    break
    
    def stop_stream(self):
        """스트림 정지"""
        self.is_running = False
        if self.listen_key:
            self.api.close_user_data_stream(self.listen_key)
            print("⏹️ 사용자 데이터 스트림 종료")

# 사용 예시
async def main():
    # API 인스턴스 생성
    api = BinanceFuturesAPI(api_key, api_secret, testnet=True)
    
    # 사용자 데이터 스트림 핸들러 생성
    stream_handler = UserDataStreamHandler(api, testnet=True)
    
    # 커스텀 콜백 정의
    async def custom_order_callback(data):
        if data['status'] == 'FILLED':
            # 체결 시 텔레그램 알림 등 추가 작업
            print(f"🎉 주문 체결 완료: {data['symbol']} {data['side']}")
    
    callbacks = {
        'account_update': stream_handler.default_account_callback,
        'order_update': custom_order_callback,
        'margin_call': stream_handler.default_margin_callback
    }
    
    # 스트림 시작
    await stream_handler.start_user_stream(callbacks)

# asyncio.run(main())
```

---

## 🚨 에러 처리 및 제한사항

### ⚠️ 주요 에러 코드

```python
class BinanceErrorHandler:
    """Binance API 에러 처리"""
    
    ERROR_CODES = {
        -1001: "DISCONNECTED - 내부 에러, 연결을 재시도하세요",
        -1002: "UNAUTHORIZED - API-key 형식이 올바르지 않습니다", 
        -1003: "TOO_MANY_REQUESTS - 요청 제한을 초과했습니다",
        -1006: "UNEXPECTED_RESP - 예기치 않은 응답을 받았습니다",
        -1007: "TIMEOUT - 타임아웃이 발생했습니다",
        -1021: "INVALID_TIMESTAMP - 타임스탬프가 recv_window 범위를 벗어났습니다",
        -1022: "INVALID_SIGNATURE - 서명이 올바르지 않습니다",
        -2010: "NEW_ORDER_REJECTED - 새로운 주문이 거부되었습니다",
        -2011: "CANCEL_REJECTED - 주문 취소가 거부되었습니다",
        -2013: "NO_SUCH_ORDER - 주문이 존재하지 않습니다",
        -2014: "BAD_API_KEY_FMT - API-key 형식이 올바르지 않습니다",
        -2015: "REJECTED_MBX_KEY - 유효하지 않은 API-key, IP, 또는 권한입니다",
        -4000: "INVALID_ORDER_STATUS - 주문 상태가 올바르지 않습니다",
        -4001: "PRICE_LESS_THAN_ZERO - 가격이 0보다 작습니다",
        -4002: "PRICE_GREATER_THAN_MAX_PRICE - 가격이 최대값을 초과했습니다",
        -4003: "QTY_LESS_THAN_ZERO - 수량이 0보다 작습니다",
        -4004: "QTY_LESS_THAN_MIN_QTY - 수량이 최소값보다 작습니다",
        -4005: "QTY_GREATER_THAN_MAX_QTY - 수량이 최대값을 초과했습니다",
        -4006: "STOP_PRICE_LESS_THAN_ZERO - 스톱 가격이 0보다 작습니다",
        -4007: "STOP_PRICE_GREATER_THAN_MAX_PRICE - 스톱 가격이 최대값을 초과했습니다",
        -4008: "TICK_SIZE_LESS_THAN_ZERO - 틱 사이즈가 0보다 작습니다",
        -4009: "MAX_PRICE_LESS_THAN_MIN_PRICE - 최대가격이 최소가격보다 작습니다",
        -4010: "MAX_QTY_LESS_THAN_MIN_QTY - 최대수량이 최소수량보다 작습니다",
        -4011: "STEP_SIZE_LESS_THAN_ZERO - 스텝 사이즈가 0보다 작습니다",
        -4012: "MAX_NUM_ORDERS_LESS_THAN_ZERO - 최대 주문 수가 0보다 작습니다",
        -4013: "PRICE_LESS_THAN_MIN_PRICE - 가격이 최소값보다 작습니다",
        -4014: "PRICE_NOT_INCREASED - 가격이 증가하지 않았습니다",
        -4015: "INVALID_CL_ORD_ID - 클라이언트 주문 ID가 올바르지 않습니다",
        -4016: "PRICE_HIGHTER_THAN_MULTIPLIER_UP - 가격이 배수 상한을 초과했습니다",
        -4017: "MULTIPLIER_UP_LESS_THAN_ZERO - 상한 배수가 0보다 작습니다",
        -4018: "MULTIPLIER_DOWN_LESS_THAN_ZERO - 하한 배수가 0보다 작습니다",
        -4019: "COMPOSITE_SCALE_OVERFLOW - 복합 스케일 오버플로우",
        -4020: "TARGET_STRATEGY_INVALID - 타겟 전략이 올바르지 않습니다",
        -4021: "INVALID_DEPTH_LIMIT - 깊이 제한이 올바르지 않습니다",
        -4022: "WRONG_MARKET_STATUS - 잘못된 시장 상태",
        -4023: "QTY_NOT_INCREASED - 수량이 증가하지 않았습니다",
        -4024: "PRICE_LOWER_THAN_MULTIPLIER_DOWN - 가격이 배수 하한보다 낮습니다",
        -4025: "MULTIPLIER_DECIMAL_LESS_THAN_ZERO - 배수 소수점이 0보다 작습니다",
        -4026: "COMMISSION_INVALID - 수수료가 올바르지 않습니다",
        -4027: "INVALID_ACCOUNT_TYPE - 계좌 유형이 올바르지 않습니다",
        -4028: "INVALID_LEVERAGE - 레버리지가 올바르지 않습니다",
        -4029: "INVALID_TICK_SIZE_PRECISION - 틱 사이즈 정밀도가 올바르지 않습니다",
        -4030: "INVALID_STEP_SIZE_PRECISION - 스텝 사이즈 정밀도가 올바르지 않습니다",
        -4031: "INVALID_WORKING_TYPE - 작업 유형이 올바르지 않습니다",
        -4032: "EXCEED_MAX_CANCEL_ORDER_SIZE - 최대 취소 주문 크기를 초과했습니다",
        -4033: "INSURANCE_ACCOUNT_NOT_FOUND - 보험 계좌를 찾을 수 없습니다",
        -4034: "INVALID_BALANCE_TYPE - 잔고 유형이 올바르지 않습니다",
        -4035: "MAX_STOP_ORDER_EXCEEDED - 최대 스톱 주문을 초과했습니다",
        -4036: "NO_NEED_TO_CHANGE_MARGIN_TYPE - 마진 타입을 변경할 필요가 없습니다",
        -4037: "THERE_EXISTS_OPEN_ORDERS - 열린 주문이 존재합니다",
        -4038: "QUANTITY_EXISTS_WITH_CLOSE_POSITION - 포지션 종료 시 수량이 존재합니다",
        -4039: "REDUCE_ONLY_REJECT - 축소 전용 주문이 거부되었습니다",
        -4040: "ORDER_TYPE_CANNOT_BE_MKT_ON_CLOSE - 시장 종료 시 시장가 주문을 사용할 수 없습니다",
        -4041: "INVALID_MARGIN_TYPE - 마진 타입이 올바르지 않습니다",
        -4042: "INVALID_ISOLATED_MARGIN_TYPE - 격리 마진 타입이 올바르지 않습니다",
        -4043: "INVALID_POSITION_SIDE - 포지션 사이드가 올바르지 않습니다",
        -4044: "POSITION_SIDE_NOT_MATCH - 포지션 사이드가 일치하지 않습니다",
        -4045: "REDUCE_ONLY_CONFLICT - 축소 전용 충돌",
        -4046: "INVALID_OPTIONS_REQUEST_TYPE - 옵션 요청 타입이 올바르지 않습니다",
        -4047: "INVALID_PENDING_ORDER_TYPE - 대기 주문 타입이 올바르지 않습니다",
        -4048: "TRADING_QUANTITATIVE_RULE_VIOLATED - 거래 정량적 규칙 위반",
        -4049: "MARKET_ORDER_REJECT - 시장가 주문 거부",
        -4050: "REJECT_ORDER_UPDATE - 주문 업데이트 거부",
        -4051: "INSUFFICIENT_BALANCE - 잔고 부족",
        -4052: "MARKET_ORDER_CURRENTLY_NOT_SUPPORT - 현재 시장가 주문을 지원하지 않습니다",
        -4053: "ONLY_SUPPORT_MARKET_ORDER - 시장가 주문만 지원합니다",
        -4054: "INVALID_MARGIN_ASSET - 마진 자산이 올바르지 않습니다",
        -4055: "INVALID_AUTO_REPAY_STATUS - 자동 상환 상태가 올바르지 않습니다",
        -4056: "ENV_NET_ERROR - 환경 네트워크 오류",
        -4057: "MARGIN_AUTO_REPAY_REJECT - 마진 자동 상환 거부",
        -4058: "CROSS_BALANCE_INSUFFICIENT - 교차 잔고 부족",
        -4059: "CROSS_BALANCE_TRANSFER_FAILED - 교차 잔고 이체 실패",
        -4060: "REPAY_WITH_COLLATERAL_IS_NOT_SUPPORTED - 담보 상환은 지원되지 않습니다",
        -4061: "ISOLATED_BALANCE_INSUFFICIENT - 격리 잔고 부족",
        -4062: "ISOLATED_BALANCE_TRANSFER_FAILED - 격리 잔고 이체 실패",
        -4063: "USER_UNIVERSAL_TRANSFER_FAILED - 사용자 범용 이체 실패",
        -4064: "INSUFFICIENT_MARGIN_LEVEL - 마진 레벨 부족",
        -4065: "COLLATERAL_REPAY_FAILED - 담보 상환 실패",
        -4066: "CROSS_COLLATERAL_REPAY_FAILED - 교차 담보 상환 실패",
        -4067: "COLLATERAL_REPAY_INPUT_PARAMETER_ERROR - 담보 상환 입력 매개변수 오류",
        -4068: "COLLATERAL_CALCULATE_FAILED - 담보 계산 실패",
        -4069: "INSUFFICIENT_COLLATERAL - 담보 부족",
        -4070: "INVALID_COLLATERAL_AMOUNT - 담보 금액이 올바르지 않습니다",
        -4071: "OPEN_ORDER_EXISTS - 열린 주문이 존재합니다",
        -4072: "QUANTITY_NOT_SUPPORT_BORROWING - 수량이 차용을 지원하지 않습니다",
        -4073: "AMOUNT_NOT_SUPPORT_BORROWING - 금액이 차용을 지원하지 않습니다",
        -4074: "BORROW_AMOUNT_NOT_SUPPORT - 차용 금액을 지원하지 않습니다",
        -4075: "CROSS_MARGIN_ACCOUNT_INFO_FAILED - 교차 마진 계좌 정보 실패",
        -4076: "CROSS_MARGIN_ACCOUNT_TRANSFER_FAILED - 교차 마진 계좌 이체 실패",
        -4077: "MAX_LEVERAGE_RATIO - 최대 레버리지 비율",
        -4078: "INVALID_MARGIN_LEVEL_FOR_NEW_ORDER - 새 주문에 대한 마진 레벨이 올바르지 않습니다",
        -4079: "CROSS_MARGIN_INSUFFICIENT_BALANCE - 교차 마진 잔고 부족",
        -4080: "ISOLATED_MARGIN_INSUFFICIENT_BALANCE - 격리 마진 잔고 부족",
        -4081: "ISOLATED_MARGIN_ACCOUNT_INFO_FAILED - 격리 마진 계좌 정보 실패",
        -4082: "ISOLATED_MARGIN_ACCOUNT_TRANSFER_FAILED - 격리 마진 계좌 이체 실패",
        -4083: "NEGATIVE_INTEREST_RATE - 음의 이자율",
        -4084: "TRANSFER_NOT_SUPPORT_SELL_MARKET - 이체는 판매 시장을 지원하지 않습니다",
        -4085: "TRANSFER_OUT_NOT_SUPPORT_MARKET_ORDER - 이체 출금은 시장가 주문을 지원하지 않습니다",
        -4086: "TRANSFER_IN_NOT_SUPPORT_MARKET_ORDER - 이체 입금은 시장가 주문을 지원하지 않습니다",
        -4087: "MAX_POSITION_LEVERAGE - 최대 포지션 레버리지",
        -4088: "MIN_POSITION_LEVERAGE - 최소 포지션 레버리지",
        -4089: "ISOLATED_LONG_LEVERAGE_REJECT - 격리 롱 레버리지 거부",
        -4090: "ISOLATED_SHORT_LEVERAGE_REJECT - 격리 숏 레버리지 거부",
        -4091: "POSITION_NOT_EXISTS - 포지션이 존재하지 않습니다",
        -4092: "INVALID_SYMBOL_STATUS - 심볼 상태가 올바르지 않습니다",
        -4093: "UNDERWEIGHT_POSITION - 포지션 비중 부족",
        -4094: "OVER_WEIGHT_POSITION - 포지션 비중 초과",
        -4095: "POSITION_SIDE_CHANGE_EXISTS_QUANTITY - 포지션 사이드 변경 시 수량이 존재합니다",
        -4096: "TOGGLE_ORDER_CANNOT_BE_PLACED - 토글 주문을 배치할 수 없습니다",
        -4097: "ADL_WILL_TRIGGER - ADL이 트리거됩니다",
        -4098: "POSITIONS_SIZE_OVER - 포지션 크기 초과",
        -4099: "REDUCE_ONLY_ORDER_PERMISSION - 축소 전용 주문 권한",
        -4100: "POSITION_CANNOT_BE_ZERO - 포지션은 0이 될 수 없습니다",
        -4101: "REDUCE_PRECISION_NOT_SUPPORTED - 정밀도 감소는 지원되지 않습니다",
        -4102: "TIF_NOT_SUPPORTED - TIF는 지원되지 않습니다",
        -4103: "REDUCE_ONLY_ORDER_TYPE_NOT_SUPPORTED - 축소 전용 주문 타입은 지원되지 않습니다",
        -4104: "USER_IN_LIQUIDATION - 사용자가 청산 중입니다",
        -4105: "POSITION_NOT_SUFFICIENT - 포지션이 충분하지 않습니다",
        -4106: "INVALID_MARGIN_MODE - 마진 모드가 올바르지 않습니다",
        -4107: "AUTO_LEVERAGE - 자동 레버리지",
        -4108: "AUTO_DELEVER - 자동 디레버리지",
        -4109: "LIQUIDATION_ORDER_CREATION_FAILED - 청산 주문 생성 실패",
        -4110: "LIQUIDATION_ORDER_CANCELLATION_FAILED - 청산 주문 취소 실패",
        -4111: "PNL_CALCULATION_FAILED - PNL 계산 실패",
        -4112: "ISOLATED_MARGIN_CALCULATION_FAILED - 격리 마진 계산 실패",
        -4113: "CROSS_MARGIN_CALCULATION_FAILED - 교차 마진 계산 실패",
        -4114: "INVALID_COMMISSION_CALCULATION - 수수료 계산이 올바르지 않습니다",
        -4115: "INVALID_REQUEST_DEFINITION - 요청 정의가 올바르지 않습니다",
        -4116: "INVALID_TYPE_DEFINITION - 타입 정의가 올바르지 않습니다",
        -4117: "INVALID_LIST_DEFINITION - 리스트 정의가 올바르지 않습니다",
        -4118: "INVALID_PARAMETER_SENT - 올바르지 않은 매개변수가 전송되었습니다",
        -4119: "INVALID_PERIOD_MODE - 기간 모드가 올바르지 않습니다",
        -4120: "INVALID_STICKY_MODE - 고정 모드가 올바르지 않습니다",
        -4121: "INVALID_MARKET_TAKE_BOUND - 시장 테이크 바운드가 올바르지 않습니다",
        -4122: "ORDER_PRICE_TOO_HIGH - 주문 가격이 너무 높습니다",
        -4123: "ORDER_PRICE_TOO_SMALL - 주문 가격이 너무 작습니다",
        -4124: "INVALID_ACTIVATION_PRICE - 활성화 가격이 올바르지 않습니다",
        -4125: "QUANTITY_EXISTS_WITH_CLOSE_POSITION - 포지션 종료 시 수량이 존재합니다",
        -4126: "REDUCE_ONLY_MUST_BE_TRUE - 축소 전용은 true여야 합니다",
        -4127: "ORDER_TYPE_CANNOT_BE_MKT_ON_CLOSE - 종료 시 시장가 주문 타입을 사용할 수 없습니다",
        -4128: "INVALID_OPENING_POSITION_STATUS - 포지션 열기 상태가 올바르지 않습니다",
        -4129: "SYMBOL_ALREADY_CLOSED - 심볼이 이미 닫혀 있습니다",
        -4130: "STRATEGY_INVALID_TRIGGER_PRICE - 전략의 트리거 가격이 올바르지 않습니다",
        -4131: "INVALID_PAIR - 쌍이 올바르지 않습니다",
        -4132: "PARAM_VALIDATION_FAILED - 매개변수 검증 실패",
        -4133: "PRICE_VALIDATION_FAILED - 가격 검증 실패",
        -4134: "QUANTITY_VALIDATION_FAILED - 수량 검증 실패",
        -4135: "TAKE_PROFIT_ORDER_EXISTS - 이익 실현 주문이 존재합니다",
        -4136: "STOP_LOSS_ORDER_EXISTS - 손절 주문이 존재합니다",
        -4137: "INVALID_SPLIT_NUM - 분할 번호가 올바르지 않습니다",
        -4138: "INVALID_SPLIT_QUANTITY - 분할 수량이 올바르지 않습니다",
        -4139: "DECIMAL_QUANTITY_NOT_SUPPORTED - 소수 수량은 지원되지 않습니다",
        -4140: "TIME_IN_FORCE_IOC_NOT_SUPPORTED - TIF IOC는 지원되지 않습니다",
        -4141: "TIME_IN_FORCE_FOK_NOT_SUPPORTED - TIF FOK는 지원되지 않습니다",
        -4142: "TIME_IN_FORCE_GTX_NOT_SUPPORTED - TIF GTX는 지원되지 않습니다",
        -4143: "TIME_IN_FORCE_NOT_SUPPORTED - TIF는 지원되지 않습니다",
        -4144: "INVALID_INTERVAL - 간격이 올바르지 않습니다",
        -4145: "INVALID_SYMBOL - 심볼이 올바르지 않습니다",
        -4146: "INVALID_USER_DATA_STREAM - 사용자 데이터 스트림이 올바르지 않습니다",
        -4147: "INVALID_NEW_ORDER_RESP_TYPE - 새 주문 응답 타입이 올바르지 않습니다",
        -4148: "INVALID_ORDER_TYPE - 주문 타입이 올바르지 않습니다",
        -4149: "INVALID_SIDE - 사이드가 올바르지 않습니다",
        -4150: "INVALID_POSITION_SIDE - 포지션 사이드가 올바르지 않습니다",
        -4151: "INVALID_TIME_IN_FORCE - TIF가 올바르지 않습니다",
        -4152: "INVALID_SELF_TRADE_PREVENTION_MODE - 자기 거래 방지 모드가 올바르지 않습니다",
        -4153: "INVALID_TRAILING_STOP_CALLBACK_RATE - 추적 스톱 콜백 비율이 올바르지 않습니다",
        -4154: "INVALID_ACTIVATION_PRICE - 활성화 가격이 올바르지 않습니다",
        -4155: "INVALID_CALLBACK_RATE - 콜백 비율이 올바르지 않습니다",
        -4156: "INVALID_CLOSE_POSITION - 포지션 종료가 올바르지 않습니다",
        -4157: "INVALID_WORKING_TYPE - 작업 타입이 올바르지 않습니다",
        -4158: "INVALID_PRICE_PROTECT - 가격 보호가 올바르지 않습니다",
        -4159: "INVALID_REDUCE_ONLY - 축소 전용이 올바르지 않습니다",
        -4160: "INVALID_MARGIN_BUY_BORROW_AMOUNT - 마진 매수 차용 금액이 올바르지 않습니다",
        -4161: "INVALID_MARGIN_BUY_BORROW_ASSET - 마진 매수 차용 자산이 올바르지 않습니다",
        -4162: "INVALID_INDEX_ASSET - 인덱스 자산이 올바르지 않습니다",
        -4163: "INVALID_RECV_WINDOW - 수신 윈도우가 올바르지 않습니다",
        -4164: "INVALID_TIMESTAMP - 타임스탬프가 올바르지 않습니다",
        -4165: "INVALID_LISTEN_KEY_EXPIRED - 리슨 키가 만료되었습니다",
        -4166: "INVALID_BALANCE_TYPE - 잔고 타입이 올바르지 않습니다",
        -4167: "INVALID_OCO_ORDER_TYPE - OCO 주문 타입이 올바르지 않습니다",
        -4168: "INVALID_OCO_ORDER_SIDE - OCO 주문 사이드가 올바르지 않습니다",
        -4169: "INVALID_OCO_ORDER_PRICE - OCO 주문 가격이 올바르지 않습니다",
        -4170: "INVALID_OCO_ORDER_QUANTITY - OCO 주문 수량이 올바르지 않습니다",
        -4171: "INVALID_OCO_ORDER_STOP_PRICE - OCO 주문 스톱 가격이 올바르지 않습니다",
        -4172: "INVALID_TIMESTAMP_OUTSIDE_RECV_WINDOW - 타임스탬프가 수신 윈도우 외부에 있습니다",
        -4173: "INVALID_ACTIVATION_PRICE_RANGE - 활성화 가격 범위가 올바르지 않습니다",
        -4174: "STRATEGY_INVALID_STOP_PRICE - 전략 스톱 가격이 올바르지 않습니다",
        -4175: "INVALID_PRICE_RANGE - 가격 범위가 올바르지 않습니다",
        -4176: "ISOLATED_LEVERAGE_REJECT_WITH_POSITION - 포지션이 있는 상태에서 격리 레버리지 거부",
        -4177: "MAX_LEVERAGE_RATIO_REACHED - 최대 레버리지 비율에 도달",
        -4178: "AMOUNT_MUST_BE_POSITIVE - 금액은 양수여야 합니다",
        -4179: "INVALID_API_KEY_TYPE - API 키 타입이 올바르지 않습니다",
        -4180: "INVALID_RSA_PUBLIC_KEY - RSA 공개 키가 올바르지 않습니다",
        -4181: "MAX_PRICE_HIGHTER_THAN_MULTIPLIER - 최대 가격이 배수보다 높습니다",
        -4182: "ISOLATED_LEVERAGE_REJECT_WITH_ORDERS - 주문이 있는 상태에서 격리 레버리지 거부",
        -4183: "ISOLATED_POSITION_REJECT_WITH_ORDERS - 주문이 있는 상태에서 격리 포지션 거부",
        -4184: "CROSS_POSITION_REJECT_WITH_ORDERS - 주문이 있는 상태에서 교차 포지션 거부",
        -4185: "ISOLATED_MARGIN_INSUFFICIENT_BALANCE_FOR_NEW_ORDER - 새 주문을 위한 격리 마진 잔고 부족",
        -4186: "ISOLATED_MARGIN_INSUFFICIENT_BALANCE_FOR_ORDER_AMENDMENT - 주문 수정을 위한 격리 마진 잔고 부족",
        -4187: "CROSS_MARGIN_INSUFFICIENT_BALANCE_FOR_NEW_ORDER - 새 주문을 위한 교차 마진 잔고 부족",
        -4188: "CROSS_MARGIN_INSUFFICIENT_BALANCE_FOR_ORDER_AMENDMENT - 주문 수정을 위한 교차 마진 잔고 부족",
        -4189: "INSUFFICIENT_BALANCE_FOR_LEVERAGE_ADJUSTMENT - 레버리지 조정을 위한 잔고 부족",
        -4190: "ORDERS_AND_POSITION_EXIST - 주문과 포지션이 존재합니다",
        -4191: "POSITION_EXIST - 포지션이 존재합니다",
        -4192: "CROSS_BORROW_DEBT - 교차 차용 부채",
        -4193: "ISOLATED_BORROW_DEBT - 격리 차용 부채",
        -4194: "ISOLATED_POSITION_EXIST - 격리 포지션이 존재합니다",
        -4195: "CROSS_POSITION_EXIST - 교차 포지션이 존재합니다",
        -4196: "POSITION_SIDE_CHANGE_DISABLE_WHEN_ASSET_MODE_OFF - 자산 모드가 꺼져 있을 때 포지션 사이드 변경 비활성화",
        -4197: "POSITION_SIDE_BOTH_ZERO - 양쪽 포지션 사이드가 0입니다",
        -4198: "POSITION_SIDE_LONG_ZERO - 롱 포지션 사이드가 0입니다",
        -4199: "POSITION_SIDE_SHORT_ZERO - 숏 포지션 사이드가 0입니다"
    }
    
    @classmethod
    def handle_error(cls, response):
        """에러 응답 처리"""
        try:
            error_data = response.json()
            error_code = error_data.get('code', 0)
            error_msg = error_data.get('msg', 'Unknown error')
            
            if error_code in cls.ERROR_CODES:
                detailed_msg = cls.ERROR_CODES[error_code]
                print(f"❌ Binance API Error [{error_code}]: {detailed_msg}")
                print(f"   Original message: {error_msg}")
            else:
                print(f"❌ Unknown Binance API Error [{error_code}]: {error_msg}")
                
            return {
                'error_code': error_code,
                'error_message': error_msg,
                'detailed_message': cls.ERROR_CODES.get(error_code, 'Unknown error code'),
                'is_retryable': cls._is_retryable_error(error_code)
            }
            
        except Exception as e:
            print(f"❌ Error parsing response: {e}")
            return {
                'error_code': -1,
                'error_message': str(e),
                'detailed_message': 'Failed to parse error response',
                'is_retryable': False
            }
    
    @classmethod
    def _is_retryable_error(cls, error_code):
        """재시도 가능한 에러인지 확인"""
        retryable_errors = [
            -1001,  # DISCONNECTED
            -1003,  # TOO_MANY_REQUESTS
            -1006,  # UNEXPECTED_RESP
            -1007   # TIMEOUT
        ]
        return error_code in retryable_errors

# 에러 처리를 포함한 래퍼 함수
def safe_api_call(func, max_retries=3, delay=1):
    """안전한 API 호출 래퍼"""
    
    for attempt in range(max_retries):
        try:
            response = func()
            
            if hasattr(response, 'status_code') and response.status_code != 200:
                error_info = BinanceErrorHandler.handle_error(response)
                
                if error_info['is_retryable'] and attempt < max_retries - 1:
                    print(f"🔄 재시도 {attempt + 1}/{max_retries} - {delay}초 대기")
                    time.sleep(delay)
                    delay *= 2  # 지수 백오프
                    continue
                else:
                    raise Exception(f"API call failed: {error_info['detailed_message']}")
            
            return response
            
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                print(f"⏰ 타임아웃 발생 - 재시도 {attempt + 1}/{max_retries}")
                time.sleep(delay)
                delay *= 2
                continue
            else:
                raise Exception("API call timed out after retries")
                
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                print(f"🔌 연결 오류 - 재시도 {attempt + 1}/{max_retries}")
                time.sleep(delay)
                delay *= 2
                continue
            else:
                raise Exception("Connection failed after retries")
                
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"❌ 예외 발생 - 재시도 {attempt + 1}/{max_retries}: {str(e)}")
                time.sleep(delay)
                delay *= 2
                continue
            else:
                raise e
    
    raise Exception("Max retries exceeded")

# 사용 예시
def robust_place_order(api, symbol, side, order_type, quantity, **kwargs):
    """견고한 주문 생성"""
    
    def order_call():
        return api.place_order(symbol, side, order_type, quantity, **kwargs)
    
    try:
        result = safe_api_call(order_call, max_retries=3, delay=1)
        print(f"✅ 주문 성공: {result}")
        return result
    except Exception as e:
        print(f"❌ 주문 실패: {e}")
        return None
```

### 📊 Rate Limiting 관리

```python
import time
from collections import deque
from threading import Lock

class RateLimiter:
    """Binance API Rate Limiting 관리"""
    
    def __init__(self):
        # Binance Futures API 제한
        self.limits = {
            'weight': {
                'limit': 2400,      # 1분당 Weight 제한
                'window': 60,       # 윈도우 크기 (초)
                'requests': deque() # 요청 기록
            },
            'orders': {
                'limit': 300,       # 1분당 주문 제한
                'window': 60,
                'requests': deque()
            },
            'raw_requests': {
                'limit': 6000,      # 5분당 Raw Request 제한
                'window': 300,
                'requests': deque()
            }
        }
        self.lock = Lock()
    
    def check_rate_limit(self, request_type='weight', weight=1):
        """레이트 리미트 확인 및 대기"""
        
        with self.lock:
            now = time.time()
            limit_info = self.limits[request_type]
            
            # 오래된 요청 기록 정리
            while (limit_info['requests'] and 
                   now - limit_info['requests'][0] > limit_info['window']):
                limit_info['requests'].popleft()
            
            # 현재 사용량 계산
            current_usage = len(limit_info['requests'])
            
            # 제한 확인
            if current_usage + weight > limit_info['limit']:
                # 대기 시간 계산
                oldest_request = limit_info['requests'][0]
                wait_time = limit_info['window'] - (now - oldest_request) + 1
                
                print(f"⏳ Rate limit reached. Waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
                
                # 재귀 호출로 다시 확인
                return self.check_rate_limit(request_type, weight)
            
            # 요청 기록 추가
            for _ in range(weight):
                limit_info['requests'].append(now)
            
            return True
    
    def get_remaining_requests(self, request_type='weight'):
        """남은 요청 수 확인"""
        
        with self.lock:
            now = time.time()
            limit_info = self.limits[request_type]
            
            # 오래된 요청 기록 정리
            while (limit_info['requests'] and 
                   now - limit_info['requests'][0] > limit_info['window']):
                limit_info['requests'].popleft()
            
            current_usage = len(limit_info['requests'])
            remaining = limit_info['limit'] - current_usage
            
            return {
                'remaining': remaining,
                'total': limit_info['limit'],
                'usage_percent': (current_usage / limit_info['limit']) * 100,
                'reset_time': (limit_info['requests'][0] + limit_info['window']) if limit_info['requests'] else now
            }

# Rate Limiter 적용 API 클래스
class RateLimitedBinanceFuturesAPI(BinanceFuturesAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rate_limiter = RateLimiter()
    
    def place_order_with_limit(self, *args, **kwargs):
        """레이트 리미터가 적용된 주문 생성"""
        
        # 주문 API는 Weight 10, Orders 1
        self.rate_limiter.check_rate_limit('weight', 10)
        self.rate_limiter.check_rate_limit('orders', 1)
        
        return self.place_order(*args, **kwargs)
    
    def get_positions_with_limit(self, *args, **kwargs):
        """레이트 리미터가 적용된 포지션 조회"""
        
        # 포지션 조회는 Weight 5
        self.rate_limiter.check_rate_limit('weight', 5)
        
        return self.get_positions(*args, **kwargs)
    
    def show_rate_limit_status(self):
        """현재 레이트 리미트 상태 표시"""
        
        weight_info = self.rate_limiter.get_remaining_requests('weight')
        orders_info = self.rate_limiter.get_remaining_requests('orders')
        
        print(f"📊 Rate Limit Status:")
        print(f"  Weight: {weight_info['remaining']}/{weight_info['total']} ({weight_info['usage_percent']:.1f}%)")
        print(f"  Orders: {orders_info['remaining']}/{orders_info['total']} ({orders_info['usage_percent']:.1f}%)")

# 사용 예시
api = RateLimitedBinanceFuturesAPI(api_key, api_secret, testnet=True)

# 안전한 대량 주문 처리
for i in range(50):
    try:
        api.place_order_with_limit('BTCUSDT', 'BUY', 'LIMIT', 0.001, 50000)
        print(f"주문 {i+1} 완료")
        
        # 주기적으로 레이트 리미트 상태 확인
        if i % 10 == 0:
            api.show_rate_limit_status()
            
    except Exception as e:
        print(f"주문 {i+1} 실패: {e}")
```

---

## 🛡️ 보안 및 베스트 프랙티스

### 🔐 API Key 보안

```python
import os
from cryptography.fernet import Fernet
import json
import base64

class SecureAPIManager:
    """안전한 API 키 관리"""
    
    def __init__(self, key_file='api_keys.enc'):
        self.key_file = key_file
        self.encryption_key = None
        
    def generate_encryption_key(self):
        """암호화 키 생성"""
        key = Fernet.generate_key()
        with open('.encryption_key', 'wb') as f:
            f.write(key)
        print("🔑 암호화 키가 생성되었습니다. '.encryption_key' 파일을 안전하게 보관하세요.")
        return key
    
    def load_encryption_key(self):
        """암호화 키 로드"""
        try:
            with open('.encryption_key', 'rb') as f:
                return f.read()
        except FileNotFoundError:
            print("❌ 암호화 키 파일이 없습니다. 새로 생성합니다.")
            return self.generate_encryption_key()
    
    def encrypt_api_keys(self, api_key, api_secret, environment='testnet'):
        """API 키 암호화 저장"""
        
        if not self.encryption_key:
            self.encryption_key = self.load_encryption_key()
        
        fernet = Fernet(self.encryption_key)
        
        credentials = {
            'api_key': api_key,
            'api_secret': api_secret,
            'environment': environment,
            'created_at': time.time()
        }
        
        # JSON을 바이트로 변환 후 암호화
        json_bytes = json.dumps(credentials).encode()
        encrypted_data = fernet.encrypt(json_bytes)
        
        # 파일에 저장
        with open(self.key_file, 'wb') as f:
            f.write(encrypted_data)
        
        print(f"🔒 API 키가 암호화되어 {self.key_file}에 저장되었습니다.")
    
    def decrypt_api_keys(self):
        """API 키 복호화"""
        
        if not self.encryption_key:
            self.encryption_key = self.load_encryption_key()
        
        try:
            fernet = Fernet(self.encryption_key)
            
            with open(self.key_file, 'rb') as f:
                encrypted_data = f.read()
            
            # 복호화
            decrypted_bytes = fernet.decrypt(encrypted_data)
            credentials = json.loads(decrypted_bytes.decode())
            
            return credentials
            
        except FileNotFoundError:
            print(f"❌ {self.key_file} 파일을 찾을 수 없습니다.")
            return None
        except Exception as e:
            print(f"❌ API 키 복호화 실패: {e}")
            return None
    
    def create_secure_api_instance(self):
        """안전한 API 인스턴스 생성"""
        
        credentials = self.decrypt_api_keys()
        if not credentials:
            print("❌ API 키를 로드할 수 없습니다.")
            return None
        
        api = BinanceFuturesAPI(
            credentials['api_key'],
            credentials['api_secret'],
            testnet=(credentials['environment'] == 'testnet')
        )
        
        print(f"✅ {credentials['environment']} API 인스턴스 생성 완료")
        return api

# 환경 변수 사용 (권장)
class EnvironmentAPIManager:
    """환경 변수를 통한 API 키 관리"""
    
    @staticmethod
    def setup_environment():
        """환경 변수 설정 가이드"""
        print("📋 환경 변수 설정 방법:")
        print("1. Linux/Mac:")
        print("   export BINANCE_FUTURES_API_KEY='your_api_key'")
        print("   export BINANCE_FUTURES_API_SECRET='your_api_secret'")
        print("   export BINANCE_FUTURES_TESTNET='true'")
        print()
        print("2. Windows:")
        print("   set BINANCE_FUTURES_API_KEY=your_api_key")
        print("   set BINANCE_FUTURES_API_SECRET=your_api_secret")
        print("   set BINANCE_FUTURES_TESTNET=true")
        print()
        print("3. .env 파일 (python-dotenv 사용):")
        print("   BINANCE_FUTURES_API_KEY=your_api_key")
        print("   BINANCE_FUTURES_API_SECRET=your_api_secret")
        print("   BINANCE_FUTURES_TESTNET=true")
    
    @staticmethod
    def create_api_from_env():
        """환경 변수에서 API 인스턴스 생성"""
        
        api_key = os.getenv('BINANCE_FUTURES_API_KEY')
        api_secret = os.getenv('BINANCE_FUTURES_API_SECRET')
        testnet = os.getenv('BINANCE_FUTURES_TESTNET', 'true').lower() == 'true'
        
        if not api_key or not api_secret:
            print("❌ 환경 변수에서 API 키를 찾을 수 없습니다.")
            EnvironmentAPIManager.setup_environment()
            return None
        
        # API 키 마스킹 출력
        masked_key = api_key[:8] + '*' * (len(api_key) - 16) + api_key[-8:]
        print(f"✅ API 키 로드 완료: {masked_key}")
        
        return BinanceFuturesAPI(api_key, api_secret, testnet)

# 사용 예시
if __name__ == "__main__":
    # 방법 1: 암호화된 파일 사용
    secure_manager = SecureAPIManager()
    
    # 최초 설정 (한 번만 실행)
    # secure_manager.encrypt_api_keys('your_api_key', 'your_api_secret', 'testnet')
    
    # API 인스턴스 생성
    api = secure_manager.create_secure_api_instance()
    
    # 방법 2: 환경 변수 사용 (권장)
    # api = EnvironmentAPIManager.create_api_from_env()
```

### 🔒 추가 보안 조치

```python
import ipaddress
import socket
import ssl
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class SecureBinanceSession:
    """보안 강화된 Binance API 세션"""
    
    def __init__(self, timeout=30, verify_ssl=True):
        self.session = requests.Session()
        self.timeout = timeout
        
        # SSL 인증서 검증 강화
        if verify_ssl:
            self.session.verify = True
            
        # 재시도 정책 설정
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "DELETE", "PUT"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 기본 헤더 설정
        self.session.headers.update({
            'User-Agent': 'BinanceFuturesBot/1.0',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
    
    def validate_binance_ssl(self, hostname):
        """Binance SSL 인증서 검증"""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((hostname, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
            # 인증서 정보 검증
            subject = dict(x[0] for x in cert['subject'])
            issuer = dict(x[0] for x in cert['issuer'])
            
            print(f"✅ SSL 인증서 검증 완료:")
            print(f"  Subject: {subject.get('commonName', 'N/A')}")
            print(f"  Issuer: {issuer.get('organizationName', 'N/A')}")
            
            return True
            
        except Exception as e:
            print(f"❌ SSL 인증서 검증 실패: {e}")
            return False
    
    def check_ip_whitelist(self, allowed_ips=None):
        """IP 화이트리스트 확인"""
        if not allowed_ips:
            return True
            
        try:
            # 현재 공용 IP 조회
            response = self.session.get('https://api.ipify.org', timeout=5)
            current_ip = response.text.strip()
            
            # IP 범위 확인
            current_ip_obj = ipaddress.ip_address(current_ip)
            
            for allowed_ip in allowed_ips:
                try:
                    if current_ip_obj in ipaddress.ip_network(allowed_ip, strict=False):
                        print(f"✅ IP 검증 통과: {current_ip}")
                        return True
                except ValueError:
                    if current_ip == allowed_ip:
                        print(f"✅ IP 검증 통과: {current_ip}")
                        return True
            
            print(f"❌ IP 검증 실패: {current_ip} (허용된 IP가 아님)")
            return False
            
        except Exception as e:
            print(f"❌ IP 확인 실패: {e}")
            return False
    
    def make_secure_request(self, method, url, **kwargs):
        """보안 강화 요청"""
        
        # 타임아웃 설정
        kwargs.setdefault('timeout', self.timeout)
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            # 응답 검증
            if response.status_code == 200:
                # Content-Type 검증
                if 'application/json' not in response.headers.get('content-type', ''):
                    print("⚠️ 응답이 JSON 형식이 아닙니다")
                
                return response
            else:
                print(f"❌ HTTP 에러: {response.status_code}")
                return response
                
        except requests.exceptions.SSLError as e:
            print(f"❌ SSL 에러: {e}")
            raise
        except requests.exceptions.Timeout as e:
            print(f"❌ 타임아웃: {e}")
            raise
        except requests.exceptions.ConnectionError as e:
            print(f"❌ 연결 에러: {e}")
            raise

# 보안 강화된 API 클래스
class SecureBinanceFuturesAPI(BinanceFuturesAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.secure_session = SecureBinanceSession()
        
        # 보안 검증
        hostname = 'fapi.binance.com' if not kwargs.get('testnet') else 'testnet.binancefuture.com'
        self.secure_session.validate_binance_ssl(hostname)
    
    def secure_api_call(self, method, endpoint, params=None, **kwargs):
        """보안 강화된 API 호출"""
        
        url = f"{self.base_url}{endpoint}"
        
        if params:
            # 파라미터 검증
            self._validate_parameters(params)
            
            if method.upper() in ['POST', 'PUT', 'DELETE']:
                kwargs['data'] = params
            else:
                kwargs['params'] = params
        
        return self.secure_session.make_secure_request(method, url, **kwargs)
    
    def _validate_parameters(self, params):
        """API 파라미터 검증"""
        
        dangerous_chars = ['<', '>', '"', "'", '&', '\n', '\r', '\t']
        
        for key, value in params.items():
            if isinstance(value, str):
                for char in dangerous_chars:
                    if char in value:
                        print(f"⚠️ 위험한 문자 감지: {key} = {value}")
                        params[key] = value.replace(char, '')
    
    def audit_log(self, action, params=None, result=None):
        """API 호출 감사 로그"""
        
        log_entry = {
            'timestamp': time.time(),
            'action': action,
            'params': params,
            'success': result is not None,
            'ip_address': self._get_current_ip()
        }
        
        # 로그 파일에 기록
        with open('api_audit.log', 'a') as f:
            f.write(f"{json.dumps(log_entry)}\n")
    
    def _get_current_ip(self):
        """현재 IP 주소 조회"""
        try:
            response = requests.get('https://api.ipify.org', timeout=5)
            return response.text.strip()
        except:
            return 'unknown'

# 사용 예시
def create_production_ready_api():
    """프로덕션 환경용 API 인스턴스 생성"""
    
    # 환경 변수에서 설정 로드
    api_key = os.getenv('BINANCE_FUTURES_API_KEY')
    api_secret = os.getenv('BINANCE_FUTURES_API_SECRET')
    
    if not api_key or not api_secret:
        raise ValueError("API 키가 환경 변수에 설정되지 않았습니다")
    
    # 보안 강화된 API 인스턴스
    api = SecureBinanceFuturesAPI(api_key, api_secret, testnet=False)
    
    # IP 화이트리스트 확인 (선택사항)
    allowed_ips = ['203.0.113.0/24', '198.51.100.1']  # 예시 IP
    if not api.secure_session.check_ip_whitelist(allowed_ips):
        raise SecurityError("IP 주소가 화이트리스트에 없습니다")
    
    print("🔒 프로덕션 환경 API 준비 완료")
    return api
```

---

## 📋 전체 API 엔드포인트 체크리스트

### ✅ General Information (2/2)

- [x] **General Info** - 거래소 기본 정보
- [x] **Change Log** - API 변경 사항 추적

### ✅ Market Data Endpoints (25/25)

**핵심 데이터:**
- [x] **Test Connectivity** - 연결 테스트
- [x] **Check Server Time** - 서버 시간 확인
- [x] **Exchange Information** - 거래소 정보
- [x] **Order Book** - 오더북 조회
- [x] **Recent Trades List** - 최근 거래 내역
- [x] **Kline/Candlestick Data** - 캔들스틱 데이터
- [x] **24hr Ticker Price Change Statistics** - 24시간 통계
- [x] **Symbol Price Ticker** - 심볼별 가격
- [x] **Symbol Order Book Ticker** - 심볼별 오더북 정보

**선물 특화 데이터:**
- [x] **Mark Price** - 마크 가격
- [x] **Get Funding Rate History** - 자금조달료 히스토리
- [x] **Open Interest** - 미결제약정
- [x] **Open Interest Statistics** - 미결제약정 통계
- [x] **Top Trader Long/Short Ratio (Accounts)** - 상위 트레이더 비율
- [x] **Top Trader Long/Short Ratio (Positions)** - 상위 포지션 비율
- [x] **Long/Short Ratio** - 롱/숏 비율
- [x] **Taker Buy/Sell Volume** - 테이커 거래량

**기타 데이터:**
- [x] **Old Trade Lookup** - 과거 거래 조회
- [x] **Compressed/Aggregate Trades List** - 통합 거래 데이터
- [x] **Continuous Contract Kline/Candlestick Data** - 연속 계약 캔들
- [x] **Index Price Kline/Candlestick Data** - 인덱스 가격 캔들
- [x] **Mark Price Kline/Candlestick Data** - 마크 가격 캔들
- [x] **Basis** - 베이시스 데이터
- [x] **Composite Index Symbol Information** - 복합 인덱스 정보

### ✅ Account/Trade Endpoints (24/24)

**주문 관리:**
- [x] **New Order** - 신규 주문
- [x] **Place Multiple Orders** - 다중 주문
- [x] **Query Order** - 주문 조회
- [x] **Cancel Order** - 주문 취소
- [x] **Cancel All Open Orders** - 전체 주문 취소
- [x] **Cancel Multiple Orders** - 다중 주문 취소
- [x] **Auto-Cancel All Open Orders** - 자동 전체 취소
- [x] **Query Current Open Order** - 현재 열린 주문 조회
- [x] **Current All Open Orders** - 모든 열린 주문
- [x] **All Orders** - 전체 주문 히스토리

**계좌 관리:**
- [x] **Futures Account Balance** - 선물 계좌 잔고
- [x] **Account Information** - 계좌 정보
- [x] **Position Information** - 포지션 정보
- [x] **Account Trade List** - 계좌 거래 내역
- [x] **Get Income History** - 수익 히스토리

**레버리지 & 마진:**
- [x] **Change Initial Leverage** - 초기 레버리지 변경
- [x] **Change Margin Type** - 마진 타입 변경
- [x] **Modify Isolated Position Margin** - 격리 마진 조정
- [x] **Get Position Margin Change History** - 마진 변경 히스토리
- [x] **Leverage Bracket** - 레버리지 브래킷

**기타:**
- [x] **User's Force Orders** - 사용자 강제 주문
- [x] **Position ADL Quantile Estimation** - ADL 정량 추정
- [x] **Trading Status** - 거래 상태

### ✅ WebSocket Market Streams (14/14)

**기본 스트림:**
- [x] **Live Subscribing/Unsubscribing** - 실시간 구독 관리
- [x] **Aggregate Trade Streams** - 통합 거래 스트림
- [x] **Trade Streams** - 개별 거래 스트림
- [x] **Kline/Candlestick Streams** - 캔들스틱 스트림
- [x] **Continuous Contract Kline/Candlestick Streams** - 연속 계약 캔들 스트림

**티커 스트림:**
- [x] **Individual Symbol Mini Ticker Stream** - 개별 심볼 미니 티커
- [x] **All Market Mini Tickers Stream** - 전체 시장 미니 티커
- [x] **Individual Symbol Ticker Streams** - 개별 심볼 티커
- [x] **All Market Tickers Stream** - 전체 시장 티커

**오더북 스트림:**
- [x] **Individual Symbol Book Ticker Streams** - 개별 심볼 북 티커
- [x] **All Book Tickers Stream** - 전체 북 티커
- [x] **Partial Book Depth Streams** - 부분 오더북 깊이
- [x] **Diff. Depth Stream** - 차분 깊이 스트림

### ✅ User Data Streams (7/7)

**스트림 관리:**
- [x] **Start User Data Stream** - 사용자 데이터 스트림 시작
- [x] **Keepalive User Data Stream** - 스트림 연결 유지
- [x] **Close User Data Stream** - 스트림 종료

**이벤트 처리:**
- [x] **Event: Account Update** - 계좌 업데이트 이벤트
- [x] **Event: Order Update** - 주문 업데이트 이벤트
- [x] **Event: Account Config Update** - 계좌 설정 업데이트 이벤트

---

## 🚀 실전 사용 시나리오

### 📊 시나리오 1: 실시간 시장 모니터링 시스템

```python
import asyncio
import pandas as pd
from datetime import datetime, timedelta

class MarketMonitoringSystem:
    """실시간 시장 모니터링 시스템"""
    
    def __init__(self, api_instance):
        self.api = api_instance
        self.symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT']
        self.alerts = []
        self.market_data = {}
        
    async def start_monitoring(self):
        """모니터링 시작"""
        
        # 1. 기본 시장 데이터 로드
        await self.load_initial_data()
        
        # 2. 실시간 스트림 시작
        tasks = [
            self.monitor_price_changes(),
            self.monitor_funding_rates(),
            self.monitor_open_interest(),
            self.monitor_long_short_ratios(),
            self.generate_alerts()
        ]
        
        await asyncio.gather(*tasks)
    
    async def load_initial_data(self):
        """초기 데이터 로드"""
        
        print("📊 초기 시장 데이터 로딩...")
        
        for symbol in self.symbols:
            # 24시간 통계
            ticker = self.api.get_24hr_ticker(symbol)
            
            # 자금조달료
            funding = self.api.get_mark_price_and_funding(symbol)
            
            # 미결제약정
            oi = self.api.get_open_interest(symbol)
            
            # 롱/숏 비율
            ls_ratio = self.api.get_long_short_ratio(symbol, '1h')
            
            self.market_data[symbol] = {
                'price': ticker['last_price'],
                'change_24h': ticker['price_change_percent'],
                'volume_24h': ticker['volume'],
                'funding_rate': funding['funding_rate'],
                'next_funding': funding['next_funding_time'],
                'open_interest': oi['open_interest'],
                'long_short_ratio': ls_ratio['current_ratio'],
                'last_update': datetime.now()
            }
            
            print(f"  {symbol}: ${ticker['last_price']:,.2f} ({ticker['price_change_percent']:+.2f}%)")
    
    async def monitor_price_changes(self):
        """가격 변동 모니터링"""
        
        # WebSocket으로 실시간 가격 추적
        from binance import AsyncClient, BinanceSocketManager
        
        client = AsyncClient()
        bm = BinanceSocketManager(client)
        
        # 전체 티커 스트림
        ts = bm.ticker_socket()
        
        async with ts as tscm:
            while True:
                res = await tscm.recv()
                
                symbol = res['symbol']
                if symbol in self.symbols:
                    price = float(res['curDayClose'])
                    change = float(res['priceChangePercent'])
                    
                    # 급격한 변동 감지
                    if abs(change) > 5:  # 5% 이상 변동
                        await self.add_alert({
                            'type': 'PRICE_ALERT',
                            'symbol': symbol,
                            'price': price,
                            'change': change,
                            'message': f"{symbol} 급변동: {change:+.2f}%"
                        })
                    
                    # 데이터 업데이트
                    if symbol in self.market_data:
                        self.market_data[symbol]['price'] = price
                        self.market_data[symbol]['change_24h'] = change
                        self.market_data[symbol]['last_update'] = datetime.now()
    
    async def monitor_funding_rates(self):
        """자금조달료 모니터링"""
        
        while True:
            for symbol in self.symbols:
                try:
                    funding = self.api.get_mark_price_and_funding(symbol)
                    rate = funding['funding_rate']
                    
                    # 높은 자금조달료 감지
                    if abs(rate) > 0.01:  # 1% 이상
                        await self.add_alert({
                            'type': 'FUNDING_ALERT',
                            'symbol': symbol,
                            'rate': rate,
                            'message': f"{symbol} 높은 자금조달료: {rate:.4f} ({rate*100:.2f}%)"
                        })
                    
                    # 데이터 업데이트
                    if symbol in self.market_data:
                        self.market_data[symbol]['funding_rate'] = rate
                        self.market_data[symbol]['next_funding'] = funding['next_funding_time']
                
                except Exception as e:
                    print(f"자금조달료 모니터링 오류 ({symbol}): {e}")
            
            await asyncio.sleep(300)  # 5분마다 확인
    
    async def monitor_open_interest(self):
        """미결제약정 모니터링"""
        
        while True:
            for symbol in self.symbols:
                try:
                    oi = self.api.get_open_interest(symbol)
                    current_oi = oi['open_interest']
                    
                    # 이전 데이터와 비교
                    if symbol in self.market_data:
                        prev_oi = self.market_data[symbol]['open_interest']
                        oi_change = (current_oi - prev_oi) / prev_oi * 100
                        
                        # 큰 변동 감지
                        if abs(oi_change) > 10:  # 10% 이상 변동
                            await self.add_alert({
                                'type': 'OI_ALERT',
                                'symbol': symbol,
                                'oi': current_oi,
                                'change': oi_change,
                                'message': f"{symbol} 미결제약정 변동: {oi_change:+.1f}%"
                            })
                        
                        self.market_data[symbol]['open_interest'] = current_oi
                
                except Exception as e:
                    print(f"미결제약정 모니터링 오류 ({symbol}): {e}")
            
            await asyncio.sleep(600)  # 10분마다 확인
    
    async def monitor_long_short_ratios(self):
        """롱/숏 비율 모니터링"""
        
        while True:
            for symbol in self.symbols:
                try:
                    ls_data = self.api.get_long_short_ratio(symbol, '1h')
                    ratio = ls_data['current_ratio']
                    
                    # 극단적인 비율 감지
                    if ratio > 3 or ratio < 0.33:  # 3:1 또는 1:3 비율
                        direction = "롱 우세" if ratio > 3 else "숏 우세"
                        await self.add_alert({
                            'type': 'RATIO_ALERT',
                            'symbol': symbol,
                            'ratio': ratio,
                            'message': f"{symbol} 극단적 롱/숏 비율: {ratio:.2f} ({direction})"
                        })
                    
                    # 데이터 업데이트
                    if symbol in self.market_data:
                        self.market_data[symbol]['long_short_ratio'] = ratio
                
                except Exception as e:
                    print(f"롱/숏 비율 모니터링 오류 ({symbol}): {e}")
            
            await asyncio.sleep(900)  # 15분마다 확인
    
    async def add_alert(self, alert_data):
        """알림 추가"""
        
        alert_data['timestamp'] = datetime.now()
        self.alerts.append(alert_data)
        
        # 콘솔 출력
        print(f"🚨 {alert_data['timestamp'].strftime('%H:%M:%S')} - {alert_data['message']}")
        
        # 알림 개수 제한 (최근 100개만 보관)
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
    
    async def generate_alerts(self):
        """종합 알림 생성"""
        
        while True:
            await asyncio.sleep(3600)  # 1시간마다
            
            # 시장 요약 생성
            summary = self.generate_market_summary()
            
            await self.add_alert({
                'type': 'MARKET_SUMMARY',
                'message': f"시장 요약: {summary}"
            })
    
    def generate_market_summary(self):
        """시장 요약 생성"""
        
        total_symbols = len(self.symbols)
        positive_change = sum(1 for data in self.market_data.values() if data['change_24h'] > 0)
        
        avg_funding = sum(data['funding_rate'] for data in self.market_data.values()) / total_symbols
        
        return f"{positive_change}/{total_symbols} 상승, 평균 자금조달료: {avg_funding:.4f}"
    
    def get_market_dashboard(self):
        """시장 대시보드 데이터"""
        
        dashboard = {}
        for symbol, data in self.market_data.items():
            dashboard[symbol] = {
                '현재가': f"${data['price']:,.2f}",
                '24h 변동': f"{data['change_24h']:+.2f}%",
                '거래량': f"{data['volume_24h']:,.0f}",
                '자금조달료': f"{data['funding_rate']:.4f}",
                '미결제약정': f"{data['open_interest']:,.0f}",
                '롱/숏': f"{data['long_short_ratio']:.2f}",
                '업데이트': data['last_update'].strftime('%H:%M:%S')
            }
        
        return dashboard

# 사용 예시
async def run_market_monitoring():
    api = BinanceFuturesAPI(api_key, api_secret, testnet=True)
    
    monitor = MarketMonitoringSystem(api)
    
    print("🚀 시장 모니터링 시스템 시작...")
    await monitor.start_monitoring()

# asyncio.run(run_market_monitoring())
```

### 🤖 시나리오 2: 자동 거래 봇

```python
class AutoTradingBot:
    """자동 거래 봇"""
    
    def __init__(self, api_instance, strategy_config):
        self.api = api_instance
        self.config = strategy_config
        self.positions = {}
        self.orders = {}
        self.is_running = False
        
    async def start_trading(self):
        """자동 거래 시작"""
        
        self.is_running = True
        print("🤖 자동 거래 봇 시작...")
        
        # 초기 포지션 로드
        await self.load_positions()
        
        # 거래 루프 시작
        tasks = [
            self.trading_loop(),
            self.risk_management_loop(),
            self.user_event_handler()
        ]
        
        await asyncio.gather(*tasks)
    
    async def trading_loop(self):
        """메인 거래 루프"""
        
        while self.is_running:
            try:
                for symbol in self.config['symbols']:
                    await self.analyze_and_trade(symbol)
                
                await asyncio.sleep(self.config['check_interval'])
                
            except Exception as e:
                print(f"거래 루프 오류: {e}")
                await asyncio.sleep(60)
    
    async def analyze_and_trade(self, symbol):
        """심볼 분석 및 거래"""
        
        # 시장 데이터 수집
        market_data = await self.collect_market_data(symbol)
        
        # 거래 신호 생성
        signal = self.generate_signal(symbol, market_data)
        
        # 신호에 따른 거래 실행
        if signal['action'] != 'HOLD':
            await self.execute_trade(symbol, signal)
    
    async def collect_market_data(self, symbol):
        """시장 데이터 수집"""
        
        # 캔들 데이터
        klines = self.api.get_klines(symbol, '15m', 50)
        df = pd.DataFrame(klines)
        
        # 기술적 지표 계산
        df['sma_20'] = df['close'].rolling(20).mean()
        df['sma_50'] = df['close'].rolling(50).mean()
        df['rsi'] = self.calculate_rsi(df['close'], 14)
        
        # 자금조달료
        funding = self.api.get_mark_price_and_funding(symbol)
        
        # 롱/숏 비율
        ls_ratio = self.api.get_long_short_ratio(symbol, '1h')
        
        return {
            'price_data': df,
            'current_price': df['close'].iloc[-1],
            'sma_20': df['sma_20'].iloc[-1],
            'sma_50': df['sma_50'].iloc[-1],
            'rsi': df['rsi'].iloc[-1],
            'funding_rate': funding['funding_rate'],
            'long_short_ratio': ls_ratio['current_ratio']
        }
    
    def generate_signal(self, symbol, data):
        """거래 신호 생성"""
        
        signal = {'action': 'HOLD', 'side': None, 'confidence': 0}
        
        # 현재 포지션 확인
        current_position = self.positions.get(symbol, {'side': None, 'size': 0})
        
        # 기술적 분석 기반 신호
        if data['rsi'] < 30 and data['current_price'] > data['sma_20']:
            # RSI 과매도 + 가격이 SMA20 위에 있음 = 매수 신호
            if current_position['side'] != 'LONG':
                signal = {
                    'action': 'BUY',
                    'side': 'LONG',
                    'confidence': 0.7,
                    'reason': 'RSI oversold + price above SMA20'
                }
        
        elif data['rsi'] > 70 and data['current_price'] < data['sma_20']:
            # RSI 과매수 + 가격이 SMA20 아래 있음 = 매도 신호
            if current_position['side'] != 'SHORT':
                signal = {
                    'action': 'SELL',
                    'side': 'SHORT',
                    'confidence': 0.7,
                    'reason': 'RSI overbought + price below SMA20'
                }
        
        # 자금조달료 고려
        if abs(data['funding_rate']) > 0.01:  # 1% 이상
            if data['funding_rate'] > 0:  # 양수 = 롱이 숏에게 지급
                # 숏 포지션 선호
                if signal['side'] == 'SHORT':
                    signal['confidence'] += 0.2
            else:  # 음수 = 숏이 롱에게 지급
                # 롱 포지션 선호
                if signal['side'] == 'LONG':
                    signal['confidence'] += 0.2
        
        # 롱/숏 비율 고려 (반대 방향 신호)
        if data['long_short_ratio'] > 2:  # 롱 과다
            if signal['side'] == 'SHORT':
                signal['confidence'] += 0.1
        elif data['long_short_ratio'] < 0.5:  # 숏 과다
            if signal['side'] == 'LONG':
                signal['confidence'] += 0.1
        
        return signal
    
    async def execute_trade(self, symbol, signal):
        """거래 실행"""
        
        if signal['confidence'] < self.config['min_confidence']:
            return
        
        try:
            # 포지션 크기 계산
            position_size = self.calculate_position_size(symbol, signal)
            
            # 기존 포지션 확인
            current_position = self.positions.get(symbol, {'side': None, 'size': 0})
            
            # 포지션 변경이 필요한 경우
            if current_position['side'] != signal['side']:
                # 기존 포지션 청산
                if current_position['size'] > 0:
                    await self.close_position(symbol)
                
                # 새 포지션 진입
                await self.open_position(symbol, signal['side'], position_size)
            
            print(f"📈 {symbol} {signal['action']} 신호 실행: {signal['reason']} (신뢰도: {signal['confidence']:.1f})")
            
        except Exception as e:
            print(f"❌ 거래 실행 실패 ({symbol}): {e}")
    
    def calculate_position_size(self, symbol, signal):
        """포지션 크기 계산"""
        
        # 계좌 잔고의 일정 비율 사용
        account = self.api.get_account_info()
        available_balance = account['available_balance']
        
        # 리스크 비율 (신뢰도에 따라 조정)
        risk_ratio = self.config['base_risk_ratio'] * signal['confidence']
        
        # 최대 포지션 크기 제한
        max_position_value = available_balance * risk_ratio
        
        # 심볼별 최소 주문 크기 고려
        min_qty = self.get_min_quantity(symbol)
        
        # 현재 가격 기준 수량 계산
        current_price = self.api.get_24hr_ticker(symbol)['last_price']
        quantity = max_position_value / current_price
        
        # 최소 수량 이상으로 조정
        quantity = max(quantity, min_qty)
        
        return round(quantity, 6)  # 소수점 6자리까지
    
    async def open_position(self, symbol, side, quantity):
        """포지션 진입"""
        
        try:
            order_side = 'BUY' if side == 'LONG' else 'SELL'
            
            # 시장가 주문으로 진입
            order = self.api.place_order(
                symbol=symbol,
                side=order_side,
                order_type='MARKET',
                quantity=quantity
            )
            
            # 포지션 정보 업데이트
            self.positions[symbol] = {
                'side': side,
                'size': quantity,
                'entry_price': float(order.get('avgPrice', 0)),
                'entry_time': datetime.now(),
                'order_id': order['orderId']
            }
            
            print(f"✅ {symbol} {side} 포지션 진입: {quantity} @ ${order.get('avgPrice', 'N/A')}")
            
            # 스톱로스 및 이익실현 주문 설정
            await self.set_stop_loss_take_profit(symbol)
            
        except Exception as e:
            print(f"❌ 포지션 진입 실패 ({symbol}): {e}")
    
    async def close_position(self, symbol):
        """포지션 청산"""
        
        position = self.positions.get(symbol)
        if not position or position['size'] == 0:
            return
        
        try:
            # 반대 방향 시장가 주문
            close_side = 'SELL' if position['side'] == 'LONG' else 'BUY'
            
            order = self.api.place_order(
                symbol=symbol,
                side=close_side,
                order_type='MARKET',
                quantity=position['size'],
                reduce_only=True
            )
            
            # 손익 계산
            exit_price = float(order.get('avgPrice', 0))
            pnl = self.calculate_pnl(position, exit_price)
            
            print(f"🔄 {symbol} 포지션 청산: ${exit_price} (PnL: {pnl:+.2f} USDT)")
            
            # 포지션 정보 삭제
            del self.positions[symbol]
            
        except Exception as e:
            print(f"❌ 포지션 청산 실패 ({symbol}): {e}")
    
    async def set_stop_loss_take_profit(self, symbol):
        """스톱로스 및 이익실현 설정"""
        
        position = self.positions.get(symbol)
        if not position:
            return
        
        entry_price = position['entry_price']
        side = position['side']
        
        # 스톱로스 가격 (2% 손실)
        if side == 'LONG':
            stop_price = entry_price * 0.98  # 2% 하락
            tp_price = entry_price * 1.04    # 4% 상승
        else:  # SHORT
            stop_price = entry_price * 1.02  # 2% 상승
            tp_price = entry_price * 0.96    # 4% 하락
        
        try:
            # 스톱로스 주문
            stop_side = 'SELL' if side == 'LONG' else 'BUY'
            stop_order = self.api.place_order(
                symbol=symbol,
                side=stop_side,
                order_type='STOP_MARKET',
                quantity=position['size'],
                stop_price=stop_price,
                reduce_only=True
            )
            
            # 이익실현 주문
            tp_order = self.api.place_order(
                symbol=symbol,
                side=stop_side,
                order_type='LIMIT',
                quantity=position['size'],
                price=tp_price,
                reduce_only=True
            )
            
            # 주문 ID 저장
            self.orders[symbol] = {
                'stop_loss': stop_order['orderId'],
                'take_profit': tp_order['orderId']
            }
            
            print(f"🛡️ {symbol} 보호 주문 설정: SL ${stop_price:.2f}, TP ${tp_price:.2f}")
            
        except Exception as e:
            print(f"❌ 보호 주문 설정 실패 ({symbol}): {e}")
    
    async def risk_management_loop(self):
        """리스크 관리 루프"""
        
        while self.is_running:
            try:
                await self.check_account_risk()
                await self.check_position_risk()
                await asyncio.sleep(30)  # 30초마다 확인
                
            except Exception as e:
                print(f"리스크 관리 오류: {e}")
                await asyncio.sleep(60)
    
    async def check_account_risk(self):
        """계좌 리스크 확인"""
        
        account = self.api.get_account_info()
        
        # 총 미실현 손익 확인
        total_unrealized_pnl = account['total_unrealized_pnl']
        total_balance = account['total_wallet_balance']
        
        pnl_ratio = total_unrealized_pnl / total_balance if total_balance > 0 else 0
        
        # 큰 손실 시 모든 포지션 청산
        if pnl_ratio < -0.1:  # 10% 이상 손실
            print(f"🚨 큰 손실 감지: {pnl_ratio:.2%} - 모든 포지션 청산")
            await self.emergency_close_all()
    
    async def emergency_close_all(self):
        """긴급 전체 포지션 청산"""
        
        print("🚨 긴급 청산 실행...")
        
        # 모든 주문 취소
        for symbol in self.positions.keys():
            try:
                self.api.cancel_all_orders(symbol)
            except:
                pass
        
        # 모든 포지션 청산
        for symbol in list(self.positions.keys()):
            await self.close_position(symbol)
        
        # 봇 중지
        self.is_running = False
        print("🛑 자동 거래 봇 중지됨")
    
    def calculate_rsi(self, prices, period=14):
        """RSI 계산"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def calculate_pnl(self, position, exit_price):
        """손익 계산"""
        entry_price = position['entry_price']
        size = position['size']
        
        if position['side'] == 'LONG':
            return (exit_price - entry_price) * size
        else:  # SHORT
            return (entry_price - exit_price) * size

# 봇 설정 예시
bot_config = {
    'symbols': ['BTCUSDT', 'ETHUSDT'],
    'check_interval': 60,  # 60초마다 확인
    'min_confidence': 0.6,  # 최소 신뢰도 60%
    'base_risk_ratio': 0.02,  # 기본 리스크 2%
    'max_positions': 3  # 최대 3개 포지션
}

# 봇 실행 예시
async def run_trading_bot():
    api = BinanceFuturesAPI(api_key, api_secret, testnet=True)
    
    bot = AutoTradingBot(api, bot_config)
    await bot.start_trading()

# asyncio.run(run_trading_bot())
```

---

## 🎓 학습 리소스 및 다음 단계

### 📚 추천 학습 순서

1. **기초 이해** (1-2일)
   - [README_FUTURES.md](README_FUTURES.md) - 프로젝트 전체 개요
   - 본 API 참조 문서의 인증 및 기본 설정 섹션

2. **실습 준비** (1일)
   - Binance Testnet 계정 생성
   - API 키 발급 및 보안 설정
   - 기본 API 호출 테스트

3. **단계별 구현** (3-5일)
   - [02_FUTURES_AGENTIC_CODING_GUIDE.md](02_FUTURES_AGENTIC_CODING_GUIDE.md) - 10단계 Phase 구조
   - Phase 1-3: 환경 설정 및 기본 API 연동
   - Phase 4-6: 전략 구현 및 백테스팅

4. **고급 활용** (1-2주)
   - [07_LEVERAGE_RISK_MANAGEMENT.md](07_LEVERAGE_RISK_MANAGEMENT.md) - 레버리지 리스크 관리
   - [08_FUNDING_RATE_STRATEGY.md](08_FUNDING_RATE_STRATEGY.md) - 자금조달료 수익 전략

### 🔗 유용한 외부 리소스

**공식 문서:**
- [Binance Futures API 공식 문서](https://binance-docs.github.io/apidocs/futures/en/)
- [CCXT 라이브러리 문서](https://docs.ccxt.com/en/latest/)
- [Freqtrade 공식 문서](https://www.freqtrade.io/en/stable/)

**커뮤니티:**
- [Binance API Telegram](https://t.me/binance_api_english)
- [Freqtrade Discord](https://discord.gg/p7nuUNVfP7)
- [CCXT GitHub](https://github.com/ccxt/ccxt)

### ⚡ 빠른 시작 체크리스트

- [ ] Binance Testnet 계정 생성
- [ ] API 키 발급 (Futures Trading 권한)
- [ ] Python 환경 설정 (3.9+)
- [ ] 필수 라이브러리 설치 (`pip install ccxt freqtrade requests`)
- [ ] 기본 API 호출 테스트
- [ ] 계좌 정보 조회 성공
- [ ] 첫 번째 테스트 주문 실행

### 🚨 주의사항

**⚠️ 실거래 전 필수 확인사항:**
1. **충분한 테스트**: 최소 1개월 테스트넷 운영
2. **리스크 관리**: 손실 허용 한도 명확히 설정
3. **자금 관리**: 전체 자금의 5-10%만 선물거래에 할당
4. **레버리지 주의**: 초보자는 2-3배 이하 권장
5. **감정적 거래 금지**: 시스템적 접근 유지

**🔐 보안 주의사항:**
1. API 키 노출 금지
2. 출금 권한 비활성화
3. IP 제한 설정 권장
4. 2FA 인증 필수
5. 정기적인 API 키 갱신

---

<div align="center">

## 🎉 축하합니다! 🎉

**Binance Futures API 72개 엔드포인트 완전 정복을 완료하셨습니다!**

이제 선물거래의 모든 기능을 활용하여 전문적인 자동매매 시스템을 구축할 수 있습니다.

[![Next Step](https://img.shields.io/badge/Next%20Step-🛠️%20실전%20구현-success?style=for-the-badge&logo=rocket)](02_FUTURES_AGENTIC_CODING_GUIDE.md)

**📧 문의사항이나 도움이 필요하시면 언제든 연락주세요!**

</div>