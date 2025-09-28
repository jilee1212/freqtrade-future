#!/usr/bin/env python3
"""
Real-time Risk Monitor
======================

Phase 7 실시간 리스크 모니터링 시스템
- 실시간 포지션 모니터링
- 자동 리스크 완화
- 알림 시스템 통합
- 성능 추적
"""

import asyncio
import logging
import time
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import requests
from threading import Thread
import pandas as pd

# 프로젝트 루트 디렉토리 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'user_data', 'strategies', 'modules'))

from telegram_notifier import telegram_service

logger = logging.getLogger(__name__)

@dataclass
class MonitoringState:
    """모니터링 상태"""
    is_running: bool = False
    last_check: Optional[datetime] = None
    total_checks: int = 0
    alerts_sent: int = 0
    errors_count: int = 0

@dataclass
class PortfolioStatus:
    """포트폴리오 상태"""
    total_balance: float = 0.0
    available_balance: float = 0.0
    used_balance: float = 0.0
    total_profit: float = 0.0
    daily_profit: float = 0.0
    open_positions: int = 0
    portfolio_risk: float = 0.0
    max_drawdown: float = 0.0
    leverage_usage: float = 1.0
    margin_ratio: float = 100.0

class RealTimeMonitor:
    """실시간 모니터링 시스템"""

    def __init__(self, config_file: str = "monitor_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.state = MonitoringState()
        self.portfolio_status = PortfolioStatus()
        self.api_client = FreqtradeAPIClient()
        self.alert_history = []
        self.performance_history = []

    def load_config(self) -> Dict:
        """설정 로드"""
        default_config = {
            "monitoring": {
                "enabled": True,
                "check_interval": 30,  # seconds
                "api_timeout": 10
            },
            "risk_thresholds": {
                "portfolio_risk_warning": 5.0,      # %
                "portfolio_risk_critical": 10.0,    # %
                "max_drawdown_warning": 2.0,        # %
                "max_drawdown_critical": 5.0,       # %
                "margin_ratio_warning": 20.0,       # %
                "margin_ratio_critical": 10.0,      # %
                "leverage_warning": 10.0,           # x
                "leverage_critical": 15.0           # x
            },
            "auto_actions": {
                "enabled": False,
                "reduce_positions_on_critical": True,
                "emergency_stop_on_extreme": True,
                "max_daily_loss": 1000.0            # USDT
            },
            "notifications": {
                "telegram_enabled": True,
                "email_enabled": False,
                "webhook_enabled": False
            },
            "api": {
                "base_url": "http://localhost:8080",
                "username": "freqtrade",
                "password": "futures2024"
            }
        }

        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 기본 설정과 병합
                    return {**default_config, **loaded_config}
            else:
                # 기본 설정 저장
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2)
                return default_config

        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return default_config

    async def start_monitoring(self):
        """모니터링 시작"""
        print("🚀 Starting Real-time Risk Monitor")
        print("=" * 60)

        self.state.is_running = True
        self.state.last_check = datetime.now()

        # 초기 상태 확인
        await self.check_system_health()

        print(f"✅ Monitoring started successfully")
        print(f"📊 Check interval: {self.config['monitoring']['check_interval']} seconds")
        print(f"🔔 Telegram notifications: {'enabled' if self.config['notifications']['telegram_enabled'] else 'disabled'}")
        print("=" * 60)

        # 메인 모니터링 루프
        while self.state.is_running:
            try:
                await self.run_monitoring_cycle()
                await asyncio.sleep(self.config['monitoring']['check_interval'])

            except KeyboardInterrupt:
                print("\n⏹️ Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Monitoring cycle error: {e}")
                self.state.errors_count += 1
                await asyncio.sleep(10)  # 에러 시 10초 대기

        self.state.is_running = False

    async def run_monitoring_cycle(self):
        """모니터링 사이클 실행"""
        try:
            self.state.total_checks += 1
            self.state.last_check = datetime.now()

            # 1. 포트폴리오 상태 업데이트
            await self.update_portfolio_status()

            # 2. 리스크 체크
            alerts = await self.check_risk_thresholds()

            # 3. 알림 전송
            if alerts:
                await self.send_alerts(alerts)

            # 4. 자동 액션 실행
            if self.config['auto_actions']['enabled']:
                await self.execute_auto_actions(alerts)

            # 5. 성능 기록
            await self.record_performance()

            # 6. 상태 출력 (매 10번째 체크마다)
            if self.state.total_checks % 10 == 0:
                self.print_status_summary()

        except Exception as e:
            logger.error(f"Monitoring cycle failed: {e}")
            self.state.errors_count += 1

    async def update_portfolio_status(self):
        """포트폴리오 상태 업데이트"""
        try:
            # API에서 데이터 수집
            balance_data = await self.api_client.get_balance()
            profit_data = await self.api_client.get_profit()
            trades_data = await self.api_client.get_trades()

            if balance_data:
                self.portfolio_status.total_balance = balance_data.get('total', 0)
                self.portfolio_status.available_balance = balance_data.get('free', 0)
                self.portfolio_status.used_balance = balance_data.get('used', 0)

            if profit_data:
                self.portfolio_status.total_profit = profit_data.get('profit_closed_coin', 0)
                self.portfolio_status.daily_profit = profit_data.get('profit_today_coin', 0)

            if trades_data:
                open_trades = [t for t in trades_data if not t.get('is_closed', True)]
                self.portfolio_status.open_positions = len(open_trades)

            # 리스크 메트릭 계산
            await self.calculate_risk_metrics()

        except Exception as e:
            logger.error(f"Failed to update portfolio status: {e}")

    async def calculate_risk_metrics(self):
        """리스크 메트릭 계산"""
        try:
            # 포트폴리오 리스크 계산
            if self.portfolio_status.total_balance > 0:
                risk_ratio = abs(self.portfolio_status.used_balance) / self.portfolio_status.total_balance
                self.portfolio_status.portfolio_risk = risk_ratio * 100

            # 최대 낙폭 계산 (단순화된 버전)
            if hasattr(self, 'balance_history') and len(self.balance_history) > 0:
                peak_balance = max(self.balance_history)
                current_balance = self.portfolio_status.total_balance
                if peak_balance > 0:
                    drawdown = (peak_balance - current_balance) / peak_balance * 100
                    self.portfolio_status.max_drawdown = max(self.portfolio_status.max_drawdown, drawdown)

            # 잔고 히스토리 업데이트
            if not hasattr(self, 'balance_history'):
                self.balance_history = []

            self.balance_history.append(self.portfolio_status.total_balance)
            if len(self.balance_history) > 1000:  # 최근 1000개만 유지
                self.balance_history = self.balance_history[-1000:]

        except Exception as e:
            logger.error(f"Failed to calculate risk metrics: {e}")

    async def check_risk_thresholds(self) -> List[Dict]:
        """리스크 임계값 체크"""
        alerts = []
        thresholds = self.config['risk_thresholds']

        # 포트폴리오 리스크 체크
        if self.portfolio_status.portfolio_risk >= thresholds['portfolio_risk_critical']:
            alerts.append({
                'level': 'CRITICAL',
                'type': 'portfolio_risk',
                'message': f'Portfolio risk critical: {self.portfolio_status.portfolio_risk:.2f}%',
                'current_value': self.portfolio_status.portfolio_risk,
                'threshold': thresholds['portfolio_risk_critical']
            })
        elif self.portfolio_status.portfolio_risk >= thresholds['portfolio_risk_warning']:
            alerts.append({
                'level': 'WARNING',
                'type': 'portfolio_risk',
                'message': f'Portfolio risk elevated: {self.portfolio_status.portfolio_risk:.2f}%',
                'current_value': self.portfolio_status.portfolio_risk,
                'threshold': thresholds['portfolio_risk_warning']
            })

        # 최대 낙폭 체크
        if self.portfolio_status.max_drawdown >= thresholds['max_drawdown_critical']:
            alerts.append({
                'level': 'CRITICAL',
                'type': 'max_drawdown',
                'message': f'Max drawdown critical: {self.portfolio_status.max_drawdown:.2f}%',
                'current_value': self.portfolio_status.max_drawdown,
                'threshold': thresholds['max_drawdown_critical']
            })
        elif self.portfolio_status.max_drawdown >= thresholds['max_drawdown_warning']:
            alerts.append({
                'level': 'WARNING',
                'type': 'max_drawdown',
                'message': f'Max drawdown elevated: {self.portfolio_status.max_drawdown:.2f}%',
                'current_value': self.portfolio_status.max_drawdown,
                'threshold': thresholds['max_drawdown_warning']
            })

        # 일일 손실 체크
        max_daily_loss = self.config['auto_actions']['max_daily_loss']
        if self.portfolio_status.daily_profit < -max_daily_loss:
            alerts.append({
                'level': 'EMERGENCY',
                'type': 'daily_loss',
                'message': f'Daily loss limit exceeded: ${self.portfolio_status.daily_profit:.2f}',
                'current_value': abs(self.portfolio_status.daily_profit),
                'threshold': max_daily_loss
            })

        return alerts

    async def send_alerts(self, alerts: List[Dict]):
        """알림 전송"""
        for alert in alerts:
            try:
                # 중복 알림 방지
                if not self.is_duplicate_alert(alert):
                    # 텔레그램 알림
                    if self.config['notifications']['telegram_enabled']:
                        await telegram_service.notify_risk(alert)

                    # 알림 히스토리 추가
                    alert['timestamp'] = datetime.now().isoformat()
                    self.alert_history.append(alert)
                    self.state.alerts_sent += 1

                    # 히스토리 크기 제한
                    if len(self.alert_history) > 100:
                        self.alert_history = self.alert_history[-100:]

            except Exception as e:
                logger.error(f"Failed to send alert: {e}")

    def is_duplicate_alert(self, alert: Dict) -> bool:
        """중복 알림 확인"""
        # 최근 10분 내 동일한 타입의 알림이 있는지 확인
        cutoff_time = datetime.now() - timedelta(minutes=10)

        for historical_alert in self.alert_history:
            alert_time = datetime.fromisoformat(historical_alert.get('timestamp', '1970-01-01'))
            if (alert_time > cutoff_time and
                historical_alert.get('type') == alert.get('type') and
                historical_alert.get('level') == alert.get('level')):
                return True

        return False

    async def execute_auto_actions(self, alerts: List[Dict]):
        """자동 액션 실행"""
        if not alerts:
            return

        critical_alerts = [a for a in alerts if a['level'] == 'CRITICAL']
        emergency_alerts = [a for a in alerts if a['level'] == 'EMERGENCY']

        # 긴급 상황 시 자동 정지
        if emergency_alerts and self.config['auto_actions']['emergency_stop_on_extreme']:
            await self.emergency_stop()

        # 중요 알림 시 포지션 감소
        elif critical_alerts and self.config['auto_actions']['reduce_positions_on_critical']:
            await self.reduce_positions()

    async def emergency_stop(self):
        """긴급 정지"""
        try:
            print("🚨 EMERGENCY STOP TRIGGERED")
            await telegram_service.notifier.send_emergency_alert(
                "Emergency stop triggered due to critical risk levels!"
            )

            # Freqtrade 봇 정지 시도
            await self.api_client.stop_bot()

        except Exception as e:
            logger.error(f"Emergency stop failed: {e}")

    async def reduce_positions(self):
        """포지션 감소"""
        try:
            print("⚠️ Reducing positions due to critical risk")
            # 구현 필요: 포지션 크기 감소 로직

        except Exception as e:
            logger.error(f"Position reduction failed: {e}")

    async def record_performance(self):
        """성능 기록"""
        try:
            performance_record = {
                'timestamp': datetime.now().isoformat(),
                'total_balance': self.portfolio_status.total_balance,
                'total_profit': self.portfolio_status.total_profit,
                'daily_profit': self.portfolio_status.daily_profit,
                'portfolio_risk': self.portfolio_status.portfolio_risk,
                'max_drawdown': self.portfolio_status.max_drawdown,
                'open_positions': self.portfolio_status.open_positions
            }

            self.performance_history.append(performance_record)

            # 히스토리 크기 제한
            if len(self.performance_history) > 1000:
                self.performance_history = self.performance_history[-1000:]

        except Exception as e:
            logger.error(f"Failed to record performance: {e}")

    async def check_system_health(self):
        """시스템 상태 확인"""
        try:
            # API 연결 테스트
            status = await self.api_client.get_status()
            if status:
                print(f"✅ Freqtrade API: Connected")
                print(f"📊 Bot Status: {status.get('state', 'Unknown')}")
            else:
                print("❌ Freqtrade API: Connection failed")

            # 텔레그램 연결 테스트
            if self.config['notifications']['telegram_enabled']:
                if telegram_service.telegram_config.enabled:
                    print("✅ Telegram: Configured")
                else:
                    print("⚠️ Telegram: Not configured")

        except Exception as e:
            logger.error(f"System health check failed: {e}")

    def print_status_summary(self):
        """상태 요약 출력"""
        print(f"\n📊 Status Summary ({datetime.now().strftime('%H:%M:%S')})")
        print(f"💰 Balance: ${self.portfolio_status.total_balance:,.2f}")
        print(f"📈 P&L: ${self.portfolio_status.total_profit:+,.2f}")
        print(f"📋 Positions: {self.portfolio_status.open_positions}")
        print(f"⚠️ Risk: {self.portfolio_status.portfolio_risk:.2f}%")
        print(f"📉 Drawdown: {self.portfolio_status.max_drawdown:.2f}%")
        print(f"🔔 Alerts: {self.state.alerts_sent}")
        print(f"✅ Checks: {self.state.total_checks}")

class FreqtradeAPIClient:
    """Freqtrade API 클라이언트 (단순화 버전)"""

    def __init__(self):
        self.base_url = "http://localhost:8080"
        self.auth = ("freqtrade", "futures2024")

    async def get_status(self) -> Optional[Dict]:
        """상태 조회"""
        try:
            # 실제 구현에서는 aiohttp 사용
            response = requests.get(f"{self.base_url}/api/v1/status", auth=self.auth, timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None

    async def get_balance(self) -> Optional[Dict]:
        """잔고 조회"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/balance", auth=self.auth, timeout=5)
            if response.status_code == 200:
                balance_data = response.json()
                usdt_balance = balance_data.get('currencies', {}).get('USDT', {})
                return {
                    'total': usdt_balance.get('free', 0) + usdt_balance.get('used', 0),
                    'free': usdt_balance.get('free', 0),
                    'used': usdt_balance.get('used', 0)
                }
        except:
            pass
        return None

    async def get_profit(self) -> Optional[Dict]:
        """수익 조회"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/profit", auth=self.auth, timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None

    async def get_trades(self) -> Optional[List]:
        """거래 내역 조회"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/trades", auth=self.auth, timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None

    async def stop_bot(self) -> bool:
        """봇 정지"""
        try:
            response = requests.post(f"{self.base_url}/api/v1/stop", auth=self.auth, timeout=5)
            return response.status_code == 200
        except:
            pass
        return False

async def main():
    """메인 함수"""
    monitor = RealTimeMonitor()
    await monitor.start_monitoring()

if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Real-time monitor stopped")