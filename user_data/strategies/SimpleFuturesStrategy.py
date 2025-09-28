#!/usr/bin/env python3
"""
Simple Futures Strategy - Testing Version
=========================================

간단한 선물거래 전략으로 AI 리스크 관리 시스템 테스트용
- RSI 기반 단순 진입/청산
- 볼린저밴드 확인
- 레버리지 고려 포지션 계산
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


class SimpleFuturesStrategy(IStrategy):
    """간단한 선물거래 테스트 전략"""

    # 전략 메타데이터
    INTERFACE_VERSION = 3
    timeframe = '15m'
    can_short = True  # 숏 포지션 활성화

    # 선물거래 전용 매개변수
    minimal_roi = {
        "0": 0.03,   # 3% 목표 수익
        "60": 0.01,  # 1시간 후 1%
        "120": 0     # 2시간 후 손절
    }
    stoploss = -0.03  # 3% 스탑로스

    # 간단한 매개변수
    rsi_overbought = IntParameter(65, 80, default=70, space="sell", optimize=False)
    rsi_oversold = IntParameter(20, 35, default=30, space="buy", optimize=False)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """간단한 지표 생성"""

        # 기본 지표
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)

        # 볼린저밴드
        bb = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2.0, nbdevdn=2.0)
        dataframe['bb_upper'] = bb['upperband']
        dataframe['bb_middle'] = bb['middleband']
        dataframe['bb_lower'] = bb['lowerband']

        # 변동성 (레버리지 계산용)
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=14)
        dataframe['volatility'] = dataframe['atr'] / dataframe['close']

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """간단한 진입 신호"""

        # 롱 진입 - RSI 과매도
        dataframe.loc[
            (dataframe['rsi'] < self.rsi_oversold.value) &
            (dataframe['close'] < dataframe['bb_middle']),
            'enter_long'
        ] = 1

        # 숏 진입 - RSI 과매수
        dataframe.loc[
            (dataframe['rsi'] > self.rsi_overbought.value) &
            (dataframe['close'] > dataframe['bb_middle']),
            'enter_short'
        ] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """간단한 청산 신호"""

        # 롱 청산
        dataframe.loc[
            (dataframe['rsi'] > 60),
            'exit_long'
        ] = 1

        # 숏 청산
        dataframe.loc[
            (dataframe['rsi'] < 40),
            'exit_short'
        ] = 1

        return dataframe

    def custom_stake_amount(self, pair: str, current_time, current_rate: float,
                           proposed_stake: float, min_stake: float, max_stake: float,
                           entry_tag: str, side: str, **kwargs) -> float:
        """간단한 포지션 크기 계산"""

        try:
            balance = self.wallets.get_total_stake_amount()

            # 고정 1% 리스크
            risk_amount = balance * 0.01

            # 레버리지 고려
            stop_distance = abs(self.stoploss)
            position_size = risk_amount / stop_distance

            # 제한 적용
            final_size = max(min_stake, min(position_size, max_stake))

            logger.info(f"Simple Position - Pair: {pair}, Risk: {risk_amount:.2f}, "
                       f"Position: {final_size:.2f}")

            return final_size

        except Exception as e:
            logger.error(f"Stake calculation failed: {e}")
            return min_stake

    def leverage(self, pair: str, current_time, current_rate: float,
                proposed_leverage: float, max_leverage: float, entry_tag: str,
                side: str, **kwargs) -> float:
        """간단한 레버리지 설정"""

        try:
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            if len(dataframe) == 0:
                return 3  # 기본값

            volatility = dataframe['volatility'].iloc[-1]

            # 변동성 기반 레버리지
            if volatility > 0.05:
                leverage = 2
            elif volatility > 0.03:
                leverage = 3
            else:
                leverage = 5

            return min(leverage, max_leverage)

        except Exception as e:
            logger.error(f"Leverage calculation failed: {e}")
            return 3

    def informative_pairs(self):
        """추가 정보성 페어"""
        return []