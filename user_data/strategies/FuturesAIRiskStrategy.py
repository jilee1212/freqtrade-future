#!/usr/bin/env python3
"""
Binance USDT Perpetual Futures - AI Risk Management Strategy
==========================================================

AI 기반 리스크 관리가 적용된 선물거래 전용 전략
- 레버리지 고려 포지션 계산
- 동적 레버리지 조정
- 변동성 기반 리스크 관리
- 마진 비율 모니터링
"""

import freqtrade.vendor.qtpylib.indicators as qtpylib
import numpy as np
import pandas as pd
from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter
import talib.abstract as ta
from pandas import DataFrame
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class FuturesAIRiskStrategy(IStrategy):
    """선물거래 전용 AI 리스크 관리 전략"""

    # 전략 메타데이터
    INTERFACE_VERSION = 3
    timeframe = '15m'
    can_short = True  # 숏 포지션 활성화

    # 선물거래 전용 매개변수
    minimal_roi = {
        "0": 0.05,   # 5% 목표 수익
        "30": 0.03,  # 30분 후 3%
        "60": 0.01,  # 1시간 후 1%
        "120": 0     # 2시간 후 손절
    }
    stoploss = -0.05  # 5% 스탑로스 (선물거래는 보수적)

    # AI 리스크 매개변수
    risk_percentage = DecimalParameter(0.5, 2.0, default=1.0, space="buy",
                                     load=True, optimize=True)
    max_leverage = IntParameter(1, 10, default=5, space="buy",
                               load=True, optimize=True)
    volatility_threshold = DecimalParameter(0.02, 0.08, default=0.04, space="buy",
                                          load=True, optimize=True)

    # 기술적 지표 매개변수
    rsi_period = IntParameter(10, 20, default=14, space="buy", optimize=True)
    bb_period = IntParameter(15, 25, default=20, space="buy", optimize=True)
    bb_std = DecimalParameter(1.8, 2.5, default=2.0, space="buy", optimize=True)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """선물거래 특화 지표 생성"""

        # 기본 지표
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=self.rsi_period.value)
        dataframe['ema_fast'] = ta.EMA(dataframe, timeperiod=12)
        dataframe['ema_slow'] = ta.EMA(dataframe, timeperiod=26)

        # 변동성 지표 (레버리지 계산용)
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=14)
        dataframe['volatility'] = dataframe['atr'] / dataframe['close']

        # 볼린저밴드
        bb = ta.BBANDS(dataframe, timeperiod=self.bb_period.value,
                       nbdevup=self.bb_std.value, nbdevdn=self.bb_std.value)
        dataframe['bb_upper'] = bb['upperband']
        dataframe['bb_middle'] = bb['middleband']
        dataframe['bb_lower'] = bb['lowerband']
        dataframe['bb_percent'] = (dataframe['close'] - dataframe['bb_lower']) / \
                                 (dataframe['bb_upper'] - dataframe['bb_lower'])
        dataframe['bb_width'] = (dataframe['bb_upper'] - dataframe['bb_lower']) / \
                               dataframe['bb_middle']

        # 거래량 지표
        dataframe['volume_sma'] = ta.SMA(dataframe['volume'], timeperiod=20)
        dataframe['volume_ratio'] = dataframe['volume'] / dataframe['volume_sma']

        # 추세 지표
        dataframe['macd'] = ta.MACD(dataframe)['macd']
        dataframe['macd_signal'] = ta.MACD(dataframe)['macdsignal']
        dataframe['macd_histogram'] = ta.MACD(dataframe)['macdhist']

        # 선물거래 특화 지표 (모의)
        dataframe['funding_rate'] = self._get_funding_rate_indicator(metadata['pair'])
        dataframe['mark_price'] = dataframe['close']  # 실제로는 API에서 가져와야 함

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """AI 기반 진입 신호 (롱/숏)"""

        # 롱 진입 조건 - RSI 과매도 + 볼밴 하단 + 상승 추세
        long_conditions = [
            (dataframe['rsi'] < 30),  # RSI 과매도
            (dataframe['close'] <= dataframe['bb_lower']),  # 볼밴 하단
            (dataframe['bb_percent'] < 0.2),  # 하위 20% 구간
            (dataframe['volume_ratio'] > 1.2),  # 거래량 증가
            (dataframe['volatility'] < self.volatility_threshold.value),  # 변동성 적정
            (dataframe['ema_fast'] > dataframe['ema_slow']),  # 상승 추세
            (dataframe['macd'] > dataframe['macd_signal']),  # MACD 상승
            (dataframe['bb_width'] > 0.02),  # 충분한 변동성
        ]

        dataframe.loc[
            self._combine_conditions(long_conditions),
            'enter_long'
        ] = 1

        # 숏 진입 조건 - RSI 과매수 + 볼밴 상단 + 하락 추세
        short_conditions = [
            (dataframe['rsi'] > 70),  # RSI 과매수
            (dataframe['close'] >= dataframe['bb_upper']),  # 볼밴 상단
            (dataframe['bb_percent'] > 0.8),  # 상위 80% 구간
            (dataframe['volume_ratio'] > 1.2),  # 거래량 증가
            (dataframe['volatility'] < self.volatility_threshold.value),  # 변동성 적정
            (dataframe['ema_fast'] < dataframe['ema_slow']),  # 하락 추세
            (dataframe['macd'] < dataframe['macd_signal']),  # MACD 하락
            (dataframe['bb_width'] > 0.02),  # 충분한 변동성
        ]

        dataframe.loc[
            self._combine_conditions(short_conditions),
            'enter_short'
        ] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """AI 기반 청산 신호"""

        # 롱 청산 - RSI 회복 또는 볼밴 중간선 도달
        dataframe.loc[
            (
                (dataframe['rsi'] > 60) |
                (dataframe['close'] > dataframe['bb_middle']) |
                (dataframe['bb_percent'] > 0.6) |
                (dataframe['macd'] < dataframe['macd_signal'])
            ),
            'exit_long'
        ] = 1

        # 숏 청산 - RSI 하락 또는 볼밴 중간선 도달
        dataframe.loc[
            (
                (dataframe['rsi'] < 40) |
                (dataframe['close'] < dataframe['bb_middle']) |
                (dataframe['bb_percent'] < 0.4) |
                (dataframe['macd'] > dataframe['macd_signal'])
            ),
            'exit_short'
        ] = 1

        return dataframe

    def custom_stake_amount(self, pair: str, current_time, current_rate: float,
                           proposed_stake: float, min_stake: float, max_stake: float,
                           entry_tag: str, side: str, **kwargs) -> float:
        """선물거래 전용 AI 포지션 크기 계산"""

        try:
            # 현재 잔고 가져오기
            balance = self.wallets.get_total_stake_amount()

            # 변동성 기반 리스크 조정
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            if len(dataframe) == 0:
                return min_stake

            current_volatility = dataframe['volatility'].iloc[-1]

            # 동적 레버리지 계산
            optimal_leverage = self._calculate_optimal_leverage(current_volatility)

            # 리스크 기반 포지션 크기 계산
            risk_amount = balance * (self.risk_percentage.value / 100)
            effective_stop_distance = abs(self.stoploss) * optimal_leverage

            if effective_stop_distance > 0:
                position_size = risk_amount / effective_stop_distance
            else:
                position_size = min_stake

            # 최소/최대 제한 적용
            position_size = max(min_stake, min(position_size, max_stake))

            # 레버리지 고려한 최종 조정
            adjusted_position = position_size / optimal_leverage

            self.logger.info(f"AI Position Calc - Pair: {pair}, Volatility: {current_volatility:.4f}, "
                           f"Leverage: {optimal_leverage}, Position: {adjusted_position:.2f}")

            return max(min_stake, min(adjusted_position, max_stake))

        except Exception as e:
            self.logger.error(f"Custom stake amount calculation failed: {e}")
            return min_stake

    def leverage(self, pair: str, current_time, current_rate: float,
                proposed_leverage: float, max_leverage: float, entry_tag: str,
                side: str, **kwargs) -> float:
        """AI 기반 동적 레버리지 계산"""

        try:
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            if len(dataframe) == 0:
                return min(3, max_leverage)

            current_volatility = dataframe['volatility'].iloc[-1]
            optimal_leverage = self._calculate_optimal_leverage(current_volatility)

            self.logger.info(f"AI Leverage - Pair: {pair}, Volatility: {current_volatility:.4f}, "
                           f"Leverage: {optimal_leverage}")

            return min(optimal_leverage, max_leverage)

        except Exception as e:
            self.logger.error(f"Leverage calculation failed: {e}")
            return min(3, max_leverage)

    def custom_exit(self, pair: str, trade, current_time, current_rate: float,
                   current_profit: float, **kwargs) -> Optional[str]:
        """AI 기반 동적 청산 관리"""

        try:
            # 레버리지 기반 손익 확인
            leverage = trade.leverage or 1
            effective_profit = current_profit * leverage

            # 고레버리지 포지션 보호
            if leverage >= 5 and current_profit < -0.02:  # 2% 손실
                return "high_leverage_protection"

            # 변동성 기반 청산
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            if len(dataframe) > 0:
                current_volatility = dataframe['volatility'].iloc[-1]

                # 변동성 급증시 포지션 보호
                if current_volatility > self.volatility_threshold.value * 2:
                    return "volatility_protection"

            return None

        except Exception as e:
            self.logger.error(f"Custom exit calculation failed: {e}")
            return None

    def _calculate_optimal_leverage(self, volatility: float) -> int:
        """변동성 기반 최적 레버리지 계산"""

        if volatility > 0.06:      # 초고변동성 (>6%)
            return min(2, self.max_leverage.value)
        elif volatility > 0.04:    # 고변동성 (4-6%)
            return min(3, self.max_leverage.value)
        elif volatility > 0.02:    # 중변동성 (2-4%)
            return min(5, self.max_leverage.value)
        else:                      # 저변동성 (<2%)
            return min(8, self.max_leverage.value)

    def _combine_conditions(self, conditions: list) -> DataFrame:
        """조건들을 AND로 결합"""
        if not conditions:
            return pd.Series([False] * len(conditions[0]), index=conditions[0].index)

        result = conditions[0]
        for condition in conditions[1:]:
            result = result & condition
        return result

    def _get_funding_rate_indicator(self, pair: str) -> DataFrame:
        """자금 조달 수수료 지표 생성 (모의)"""
        # 실제 구현에서는 exchange API에서 가져와야 함
        # 현재는 모의 데이터로 0.001% 고정값 사용
        return pd.Series([0.001] * 1000)

    def informative_pairs(self):
        """추가 정보성 페어 (선택사항)"""
        return []