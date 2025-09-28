#!/usr/bin/env python3
"""
Position Manager
===============

포지션 모드 및 마진 관리 시스템
- One-way vs Hedge 모드 관리
- 마진 모드 설정 (Isolated/Cross)
- 레버리지 동적 조정
- 포지션 리스크 모니터링
"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class PositionMode(Enum):
    """포지션 모드"""
    ONE_WAY = "oneway"      # 단일 방향 (기본)
    HEDGE = "hedge"         # 헤지 모드 (롱/숏 동시)

class MarginMode(Enum):
    """마진 모드"""
    ISOLATED = "ISOLATED"   # 격리 마진
    CROSS = "CROSSED"       # 교차 마진

@dataclass
class PositionInfo:
    """포지션 정보"""
    symbol: str
    side: str               # LONG, SHORT
    size: float
    entry_price: float
    mark_price: float
    liquidation_price: float
    unrealized_pnl: float
    percentage: float
    margin_ratio: float
    maintenance_margin: float
    initial_margin: float
    leverage: int
    margin_mode: str
    risk_level: str

class PositionManager:
    """포지션 모드 및 마진 관리"""

    def __init__(self, exchange):
        self.exchange = exchange
        self.current_position_mode = PositionMode.ONE_WAY
        self.default_margin_mode = MarginMode.ISOLATED
        self.position_cache = {}
        self.last_update = datetime.now()

    def set_position_mode(self, hedge_mode: bool = False) -> bool:
        """포지션 모드 설정"""
        try:
            # Binance Futures API로 포지션 모드 변경
            result = self.exchange._api.futures_change_position_mode(
                dualSidePosition=hedge_mode
            )

            if hedge_mode:
                self.current_position_mode = PositionMode.HEDGE
                logger.info("✅ Hedge mode activated (Long/Short 동시 가능)")
            else:
                self.current_position_mode = PositionMode.ONE_WAY
                logger.info("✅ One-way mode activated (기본 모드)")

            return True

        except Exception as e:
            if "No need to change position mode" in str(e):
                logger.info(f"ℹ️  Position mode already set to {'hedge' if hedge_mode else 'one-way'}")
                return True
            else:
                logger.error(f"Position mode change error: {e}")
                return False

    def set_margin_mode(self, pair: str, margin_type: MarginMode = MarginMode.ISOLATED) -> bool:
        """마진 모드 설정"""
        try:
            symbol = pair.replace('/', '')
            result = self.exchange._api.futures_change_margin_type(
                symbol=symbol,
                marginType=margin_type.value
            )

            logger.info(f"✅ {pair} margin mode set to {margin_type.value}")
            return True

        except Exception as e:
            if "No need to change margin type" in str(e):
                logger.info(f"ℹ️  {pair} already in {margin_type.value} mode")
                return True
            else:
                logger.error(f"Margin mode change error for {pair}: {e}")
                return False

    def adjust_leverage(self, pair: str, leverage: int) -> Optional[Dict]:
        """레버리지 조정"""
        try:
            symbol = pair.replace('/', '')
            result = self.exchange._api.futures_change_leverage(
                symbol=symbol,
                leverage=leverage
            )

            logger.info(f"✅ {pair} leverage set to {leverage}x")
            return result

        except Exception as e:
            logger.error(f"Leverage adjustment error for {pair}: {e}")
            return None

    def get_position_info(self, pair: str = None) -> Union[PositionInfo, List[PositionInfo], None]:
        """포지션 정보 조회"""
        try:
            positions = self.exchange._api.futures_position_information()

            if pair:
                # 특정 페어 포지션 정보
                symbol = pair.replace('/', '')
                for pos in positions:
                    if pos['symbol'] == symbol and float(pos['positionAmt']) != 0:
                        return self._format_position_info(pos)
                return None
            else:
                # 모든 활성 포지션 정보
                active_positions = []
                for pos in positions:
                    if float(pos['positionAmt']) != 0:
                        active_positions.append(self._format_position_info(pos))
                return active_positions

        except Exception as e:
            logger.error(f"Position info fetch error: {e}")
            return None

    def _format_position_info(self, position: Dict) -> PositionInfo:
        """포지션 정보 포맷팅"""

        position_amt = float(position['positionAmt'])
        mark_price = float(position['markPrice'])
        entry_price = float(position['entryPrice'])
        liquidation_price = float(position['liquidationPrice'])
        unrealized_pnl = float(position['unRealizedProfit'])
        margin_ratio = float(position['marginRatio'])
        maintenance_margin = float(position['maintMargin'])
        initial_margin = float(position['initialMargin'])

        # 리스크 레벨 계산
        risk_level = self._calculate_risk_level(margin_ratio, liquidation_price, mark_price)

        # 수익률 계산
        if entry_price > 0:
            if position_amt > 0:  # LONG
                percentage = (mark_price - entry_price) / entry_price * 100
            else:  # SHORT
                percentage = (entry_price - mark_price) / entry_price * 100
        else:
            percentage = 0

        return PositionInfo(
            symbol=position['symbol'],
            side='LONG' if position_amt > 0 else 'SHORT',
            size=abs(position_amt),
            entry_price=entry_price,
            mark_price=mark_price,
            liquidation_price=liquidation_price,
            unrealized_pnl=unrealized_pnl,
            percentage=percentage,
            margin_ratio=margin_ratio,
            maintenance_margin=maintenance_margin,
            initial_margin=initial_margin,
            leverage=int(1 / margin_ratio) if margin_ratio > 0 else 1,
            margin_mode=position.get('marginType', 'isolated'),
            risk_level=risk_level
        )

    def _calculate_risk_level(self, margin_ratio: float, liquidation_price: float, mark_price: float) -> str:
        """리스크 레벨 계산"""

        if liquidation_price > 0:
            distance_to_liquidation = abs(mark_price - liquidation_price) / mark_price
        else:
            distance_to_liquidation = 1.0

        if margin_ratio > 0.8 or distance_to_liquidation < 0.05:  # 5% 이내
            return "CRITICAL"
        elif margin_ratio > 0.6 or distance_to_liquidation < 0.15:  # 15% 이내
            return "HIGH"
        elif margin_ratio > 0.4 or distance_to_liquidation < 0.30:  # 30% 이내
            return "MEDIUM"
        else:
            return "LOW"

    def get_account_balance(self) -> Dict:
        """계좌 잔고 정보 조회"""
        try:
            account_info = self.exchange._api.futures_account()

            return {
                'total_wallet_balance': float(account_info['totalWalletBalance']),
                'total_unrealized_pnl': float(account_info['totalUnrealizedProfit']),
                'total_margin_balance': float(account_info['totalMarginBalance']),
                'total_initial_margin': float(account_info['totalInitialMargin']),
                'total_maintenance_margin': float(account_info['totalMaintMargin']),
                'available_balance': float(account_info['availableBalance']),
                'max_withdraw_amount': float(account_info['maxWithdrawAmount']),
                'can_trade': account_info['canTrade'],
                'can_withdraw': account_info['canWithdraw']
            }

        except Exception as e:
            logger.error(f"Account balance fetch error: {e}")
            return {}

    def calculate_position_size(self, pair: str, risk_amount: float, entry_price: float,
                              stop_loss: float, leverage: int = 1) -> float:
        """포지션 크기 계산"""

        try:
            # 스탑로스까지의 거리 계산
            stop_distance = abs(entry_price - stop_loss) / entry_price

            if stop_distance == 0:
                return 0

            # 레버리지 고려한 포지션 크기
            position_size = risk_amount / (stop_distance * leverage)

            # 최소 주문 단위 확인 (추가 구현 필요)
            # min_notional = self.get_min_notional(pair)
            # position_size = max(position_size, min_notional)

            return position_size

        except Exception as e:
            logger.error(f"Position size calculation error: {e}")
            return 0

    def check_margin_requirements(self, pair: str, side: str, size: float, leverage: int) -> Dict:
        """마진 요구사항 확인"""

        try:
            # 현재 가격 조회
            ticker = self.exchange.fetch_ticker(pair)
            current_price = ticker['last']

            # 필요 마진 계산
            notional_value = size * current_price
            required_margin = notional_value / leverage

            # 계좌 잔고 조회
            balance_info = self.get_account_balance()
            available_balance = balance_info.get('available_balance', 0)

            # 마진 체크
            can_open = available_balance >= required_margin
            margin_ratio = required_margin / available_balance if available_balance > 0 else float('inf')

            return {
                'can_open_position': can_open,
                'required_margin': required_margin,
                'available_balance': available_balance,
                'margin_utilization': margin_ratio,
                'notional_value': notional_value,
                'leverage': leverage,
                'recommendation': self._get_margin_recommendation(margin_ratio)
            }

        except Exception as e:
            logger.error(f"Margin requirement check error: {e}")
            return {'can_open_position': False, 'error': str(e)}

    def _get_margin_recommendation(self, margin_ratio: float) -> str:
        """마진 비율 기반 추천"""

        if margin_ratio > 0.8:
            return "REDUCE_POSITION_SIZE"  # 포지션 크기 줄이기
        elif margin_ratio > 0.6:
            return "CAUTION_HIGH_RISK"     # 주의 높은 리스크
        elif margin_ratio > 0.4:
            return "MODERATE_RISK"         # 적당한 리스크
        else:
            return "SAFE_POSITION"         # 안전한 포지션

    def close_position(self, pair: str, percentage: float = 100) -> Optional[Dict]:
        """포지션 청산"""

        try:
            position = self.get_position_info(pair)
            if not position:
                logger.warning(f"No active position found for {pair}")
                return None

            # 청산할 수량 계산
            close_size = position.size * (percentage / 100)

            # 반대 방향으로 주문 실행
            side = 'sell' if position.side == 'LONG' else 'buy'

            # 시장가 주문으로 즉시 청산
            order = self.exchange.create_market_order(
                symbol=pair,
                side=side,
                amount=close_size,
                params={'reduceOnly': True}  # 포지션 감소 전용
            )

            logger.info(f"✅ {percentage}% of {pair} position closed")
            return order

        except Exception as e:
            logger.error(f"Position close error for {pair}: {e}")
            return None

    def emergency_close_all_positions(self) -> List[Dict]:
        """모든 포지션 긴급 청산"""

        results = []
        positions = self.get_position_info()

        if not positions:
            logger.info("No active positions to close")
            return results

        for position in positions:
            try:
                pair = position.symbol.replace('USDT', '/USDT:USDT')  # 페어 형식 변환
                result = self.close_position(pair, 100)
                if result:
                    results.append({
                        'symbol': position.symbol,
                        'status': 'success',
                        'order': result
                    })
                else:
                    results.append({
                        'symbol': position.symbol,
                        'status': 'failed',
                        'error': 'Close order failed'
                    })

                time.sleep(0.1)  # API 호출 제한 방지

            except Exception as e:
                results.append({
                    'symbol': position.symbol,
                    'status': 'error',
                    'error': str(e)
                })

        logger.info(f"Emergency close completed: {len(results)} positions processed")
        return results

    def optimize_margin_allocation(self) -> Dict:
        """마진 할당 최적화"""

        try:
            positions = self.get_position_info()
            if not positions:
                return {"status": "no_positions"}

            balance_info = self.get_account_balance()
            total_margin = balance_info.get('total_margin_balance', 0)

            recommendations = []

            for position in positions:
                # 포지션별 리스크 분석
                risk_score = self._calculate_position_risk_score(position)

                recommendation = {
                    'symbol': position.symbol,
                    'current_margin_ratio': position.margin_ratio,
                    'risk_level': position.risk_level,
                    'risk_score': risk_score,
                    'recommended_action': self._get_optimization_action(position, risk_score)
                }

                recommendations.append(recommendation)

            return {
                'status': 'success',
                'total_positions': len(positions),
                'total_margin_balance': total_margin,
                'recommendations': recommendations
            }

        except Exception as e:
            logger.error(f"Margin optimization error: {e}")
            return {'status': 'error', 'error': str(e)}

    def _calculate_position_risk_score(self, position: PositionInfo) -> float:
        """포지션 리스크 점수 계산 (0-100)"""

        # 마진 비율 점수 (70%)
        margin_score = min(position.margin_ratio * 100, 100) * 0.7

        # 청산가 거리 점수 (30%)
        if position.liquidation_price > 0:
            distance = abs(position.mark_price - position.liquidation_price) / position.mark_price
            liquidation_score = max(0, (1 - distance * 5)) * 100 * 0.3
        else:
            liquidation_score = 0

        total_score = margin_score + liquidation_score
        return min(total_score, 100)

    def _get_optimization_action(self, position: PositionInfo, risk_score: float) -> str:
        """최적화 행동 제안"""

        if risk_score > 80:
            return "URGENT_REDUCE_LEVERAGE_OR_CLOSE"
        elif risk_score > 60:
            return "REDUCE_LEVERAGE"
        elif risk_score > 40:
            return "MONITOR_CLOSELY"
        elif risk_score > 20:
            return "NORMAL_MONITORING"
        else:
            return "OPTIMAL_POSITION"

    def generate_position_report(self) -> str:
        """포지션 현황 리포트 생성"""

        positions = self.get_position_info()
        balance_info = self.get_account_balance()

        report = "📊 POSITION MANAGEMENT REPORT\n"
        report += "=" * 50 + "\n\n"

        # 계좌 요약
        report += "💰 ACCOUNT SUMMARY:\n"
        report += f"   Total Balance: ${balance_info.get('total_wallet_balance', 0):.2f}\n"
        report += f"   Available: ${balance_info.get('available_balance', 0):.2f}\n"
        report += f"   Unrealized PnL: ${balance_info.get('total_unrealized_pnl', 0):.2f}\n"
        report += f"   Position Mode: {self.current_position_mode.value}\n\n"

        if not positions:
            report += "❌ No active positions\n"
            return report

        # 포지션 상세
        report += f"📈 ACTIVE POSITIONS ({len(positions)}):\n\n"

        for i, pos in enumerate(positions, 1):
            report += f"{i}. {pos.symbol} ({pos.side})\n"
            report += f"   Size: {pos.size:.4f}\n"
            report += f"   Entry: ${pos.entry_price:.4f}\n"
            report += f"   Mark: ${pos.mark_price:.4f}\n"
            report += f"   PnL: ${pos.unrealized_pnl:.2f} ({pos.percentage:.2f}%)\n"
            report += f"   Leverage: {pos.leverage}x\n"
            report += f"   Margin Ratio: {pos.margin_ratio:.1%}\n"
            report += f"   Risk Level: {pos.risk_level}\n"
            report += f"   Liquidation: ${pos.liquidation_price:.4f}\n\n"

        # 리스크 요약
        high_risk_positions = [p for p in positions if p.risk_level in ['HIGH', 'CRITICAL']]
        if high_risk_positions:
            report += f"⚠️  HIGH RISK POSITIONS: {len(high_risk_positions)}\n"
            for pos in high_risk_positions:
                report += f"   - {pos.symbol}: {pos.risk_level}\n"

        report += f"\n📅 Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

        return report