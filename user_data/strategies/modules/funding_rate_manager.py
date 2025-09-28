#!/usr/bin/env python3
"""
Funding Rate Manager
===================

자금 조달 수수료 분석 및 수익 창출 시스템
- 실시간 자금 조달료 모니터링
- 수익성 분석 및 포지션 추천
- 자금 조달료 기반 전략 최적화
"""

import requests
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FundingRateData:
    """자금 조달 수수료 데이터"""
    symbol: str
    funding_rate: float
    funding_time: datetime
    next_funding_time: datetime
    mark_price: float
    estimated_income: float
    recommendation: str

class FundingRateManager:
    """자금 조달 수수료 관리 시스템"""

    def __init__(self, exchange):
        self.exchange = exchange
        self.funding_threshold_high = 0.01    # 1% 이상 (매우 높음)
        self.funding_threshold_medium = 0.005 # 0.5% 이상 (높음)
        self.funding_threshold_low = 0.001    # 0.1% 이상 (보통)

        self.funding_history = {}
        self.position_recommendations = {}

    def get_current_funding_rate(self, pair: str) -> Optional[FundingRateData]:
        """현재 자금 조달 수수료 조회"""
        try:
            # Binance Futures API에서 자금조달료 가져오기
            funding_info = self.exchange.fetch_funding_rate(pair)

            current_rate = funding_info.get('fundingRate', 0)
            funding_time = datetime.fromtimestamp(funding_info.get('fundingTimestamp', 0) / 1000)
            next_time = self._calculate_next_funding_time(funding_time)
            mark_price = funding_info.get('markPrice', 0)

            # 8시간당 예상 수익 계산
            estimated_income = abs(current_rate) if current_rate != 0 else 0

            # 추천 생성
            recommendation = self._generate_recommendation(current_rate)

            return FundingRateData(
                symbol=pair,
                funding_rate=current_rate,
                funding_time=funding_time,
                next_funding_time=next_time,
                mark_price=mark_price,
                estimated_income=estimated_income,
                recommendation=recommendation
            )

        except Exception as e:
            logger.error(f"Failed to fetch funding rate for {pair}: {e}")
            return None

    def _calculate_next_funding_time(self, current_funding_time: datetime) -> datetime:
        """다음 자금 조달 시간 계산 (8시간마다)"""
        next_time = current_funding_time + timedelta(hours=8)
        return next_time

    def _generate_recommendation(self, funding_rate: float) -> str:
        """자금 조달료 기반 추천 생성"""

        if funding_rate > self.funding_threshold_high:
            return "short_highly_profitable"    # 숏 매우 유리
        elif funding_rate > self.funding_threshold_medium:
            return "short_profitable"           # 숏 유리
        elif funding_rate > self.funding_threshold_low:
            return "short_favorable"            # 숏 선호
        elif funding_rate < -self.funding_threshold_high:
            return "long_highly_profitable"     # 롱 매우 유리
        elif funding_rate < -self.funding_threshold_medium:
            return "long_profitable"            # 롱 유리
        elif funding_rate < -self.funding_threshold_low:
            return "long_favorable"             # 롱 선호
        else:
            return "neutral"                    # 중립

    def analyze_funding_opportunity(self, pair: str) -> Dict:
        """자금 조달료 수익 기회 분석"""

        funding_data = self.get_current_funding_rate(pair)
        if not funding_data:
            return {"status": "error", "message": "Failed to fetch funding data"}

        current_time = datetime.now()
        time_to_funding = (funding_data.next_funding_time - current_time).total_seconds() / 3600

        analysis = {
            'pair': pair,
            'funding_rate': funding_data.funding_rate,
            'funding_rate_percent': funding_data.funding_rate * 100,
            'next_funding_time': funding_data.next_funding_time,
            'hours_to_funding': time_to_funding,
            'estimated_8h_return': funding_data.estimated_income * 100,
            'annualized_return': funding_data.estimated_income * 365 * 3 * 100,  # 년 1095회
            'recommendation': funding_data.recommendation,
            'profitability_score': self._calculate_profitability_score(funding_data.funding_rate),
            'risk_level': self._assess_risk_level(funding_data.funding_rate),
            'suggested_action': self._suggest_action(funding_data)
        }

        return analysis

    def _calculate_profitability_score(self, funding_rate: float) -> int:
        """수익성 점수 계산 (1-10)"""
        abs_rate = abs(funding_rate)

        if abs_rate >= 0.01:      # >= 1%
            return 10
        elif abs_rate >= 0.005:   # >= 0.5%
            return 8
        elif abs_rate >= 0.002:   # >= 0.2%
            return 6
        elif abs_rate >= 0.001:   # >= 0.1%
            return 4
        elif abs_rate >= 0.0005:  # >= 0.05%
            return 2
        else:
            return 1

    def _assess_risk_level(self, funding_rate: float) -> str:
        """리스크 레벨 평가"""
        abs_rate = abs(funding_rate)

        if abs_rate >= 0.01:
            return "high"     # 높은 수익이지만 시장 불안정 가능
        elif abs_rate >= 0.005:
            return "medium"   # 적당한 수익과 리스크
        else:
            return "low"      # 낮은 리스크

    def _suggest_action(self, funding_data: FundingRateData) -> str:
        """구체적인 행동 제안"""

        rate = funding_data.funding_rate
        time_to_funding = (funding_data.next_funding_time - datetime.now()).total_seconds() / 3600

        if time_to_funding > 6:
            return "wait_closer_to_funding"

        if rate > 0.01:
            return f"open_short_position_high_profit"
        elif rate > 0.005:
            return f"open_short_position_good_profit"
        elif rate > 0.001:
            return f"consider_short_position"
        elif rate < -0.01:
            return f"open_long_position_high_profit"
        elif rate < -0.005:
            return f"open_long_position_good_profit"
        elif rate < -0.001:
            return f"consider_long_position"
        else:
            return "no_action_recommended"

    def should_hold_for_funding(self, pair: str, side: str, current_profit: float = 0) -> bool:
        """자금 조달료 수익을 위해 포지션 유지 여부 판단"""

        funding_data = self.get_current_funding_rate(pair)
        if not funding_data:
            return False

        time_to_funding = (funding_data.next_funding_time - datetime.now()).total_seconds() / 3600
        funding_rate = funding_data.funding_rate

        # 자금 조달 시간이 2시간 이내이고 수익성이 있는 경우
        if time_to_funding <= 2 and abs(funding_rate) >= 0.005:  # 0.5% 이상

            # 롱 포지션이고 음의 자금조달료 (롱에 유리)
            if side == 'long' and funding_rate < -0.005:
                expected_funding_profit = abs(funding_rate)
                # 현재 손실이 예상 자금조달료 수익보다 작으면 유지
                if current_profit > -expected_funding_profit:
                    return True

            # 숏 포지션이고 양의 자금조달료 (숏에 유리)
            elif side == 'short' and funding_rate > 0.005:
                expected_funding_profit = abs(funding_rate)
                # 현재 손실이 예상 자금조달료 수익보다 작으면 유지
                if current_profit > -expected_funding_profit:
                    return True

        return False

    def get_multi_pair_analysis(self, pairs: List[str]) -> Dict[str, Dict]:
        """여러 페어의 자금 조달료 분석"""

        results = {}
        for pair in pairs:
            try:
                analysis = self.analyze_funding_opportunity(pair)
                results[pair] = analysis
                time.sleep(0.1)  # API 호출 제한 방지
            except Exception as e:
                logger.error(f"Failed to analyze {pair}: {e}")
                results[pair] = {"status": "error", "message": str(e)}

        return results

    def find_best_funding_opportunities(self, pairs: List[str], min_score: int = 6) -> List[Dict]:
        """최고의 자금 조달료 기회 찾기"""

        analyses = self.get_multi_pair_analysis(pairs)
        opportunities = []

        for pair, analysis in analyses.items():
            if analysis.get('status') == 'error':
                continue

            score = analysis.get('profitability_score', 0)
            if score >= min_score:
                opportunities.append({
                    'pair': pair,
                    'score': score,
                    'funding_rate': analysis['funding_rate'],
                    'estimated_return': analysis['estimated_8h_return'],
                    'recommendation': analysis['recommendation'],
                    'risk_level': analysis['risk_level'],
                    'hours_to_funding': analysis['hours_to_funding']
                })

        # 점수순으로 정렬
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        return opportunities

    def generate_funding_report(self, pairs: List[str]) -> str:
        """자금 조달료 분석 리포트 생성"""

        opportunities = self.find_best_funding_opportunities(pairs, min_score=4)

        report = "🏦 FUNDING RATE ANALYSIS REPORT\n"
        report += "=" * 50 + "\n\n"

        if not opportunities:
            report += "❌ No profitable funding opportunities found.\n"
            return report

        report += f"✅ Found {len(opportunities)} funding opportunities:\n\n"

        for i, opp in enumerate(opportunities[:5], 1):  # 상위 5개만 표시
            report += f"{i}. {opp['pair']}\n"
            report += f"   📊 Score: {opp['score']}/10\n"
            report += f"   💰 Funding Rate: {opp['funding_rate']*100:.3f}%\n"
            report += f"   📈 8h Return: {opp['estimated_return']:.3f}%\n"
            report += f"   🎯 Action: {opp['recommendation']}\n"
            report += f"   ⚠️  Risk: {opp['risk_level']}\n"
            report += f"   ⏰ Next funding: {opp['hours_to_funding']:.1f}h\n\n"

        # 총 요약
        total_high_score = len([o for o in opportunities if o['score'] >= 8])
        avg_return = np.mean([o['estimated_return'] for o in opportunities])

        report += f"📋 SUMMARY:\n"
        report += f"   High-score opportunities: {total_high_score}\n"
        report += f"   Average 8h return: {avg_return:.3f}%\n"
        report += f"   Report time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

        return report

    def update_funding_history(self, pair: str):
        """자금 조달료 히스토리 업데이트"""

        funding_data = self.get_current_funding_rate(pair)
        if funding_data:
            if pair not in self.funding_history:
                self.funding_history[pair] = []

            self.funding_history[pair].append({
                'timestamp': datetime.now(),
                'funding_rate': funding_data.funding_rate,
                'mark_price': funding_data.mark_price
            })

            # 최근 100개 기록만 유지
            if len(self.funding_history[pair]) > 100:
                self.funding_history[pair] = self.funding_history[pair][-100:]

    def get_funding_trend(self, pair: str, periods: int = 10) -> Dict:
        """자금 조달료 트렌드 분석"""

        if pair not in self.funding_history or len(self.funding_history[pair]) < periods:
            return {"status": "insufficient_data"}

        recent_rates = [h['funding_rate'] for h in self.funding_history[pair][-periods:]]

        trend_analysis = {
            'pair': pair,
            'periods_analyzed': periods,
            'current_rate': recent_rates[-1],
            'average_rate': np.mean(recent_rates),
            'trend_direction': 'increasing' if recent_rates[-1] > recent_rates[0] else 'decreasing',
            'volatility': np.std(recent_rates),
            'max_rate': max(recent_rates),
            'min_rate': min(recent_rates),
            'trend_strength': abs(recent_rates[-1] - recent_rates[0]) / max(abs(recent_rates[0]), 0.0001)
        }

        return trend_analysis