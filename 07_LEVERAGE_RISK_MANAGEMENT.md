    ], index=['BTC', 'ETH', 'ADA'], columns=['BTC', 'ETH', 'ADA'])
    
    # 주요 시나리오 테스트
    test_scenarios = ['covid_crash_2020', 'luna_ust_collapse_2022', 'black_swan_extreme']
    
    for scenario_name in test_scenarios:
        print(f"🔄 {scenario_name} 테스트 중...")
        result = stress_tester.simulate_crash_scenario(
            scenario_name, portfolio_positions, correlation_matrix
        )
        print("✅ 완료\n")
    
    # 종합 보고서 생성
    report = stress_tester.generate_stress_test_report(test_scenarios)
    print(report)
    
    # 최악 시나리오 분석
    print("\n🎯 최악 시나리오 분석:")
    worst_scenario = None
    worst_loss = 0
    
    for scenario_name in test_scenarios:
        result = stress_tester.test_results[scenario_name]
        portfolio_loss = abs(result['portfolio_impact']['portfolio_return'])
        
        if portfolio_loss > worst_loss:
            worst_loss = portfolio_loss
            worst_scenario = scenario_name
    
    if worst_scenario:
        print(f"최악 시나리오: {worst_scenario}")
        print(f"예상 최대 손실: {worst_loss:.1%}")
        
        worst_result = stress_tester.test_results[worst_scenario]
        safe_leverage = worst_result['survival_analysis']['safe_max_leverage']
        print(f"권장 최대 레버리지: {safe_leverage}x")

# 실행
run_comprehensive_stress_test()
```

---

## 🤖 **자동화 리스크 시스템**

### 📱 **실시간 리스크 모니터링 봇**

24시간 무중단으로 리스크를 모니터링하고 자동으로 대응하는 시스템입니다.

```python
# user_data/strategies/modules/risk_automation.py
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Optional
import logging
from dataclasses import dataclass, asdict

@dataclass
class RiskAlert:
    """리스크 알림 데이터 클래스"""
    timestamp: datetime
    alert_type: str  # WARNING, CRITICAL, EMERGENCY
    symbol: str
    metric: str
    current_value: float
    threshold: float
    message: str
    suggested_action: str
    priority: int  # 1-10 (10이 최고 우선순위)

class RealTimeRiskMonitor:
    """실시간 리스크 모니터링 시스템"""
    
    def __init__(self, exchange, config: Dict):
        self.exchange = exchange
        self.config = config
        self.is_running = False
        self.alert_history = []
        self.risk_thresholds = self._initialize_thresholds()
        self.notification_handlers = []
        
        # 로깅 설정
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _initialize_thresholds(self) -> Dict[str, Dict]:
        """리스크 임계값 초기화"""
        
        return {
            'portfolio_var': {
                'warning': 0.02,    # 2% VaR
                'critical': 0.05,   # 5% VaR
                'emergency': 0.10   # 10% VaR
            },
            'margin_ratio': {
                'warning': 0.7,     # 70% 마진 사용
                'critical': 0.8,    # 80% 마진 사용
                'emergency': 0.9    # 90% 마진 사용
            },
            'liquidation_distance': {
                'warning': 0.2,     # 20% 청산 거리
                'critical': 0.1,    # 10% 청산 거리
                'emergency': 0.05   # 5% 청산 거리
            },
            'portfolio_drawdown': {
                'warning': 0.1,     # 10% 낙폭
                'critical': 0.15,   # 15% 낙폭
                'emergency': 0.2    # 20% 낙폭
            },
            'correlation_spike': {
                'warning': 0.8,     # 80% 상관관계
                'critical': 0.9,    # 90% 상관관계
                'emergency': 0.95   # 95% 상관관계
            }
        }
    
    def add_notification_handler(self, handler: Callable):
        """알림 핸들러 추가"""
        self.notification_handlers.append(handler)
    
    async def start_monitoring(self, check_interval: int = 30):
        """모니터링 시작"""
        
        self.is_running = True
        self.logger.info("🤖 실시간 리스크 모니터링 시작")
        
        while self.is_running:
            try:
                await self._perform_risk_check()
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                self.logger.error(f"❌ 모니터링 오류: {e}")
                await asyncio.sleep(check_interval)
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.is_running = False
        self.logger.info("🛑 리스크 모니터링 중지")
    
    async def _perform_risk_check(self):
        """리스크 점검 수행"""
        
        # 1. 포지션 정보 수집
        positions = await self._get_current_positions()
        
        if not positions:
            return
        
        # 2. 계좌 정보 수집
        account_info = await self._get_account_info()
        
        # 3. 시장 데이터 수집
        market_data = await self._get_market_data([pos['symbol'] for pos in positions])
        
        # 4. 리스크 메트릭스 계산
        risk_metrics = await self._calculate_risk_metrics(positions, account_info, market_data)
        
        # 5. 알림 생성 및 발송
        alerts = self._generate_alerts(risk_metrics)
        
        for alert in alerts:
            await self._send_alert(alert)
    
    async def _get_current_positions(self) -> List[Dict]:
        """현재 포지션 조회"""
        
        try:
            positions = self.exchange._api.futures_position_information()
            active_positions = []
            
            for pos in positions:
                if float(pos['positionAmt']) != 0:
                    active_positions.append({
                        'symbol': pos['symbol'],
                        'side': 'LONG' if float(pos['positionAmt']) > 0 else 'SHORT',
                        'size': abs(float(pos['positionAmt'])),
                        'notional': abs(float(pos['notional'])),
                        'entry_price': float(pos['entryPrice']),
                        'mark_price': float(pos['markPrice']),
                        'liquidation_price': float(pos['liquidationPrice']) if pos['liquidationPrice'] != '0' else None,
                        'unrealized_pnl': float(pos['unRealizedProfit']),
                        'leverage': int(pos.get('leverage', 1)),
                        'margin_type': pos.get('marginType', 'isolated')
                    })
            
            return active_positions
            
        except Exception as e:
            self.logger.error(f"❌ 포지션 조회 실패: {e}")
            return []
    
    async def _get_account_info(self) -> Dict:
        """계좌 정보 조회"""
        
        try:
            account = self.exchange._api.futures_account()
            
            return {
                'total_wallet_balance': float(account['totalWalletBalance']),
                'total_unrealized_profit': float(account['totalUnrealizedProfit']),
                'total_margin_balance': float(account['totalMarginBalance']),
                'total_maint_margin': float(account['totalMaintMargin']),
                'total_initial_margin': float(account['totalInitialMargin']),
                'available_balance': float(account['availableBalance']),
                'max_withdraw_amount': float(account['maxWithdrawAmount'])
            }
            
        except Exception as e:
            self.logger.error(f"❌ 계좌 정보 조회 실패: {e}")
            return {}
    
    async def _get_market_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """시장 데이터 조회"""
        
        market_data = {}
        
        try:
            for symbol in symbols:
                # 24시간 통계
                ticker = self.exchange._api.futures_ticker_24hr_price_change(symbol=symbol)
                
                # 자금 조달 수수료
                funding_rate = self.exchange._api.futures_funding_rate(symbol=symbol, limit=1)
                
                # 호가창 정보
                orderbook = self.exchange._api.futures_order_book(symbol=symbol, limit=10)
                
                market_data[symbol] = {
                    'price': float(ticker['lastPrice']),
                    'price_change_24h': float(ticker['priceChangePercent']),
                    'volume_24h': float(ticker['volume']),
                    'funding_rate': float(funding_rate[0]['fundingRate']) if funding_rate else 0,
                    'bid_price': float(orderbook['bids'][0][0]) if orderbook['bids'] else 0,
                    'ask_price': float(orderbook['asks'][0][0]) if orderbook['asks'] else 0,
                    'spread': 0  # 계산 후 업데이트
                }
                
                # 스프레드 계산
                if market_data[symbol]['bid_price'] and market_data[symbol]['ask_price']:
                    spread = (market_data[symbol]['ask_price'] - market_data[symbol]['bid_price']) / market_data[symbol]['bid_price']
                    market_data[symbol]['spread'] = spread
                
        except Exception as e:
            self.logger.error(f"❌ 시장 데이터 조회 실패: {e}")
        
        return market_data
    
    async def _calculate_risk_metrics(self, positions: List[Dict], 
                                    account_info: Dict, 
                                    market_data: Dict[str, Dict]) -> Dict:
        """리스크 메트릭스 계산"""
        
        risk_metrics = {}
        
        # 1. 포트폴리오 VaR
        portfolio_var = self._calculate_portfolio_var(positions, market_data)
        risk_metrics['portfolio_var'] = portfolio_var
        
        # 2. 마진 비율
        if account_info:
            margin_ratio = account_info['total_maint_margin'] / account_info['total_margin_balance'] if account_info['total_margin_balance'] > 0 else 0
            risk_metrics['margin_ratio'] = margin_ratio
        
        # 3. 청산 거리
        liquidation_distances = {}
        for pos in positions:
            if pos['liquidation_price']:
                distance = abs(pos['mark_price'] - pos['liquidation_price']) / pos['mark_price']
                liquidation_distances[pos['symbol']] = distance
        
        risk_metrics['liquidation_distances'] = liquidation_distances
        risk_metrics['min_liquidation_distance'] = min(liquidation_distances.values()) if liquidation_distances else 1.0
        
        # 4. 포트폴리오 낙폭
        total_unrealized_pnl = sum(pos['unrealized_pnl'] for pos in positions)
        total_notional = sum(pos['notional'] for pos in positions)
        portfolio_drawdown = abs(total_unrealized_pnl) / total_notional if total_notional > 0 and total_unrealized_pnl < 0 else 0
        risk_metrics['portfolio_drawdown'] = portfolio_drawdown
        
        # 5. 레버리지 분포
        leverages = [pos['leverage'] for pos in positions]
        risk_metrics['avg_leverage'] = sum(leverages) / len(leverages) if leverages else 0
        risk_metrics['max_leverage'] = max(leverages) if leverages else 0
        
        # 6. 상관관계 리스크 (간단한 근사)
        if len(positions) > 1:
            # 가격 변동률 기반 상관관계 추정
            price_changes = [market_data.get(pos['symbol'], {}).get('price_change_24h', 0) for pos in positions]
            correlation_risk = np.corrcoef(price_changes)[0, 1] if len(price_changes) >= 2 else 0
            risk_metrics['correlation_risk'] = abs(correlation_risk)
        
        return risk_metrics
    
    def _calculate_portfolio_var(self, positions: List[Dict], 
                               market_data: Dict[str, Dict]) -> float:
        """포트폴리오 VaR 계산 (간단한 방법)"""
        
        if not positions:
            return 0
        
        # 각 포지션의 일일 VaR 추정
        total_var = 0
        
        for pos in positions:
            symbol = pos['symbol']
            if symbol in market_data:
                # 변동성 추정 (24시간 가격변동률 기반)
                volatility = abs(market_data[symbol]['price_change_24h']) / 100
                
                # 포지션 가치
                position_value = pos['notional']
                
                # 레버리지 고려
                leverage = pos['leverage']
                
                # VaR 계산 (95% 신뢰구간, 정규분포 가정)
                position_var = position_value * volatility * leverage * 1.65
                total_var += position_var ** 2  # 분산 합계
        
        # 포트폴리오 VaR (분산의 제곱근)
        portfolio_var = np.sqrt(total_var)
        
        # 총 포트폴리오 가치 대비 비율
        total_portfolio_value = sum(pos['notional'] for pos in positions)
        var_ratio = portfolio_var / total_portfolio_value if total_portfolio_value > 0 else 0
        
        return var_ratio
    
    def _generate_alerts(self, risk_metrics: Dict) -> List[RiskAlert]:
        """알림 생성"""
        
        alerts = []
        current_time = datetime.now()
        
        # 1. 포트폴리오 VaR 알림
        portfolio_var = risk_metrics.get('portfolio_var', 0)
        var_thresholds = self.risk_thresholds['portfolio_var']
        
        if portfolio_var >= var_thresholds['emergency']:
            alerts.append(RiskAlert(
                timestamp=current_time,
                alert_type='EMERGENCY',
                symbol='PORTFOLIO',
                metric='VaR',
                current_value=portfolio_var,
                threshold=var_thresholds['emergency'],
                message=f"포트폴리오 VaR 위험 수준: {portfolio_var:.2%}",
                suggested_action="즉시 포지션 축소 필요",
                priority=10
            ))
        elif portfolio_var >= var_thresholds['critical']:
            alerts.append(RiskAlert(
                timestamp=current_time,
                alert_type='CRITICAL',
                symbol='PORTFOLIO',
                metric='VaR',
                current_value=portfolio_var,
                threshold=var_thresholds['critical'],
                message=f"포트폴리오 VaR 경고: {portfolio_var:.2%}",
                suggested_action="포지션 크기 재검토 권장",
                priority=7
            ))
        
        # 2. 마진 비율 알림
        margin_ratio = risk_metrics.get('margin_ratio', 0)
        margin_thresholds = self.risk_thresholds['margin_ratio']
        
        if margin_ratio >= margin_thresholds['emergency']:
            alerts.append(RiskAlert(
                timestamp=current_time,
                alert_type='EMERGENCY',
                symbol='PORTFOLIO',
                metric='Margin Ratio',
                current_value=margin_ratio,
                threshold=margin_thresholds['emergency'],
                message=f"마진 비율 위험: {margin_ratio:.1%}",
                suggested_action="즉시 마진 추가 또는 포지션 축소",
                priority=9
            ))
        
        # 3. 청산 거리 알림
        min_liquidation_distance = risk_metrics.get('min_liquidation_distance', 1.0)
        liq_thresholds = self.risk_thresholds['liquidation_distance']
        
        if min_liquidation_distance <= liq_thresholds['emergency']:
            alerts.append(RiskAlert(
                timestamp=current_time,
                alert_type='EMERGENCY',
                symbol='PORTFOLIO',
                metric='Liquidation Distance',
                current_value=min_liquidation_distance,
                threshold=liq_thresholds['emergency'],
                message=f"청산 위험 임박: {min_liquidation_distance:.1%}",
                suggested_action="긴급 포지션 축소 또는 마진 추가",
                priority=10
            ))
        
        # 4. 포트폴리오 낙폭 알림
        portfolio_drawdown = risk_metrics.get('portfolio_drawdown', 0)
        dd_thresholds = self.risk_thresholds['portfolio_drawdown']
        
        if portfolio_drawdown >= dd_thresholds['critical']:
            alerts.append(RiskAlert(
                timestamp=current_time,
                alert_type='CRITICAL',
                symbol='PORTFOLIO',
                metric='Drawdown',
                current_value=portfolio_drawdown,
                threshold=dd_thresholds['critical'],
                message=f"포트폴리오 낙폭: {portfolio_drawdown:.1%}",
                suggested_action="손절매 전략 재검토",
                priority=6
            ))
        
        # 5. 높은 레버리지 알림
        max_leverage = risk_metrics.get('max_leverage', 0)
        if max_leverage > 10:
            alerts.append(RiskAlert(
                timestamp=current_time,
                alert_type='WARNING',
                symbol='PORTFOLIO',
                metric='Max Leverage',
                current_value=max_leverage,
                threshold=10,
                message=f"높은 레버리지 감지: {max_leverage}x",
                suggested_action="레버리지 감소 고려",
                priority=4
            ))
        
        return alerts
    
    async def _send_alert(self, alert: RiskAlert):
        """알림 발송"""
        
        # 중복 알림 방지 (같은 메트릭에 대해 5분 이내 재알림 방지)
        recent_alerts = [a for a in self.alert_history if 
                        a.metric == alert.metric and 
                        (alert.timestamp - a.timestamp).total_seconds() < 300]
        
        if recent_alerts:
            return
        
        # 알림 이력에 추가
        self.alert_history.append(alert)
        
        # 이력 정리 (24시간 이상 된 알림 제거)
        cutoff_time = alert.timestamp - timedelta(hours=24)
        self.alert_history = [a for a in self.alert_history if a.timestamp > cutoff_time]
        
        # 로그 기록
        self.logger.warning(f"🚨 {alert.alert_type}: {alert.message}")
        
        # 알림 핸들러 실행
        for handler in self.notification_handlers:
            try:
                await handler(alert)
            except Exception as e:
                self.logger.error(f"❌ 알림 핸들러 오류: {e}")

# 텔레그램 알림 핸들러
class TelegramNotificationHandler:
    """텔레그램 알림 핸들러"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
    
    async def __call__(self, alert: RiskAlert):
        """알림 발송"""
        
        # 알림 타입별 이모지
        emoji_map = {
            'EMERGENCY': '🚨',
            'CRITICAL': '⚠️',
            'WARNING': '💛'
        }
        
        emoji = emoji_map.get(alert.alert_type, '📊')
        
        message = f"""
{emoji} **{alert.alert_type} ALERT**

📈 **Symbol**: {alert.symbol}
📊 **Metric**: {alert.metric}
📉 **Current**: {alert.current_value:.2%} 
🎯 **Threshold**: {alert.threshold:.2%}
⏰ **Time**: {alert.timestamp.strftime('%H:%M:%S')}

💡 **Action**: {alert.suggested_action}

*Priority: {alert.priority}/10*
        """
        
        await self._send_telegram_message(message)
    
    async def _send_telegram_message(self, message: str):
        """텔레그램 메시지 발송"""
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/sendMessage"
                payload = {
                    'chat_id': self.chat_id,
                    'text': message,
                    'parse_mode': 'Markdown'
                }
                
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        print("📱 텔레그램 알림 전송 완료")
                    else:
                        print(f"❌ 텔레그램 전송 실패: {response.status}")
                        
        except Exception as e:
            print(f"❌ 텔레그램 오류: {e}")

# 슬랙 알림 핸들러
class SlackNotificationHandler:
    """슬랙 알림 핸들러"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def __call__(self, alert: RiskAlert):
        """알림 발송"""
        
        # 알림 타입별 색상
        color_map = {
            'EMERGENCY': '#FF0000',  # 빨강
            'CRITICAL': '#FFA500',   # 주황
            'WARNING': '#FFFF00'     # 노랑
        }
        
        color = color_map.get(alert.alert_type, '#808080')
        
        payload = {
            'attachments': [{
                'color': color,
                'title': f'{alert.alert_type} Risk Alert',
                'fields': [
                    {'title': 'Symbol', 'value': alert.symbol, 'short': True},
                    {'title': 'Metric', 'value': alert.metric, 'short': True},
                    {'title': 'Current Value', 'value': f'{alert.current_value:.2%}', 'short': True},
                    {'title': 'Threshold', 'value': f'{alert.threshold:.2%}', 'short': True},
                    {'title': 'Suggested Action', 'value': alert.suggested_action, 'short': False}
                ],
                'timestamp': alert.timestamp.timestamp()
            }]
        }
        
        await self._send_slack_message(payload)
    
    async def _send_slack_message(self, payload: Dict):
        """슬랙 메시지 발송"""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status == 200:
                        print("📱 슬랙 알림 전송 완료")
                    else:
                        print(f"❌ 슬랙 전송 실패: {response.status}")
                        
        except Exception as e:
            print(f"❌ 슬랙 오류: {e}")

# 자동 대응 시스템
class AutomatedResponseSystem:
    """자동 대응 시스템"""
    
    def __init__(self, exchange, risk_monitor: RealTimeRiskMonitor):
        self.exchange = exchange
        self.risk_monitor = risk_monitor
        self.auto_actions_enabled = False
        self.action_history = []
        
    def enable_auto_actions(self, confirmation_required: bool = True):
        """자동 대응 활성화"""
        
        if confirmation_required:
            confirm = input("⚠️ 자동 대응을 활성화하시겠습니까? (y/N): ")
            if confirm.lower() != 'y':
                print("❌ 자동 대응 활성화 취소")
                return
        
        self.auto_actions_enabled = True
        print("✅ 자동 대응 시스템 활성화")
        
        # 알림 핸들러로 등록
        self.risk_monitor.add_notification_handler(self._handle_emergency_alert)
    
    async def _handle_emergency_alert(self, alert: RiskAlert):
        """긴급 알림 자동 처리"""
        
        if not self.auto_actions_enabled:
            return
        
        if alert.alert_type != 'EMERGENCY':
            return
        
        # 긴급 상황별 자동 대응
        if alert.metric == 'Liquidation Distance':
            await self._emergency_position_reduction(alert)
        elif alert.metric == 'Margin Ratio':
            await self._emergency_margin_management(alert)
        elif alert.metric == 'VaR':
            await self._emergency_risk_reduction(alert)
    
    async def _emergency_position_reduction(self, alert: RiskAlert):
        """긴급 포지션 축소"""
        
        try:
            print(f"🚨 긴급 포지션 축소 실행: {alert.symbol}")
            
            # 현재 포지션 조회
            positions = await self.risk_monitor._get_current_positions()
            
            for position in positions:
                # 청산 위험이 높은 포지션 50% 축소
                liquidation_distance = abs(position['mark_price'] - position['liquidation_price']) / position['mark_price']
                
                if liquidation_distance < 0.05:  # 5% 이내
                    reduce_size = position['size'] * 0.5
                    side = 'sell' if position['side'] == 'LONG' else 'buy'
                    
                    order = self.exchange.create_market_order(
                        symbol=position['symbol'],
                        side=side,
                        amount=reduce_size,
                        params={'reduceOnly': True}
                    )
                    
                    self.action_history.append({
                        'timestamp': datetime.now(),
                        'action': 'EMERGENCY_POSITION_REDUCTION',
                        'symbol': position['symbol'],
                        'original_size': position['size'],
                        'reduced_size': reduce_size,
                        'order_id': order['id']
                    })
                    
                    print(f"✅ {position['symbol']} 50% 축소 완료")
                    
        except Exception as e:
            print(f"❌ 긴급 포지션 축소 실패: {e}")
    
    async def _emergency_margin_management(self, alert: RiskAlert):
        """긴급 마진 관리"""
        
        print("🚨 긴급 마진 관리 - 수동 개입 필요")
        print("   권장 조치: 마진 추가 또는 포지션 축소")
        # 실제 구현에서는 사전 설정된 마진 추가 로직 실행
    
    async def _emergency_risk_reduction(self, alert: RiskAlert):
        """긴급 리스크 감소"""
        
        try:
            print("🚨 긴급 리스크 감소 - 전체 포지션 25% 축소")
            
            positions = await self.risk_monitor._get_current_positions()
            
            for position in positions:
                reduce_size = position['size'] * 0.25
                side = 'sell' if position['side'] == 'LONG' else 'buy'
                
                order = self.exchange.create_market_order(
                    symbol=position['symbol'],
                    side=side,
                    amount=reduce_size,
                    params={'reduceOnly': True}
                )
                
                self.action_history.append({
                    'timestamp': datetime.now(),
                    'action': 'EMERGENCY_RISK_REDUCTION',
                    'symbol': position['symbol'],
                    'reduction_percentage': 0.25,
                    'order_id': order['id']
                })
                
                print(f"✅ {position['symbol']} 25% 축소 완료")
                
        except Exception as e:
            print(f"❌ 긴급 리스크 감소 실패: {e}")

# 실전 사용 예제
async def demonstrate_automated_risk_system():
    """자동화 리스크 시스템 실증"""
    
    print("🤖 자동화 리스크 시스템 데모\n")
    
    # Mock 거래소 (실제로는 ccxt 객체 사용)
    class MockExchange:
        class _api:
            @staticmethod
            def futures_position_information():
                return [{
                    'symbol': 'BTCUSDT',
                    'positionAmt': '0.1',
                    'notional': '5000',
                    'entryPrice': '50000',
                    'markPrice': '48000',
                    'liquidationPrice': '45000',
                    'unRealizedProfit': '-200',
                    'leverage': '5'
                }]
            
            @staticmethod
            def futures_account():
                return {
                    'totalWalletBalance': '10000',
                    'totalUnrealizedProfit': '-200',
                    'totalMarginBalance': '9800',
                    'totalMaintMargin': '8000',
                    'totalInitialMargin': '5000',
                    'availableBalance': '4800',
                    'maxWithdrawAmount': '4800'
                }
            
            @staticmethod
            def futures_ticker_24hr_price_change(symbol):
                return {
                    'lastPrice': '48000',
                    'priceChangePercent': '-4.0',
                    'volume': '1000000'
                }
    
    # 시스템 초기화
    exchange = MockExchange()
    config = {}
    
    risk_monitor = RealTimeRiskMonitor(exchange, config)
    
    # 알림 핸들러 추가 (실제 토큰 필요)
    # telegram_handler = TelegramNotificationHandler("BOT_TOKEN", "CHAT_ID")
    # risk_monitor.add_notification_handler(telegram_handler)
    
    # 자동 대응 시스템
    auto_response = AutomatedResponseSystem(exchange, risk_monitor)
    auto_response.enable_auto_actions(confirmation_required=False)
    
    print("✅ 자동화 리스크 시스템 설정 완료")
    print("📊 리스크 모니터링 시작...")
    
    # 한 번 실행 테스트
    await risk_monitor._perform_risk_check()
    
    print("\n📋 설정된 리스크 임계값:")
    for metric, thresholds in risk_monitor.risk_thresholds.items():
        print(f"{metric}:")
        for level, value in thresholds.items():
            print(f"  {level}: {value:.1%}")
    
    print("\n💡 자동 대응 기능:")
    print("- 청산 위험 5% 이내: 자동 50% 포지션 축소")
    print("- 마진 비율 90% 초과: 마진 추가 권장")
    print("- 포트폴리오 VaR 10% 초과: 전체 25% 축소")

# 실행 (비동기)
# asyncio.run(demonstrate_automated_risk_system())
```

---

## 🧮 **고급 수학적 모델**

### 📊 **Monte Carlo 시뮬레이션 구현**

```python
# user_data/strategies/modules/monte_carlo.py
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import norm, t, skewnorm
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class SimulationParameters:
    """시뮬레이션 매개변수"""
    num_simulations: int = 10000
    time_horizon: int = 252  # 1년
    initial_portfolio_value: float = 100000
    confidence_levels: List[float] = None
    
    def __post_init__(self):
        if self.confidence_levels is None:
            self.confidence_levels = [0.90, 0.95, 0.99]

class MonteCarloSimulator:
    """몬테카를로 시뮬레이션 엔진"""
    
    def __init__(self, parameters: SimulationParameters = None):
        self.params = parameters or SimulationParameters()
        self.simulation_results = {}
        
    def simulate_portfolio_paths(self, 
                                portfolio_weights: np.ndarray,
                                expected_returns: np.ndarray,
                                covariance_matrix: np.ndarray,
                                leverage_factors: np.ndarray = None) -> Dict:
        """포트폴리오 경로 시뮬레이션"""
        
        if leverage_factors is None:
            leverage_factors = np.ones_like(portfolio_weights)
        
        # 시뮬레이션 설정
        num_assets = len(portfolio_weights)
        num_days = self.params.time_horizon
        num_sims = self.params.num_simulations
        
        # 일일 수익률 매개변수 (연간 → 일일)
        daily_returns = expected_returns / 252
        daily_cov = covariance_matrix / 252
        
        # 다변량 정규분포에서 수익률 생성
        portfolio_paths = np.zeros((num_sims, num_days + 1))
        portfolio_paths[:, 0] = self.params.initial_portfolio_value
        
        # 각 시뮬레이션 실행
        for sim in range(num_sims):
            # 상관관계를 고려한 수익률 생성
            random_returns = np.random.multivariate_normal(
                daily_returns, daily_cov, size=num_days
            )
            
            # 포트폴리오 일일 수익률 계산
            for day in range(num_days):
                # 자산별 수익률
                asset_returns = random_returns[day]
                
                # 레버리지 적용
                leveraged_returns = asset_returns * leverage_factors
                
                # 포트폴리오 수익률 (가중평균)
                portfolio_return = np.sum(portfolio_weights * leveraged_returns)
                
                # 복리 적용
                portfolio_paths[sim, day + 1] = portfolio_paths[sim, day] * (1 + portfolio_return)
        
        # 결과 분석
        final_values = portfolio_paths[:, -1]
        total_returns = (final_values / self.params.initial_portfolio_value) - 1
        
        # 리스크 메트릭스 계산
        risk_metrics = self._calculate_simulation_metrics(portfolio_paths, total_returns)
        
        return {
            'portfolio_paths': portfolio_paths,
            'final_values': final_values,
            'total_returns': total_returns,
            'risk_metrics': risk_metrics,
            'parameters': {
                'weights': portfolio_weights,
                'expected_returns': expected_returns,
                'leverage_factors': leverage_factors
            }
        }
    
    def simulate_extreme_scenarios(self,
                                 portfolio_weights: np.ndarray,
                                 expected_returns: np.ndarray,
                                 covariance_matrix: np.ndarray,
                                 tail_risk_factor: float = 2.0) -> Dict:
        """극단 시나리오 시뮬레이션 (Fat Tail 고려)"""
        
        # t-분포 사용 (더 두꺼운 꼬리)
        degrees_of_freedom = 5  # 자유도가 낮을수록 더 극단적
        
        num_assets = len(portfolio_weights)
        num_days = self.params.time_horizon
        num_sims = self.params.num_simulations
        
        daily_returns = expected_returns / 252
        daily_cov = covariance_matrix / 252
        
        # Cholesky 분해로 상관관계 구현
        L = np.linalg.cholesky(daily_cov)
        
        portfolio_paths = np.zeros((num_sims, num_days + 1))
        portfolio_paths[:, 0] = self.params.initial_portfolio_value
        
        extreme_events = []  # 극단 이벤트 기록
        
        for sim in range(num_sims):
            for day in range(num_days):
                # t-분포에서 랜덤 변수 생성
                t_random = np.random.standard_t(degrees_of_freedom, size=num_assets)
                
                # 표준편차 조정
                t_random = t_random * np.sqrt((degrees_of_freedom - 2) / degrees_of_freedom)
                
                # 상관관계 적용
                correlated_random = L @ t_random
                
                # 수익률 계산
                asset_returns = daily_returns + correlated_random
                
                # 극단 이벤트 감지 (3 시그마 초과)
                for i, ret in enumerate(asset_returns):
                    if abs(ret) > 3 * np.sqrt(daily_cov[i, i]):
                        extreme_events.append({
                            'simulation': sim,
                            'day': day,
                            'asset': i,
                            'return': ret,
                            'sigma_level': abs(ret) / np.sqrt(daily_cov[i, i])
                        })
                
                # 포트폴리오 수익률
                portfolio_return = np.sum(portfolio_weights * asset_returns)
                portfolio_paths[sim, day + 1] = portfolio_paths[sim, day] * (1 + portfolio_return)
        
        # 결과 분석
        final_values = portfolio_paths[:, -1]
        total_returns = (final_values / self.params.initial_portfolio_value) - 1
        
        # 극단값 분석
        extreme_analysis = self._analyze_extreme_events(extreme_events, portfolio_paths)
        
        return {
            'portfolio_paths': portfolio_paths,
            'final_values': final_values,
            'total_returns': total_returns,
            'extreme_events': extreme_events,
            'extreme_analysis': extreme_analysis,
            'fat_tail_metrics': self._calculate_fat_tail_metrics(total_returns)
        }
    
    def _calculate_simulation_metrics(self, paths: np.ndarray, 
                                    returns: np.ndarray) -> Dict:
        """시뮬레이션 메트릭스 계산"""
        
        metrics = {}
        
        # 기본 통계
        metrics['mean_return'] = np.mean(returns)
        metrics['std_return'] = np.std(returns)
        metrics['skewness'] = stats.skew(returns)
        metrics['kurtosis'] = stats.kurtosis(returns)
        
        # VaR/CVaR 계산
        for confidence in self.params.confidence_levels:
            var_level = np.percentile(returns, (1 - confidence) * 100)
            cvar_level = np.mean(returns[returns <= var_level])
            
            metrics[f'var_{int(confidence*100)}'] = var_level
            metrics[f'cvar_{int(confidence*100)}'] = cvar_level
        
        # 최대 낙폭 분포
        max_drawdowns = []
        for sim_path in paths:
            running_max = np.maximum.accumulate(sim_path)
            drawdowns = (sim_path - running_max) / running_max
            max_drawdowns.append(np.min(drawdowns))
        
        metrics['max_drawdown_mean'] = np.mean(max_drawdowns)
        metrics['max_drawdown_95'] = np.percentile(max_drawdowns, 5)  # 하위 5%
        
        # 확률 메트릭스
        metrics['prob_positive'] = np.mean(returns > 0)
        metrics['prob_loss_5pct'] = np.mean(returns < -0.05)
        metrics['prob_loss_10pct'] = np.mean(returns < -0.10)
        metrics['prob_loss_20pct'] = np.mean(returns < -0.20)
        
        # 목표 수익률 달성 확률
        target_returns = [0.05, 0.10, 0.15, 0.20]
        for target in target_returns:
            metrics[f'prob_return_{int(target*100)}pct'] = np.mean(returns > target)
        
        return metrics
    
    def _analyze_extreme_events(self, extreme_events: List[Dict],
                              paths: np.ndarray) -> Dict:
        """극단 이벤트 분석"""
        
        if not extreme_events:
            return {'no_extreme_events': True}
        
        # 극단 이벤트가 발생한 시뮬레이션의 성과
        affected_simulations = list(set([event['simulation'] for event in extreme_events]))
        
        affected_returns = []
        unaffected_returns = []
        
        for sim in range(len(paths)):
            final_return = (paths[sim, -1] / paths[sim, 0]) - 1
            
            if sim in affected_simulations:
                affected_returns.append(final_return)
            else:
                unaffected_returns.append(final_return)
        
        return {
            'total_extreme_events': len(extreme_events),
            'affected_simulations': len(affected_simulations),
            'affected_ratio': len(affected_simulations) / len(paths),
            'avg_return_affected': np.mean(affected_returns) if affected_returns else 0,
            'avg_return_unaffected': np.mean(unaffected_returns) if unaffected_returns else 0,
            'extreme_event_impact': np.mean(unaffected_returns) - np.mean(affected_returns) if affected_returns and unaffected_returns else 0
        }
    
    def _calculate_fat_tail_metrics(self, returns: np.ndarray) -> Dict:
        """Fat Tail 메트릭스 계산"""
        
        # Hill 추정량 (극단값 지수)
        sorted_returns = np.sort(returns)
        n = len(returns)
        k = int(n * 0.05)  # 상위/하위 5%
        
        # 하단 꼬리 (손실)
        lower_tail = sorted_returns[:k]
        if len(lower_tail) > 1:
            hill_lower = np.mean(np.log(np.abs(lower_tail[:-1]) / np.abs(lower_tail[-1])))
            tail_index_lower = 1 / hill_lower if hill_lower > 0 else np.inf
        else:
            tail_index_lower = np.inf
        
        # 상단 꼬리 (이익)
        upper_tail = sorted_returns[-k:]
        if len(upper_tail) > 1:
            hill_upper = np.mean(np.log(upper_tail[1:] / upper_tail[0]))
            tail_index_upper = 1 / hill_upper if hill_upper > 0 else np.inf
        else:
            tail_index_upper = np.inf
        
        return {
            'tail_index_lower': tail_index_lower,
            'tail_index_upper': tail_index_upper,
            'tail_asymmetry': tail_index_upper / tail_index_lower if tail_index_lower != 0 else np.inf
        }
    
    def stress_test_scenarios(self, 
                            portfolio_weights: np.ndarray,
                            base_returns: np.ndarray,
                            base_covariance: np.ndarray) -> Dict:
        """다양한 스트레스 시나리오 테스트"""
        
        scenarios = {
            'base_case': {
                'returns': base_returns,
                'covariance': base_covariance,
                'description': '기본 시나리오'
            },
            'high_volatility': {
                'returns': base_returns,
                'covariance': base_covariance * 2.0,  # 변동성 2배
                'description': '고변동성 시나리오'
            },
            'low_returns': {
                'returns': base_returns * 0.5,  # 수익률 절반
                'covariance': base_covariance,
                'description': '저수익률 시나리오'
            },
            'high_correlation': {
                'returns': base_returns,
                'covariance': self._increase_correlations(base_covariance, 0.9),
                'description': '고상관관계 시나리오'
            },
            'negative_returns': {
                'returns': -np.abs(base_returns),  # 음의 수익률
                'covariance': base_covariance,
                'description': '하락장 시나리오'
            }
        }
        
        scenario_results = {}
        
        for scenario_name, scenario_data in scenarios.items():
            print(f"📊 {scenario_name} 시나리오 시뮬레이션 중...")
            
            result = self.simulate_portfolio_paths(
                portfolio_weights,
                scenario_data['returns'],
                scenario_data['covariance']
            )
            
            scenario_results[scenario_name] = {
                **result,
                'description': scenario_data['description']
            }
        
        # 시나리오 비교 분석
        comparison = self._compare_scenarios(scenario_results)
        
        return {
            'scenario_results': scenario_results,
            'scenario_comparison': comparison
        }
    
    def _increase_correlations(self, cov_matrix: np.ndarray, 
                             target_correlation: float) -> np.ndarray:
        """상관관계 증가"""
        
        # 상관관계 매트릭스 추출
        std_devs = np.sqrt(np.diag(cov_matrix))
        corr_matrix = cov_matrix / np.outer(std_devs, std_devs)
        
        # 대각선 제외하고 상관관계 조정
        n = corr_matrix.shape[0]
        for i in range(n):
            for j in range(n):
                if i != j:
                    corr_matrix[i, j] = target_correlation
        
        # 공분산 매트릭스로 변환
        new_cov_matrix = np.outer(std_devs, std_devs) * corr_matrix
        
        return new_cov_matrix
    
    def _compare_scenarios(self, scenario_results: Dict) -> Dict:
        """시나리오 비교"""
        
        comparison = {}
        base_case = scenario_results.get('base_case')
        
        if not base_case:
            return comparison
        
        base_metrics = base_case['risk_metrics']
        
        for scenario_name, scenario_data in scenario_results.items():
            if scenario_name == 'base_case':
                continue
            
            scenario_metrics = scenario_data['risk_metrics']
            
            comparison[scenario_name] = {
                'return_change': scenario_metrics['mean_return'] - base_metrics['mean_return'],
                'volatility_change': scenario_metrics['std_return'] - base_metrics['std_return'],
                'var_95_change': scenario_metrics['var_95'] - base_metrics['var_95'],
                'max_drawdown_change': scenario_metrics['max_drawdown_95'] - base_metrics['max_drawdown_95']
            }
        
        return comparison

# GARCH 모델을 통한 변동성 예측
class GARCHVolatilityPredictor:
    """GARCH 모델 기반 변동성 예측"""
    
    def __init__(self):
        self.fitted_params = {}
    
    def fit_garch_model(self, returns: pd.Series, p: int = 1, q: int = 1) -> Dict:
        """GARCH(p,q) 모델 적합"""
        
        # 간단한 GARCH(1,1) 구현
        # 실제 사용시에는 arch 라이브러리 권장
        
        n = len(returns)
        omega = 0.01  # 장기 변동성
        alpha = 0.1   # ARCH 계수
        beta = 0.8    # GARCH 계수
        
        # 조건부 분산 계산
        conditional_variance = np.zeros(n)
        conditional_variance[0] = np.var(returns)
        
        for t in range(1, n):
            conditional_variance[t] = (omega + 
                                     alpha * returns.iloc[t-1]**2 + 
                                     beta * conditional_variance[t-1])
        
        # 변동성 (표준편차)
        conditional_volatility = np.sqrt(conditional_variance)
        
        self.fitted_params = {
            'omega': omega,
            'alpha': alpha,
            'beta': beta,
            'conditional_variance': conditional_variance,
            'conditional_volatility': conditional_volatility
        }
        
        return self.fitted_params
    
    def forecast_volatility(self, horizon: int = 20) -> np.ndarray:
        """변동성 예측"""
        
        if not self.fitted_params:
            raise ValueError("모델이 적합되지 않았습니다.")
        
        omega = self.fitted_params['omega']
        alpha = self.fitted_params['alpha']
        beta = self.fitted_params['beta']
        
        # 마지막 조건부 분산
        last_variance = self.fitted_params['conditional_variance'][-1]
        
        # 예측
        forecast_variance = np.zeros(horizon)
        
        for h in range(horizon):
            if h == 0:
                forecast_variance[h] = omega + (alpha + beta) * last_variance
            else:
                # 장기 수렴
                long_run_variance = omega / (1 - alpha - beta)
                forecast_variance[h] = long_run_variance + (alpha + beta)**h * (last_variance - long_run_variance)
        
        return np.sqrt(forecast_variance)

# 실전 사용 예제
def demonstrate_monte_carlo_simulation():
    """몬테카를로 시뮬레이션 실증"""
    
    print("🎲 몬테카를로 시뮬레이션 시스템 실증\n")
    
    # 시뮬레이션 매개변수
    params = SimulationParameters(
        num_simulations=5000,
        time_horizon=252,  # 1년
        initial_portfolio_value=100000,
        confidence_levels=[0.90, 0.95, 0.99]
    )
    
    # 몬테카를로 시뮬레이터
    mc_simulator = MonteCarloSimulator(params)
    
    # 포트폴리오 설정 (3자산 포트폴리오)
    portfolio_weights = np.array([0.5, 0.3, 0.2])  # BTC, ETH, ADA
    expected_returns = np.array([0.15, 0.12, 0.08])  # 연간 기대수익률
    
    # 공분산 매트릭스 (연간)
    correlations = np.array([
        [1.0, 0.8, 0.6],
        [0.8, 1.0, 0.7],
        [0.6, 0.7, 1.0]
    ])
    
    volatilities = np.array([0.6, 0.5, 0.8])  # 연간 변동성
    covariance_matrix = np.outer(volatilities, volatilities) * correlations
    
    # 레버리지 팩터
    leverage_factors = np.array([3, 2, 5])  # 자산별 레버리지
    
    print("📊 포트폴리오 설정:")
    print(f"가중치: {portfolio_weights}")
    print(f"기대수익률: {expected_returns}")
    print(f"레버리지: {leverage_factors}")
    print()
    
    # 1. 기본 시뮬레이션
    print("🎯 기본 포트폴리오 시뮬레이션:")
    basic_result = mc_simulator.simulate_portfolio_paths(
        portfolio_weights, expected_returns, covariance_matrix, leverage_factors
    )
    
    basic_metrics = basic_result['risk_metrics']
    print(f"평균 수익률: {basic_metrics['mean_return']:.2%}")
    print(f"변동성: {basic_metrics['std_return']:.2%}")
    print(f"왜도: {basic_metrics['skewness']:.3f}")
    print(f"첨도: {basic_metrics['kurtosis']:.3f}")
    
    for confidence in params.confidence_levels:
        var_key = f'var_{int(confidence*100)}'
        cvar_key = f'cvar_{int(confidence*100)}'
        print(f"VaR {confidence:.0%}: {basic_metrics[var_key]:.2%}")
        print(f"CVaR {confidence:.0%}: {basic_metrics[cvar_key]:.2%}")
    
    print(f"최대 낙폭 (평균): {basic_metrics['max_drawdown_mean']:.2%}")
    print(f"최대 낙폭 (95%): {basic_metrics['max_drawdown_95']:.2%}")
    print()
    
    # 2. 극단 시나리오 시뮬레이션
    print("💥 극단 시나리오 시뮬레이션 (Fat Tail):")
    extreme_result = mc_simulator.simulate_extreme_scenarios(
        portfolio_weights, expected_returns, covariance_matrix
    )
    
    extreme_analysis = extreme_result['extreme_analysis']
    fat_tail_metrics = extreme_result['fat_tail_metrics']
    
    print(f"극단 이벤트 수: {extreme_analysis['total_extreme_events']}")
    print(f"영향받은 시뮬레이션: {extreme_analysis['affected_ratio']:.1%}")
    print(f"극단 이벤트 영향: {extreme_analysis['extreme_event_impact']:.2%}")
    print(f"하단 꼬리 지수: {fat_tail_metrics['tail_index_lower']:.2f}")
    print(f"상단 꼬리 지수: {fat_tail_metrics['tail_index_upper']:.2f}")
    print()
    
    # 3. 스트레스 테스트
    print("🧪 스트레스 테스트 시나리오:")
    stress_results = mc_simulator.stress_test_scenarios(
        portfolio_weights, expected_returns, covariance_matrix
    )
    
    comparison = stress_results['scenario_comparison']
    
    for scenario_name, changes in comparison.items():
        print(f"{scenario_name}:")
        print(f"  수익률 변화: {changes['return_change']:+.2%}")
        print(f"  변동성 변화: {changes['volatility_change']:+.2%}")
        print(f"  VaR 95% 변화: {changes['var_95_change']:+.2%}")
        print()
    
    # 4. 확률 분석
    print("🎯 목표 달성 확률:")
    prob_metrics = basic_metrics
    print(f"양수 수익률 확률: {prob_metrics['prob_positive']:.1%}")
    print(f"5% 이상 손실 확률: {prob_metrics['prob_loss_5pct']:.1%}")
    print(f"10% 이상 손실 확률: {prob_metrics['prob_loss_10pct']:.1%}")
    print(f"20% 이상 손실 확률: {prob_metrics['prob_loss_20pct']:.1%}")
    
    for target in [5, 10, 15, 20]:
        prob_key = f'prob_return_{target}pct'
        if prob_key in prob_metrics:
            print(f"{target}% 이상 수익 확률: {prob_metrics[prob_key]:.1%}")

# 실행
demonstrate_monte_carlo_simulation()
```

---

## 🎯 **결론 및 다음 단계**

### 📋 **핵심 요약**

이 가이드를 통해 우리는 Binance USDT Perpetual Futures에서의 레버리지 리스크 관리를 위한 완전한 시스템을 구축했습니다:

**🔧 구현된 핵심 시스템:**
1. **Kelly Criterion 기반 포지션 크기 계산**
2. **동적 레버리지 조정 시스템**
3. **실시간 청산 방지 모니터링**
4. **VaR/CVaR 기반 리스크 측정**
5. **몬테카를로 시뮬레이션 엔진**
6. **자동화된 리스크 대응 시스템**

### 🚀 **즉시 적용 가능한 실전 전략**

```python
# user_data/strategies/LeverageRiskStrategy.py
"""
통합 레버리지 리스크 관리 전략
모든 구성 요소를 통합한 실전 구현
"""

from freqtrade.strategy import IStrategy
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Optional

class LeverageRiskStrategy(IStrategy):
    """전문가급 레버리지 리스크 관리 전략"""
    
    INTERFACE_VERSION = 3
    
    # 기본 전략 설정
    timeframe = '15m'
    stoploss = -0.99  # 동적으로 조정
    
    # 리스크 관리 설정
    max_portfolio_risk = 0.02  # 포트폴리오 일일 리스크 2%
    target_sharpe_ratio = 1.5
    max_leverage = 10
    
    def __init__(self, config: dict) -> None:
        super().__init__(config)
        
        # 리스크 관리 모듈 초기화
        from .modules.kelly_criterion import KellyCriterionCalculator
        from .modules.dynamic_leverage import DynamicLeverageManager
        from .modules.liquidation_monitor import LiquidationMonitor
        
        self.kelly_calculator = KellyCriterionCalculator()
        self.leverage_manager = DynamicLeverageManager()
        self.liquidation_monitor = LiquidationMonitor(self.dp.exchange)
    
    def custom_stake_amount(self, pair: str, current_time, current_rate: float,
                           proposed_stake: float, min_stake: Optional[float],
                           max_stake: float, leverage: float, entry_tag: Optional[str],
                           side: str, **kwargs) -> float:
        """Kelly Criterion 기반 최적 포지션 크기 계산"""
        
        try:
            # 포트폴리오 전체 잔고
            total_balance = self.wallets.get_total_stake_amount()
            
            # 과거 거래 데이터 기반 Kelly 계산
            if len(self.kelly_calculator.historical_trades) > 30:
                kelly_result = self.kelly_calculator.calculate_optimal_position_size(
                    total_balance, self.max_leverage
                )
                optimal_risk = kelly_result['recommended_risk']
            else:
                # 초기 보수적 접근
                optimal_risk = total_balance * 0.01  # 1%
            
            # 현재 변동성 기반 레버리지 조정
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            if len(dataframe) > 20:
                volatility = dataframe['close'].pct_change().rolling(20).std().iloc[-1]
                leverage_analysis = self.leverage_manager.calculate_optimal_leverage(
                    pair, current_rate, dataframe['close']
                )
                optimal_leverage = leverage_analysis['final_leverage']
            else:
                optimal_leverage = 3  # 기본값
            
            # 스탑로스 거리 계산
            if self.stoploss:
                stop_distance = abs(self.stoploss)
            else:
                # ATR 기반 동적 스탑로스
                if 'atr' in dataframe.columns:
                    atr = dataframe['atr'].iloc[-1]
                    stop_distance = (atr * 2) / current_rate  # ATR의 2배
                else:
                    stop_distance = 0.02  # 기본 2%
            
            # 레버리지 고려한 실제 리스크 계산
            effective_stop_distance = stop_distance * optimal_leverage
            
            # 최종 포지션 크기
            position_size = optimal_risk / effective_stop_distance
            
            # 한계값 적용
            position_size = max(min_stake or 0, min(position_size, max_stake))
            
            return position_size
            
        except Exception as e:
            self.logger.error(f"포지션 크기 계산 오류: {e}")
            return min_stake or (total_balance * 0.01)  # 안전한 기본값
    
    def leverage(self, pair: str, current_time, current_rate: float,
                proposed_leverage: int, max_leverage: int, entry_tag: Optional[str],
                side: str, **kwargs) -> float:
        """동적 레버리지 계산"""
        
        try:
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            
            if len(dataframe) > 20:
                leverage_analysis = self.leverage_manager.calculate_optimal_leverage(
                    pair, current_rate, dataframe['close']
                )
                optimal_leverage = leverage_analysis['final_leverage']
                
                # 최대 레버리지 제한
                final_leverage = min(optimal_leverage, max_leverage, self.max_leverage)
                
                self.logger.info(f"{pair} 최적 레버리지: {final_leverage}x "
                               f"(변동성: {leverage_analysis['current_volatility']:.2%})")
                
                return final_leverage
            
            return min(3, max_leverage)  # 기본값
            
        except Exception as e:
            self.logger.error(f"레버리지 계산 오류: {e}")
            return min(3, max_leverage)
    
    def custom_exit(self, pair: str, trade, current_time, current_rate: float,
                   current_profit: float, **kwargs) -> Optional[str]:
        """AI 기반 동적 청산 관리"""
        
        try:
            # 1. 청산 위험 모니터링
            liquidation_risk = self.liquidation_monitor.monitor_liquidation_risk()
            
            for risk_position in liquidation_risk:
                if risk_position['symbol'] == pair.replace('/', ''):
                    if risk_position['risk_level'] in ['CRITICAL', 'EMERGENCY']:
                        return f"liquidation_risk_{risk_position['risk_level'].lower()}"
            
            # 2. 레버리지 기반 동적 스탑로스
            leverage = trade.leverage or 1
            
            # 고레버리지 포지션 보호
            if leverage >= 5:
                if current_profit < -0.01:  # 1% 손실에서 조기 청산
                    return "high_leverage_protection"
            
            # 3. 변동성 기반 이익 실현
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            if len(dataframe) > 20:
                current_volatility = dataframe['close'].pct_change().rolling(20).std().iloc[-1]
                
                # 높은 변동성 구간에서 이익 실현
                if current_volatility > 0.04 and current_profit > 0.03:  # 4% 변동성, 3% 이익
                    return "high_volatility_profit_taking"
            
            # 4. 자금 조달 수수료 고려
            try:
                funding_rate = self.dp.exchange._api.futures_funding_rate(
                    symbol=pair.replace('/', ''), limit=1
                )[0]['fundingRate']
                
                funding_cost = float(funding_rate) * (trade.open_date_utc.timestamp() - current_time.timestamp()) / 28800
                
                # 자금 조달 비용이 수익보다 클 때
                if abs(funding_cost) > abs(current_profit) * 0.5:
                    return "funding_cost_exit"
                    
            except Exception:
                pass  # 자금 조달 수수료 조회 실패시 무시
            
            return None
            
        except Exception as e:
            self.logger.error(f"청산 관리 오류: {e}")
            return None
    
    def confirm_trade_exit(self, pair: str, trade, order_type: str, amount: float,
                          rate: float, time_in_force: str, exit_reason: str,
                          current_time, **kwargs) -> bool:
        """거래 종료 확인"""
        
        # 거래 결과를 Kelly Criterion 계산기에 추가
        if trade.close_profit is not None:
            leverage = trade.leverage or 1
            self.kelly_calculator.add_trade_result(trade.close_profit, leverage)
        
        # 긴급 상황에서는 항상 승인
        emergency_reasons = [
            'liquidation_risk_emergency',
            'liquidation_risk_critical',
            'high_leverage_protection'
        ]
        
        if exit_reason in emergency_reasons:
            self.logger.warning(f"긴급 청산 승인: {pair} - {exit_reason}")
            return True
        
        return True  # 기본적으로 모든 청산 승인
    
    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """기술적 지표 계산"""
        
        # ATR (Average True Range)
        dataframe['atr'] = ta.ATR(dataframe)
        
        # 볼린저 밴드
        bollinger = ta.BBANDS(dataframe['close'])
        dataframe['bb_lower'] = bollinger['lowerband']
        dataframe['bb_middle'] = bollinger['middleband']
        dataframe['bb_upper'] = bollinger['upperband']
        dataframe['bb_width'] = (dataframe['bb_upper'] - dataframe['bb_lower']) / dataframe['bb_middle']
        
        # RSI
        dataframe['rsi'] = ta.RSI(dataframe)
        
        # 변동성 측정
        dataframe['volatility'] = dataframe['close'].pct_change().rolling(20).std()
        
        # 볼륨 지표
        dataframe['volume_sma'] = dataframe['volume'].rolling(20).mean()
        dataframe['volume_ratio'] = dataframe['volume'] / dataframe['volume_sma']
        
        return dataframe
    
    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """진입 신호 생성"""
        
        # 롱 진입 조건
        dataframe.loc[
            (
                (dataframe['rsi'] < 30) &  # 과매도
                (dataframe['close'] <= dataframe['bb_lower']) &  # 볼린저밴드 하단
                (dataframe['volume_ratio'] > 1.2) &  # 거래량 증가
                (dataframe['volatility'] < 0.05)  # 변동성 제한
            ),
            'enter_long'] = 1
        
        # 숏 진입 조건  
        dataframe.loc[
            (
                (dataframe['rsi'] > 70) &  # 과매수
                (dataframe['close'] >= dataframe['bb_upper']) &  # 볼린저밴드 상단
                (dataframe['volume_ratio'] > 1.2) &  # 거래량 증가
                (dataframe['volatility'] < 0.05)  # 변동성 제한
            ),
            'enter_short'] = 1
        
        return dataframe
    
    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """청산 신호 생성"""
        
        # 롱 청산 조건
        dataframe.loc[
            (
                (dataframe['rsi'] > 65) |  # RSI 상승
                (dataframe['close'] >= dataframe['bb_middle'])  # 중간선 돌파
            ),
            'exit_long'] = 1
        
        # 숏 청산 조건
        dataframe.loc[
            (
                (dataframe['rsi'] < 35) |  # RSI 하락
                (dataframe['close'] <= dataframe['bb_middle'])  # 중간선 하향 돌파
            ),
            'exit_short'] = 1
        
        return dataframe
```

### 📊 **실전 배포 체크리스트**

```markdown
## 🚀 **Freqtrade Futures 레버리지 리스크 관리 배포 가이드**

### ✅ **1단계: 환경 설정 검증**
- [ ] Python 3.9+ 설치 확인
- [ ] Freqtrade 2024.1+ 버전 설치
- [ ] 필수 라이브러리 설치: `pip install numpy pandas scipy plotly`
- [ ] Binance Testnet API 키 발급 및 설정

### ✅ **2단계: 리스크 관리 모듈 배포**
- [ ] `user_data/strategies/modules/` 디렉토리 생성
- [ ] Kelly Criterion 계산 모듈 (`kelly_criterion.py`) 배포
- [ ] 동적 레버리지 관리 모듈 (`dynamic_leverage.py`) 배포
- [ ] 청산 모니터링 모듈 (`liquidation_monitor.py`) 배포
- [ ] VaR 계산 모듈 (`risk_metrics.py`) 배포

### ✅ **3단계: 전략 구성 파일 설정**
```json
{
  "max_open_trades": 3,
  "stake_currency": "USDT",
  "stake_amount": "unlimited",
  "trading_mode": "futures",
  "margin_mode": "isolated",
  "dry_run": true,
  "exchange": {
    "name": "binance",
    "sandbox": true,
    "ccxt_config": {
      "options": {
        "defaultType": "future"
      }
    }
  },
  "strategy": "LeverageRiskStrategy",
  "strategy_path": "user_data/strategies/"
}
```

### ✅ **4단계: 백테스팅 검증**
```bash
# 3개월 백테스팅 실행
freqtrade backtesting \
  --config user_data/config_futures.json \
  --strategy LeverageRiskStrategy \
  --timerange 20240701-20241001 \
  --breakdown day

# 성과 지표 확인
# - 총 수익률 > 15%
# - 샤프 비율 > 1.5
# - 최대 낙폭 < 15%
# - 승률 > 60%
```

### ✅ **5단계: 라이브 테스트 (소액)**
- [ ] 테스트넷에서 1주일 운영
- [ ] 실거래 환경에서 $100 테스트
- [ ] 리스크 알림 시스템 동작 확인
- [ ] 청산 방지 시스템 테스트

### ✅ **6단계: 모니터링 시스템 구축**
- [ ] 텔레그램 봇 설정 (알림용)
- [ ] 대시보드 구축 (선택사항)
- [ ] 로그 모니터링 설정
- [ ] 일일 리포트 자동화

### ✅ **7단계: 위험 관리 규칙 설정**
- [ ] 최대 포트폴리오 리스크: 일일 2%
- [ ] 최대 개별 포지션 리스크: 0.5%
- [ ] 최대 레버리지: 5배 (초보자), 10배 (경험자)
- [ ] 강제 청산 버퍼: 20%
- [ ] 자금 조달 수수료 한도: 수익의 30%
```

### 🎯 **성과 최적화 가이드**

```python
# user_data/strategies/optimization_config.py
"""
성과 최적화를 위한 설정 가이드
"""

# 1. 시장별 최적 설정
MARKET_CONFIGS = {
    'BTCUSDT': {
        'max_leverage': 5,
        'target_volatility': 0.025,
        'kelly_fraction': 0.25,
        'stop_loss_atr_multiplier': 2.0
    },
    'ETHUSDT': {
        'max_leverage': 3,
        'target_volatility': 0.030,
        'kelly_fraction': 0.20,
        'stop_loss_atr_multiplier': 2.5
    },
    'ALTCOINS': {
        'max_leverage': 2,
        'target_volatility': 0.040,
        'kelly_fraction': 0.15,
        'stop_loss_atr_multiplier': 3.0
    }
}

# 2. 변동성 체제별 조정
VOLATILITY_REGIMES = {
    'LOW_VOL': {      # < 2%
        'leverage_multiplier': 1.5,
        'position_size_multiplier': 1.2,
        'stop_loss_multiplier': 0.8
    },
    'NORMAL_VOL': {   # 2-4%
        'leverage_multiplier': 1.0,
        'position_size_multiplier': 1.0,
        'stop_loss_multiplier': 1.0
    },
    'HIGH_VOL': {     # 4-6%
        'leverage_multiplier': 0.7,
        'position_size_multiplier': 0.8,
        'stop_loss_multiplier': 1.3
    },
    'EXTREME_VOL': {  # > 6%
        'leverage_multiplier': 0.4,
        'position_size_multiplier': 0.5,
        'stop_loss_multiplier': 2.0
    }
}

# 3. 시간대별 조정
TIME_BASED_ADJUSTMENTS = {
    'ASIAN_SESSION': {    # UTC 00:00-08:00
        'risk_multiplier': 0.8,  # 낮은 유동성
        'max_leverage': 3
    },
    'EUROPEAN_SESSION': { # UTC 08:00-16:00
        'risk_multiplier': 1.0,
        'max_leverage': 5
    },
    'US_SESSION': {       # UTC 16:00-24:00
        'risk_multiplier': 1.2,  # 높은 변동성
        'max_leverage': 7
    }
}
```

### 🎓 **고급 활용 팁**

```python
# 1. 다중 시간프레임 리스크 관리
def multi_timeframe_risk_analysis(self, pair: str):
    """다중 시간프레임 리스크 분석"""
    
    timeframes = ['5m', '15m', '1h', '4h']
    risk_scores = {}
    
    for tf in timeframes:
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, tf)
        volatility = dataframe['close'].pct_change().rolling(20).std().iloc[-1]
        
        # 시간프레임별 가중치
        weight = {'5m': 0.1, '15m': 0.3, '1h': 0.4, '4h': 0.2}[tf]
        risk_scores[tf] = volatility * weight
    
    # 종합 리스크 점수
    total_risk = sum(risk_scores.values())
    
    return {
        'total_risk': total_risk,
        'risk_level': 'HIGH' if total_risk > 0.04 else 'MEDIUM' if total_risk > 0.02 else 'LOW',
        'timeframe_breakdown': risk_scores
    }

# 2. 상관관계 기반 포지션 제한
def correlation_based_position_limit(self, new_pair: str):
    """상관관계 기반 포지션 제한"""
    
    active_pairs = [trade.pair for trade in self.active_trades]
    
    if not active_pairs:
        return True  # 첫 번째 포지션은 허용
    
    # 간단한 상관관계 확인 (실제로는 과거 데이터 분석 필요)
    high_correlation_pairs = {
        'BTCUSDT': ['ETHUSDT'],
        'ETHUSDT': ['BTCUSDT', 'ADAUSDT'],
        'ADAUSDT': ['ETHUSDT', 'DOTUSDT']
    }
    
    correlated_pairs = high_correlation_pairs.get(new_pair, [])
    active_correlated = [pair for pair in active_pairs if pair in correlated_pairs]
    
    # 고상관 자산이 2개 이상 있으면 제한
    return len(active_correlated) < 2

# 3. 시장 체제 감지
def detect_market_regime(self, pair: str):
    """시장 체제 감지 (트렌드/레인지)"""
    
    dataframe, _ = self.dp.get_analyzed_dataframe(pair, '1h')
    
    # ADX로 트렌드 강도 측정
    adx = ta.ADX(dataframe)
    current_adx = adx.iloc[-1]
    
    # 볼린저밴드 폭으로 변동성 측정
    bb_width = dataframe['bb_width'].iloc[-1]
    
    if current_adx > 25 and bb_width > 0.04:
        return 'TRENDING_HIGH_VOL'
    elif current_adx > 25:
        return 'TRENDING_LOW_VOL'
    elif bb_width > 0.04:
        return 'RANGING_HIGH_VOL'
    else:
        return 'RANGING_LOW_VOL'
```

### 📈 **성과 모니터링 대시보드**

```python
# user_data/utils/performance_dashboard.py
"""
실시간 성과 모니터링 대시보드
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_risk_dashboard():
    """리스크 관리 대시보드"""
    
    st.title("🛡️ 레버리지 리스크 관리 대시보드")
    
    # 실시간 메트릭스
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("포트폴리오 VaR", "2.3%", "0.1%")
    
    with col2:
        st.metric("평균 레버리지", "4.2x", "-0.3x")
    
    with col3:
        st.metric("마진 사용률", "65%", "5%")
    
    with col4:
        st.metric("최소 청산거리", "12%", "2%")
    
    # 포지션 현황
    st.subheader("📊 현재 포지션")
    
    position_data = {
        'Symbol': ['BTCUSDT', 'ETHUSDT', 'ADAUSDT'],
        'Side': ['LONG', 'SHORT', 'LONG'],
        'Size': [50000, 30000, 20000],
        'Leverage': [5, 3, 7],
        'PnL': ['+2.3%', '-0.8%', '+1.5%'],
        'Liquidation Distance': ['15%', '22%', '12%']
    }
    
    st.dataframe(position_data)
    
    # 리스크 차트
    st.subheader("📈 리스크 추이")
    
    # 실제 데이터 로드 (여기서는 예시)
    dates = pd.date_range('2024-01-01', periods=30)
    var_data = np.random.normal(0.02, 0.005, 30)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=var_data, name='일일 VaR'))
    fig.add_hline(y=0.05, line_dash="dash", line_color="red", 
                  annotation_text="위험 한계 (5%)")
    
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    create_risk_dashboard()
```

### 🎯 **최종 권장사항**

**📋 초보자 설정:**
- 최대 레버리지: 3배
- 포트폴리오 리스크: 1%
- 포지션 수: 2개 이하
- 청산 버퍼: 30%

**📊 중급자 설정:**
- 최대 레버리지: 5배
- 포트폴리오 리스크: 2%
- 포지션 수: 3개 이하
- 청산 버퍼: 20%

**🚀 고급자 설정:**
- 최대 레버리지: 10배
- 포트폴리오 리스크: 3%
- 포지션 수: 5개 이하
- 청산 버퍼: 15%

---

## 🎉 **축하합니다!**

**Binance USDT Perpetual Futures 전용 레버리지 리스크 관리 완전 가이드**를 성공적으로 완료하셨습니다! 

이제 여러분은:
- ✅ 수학적으로 정확한 포지션 크기 계산 능력
- ✅ 동적 레버리지 조정 시스템 구축 능력  
- ✅ 실시간 청산 방지 모니터링 시스템
- ✅ 전문가급 리스크 메트릭스 분석 능력
- ✅ 자동화된 리스크 대응 시스템

을 갖추게 되었습니다.

### 🔗 **다음 단계 추천**

1. **[03_FUTURES_AUTOMATION_SETUP.md](03_FUTURES_AUTOMATION_SETUP.md)**: 완전 자동화 시스템 구축
2. **[08_FUNDING_RATE_STRATEGY.md](08_FUNDING_RATE_STRATEGY.md)**: 자금 조달료 수익 극대화
3. **[04_FUTURES_TROUBLESHOOTING.md](04_FUTURES_TROUBLESHOOTING.md)**: 고급 문제 해결

### 💬 **지원 및 피드백**

궁금한 점이나 개선 제안이 있으시면 언제든 연락주세요!

---

<div align="center">

**🚀 안전하고 수익성 높은 선물 거래의 여정이 시작됩니다! 🚀**

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue?style=for-the-badge&logo=github)](https://github.com/freqtrade/freqtrade)
[![Telegram](https://img.shields.io/badge/Telegram-Community-blue?style=for-the-badge&logo=telegram)](https://t.me/freqtradebot)

**⚠️ 리스크 고지: 레버리지 거래는 높은 위험을 수반합니다. 투자 전 충분한 학습과 리스크 관리가 필수입니다.**

</div>---

## 💥 **스트레스 테스트 시나리오**

### 📉 **역사적 크래시 시나리오 분석**

과거 극단적 시장 상황을 재현하여 포트폴리오의 복원력을 테스트합니다.

```python
# user_data/strategies/modules/stress_testing.py
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class CrashScenario:
    """크래시 시나리오 정의"""
    name: str
    description: str
    duration_days: int
    max_drawdown: float
    volatility_multiplier: float
    correlation_shift: float  # 상관관계 변화
    recovery_period: int     # 회복 기간

class StressTester:
    """스트레스 테스트 엔진"""
    
    def __init__(self):
        self.crash_scenarios = self._initialize_scenarios()
        self.test_results = {}
        
    def _initialize_scenarios(self) -> Dict[str, CrashScenario]:
        """역사적 크래시 시나리오 초기화"""
        
        return {
            'covid_crash_2020': CrashScenario(
                name="COVID-19 Crash (March 2020)",
                description="팬데믹으로 인한 급격한 시장 붕괴",
                duration_days=30,
                max_drawdown=0.50,  # 50% 하락
                volatility_multiplier=3.0,
                correlation_shift=0.3,  # 상관관계 증가
                recovery_period=120
            ),
            'luna_ust_collapse_2022': CrashScenario(
                name="LUNA/UST Collapse (May 2022)",
                description="알고리즘 스테이블코인 붕괴 사태",
                duration_days=7,
                max_drawdown=0.80,  # 80% 하락
                volatility_multiplier=5.0,
                correlation_shift=0.5,
                recovery_period=180
            ),
            'ftx_bankruptcy_2022': CrashScenario(
                name="FTX Bankruptcy (November 2022)",
                description="대형 거래소 파산으로 인한 신뢰도 급락",
                duration_days=14,
                max_drawdown=0.25,  # 25% 하락
                volatility_multiplier=2.5,
                correlation_shift=0.4,
                recovery_period=90
            ),
            'china_evergrande_2021': CrashScenario(
                name="Evergrande Crisis (September 2021)",
                description="중국 부동산 대기업 부채 위기",
                duration_days=21,
                max_drawdown=0.35,  # 35% 하락
                volatility_multiplier=2.0,
                correlation_shift=0.2,
                recovery_period=60
            ),
            'black_swan_extreme': CrashScenario(
                name="Black Swan Extreme Event",
                description="예상치 못한 극단적 시장 충격",
                duration_days=3,
                max_drawdown=0.70,  # 70% 하락
                volatility_multiplier=8.0,
                correlation_shift=0.7,
                recovery_period=365
            )
        }
    
    def simulate_crash_scenario(self, scenario_name: str,
                              portfolio_positions: Dict[str, Dict],
                              base_correlations: pd.DataFrame) -> Dict:
        """크래시 시나리오 시뮬레이션"""
        
        if scenario_name not in self.crash_scenarios:
            raise ValueError(f"알 수 없는 시나리오: {scenario_name}")
        
        scenario = self.crash_scenarios[scenario_name]
        
        print(f"🚨 스트레스 테스트: {scenario.name}")
        print(f"📝 설명: {scenario.description}")
        print(f"⏱️ 지속기간: {scenario.duration_days}일")
        print(f"📉 최대 하락: {scenario.max_drawdown:.0%}")
        print()
        
        # 시나리오 수익률 생성
        crash_returns = self._generate_crash_returns(scenario, len(portfolio_positions))
        
        # 포트폴리오 영향 분석
        portfolio_impact = self._analyze_portfolio_impact(
            portfolio_positions, crash_returns, scenario
        )
        
        # 레버리지 영향 분석
        leverage_impact = self._analyze_leverage_impact(
            portfolio_positions, crash_returns, scenario
        )
        
        # 회복 시나리오
        recovery_analysis = self._analyze_recovery_scenario(
            portfolio_positions, crash_returns, scenario
        )
        
        # 리스크 메트릭스 변화
        risk_metrics_change = self._calculate_risk_metrics_change(
            portfolio_positions, scenario
        )
        
        test_result = {
            'scenario': scenario,
            'crash_returns': crash_returns,
            'portfolio_impact': portfolio_impact,
            'leverage_impact': leverage_impact,
            'recovery_analysis': recovery_analysis,
            'risk_metrics_change': risk_metrics_change,
            'survival_analysis': self._analyze_survival_probability(portfolio_impact, leverage_impact)
        }
        
        self.test_results[scenario_name] = test_result
        return test_result
    
    def _generate_crash_returns(self, scenario: CrashScenario, 
                               num_assets: int) -> Dict[str, pd.Series]:
        """크래시 수익률 생성"""
        
        crash_returns = {}
        
        # 시간 축 생성
        dates = pd.date_range(start='2024-01-01', periods=scenario.duration_days, freq='D')
        
        # 각 자산별 크래시 수익률 생성
        asset_names = [f'Asset_{i}' for i in range(num_assets)]
        
        for i, asset in enumerate(asset_names):
            # 하락 곡선 생성 (지수적 감소)
            decline_curve = np.exp(-np.linspace(0, 3, scenario.duration_days)) - 1
            decline_curve *= scenario.max_drawdown
            
            # 일일 수익률로 변환
            daily_returns = np.diff(np.concatenate([[0], decline_curve]))
            
            # 변동성 증가 반영
            base_volatility = 0.02  # 2% 기본 일일 변동성
            stressed_volatility = base_volatility * scenario.volatility_multiplier
            
            # 노이즈 추가
            noise = np.random.normal(0, stressed_volatility * 0.5, len(daily_returns))
            final_returns = daily_returns + noise
            
            crash_returns[asset] = pd.Series(final_returns, index=dates)
        
        return crash_returns
    
    def _analyze_portfolio_impact(self, positions: Dict[str, Dict],
                                 crash_returns: Dict[str, pd.Series],
                                 scenario: CrashScenario) -> Dict:
        """포트폴리오 영향 분석"""
        
        total_portfolio_value = sum(pos['notional_value'] for pos in positions.values())
        
        # 포지션별 영향 계산
        position_impacts = {}
        total_pnl = 0
        
        for i, (symbol, position) in enumerate(positions.items()):
            asset_key = f'Asset_{i}'
            if asset_key in crash_returns:
                position_value = position['notional_value']
                leverage = position.get('leverage', 1)
                
                # 누적 수익률 계산
                cumulative_return = (1 + crash_returns[asset_key]).prod() - 1
                
                # 레버리지 적용
                leveraged_return = cumulative_return * leverage
                
                # P&L 계산
                position_pnl = position_value * leveraged_return
                total_pnl += position_pnl
                
                # 청산 위험 분석
                liquidation_risk = self._calculate_liquidation_risk(
                    crash_returns[asset_key], leverage, position_value
                )
                
                position_impacts[symbol] = {
                    'initial_value': position_value,
                    'cumulative_return': cumulative_return,
                    'leveraged_return': leveraged_return,
                    'pnl': position_pnl,
                    'pnl_percentage': position_pnl / position_value,
                    'weight': position_value / total_portfolio_value,
                    'liquidation_risk': liquidation_risk
                }
        
        # 포트폴리오 전체 영향
        portfolio_return = total_pnl / total_portfolio_value
        portfolio_final_value = total_portfolio_value + total_pnl
        
        return {
            'initial_portfolio_value': total_portfolio_value,
            'final_portfolio_value': portfolio_final_value,
            'total_pnl': total_pnl,
            'portfolio_return': portfolio_return,
            'position_impacts': position_impacts,
            'worst_position': min(position_impacts.items(), 
                                key=lambda x: x[1]['pnl_percentage'])[0],
            'portfolio_survival': portfolio_final_value > 0
        }
    
    def _calculate_liquidation_risk(self, returns: pd.Series, 
                                  leverage: int, position_value: float) -> Dict:
        """청산 위험 계산"""
        
        # 누적 손실 추적
        cumulative_returns = (1 + returns).cumprod() - 1
        leveraged_cumulative = cumulative_returns * leverage
        
        # 청산 임계점 (-100/leverage %)
        liquidation_threshold = -1.0 / leverage
        
        # 청산 발생 여부
        liquidation_occurred = (leveraged_cumulative <= liquidation_threshold).any()
        
        if liquidation_occurred:
            liquidation_day = (leveraged_cumulative <= liquidation_threshold).idxmax()
            days_to_liquidation = (liquidation_day - returns.index[0]).days
        else:
            liquidation_day = None
            days_to_liquidation = None
        
        # 최대 손실
        max_loss = leveraged_cumulative.min()
        max_loss_day = leveraged_cumulative.idxmin()
        
        return {
            'liquidation_occurred': liquidation_occurred,
            'liquidation_day': liquidation_day,
            'days_to_liquidation': days_to_liquidation,
            'max_loss': max_loss,
            'max_loss_day': max_loss_day,
            'safety_margin': abs(max_loss - liquidation_threshold) if not liquidation_occurred else 0
        }
    
    def _analyze_leverage_impact(self, positions: Dict[str, Dict],
                               crash_returns: Dict[str, pd.Series],
                               scenario: CrashScenario) -> Dict:
        """레버리지별 영향 분석"""
        
        leverage_analysis = {}
        
        # 다양한 레버리지 레벨에서 테스트
        leverage_levels = [1, 3, 5, 10, 20]
        
        for leverage in leverage_levels:
            total_value = sum(pos['notional_value'] for pos in positions.values())
            total_pnl = 0
            liquidations = 0
            
            for i, (symbol, position) in enumerate(positions.items()):
                asset_key = f'Asset_{i}'
                if asset_key in crash_returns:
                    returns = crash_returns[asset_key]
                    position_value = position['notional_value']
                    
                    # 레버리지 적용된 수익률
                    leveraged_returns = returns * leverage
                    cumulative_return = (1 + leveraged_returns).prod() - 1
                    
                    # 청산 확인
                    liquidation_threshold = -1.0 / leverage
                    if cumulative_return <= liquidation_threshold:
                        liquidations += 1
                        position_pnl = -position_value  # 전체 손실
                    else:
                        position_pnl = position_value * cumulative_return
                    
                    total_pnl += position_pnl
            
            portfolio_return = total_pnl / total_value if total_value > 0 else 0
            
            leverage_analysis[leverage] = {
                'leverage': leverage,
                'portfolio_return': portfolio_return,
                'total_pnl': total_pnl,
                'liquidated_positions': liquidations,
                'liquidation_rate': liquidations / len(positions),
                'portfolio_survival': (total_value + total_pnl) > 0,
                'risk_score': self._calculate_leverage_risk_score(
                    portfolio_return, liquidations, len(positions)
                )
            }
        
        return leverage_analysis
    
    def _calculate_leverage_risk_score(self, portfolio_return: float,
                                     liquidations: int, total_positions: int) -> float:
        """레버리지 리스크 점수 계산"""
        
        # 0-100 점수 (낮을수록 위험)
        loss_penalty = max(0, 100 + portfolio_return * 100)  # 손실에 따른 감점
        liquidation_penalty = (liquidations / total_positions) * 50  # 청산에 따른 감점
        
        risk_score = max(0, loss_penalty - liquidation_penalty)
        return risk_score
    
    def _analyze_recovery_scenario(self, positions: Dict[str, Dict],
                                 crash_returns: Dict[str, pd.Series],
                                 scenario: CrashScenario) -> Dict:
        """회복 시나리오 분석"""
        
        # 회복 기간 수익률 시뮬레이션
        recovery_returns = self._simulate_recovery_returns(
            crash_returns, scenario.recovery_period
        )
        
        # 회복 후 포트폴리오 가치
        total_value = sum(pos['notional_value'] for pos in positions.values())
        
        recovery_scenarios = {}
        
        # 다양한 회복 속도 시나리오
        recovery_speeds = {'slow': 0.5, 'normal': 1.0, 'fast': 1.5}
        
        for speed_name, speed_multiplier in recovery_speeds.items():
            adjusted_recovery = {
                asset: returns * speed_multiplier 
                for asset, returns in recovery_returns.items()
            }
            
            total_recovery_pnl = 0
            
            for i, (symbol, position) in enumerate(positions.items()):
                asset_key = f'Asset_{i}'
                if asset_key in adjusted_recovery:
                    position_value = position['notional_value']
                    leverage = position.get('leverage', 1)
                    
                    # 크래시 + 회복 전체 수익률
                    crash_cumret = (1 + crash_returns[asset_key]).prod() - 1
                    recovery_cumret = (1 + adjusted_recovery[asset_key]).prod() - 1
                    
                    # 크래시 후 잔존 가치에서 회복
                    post_crash_value = position_value * (1 + crash_cumret * leverage)
                    if post_crash_value > 0:  # 청산되지 않은 경우만
                        recovery_pnl = post_crash_value * recovery_cumret * leverage
                        total_recovery_pnl += recovery_pnl
            
            final_portfolio_value = total_value + total_recovery_pnl
            recovery_percentage = (final_portfolio_value / total_value - 1) * 100
            
            recovery_scenarios[speed_name] = {
                'speed_multiplier': speed_multiplier,
                'final_value': final_portfolio_value,
                'recovery_percentage': recovery_percentage,
                'time_to_breakeven': self._calculate_breakeven_time(
                    recovery_percentage, scenario.recovery_period
                )
            }
        
        return recovery_scenarios
    
    def _simulate_recovery_returns(self, crash_returns: Dict[str, pd.Series],
                                 recovery_period: int) -> Dict[str, pd.Series]:
        """회복 기간 수익률 시뮬레이션"""
        
        recovery_returns = {}
        
        for asset, crash_series in crash_returns.items():
            # 크래시 최종 수준에서 점진적 회복
            final_crash_level = (1 + crash_series).prod() - 1
            
            # 회복 곡선 (로그 함수 사용)
            recovery_dates = pd.date_range(
                start=crash_series.index[-1] + timedelta(days=1),
                periods=recovery_period,
                freq='D'
            )
            
            # 점진적 회복 (50% 회복 목표)
            recovery_target = abs(final_crash_level) * 0.5
            recovery_curve = recovery_target * (1 - np.exp(-np.linspace(0, 3, recovery_period)))
            
            # 일일 수익률로 변환
            daily_recovery = np.diff(np.concatenate([[0], recovery_curve]))
            
            # 변동성 추가
            noise = np.random.normal(0, 0.015, len(daily_recovery))  # 1.5% 변동성
            final_recovery = daily_recovery + noise
            
            recovery_returns[asset] = pd.Series(final_recovery, index=recovery_dates)
        
        return recovery_returns
    
    def _calculate_breakeven_time(self, recovery_percentage: float, 
                                recovery_period: int) -> int:
        """손익분기점 도달 시간 계산"""
        
        if recovery_percentage >= 0:
            return 0  # 이미 손익분기점 달성
        
        # 선형 근사로 손익분기점 추정
        breakeven_ratio = abs(recovery_percentage) / recovery_percentage if recovery_percentage != 0 else 1
        estimated_days = int(recovery_period * breakeven_ratio)
        
        return min(estimated_days, recovery_period * 2)  # 최대 2배 기간
    
    def _analyze_survival_probability(self, portfolio_impact: Dict,
                                    leverage_impact: Dict) -> Dict:
        """생존 확률 분석"""
        
        # 현재 포트폴리오 생존 여부
        current_survival = portfolio_impact['portfolio_survival']
        
        # 레버리지별 생존 확률
        leverage_survival = {}
        for leverage, impact in leverage_impact.items():
            leverage_survival[leverage] = impact['portfolio_survival']
        
        # 위험 레버리지 임계점 찾기
        safe_leverage = max([lev for lev, survival in leverage_survival.items() if survival], default=1)
        danger_leverage = min([lev for lev, survival in leverage_survival.items() if not survival], default=20)
        
        return {
            'current_portfolio_survival': current_survival,
            'leverage_survival_map': leverage_survival,
            'safe_max_leverage': safe_leverage,
            'danger_min_leverage': danger_leverage,
            'survival_rate_by_leverage': {
                lev: 1.0 if survival else 0.0 
                for lev, survival in leverage_survival.items()
            }
        }
    
    def generate_stress_test_report(self, scenario_names: List[str] = None) -> str:
        """스트레스 테스트 종합 보고서 생성"""
        
        if scenario_names is None:
            scenario_names = list(self.test_results.keys())
        
        report = []
        report.append("📋 **스트레스 테스트 종합 보고서**")
        report.append("=" * 50)
        report.append("")
        
        for scenario_name in scenario_names:
            if scenario_name not in self.test_results:
                continue
                
            result = self.test_results[scenario_name]
            scenario = result['scenario']
            portfolio_impact = result['portfolio_impact']
            survival_analysis = result['survival_analysis']
            
            report.append(f"## 🚨 {scenario.name}")
            report.append(f"**설명**: {scenario.description}")
            report.append(f"**기간**: {scenario.duration_days}일")
            report.append(f"**최대 하락**: {scenario.max_drawdown:.0%}")
            report.append("")
            
            report.append("### 📊 포트폴리오 영향")
            report.append(f"- 포트폴리오 수익률: {portfolio_impact['portfolio_return']:.1%}")
            report.append(f"- 총 P&L: ${portfolio_impact['total_pnl']:,.0f}")
            report.append(f"- 포트폴리오 생존: {'✅ 생존' if portfolio_impact['portfolio_survival'] else '❌ 청산'}")
            report.append(f"- 최악 포지션: {portfolio_impact['worst_position']}")
            report.append("")
            
            report.append("### ⚖️ 레버리지별 생존율")
            leverage_impact = result['leverage_impact']
            for leverage in [1, 3, 5, 10, 20]:
                if leverage in leverage_impact:
                    impact = leverage_impact[leverage]
                    status = "✅" if impact['portfolio_survival'] else "❌"
                    report.append(f"- {leverage}x: {status} (수익률: {impact['portfolio_return']:.1%})")
            report.append("")
            
            report.append("### 🔄 회복 시나리오")
            recovery_analysis = result['recovery_analysis']
            for speed, analysis in recovery_analysis.items():
                report.append(f"- {speed.capitalize()} 회복: {analysis['recovery_percentage']:.1%}")
            report.append("")
            
            report.append("### 💡 권장사항")
            safe_leverage = survival_analysis['safe_max_leverage']
            report.append(f"- 안전 최대 레버리지: {safe_leverage}x")
            
            if not portfolio_impact['portfolio_survival']:
                report.append("- ⚠️ 현재 포트폴리오는 이 시나리오에서 생존 불가")
                report.append("- 레버리지 감소 또는 리스크 분산 필요")
            
            report.append("")
            report.append("-" * 50)
            report.append("")
        
        return "\n".join(report)

# 실전 사용 예제
def run_comprehensive_stress_test():
    """종합 스트레스 테스트 실행"""
    
    print("💥 종합 스트레스 테스트 시작\n")
    
    # 스트레스 테스터 초기화
    stress_tester = StressTester()
    
    # 가상의 포트폴리오 포지션
    portfolio_positions = {
        'BTCUSDT': {
            'notional_value': 500000,
            'leverage': 5,
            'entry_price': 50000,
            'position_size': 10
        },
        'ETHUSDT': {
            'notional_value': 300000,
            'leverage': 3,
            'entry_price': 3000,
            'position_size': 100
        },
        'ADAUSDT': {
            'notional_value': 200000,
            'leverage': 10,
            'position_size': 400000,
            'entry_price': 0.5
        }
    }
    
    # 상관관계 매트릭스 (예시)
    correlation_matrix = pd.DataFrame([
        [1.0, 0.8, 0.6],
        [0.8, 1.0, 0.7],
        [0.6, 0.7, 1.0]
    ], index=['BTC', 'ETH', 'ADA'], columns=['BTC', 'ETH', 'ADA---

## 🔄 **동적 레버리지 조정**

### 📊 **변동성 기반 레버리지 스케일링**

시장 변동성에 따라 레버리지를 동적으로 조정하여 리스크를 일정하게 유지하는 시스템입니다.

```python
# user_data/strategies/modules/dynamic_leverage.py
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class LeverageConfig:
    """레버리지 설정 클래스"""
    base_leverage: int = 3
    max_leverage: int = 10
    min_leverage: int = 1
    target_volatility: float = 0.02
    volatility_window: int = 20
    adjustment_threshold: float = 0.1  # 10% 변화시 조정

class DynamicLeverageManager:
    """동적 레버리지 관리 시스템"""
    
    def __init__(self, config: LeverageConfig = None):
        self.config = config or LeverageConfig()
        self.volatility_history = {}
        self.leverage_history = {}
        
    def calculate_realized_volatility(self, price_series: pd.Series) -> float:
        """실현 변동성 계산"""
        
        if len(price_series) < self.config.volatility_window:
            return self.config.target_volatility
        
        # 수익률 계산
        returns = price_series.pct_change().dropna()
        
        # 롤링 변동성 (연환산)
        rolling_vol = returns.rolling(
            window=self.config.volatility_window
        ).std() * np.sqrt(252)
        
        return rolling_vol.iloc[-1] if not pd.isna(rolling_vol.iloc[-1]) else self.config.target_volatility
    
    def calculate_optimal_leverage(self, symbol: str, current_price: float,
                                 price_history: pd.Series) -> Dict[str, float]:
        """최적 레버리지 계산"""
        
        # 현재 변동성 계산
        current_volatility = self.calculate_realized_volatility(price_history)
        
        # 변동성 기반 레버리지 조정
        volatility_adjustment = self.config.target_volatility / current_volatility
        
        # 기본 레버리지에 변동성 조정 적용
        optimal_leverage = self.config.base_leverage * volatility_adjustment
        
        # 한계값 적용
        optimal_leverage = np.clip(
            optimal_leverage,
            self.config.min_leverage,
            self.config.max_leverage
        )
        
        # 변동성 체제 분류
        vol_regime = self._classify_volatility_regime(current_volatility)
        
        # 체제별 추가 조정
        regime_adjustment = self._get_regime_adjustment(vol_regime)
        final_leverage = optimal_leverage * regime_adjustment
        
        # 최종 한계값 재적용
        final_leverage = np.clip(
            final_leverage,
            self.config.min_leverage,
            self.config.max_leverage
        )
        
        # 정수로 반올림
        final_leverage = round(final_leverage)
        
        # 이력 저장
        self.volatility_history[symbol] = current_volatility
        self.leverage_history[symbol] = final_leverage
        
        return {
            'symbol': symbol,
            'current_volatility': current_volatility,
            'target_volatility': self.config.target_volatility,
            'volatility_ratio': current_volatility / self.config.target_volatility,
            'base_leverage': self.config.base_leverage,
            'volatility_adjusted_leverage': optimal_leverage,
            'regime': vol_regime,
            'regime_adjustment': regime_adjustment,
            'final_leverage': final_leverage,
            'leverage_change': self._calculate_leverage_change(symbol, final_leverage)
        }
    
    def _classify_volatility_regime(self, volatility: float) -> str:
        """변동성 체제 분류"""
        
        if volatility < self.config.target_volatility * 0.5:
            return "LOW_VOL"
        elif volatility < self.config.target_volatility * 1.5:
            return "NORMAL_VOL"
        elif volatility < self.config.target_volatility * 2.5:
            return "HIGH_VOL"
        else:
            return "EXTREME_VOL"
    
    def _get_regime_adjustment(self, regime: str) -> float:
        """체제별 조정 계수"""
        
        adjustments = {
            "LOW_VOL": 1.2,      # 낮은 변동성시 레버리지 증가
            "NORMAL_VOL": 1.0,   # 정상 변동성시 조정 없음
            "HIGH_VOL": 0.8,     # 높은 변동성시 레버리지 감소
            "EXTREME_VOL": 0.6   # 극한 변동성시 대폭 감소
        }
        
        return adjustments.get(regime, 1.0)
    
    def _calculate_leverage_change(self, symbol: str, new_leverage: int) -> Dict[str, any]:
        """레버리지 변화 계산"""
        
        if symbol not in self.leverage_history:
            return {
                'previous_leverage': None,
                'change_amount': 0,
                'change_percentage': 0,
                'should_adjust': False
            }
        
        previous_leverage = self.leverage_history.get(symbol, self.config.base_leverage)
        change_amount = new_leverage - previous_leverage
        change_percentage = (change_amount / previous_leverage) if previous_leverage > 0 else 0
        
        # 조정 필요성 판단
        should_adjust = abs(change_percentage) >= self.config.adjustment_threshold
        
        return {
            'previous_leverage': previous_leverage,
            'change_amount': change_amount,
            'change_percentage': change_percentage,
            'should_adjust': should_adjust
        }
    
    def create_leverage_adjustment_plan(self, positions: Dict[str, Dict],
                                      price_data: Dict[str, pd.Series]) -> Dict[str, Dict]:
        """레버리지 조정 계획 생성"""
        
        adjustment_plan = {}
        
        for symbol, position in positions.items():
            if symbol in price_data:
                # 최적 레버리지 계산
                leverage_analysis = self.calculate_optimal_leverage(
                    symbol, position['current_price'], price_data[symbol]
                )
                
                current_leverage = position.get('leverage', self.config.base_leverage)
                recommended_leverage = leverage_analysis['final_leverage']
                
                # 조정 필요성 평가
                adjustment_needed = leverage_analysis['leverage_change']['should_adjust']
                
                if adjustment_needed:
                    # 조정 전략 수립
                    adjustment_strategy = self._plan_leverage_adjustment(
                        symbol, current_leverage, recommended_leverage, position
                    )
                    
                    adjustment_plan[symbol] = {
                        'analysis': leverage_analysis,
                        'adjustment_strategy': adjustment_strategy,
                        'priority': self._calculate_adjustment_priority(leverage_analysis),
                        'estimated_impact': self._estimate_adjustment_impact(
                            position, current_leverage, recommended_leverage
                        )
                    }
        
        return adjustment_plan
    
    def _plan_leverage_adjustment(self, symbol: str, current_leverage: int,
                                target_leverage: int, position: Dict) -> Dict:
        """레버리지 조정 전략 수립"""
        
        position_size = position['position_size']
        current_margin = position_size / current_leverage
        target_margin = position_size / target_leverage
        margin_difference = target_margin - current_margin
        
        if target_leverage > current_leverage:
            # 레버리지 증가 (마진 감소)
            strategy_type = "INCREASE_LEVERAGE"
            action_required = "REDUCE_MARGIN"
            margin_to_free = abs(margin_difference)
        else:
            # 레버리지 감소 (마진 증가)
            strategy_type = "DECREASE_LEVERAGE"
            action_required = "ADD_MARGIN"
            margin_to_add = abs(margin_difference)
        
        return {
            'strategy_type': strategy_type,
            'action_required': action_required,
            'current_leverage': current_leverage,
            'target_leverage': target_leverage,
            'current_margin': current_margin,
            'target_margin': target_margin,
            'margin_adjustment': abs(margin_difference),
            'adjustment_percentage': abs(margin_difference) / current_margin if current_margin > 0 else 0
        }
    
    def _calculate_adjustment_priority(self, leverage_analysis: Dict) -> str:
        """조정 우선순위 계산"""
        
        volatility_ratio = leverage_analysis['volatility_ratio']
        regime = leverage_analysis['regime']
        change_percentage = abs(leverage_analysis['leverage_change']['change_percentage'])
        
        if regime == "EXTREME_VOL" or change_percentage > 0.5:
            return "HIGH"
        elif regime == "HIGH_VOL" or change_percentage > 0.3:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _estimate_adjustment_impact(self, position: Dict, 
                                  current_leverage: int, 
                                  target_leverage: int) -> Dict:
        """조정 영향 추정"""
        
        position_size = position['position_size']
        current_exposure = position_size * current_leverage
        target_exposure = position_size * target_leverage
        
        exposure_change = target_exposure - current_exposure
        exposure_change_pct = exposure_change / current_exposure if current_exposure > 0 else 0
        
        # 리스크 변화 추정
        risk_multiplier = target_leverage / current_leverage
        
        return {
            'exposure_change': exposure_change,
            'exposure_change_percentage': exposure_change_pct,
            'risk_multiplier': risk_multiplier,
            'estimated_var_change': (risk_multiplier - 1) * 100,  # VaR 변화율 (%)
            'capital_efficiency_change': target_leverage / current_leverage - 1
        }

# 백테스팅 시스템
class LeverageBacktester:
    """동적 레버리지 백테스팅"""
    
    def __init__(self, dynamic_manager: DynamicLeverageManager):
        self.dynamic_manager = dynamic_manager
        self.backtest_results = {}
        
    def run_leverage_backtest(self, price_data: Dict[str, pd.Series],
                            initial_capital: float = 100000,
                            rebalance_frequency: int = 7) -> Dict:
        """레버리지 전략 백테스팅"""
        
        results = {
            'static_leverage': {},
            'dynamic_leverage': {},
            'comparison': {}
        }
        
        for symbol, prices in price_data.items():
            print(f"📊 {symbol} 백테스팅 중...")
            
            # 정적 레버리지 (고정 3배)
            static_results = self._backtest_static_leverage(
                prices, initial_capital, leverage=3
            )
            
            # 동적 레버리지
            dynamic_results = self._backtest_dynamic_leverage(
                prices, initial_capital, rebalance_frequency
            )
            
            # 결과 저장
            results['static_leverage'][symbol] = static_results
            results['dynamic_leverage'][symbol] = dynamic_results
            
            # 성과 비교
            comparison = self._compare_strategies(static_results, dynamic_results)
            results['comparison'][symbol] = comparison
        
        return results
    
    def _backtest_static_leverage(self, prices: pd.Series, 
                                initial_capital: float, leverage: int) -> Dict:
        """정적 레버리지 백테스팅"""
        
        returns = prices.pct_change().dropna()
        leveraged_returns = returns * leverage
        
        # 누적 수익률
        cumulative_returns = (1 + leveraged_returns).cumprod()
        final_value = initial_capital * cumulative_returns.iloc[-1]
        
        # 성과 지표
        total_return = (final_value / initial_capital) - 1
        volatility = leveraged_returns.std() * np.sqrt(252)
        sharpe_ratio = leveraged_returns.mean() / leveraged_returns.std() * np.sqrt(252)
        max_drawdown = self._calculate_max_drawdown(cumulative_returns)
        
        return {
            'strategy': 'static_leverage',
            'leverage': leverage,
            'final_value': final_value,
            'total_return': total_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'cumulative_returns': cumulative_returns
        }
    
    def _backtest_dynamic_leverage(self, prices: pd.Series,
                                 initial_capital: float,
                                 rebalance_frequency: int) -> Dict:
        """동적 레버리지 백테스팅"""
        
        portfolio_value = initial_capital
        leverage_history = []
        value_history = []
        
        for i in range(len(prices)):
            if i < self.dynamic_manager.config.volatility_window:
                current_leverage = self.dynamic_manager.config.base_leverage
            else:
                # 과거 데이터로 레버리지 계산
                price_window = prices.iloc[:i+1]
                leverage_analysis = self.dynamic_manager.calculate_optimal_leverage(
                    'BACKTEST', prices.iloc[i], price_window
                )
                current_leverage = leverage_analysis['final_leverage']
            
            leverage_history.append(current_leverage)
            
            # 수익률 적용 (다음 기간)
            if i < len(prices) - 1:
                price_change = (prices.iloc[i+1] / prices.iloc[i]) - 1
                leveraged_return = price_change * current_leverage
                portfolio_value *= (1 + leveraged_return)
            
            value_history.append(portfolio_value)
        
        # 성과 지표 계산
        value_series = pd.Series(value_history, index=prices.index)
        returns_series = value_series.pct_change().dropna()
        
        total_return = (portfolio_value / initial_capital) - 1
        volatility = returns_series.std() * np.sqrt(252)
        sharpe_ratio = returns_series.mean() / returns_series.std() * np.sqrt(252) if returns_series.std() > 0 else 0
        max_drawdown = self._calculate_max_drawdown(value_series / initial_capital)
        
        return {
            'strategy': 'dynamic_leverage',
            'final_value': portfolio_value,
            'total_return': total_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'leverage_history': leverage_history,
            'value_history': value_series,
            'avg_leverage': np.mean(leverage_history),
            'leverage_volatility': np.std(leverage_history)
        }
    
    def _calculate_max_drawdown(self, cumulative_returns: pd.Series) -> float:
        """최대 낙폭 계산"""
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        return abs(drawdown.min())
    
    def _compare_strategies(self, static_results: Dict, dynamic_results: Dict) -> Dict:
        """전략 비교"""
        
        return {
            'return_improvement': dynamic_results['total_return'] - static_results['total_return'],
            'sharpe_improvement': dynamic_results['sharpe_ratio'] - static_results['sharpe_ratio'],
            'volatility_reduction': static_results['volatility'] - dynamic_results['volatility'],
            'drawdown_improvement': static_results['max_drawdown'] - dynamic_results['max_drawdown'],
            'dynamic_advantage': dynamic_results['sharpe_ratio'] > static_results['sharpe_ratio']
        }

# 실시간 레버리지 조정 시스템
class RealTimeLeverageAdjuster:
    """실시간 레버리지 조정 시스템"""
    
    def __init__(self, exchange, dynamic_manager: DynamicLeverageManager):
        self.exchange = exchange
        self.dynamic_manager = dynamic_manager
        self.adjustment_cooldown = 3600  # 1시간 쿨다운
        self.last_adjustments = {}
        
    async def monitor_and_adjust(self, symbols: List[str], 
                               check_interval: int = 300):  # 5분마다 체크
        """레버리지 모니터링 및 자동 조정"""
        
        print("🔄 실시간 레버리지 조정 시스템 시작...")
        
        while True:
            try:
                for symbol in symbols:
                    await self._check_and_adjust_leverage(symbol)
                
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                print(f"⚠️ 레버리지 조정 오류: {e}")
                await asyncio.sleep(check_interval)
    
    async def _check_and_adjust_leverage(self, symbol: str):
        """개별 심볼 레버리지 확인 및 조정"""
        
        try:
            # 현재 포지션 정보 가져오기
            position = await self._get_current_position(symbol)
            
            if not position or float(position['positionAmt']) == 0:
                return  # 포지션 없음
            
            # 가격 데이터 가져오기
            price_history = await self._get_price_history(symbol)
            current_price = float(position['markPrice'])
            
            # 최적 레버리지 계산
            leverage_analysis = self.dynamic_manager.calculate_optimal_leverage(
                symbol, current_price, price_history
            )
            
            current_leverage = int(float(position['leverage']))
            recommended_leverage = leverage_analysis['final_leverage']
            
            # 조정 필요성 확인
            if leverage_analysis['leverage_change']['should_adjust']:
                # 쿨다운 확인
                if self._is_cooldown_active(symbol):
                    return
                
                # 레버리지 조정 실행
                success = await self._execute_leverage_adjustment(
                    symbol, current_leverage, recommended_leverage
                )
                
                if success:
                    self.last_adjustments[symbol] = datetime.now()
                    print(f"✅ {symbol} 레버리지 조정: {current_leverage}x → {recommended_leverage}x")
                    
                    # 알림 발송
                    await self._send_adjustment_notification(
                        symbol, current_leverage, recommended_leverage, leverage_analysis
                    )
        
        except Exception as e:
            print(f"❌ {symbol} 레버리지 확인 실패: {e}")
    
    def _is_cooldown_active(self, symbol: str) -> bool:
        """쿨다운 활성 여부 확인"""
        
        if symbol not in self.last_adjustments:
            return False
        
        last_adjustment = self.last_adjustments[symbol]
        time_since_last = (datetime.now() - last_adjustment).total_seconds()
        
        return time_since_last < self.adjustment_cooldown
    
    async def _execute_leverage_adjustment(self, symbol: str,
                                         current_leverage: int,
                                         target_leverage: int) -> bool:
        """레버리지 조정 실행"""
        
        try:
            # 바이낸스 API를 통한 레버리지 변경
            result = self.exchange._api.futures_change_leverage(
                symbol=symbol.replace('/', ''),
                leverage=target_leverage
            )
            
            return result.get('leverage') == target_leverage
            
        except Exception as e:
            print(f"❌ 레버리지 조정 실패 ({symbol}): {e}")
            return False
    
    async def _get_current_position(self, symbol: str) -> Dict:
        """현재 포지션 정보 조회"""
        
        try:
            positions = self.exchange._api.futures_position_information()
            
            for pos in positions:
                if pos['symbol'] == symbol.replace('/', '') and float(pos['positionAmt']) != 0:
                    return pos
            
            return None
            
        except Exception as e:
            print(f"❌ 포지션 조회 실패 ({symbol}): {e}")
            return None
    
    async def _get_price_history(self, symbol: str, limit: int = 100) -> pd.Series:
        """가격 이력 조회"""
        
        try:
            # 1시간 봉 데이터 조회
            klines = self.exchange._api.futures_klines(
                symbol=symbol.replace('/', ''),
                interval='1h',
                limit=limit
            )
            
            # 종가 데이터 추출
            closes = [float(kline[4]) for kline in klines]
            timestamps = [pd.to_datetime(kline[0], unit='ms') for kline in klines]
            
            return pd.Series(closes, index=timestamps)
            
        except Exception as e:
            print(f"❌ 가격 데이터 조회 실패 ({symbol}): {e}")
            return pd.Series()
    
    async def _send_adjustment_notification(self, symbol: str,
                                          old_leverage: int,
                                          new_leverage: int,
                                          analysis: Dict):
        """조정 알림 발송"""
        
        message = f"""
🔄 **레버리지 자동 조정**

📈 **심볼**: {symbol}
📊 **레버리지**: {old_leverage}x → {new_leverage}x
📉 **변동성**: {analysis['current_volatility']:.2%} (목표: {analysis['target_volatility']:.2%})
⚖️ **체제**: {analysis['regime']}
📈 **변화율**: {analysis['leverage_change']['change_percentage']:.1%}

*시장 변동성 변화에 따른 자동 조정입니다.*
        """
        
        # 텔레그램 알림 (구현 필요)
        print(message)

# 실전 사용 예제
def demonstrate_dynamic_leverage():
    """동적 레버리지 시스템 실증"""
    
    print("🔄 동적 레버리지 시스템 데모\n")
    
    # 설정 초기화
    config = LeverageConfig(
        base_leverage=3,
        max_leverage=10,
        min_leverage=1,
        target_volatility=0.025,  # 2.5% 목표 변동성
        volatility_window=20
    )
    
    # 동적 레버리지 매니저
    dynamic_manager = DynamicLeverageManager(config)
    
    # 가상의 가격 데이터 생성 (변동성 변화 시뮬레이션)
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=200)
    
    # 3단계 변동성 시나리오
    price_data = []
    base_price = 50000
    
    for i in range(len(dates)):
        if i < 50:  # 낮은 변동성 구간
            volatility = 0.015
        elif i < 150:  # 높은 변동성 구간
            volatility = 0.045
        else:  # 정상 변동성 구간
            volatility = 0.025
        
        daily_return = np.random.normal(0.0005, volatility)
        base_price *= (1 + daily_return)
        price_data.append(base_price)
    
    btc_prices = pd.Series(price_data, index=dates)
    
    # 동적 레버리지 분석
    print("📊 기간별 레버리지 분석:")
    
    leverage_recommendations = []
    volatility_measurements = []
    
    for i in range(20, len(dates), 10):  # 10일마다 분석
        price_window = btc_prices.iloc[:i]
        analysis = dynamic_manager.calculate_optimal_leverage(
            'BTCUSDT', btc_prices.iloc[i], price_window
        )
        
        leverage_recommendations.append(analysis['final_leverage'])
        volatility_measurements.append(analysis['current_volatility'])
        
        if i in [30, 80, 130, 180]:  # 주요 시점 출력
            print(f"Day {i}:")
            print(f"  변동성: {analysis['current_volatility']:.2%}")
            print(f"  체제: {analysis['regime']}")
            print(f"  권장 레버리지: {analysis['final_leverage']}x")
            print(f"  조정 사유: 변동성 비율 {analysis['volatility_ratio']:.2f}")
            print()
    
    # 백테스팅 실행
    print("📈 백테스팅 비교:")
    
    backtester = LeverageBacktester(dynamic_manager)
    backtest_results = backtester.run_leverage_backtest(
        {'BTCUSDT': btc_prices},
        initial_capital=100000,
        rebalance_frequency=7
    )
    
    btc_results = backtest_results['comparison']['BTCUSDT']
    static_performance = backtest_results['static_leverage']['BTCUSDT']
    dynamic_performance = backtest_results['dynamic_leverage']['BTCUSDT']
    
    print(f"정적 레버리지 (3x):")
    print(f"  총 수익률: {static_performance['total_return']:.1%}")
    print(f"  샤프 비율: {static_performance['sharpe_ratio']:.2f}")
    print(f"  최대 낙폭: {static_performance['max_drawdown']:.1%}")
    print(f"  변동성: {static_performance['volatility']:.1%}")
    
    print(f"\n동적 레버리지:")
    print(f"  총 수익률: {dynamic_performance['total_return']:.1%}")
    print(f"  샤프 비율: {dynamic_performance['sharpe_ratio']:.2f}")
    print(f"  최대 낙폭: {dynamic_performance['max_drawdown']:.1%}")
    print(f"  변동성: {dynamic_performance['volatility']:.1%}")
    print(f"  평균 레버리지: {dynamic_performance['avg_leverage']:.1f}x")
    
    print(f"\n📊 성과 개선:")
    print(f"  수익률 개선: {btc_results['return_improvement']:+.1%}")
    print(f"  샤프 비율 개선: {btc_results['sharpe_improvement']:+.2f}")
    print(f"  변동성 감소: {btc_results['volatility_reduction']:+.1%}")
    print(f"  낙폭 개선: {btc_results['drawdown_improvement']:+.1%}")
    
    # 레버리지 변화 시각화 데이터
    print(f"\n🔄 레버리지 변화 패턴:")
    leverage_changes = np.diff(leverage_recommendations)
    print(f"  평균 레버리지: {np.mean(leverage_recommendations):.1f}x")
    print(f"  레버리지 변동성: {np.std(leverage_recommendations):.1f}")
    print(f"  조정 빈도: {np.sum(np.abs(leverage_changes) > 0)} / {len(leverage_changes)} 회")

# 실행
demonstrate_dynamic_leverage()
```

---

## 📈 **포트폴리오 레벨 리스크 관리**

### 🔗 **Multi-Strategy 리스크 분산**

여러 전략을 동시에 운영할 때의 포트폴리오 레벨 리스크 관리 시스템입니다.

```python
# user_data/strategies/modules/portfolio_risk.py
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from typing import Dict, List, Tuple
import networkx as nx
from dataclasses import dataclass

@dataclass
class StrategyConfig:
    """전략 설정 클래스"""
    name: str
    max_allocation: float  # 최대 할당 비율
    target_sharpe: float   # 목표 샤프 비율
    max_drawdown_limit: float  # 최대 낙폭 한계
    correlation_limit: float   # 상관관계 한계

class PortfolioRiskManager:
    """포트폴리오 레벨 리스크 관리"""
    
    def __init__(self, max_portfolio_leverage: int = 5):
        self.max_portfolio_leverage = max_portfolio_leverage
        self.strategies = {}
        self.correlation_matrix = pd.DataFrame()
        self.risk_budget = {}
        
    def add_strategy(self, strategy_name: str, config: StrategyConfig,
                    historical_returns: pd.Series):
        """전략 추가"""
        
        self.strategies[strategy_name] = {
            'config': config,
            'returns': historical_returns,
            'current_allocation': 0.0,
            'risk_metrics': self._calculate_strategy_metrics(historical_returns)
        }
        
        # 상관관계 매트릭스 업데이트
        self._update_correlation_matrix()
    
    def _calculate_strategy_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """전략별 리스크 메트릭스 계산"""
        
        return {
            'expected_return': returns.mean() * 252,
            'volatility': returns.std() * np.sqrt(252),
            'sharpe_ratio': returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0,
            'max_drawdown': self._calculate_max_drawdown(returns),
            'var_95': np.percentile(-returns, 95),
            'skewness': returns.skew(),
            'kurtosis': returns.kurtosis()
        }
    
    def _update_correlation_matrix(self):
        """상관관계 매트릭스 업데이트"""
        
        if len(self.strategies) < 2:
            return
        
        returns_data = pd.DataFrame()
        for name, strategy in self.strategies.items():
            returns_data[name] = strategy['returns']
        
        self.correlation_matrix = returns_data.corr()
    
    def optimize_portfolio_allocation(self, total_capital: float,
                                    risk_target: float = 0.15) -> Dict[str, float]:
        """포트폴리오 최적 할당 계산"""
        
        if len(self.strategies) < 2:
            print("⚠️ 최소 2개 이상의 전략이 필요합니다.")
            return {}
        
        # 기대수익률과 공분산 매트릭스 준비
        expected_returns = np.array([
            strategy['risk_metrics']['expected_return'] 
            for strategy in self.strategies.values()
        ])
        
        # 공분산 매트릭스 계산
        returns_matrix = pd.DataFrame({
            name: strategy['returns'] 
            for name, strategy in self.strategies.items()
        })
        cov_matrix = returns_matrix.cov() * 252  # 연환산
        
        # 제약 조건 설정
        constraints = self._build_optimization_constraints()
        bounds = self._build_optimization_bounds()
        
        # 목적함수: 샤프 비율 최대화
        def objective(weights):
            portfolio_return = np.sum(weights * expected_returns)
            portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
            portfolio_volatility = np.sqrt(portfolio_variance)
            
            if portfolio_volatility == 0:
                return -np.inf
            
            sharpe_ratio = portfolio_return / portfolio_volatility
            return -sharpe_ratio  # 최소화 문제로 변환
        
        # 최적화 실행
        n_assets = len(self.strategies)
        initial_weights = np.array([1/n_assets] * n_assets)
        
        result = minimize(
            objective,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        if result.success:
            optimal_weights = result.x
            strategy_names = list(self.strategies.keys())
            
            # 자본 할당 계산
            allocation = {}
            for i, name in enumerate(strategy_names):
                allocation[name] = {
                    'weight': optimal_weights[i],
                    'capital': total_capital * optimal_weights[i],
                    'expected_return': expected_returns[i] * optimal_weights[i],
                    'risk_contribution': self._calculate_risk_contribution(
                        optimal_weights, cov_matrix, i
                    )
                }
            
            # 포트폴리오 메트릭스
            portfolio_metrics = self._calculate_portfolio_metrics(
                optimal_weights, expected_returns, cov_matrix
            )
            
            return {
                'allocations': allocation,
                'portfolio_metrics': portfolio_metrics,
                'optimization_success': True,
                'total_allocated': sum(w for w in optimal_weights)
            }
        
        else:
            print(f"❌ 최적화 실패: {result.message}")
            return {'optimization_success': False}
    
    def _build_optimization_constraints(self) -> List[Dict]:
        """최적화 제약 조건"""
        
        constraints = []
        
        # 가중치 합 = 1
        constraints.append({
            'type': 'eq',
            'fun': lambda x: np.sum(x) - 1
        })
        
        # 상관관계 제약 (고상관 전략들의 합 제한)
        if len(self.correlation_matrix) > 1:
            high_corr_pairs = self._find_high_correlation_pairs(threshold=0.8)
            
            for pair in high_corr_pairs:
                i, j = pair
                constraints.append({
                    'type': 'ineq',
                    'fun': lambda x, i=i, j=j: 0.6 - (x[i] + x[j])  # 고상관 전략 합계 60% 제한
                })
        
        return constraints
    
    def _build_optimization_bounds(self) -> List[Tuple[float, float]]:
        """최적화 경계 조건"""
        
        bounds = []
        for name, strategy in self.strategies.items():
            max_allocation = strategy['config'].max_allocation
            bounds.append((0.0, max_allocation))
        
        return bounds
    
    def _find_high_correlation_pairs(self, threshold: float = 0.8) -> List[Tuple[int, int]]:
        """고상관 전략 쌍 찾기"""
        
        high_corr_pairs = []
        n = len(self.correlation_matrix)
        
        for i in range(n):
            for j in range(i+1, n):
                if abs(self.correlation_matrix.iloc[i, j]) > threshold:
                    high_corr_pairs.append((i, j))
        
        return high_corr_pairs
    
    def _calculate_risk_contribution(self, weights: np.ndarray,
                                   cov_matrix: pd.DataFrame, asset_index: int) -> float:
        """리스크 기여도 계산"""
        
        portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
        marginal_contribution = np.dot(cov_matrix, weights)[asset_index]
        risk_contribution = weights[asset_index] * marginal_contribution / portfolio_variance
        
        return risk_contribution
    
    def _calculate_portfolio_metrics(self, weights: np.ndarray,
                                   expected_returns: np.ndarray,
                                   cov_matrix: pd.DataFrame) -> Dict[str, float]:
        """포트폴리오 메트릭스 계산"""
        
        portfolio_return = np.sum(weights * expected_returns)
        portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
        portfolio_volatility = np.sqrt(portfolio_variance)
        sharpe_ratio = portfolio_return / portfolio_volatility if portfolio_volatility > 0 else 0
        
        return {
            'expected_return': portfolio_return,
            'volatility': portfolio_volatility,
            'sharpe_ratio': sharpe_ratio,
            'diversification_ratio': self._calculate_diversification_ratio(weights, cov_matrix)
        }
    
    def _calculate_diversification_ratio(self, weights: np.ndarray,
                                       cov_matrix: pd.DataFrame) -> float:
        """다각화 비율 계산"""
        
        # 가중평균 변동성
        individual_volatilities = np.sqrt(np.diag(cov_matrix))
        weighted_avg_vol = np.sum(weights * individual_volatilities)
        
        # 포트폴리오 변동성
        portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
        
        return weighted_avg_vol / portfolio_vol if portfolio_vol > 0 else 1.0

class RiskBudgetManager:
    """리스크 예산 관리"""
    
    def __init__(self, total_risk_budget: float = 0.02):
        self.total_risk_budget = total_risk_budget  # 전체 포트폴리오 일일 VaR 한도
        self.strategy_budgets = {}
        self.used_budget = {}
        
    def allocate_risk_budget(self, strategies: Dict[str, Dict],
                           allocation_method: str = 'equal_risk') -> Dict[str, float]:
        """리스크 예산 할당"""
        
        if allocation_method == 'equal_risk':
            # 동일 리스크 할당
            risk_per_strategy = self.total_risk_budget / len(strategies)
            
            for strategy_name in strategies.keys():
                self.strategy_budgets[strategy_name] = risk_per_strategy
                
        elif allocation_method == 'performance_weighted':
            # 성과 가중 할당
            sharpe_ratios = {
                name: strategy['risk_metrics']['sharpe_ratio']
                for name, strategy in strategies.items()
            }
            
            total_sharpe = sum(max(0, sharpe) for sharpe in sharpe_ratios.values())
            
            for name, sharpe in sharpe_ratios.items():
                if total_sharpe > 0:
                    weight = max(0, sharpe) / total_sharpe
                    self.strategy_budgets[name] = self.total_risk_budget * weight
                else:
                    self.strategy_budgets[name] = self.total_risk_budget / len(strategies)
        
        elif allocation_method == 'volatility_inverse':
            # 변동성 역가중 할당
            volatilities = {
                name: strategy['risk_metrics']['volatility']
                for name, strategy in strategies.items()
            }
            
            inverse_vols = {name: 1/vol if vol > 0 else 1 for name, vol in volatilities.items()}
            total_inverse_vol = sum(inverse_vols.values())
            
            for name, inv_vol in inverse_vols.items():
                weight = inv_vol / total_inverse_vol
                self.strategy_budgets[name] = self.total_risk_budget * weight
        
        return self.strategy_budgets
    
    def monitor_risk_usage(self, current_positions: Dict[str, Dict]) -> Dict[str, Dict]:
        """리스크 사용량 모니터링"""
        
        usage_report = {}
        
        for strategy_name, budget in self.strategy_budgets.items():
            if strategy_name in current_positions:
                position = current_positions[strategy_name]
                
                # 현재 VaR 계산 (간단한 근사)
                current_exposure = position.get('notional_value', 0)
                volatility = position.get('volatility', 0.02)
                current_var = current_exposure * volatility * 1.65  # 95% VaR 근사
                
                usage_ratio = current_var / budget if budget > 0 else 0
                remaining_budget = budget - current_var
                
                usage_report[strategy_name] = {
                    'allocated_budget': budget,
                    'used_budget': current_var,
                    'usage_ratio': usage_ratio,
                    'remaining_budget': remaining_budget,
                    'status': self._get_usage_status(usage_ratio)
                }
        
        return usage_report
    
    def _get_usage_status(self, usage_ratio: float) -> str:
        """사용량 상태 평가"""
        
        if usage_ratio > 1.0:
            return "OVER_BUDGET"
        elif usage_ratio > 0.8:
            return "HIGH_USAGE"
        elif usage_ratio > 0.5:
            return "MODERATE_USAGE"
        else:
            return "LOW_USAGE"
    
    def suggest_position_adjustments(self, usage_report: Dict[str, Dict]) -> List[Dict]:
        """포지션 조정 제안"""
        
        suggestions = []
        
        for strategy_name, usage in usage_report.items():
            if usage['status'] == 'OVER_BUDGET':
                reduction_needed = usage['used_budget'] - usage['allocated_budget']
                reduction_ratio = reduction_needed / usage['used_budget']
                
                suggestions.append({
                    'strategy': strategy_name,
                    'action': 'REDUCE_POSITION',
                    'reduction_ratio': reduction_ratio,
                    'priority': 'HIGH',
                    'reason': f"예산 초과: {usage['usage_ratio']:.1%}"
                })
                
            elif usage['status'] == 'LOW_USAGE' and usage['usage_ratio'] < 0.3:
                increase_potential = usage['remaining_budget'] / usage['allocated_budget']
                
                suggestions.append({
                    'strategy': strategy_name,
                    'action': 'INCREASE_POSITION',
                    'increase_potential': increase_potential,
                    'priority': 'LOW',
                    'reason': f"예산 여유: {usage['usage_ratio']:.1%}"
                })
        
        return suggestions

# 실전 사용 예제
def demonstrate_portfolio_risk_management():
    """포트폴리오 리스크 관리 실증"""
    
    print("📊 포트폴리오 리스크 관리 시스템 데모\n")
    
    # 포트폴리오 매니저 초기화
    portfolio_manager = PortfolioRiskManager(max_portfolio_leverage=5)
    
    # 가상의 전략 수익률 데이터 생성
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=252)
    
    # 전략 1: 트렌드 팔로잉 (높은 수익, 높은 변동성)
    trend_returns = pd.Series(
        np.random.normal(0.0015, 0.025, 252),  # 연 38% 수익, 40% 변동성
        index=dates
    )
    
    # 전략 2: 평균 회귀 (중간 수익, 낮은 변동성)
    mean_revert_returns = pd.Series(
        np.random.normal(0.0008, 0.015, 252),  # 연 20% 수익, 24% 변동성
        index=dates
    )
    
    # 전략 3: 볼린저 밴드 (낮은 수익, 중간 변동성, 트렌드와 음의 상관관계)
    bollinger_returns = pd.Series(
        np.random.normal(0.0005, 0.020, 252) - 0.3 * trend_returns,  # 트렌드와 음의 상관관계
        index=dates
    )
    
    # 전략 설정
    strategy_configs = {
        'TrendFollowing': StrategyConfig(
            name='TrendFollowing',
            max_allocation=0.5,
            target_sharpe=1.5,
            max_drawdown_limit=0.15,
            correlation_limit=0.7
        ),
        'MeanReversion': StrategyConfig(
            name='MeanReversion',
            max_allocation=0.4,
            target_sharpe=1.2,
            max_drawdown_limit=0.10,
            correlation_limit=0.7
        ),
        'BollingerBands': StrategyConfig(
            name='BollingerBands',
            max_allocation=0.3,
            target_sharpe=1.0,
            max_drawdown_limit=0.12,
            correlation_limit=0.7
        )
    }
    
    # 전략 추가
    portfolio_manager.add_strategy('TrendFollowing', strategy_configs['TrendFollowing'], trend_returns)
    portfolio_manager.add_strategy('MeanReversion', strategy_configs['MeanReversion'], mean_revert_returns)
    portfolio_manager.add_strategy('BollingerBands', strategy_configs['BollingerBands'], bollinger_returns)
    
    print("📈 개별 전략 분석:")
    for name, strategy in portfolio_manager.strategies.items():
        metrics = strategy['risk_metrics']
        print(f"{name}:")
        print(f"  기대수익률: {metrics['expected_return']:.1%}")
        print(f"  변동성: {metrics['volatility']:.1%}")
        print(f"  샤프 비율: {metrics['sharpe_ratio']:.2f}")
        print(f"  최대 낙폭: {metrics['max_drawdown']:.1%}")
        print()
    
    # 상관관계 분석
    print("🔗 전략 간 상관관계:")
    print(portfolio_manager.correlation_matrix.round(3))
    print()
    
    # 포트폴리오 최적화
    total_capital = 1000000  # $1M
    optimization_result = portfolio_manager.optimize_portfolio_allocation(total_capital)
    
    if optimization_result['optimization_success']:
        print("⚖️ 최적 포트폴리오 할당:")
        
        allocations = optimization_result['allocations']
        for name, allocation in allocations.items():
            print(f"{name}:")
            print(f"  가중치: {allocation['weight']:.1%}")
            print(f"  자본: ${allocation['capital']:,.0f}")
            print(f"  리스크 기여도: {allocation['risk_contribution']:.1%}")
            print()
        
        portfolio_metrics = optimization_result['portfolio_metrics']
        print("📊 포트폴리오 메트릭스:")
        print(f"기대수익률: {portfolio_metrics['expected_return']:.1%}")
        print(f"변동성: {portfolio_metrics['volatility']:.1%}")
        print(f"샤프 비율: {portfolio_metrics['sharpe_ratio']:.2f}")
        print(f"다각화 비율: {portfolio_metrics['diversification_ratio']:.2f}")
        print()
    
    # 리스크 예산 관리
    print("💰 리스크 예산 관리:")
    
    risk_budget_manager = RiskBudgetManager(total_risk_budget=0.025)  # 2.5% 일일 VaR 한도
    
    # 성과 가중 방식으로 리스크 예산 할당
    budget_allocation = risk_budget_manager.allocate_risk_budget(
        portfolio_manager.strategies, 
        allocation_method='performance_weighted'
    )
    
    print("리스크 예산 할당:")
    for strategy, budget in budget_allocation.items():
        print(f"  {strategy}: {budget:.3f} ({budget/risk_budget_manager.total_risk_budget:.1%})")
    print()
    
    # 가상의 현재 포지션
    current_positions = {
        'TrendFollowing': {'notional_value': 400000, 'volatility': 0.04},
        'MeanReversion': {'notional_value': 300000, 'volatility': 0.024},
        'BollingerBands': {'notional_value': 200000, 'volatility': 0.032}
    }
    
    # 리스크 사용량 모니터링
    usage_report = risk_budget_manager.monitor_risk_usage(current_positions)
    
    print("📊 리스크 사용량 현황:")
    for strategy, usage in usage_report.items():
        print(f"{strategy}:")
        print(f"  할당 예산: {usage['allocated_budget']:.4f}")
        print(f"  사용 예산: {usage['used_budget']:.4f}")
        print(f"  사용률: {usage['usage_ratio']:.1%}")
        print(f"  상태: {usage['status']}")
        print()
    
    # 조정 제안
    suggestions = risk_budget_manager.suggest_position_adjustments(usage_report)
    
    if suggestions:
        print("💡 포지션 조정 제안:")
        for suggestion in suggestions:
            print(f"  {suggestion['strategy']}: {suggestion['action']}")
            print(f"    사유: {suggestion['reason']}")
            print(f"    우선순위: {suggestion['priority']}")
            if 'reduction_ratio' in suggestion:
                print(f"    권장 축소: {suggestion['reduction_ratio']:.1%}")
            print()

# 실행
demonstrate_portfolio_risk_management()
```# 07_LEVERAGE_RISK_MANAGEMENT.md

<div align="center">

# ⚖️ **Freqtrade Futures: 레버리지 리스크 관리 완전 가이드** ⚖️

## 📋 **Binance USDT Perpetual Futures 전용 전문가급 리스크 관리**

[![Leverage Management](https://img.shields.io/badge/Leverage-Risk%20Management-critical?style=for-the-badge&logo=balance-scale)](https://binance.com)
[![Kelly Criterion](https://img.shields.io/badge/Position%20Sizing-Kelly%20Criterion-success?style=for-the-badge&logo=calculator)](https://en.wikipedia.org/wiki/Kelly_criterion)
[![VaR Analysis](https://img.shields.io/badge/Risk%20Metrics-VaR%2FCVaR-blue?style=for-the-badge&logo=chart-line)](https://www.investopedia.com/terms/v/var.asp)

**🎯 목표**: 수학적으로 정확한 레버리지 리스크 관리 시스템 구축  
**📊 수준**: 전문가급 (수학적 모델링 포함)  
**⏱️ 예상 시간**: 60분 (단계별 구현)

</div>

---

## 📚 **목차**

1. [🎯 레버리지 기초 이론](#-레버리지-기초-이론) *(15분)*
2. [📐 포지션 크기 계산 시스템](#-포지션-크기-계산-시스템) *(20분)*
3. [⚖️ 마진 관리 전략](#️-마진-관리-전략) *(25분)*
4. [🛡️ 청산 방지 시스템](#️-청산-방지-시스템) *(30분)*
5. [📊 리스크 메트릭스 대시보드](#-리스크-메트릭스-대시보드) *(35분)*
6. [🔄 동적 레버리지 조정](#-동적-레버리지-조정) *(40분)*
7. [📈 포트폴리오 레벨 리스크 관리](#-포트폴리오-레벨-리스크-관리) *(45분)*
8. [💥 스트레스 테스트 시나리오](#-스트레스-테스트-시나리오) *(50분)*
9. [🤖 자동화 리스크 시스템](#-자동화-리스크-시스템) *(55분)*
10. [🧮 고급 수학적 모델](#-고급-수학적-모델) *(60분)*

---

## 🎯 **레버리지 기초 이론**

### 📊 **레버리지 메커니즘 완전 이해**

레버리지는 적은 자본으로 큰 포지션을 취할 수 있게 하는 금융 도구입니다. 하지만 수익과 손실을 모두 확대시키는 양날의 검입니다.

#### **수학적 정의**

```python
# 레버리지 기본 공식
def calculate_leverage_effects():
    """레버리지 효과 계산"""
    
    # 기본 변수
    account_balance = 10000  # USDT
    leverage = 10  # 10배 레버리지
    position_size = account_balance * leverage  # 100,000 USDT
    
    # 가격 변동 시나리오
    price_changes = [-0.05, -0.02, -0.01, 0, 0.01, 0.02, 0.05]
    
    print("💰 레버리지 효과 분석:")
    print("가격변동 | 포지션손익 | 계좌손익 | 계좌변화율")
    print("-" * 50)
    
    for change in price_changes:
        position_pnl = position_size * change
        account_pnl = position_pnl  # 1:1 매핑
        account_change_pct = (account_pnl / account_balance) * 100
        
        print(f"{change:+6.1%} | {position_pnl:+8.0f} | {account_pnl:+8.0f} | {account_change_pct:+6.1f}%")
        
        # 청산 확인
        if account_balance + account_pnl <= 0:
            print(f"         🚨 청산 발생! 잔고 소진")

# 실행
calculate_leverage_effects()
```

#### **바이낸스 선물 레버리지 시스템**

```python
# user_data/strategies/modules/leverage_calculator.py
import numpy as np
from typing import Dict, Tuple

class BinanceLeverageSystem:
    """바이낸스 선물 레버리지 시스템 모델링"""
    
    def __init__(self):
        # 바이낸스 레버리지 브래킷 (BTCUSDT 기준)
        self.leverage_brackets = {
            (0, 50000): {"max_leverage": 125, "maint_margin_rate": 0.004},
            (50000, 250000): {"max_leverage": 100, "maint_margin_rate": 0.005},
            (250000, 1000000): {"max_leverage": 50, "maint_margin_rate": 0.01},
            (1000000, 5000000): {"max_leverage": 20, "maint_margin_rate": 0.025},
            (5000000, 20000000): {"max_leverage": 10, "maint_margin_rate": 0.05},
            (20000000, float('inf')): {"max_leverage": 5, "maint_margin_rate": 0.1}
        }
    
    def get_max_leverage(self, notional_value: float) -> int:
        """포지션 크기에 따른 최대 레버리지 계산"""
        for (min_val, max_val), bracket in self.leverage_brackets.items():
            if min_val <= notional_value < max_val:
                return bracket["max_leverage"]
        return 1
    
    def get_maintenance_margin_rate(self, notional_value: float) -> float:
        """유지 마진 비율 계산"""
        for (min_val, max_val), bracket in self.leverage_brackets.items():
            if min_val <= notional_value < max_val:
                return bracket["maint_margin_rate"]
        return 0.1
    
    def calculate_liquidation_price(self, entry_price: float, 
                                  leverage: int, side: str, 
                                  notional_value: float) -> float:
        """청산 가격 계산"""
        
        maint_margin_rate = self.get_maintenance_margin_rate(notional_value)
        
        if side.upper() == "LONG":
            # 롱 포지션 청산 가격
            liquidation_price = entry_price * (1 - (1/leverage) + maint_margin_rate)
        else:
            # 숏 포지션 청산 가격
            liquidation_price = entry_price * (1 + (1/leverage) - maint_margin_rate)
            
        return liquidation_price
    
    def calculate_required_margin(self, notional_value: float, 
                                 leverage: int) -> Dict[str, float]:
        """필요 마진 계산"""
        
        initial_margin = notional_value / leverage
        maintenance_margin_rate = self.get_maintenance_margin_rate(notional_value)
        maintenance_margin = notional_value * maintenance_margin_rate
        
        return {
            "initial_margin": initial_margin,
            "maintenance_margin": maintenance_margin,
            "margin_ratio": maintenance_margin / initial_margin,
            "leverage_efficiency": 1 - (maintenance_margin / notional_value)
        }

# 사용 예제
leverage_system = BinanceLeverageSystem()

# 10,000 USDT 포지션 분석
notional = 10000
max_lev = leverage_system.get_max_leverage(notional)
margin_info = leverage_system.calculate_required_margin(notional, max_lev)

print(f"포지션 크기: ${notional:,}")
print(f"최대 레버리지: {max_lev}x")
print(f"초기 마진: ${margin_info['initial_margin']:,.2f}")
print(f"유지 마진: ${margin_info['maintenance_margin']:,.2f}")
print(f"레버리지 효율성: {margin_info['leverage_efficiency']:.2%}")
```

### ⚖️ **Cross vs Isolated Margin 차이점**

```python
class MarginModeComparison:
    """마진 모드 비교 분석"""
    
    def __init__(self, account_balance: float):
        self.account_balance = account_balance
    
    def simulate_cross_margin(self, positions: list) -> Dict:
        """Cross Margin 시뮬레이션"""
        
        total_unrealized_pnl = sum(pos['unrealized_pnl'] for pos in positions)
        total_margin_used = sum(pos['margin_used'] for pos in positions)
        
        # 전체 계좌 잔고가 마진 역할
        available_margin = self.account_balance + total_unrealized_pnl
        margin_ratio = total_margin_used / available_margin if available_margin > 0 else float('inf')
        
        return {
            "mode": "Cross Margin",
            "total_margin_used": total_margin_used,
            "available_margin": available_margin,
            "margin_ratio": margin_ratio,
            "liquidation_risk": margin_ratio > 0.8,
            "risk_level": self._assess_risk_level(margin_ratio)
        }
    
    def simulate_isolated_margin(self, positions: list) -> Dict:
        """Isolated Margin 시뮬레이션"""
        
        position_risks = []
        total_margin_used = 0
        
        for pos in positions:
            margin_used = pos['margin_used']
            unrealized_pnl = pos['unrealized_pnl']
            
            # 각 포지션이 독립적인 마진 계좌
            position_margin = margin_used + unrealized_pnl
            margin_ratio = abs(unrealized_pnl) / margin_used if margin_used > 0 else 0
            
            position_risks.append({
                "symbol": pos['symbol'],
                "margin_ratio": margin_ratio,
                "liquidation_risk": margin_ratio > 0.8,
                "isolated_balance": position_margin
            })
            
            total_margin_used += margin_used
        
        return {
            "mode": "Isolated Margin",
            "total_margin_used": total_margin_used,
            "available_balance": self.account_balance - total_margin_used,
            "position_risks": position_risks,
            "max_margin_ratio": max([p['margin_ratio'] for p in position_risks]),
            "risk_level": self._assess_isolated_risk(position_risks)
        }
    
    def _assess_risk_level(self, margin_ratio: float) -> str:
        """리스크 레벨 평가"""
        if margin_ratio > 0.9:
            return "CRITICAL"
        elif margin_ratio > 0.8:
            return "HIGH"
        elif margin_ratio > 0.6:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _assess_isolated_risk(self, position_risks: list) -> str:
        """Isolated 리스크 평가"""
        critical_positions = [p for p in position_risks if p['margin_ratio'] > 0.8]
        
        if len(critical_positions) > 0:
            return f"CRITICAL ({len(critical_positions)} positions at risk)"
        else:
            return "STABLE"

# 사용 예제
margin_analyzer = MarginModeComparison(account_balance=50000)

# 예제 포지션들
positions = [
    {"symbol": "BTCUSDT", "margin_used": 5000, "unrealized_pnl": -800},
    {"symbol": "ETHUSDT", "margin_used": 3000, "unrealized_pnl": 450},
    {"symbol": "ADAUSDT", "margin_used": 2000, "unrealized_pnl": -200}
]

cross_analysis = margin_analyzer.simulate_cross_margin(positions)
isolated_analysis = margin_analyzer.simulate_isolated_margin(positions)

print("📊 마진 모드 비교 분석:")
print(f"Cross Margin - 리스크: {cross_analysis['risk_level']}")
print(f"Isolated Margin - 리스크: {isolated_analysis['risk_level']}")
```

---

## 📐 **포지션 크기 계산 시스템**

### 🎯 **Kelly Criterion 구현**

Kelly Criterion은 최적의 베팅 크기를 결정하는 수학적 공식입니다. 선물 거래에서 포지션 크기 결정에 활용할 수 있습니다.

#### **수학적 유도**

Kelly Criterion 공식: **f* = (bp - q) / b**

where:
- f* = 최적 베팅 비율
- b = 승리 시 수익률 (odds)
- p = 승리 확률
- q = 패배 확률 (1-p)

```python
# user_data/strategies/modules/kelly_criterion.py
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from typing import Tuple, Dict, List

class KellyCriterionCalculator:
    """Kelly Criterion 기반 포지션 크기 계산"""
    
    def __init__(self):
        self.historical_trades = []
        self.min_trade_sample = 30  # 최소 거래 샘플 수
    
    def add_trade_result(self, return_pct: float, leverage: int = 1):
        """거래 결과 추가"""
        actual_return = return_pct * leverage
        self.historical_trades.append(actual_return)
    
    def calculate_win_probability(self) -> float:
        """승률 계산"""
        if len(self.historical_trades) < self.min_trade_sample:
            return 0.5  # 기본값
        
        winning_trades = [r for r in self.historical_trades if r > 0]
        return len(winning_trades) / len(self.historical_trades)
    
    def calculate_average_returns(self) -> Tuple[float, float]:
        """평균 승리/패배 수익률 계산"""
        if len(self.historical_trades) < self.min_trade_sample:
            return 0.02, -0.01  # 기본값
        
        winning_trades = [r for r in self.historical_trades if r > 0]
        losing_trades = [r for r in self.historical_trades if r < 0]
        
        avg_win = np.mean(winning_trades) if winning_trades else 0.02
        avg_loss = np.mean(losing_trades) if losing_trades else -0.01
        
        return avg_win, avg_loss
    
    def calculate_kelly_fraction(self) -> Dict[str, float]:
        """Kelly Fraction 계산"""
        
        p = self.calculate_win_probability()
        avg_win, avg_loss = self.calculate_average_returns()
        
        # Kelly 공식 적용
        if avg_loss == 0:
            kelly_fraction = 0
        else:
            # b = 승리 시 수익률 / 패배 시 손실률의 절댓값
            b = abs(avg_win / avg_loss)
            q = 1 - p
            
            kelly_fraction = (b * p - q) / b
        
        # 안전 계수 적용 (일반적으로 Kelly의 25-50% 사용)
        safe_kelly = kelly_fraction * 0.25
        
        return {
            "kelly_fraction": kelly_fraction,
            "safe_kelly": safe_kelly,
            "win_probability": p,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "win_loss_ratio": abs(avg_win / avg_loss) if avg_loss != 0 else 0,
            "expectancy": p * avg_win + (1-p) * avg_loss
        }
    
    def calculate_optimal_position_size(self, account_balance: float, 
                                       max_leverage: int = 10,
                                       risk_limit: float = 0.02) -> Dict[str, float]:
        """최적 포지션 크기 계산"""
        
        kelly_data = self.calculate_kelly_fraction()
        kelly_fraction = kelly_data['safe_kelly']
        
        # 리스크 제한 적용
        max_risk_amount = account_balance * risk_limit
        kelly_risk_amount = account_balance * abs(kelly_fraction)
        
        # 더 보수적인 값 선택
        optimal_risk = min(max_risk_amount, kelly_risk_amount)
        
        # 레버리지를 고려한 포지션 크기
        base_position_size = optimal_risk / abs(kelly_data['avg_loss'])
        
        results = {}
        for leverage in range(1, max_leverage + 1):
            leveraged_position = base_position_size * leverage
            margin_required = leveraged_position / leverage
            
            # 계좌 대비 포지션 비율
            position_ratio = leveraged_position / account_balance
            
            results[f"leverage_{leverage}x"] = {
                "position_size": leveraged_position,
                "margin_required": margin_required,
                "position_ratio": position_ratio,
                "expected_return": kelly_data['expectancy'] * leverage,
                "max_loss": abs(kelly_data['avg_loss']) * leverage
            }
        
        return {
            "kelly_analysis": kelly_data,
            "position_scenarios": results,
            "recommended_risk": optimal_risk
        }

# 실전 사용 예제
def implement_kelly_in_freqtrade():
    """Freqtrade에서 Kelly Criterion 적용"""
    
    kelly_calc = KellyCriterionCalculator()
    
    # 과거 거래 데이터 시뮬레이션 (실제로는 백테스팅 결과 사용)
    np.random.seed(42)
    for _ in range(100):
        # 60% 승률, 평균 승리 2%, 평균 손실 1%
        if np.random.random() < 0.6:
            return_pct = np.random.normal(0.02, 0.01)
        else:
            return_pct = np.random.normal(-0.01, 0.005)
        
        kelly_calc.add_trade_result(return_pct)
    
    # 포지션 크기 계산
    account_balance = 10000
    position_analysis = kelly_calc.calculate_optimal_position_size(account_balance)
    
    print("🎯 Kelly Criterion 기반 포지션 분석:")
    print(f"Kelly Fraction: {position_analysis['kelly_analysis']['kelly_fraction']:.4f}")
    print(f"Safe Kelly (25%): {position_analysis['kelly_analysis']['safe_kelly']:.4f}")
    print(f"승률: {position_analysis['kelly_analysis']['win_probability']:.2%}")
    print(f"기댓값: {position_analysis['kelly_analysis']['expectancy']:.4f}")
    
    print("\n📊 레버리지별 포지션 크기:")
    for leverage, data in position_analysis['position_scenarios'].items():
        if leverage in ['leverage_1x', 'leverage_3x', 'leverage_5x', 'leverage_10x']:
            print(f"{leverage}: ${data['position_size']:,.0f} "
                  f"(마진: ${data['margin_required']:,.0f}, "
                  f"비율: {data['position_ratio']:.1%})")

# 실행
implement_kelly_in_freqtrade()
```

### 📊 **Fixed Fractional Method**

```python
class FixedFractionalMethod:
    """고정 비율 방법론"""
    
    def __init__(self, risk_percentage: float = 0.02):
        self.risk_percentage = risk_percentage  # 거래당 리스크 %
    
    def calculate_position_size(self, account_balance: float,
                               entry_price: float,
                               stop_loss_price: float,
                               leverage: int = 1) -> Dict[str, float]:
        """고정 비율 방법론으로 포지션 크기 계산"""
        
        # 리스크 금액 계산
        risk_amount = account_balance * self.risk_percentage
        
        # 스탑로스까지의 거리 (%)
        price_risk = abs(entry_price - stop_loss_price) / entry_price
        
        # 레버리지 고려한 실제 리스크
        effective_risk = price_risk * leverage
        
        # 포지션 크기 계산
        position_size = risk_amount / effective_risk
        
        # 마진 계산
        margin_required = position_size / leverage
        
        return {
            "position_size": position_size,
            "margin_required": margin_required,
            "risk_amount": risk_amount,
            "price_risk_pct": price_risk * 100,
            "effective_risk_pct": effective_risk * 100,
            "position_ratio": position_size / account_balance
        }
    
    def optimize_leverage(self, account_balance: float,
                         entry_price: float,
                         stop_loss_price: float,
                         max_leverage: int = 10) -> Dict[int, Dict]:
        """최적 레버리지 찾기"""
        
        results = {}
        
        for leverage in range(1, max_leverage + 1):
            calc = self.calculate_position_size(
                account_balance, entry_price, stop_loss_price, leverage
            )
            
            # 마진 사용률 계산
            margin_ratio = calc['margin_required'] / account_balance
            
            # 실용성 점수 (낮은 마진 사용률과 적절한 포지션 크기)
            if margin_ratio <= 0.1:  # 10% 이하 마진 사용
                practicality_score = 1.0
            elif margin_ratio <= 0.3:  # 30% 이하
                practicality_score = 0.7
            elif margin_ratio <= 0.5:  # 50% 이하
                practicality_score = 0.4
            else:
                practicality_score = 0.1
            
            results[leverage] = {
                **calc,
                "margin_ratio": margin_ratio,
                "practicality_score": practicality_score
            }
        
        # 최적 레버리지 추천
        best_leverage = max(results.keys(), 
                           key=lambda x: results[x]['practicality_score'])
        
        return {
            "all_scenarios": results,
            "recommended_leverage": best_leverage,
            "recommended_position": results[best_leverage]
        }

# 사용 예제
fixed_fractional = FixedFractionalMethod(risk_percentage=0.01)  # 1% 리스크

# 시나리오: BTC $50,000 진입, $48,000 스탑로스
optimization = fixed_fractional.optimize_leverage(
    account_balance=10000,
    entry_price=50000,
    stop_loss_price=48000,
    max_leverage=10
)

print("📐 Fixed Fractional Method 최적화:")
print(f"추천 레버리지: {optimization['recommended_leverage']}x")
recommended = optimization['recommended_position']
print(f"포지션 크기: ${recommended['position_size']:,.0f}")
print(f"마진 필요량: ${recommended['margin_required']:,.0f}")
print(f"마진 사용률: {recommended['margin_ratio']:.1%}")
```

### 📈 **변동성 기반 포지션 크기 조정**

```python
class VolatilityBasedSizing:
    """변동성 기반 포지션 크기 조정"""
    
    def __init__(self, target_volatility: float = 0.02):
        self.target_volatility = target_volatility  # 목표 일일 변동성 2%
    
    def calculate_realized_volatility(self, price_data: pd.Series, 
                                    window: int = 20) -> float:
        """실현 변동성 계산 (20일 기준)"""
        
        # 일일 수익률 계산
        returns = price_data.pct_change().dropna()
        
        # 연간화된 변동성 (√252 사용)
        daily_vol = returns.rolling(window=window).std().iloc[-1]
        
        return daily_vol
    
    def adjust_position_for_volatility(self, base_position_size: float,
                                     current_volatility: float,
                                     leverage: int = 1) -> Dict[str, float]:
        """변동성에 따른 포지션 크기 조정"""
        
        # 변동성 조정 배수
        vol_adjustment = self.target_volatility / current_volatility
        
        # 극단적 조정 방지 (0.5x ~ 2.0x 범위)
        vol_adjustment = np.clip(vol_adjustment, 0.5, 2.0)
        
        # 조정된 포지션 크기
        adjusted_position = base_position_size * vol_adjustment
        
        # 레버리지 고려
        leveraged_position = adjusted_position * leverage
        margin_required = leveraged_position / leverage
        
        return {
            "base_position": base_position_size,
            "volatility_adjustment": vol_adjustment,
            "adjusted_position": adjusted_position,
            "leveraged_position": leveraged_position,
            "margin_required": margin_required,
            "current_volatility": current_volatility,
            "target_volatility": self.target_volatility,
            "volatility_ratio": current_volatility / self.target_volatility
        }
    
    def create_volatility_ladder(self, base_position: float) -> pd.DataFrame:
        """변동성 레더 생성"""
        
        volatility_scenarios = np.arange(0.005, 0.05, 0.005)  # 0.5% ~ 5%
        
        results = []
        for vol in volatility_scenarios:
            adjustment = self.adjust_position_for_volatility(base_position, vol)
            results.append({
                'volatility': vol * 100,  # 퍼센트로 표시
                'adjustment_factor': adjustment['volatility_adjustment'],
                'adjusted_position': adjustment['adjusted_position'],
                'volatility_bucket': self._categorize_volatility(vol)
            })
        
        return pd.DataFrame(results)
    
    def _categorize_volatility(self, volatility: float) -> str:
        """변동성 구간 분류"""
        if volatility < 0.01:
            return "Low"
        elif volatility < 0.025:
            return "Medium"
        elif volatility < 0.04:
            return "High"
        else:
            return "Extreme"

# 실전 적용 예제
def integrate_with_freqtrade():
    """Freqtrade와 통합"""
    
    vol_sizer = VolatilityBasedSizing(target_volatility=0.015)  # 1.5% 목표
    
    # 가상의 가격 데이터 생성
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100)
    prices = pd.Series(50000 * np.cumprod(1 + np.random.normal(0, 0.02, 100)), 
                      index=dates)
    
    # 현재 변동성 계산
    current_vol = vol_sizer.calculate_realized_volatility(prices)
    
    # 포지션 조정
    base_position = 10000  # $10,000 기본 포지션
    adjustment = vol_sizer.adjust_position_for_volatility(base_position, current_vol)
    
    print("📊 변동성 기반 포지션 조정:")
    print(f"현재 변동성: {current_vol:.2%}")
    print(f"목표 변동성: {vol_sizer.target_volatility:.2%}")
    print(f"조정 배수: {adjustment['volatility_adjustment']:.2f}x")
    print(f"조정된 포지션: ${adjustment['adjusted_position']:,.0f}")
    
    # 변동성 레더 생성
    ladder = vol_sizer.create_volatility_ladder(base_position)
    print("\n📈 변동성 레더:")
    print(ladder.round(2))

# 실행
integrate_with_freqtrade()
```

---

## ⚖️ **마진 관리 전략**

### 🔍 **Isolated Margin 활용법**

Isolated Margin은 각 포지션이 독립적인 마진을 사용하여 리스크를 격리시키는 방법입니다.

```python
# user_data/strategies/modules/isolated_margin.py
class IsolatedMarginManager:
    """Isolated Margin 전문 관리"""
    
    def __init__(self, max_positions: int = 5):
        self.max_positions = max_positions
        self.positions = {}
        
    def calculate_isolated_margin(self, symbol: str, 
                                position_size: float,
                                entry_price: float,
                                leverage: int,
                                additional_margin: float = 0) -> Dict[str, float]:
        """Isolated Margin 계산"""
        
        # 필요 마진 계산
        notional_value = position_size * entry_price
        initial_margin = notional_value / leverage
        total_margin = initial_margin + additional_margin
        
        # 청산 가격 계산
        maintenance_margin_rate = self._get_maintenance_margin_rate(notional_value)
        
        return {
            "symbol": symbol,
            "position_size": position_size,
            "notional_value": notional_value,
            "leverage": leverage,
            "initial_margin": initial_margin,
            "additional_margin": additional_margin,
            "total_margin": total_margin,
            "maintenance_margin_rate": maintenance_margin_rate,
            "margin_ratio": initial_margin / total_margin,
            "buffer_ratio": additional_margin / initial_margin if initial_margin > 0 else 0
        }
    
    def optimize_margin_allocation(self, total_capital: float,
                                 position_requests: List[Dict]) -> Dict:
        """마진 할당 최적화"""
        
        # 각 포지션의 마진 요구사항 계산
        margin_calculations = []
        total_required_margin = 0
        
        for req in position_requests:
            margin_calc = self.calculate_isolated_margin(
                req['symbol'], req['position_size'], 
                req['entry_price'], req['leverage']
            )
            margin_calculations.append(margin_calc)
            total_required_margin += margin_calc['initial_margin']
        
        # 사용 가능한 자본 대비 마진 사용률
        margin_utilization = total_required_margin / total_capital
        
        # 마진 할당 전략
        allocation_strategy = self._determine_allocation_strategy(margin_utilization)
        
        # 추가 마진 배분
        remaining_capital = total_capital - total_required_margin
        
        optimized_positions = []
        for calc in margin_calculations:
            # 포지션 중요도에 따른 추가 마진 배분
            position_weight = calc['notional_value'] / sum(c['notional_value'] for c in margin_calculations)
            additional_margin = remaining_capital * position_weight * 0.3  # 30%만 추가 마진으로 사용
            
            optimized = self.calculate_isolated_margin(
                calc['symbol'], calc['position_size'],
                calc['entry_price'] / calc['position_size'],  # 역계산으로 entry_price 추정
                calc['leverage'], additional_margin
            )
            optimized_positions.append(optimized)
        
        return {
            "allocation_strategy": allocation_strategy,
            "total_margin_required": total_required_margin,
            "margin_utilization": margin_utilization,
            "remaining_capital": remaining_capital,
            "optimized_positions": optimized_positions,
            "risk_assessment": self._assess_portfolio_risk(optimized_positions)
        }
    
    def _get_maintenance_margin_rate(self, notional_value: float) -> float:
        """유지 마진 비율 (바이낸스 기준)"""
        if notional_value < 50000:
            return 0.004
        elif notional_value < 250000:
            return 0.005
        elif notional_value < 1000000:
            return 0.01
        else:
            return 0.025
    
    def _determine_allocation_strategy(self, utilization: float) -> str:
        """마진 할당 전략 결정"""
        if utilization < 0.3:
            return "CONSERVATIVE"  # 보수적 - 많은 버퍼
        elif utilization < 0.6:
            return "BALANCED"      # 균형적 - 적당한 버퍼
        elif utilization < 0.8:
            return "AGGRESSIVE"    # 공격적 - 최소 버퍼
        else:
            return "OVERLEVERED"   # 과도한 레버리지
    
    def _assess_portfolio_risk(self, positions: List[Dict]) -> Dict[str, float]:
        """포트폴리오 리스크 평가"""
        
        total_notional = sum(pos['notional_value'] for pos in positions)
        total_margin = sum(pos['total_margin'] for pos in positions)
        
        # 포지션별 리스크 가중치
        risk_weights = []
        for pos in positions:
            weight = pos['notional_value'] / total_notional
            leverage_risk = pos['leverage'] / 10  # 10배를 기준으로 정규화
            risk_weights.append(weight * leverage_risk)
        
        portfolio_risk_score = sum(risk_weights)
        
        return {
            "portfolio_risk_score": portfolio_risk_score,
            "average_leverage": total_notional / total_margin,
            "risk_concentration": max(risk_weights),
            "risk_diversification": 1 - (np.std(risk_weights) / np.mean(risk_weights))
        }

# 실제 사용 예제
def demonstrate_isolated_margin():
    """Isolated Margin 실증"""
    
    margin_manager = IsolatedMarginManager()
    
    # 포지션 요청 시나리오
    position_requests = [
        {"symbol": "BTCUSDT", "position_size": 0.5, "entry_price": 50000, "leverage": 5},
        {"symbol": "ETHUSDT", "position_size": 10, "entry_price": 3000, "leverage": 3},
        {"symbol": "ADAUSDT", "position_size": 15000, "entry_price": 0.5, "leverage": 10}
    ]
    
    # 총 자본 $50,000
    allocation = margin_manager.optimize_margin_allocation(50000, position_requests)
    
    print("⚖️ Isolated Margin 최적화 결과:")
    print(f"할당 전략: {allocation['allocation_strategy']}")
    print(f"마진 사용률: {allocation['margin_utilization']:.1%}")
    print(f"잔여 자본: ${allocation['remaining_capital']:,.0f}")
    
    print("\n📊 포지션별 마진 배분:")
    for pos in allocation['optimized_positions']:
        print(f"{pos['symbol']}:")
        print(f"  - 레버리지: {pos['leverage']}x")
        print(f"  - 초기 마진: ${pos['initial_margin']:,.0f}")
        print(f"  - 추가 마진: ${pos['additional_margin']:,.0f}")
        print(f"  - 버퍼 비율: {pos['buffer_ratio']:.1%}")
    
    risk = allocation['risk_assessment']
    print(f"\n🎯 포트폴리오 리스크:")
    print(f"리스크 점수: {risk['portfolio_risk_score']:.2f}")
    print(f"평균 레버리지: {risk['average_leverage']:.1f}x")
    print(f"리스크 집중도: {risk['risk_concentration']:.2f}")

# 실행
demonstrate_isolated_margin()
```

### 🔄 **Cross Margin 리스크/혜택 분석**

```python
class CrossMarginAnalyzer:
    """Cross Margin 심화 분석"""
    
    def __init__(self):
        self.correlation_matrix = self._load_correlation_matrix()
    
    def _load_correlation_matrix(self) -> pd.DataFrame:
        """암호화폐 간 상관관계 매트릭스 (예시)"""
        symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT', 'BNBUSDT']
        
        # 실제로는 과거 데이터에서 계산
        correlation_data = np.array([
            [1.00, 0.85, 0.70, 0.65, 0.60],
            [0.85, 1.00, 0.75, 0.70, 0.65],
            [0.70, 0.75, 1.00, 0.60, 0.55],
            [0.65, 0.70, 0.60, 1.00, 0.50],
            [0.60, 0.65, 0.55, 0.50, 1.00]
        ])
        
        return pd.DataFrame(correlation_data, index=symbols, columns=symbols)
    
    def analyze_cross_margin_benefits(self, positions: List[Dict], 
                                    account_balance: float) -> Dict:
        """Cross Margin 혜택 분석"""
        
        # 개별 포지션 마진 vs Cross 마진 비교
        isolated_total_margin = 0
        position_details = []
        
        for pos in positions:
            # Isolated 모드에서 필요한 마진
            isolated_margin = pos['notional_value'] / pos['leverage']
            isolated_total_margin += isolated_margin
            
            position_details.append({
                'symbol': pos['symbol'],
                'notional_value': pos['notional_value'],
                'leverage': pos['leverage'],
                'isolated_margin': isolated_margin,
                'unrealized_pnl': pos.get('unrealized_pnl', 0)
            })
        
        # Cross 모드에서의 마진 효율성
        total_unrealized_pnl = sum(pos['unrealized_pnl'] for pos in position_details)
        cross_available_margin = account_balance + total_unrealized_pnl
        
        # 마진 절약 효과
        margin_savings = isolated_total_margin - sum(pos['isolated_margin'] for pos in position_details)
        margin_efficiency = (account_balance - isolated_total_margin) / account_balance
        
        # 리스크 분석
        risk_analysis = self._analyze_cross_margin_risks(position_details)
        
        return {
            "isolated_margin_required": isolated_total_margin,
            "cross_margin_available": cross_available_margin,
            "margin_savings": margin_savings,
            "margin_efficiency": margin_efficiency,
            "position_details": position_details,
            "risk_analysis": risk_analysis,
            "cross_margin_ratio": isolated_total_margin / account_balance,
            "liquidation_threshold": self._calculate_liquidation_threshold(position_details, account_balance)
        }
    
    def _analyze_cross_margin_risks(self, positions: List[Dict]) -> Dict:
        """Cross Margin 리스크 분석"""
        
        # 포지션 간 상관관계 분석
        correlation_risk = 0
        total_exposure = 0
        
        for i, pos1 in enumerate(positions):
            for j, pos2 in enumerate(positions):
                if i < j:  # 중복 계산 방지
                    symbol1 = pos1['symbol']
                    symbol2 = pos2['symbol']
                    
                    if symbol1 in self.correlation_matrix.index and symbol2 in self.correlation_matrix.columns:
                        correlation = self.correlation_matrix.loc[symbol1, symbol2]
                        exposure1 = pos1['notional_value']
                        exposure2 = pos2['notional_value']
                        
                        # 상관관계가 높을수록 리스크 증가
                        correlation_risk += correlation * exposure1 * exposure2
                        total_exposure += exposure1 + exposure2
        
        # 정규화된 상관관계 리스크
        normalized_correlation_risk = correlation_risk / (total_exposure ** 2) if total_exposure > 0 else 0
        
        # 집중도 리스크
        exposures = [pos['notional_value'] for pos in positions]
        concentration_risk = max(exposures) / sum(exposures) if sum(exposures) > 0 else 0
        
        return {
            "correlation_risk": normalized_correlation_risk,
            "concentration_risk": concentration_risk,
            "total_exposure": total_exposure,
            "position_count": len(positions),
            "risk_score": (normalized_correlation_risk + concentration_risk) / 2
        }
    
    def _calculate_liquidation_threshold(self, positions: List[Dict], 
                                       account_balance: float) -> Dict:
        """Cross Margin 청산 임계점 계산"""
        
        # 각 포지션의 유지 마진 계산
        total_maintenance_margin = 0
        for pos in positions:
            maintenance_rate = 0.005  # 기본 0.5%
            maintenance_margin = pos['notional_value'] * maintenance_rate
            total_maintenance_margin += maintenance_margin
        
        # 청산 임계점
        current_margin = account_balance + sum(pos['unrealized_pnl'] for pos in positions)
        margin_call_threshold = total_maintenance_margin * 1.1  # 10% 버퍼
        liquidation_distance = (current_margin - total_maintenance_margin) / current_margin
        
        return {
            "total_maintenance_margin": total_maintenance_margin,
            "current_margin": current_margin,
            "margin_call_threshold": margin_call_threshold,
            "liquidation_distance": liquidation_distance,
            "safety_level": "SAFE" if liquidation_distance > 0.2 else "CAUTION" if liquidation_distance > 0.1 else "DANGER"
        }

# 시뮬레이션 실행
def run_cross_margin_simulation():
    """Cross Margin 시뮬레이션"""
    
    analyzer = CrossMarginAnalyzer()
    
    # 시나리오: 다양한 포지션
    positions = [
        {"symbol": "BTCUSDT", "notional_value": 25000, "leverage": 5, "unrealized_pnl": -500},
        {"symbol": "ETHUSDT", "notional_value": 15000, "leverage": 3, "unrealized_pnl": 300},
        {"symbol": "ADAUSDT", "notional_value": 8000, "leverage": 10, "unrealized_pnl": -200},
        {"symbol": "SOLUSDT", "notional_value": 12000, "leverage": 4, "unrealized_pnl": 150}
    ]
    
    analysis = analyzer.analyze_cross_margin_benefits(positions, account_balance=50000)
    
    print("🔄 Cross Margin 분석 결과:")
    print(f"Isolated 마진 필요량: ${analysis['isolated_margin_required']:,.0f}")
    print(f"Cross 마진 가용량: ${analysis['cross_margin_available']:,.0f}")
    print(f"마진 효율성: {analysis['margin_efficiency']:.1%}")
    
    risk = analysis['risk_analysis']
    print(f"\n⚠️ 리스크 분석:")
    print(f"상관관계 리스크: {risk['correlation_risk']:.3f}")
    print(f"집중도 리스크: {risk['concentration_risk']:.3f}")
    print(f"종합 리스크 점수: {risk['risk_score']:.3f}")
    
    liquidation = analysis['liquidation_threshold']
    print(f"\n🚨 청산 분석:")
    print(f"청산까지 거리: {liquidation['liquidation_distance']:.1%}")
    print(f"안전 수준: {liquidation['safety_level']}")

# 실행
run_cross_margin_simulation()
```

---

## 🛡️ **청산 방지 시스템**

### 📊 **청산 가격 실시간 계산**

```python
# user_data/strategies/modules/liquidation_monitor.py
import asyncio
import websocket
import json
from datetime import datetime
from typing import Dict, List, Callable

class LiquidationMonitor:
    """실시간 청산 모니터링 시스템"""
    
    def __init__(self, exchange, alert_callback: Callable = None):
        self.exchange = exchange
        self.alert_callback = alert_callback
        self.positions = {}
        self.price_feeds = {}
        self.alert_thresholds = {
            "liquidation_distance_warning": 0.15,    # 15%
            "liquidation_distance_critical": 0.05,   # 5%
            "margin_ratio_warning": 0.8,             # 80%
            "margin_ratio_critical": 0.9             # 90%
        }
    
    def calculate_liquidation_price(self, position: Dict) -> float:
        """정확한 청산 가격 계산"""
        
        symbol = position['symbol']
        side = position['side']  # 'long' or 'short'
        entry_price = position['entryPrice']
        position_size = abs(position['positionAmt'])
        leverage = position.get('leverage', 1)
        
        # 바이낸스 유지 마진 비율 가져오기
        maintenance_margin_rate = self._get_maintenance_margin_rate(
            position_size * entry_price
        )
        
        if side.lower() == 'long':
            # 롱 포지션: 가격 하락 시 청산
            liquidation_price = entry_price * (
                1 - (1/leverage) + maintenance_margin_rate
            )
        else:
            # 숏 포지션: 가격 상승 시 청산
            liquidation_price = entry_price * (
                1 + (1/leverage) - maintenance_margin_rate
            )
        
        return liquidation_price
    
    def monitor_liquidation_risk(self) -> List[Dict]:
        """청산 위험 모니터링"""
        
        try:
            # 현재 포지션 정보 가져오기
            positions = self.exchange._api.futures_position_information()
            risk_positions = []
            
            for position in positions:
                position_amt = float(position['positionAmt'])
                
                if position_amt != 0:  # 활성 포지션만
                    mark_price = float(position['markPrice'])
                    liquidation_price = float(position['liquidationPrice'])
                    
                    # 청산까지의 거리 계산
                    if position_amt > 0:  # 롱 포지션
                        distance_to_liquidation = (mark_price - liquidation_price) / mark_price
                    else:  # 숏 포지션
                        distance_to_liquidation = (liquidation_price - mark_price) / mark_price
                    
                    # 마진 비율 계산
                    maintenance_margin = float(position['maintMargin'])
                    margin_balance = float(position['marginBalance'])
                    margin_ratio = maintenance_margin / margin_balance if margin_balance > 0 else 1.0
                    
                    # 위험 수준 평가
                    risk_level = self._calculate_risk_level(margin_ratio, distance_to_liquidation)
                    
                    if risk_level in ['WARNING', 'CRITICAL', 'EMERGENCY']:
                        risk_positions.append({
                            'symbol': position['symbol'],
                            'side': position['side'],
                            'size': position['contracts'],
                            'margin_ratio': margin_ratio,
                            'liquidation_price': liquidation_price,
                            'mark_price': mark_price,
                            'distance_to_liquidation': distance_to_liquidation,
                            'risk_level': risk_level,
                            'unrealized_pnl': position.get('unrealizedPnl', 0)
                        })
            
            return risk_positions
            
        except Exception as e:
            print(f"⚠️ 청산 위험 확인 실패: {e}")
            return []
    
    def _calculate_risk_level(self, margin_ratio: float, 
                            distance_to_liquidation: float) -> str:
        """위험 수준 계산"""
        
        if margin_ratio >= 0.95 or distance_to_liquidation < 0.02:
            return 'EMERGENCY'
        elif margin_ratio >= 0.9 or distance_to_liquidation < 0.05:
            return 'CRITICAL'
        elif margin_ratio >= 0.8 or distance_to_liquidation < 0.15:
            return 'WARNING'
        else:
            return 'SAFE'
    
    def _get_maintenance_margin_rate(self, notional_value: float) -> float:
        """유지 마진 비율 (바이낸스 기준)"""
        if notional_value < 50000:
            return 0.004
        elif notional_value < 250000:
            return 0.005
        elif notional_value < 1000000:
            return 0.01
        elif notional_value < 5000000:
            return 0.025
        else:
            return 0.05
    
    async def start_real_time_monitoring(self, check_interval: int = 30):
        """실시간 모니터링 시작"""
        
        print("🛡️ 청산 방지 시스템 시작...")
        
        while True:
            try:
                risk_positions = self.monitor_liquidation_risk()
                
                if risk_positions:
                    await self._handle_risk_positions(risk_positions)
                
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                print(f"⚠️ 모니터링 오류: {e}")
                await asyncio.sleep(check_interval)
    
    async def _handle_risk_positions(self, risk_positions: List[Dict]):
        """위험 포지션 처리"""
        
        for position in risk_positions:
            risk_level = position['risk_level']
            
            if risk_level == 'EMERGENCY':
                await self._emergency_action(position)
            elif risk_level == 'CRITICAL':
                await self._critical_action(position)
            elif risk_level == 'WARNING':
                await self._warning_action(position)
    
    async def _emergency_action(self, position: Dict):
        """긴급 조치"""
        
        print(f"🚨 긴급: {position['symbol']} 청산 위험!")
        
        # 1. 즉시 알림 발송
        if self.alert_callback:
            await self.alert_callback(f"🚨 EMERGENCY: {position['symbol']} 청산 위험! "
                                    f"거리: {position['distance_to_liquidation']:.1%}")
        
        # 2. 포지션 일부 축소 고려
        await self._consider_position_reduction(position, reduction_ratio=0.5)
    
    async def _critical_action(self, position: Dict):
        """중요 조치"""
        
        print(f"⚠️ 경고: {position['symbol']} 높은 청산 위험")
        
        if self.alert_callback:
            await self.alert_callback(f"⚠️ CRITICAL: {position['symbol']} 청산 주의 "
                                    f"거리: {position['distance_to_liquidation']:.1%}")
        
        # 마진 추가 또는 포지션 축소 검토
        await self._consider_margin_adjustment(position)
    
    async def _warning_action(self, position: Dict):
        """경고 조치"""
        
        print(f"💛 주의: {position['symbol']} 청산 위험 증가")
        
        if self.alert_callback:
            await self.alert_callback(f"💛 WARNING: {position['symbol']} 청산 거리 "
                                    f"{position['distance_to_liquidation']:.1%}")
    
    async def _consider_position_reduction(self, position: Dict, 
                                         reduction_ratio: float = 0.3):
        """포지션 축소 고려"""
        
        symbol = position['symbol']
        current_size = abs(position['size'])
        reduce_size = current_size * reduction_ratio
        
        print(f"📉 {symbol} 포지션 {reduction_ratio:.0%} 축소 검토")
        print(f"   현재 크기: {current_size}")
        print(f"   축소 크기: {reduce_size}")
        
        # 실제 주문 실행은 수동 승인 후 (안전장치)
        confirmation = input(f"⚠️ {symbol} {reduction_ratio:.0%} 축소를 실행하시겠습니까? (y/N): ")
        
        if confirmation.lower() == 'y':
            try:
                # 포지션 축소 주문 실행
                side = 'sell' if position['side'] == 'long' else 'buy'
                
                order = self.exchange.create_market_order(
                    symbol=symbol,
                    type='market',
                    side=side,
                    amount=reduce_size,
                    params={'reduceOnly': True}
                )
                
                print(f"✅ {symbol} 포지션 축소 완료: {order['id']}")
                
            except Exception as e:
                print(f"❌ 포지션 축소 실패: {e}")
    
    async def _consider_margin_adjustment(self, position: Dict):
        """마진 조정 고려"""
        
        symbol = position['symbol']
        current_margin = position.get('margin_balance', 0)
        suggested_addition = current_margin * 0.2  # 20% 추가
        
        print(f"💰 {symbol} 마진 추가 검토:")
        print(f"   현재 마진: ${current_margin:,.0f}")
        print(f"   권장 추가: ${suggested_addition:,.0f}")
        
        # 마진 추가는 수동으로 수행 (안전성)

# 텔레그램 알림 통합
class TelegramAlertCallback:
    """텔레그램 알림 콜백"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
    
    async def __call__(self, message: str):
        """알림 전송"""
        try:
            import aiohttp
            
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        print(f"📱 텔레그램 알림 전송 완료")
                    else:
                        print(f"❌ 텔레그램 알림 실패: {response.status}")
                        
        except Exception as e:
            print(f"❌ 텔레그램 전송 오류: {e}")

# 사용 예제
async def run_liquidation_monitor():
    """청산 모니터 실행"""
    
    # 텔레그램 알림 설정 (실제 토큰으로 교체)
    telegram_callback = TelegramAlertCallback(
        bot_token="YOUR_BOT_TOKEN",
        chat_id="YOUR_CHAT_ID"
    )
    
    # 가상의 거래소 객체 (실제로는 ccxt 객체 사용)
    class MockExchange:
        class _api:
            @staticmethod
            def futures_position_information():
                # 테스트 데이터
                return [
                    {
                        'symbol': 'BTCUSDT',
                        'positionAmt': '0.1',
                        'entryPrice': '50000',
                        'markPrice': '48000',
                        'liquidationPrice': '45000',
                        'maintMargin': '400',
                        'marginBalance': '500',
                        'side': 'LONG',
                        'unrealizedPnl': '-200'
                    }
                ]
    
    # 모니터 시작
    exchange = MockExchange()
    monitor = LiquidationMonitor(exchange, telegram_callback)
    
    # 한 번 실행 테스트
    risk_positions = monitor.monitor_liquidation_risk()
    if risk_positions:
        print("🚨 위험 포지션 발견:")
        for pos in risk_positions:
            print(f"  {pos['symbol']}: {pos['risk_level']} - "
                  f"청산 거리 {pos['distance_to_liquidation']:.1%}")

# 실행 (비동기)
# asyncio.run(run_liquidation_monitor())
```

### 🔄 **자동 손절매 시스템**

```python
class AutoStopLossSystem:
    """지능형 자동 손절매 시스템"""
    
    def __init__(self, exchange):
        self.exchange = exchange
        self.stop_loss_orders = {}
        self.trailing_stops = {}
        
    def create_dynamic_stop_loss(self, symbol: str, position: Dict,
                                stop_loss_pct: float = 0.02) -> Dict:
        """동적 손절매 주문 생성"""
        
        entry_price = position['entryPrice']
        position_size = abs(position['positionAmt'])
        side = position['side']
        leverage = position.get('leverage', 1)
        
        # 레버리지 고려한 실제 손절 거리
        effective_stop_distance = stop_loss_pct / leverage
        
        if side.lower() == 'long':
            stop_price = entry_price * (1 - effective_stop_distance)
            order_side = 'sell'
        else:
            stop_price = entry_price * (1 + effective_stop_distance)
            order_side = 'buy'
        
        try:
            # OCO (One-Cancels-Other) 주문 생성
            stop_order = self.exchange.create_order(
                symbol=symbol,
                type='stop_market',
                side=order_side,
                amount=position_size,
                params={
                    'stopPrice': stop_price,
                    'reduceOnly': True,
                    'timeInForce': 'GTC'
                }
            )
            
            self.stop_loss_orders[symbol] = {
                'order_id': stop_order['id'],
                'stop_price': stop_price,
                'created_at': datetime.now(),
                'position_size': position_size,
                'leverage': leverage
            }
            
            return {
                'success': True,
                'order_id': stop_order['id'],
                'stop_price': stop_price,
                'effective_distance': effective_stop_distance
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_trailing_stop(self, symbol: str, position: Dict,
                           trail_percent: float = 0.03) -> Dict:
        """트레일링 스탑 생성"""
        
        entry_price = position['entryPrice']
        current_price = position['markPrice']
        side = position['side']
        
        # 초기 트레일링 스탑 가격 설정
        if side.lower() == 'long':
            # 롱 포지션: 현재가에서 trail_percent만큼 아래
            trail_stop_price = current_price * (1 - trail_percent)
            trail_direction = 'up'
        else:
            # 숏 포지션: 현재가에서 trail_percent만큼 위
            trail_stop_price = current_price * (1 + trail_percent)
            trail_direction = 'down'
        
        self.trailing_stops[symbol] = {
            'trail_percent': trail_percent,
            'current_stop_price': trail_stop_price,
            'highest_price': current_price if side.lower() == 'long' else None,
            'lowest_price': current_price if side.lower() == 'short' else None,
            'side': side,
            'position_size': abs(position['positionAmt']),
            'trail_direction': trail_direction,
            'active': True
        }
        
        return {
            'success': True,
            'initial_stop_price': trail_stop_price,
            'trail_percent': trail_percent
        }
    
    def update_trailing_stops(self, current_prices: Dict[str, float]):
        """트레일링 스탑 업데이트"""
        
        updated_stops = []
        
        for symbol, trail_data in self.trailing_stops.items():
            if not trail_data['active']:
                continue
                
            current_price = current_prices.get(symbol)
            if not current_price:
                continue
            
            side = trail_data['side']
            trail_percent = trail_data['trail_percent']
            
            if side.lower() == 'long':
                # 롱 포지션: 가격이 상승하면 스탑도 상승
                if current_price > trail_data['highest_price']:
                    trail_data['highest_price'] = current_price
                    new_stop_price = current_price * (1 - trail_percent)
                    
                    if new_stop_price > trail_data['current_stop_price']:
                        trail_data['current_stop_price'] = new_stop_price
                        updated_stops.append({
                            'symbol': symbol,
                            'new_stop_price': new_stop_price,
                            'price_move': 'up'
                        })
                
                # 스탑 가격에 도달하면 실행
                if current_price <= trail_data['current_stop_price']:
                    self._execute_trailing_stop(symbol, trail_data)
            
            else:  # 숏 포지션
                # 숏 포지션: 가격이 하락하면 스탑도 하락
                if current_price < trail_data['lowest_price']:
                    trail_data['lowest_price'] = current_price
                    new_stop_price = current_price * (1 + trail_percent)
                    
                    if new_stop_price < trail_data['current_stop_price']:
                        trail_data['current_stop_price'] = new_stop_price
                        updated_stops.append({
                            'symbol': symbol,
                            'new_stop_price': new_stop_price,
                            'price_move': 'down'
                        })
                
                # 스탑 가격에 도달하면 실행
                if current_price >= trail_data['current_stop_price']:
                    self._execute_trailing_stop(symbol, trail_data)
        
        return updated_stops
    
    def _execute_trailing_stop(self, symbol: str, trail_data: Dict):
        """트레일링 스탑 실행"""
        
        try:
            side = 'sell' if trail_data['side'].lower() == 'long' else 'buy'
            
            # 시장가 주문으로 포지션 청산
            order = self.exchange.create_market_order(
                symbol=symbol,
                side=side,
                amount=trail_data['position_size'],
                params={'reduceOnly': True}
            )
            
            print(f"🎯 트레일링 스탑 실행: {symbol}")
            print(f"   실행 가격: {trail_data['current_stop_price']}")
            print(f"   주문 ID: {order['id']}")
            
            # 트레일링 스탑 비활성화
            trail_data['active'] = False
            
            return order
            
        except Exception as e:
            print(f"❌ 트레일링 스탑 실행 실패 ({symbol}): {e}")
            return None

# 포지션 축소 메커니즘
class EmergencyPositionManager:
    """긴급 포지션 관리 시스템"""
    
    def __init__(self, exchange):
        self.exchange = exchange
        self.emergency_rules = {
            'max_portfolio_loss': 0.15,    # 15% 포트폴리오 손실
            'max_position_loss': 0.25,     # 25% 개별 포지션 손실
            'margin_ratio_emergency': 0.9, # 90% 마진 사용률
            'liquidation_distance_min': 0.05  # 5% 청산 거리
        }
    
    def assess_emergency_situation(self, account_info: Dict, 
                                 positions: List[Dict]) -> Dict:
        """긴급 상황 평가"""
        
        total_balance = account_info['totalWalletBalance']
        total_unrealized_pnl = account_info['totalUnrealizedProfit']
        
        # 포트폴리오 손실률
        portfolio_loss_pct = abs(total_unrealized_pnl) / total_balance if total_balance > 0 else 0
        
        # 개별 포지션 평가
        critical_positions = []
        emergency_positions = []
        
        for pos in positions:
            if float(pos['positionAmt']) == 0:
                continue
                
            entry_price = float(pos['entryPrice'])
            mark_price = float(pos['markPrice'])
            unrealized_pnl = float(pos['unrealizedProfit'])
            initial_margin = float(pos['initialMargin'])
            
            # 포지션 손실률
            position_loss_pct = abs(unrealized_pnl) / initial_margin if initial_margin > 0 else 0
            
            # 청산 거리
            liquidation_price = float(pos['liquidationPrice'])
            if liquidation_price > 0:
                if float(pos['positionAmt']) > 0:  # 롱
                    liquidation_distance = (mark_price - liquidation_price) / mark_price
                else:  # 숏
                    liquidation_distance = (liquidation_price - mark_price) / mark_price
            else:
                liquidation_distance = 1.0
            
            # 위험 수준 분류
            if (position_loss_pct > self.emergency_rules['max_position_loss'] or
                liquidation_distance < self.emergency_rules['liquidation_distance_min']):
                emergency_positions.append({
                    'symbol': pos['symbol'],
                    'loss_pct': position_loss_pct,
                    'liquidation_distance': liquidation_distance,
                    'unrealized_pnl': unrealized_pnl,
                    'priority': 'EMERGENCY'
                })
            elif position_loss_pct > self.emergency_rules['max_position_loss'] * 0.7:
                critical_positions.append({
                    'symbol': pos['symbol'],
                    'loss_pct': position_loss_pct,
                    'liquidation_distance': liquidation_distance,
                    'unrealized_pnl': unrealized_pnl,
                    'priority': 'CRITICAL'
                })
        
        # 전체 상황 평가
        situation_level = self._determine_situation_level(
            portfolio_loss_pct, len(emergency_positions), len(critical_positions)
        )
        
        return {
            'situation_level': situation_level,
            'portfolio_loss_pct': portfolio_loss_pct,
            'emergency_positions': emergency_positions,
            'critical_positions': critical_positions,
            'total_positions_at_risk': len(emergency_positions) + len(critical_positions),
            'recommended_actions': self._get_recommended_actions(situation_level, emergency_positions)
        }
    
    def _determine_situation_level(self, portfolio_loss: float, 
                                 emergency_count: int, critical_count: int) -> str:
        """상황 수준 결정"""
        
        if (portfolio_loss > self.emergency_rules['max_portfolio_loss'] or 
            emergency_count > 0):
            return 'EMERGENCY'
        elif (portfolio_loss > self.emergency_rules['max_portfolio_loss'] * 0.7 or
              critical_count > 2):
            return 'CRITICAL'
        elif critical_count > 0:
            return 'WARNING'
        else:
            return 'NORMAL'
    
    def _get_recommended_actions(self, situation_level: str, 
                               emergency_positions: List[Dict]) -> List[str]:
        """권장 조치 사항"""
        
        actions = []
        
        if situation_level == 'EMERGENCY':
            actions.extend([
                "즉시 모든 포지션 50% 축소",
                "추가 마진 투입 검토",
                "신규 포지션 진입 중단",
                "실시간 모니터링 강화"
            ])
        elif situation_level == 'CRITICAL':
            actions.extend([
                "위험 포지션 30% 축소",
                "레버리지 감소 검토",
                "손절매 주문 재설정"
            ])
        elif situation_level == 'WARNING':
            actions.extend([
                "포지션 크기 재검토",
                "리스크 분산 강화"
            ])
        
        return actions
    
    def execute_emergency_reduction(self, positions_to_reduce: List[Dict], 
                                  reduction_percentage: float = 0.5) -> List[Dict]:
        """긴급 포지션 축소 실행"""
        
        executed_orders = []
        
        for pos_info in positions_to_reduce:
            symbol = pos_info['symbol']
            
            try:
                # 현재 포지션 정보 가져오기
                position = self._get_current_position(symbol)
                
                if not position:
                    continue
                
                current_size = abs(float(position['positionAmt']))
                reduction_size = current_size * reduction_percentage
                
                # 축소 주문 실행
                side = 'sell' if float(position['positionAmt']) > 0 else 'buy'
                
                order = self.exchange.create_market_order(
                    symbol=symbol,
                    side=side,
                    amount=reduction_size,
                    params={'reduceOnly': True}
                )
                
                executed_orders.append({
                    'symbol': symbol,
                    'order_id': order['id'],
                    'reduction_size': reduction_size,
                    'reduction_pct': reduction_percentage,
                    'status': 'executed'
                })
                
                print(f"🚨 긴급 축소 완료: {symbol} ({reduction_percentage:.0%})")
                
            except Exception as e:
                executed_orders.append({
                    'symbol': symbol,
                    'error': str(e),
                    'status': 'failed'
                })
                print(f"❌ 긴급 축소 실패 ({symbol}): {e}")
        
        return executed_orders
    
    def _get_current_position(self, symbol: str) -> Dict:
        """현재 포지션 정보 조회"""
        try:
            positions = self.exchange._api.futures_position_information()
            for pos in positions:
                if pos['symbol'] == symbol and float(pos['positionAmt']) != 0:
                    return pos
            return None
        except Exception as e:
            print(f"❌ 포지션 조회 실패 ({symbol}): {e}")
            return None

# 통합 예제
def demonstrate_liquidation_prevention():
    """청산 방지 시스템 종합 시연"""
    
    print("🛡️ 청산 방지 시스템 종합 테스트\n")
    
    # Mock 데이터
    mock_account = {
        'totalWalletBalance': 50000,
        'totalUnrealizedProfit': -3000
    }
    
    mock_positions = [
        {
            'symbol': 'BTCUSDT',
            'positionAmt': '0.5',
            'entryPrice': '50000',
            'markPrice': '46000',
            'liquidationPrice': '43000',
            'unrealizedProfit': '-2000',
            'initialMargin': '5000',
            'side': 'LONG'
        },
        {
            'symbol': 'ETHUSDT',
            'positionAmt': '-10',
            'entryPrice': '3000',
            'markPrice': '3200',
            'liquidationPrice': '3300',
            'unrealizedProfit': '-1000',
            'initialMargin': '3000',
            'side': 'SHORT'
        }
    ]
    
    # 긴급 상황 평가
    emergency_manager = EmergencyPositionManager(None)
    assessment = emergency_manager.assess_emergency_situation(mock_account, mock_positions)
    
    print(f"📊 긴급 상황 평가:")
    print(f"상황 수준: {assessment['situation_level']}")
    print(f"포트폴리오 손실: {assessment['portfolio_loss_pct']:.1%}")
    print(f"긴급 포지션: {len(assessment['emergency_positions'])}개")
    print(f"위험 포지션: {len(assessment['critical_positions'])}개")
    
    print(f"\n📋 권장 조치:")
    for action in assessment['recommended_actions']:
        print(f"  • {action}")
    
    # 위험 포지션 상세 분석
    if assessment['emergency_positions']:
        print(f"\n🚨 긴급 포지션 상세:")
        for pos in assessment['emergency_positions']:
            print(f"  {pos['symbol']}: 손실 {pos['loss_pct']:.1%}, "
                  f"청산거리 {pos['liquidation_distance']:.1%}")

# 실행
demonstrate_liquidation_prevention()
```

---

## 📊 **리스크 메트릭스 대시보드**

### 📈 **VaR/CVaR 실시간 계산**

Value at Risk (VaR)와 Conditional Value at Risk (CVaR)는 포트폴리오의 잠재적 손실을 측정하는 핵심 리스크 지표입니다.

```python
# user_data/strategies/modules/risk_metrics.py
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import norm
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Tuple

class VaRCalculator:
    """VaR/CVaR 계산 엔진"""
    
    def __init__(self, confidence_levels: List[float] = [0.95, 0.99]):
        self.confidence_levels = confidence_levels
        self.historical_returns = {}
        
    def add_return_data(self, symbol: str, returns: pd.Series):
        """수익률 데이터 추가"""
        self.historical_returns[symbol] = returns
    
    def calculate_parametric_var(self, returns: pd.Series, 
                                confidence_level: float = 0.95,
                                position_value: float = 10000) -> Dict[str, float]:
        """모수적 VaR 계산 (정규분포 가정)"""
        
        # 수익률 통계
        mean_return = returns.mean()
        std_return = returns.std()
        
        # VaR 계산 (1일 기준)
        z_score = norm.ppf(1 - confidence_level)
        var_1d = position_value * (mean_return + z_score * std_return)
        
        # 다양한 기간 VaR
        var_1w = var_1d * np.sqrt(7)   # 1주
        var_1m = var_1d * np.sqrt(30)  # 1개월
        
        return {
            'var_1d': abs(var_1d),
            'var_1w': abs(var_1w),
            'var_1m': abs(var_1m),
            'confidence_level': confidence_level,
            'method': 'parametric',
            'mean_return': mean_return,
            'volatility': std_return
        }
    
    def calculate_historical_var(self, returns: pd.Series,
                               confidence_level: float = 0.95,
                               position_value: float = 10000) -> Dict[str, float]:
        """과거 데이터 기반 VaR 계산"""
        
        if len(returns) < 100:
            print("⚠️ 과거 데이터 부족 (최소 100개 필요)")
            return {}
        
        # 손실 분포 (음수 수익률)
        losses = -returns * position_value
        
        # VaR 계산 (백분위수 기반)
        var_1d = np.percentile(losses, confidence_level * 100)
        
        # CVaR 계산 (VaR을 초과하는 손실의 평균)
        cvar_1d = losses[losses >= var_1d].mean()
        
        return {
            'var_1d': var_1d,
            'cvar_1d': cvar_1d,
            'confidence_level': confidence_level,
            'method': 'historical',
            'worst_loss': losses.max(),
            'best_gain': (-losses).max()
        }
    
    def calculate_monte_carlo_var(self, returns: pd.Series,
                                confidence_level: float = 0.95,
                                position_value: float = 10000,
                                num_simulations: int = 10000) -> Dict[str, float]:
        """몬테카를로 시뮬레이션 VaR"""
        
        mean_return = returns.mean()
        std_return = returns.std()
        
        # 시뮬레이션 실행
        np.random.seed(42)
        simulated_returns = np.random.normal(mean_return, std_return, num_simulations)
        simulated_pnl = simulated_returns * position_value
        
        # VaR/CVaR 계산
        losses = -simulated_pnl
        var_1d = np.percentile(losses, confidence_level * 100)
        cvar_1d = losses[losses >= var_1d].mean()
        
        return {
            'var_1d': var_1d,
            'cvar_1d': cvar_1d,
            'confidence_level': confidence_level,
            'method': 'monte_carlo',
            'num_simulations': num_simulations,
            'simulated_returns': simulated_returns
        }
    
    def calculate_portfolio_var(self, positions: Dict[str, Dict],
                              correlation_matrix: pd.DataFrame,
                              confidence_level: float = 0.95) -> Dict[str, float]:
        """포트폴리오 VaR 계산 (상관관계 고려)"""
        
        portfolio_returns = []
        weights = []
        total_value = sum(pos['position_value'] for pos in positions.values())
        
        # 포트폴리오 수익률 계산
        for symbol, pos_data in positions.items():
            if symbol in self.historical_returns:
                returns = self.historical_returns[symbol]
                weight = pos_data['position_value'] / total_value
                weights.append(weight)
                
                if len(portfolio_returns) == 0:
                    portfolio_returns = returns * weight
                else:
                    portfolio_returns += returns * weight
        
        # 포트폴리오 VaR 계산
        portfolio_var = self.calculate_historical_var(
            portfolio_returns, confidence_level, total_value
        )
        
        # 개별 VaR 합계 (다각화 효과 비교용)
        individual_var_sum = 0
        for symbol, pos_data in positions.items():
            if symbol in self.historical_returns:
                individual_var = self.calculate_historical_var(
                    self.historical_returns[symbol], 
                    confidence_level, 
                    pos_data['position_value']
                )
                individual_var_sum += individual_var.get('var_1d', 0)
        
        # 다각화 효과
        diversification_benefit = individual_var_sum - portfolio_var.get('var_1d', 0)
        
        return {
            **portfolio_var,
            'individual_var_sum': individual_var_sum,
            'diversification_benefit': diversification_benefit,
            'diversification_ratio': diversification_benefit / individual_var_sum if individual_var_sum > 0 else 0
        }

class RiskMetricsDashboard:
    """실시간 리스크 메트릭스 대시보드"""
    
    def __init__(self):
        self.var_calculator = VaRCalculator()
        self.risk_metrics = {}
        
    def update_risk_metrics(self, positions: Dict[str, Dict],
                           price_data: Dict[str, pd.Series]) -> Dict[str, Dict]:
        """리스크 메트릭스 업데이트"""
        
        updated_metrics = {}
        
        for symbol, position in positions.items():
            if symbol in price_data:
                # 수익률 계산
                returns = price_data[symbol].pct_change().dropna()
                self.var_calculator.add_return_data(symbol, returns)
                
                # 다양한 VaR 계산
                position_value = position['position_value']
                leverage = position.get('leverage', 1)
                
                # 레버리지 조정된 수익률
                leveraged_returns = returns * leverage
                
                metrics = {}
                for confidence in [0.90, 0.95, 0.99]:
                    # 방법론별 VaR
                    parametric_var = self.var_calculator.calculate_parametric_var(
                        leveraged_returns, confidence, position_value
                    )
                    historical_var = self.var_calculator.calculate_historical_var(
                        leveraged_returns, confidence, position_value
                    )
                    
                    metrics[f'var_{int(confidence*100)}'] = {
                        'parametric': parametric_var,
                        'historical': historical_var
                    }
                
                # 추가 리스크 메트릭스
                metrics['additional'] = self._calculate_additional_metrics(
                    leveraged_returns, position_value
                )
                
                updated_metrics[symbol] = metrics
        
        self.risk_metrics = updated_metrics
        return updated_metrics
    
    def _calculate_additional_metrics(self, returns: pd.Series, 
                                    position_value: float) -> Dict[str, float]:
        """추가 리스크 메트릭스"""
        
        # 최대 낙폭 (Maximum Drawdown)
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # 샤프 비율 (무위험수익률 0 가정)
        sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        
        # 소르티노 비율 (하방 위험만 고려)
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else returns.std()
        sortino_ratio = returns.mean() / downside_std * np.sqrt(252) if downside_std > 0 else 0
        
        # 왜도와 첨도
        skewness = returns.skew()
        kurtosis = returns.kurtosis()
        
        # 승률
        win_rate = (returns > 0).mean()
        
        return {
            'max_drawdown': abs(max_drawdown),
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'skewness': skewness,
            'kurtosis': kurtosis,
            'win_rate': win_rate,
            'volatility_annual': returns.std() * np.sqrt(252)
        }
    
    def create_risk_dashboard(self, save_path: str = "risk_dashboard.html") -> str:
        """인터랙티브 리스크 대시보드 생성"""
        
        if not self.risk_metrics:
            print("⚠️ 리스크 메트릭스 데이터가 없습니다.")
            return ""
        
        # 서브플롯 생성
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=[
                'VaR Comparison (95%)', 'CVaR vs VaR',
                'Risk Metrics Heatmap', 'Drawdown Analysis',
                'Risk-Return Scatter', 'Portfolio Risk Breakdown'
            ],
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "heatmap", "colspan": 2}, None],
                   [{"type": "scatter"}, {"type": "pie"}]]
        )
        
        # 1. VaR 비교 차트
        symbols = list(self.risk_metrics.keys())
        parametric_vars = [self.risk_metrics[s]['var_95']['parametric']['var_1d'] for s in symbols]
        historical_vars = [self.risk_metrics[s]['var_95']['historical']['var_1d'] for s in symbols]
        
        fig.add_trace(go.Bar(name='Parametric VaR', x=symbols, y=parametric_vars, 
                            marker_color='lightblue'), row=1, col=1)
        fig.add_trace(go.Bar(name='Historical VaR', x=symbols, y=historical_vars, 
                            marker_color='darkblue'), row=1, col=1)
        
        # 2. CVaR vs VaR
        cvars = [self.risk_metrics[s]['var_95']['historical'].get('cvar_1d', 0) for s in symbols]
        vars_95 = [self.risk_metrics[s]['var_95']['historical']['var_1d'] for s in symbols]
        
        fig.add_trace(go.Bar(name='VaR 95%', x=symbols, y=vars_95, 
                            marker_color='orange'), row=1, col=2)
        fig.add_trace(go.Bar(name='CVaR 95%', x=symbols, y=cvars, 
                            marker_color='red'), row=1, col=2)
        
        # 3. 리스크-수익률 산점도
        returns = [self.risk_metrics[s]['additional']['sharpe_ratio'] for s in symbols]
        volatilities = [self.risk_metrics[s]['additional']['volatility_annual'] for s in symbols]
        
        fig.add_trace(go.Scatter(x=volatilities, y=returns, mode='markers+text',
                                text=symbols, textposition="top center",
                                marker=dict(size=10, color='green'),
                                name='Risk-Return'), row=3, col=1)
        
        # 레이아웃 업데이트
        fig.update_layout(
            title="📊 Real-time Risk Metrics Dashboard",
            height=900,
            showlegend=True
        )
        
        # HTML 파일로 저장
        fig.write_html(save_path)
        print(f"📊 대시보드 생성 완료: {save_path}")
        
        return save_path

# 실전 사용 예제
def demonstrate_var_calculation():
    """VaR 계산 실증"""
    
    # 가상의 가격 데이터 생성
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=252)  # 1년 데이터
    
    # BTC 가격 시뮬레이션 (높은 변동성)
    btc_returns = np.random.normal(0.001, 0.04, 252)  # 일일 0.1%, 변동성 4%
    btc_prices = pd.Series(50000 * np.cumprod(1 + btc_returns), index=dates)
    
    # ETH 가격 시뮬레이션 (중간 변동성)
    eth_returns = np.random.normal(0.0008, 0.035, 252)
    eth_prices = pd.Series(3000 * np.cumprod(1 + eth_returns), index=dates)
    
    # VaR 계산기 초기화
    var_calc = VaRCalculator()
    
    # BTC VaR 계산
    btc_returns_series = btc_prices.pct_change().dropna()
    btc_position_value = 100000  # $100,000 포지션
    
    print("₿ BTC VaR 분석 ($100,000 포지션):")
    
    # 방법론별 VaR
    parametric_var = var_calc.calculate_parametric_var(btc_returns_series, 0.95, btc_position_value)
    historical_var = var_calc.calculate_historical_var(btc_returns_series, 0.95, btc_position_value)
    monte_carlo_var = var_calc.calculate_monte_carlo_var(btc_returns_series, 0.95, btc_position_value)
    
    print(f"모수적 VaR (95%): ${parametric_var['var_1d']:,.0f}")
    print(f"과거데이터 VaR (95%): ${historical_var['var_1d']:,.0f}")
    print(f"몬테카를로 VaR (95%): ${monte_carlo_var['var_1d']:,.0f}")
    print(f"CVaR (95%): ${historical_var['cvar_1d']:,.0f}")
    
    # 신뢰구간별 VaR
    print(f"\n📊 신뢰구간별 VaR:")
    for confidence in [0.90, 0.95, 0.99]:
        var_result = var_calc.calculate_historical_var(btc_returns_series, confidence, btc_position_value)
        print(f"{confidence:.0%} VaR: ${var_result['var_1d']:,.0f}")
    
    # 레버리지 영향 분석
    print(f"\n⚖️ 레버리지별 VaR (95% 신뢰구간):")
    for leverage in [1, 3, 5, 10]:
        leveraged_returns = btc_returns_series * leverage
        leveraged_var = var_calc.calculate_historical_var(leveraged_returns, 0.95, btc_position_value)
        print(f"{leverage}x 레버리지: ${leveraged_var['var_1d']:,.0f}")

# 실행
demonstrate_var_calculation()
```

### 📈 **Rolling Sharpe Ratio 모니터링**

```python
class RollingRiskMonitor:
    """롤링 윈도우 리스크 지표 모니터링"""
    
    def __init__(self, window_size: int = 30):
        self.window_size = window_size
        self.performance_history = {}
        
    def calculate_rolling_metrics(self, returns: pd.Series) -> pd.DataFrame:
        """롤링 리스크 지표 계산"""
        
        if len(returns) < self.window_size:
            print(f"⚠️ 데이터 부족: {len(returns)} < {self.window_size}")
            return pd.DataFrame()
        
        # 롤링 계산
        rolling_metrics = pd.DataFrame(index=returns.index)
        
        # 1. 롤링 샤프 비율
        rolling_mean = returns.rolling(window=self.window_size).mean()
        rolling_std = returns.rolling(window=self.window_size).std()
        rolling_metrics['sharpe_ratio'] = (rolling_mean / rolling_std) * np.sqrt(252)
        
        # 2. 롤링 소르티노 비율
        rolling_downside_std = returns.rolling(window=self.window_size).apply(
            lambda x: x[x < 0].std()
        )
        rolling_metrics['sortino_ratio'] = (rolling_mean / rolling_downside_std) * np.sqrt(252)
        
        # 3. 롤링 최대 낙폭
        rolling_metrics['max_drawdown'] = returns.rolling(window=self.window_size).apply(
            self._calculate_rolling_drawdown
        )
        
        # 4. 롤링 변동성
        rolling_metrics['volatility'] = rolling_std * np.sqrt(252)
        
        # 5. 롤링 VaR (95%)
        rolling_metrics['var_95'] = returns.rolling(window=self.window_size).apply(
            lambda x: np.percentile(-x, 95)
        )
        
        # 6. 롤링 승률
        rolling_metrics['win_rate'] = returns.rolling(window=self.window_size).apply(
            lambda x: (x > 0).mean()
        )
        
        return rolling_metrics.dropna()
    
    def _calculate_rolling_drawdown(self, window_returns: pd.Series) -> float:
        """윈도우 내 최대 낙폭 계산"""
        cumulative = (1 + window_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return abs(drawdown.min())
    
    def detect_risk_regime_changes(self, rolling_metrics: pd.DataFrame) -> pd.DataFrame:
        """리스크 체제 변화 감지"""
        
        regime_changes = pd.DataFrame(index=rolling_metrics.index)
        
        # 변동성 체제 (낮음/보통/높음)
        vol_quantiles = rolling_metrics['volatility'].quantile([0.33, 0.67])
        regime_changes['volatility_regime'] = pd.cut(
            rolling_metrics['volatility'],
            bins=[-np.inf, vol_quantiles.iloc[0], vol_quantiles.iloc[1], np.inf],
            labels=['Low', 'Medium', 'High']
        )
        
        # 샤프 비율 체제
        sharpe_quantiles = rolling_metrics['sharpe_ratio'].quantile([0.33, 0.67])
        regime_changes['sharpe_regime'] = pd.cut(
            rolling_metrics['sharpe_ratio'],
            bins=[-np.inf, sharpe_quantiles.iloc[0], sharpe_quantiles.iloc[1], np.inf],
            labels=['Poor', 'Average', 'Good']
        )
        
        # 체제 변화 지점 감지
        regime_changes['vol_regime_change'] = (
            regime_changes['volatility_regime'] != regime_changes['volatility_regime'].shift(1)
        )
        regime_changes['sharpe_regime_change'] = (
            regime_changes['sharpe_regime'] != regime_changes['sharpe_regime'].shift(1)
        )
        
        return regime_changes
    
    def create_risk_alert_system(self, rolling_metrics: pd.DataFrame,
                               alert_thresholds: Dict[str, float] = None) -> List[Dict]:
        """리스크 알림 시스템"""
        
        if alert_thresholds is None:
            alert_thresholds = {
                'sharpe_ratio_min': 0.5,
                'volatility_max': 0.4,
                'max_drawdown_max': 0.15,
                'var_95_max': 0.05,
                'win_rate_min': 0.4
            }
        
        alerts = []
        latest_metrics = rolling_metrics.iloc[-1]
        
        # 각 지표별 알림 체크
        for metric, threshold in alert_thresholds.items():
            current_value = latest_metrics.get(metric.replace('_min', '').replace('_max', ''))
            
            if current_value is None:
                continue
            
            if '_min' in metric and current_value < threshold:
                alerts.append({
                    'type': 'WARNING',
                    'metric': metric,
                    'current_value': current_value,
                    'threshold': threshold,
                    'message': f"{metric} below threshold: {current_value:.3f} < {threshold}"
                })
            elif '_max' in metric and current_value > threshold:
                alerts.append({
                    'type': 'WARNING',
                    'metric': metric,
                    'current_value': current_value,
                    'threshold': threshold,
                    'message': f"{metric} above threshold: {current_value:.3f} > {threshold}"
                })
        
        return alerts

# 시각화 대시보드
def create_interactive_risk_dashboard():
    """인터랙티브 리스크 대시보드 생성"""
    
    # 샘플 데이터 생성
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=180)
    
    # 변동성이 변하는 수익률 시뮬레이션
    returns_data = []
    volatility = 0.02
    
    for i in range(len(dates)):
        # 변동성 클러스터링 효과
        if i > 60 and i < 120:
            volatility = 0.05  # 고변동성 구간
        else:
            volatility = 0.02  # 일반 변동성
            
        daily_return = np.random.normal(0.0005, volatility)
        returns_data.append(daily_return)
    
    returns = pd.Series(returns_data, index=dates)
    
    # 롤링 메트릭스 계산
    monitor = RollingRiskMonitor(window_size=30)
    rolling_metrics = monitor.calculate_rolling_metrics(returns)
    regime_changes = monitor.detect_risk_regime_changes(rolling_metrics)
    
    # 플롯 생성
    fig = make_subplots(
        rows=4, cols=2,
        subplot_titles=[
            'Rolling Sharpe Ratio', 'Rolling Volatility',
            'Rolling Max Drawdown', 'Rolling VaR (95%)',
            'Win Rate Trend', 'Risk Regime Changes',
            'Portfolio Value', 'Risk Alerts Timeline'
        ],
        vertical_spacing=0.08
    )
    
    # 1. 롤링 샤프 비율
    fig.add_trace(go.Scatter(
        x=rolling_metrics.index, 
        y=rolling_metrics['sharpe_ratio'],
        mode='lines',
        name='Sharpe Ratio',
        line=dict(color='blue')
    ), row=1, col=1)
    
    # 임계선 추가
    fig.add_hline(y=1.0, line_dash="dash", line_color="green", 
                  annotation_text="Good (>1.0)", row=1, col=1)
    
    # 2. 롤링 변동성
    fig.add_trace(go.Scatter(
        x=rolling_metrics.index,
        y=rolling_metrics['volatility'],
        mode='lines',
        name='Volatility',
        line=dict(color='red')
    ), row=1, col=2)
    
    # 3. 롤링 최대 낙폭
    fig.add_trace(go.Scatter(
        x=rolling_metrics.index,
        y=rolling_metrics['max_drawdown'],
        mode='lines',
        name='Max Drawdown',
        line=dict(color='orange'),
        fill='tonexty'
    ), row=2, col=1)
    
    # 4. 롤링 VaR
    fig.add_trace(go.Scatter(
        x=rolling_metrics.index,
        y=rolling_metrics['var_95'],
        mode='lines',
        name='VaR 95%',
        line=dict(color='purple')
    ), row=2, col=2)
    
    # 5. 승률 트렌드
    fig.add_trace(go.Scatter(
        x=rolling_metrics.index,
        y=rolling_metrics['win_rate'],
        mode='lines',
        name='Win Rate',
        line=dict(color='green')
    ), row=3, col=1)
    
    # 6. 리스크 체제 변화
    # 변동성 체제를 색상으로 표시
    volatility_colors = {'Low': 'green', 'Medium': 'yellow', 'High': 'red'}
    for regime in ['Low', 'Medium', 'High']:
        regime_data = regime_changes[regime_changes['volatility_regime'] == regime]
        if not regime_data.empty:
            fig.add_trace(go.Scatter(
                x=regime_data.index,
                y=[1] * len(regime_data),
                mode='markers',
                name=f'Vol: {regime}',
                marker=dict(color=volatility_colors[regime], size=8)
            ), row=3, col=2)
    
    # 7. 포트폴리오 가치 변화
    cumulative_returns = (1 + returns).cumprod()
    fig.add_trace(go.Scatter(
        x=cumulative_returns.index,
        y=cumulative_returns * 100000,  # $100,000 시작
        mode='lines',
        name='Portfolio Value',
        line=dict(color='darkblue', width=3)
    ), row=4, col=1)
    
    # 레이아웃 업데이트
    fig.update_layout(
        title="📊 Real-time Risk Monitoring Dashboard",
        height=1200,
        showlegend=True
    )
    
    # HTML 저장
    fig.write_html("rolling_risk_dashboard.html")
    print("📊 롤링 리스크 대시보드 생성 완료: rolling_risk_dashboard.html")
    
    # 현재 리스크 알림 확인
    alerts = monitor.create_risk_alert_system(rolling_metrics)
    
    if alerts:
        print("\n🚨 현재 리스크 알림:")
        for alert in alerts:
            print(f"  {alert['type']}: {alert['message']}")
    else:
        print("\n✅ 현재 리스크 알림 없음")
    
    return fig

# 실행
create_interactive_risk_dashboard()
```

---

이제 레버리지 리스크 관리 가이드의 핵심 부분들을 완성했습니다. 계속해서 나머지 섹션들을 완성하겠습니다.