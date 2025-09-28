#!/usr/bin/env python3
"""
Advanced Leverage Manager
========================

고급 레버리지 관리 시스템
- 시장 조건별 동적 레버리지 조정
- 변동성 기반 레버리지 최적화
- 포트폴리오 레벨 레버리지 관리
- 리스크 기반 레버리지 제한
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class MarketCondition(Enum):
    """시장 상태"""
    BULL_STRONG = "bull_strong"        # 강한 상승
    BULL_WEAK = "bull_weak"            # 약한 상승
    SIDEWAYS = "sideways"              # 횡보
    BEAR_WEAK = "bear_weak"            # 약한 하락
    BEAR_STRONG = "bear_strong"        # 강한 하락
    VOLATILE = "volatile"              # 고변동성

class VolatilityLevel(Enum):
    """변동성 수준"""
    VERY_LOW = "very_low"      # < 1%
    LOW = "low"                # 1-2%
    NORMAL = "normal"          # 2-4%
    HIGH = "high"              # 4-8%
    VERY_HIGH = "very_high"    # > 8%

@dataclass
class LeverageRecommendation:
    """레버리지 추천"""
    symbol: str
    current_leverage: int
    recommended_leverage: int
    max_safe_leverage: int
    volatility_level: VolatilityLevel
    market_condition: MarketCondition
    confidence_score: float  # 0-1
    reasoning: str

class AdvancedLeverageManager:
    """고급 레버리지 관리"""

    def __init__(self, position_manager, exchange):
        self.position_manager = position_manager
        self.exchange = exchange

        # 레버리지 제한 설정
        self.max_leverage_limits = {
            VolatilityLevel.VERY_LOW: 20,
            VolatilityLevel.LOW: 15,
            VolatilityLevel.NORMAL: 10,
            VolatilityLevel.HIGH: 5,
            VolatilityLevel.VERY_HIGH: 2
        }

        # 시장 조건별 레버리지 승수
        self.market_condition_multipliers = {
            MarketCondition.BULL_STRONG: 1.2,
            MarketCondition.BULL_WEAK: 1.0,
            MarketCondition.SIDEWAYS: 0.8,
            MarketCondition.BEAR_WEAK: 0.8,
            MarketCondition.BEAR_STRONG: 0.6,
            MarketCondition.VOLATILE: 0.5
        }

    def calculate_optimal_leverage(self, pair: str, side: str = 'long',
                                 portfolio_exposure: float = 0.5) -> LeverageRecommendation:
        """최적 레버리지 계산"""

        try:
            # 1. 변동성 분석
            volatility_data = self._analyze_volatility(pair)
            volatility_level = self._classify_volatility(volatility_data['current_volatility'])

            # 2. 시장 조건 분석
            market_condition = self._analyze_market_condition(pair)

            # 3. 기본 레버리지 계산
            base_leverage = self.max_leverage_limits[volatility_level]

            # 4. 시장 조건 적용
            market_multiplier = self.market_condition_multipliers[market_condition]
            adjusted_leverage = int(base_leverage * market_multiplier)

            # 5. 포트폴리오 노출도 고려
            portfolio_adjustment = max(0.5, 1 - portfolio_exposure)
            final_leverage = max(1, int(adjusted_leverage * portfolio_adjustment))

            # 6. 안전 한계 계산
            max_safe_leverage = self._calculate_max_safe_leverage(pair, volatility_data)

            # 7. 최종 추천값
            recommended_leverage = min(final_leverage, max_safe_leverage)

            # 8. 신뢰도 계산
            confidence_score = self._calculate_confidence_score(
                volatility_data, market_condition, portfolio_exposure
            )

            # 9. 추론 설명
            reasoning = self._generate_reasoning(
                volatility_level, market_condition, portfolio_exposure,
                base_leverage, recommended_leverage
            )

            return LeverageRecommendation(
                symbol=pair,
                current_leverage=self._get_current_leverage(pair),
                recommended_leverage=recommended_leverage,
                max_safe_leverage=max_safe_leverage,
                volatility_level=volatility_level,
                market_condition=market_condition,
                confidence_score=confidence_score,
                reasoning=reasoning
            )

        except Exception as e:
            logger.error(f"Leverage calculation failed for {pair}: {e}")
            return self._get_fallback_recommendation(pair)

    def _analyze_volatility(self, pair: str, periods: int = 24) -> Dict:
        """변동성 분석"""

        try:
            # 1시간 OHLCV 데이터 가져오기
            ohlcv = self.exchange.fetch_ohlcv(pair, '1h', limit=periods * 2)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

            # 수익률 계산
            df['returns'] = df['close'].pct_change()

            # 다양한 변동성 지표 계산
            current_volatility = df['returns'].tail(periods).std() * np.sqrt(24)  # 일일 변동성
            rolling_vol_5d = df['returns'].tail(120).std() * np.sqrt(24)  # 5일 변동성
            rolling_vol_30d = df['returns'].tail(720).std() * np.sqrt(24)  # 30일 변동성

            # ATR 기반 변동성
            df['tr'] = np.maximum(
                df['high'] - df['low'],
                np.maximum(
                    abs(df['high'] - df['close'].shift(1)),
                    abs(df['low'] - df['close'].shift(1))
                )
            )
            atr_volatility = df['tr'].tail(periods).mean() / df['close'].iloc[-1]

            # 볼린저밴드 폭
            bb_period = min(20, len(df))
            sma = df['close'].tail(bb_period).mean()
            bb_std = df['close'].tail(bb_period).std()
            bb_width = (bb_std * 2) / sma

            return {
                'current_volatility': current_volatility,
                'vol_5d': rolling_vol_5d,
                'vol_30d': rolling_vol_30d,
                'atr_volatility': atr_volatility,
                'bb_width': bb_width,
                'vol_trend': 'increasing' if current_volatility > rolling_vol_30d else 'decreasing',
                'vol_percentile': self._calculate_volatility_percentile(df['returns'], current_volatility)
            }

        except Exception as e:
            logger.error(f"Volatility analysis failed for {pair}: {e}")
            return {'current_volatility': 0.04}  # 기본값

    def _classify_volatility(self, volatility: float) -> VolatilityLevel:
        """변동성 수준 분류"""

        if volatility < 0.01:
            return VolatilityLevel.VERY_LOW
        elif volatility < 0.02:
            return VolatilityLevel.LOW
        elif volatility < 0.04:
            return VolatilityLevel.NORMAL
        elif volatility < 0.08:
            return VolatilityLevel.HIGH
        else:
            return VolatilityLevel.VERY_HIGH

    def _analyze_market_condition(self, pair: str) -> MarketCondition:
        """시장 조건 분석"""

        try:
            # 다양한 기간의 가격 데이터 분석
            ohlcv = self.exchange.fetch_ohlcv(pair, '1h', limit=168)  # 7일
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

            current_price = df['close'].iloc[-1]

            # 이동평균선 계산
            df['sma_24'] = df['close'].rolling(24).mean()   # 1일
            df['sma_72'] = df['close'].rolling(72).mean()   # 3일
            df['sma_168'] = df['close'].rolling(168).mean() # 7일

            # 가격 변화율 계산
            change_24h = (current_price - df['close'].iloc[-25]) / df['close'].iloc[-25]
            change_72h = (current_price - df['close'].iloc[-73]) / df['close'].iloc[-73]

            # 트렌드 강도 계산
            sma_24 = df['sma_24'].iloc[-1]
            sma_72 = df['sma_72'].iloc[-1]
            sma_168 = df['sma_168'].iloc[-1]

            # 볼린저밴드 위치
            bb_sma = df['close'].tail(20).mean()
            bb_std = df['close'].tail(20).std()
            bb_position = (current_price - bb_sma) / (bb_std * 2)

            # 변동성
            volatility = df['close'].pct_change().tail(24).std()

            # 조건 판단
            if volatility > 0.08:  # 8% 이상 변동성
                return MarketCondition.VOLATILE
            elif change_24h > 0.05 and current_price > sma_24 > sma_72:  # 강한 상승
                return MarketCondition.BULL_STRONG
            elif change_24h > 0.02 and current_price > sma_24:  # 약한 상승
                return MarketCondition.BULL_WEAK
            elif change_24h < -0.05 and current_price < sma_24 < sma_72:  # 강한 하락
                return MarketCondition.BEAR_STRONG
            elif change_24h < -0.02 and current_price < sma_24:  # 약한 하락
                return MarketCondition.BEAR_WEAK
            else:  # 횡보
                return MarketCondition.SIDEWAYS

        except Exception as e:
            logger.error(f"Market condition analysis failed for {pair}: {e}")
            return MarketCondition.SIDEWAYS

    def _calculate_max_safe_leverage(self, pair: str, volatility_data: Dict) -> int:
        """최대 안전 레버리지 계산"""

        # VaR 기반 계산 (Value at Risk)
        current_vol = volatility_data.get('current_volatility', 0.04)

        # 95% 신뢰도로 일일 최대 손실 5% 제한
        max_daily_loss = 0.05
        confidence_level = 1.645  # 95% 신뢰도 z-score

        # 안전 레버리지 = 최대 허용 손실 / (변동성 * 신뢰구간)
        safe_leverage = max_daily_loss / (current_vol * confidence_level)

        # 정수로 변환하고 최소 1, 최대 50 제한
        return max(1, min(int(safe_leverage), 50))

    def _calculate_volatility_percentile(self, returns: pd.Series, current_vol: float) -> float:
        """변동성 백분위 계산"""

        if len(returns) < 30:
            return 0.5

        # 30일 롤링 변동성 계산
        rolling_vols = []
        for i in range(30, len(returns)):
            vol = returns.iloc[i-30:i].std()
            rolling_vols.append(vol)

        if not rolling_vols:
            return 0.5

        # 현재 변동성의 백분위 계산
        percentile = np.percentile(rolling_vols, current_vol * 100)
        return max(0, min(1, percentile))

    def _get_current_leverage(self, pair: str) -> int:
        """현재 레버리지 조회"""

        try:
            position = self.position_manager.get_position_info(pair)
            if position:
                return position.leverage
            else:
                # 기본 레버리지 조회 (포지션이 없는 경우)
                symbol = pair.replace('/', '')
                leverage_brackets = self.exchange._api.futures_leverage_bracket(symbol=symbol)
                if leverage_brackets:
                    return leverage_brackets[0]['initialLeverage']
        except Exception as e:
            logger.error(f"Failed to get current leverage for {pair}: {e}")

        return 1  # 기본값

    def _calculate_confidence_score(self, volatility_data: Dict, market_condition: MarketCondition,
                                  portfolio_exposure: float) -> float:
        """신뢰도 점수 계산"""

        base_confidence = 0.8

        # 변동성 데이터 품질
        if volatility_data.get('vol_trend') == 'stable':
            base_confidence += 0.1

        # 시장 조건 명확성
        if market_condition in [MarketCondition.BULL_STRONG, MarketCondition.BEAR_STRONG]:
            base_confidence += 0.1
        elif market_condition == MarketCondition.VOLATILE:
            base_confidence -= 0.2

        # 포트폴리오 다양성
        if 0.3 <= portfolio_exposure <= 0.7:  # 적절한 분산
            base_confidence += 0.1

        return max(0.1, min(1.0, base_confidence))

    def _generate_reasoning(self, volatility_level: VolatilityLevel, market_condition: MarketCondition,
                          portfolio_exposure: float, base_leverage: int, final_leverage: int) -> str:
        """추론 설명 생성"""

        reasoning = f"Base leverage {base_leverage}x for {volatility_level.value} volatility. "

        market_impact = self.market_condition_multipliers[market_condition]
        if market_impact > 1.0:
            reasoning += f"Increased due to {market_condition.value} market (+{(market_impact-1)*100:.0f}%). "
        elif market_impact < 1.0:
            reasoning += f"Reduced due to {market_condition.value} market ({(market_impact-1)*100:.0f}%). "

        if portfolio_exposure > 0.7:
            reasoning += f"Further reduced due to high portfolio exposure ({portfolio_exposure:.1%}). "

        reasoning += f"Final recommendation: {final_leverage}x."

        return reasoning

    def _get_fallback_recommendation(self, pair: str) -> LeverageRecommendation:
        """기본 추천 (에러 시)"""

        return LeverageRecommendation(
            symbol=pair,
            current_leverage=1,
            recommended_leverage=3,
            max_safe_leverage=5,
            volatility_level=VolatilityLevel.NORMAL,
            market_condition=MarketCondition.SIDEWAYS,
            confidence_score=0.5,
            reasoning="Fallback recommendation due to analysis error"
        )

    def optimize_portfolio_leverage(self, pairs: List[str]) -> Dict[str, LeverageRecommendation]:
        """포트폴리오 레벨 레버리지 최적화"""

        recommendations = {}
        total_exposure = 0

        # 현재 포트폴리오 노출도 계산
        positions = self.position_manager.get_position_info()
        if positions:
            balance_info = self.position_manager.get_account_balance()
            total_balance = balance_info.get('total_wallet_balance', 1)

            for position in positions:
                position_value = position.size * position.mark_price
                exposure = position_value / total_balance
                total_exposure += exposure

        # 각 페어별 추천 계산
        for pair in pairs:
            try:
                recommendation = self.calculate_optimal_leverage(
                    pair, portfolio_exposure=total_exposure
                )
                recommendations[pair] = recommendation
            except Exception as e:
                logger.error(f"Portfolio optimization failed for {pair}: {e}")
                recommendations[pair] = self._get_fallback_recommendation(pair)

        return recommendations

    def adjust_leverage_based_on_pnl(self, pair: str, current_pnl_percent: float) -> int:
        """손익률 기반 레버리지 조정"""

        base_recommendation = self.calculate_optimal_leverage(pair)
        base_leverage = base_recommendation.recommended_leverage

        # 손익률에 따른 조정
        if current_pnl_percent > 0.2:  # 20% 이상 수익
            # 수익 보호를 위해 레버리지 감소
            adjusted_leverage = max(1, int(base_leverage * 0.7))
        elif current_pnl_percent < -0.1:  # 10% 이상 손실
            # 추가 손실 방지를 위해 레버리지 대폭 감소
            adjusted_leverage = max(1, int(base_leverage * 0.5))
        elif current_pnl_percent < -0.05:  # 5% 이상 손실
            # 레버리지 감소
            adjusted_leverage = max(1, int(base_leverage * 0.8))
        else:
            # 정상 범위
            adjusted_leverage = base_leverage

        return adjusted_leverage

    def generate_leverage_report(self, pairs: List[str]) -> str:
        """레버리지 분석 리포트 생성"""

        recommendations = self.optimize_portfolio_leverage(pairs)

        report = "⚖️ LEVERAGE OPTIMIZATION REPORT\n"
        report += "=" * 50 + "\n\n"

        if not recommendations:
            report += "❌ No pairs to analyze\n"
            return report

        # 요약 통계
        avg_confidence = np.mean([r.confidence_score for r in recommendations.values()])
        high_confidence_count = len([r for r in recommendations.values() if r.confidence_score > 0.8])

        report += f"📊 SUMMARY:\n"
        report += f"   Pairs analyzed: {len(recommendations)}\n"
        report += f"   Average confidence: {avg_confidence:.1%}\n"
        report += f"   High confidence recommendations: {high_confidence_count}\n\n"

        # 개별 추천
        report += "🎯 INDIVIDUAL RECOMMENDATIONS:\n\n"

        for pair, rec in recommendations.items():
            confidence_emoji = "🟢" if rec.confidence_score > 0.8 else "🟡" if rec.confidence_score > 0.6 else "🔴"

            report += f"📈 {pair}\n"
            report += f"   Current: {rec.current_leverage}x\n"
            report += f"   Recommended: {rec.recommended_leverage}x\n"
            report += f"   Max Safe: {rec.max_safe_leverage}x\n"
            report += f"   Volatility: {rec.volatility_level.value}\n"
            report += f"   Market: {rec.market_condition.value}\n"
            report += f"   {confidence_emoji} Confidence: {rec.confidence_score:.1%}\n"
            report += f"   Reasoning: {rec.reasoning}\n\n"

        # 포트폴리오 레벨 조언
        high_leverage_count = len([r for r in recommendations.values() if r.recommended_leverage > 10])
        if high_leverage_count > 3:
            report += "⚠️ WARNING: Multiple high-leverage recommendations detected.\n"
            report += "   Consider reducing overall portfolio risk.\n\n"

        report += f"📅 Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

        return report

    def validate_leverage_change(self, pair: str, new_leverage: int) -> Dict:
        """레버리지 변경 유효성 검사"""

        try:
            # 현재 포지션 확인
            position = self.position_manager.get_position_info(pair)

            # 권장 레버리지와 비교
            recommendation = self.calculate_optimal_leverage(pair)

            # 유효성 검사
            validation_result = {
                'is_valid': True,
                'warnings': [],
                'recommendations': [],
                'risk_score': 0  # 0-100
            }

            # 1. 최대 안전 레버리지 초과 확인
            if new_leverage > recommendation.max_safe_leverage:
                validation_result['warnings'].append(
                    f"Leverage {new_leverage}x exceeds safe limit {recommendation.max_safe_leverage}x"
                )
                validation_result['risk_score'] += 30

            # 2. 변동성 대비 레버리지 확인
            if (recommendation.volatility_level == VolatilityLevel.VERY_HIGH and
                new_leverage > 3):
                validation_result['warnings'].append(
                    f"High leverage {new_leverage}x in very high volatility market"
                )
                validation_result['risk_score'] += 25

            # 3. 시장 조건 확인
            if (recommendation.market_condition == MarketCondition.VOLATILE and
                new_leverage > 5):
                validation_result['warnings'].append(
                    f"High leverage {new_leverage}x in volatile market conditions"
                )
                validation_result['risk_score'] += 20

            # 4. 기존 포지션이 있는 경우 추가 확인
            if position:
                if position.risk_level in ['HIGH', 'CRITICAL']:
                    validation_result['warnings'].append(
                        f"Current position already at {position.risk_level} risk level"
                    )
                    validation_result['risk_score'] += 25

            # 5. 권장사항 생성
            if new_leverage > recommendation.recommended_leverage * 1.5:
                validation_result['recommendations'].append(
                    f"Consider using recommended leverage {recommendation.recommended_leverage}x"
                )

            if validation_result['risk_score'] > 50:
                validation_result['recommendations'].append(
                    "Consider reducing leverage for better risk management"
                )

            # 6. 최종 유효성 판단
            if validation_result['risk_score'] > 70:
                validation_result['is_valid'] = False

            return validation_result

        except Exception as e:
            logger.error(f"Leverage validation failed for {pair}: {e}")
            return {
                'is_valid': False,
                'warnings': [f"Validation error: {str(e)}"],
                'recommendations': ["Use conservative leverage due to validation error"],
                'risk_score': 100
            }