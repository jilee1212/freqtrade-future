#!/usr/bin/env python3
"""
Ross Cameron RSI Futures Strategy
=================================

로스 카메론의 RSI 반전 전략을 선물거래에 최적화
- RSI 과매도/과매수 구간 활용
- 볼린저밴드 확장/수축 패턴
- 자금 조달 수수료 고려
- AI 리스크 관리 통합
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


class RossCameronFuturesStrategy(IStrategy):
    """로스 카메론 RSI 전략 - 선물거래 최적화"""

    # 전략 메타데이터
    INTERFACE_VERSION = 3
    timeframe = '15m'
    can_short = True  # 숏 포지션 활성화

    # 로스 카메론 스타일 매개변수
    minimal_roi = {
        "0": 0.05,   # 5% 목표 수익
        "30": 0.03,  # 30분 후 3%
        "60": 0.01,  # 1시간 후 1%
        "120": 0     # 2시간 후 손절
    }
    stoploss = -0.04  # 4% 스탑로스

    # 로스 카메론 RSI 매개변수
    rsi_overbought = IntParameter(65, 80, default=70, space="sell", optimize=True)
    rsi_oversold = IntParameter(20, 35, default=30, space="buy", optimize=True)
    rsi_period = IntParameter(10, 20, default=14, space="buy", optimize=True)

    # 볼린저밴드 매개변수
    bb_period = IntParameter(15, 25, default=20, space="buy", optimize=True)
    bb_deviation = DecimalParameter(1.8, 2.5, default=2.0, space="buy", optimize=True)

    # 선물거래 리스크 매개변수
    risk_percentage = DecimalParameter(0.5, 2.0, default=1.0, space="buy", optimize=True)
    max_leverage = IntParameter(2, 10, default=5, space="buy", optimize=True)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """로스 카메론 지표 + 선물거래 특화"""

        # 로스 카메론 핵심 지표
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=self.rsi_period.value)
        dataframe['rsi_7'] = ta.RSI(dataframe, timeperiod=7)   # 단기 RSI
        dataframe['rsi_21'] = ta.RSI(dataframe, timeperiod=21) # 장기 RSI

        # 볼린저밴드 (동적 편차)
        bb = ta.BBANDS(dataframe, timeperiod=self.bb_period.value,
                       nbdevup=self.bb_deviation.value, nbdevdn=self.bb_deviation.value)
        dataframe['bb_upper'] = bb['upperband']
        dataframe['bb_middle'] = bb['middleband']
        dataframe['bb_lower'] = bb['lowerband']
        dataframe['bb_width'] = (dataframe['bb_upper'] - dataframe['bb_lower']) / dataframe['bb_middle']
        dataframe['bb_percent'] = (dataframe['close'] - dataframe['bb_lower']) / \
                                 (dataframe['bb_upper'] - dataframe['bb_lower'])

        # 이동평균선 (트렌드 확인)
        dataframe['ema_9'] = ta.EMA(dataframe, timeperiod=9)
        dataframe['ema_20'] = ta.EMA(dataframe, timeperiod=20)
        dataframe['ema_50'] = ta.EMA(dataframe, timeperiod=50)

        # 거래량 분석
        dataframe['volume_sma'] = ta.SMA(dataframe['volume'], timeperiod=20)
        dataframe['volume_ratio'] = dataframe['volume'] / dataframe['volume_sma']

        # 변동성 지표 (레버리지 계산용)
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=14)
        dataframe['volatility'] = dataframe['atr'] / dataframe['close']

        # MACD (추세 확인)
        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macd_signal'] = macd['macdsignal']
        dataframe['macd_histogram'] = macd['macdhist']

        # 선물거래 특화 지표
        dataframe['funding_rate'] = self._get_funding_rate_indicator(metadata['pair'])
        dataframe['mark_price'] = dataframe['close']  # 실제로는 API에서 가져와야 함

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """로스 카메론 진입 신호 (선물 최적화)"""

        # 롱 진입 조건 - RSI 과매도 + 볼밴 하단 + 상승 모멘텀
        long_conditions = [
            # 핵심 RSI 조건 (로스 카메론 스타일)
            (dataframe['rsi'] < self.rsi_oversold.value),
            (dataframe['rsi_7'] < self.rsi_oversold.value + 5),  # 단기 RSI도 과매도

            # 볼린저밴드 조건 (반전 신호)
            (dataframe['close'] <= dataframe['bb_lower'] * 1.01),  # 하단 근처
            (dataframe['bb_percent'] < 0.2),  # 하위 20% 구간

            # 거래량 확인 (돌파력 확인)
            (dataframe['volume_ratio'] > 1.1),  # 평균 대비 10% 이상

            # 변동성 필터 (너무 높은 변동성 제외)
            (dataframe['volatility'] < 0.08),  # 8% 미만

            # 볼밴 폭 확인 (충분한 변동성)
            (dataframe['bb_width'] > 0.015),  # 1.5% 이상

            # 선물거래 특화 조건
            (dataframe['funding_rate'] <= 0.001),  # 높은 양의 자금조달료 제외
        ]

        dataframe.loc[
            self._combine_conditions(long_conditions),
            'enter_long'
        ] = 1

        # 숏 진입 조건 - RSI 과매수 + 볼밴 상단 + 하락 모멘텀
        short_conditions = [
            # 핵심 RSI 조건
            (dataframe['rsi'] > self.rsi_overbought.value),
            (dataframe['rsi_7'] > self.rsi_overbought.value - 5),  # 단기 RSI도 과매수

            # 볼린저밴드 조건
            (dataframe['close'] >= dataframe['bb_upper'] * 0.99),  # 상단 근처
            (dataframe['bb_percent'] > 0.8),  # 상위 80% 구간

            # 거래량 확인
            (dataframe['volume_ratio'] > 1.1),

            # 변동성 필터
            (dataframe['volatility'] < 0.08),

            # 볼밴 폭 확인
            (dataframe['bb_width'] > 0.015),

            # 선물거래 특화 조건
            (dataframe['funding_rate'] >= -0.001),  # 높은 음의 자금조달료 제외
        ]

        dataframe.loc[
            self._combine_conditions(short_conditions),
            'enter_short'
        ] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """로스 카메론 청산 신호"""

        # 롱 청산 - RSI 회복 또는 목표 달성
        dataframe.loc[
            (
                (dataframe['rsi'] > 60) |  # RSI 회복
                (dataframe['close'] > dataframe['bb_middle']) |  # 중간선 돌파
                (dataframe['bb_percent'] > 0.6) |  # 상위 구간 진입
                (dataframe['macd'] < dataframe['macd_signal'])  # MACD 하락 전환
            ),
            'exit_long'
        ] = 1

        # 숏 청산 - RSI 하락 또는 목표 달성
        dataframe.loc[
            (
                (dataframe['rsi'] < 40) |  # RSI 하락
                (dataframe['close'] < dataframe['bb_middle']) |  # 중간선 하락
                (dataframe['bb_percent'] < 0.4) |  # 하위 구간 진입
                (dataframe['macd'] > dataframe['macd_signal'])  # MACD 상승 전환
            ),
            'exit_short'
        ] = 1

        return dataframe

    def custom_stake_amount(self, pair: str, current_time, current_rate: float,
                           proposed_stake: float, min_stake: float, max_stake: float,
                           entry_tag: str, side: str, **kwargs) -> float:
        """로스 카메론 스타일 + AI 리스크 관리"""

        try:
            balance = self.wallets.get_total_stake_amount()

            # 변동성 기반 리스크 조정
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            if len(dataframe) == 0:
                return min_stake

            current_volatility = dataframe['volatility'].iloc[-1]
            bb_width = dataframe['bb_width'].iloc[-1]

            # 로스 카메론 스타일: 볼밴 폭에 따른 포지션 조정
            if bb_width > 0.04:  # 높은 변동성
                risk_factor = 0.5  # 리스크 감소
            elif bb_width < 0.02:  # 낮은 변동성
                risk_factor = 1.5  # 리스크 증가
            else:
                risk_factor = 1.0  # 기본

            # 동적 레버리지 계산
            optimal_leverage = self._calculate_optimal_leverage(current_volatility)

            # 리스크 기반 포지션 크기 계산
            risk_amount = balance * (self.risk_percentage.value / 100) * risk_factor
            effective_stop_distance = abs(self.stoploss) * optimal_leverage

            if effective_stop_distance > 0:
                position_size = risk_amount / effective_stop_distance
            else:
                position_size = min_stake

            # 최소/최대 제한 적용
            final_size = max(min_stake, min(position_size, max_stake))

            logger.info(f"Ross Cameron Position - Pair: {pair}, Volatility: {current_volatility:.4f}, "
                       f"BB Width: {bb_width:.4f}, Risk Factor: {risk_factor:.2f}, "
                       f"Leverage: {optimal_leverage}, Position: {final_size:.2f}")

            return final_size

        except Exception as e:
            logger.error(f"Ross Cameron stake calculation failed: {e}")
            return min_stake

    def leverage(self, pair: str, current_time, current_rate: float,
                proposed_leverage: float, max_leverage: float, entry_tag: str,
                side: str, **kwargs) -> float:
        """로스 카메론 스타일 레버리지"""

        try:
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            if len(dataframe) == 0:
                return min(3, max_leverage)

            current_volatility = dataframe['volatility'].iloc[-1]
            rsi = dataframe['rsi'].iloc[-1]

            # RSI 기반 레버리지 조정 (로스 카메론 특화)
            if side == 'long' and rsi < 25:  # 극도 과매도
                base_leverage = self._calculate_optimal_leverage(current_volatility) + 1
            elif side == 'short' and rsi > 75:  # 극도 과매수
                base_leverage = self._calculate_optimal_leverage(current_volatility) + 1
            else:
                base_leverage = self._calculate_optimal_leverage(current_volatility)

            final_leverage = min(base_leverage, self.max_leverage.value, max_leverage)

            logger.info(f"Ross Cameron Leverage - Pair: {pair}, RSI: {rsi:.1f}, "
                       f"Side: {side}, Leverage: {final_leverage}")

            return final_leverage

        except Exception as e:
            logger.error(f"Ross Cameron leverage calculation failed: {e}")
            return min(3, max_leverage)

    def custom_exit(self, pair: str, trade, current_time, current_rate: float,
                   current_profit: float, **kwargs) -> Optional[str]:
        """로스 카메론 스타일 동적 청산"""

        try:
            # 로스 카메론 스타일: 빠른 이익 실현
            if current_profit > 0.02:  # 2% 이익시
                return "ross_cameron_quick_profit"

            # 레버리지 기반 손실 제한
            leverage = trade.leverage or 1
            if leverage >= 5 and current_profit < -0.015:  # 1.5% 손실
                return "high_leverage_protection"

            # RSI 기반 청산 (추가 확인)
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            if len(dataframe) > 0:
                current_rsi = dataframe['rsi'].iloc[-1]

                if trade.is_short and current_rsi < 35:  # 숏에서 RSI 하락시
                    return "rsi_reversal_exit"
                elif not trade.is_short and current_rsi > 65:  # 롱에서 RSI 상승시
                    return "rsi_reversal_exit"

            return None

        except Exception as e:
            logger.error(f"Ross Cameron custom exit failed: {e}")
            return None

    def _calculate_optimal_leverage(self, volatility: float) -> int:
        """변동성 기반 최적 레버리지 계산"""

        if volatility > 0.06:      # 초고변동성 (>6%)
            return 2
        elif volatility > 0.04:    # 고변동성 (4-6%)
            return 3
        elif volatility > 0.025:   # 중변동성 (2.5-4%)
            return 4
        else:                      # 저변동성 (<2.5%)
            return 5

    def _combine_conditions(self, conditions: list) -> DataFrame:
        """조건들을 AND로 결합"""
        if not conditions:
            return pd.Series([False] * 1000)

        result = conditions[0]
        for condition in conditions[1:]:
            result = result & condition
        return result

    def _get_funding_rate_indicator(self, pair: str) -> DataFrame:
        """자금 조달 수수료 지표 생성 (모의)"""
        # 실제 구현에서는 exchange API에서 가져와야 함
        # 현재는 모의 데이터로 0.0005% 고정값 사용
        return pd.Series([0.0005] * 1000)

    def custom_entry_price(self, pair: str, current_time, proposed_rate: float,
                          entry_tag: str, side: str, **kwargs) -> float:
        """로스 카메론 스타일 진입가 최적화"""

        try:
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            if len(dataframe) == 0:
                return proposed_rate

            if side == "long":
                # 볼린저밴드 하단 근처에서 진입
                bb_lower = dataframe['bb_lower'].iloc[-1]
                return min(proposed_rate, bb_lower * 1.002)  # 0.2% 위

            elif side == "short":
                # 볼린저밴드 상단 근처에서 진입
                bb_upper = dataframe['bb_upper'].iloc[-1]
                return max(proposed_rate, bb_upper * 0.998)  # 0.2% 아래

            return proposed_rate

        except Exception as e:
            logger.error(f"Custom entry price calculation failed: {e}")
            return proposed_rate

    def informative_pairs(self):
        """추가 정보성 페어"""
        return []