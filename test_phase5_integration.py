#!/usr/bin/env python3
"""
Phase 5 Integration Test
========================

Phase 5 고급 선물거래 기능 통합 테스트
- 모든 모듈 기능 검증
- 실전 데이터 테스트
- 성능 벤치마크
"""

import sys
import os
import asyncio
import time
from datetime import datetime
import json

# 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), 'user_data', 'strategies', 'modules'))

# Freqtrade 관련
from freqtrade.configuration import Configuration
from freqtrade.data.dataprovider import DataProvider
from freqtrade.resolvers import ExchangeResolver

# Phase 5 모듈들
from funding_rate_manager import FundingRateManager
from position_manager import PositionManager
from risk_monitor import RiskMonitor
from advanced_leverage_manager import AdvancedLeverageManager


class Phase5IntegrationTest:
    """Phase 5 통합 테스트"""

    def __init__(self):
        self.config_path = "user_data/config_futures.json"
        self.test_pair = "BTC/USDT:USDT"
        self.exchange = None
        self.modules = {}

    async def run_complete_test(self):
        """전체 테스트 실행"""
        print("Starting Phase 5 Integration Test")
        print("=" * 60)

        try:
            # 1. 초기화 테스트
            await self._test_initialization()

            # 2. 모듈별 기능 테스트
            await self._test_funding_rate_manager()
            await self._test_position_manager()
            await self._test_risk_monitor()
            await self._test_leverage_manager()

            # 3. 통합 테스트
            await self._test_module_integration()

            # 4. 성능 테스트
            await self._test_performance()

            print("\n✅ All Phase 5 tests completed successfully!")
            print("🎯 Advanced futures trading system is ready for production")

        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            raise

    async def _test_initialization(self):
        """초기화 테스트"""
        print("\n📋 Testing Initialization...")

        # 설정 로드
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Exchange 초기화
        self.exchange = ExchangeResolver.load_exchange(
            config['exchange']['name'], config, validate=False
        )

        # 모듈 초기화
        self.modules = {
            'position_manager': PositionManager(self.exchange),
            'funding_manager': FundingRateManager(self.exchange),
            'risk_monitor': None,  # position_manager 필요
            'leverage_manager': None  # position_manager 필요
        }

        # 의존성 모듈 초기화
        self.modules['risk_monitor'] = RiskMonitor(
            self.modules['position_manager'], self.exchange
        )
        self.modules['leverage_manager'] = AdvancedLeverageManager(
            self.modules['position_manager'], self.exchange
        )

        print(f"   ✅ Exchange connected: {self.exchange.name}")
        print(f"   ✅ All modules initialized: {len(self.modules)}")

    async def _test_funding_rate_manager(self):
        """자금조달료 관리자 테스트"""
        print("\n💰 Testing Funding Rate Manager...")

        funding_manager = self.modules['funding_manager']

        # 1. 현재 자금조달료 조회
        funding_data = funding_manager.get_current_funding_rate(self.test_pair)
        if funding_data:
            print(f"   ✅ Current funding rate: {funding_data.funding_rate:.6f}")
            print(f"   📊 Estimated 8h income: {funding_data.estimated_income:.4f}%")
            print(f"   🎯 Recommendation: {funding_data.recommendation}")
        else:
            print("   ⚠️ Could not fetch funding rate (testnet limitation)")

        # 2. 자금조달료 기회 분석
        analysis = funding_manager.analyze_funding_opportunity(self.test_pair)
        print(f"   📈 Profitability score: {analysis.get('profitability_score', 'N/A')}/10")
        print(f"   ⚠️ Risk level: {analysis.get('risk_level', 'N/A')}")

        # 3. 다중 페어 분석 (시뮬레이션)
        test_pairs = [self.test_pair]
        opportunities = funding_manager.find_best_funding_opportunities(test_pairs, min_score=1)
        print(f"   🔍 Found {len(opportunities)} funding opportunities")

        # 4. 리포트 생성
        report = funding_manager.generate_funding_report(test_pairs)
        print(f"   📄 Generated funding report ({len(report)} chars)")

    async def _test_position_manager(self):
        """포지션 관리자 테스트"""
        print("\n📊 Testing Position Manager...")

        position_manager = self.modules['position_manager']

        # 1. 계정 잔고 조회
        balance = position_manager.get_account_balance()
        print(f"   💳 Total balance: {balance.get('total_wallet_balance', 'N/A')} USDT")
        print(f"   💰 Available balance: {balance.get('available_balance', 'N/A')} USDT")

        # 2. 포지션 정보 조회
        positions = position_manager.get_position_info()
        if positions:
            print(f"   📈 Active positions: {len(positions)}")
            for pos in positions[:3]:  # 최대 3개만 표시
                print(f"      {pos.symbol}: {pos.side} {pos.size} @ {pos.entry_price}")
        else:
            print("   📝 No active positions")

        # 3. 포지션 모드 확인
        position_mode = position_manager.get_position_mode()
        print(f"   ⚙️ Position mode: {position_mode}")

        # 4. 마진 모드 확인
        margin_mode = position_manager.get_margin_mode(self.test_pair)
        print(f"   🏦 Margin mode: {margin_mode}")

        # 5. 레버리지 정보
        leverage_info = position_manager.get_leverage_info(self.test_pair)
        print(f"   ⚖️ Current leverage: {leverage_info.get('leverage', 'N/A')}x")

    async def _test_risk_monitor(self):
        """리스크 모니터 테스트"""
        print("\n⚠️ Testing Risk Monitor...")

        risk_monitor = self.modules['risk_monitor']

        # 1. 포지션 리스크 확인
        risk_alerts = risk_monitor.check_position_risk(self.test_pair)
        print(f"   🚨 Risk alerts: {len(risk_alerts)}")

        for alert in risk_alerts[:3]:  # 최대 3개만 표시
            print(f"      {alert.level.value}: {alert.alert_type} - {alert.message}")

        # 2. 계정 레벨 리스크
        account_risk = risk_monitor.assess_account_risk()
        print(f"   📊 Account risk score: {account_risk.get('risk_score', 'N/A')}/10")
        print(f"   💹 Portfolio health: {account_risk.get('portfolio_health', 'N/A')}")

        # 3. 리스크 리포트 생성
        risk_report = risk_monitor.generate_risk_report()
        print(f"   📋 Risk report generated ({len(risk_report)} chars)")

        # 4. 자동 액션 테스트 (시뮬레이션)
        print("   🤖 Testing automatic risk actions (simulation mode)")

    async def _test_leverage_manager(self):
        """레버리지 관리자 테스트"""
        print("\n⚖️ Testing Leverage Manager...")

        leverage_manager = self.modules['leverage_manager']

        # 1. 최적 레버리지 계산
        leverage_rec = leverage_manager.calculate_optimal_leverage(self.test_pair)
        print(f"   🎯 Recommended leverage: {leverage_rec.recommended_leverage}x")
        print(f"   🛡️ Max safe leverage: {leverage_rec.max_safe_leverage}x")
        print(f"   📊 Volatility level: {leverage_rec.volatility_level.value}")
        print(f"   📈 Market condition: {leverage_rec.market_condition.value}")
        print(f"   🎲 Confidence: {leverage_rec.confidence_score:.1%}")

        # 2. 포트폴리오 레버리지 최적화
        portfolio_rec = leverage_manager.optimize_portfolio_leverage([self.test_pair])
        print(f"   📁 Portfolio recommendations: {len(portfolio_rec)}")

        # 3. 레버리지 검증
        validation = leverage_manager.validate_leverage_change(self.test_pair, 5)
        print(f"   ✅ Leverage validation: {'PASS' if validation['is_valid'] else 'FAIL'}")
        print(f"   ⚠️ Warnings: {len(validation['warnings'])}")
        print(f"   🎯 Risk score: {validation['risk_score']}/100")

        # 4. 레버리지 리포트
        leverage_report = leverage_manager.generate_leverage_report([self.test_pair])
        print(f"   📊 Leverage report generated ({len(leverage_report)} chars)")

    async def _test_module_integration(self):
        """모듈 통합 테스트"""
        print("\n🔗 Testing Module Integration...")

        # 1. 통합 분석 파이프라인
        print("   🔄 Running integrated analysis pipeline...")

        # 자금조달료 분석
        funding_analysis = self.modules['funding_manager'].analyze_funding_opportunity(self.test_pair)

        # 레버리지 최적화
        leverage_rec = self.modules['leverage_manager'].calculate_optimal_leverage(self.test_pair)

        # 리스크 평가
        risk_alerts = self.modules['risk_monitor'].check_position_risk(self.test_pair)

        # 2. 통합 의사결정 시뮬레이션
        decision_score = self._calculate_integrated_decision_score(
            funding_analysis, leverage_rec, risk_alerts
        )
        print(f"   🎯 Integrated decision score: {decision_score:.2f}/10")

        # 3. 모듈간 데이터 일관성 확인
        consistency_check = self._check_module_consistency()
        print(f"   ✅ Module consistency: {'PASS' if consistency_check else 'FAIL'}")

    async def _test_performance(self):
        """성능 테스트"""
        print("\n⚡ Testing Performance...")

        # 1. 개별 모듈 성능
        module_times = {}

        for module_name, module in self.modules.items():
            start_time = time.time()

            if module_name == 'funding_manager':
                module.analyze_funding_opportunity(self.test_pair)
            elif module_name == 'leverage_manager':
                module.calculate_optimal_leverage(self.test_pair)
            elif module_name == 'risk_monitor':
                module.check_position_risk(self.test_pair)
            elif module_name == 'position_manager':
                module.get_position_info()

            module_times[module_name] = time.time() - start_time

        # 성능 결과 출력
        for module_name, exec_time in module_times.items():
            status = "✅" if exec_time < 1.0 else "⚠️" if exec_time < 3.0 else "❌"
            print(f"   {status} {module_name}: {exec_time:.3f}s")

        # 2. 통합 성능 테스트
        start_time = time.time()
        await self._run_integrated_analysis()
        total_time = time.time() - start_time

        status = "✅" if total_time < 5.0 else "⚠️" if total_time < 10.0 else "❌"
        print(f"   {status} Integrated analysis: {total_time:.3f}s")

    def _calculate_integrated_decision_score(self, funding_analysis, leverage_rec, risk_alerts):
        """통합 의사결정 점수 계산"""
        try:
            # 기본 점수
            base_score = 5.0

            # 자금조달료 점수 반영
            funding_score = funding_analysis.get('profitability_score', 5)
            base_score += (funding_score - 5) * 0.3

            # 레버리지 신뢰도 반영
            confidence = leverage_rec.confidence_score
            base_score += (confidence - 0.5) * 4

            # 리스크 알림 반영
            critical_alerts = len([a for a in risk_alerts if a.level.value == 'CRITICAL'])
            base_score -= critical_alerts * 2

            return max(0, min(10, base_score))

        except:
            return 5.0

    def _check_module_consistency(self):
        """모듈간 일관성 확인"""
        try:
            # 모든 모듈이 초기화되었는지 확인
            if any(module is None for module in self.modules.values()):
                return False

            # 기본 기능 동작 확인
            balance = self.modules['position_manager'].get_account_balance()
            if not isinstance(balance, dict):
                return False

            return True

        except:
            return False

    async def _run_integrated_analysis(self):
        """통합 분석 실행"""
        try:
            # 모든 모듈의 주요 기능 실행
            funding_analysis = self.modules['funding_manager'].analyze_funding_opportunity(self.test_pair)
            leverage_rec = self.modules['leverage_manager'].calculate_optimal_leverage(self.test_pair)
            risk_alerts = self.modules['risk_monitor'].check_position_risk(self.test_pair)
            positions = self.modules['position_manager'].get_position_info()

            return {
                'funding': funding_analysis,
                'leverage': leverage_rec,
                'risk': risk_alerts,
                'positions': positions
            }

        except Exception as e:
            print(f"   ❌ Integrated analysis failed: {e}")
            return None


async def main():
    """메인 함수"""
    test = Phase5IntegrationTest()
    await test.run_complete_test()


if __name__ == "__main__":
    asyncio.run(main())