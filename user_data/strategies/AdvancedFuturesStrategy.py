#!/usr/bin/env python3
"""
Advanced Futures Trading Strategy
=================================

Phase 5 통합 고급 선물거래 전략
- 모든 리스크 관리 모듈 통합
- 자금조달료 최적화
- 동적 레버리지 관리
- 실시간 리스크 모니터링
- 포지션 모드 최적화
"""

import freqtrade.vendor.qtpylib.indicators as qtpylib
import numpy as np
import pandas as pd
from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter
import talib.abstract as ta
from pandas import DataFrame
from typing import Optional, Dict
import logging
from datetime import datetime, timedelta
import sys
import os

# Phase 5 모듈 임포트
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))
from funding_rate_manager import FundingRateManager
from position_manager import PositionManager
from risk_monitor import RiskMonitor, AlertLevel
from advanced_leverage_manager import AdvancedLeverageManager

logger = logging.getLogger(__name__)


class AdvancedFuturesStrategy(IStrategy):
    """고급 선물거래 전략 - Phase 5 완전 통합"""

    # 전략 메타데이터
    INTERFACE_VERSION = 3
    timeframe = '15m'
    can_short = True

    # 공격적인 ROI 설정 (자금조달료 수익 포함)
    minimal_roi = {
        "0": 0.08,    # 8% 목표
        "15": 0.05,   # 15분 후 5%
        "30": 0.03,   # 30분 후 3%
        "60": 0.015,  # 1시간 후 1.5%
        "120": 0.01,  # 2시간 후 1%
        "240": 0      # 4시간 후 손절
    }

    # 동적 스탑로스 (레버리지 기반)
    stoploss = -0.06  # 기본 6%

    # 전략 매개변수
    rsi_period = IntParameter(10, 20, default=14, space="buy", optimize=True)
    rsi_oversold = IntParameter(25, 35, default=30, space="buy", optimize=True)
    rsi_overbought = IntParameter(65, 75, default=70, space="sell", optimize=True)

    bb_period = IntParameter(15, 25, default=20, space="buy", optimize=True)
    bb_deviation = DecimalParameter(1.8, 2.5, default=2.0, space="buy", optimize=True)

    # 리스크 관리 매개변수
    max_portfolio_risk = DecimalParameter(0.02, 0.08, default=0.05, space="buy", optimize=True)
    funding_importance = DecimalParameter(0.1, 0.5, default=0.3, space="buy", optimize=True)

    def __init__(self, config: dict) -> None:
        super().__init__(config)

        # Phase 5 모듈 초기화
        self.position_manager = None
        self.funding_manager = None
        self.risk_monitor = None
        self.leverage_manager = None

        # 초기화 플래그
        self._modules_initialized = False

    def _initialize_modules(self):
        """Phase 5 모듈들 초기화"""
        if self._modules_initialized:
            return

        try:
            # Exchange 객체가 준비될 때까지 대기
            if hasattr(self, 'dp') and hasattr(self.dp, 'exchange'):
                exchange = self.dp.exchange

                # 모듈 초기화
                self.position_manager = PositionManager(exchange)
                self.funding_manager = FundingRateManager(exchange)
                self.risk_monitor = RiskMonitor(self.position_manager, exchange)
                self.leverage_manager = AdvancedLeverageManager(self.position_manager, exchange)

                self._modules_initialized = True
                logger.info("✅ Phase 5 modules initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Phase 5 modules: {e}")

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """고급 지표 계산"""

        # Phase 5 모듈 초기화 시도
        self._initialize_modules()

        # 기본 기술적 지표
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=self.rsi_period.value)
        dataframe['rsi_short'] = ta.RSI(dataframe, timeperiod=7)
        dataframe['rsi_long'] = ta.RSI(dataframe, timeperiod=21)

        # 볼린저밴드
        bb = ta.BBANDS(dataframe, timeperiod=self.bb_period.value,
                       nbdevup=self.bb_deviation.value, nbdevdn=self.bb_deviation.value)
        dataframe['bb_upper'] = bb['upperband']
        dataframe['bb_middle'] = bb['middleband']
        dataframe['bb_lower'] = bb['lowerband']
        dataframe['bb_width'] = (dataframe['bb_upper'] - dataframe['bb_lower']) / dataframe['bb_middle']
        dataframe['bb_percent'] = (dataframe['close'] - dataframe['bb_lower']) / \
                                 (dataframe['bb_upper'] - dataframe['bb_lower'])

        # 이동평균선
        dataframe['ema_12'] = ta.EMA(dataframe, timeperiod=12)
        dataframe['ema_26'] = ta.EMA(dataframe, timeperiod=26)
        dataframe['ema_50'] = ta.EMA(dataframe, timeperiod=50)

        # MACD
        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macd_signal'] = macd['macdsignal']
        dataframe['macd_histogram'] = macd['macdhist']

        # 변동성 지표
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=14)
        dataframe['volatility'] = dataframe['atr'] / dataframe['close']

        # 거래량 지표
        dataframe['volume_sma'] = ta.SMA(dataframe['volume'], timeperiod=20)
        dataframe['volume_ratio'] = dataframe['volume'] / dataframe['volume_sma']

        # 모멘텀 지표
        dataframe['adx'] = ta.ADX(dataframe, timeperiod=14)
        dataframe['cci'] = ta.CCI(dataframe, timeperiod=20)

        # 자금조달료 지표 (실제 데이터)
        dataframe['funding_score'] = self._calculate_funding_score(metadata['pair'])

        # 리스크 지표
        dataframe['risk_score'] = self._calculate_risk_score(dataframe)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """진입 신호 생성 (고급 로직)"""

        pair = metadata['pair']

        # 롱 진입 조건
        long_conditions = [
            # 기본 기술적 조건
            (dataframe['rsi'] < self.rsi_oversold.value),
            (dataframe['rsi_short'] < self.rsi_oversold.value + 10),
            (dataframe['close'] <= dataframe['bb_lower'] * 1.01),
            (dataframe['bb_percent'] < 0.2),

            # 트렌드 조건
            (dataframe['macd'] > dataframe['macd_signal']),
            (dataframe['ema_12'] > dataframe['ema_26']),

            # 거래량 조건
            (dataframe['volume_ratio'] > 1.2),

            # 변동성 조건
            (dataframe['volatility'] > 0.01),
            (dataframe['volatility'] < 0.08),

            # 자금조달료 조건
            (dataframe['funding_score'] >= 0.5),  # 롱에 유리

            # 리스크 조건
            (dataframe['risk_score'] < 7),
        ]

        # 숏 진입 조건
        short_conditions = [
            # 기본 기술적 조건
            (dataframe['rsi'] > self.rsi_overbought.value),
            (dataframe['rsi_short'] > self.rsi_overbought.value - 10),
            (dataframe['close'] >= dataframe['bb_upper'] * 0.99),
            (dataframe['bb_percent'] > 0.8),

            # 트렌드 조건
            (dataframe['macd'] < dataframe['macd_signal']),
            (dataframe['ema_12'] < dataframe['ema_26']),

            # 거래량 조건
            (dataframe['volume_ratio'] > 1.2),

            # 변동성 조건
            (dataframe['volatility'] > 0.01),
            (dataframe['volatility'] < 0.08),

            # 자금조달료 조건
            (dataframe['funding_score'] <= -0.5),  # 숏에 유리

            # 리스크 조건
            (dataframe['risk_score'] < 7),
        ]

        # 추가 안전 검사
        if self._is_safe_to_enter(pair):
            dataframe.loc[self._combine_conditions(long_conditions), 'enter_long'] = 1
            dataframe.loc[self._combine_conditions(short_conditions), 'enter_short'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """청산 신호 생성"""

        # 롱 청산 - 다양한 청산 조건
        long_exit_conditions = [
            (dataframe['rsi'] > 70),
            (dataframe['bb_percent'] > 0.8),
            (dataframe['macd'] < dataframe['macd_signal']),
            (dataframe['close'] > dataframe['bb_upper']),
            (dataframe['risk_score'] > 8),
        ]

        # 숏 청산
        short_exit_conditions = [
            (dataframe['rsi'] < 30),
            (dataframe['bb_percent'] < 0.2),
            (dataframe['macd'] > dataframe['macd_signal']),
            (dataframe['close'] < dataframe['bb_lower']),
            (dataframe['risk_score'] > 8),
        ]

        dataframe.loc[self._combine_conditions(long_exit_conditions, any_condition=True), 'exit_long'] = 1
        dataframe.loc[self._combine_conditions(short_exit_conditions, any_condition=True), 'exit_short'] = 1

        return dataframe

    def custom_stake_amount(self, pair: str, current_time, current_rate: float,
                           proposed_stake: float, min_stake: float, max_stake: float,
                           entry_tag: str, side: str, **kwargs) -> float:
        """고급 포지션 크기 계산"""

        try:
            if not self._modules_initialized:
                return min_stake

            # 잔고 정보
            balance = self.wallets.get_total_stake_amount()

            # 현재 데이터
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            if len(dataframe) == 0:
                return min_stake

            current_volatility = dataframe['volatility'].iloc[-1]
            risk_score = dataframe['risk_score'].iloc[-1]

            # 레버리지 최적화
            leverage_rec = self.leverage_manager.calculate_optimal_leverage(pair, side)
            optimal_leverage = leverage_rec.recommended_leverage

            # 리스크 기반 포지션 크기
            max_risk = balance * self.max_portfolio_risk.value

            # 변동성 조정
            volatility_adjustment = max(0.5, min(2.0, 1 / (current_volatility * 20)))

            # 포지션 크기 계산
            position_size = (max_risk * volatility_adjustment) / max(abs(self.stoploss), 0.02)

            # 최종 조정
            final_size = max(min_stake, min(position_size, max_stake * 0.8))

            logger.info(f"💰 Advanced Stake - {pair}: {final_size:.2f} USDT "
                       f"(Volatility: {current_volatility:.3f}, Risk: {risk_score:.1f}, "
                       f"Leverage: {optimal_leverage}x)")

            return final_size

        except Exception as e:
            logger.error(f"❌ Advanced stake calculation failed: {e}")
            return min_stake

    def leverage(self, pair: str, current_time, current_rate: float,
                proposed_leverage: float, max_leverage: float, entry_tag: str,
                side: str, **kwargs) -> float:
        """동적 레버리지 계산"""

        try:
            if not self._modules_initialized:
                return min(3, max_leverage)

            # 레버리지 관리자 사용
            leverage_rec = self.leverage_manager.calculate_optimal_leverage(pair, side)
            recommended_leverage = leverage_rec.recommended_leverage

            # 최대값 제한
            final_leverage = min(recommended_leverage, max_leverage, 20)

            logger.info(f"⚖️ Dynamic Leverage - {pair}: {final_leverage}x "
                       f"(Recommended: {recommended_leverage}x, Confidence: {leverage_rec.confidence_score:.1%})")

            return final_leverage

        except Exception as e:
            logger.error(f"❌ Dynamic leverage calculation failed: {e}")
            return min(3, max_leverage)

    def custom_exit(self, pair: str, trade, current_time, current_rate: float,
                   current_profit: float, **kwargs) -> Optional[str]:
        """고급 청산 로직"""

        try:
            if not self._modules_initialized:
                return None

            # 리스크 모니터링
            risk_alerts = self.risk_monitor.check_position_risk(pair)

            # 긴급 청산 조건
            for alert in risk_alerts:
                if alert.alert_level == AlertLevel.CRITICAL:
                    return f"critical_risk_exit_{alert.metric.value}"

            # 자금조달료 기반 청산
            if self.funding_manager and self._should_exit_for_funding(pair, trade, current_profit):
                return "funding_optimized_exit"

            # 수익 최적화 청산
            if current_profit > 0.05:  # 5% 이상 수익
                return "profit_optimization_exit"

            # 레버리지 기반 손실 제한
            leverage = getattr(trade, 'leverage', 1)
            if leverage >= 10 and current_profit < -0.02:  # 고레버리지에서 2% 손실
                return "high_leverage_protection_exit"

            return None

        except Exception as e:
            logger.error(f"❌ Advanced exit logic failed: {e}")
            return None

    def custom_entry_price(self, pair: str, current_time, proposed_rate: float,
                          entry_tag: str, side: str, **kwargs) -> float:
        """최적 진입가 계산"""

        try:
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            if len(dataframe) == 0:
                return proposed_rate

            bb_upper = dataframe['bb_upper'].iloc[-1]
            bb_lower = dataframe['bb_lower'].iloc[-1]
            bb_middle = dataframe['bb_middle'].iloc[-1]

            if side == "long":
                # 롱: 중간선과 하단 사이에서 진입
                target_price = min(proposed_rate, (bb_middle + bb_lower) / 2)
                return max(target_price, bb_lower * 1.001)

            elif side == "short":
                # 숏: 중간선과 상단 사이에서 진입
                target_price = max(proposed_rate, (bb_middle + bb_upper) / 2)
                return min(target_price, bb_upper * 0.999)

            return proposed_rate

        except Exception as e:
            logger.error(f"❌ Custom entry price calculation failed: {e}")
            return proposed_rate

    def confirm_trade_entry(self, pair: str, order_type: str, amount: float,
                           rate: float, time_in_force: str, current_time,
                           entry_tag: str, side: str, **kwargs) -> bool:
        """거래 진입 최종 확인"""

        try:
            if not self._modules_initialized:
                return True

            # 포트폴리오 리스크 확인
            portfolio_risk = self._calculate_portfolio_risk()
            if portfolio_risk > 0.15:  # 15% 초과시 진입 금지
                logger.warning(f"⚠️ Portfolio risk too high: {portfolio_risk:.1%}")
                return False

            # 자금조달료 확인
            funding_analysis = self.funding_manager.analyze_funding_opportunity(pair)
            if funding_analysis.get('profitability_score', 0) < 3:
                logger.warning(f"⚠️ Poor funding opportunity for {pair}")
                return False

            # 최종 리스크 검사
            if self.risk_monitor:
                risk_alerts = self.risk_monitor.check_position_risk(pair)
                critical_alerts = [alert for alert in risk_alerts if alert.alert_level == AlertLevel.CRITICAL]
                if critical_alerts:
                    logger.warning(f"Critical risk alerts prevent entry: {len(critical_alerts)}")
                    return False

            return True

        except Exception as e:
            logger.error(f"❌ Trade confirmation failed: {e}")
            return True  # 에러시 진입 허용

    # 헬퍼 메서드들
    def _calculate_funding_score(self, pair: str) -> pd.Series:
        """자금조달료 점수 계산"""
        try:
            if self.funding_manager:
                funding_data = self.funding_manager.get_current_funding_rate(pair)
                if funding_data:
                    rate = funding_data.funding_rate
                    # -1 ~ 1 점수로 변환 (음수=롱유리, 양수=숏유리)
                    score = np.tanh(rate * 1000)  # -1 ~ 1 범위로 스케일링
                    return pd.Series([score] * 1000)
        except:
            pass
        return pd.Series([0] * 1000)

    def _calculate_risk_score(self, dataframe: DataFrame) -> pd.Series:
        """리스크 점수 계산 (1-10)"""
        try:
            volatility = dataframe['volatility']
            bb_width = dataframe['bb_width']
            volume_ratio = dataframe['volume_ratio']

            # 변동성 점수
            vol_score = np.clip(volatility * 100, 1, 5)

            # 볼밴 폭 점수
            bb_score = np.clip(bb_width * 100, 1, 3)

            # 거래량 점수
            vol_ratio_score = np.clip(volume_ratio, 0.5, 2)

            # 종합 점수
            total_score = vol_score + bb_score + vol_ratio_score
            return np.clip(total_score, 1, 10)

        except:
            return pd.Series([5] * len(dataframe))

    def _is_safe_to_enter(self, pair: str) -> bool:
        """진입 안전성 확인"""
        try:
            if not self._modules_initialized:
                return True

            # 기본 안전 검사
            portfolio_risk = self._calculate_portfolio_risk()
            return portfolio_risk < 0.12  # 12% 미만

        except:
            return True

    def _calculate_portfolio_risk(self) -> float:
        """포트폴리오 리스크 계산"""
        try:
            if not self.position_manager:
                return 0.0

            positions = self.position_manager.get_position_info()
            if not positions:
                return 0.0

            account_balance = self.position_manager.get_account_balance()
            total_balance = account_balance.get('total_wallet_balance', 1)

            total_exposure = 0
            for position in positions:
                position_value = position.size * position.mark_price
                exposure = position_value / total_balance
                total_exposure += exposure

            return total_exposure

        except:
            return 0.0

    def _should_exit_for_funding(self, pair: str, trade, current_profit: float) -> bool:
        """자금조달료 기반 청산 판단"""
        try:
            if not self.funding_manager:
                return False

            # 자금조달료 수익 유지 여부 확인
            should_hold = self.funding_manager.should_hold_for_funding(
                pair, 'long' if not trade.is_short else 'short', current_profit
            )

            # 유지하지 않는 것이 좋다면 청산
            return not should_hold

        except:
            return False

    def _combine_conditions(self, conditions: list, any_condition: bool = False) -> pd.Series:
        """조건들을 결합"""
        if not conditions:
            return pd.Series([False] * 1000)

        result = conditions[0]
        for condition in conditions[1:]:
            if any_condition:
                result = result | condition  # OR 연산
            else:
                result = result & condition  # AND 연산

        return result

    def informative_pairs(self):
        """추가 정보성 페어"""
        return []