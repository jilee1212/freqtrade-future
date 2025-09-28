#!/usr/bin/env python3
"""
Binance Futures Testnet API 연결 테스트
"""

import ccxt
import json
from datetime import datetime

def test_binance_futures_testnet():
    """Binance Futures Testnet API 연결 및 기본 정보 테스트"""

    # API 키 설정
    api_key = "16sriPIRmf6AE4AHdNP2N6vSaymm3VHMGm4oJ9gGmrf4GcxhaaG0NG59vF632JaJ"
    secret_key = "tk4XVhMB5AOH6Q3YSwLHetKy97TwdmkfiQRB0gkvCLqeqQyZ1RhwkcVfbz6WxFHt"

    # Exchange 객체 생성
    exchange = ccxt.binance({
        'apiKey': api_key,
        'secret': secret_key,
        'sandbox': True,
        'options': {
            'defaultType': 'future'  # futures 모드 활성화
        },
        'enableRateLimit': True,
    })

    print("Binance Futures Testnet API connection test starting...")
    print(f"Current time: {datetime.now()}")
    print("-" * 50)

    try:
        # 1. 서버 시간 확인
        print("1. Checking server time...")
        server_time = exchange.fetch_time()
        print(f"   SUCCESS: Server time: {datetime.fromtimestamp(server_time/1000)}")

        # 2. 계좌 정보 확인
        print("\n2. Checking account information...")
        balance = exchange.fetch_balance()
        print(f"   SUCCESS: Account loaded successfully")
        print(f"   USDT Balance: {balance.get('USDT', {}).get('total', 0)}")

        # 3. 마켓 정보 확인
        print("\n3. Loading market information...")
        markets = exchange.load_markets()

        # USDT Perpetual 페어 찾기
        futures_pairs = []
        for symbol, market in markets.items():
            if (market.get('type') == 'swap' and
                market.get('quote') == 'USDT' and
                market.get('active') == True):
                futures_pairs.append(symbol)

        print(f"   SUCCESS: Total futures pairs found: {len(futures_pairs)}")
        print(f"   First 10 pairs: {futures_pairs[:10]}")

        # 4. 틱커 정보 테스트
        if futures_pairs:
            test_pair = futures_pairs[0]  # 첫 번째 페어로 테스트
            print(f"\n4. Testing ticker information ({test_pair})...")
            ticker = exchange.fetch_ticker(test_pair)
            print(f"   SUCCESS: Current price: {ticker['last']}")
            print(f"   24h change: {ticker['percentage']}%")

        # 5. 포지션 정보 확인
        print("\n5. Checking position information...")
        positions = exchange.fetch_positions()
        active_positions = [pos for pos in positions if float(pos['contracts']) != 0]
        print(f"   SUCCESS: Total positions: {len(positions)}")
        print(f"   Active positions: {len(active_positions)}")

        print("\n" + "="*50)
        print("SUCCESS: All tests passed! API connection is working properly.")
        print("READY: Can be used with Freqtrade.")

        # 권장 페어 출력
        print(f"\nRecommended FUTURES pairs (top 5):")
        for i, pair in enumerate(futures_pairs[:5], 1):
            print(f"   {i}. {pair}")

        return True, futures_pairs[:5]

    except Exception as e:
        print(f"\nERROR: API connection failed: {str(e)}")
        print("Troubleshooting steps:")
        print("   1. Check if API keys are correct")
        print("   2. Verify Futures Trading permission is enabled in Testnet")
        print("   3. Check internet connection")
        return False, []

if __name__ == "__main__":
    success, recommended_pairs = test_binance_futures_testnet()

    if success and recommended_pairs:
        print(f"\nTIP: Pairs to add to config_futures.json:")
        print(json.dumps(recommended_pairs, indent=2))