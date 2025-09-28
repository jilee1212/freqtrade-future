#!/usr/bin/env python3
"""
Risk Monitor
===========

실시간 리스크 모니터링 및 강제 청산 방지 시스템
- 마진 비율 실시간 감시
- 청산가 접근 알림
- 자동 리스크 완화 조치
- ADL(Auto-Deleveraging) 방지
"""

import time
import threading
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import logging
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """알림 레벨"""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"

class RiskMetric(Enum):
    """리스크 지표"""
    MARGIN_RATIO = "margin_ratio"
    LIQUIDATION_DISTANCE = "liquidation_distance"
    UNREALIZED_PNL = "unrealized_pnl"
    PORTFOLIO_VAR = "portfolio_var"
    ADL_RISK = "adl_risk"

@dataclass
class RiskAlert:
    """리스크 알림"""
    timestamp: datetime
    alert_level: AlertLevel
    metric: RiskMetric
    symbol: str
    current_value: float
    threshold: float
    message: str
    suggested_action: str
    priority: int  # 1-10 (10이 최고 우선순위)

class RiskMonitor:
    """실시간 리스크 모니터링"""

    def __init__(self, position_manager, funding_manager=None, telegram_bot=None):
        self.position_manager = position_manager
        self.funding_manager = funding_manager
        self.telegram_bot = telegram_bot

        self.monitoring = False
        self.alert_history = []
        self.notification_handlers = []

        # 리스크 임계값 설정
        self.thresholds = {
            'margin_ratio': {
                'warning': 0.6,     # 60% 마진 사용
                'critical': 0.8,    # 80% 마진 사용
                'emergency': 0.9    # 90% 마진 사용
            },
            'liquidation_distance': {
                'warning': 0.2,     # 20% 거리
                'critical': 0.1,    # 10% 거리
                'emergency': 0.05   # 5% 거리
            },
            'unrealized_pnl': {
                'warning': -0.1,    # -10% 손실
                'critical': -0.2,   # -20% 손실
                'emergency': -0.3   # -30% 손실
            }
        }

        # 자동 대응 설정
        self.auto_actions = {
            'reduce_position_on_critical': True,
            'close_position_on_emergency': True,
            'send_telegram_alerts': True,
            'log_all_alerts': True
        }

    def start_monitoring(self, interval: int = 30) -> bool:
        """리스크 모니터링 시작"""
        try:
            if self.monitoring:
                logger.warning("Risk monitoring is already running")
                return False

            self.monitoring = True

            # 모니터링 스레드 시작
            monitor_thread = threading.Thread(
                target=self._monitor_loop,
                args=(interval,),
                daemon=True
            )
            monitor_thread.start()

            logger.info(f"🔍 Risk monitoring started (interval: {interval}s)")
            return True

        except Exception as e:
            logger.error(f"Failed to start risk monitoring: {e}")
            return False

    def stop_monitoring(self):
        """리스크 모니터링 중지"""
        self.monitoring = False
        logger.info("⏹️  Risk monitoring stopped")

    def _monitor_loop(self, interval: int):
        """모니터링 메인 루프"""
        while self.monitoring:
            try:
                self._check_all_risks()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(60)  # 에러 시 1분 대기

    def _check_all_risks(self):
        """모든 리스크 확인"""

        # 활성 포지션 조회
        positions = self.position_manager.get_position_info()
        if not positions:
            return

        # 각 포지션별 리스크 확인
        for position in positions:
            self._check_position_risks(position)

        # 포트폴리오 전체 리스크 확인
        self._check_portfolio_risks(positions)

    def _check_position_risks(self, position):
        """개별 포지션 리스크 확인"""

        symbol = position.symbol

        # 1. 마진 비율 확인
        self._check_margin_ratio(position)

        # 2. 청산가 거리 확인
        self._check_liquidation_distance(position)

        # 3. 미실현 손익 확인
        self._check_unrealized_pnl(position)

        # 4. ADL 위험도 확인
        self._check_adl_risk(position)

    def _check_margin_ratio(self, position):
        """마진 비율 확인"""

        margin_ratio = position.margin_ratio
        symbol = position.symbol

        if margin_ratio >= self.thresholds['margin_ratio']['emergency']:
            alert = RiskAlert(
                timestamp=datetime.now(),
                alert_level=AlertLevel.EMERGENCY,
                metric=RiskMetric.MARGIN_RATIO,
                symbol=symbol,
                current_value=margin_ratio,
                threshold=self.thresholds['margin_ratio']['emergency'],
                message=f"🚨 EMERGENCY: {symbol} margin ratio extremely high: {margin_ratio:.1%}",
                suggested_action="IMMEDIATE_POSITION_REDUCTION_OR_CLOSE",
                priority=10
            )
            self._handle_alert(alert)

        elif margin_ratio >= self.thresholds['margin_ratio']['critical']:
            alert = RiskAlert(
                timestamp=datetime.now(),
                alert_level=AlertLevel.CRITICAL,
                metric=RiskMetric.MARGIN_RATIO,
                symbol=symbol,
                current_value=margin_ratio,
                threshold=self.thresholds['margin_ratio']['critical'],
                message=f"⚠️ CRITICAL: {symbol} margin ratio high: {margin_ratio:.1%}",
                suggested_action="REDUCE_LEVERAGE_OR_POSITION_SIZE",
                priority=8
            )
            self._handle_alert(alert)

        elif margin_ratio >= self.thresholds['margin_ratio']['warning']:
            alert = RiskAlert(
                timestamp=datetime.now(),
                alert_level=AlertLevel.WARNING,
                metric=RiskMetric.MARGIN_RATIO,
                symbol=symbol,
                current_value=margin_ratio,
                threshold=self.thresholds['margin_ratio']['warning'],
                message=f"⚠️ WARNING: {symbol} margin ratio elevated: {margin_ratio:.1%}",
                suggested_action="MONITOR_CLOSELY",
                priority=5
            )
            self._handle_alert(alert)

    def _check_liquidation_distance(self, position):
        """청산가 거리 확인"""

        if position.liquidation_price <= 0:
            return

        mark_price = position.mark_price
        liquidation_price = position.liquidation_price
        distance = abs(mark_price - liquidation_price) / mark_price
        symbol = position.symbol

        if distance <= self.thresholds['liquidation_distance']['emergency']:
            alert = RiskAlert(
                timestamp=datetime.now(),
                alert_level=AlertLevel.EMERGENCY,
                metric=RiskMetric.LIQUIDATION_DISTANCE,
                symbol=symbol,
                current_value=distance,
                threshold=self.thresholds['liquidation_distance']['emergency'],
                message=f"🚨 LIQUIDATION IMMINENT: {symbol} only {distance:.1%} from liquidation",
                suggested_action="EMERGENCY_CLOSE_POSITION",
                priority=10
            )
            self._handle_alert(alert)

        elif distance <= self.thresholds['liquidation_distance']['critical']:
            alert = RiskAlert(
                timestamp=datetime.now(),
                alert_level=AlertLevel.CRITICAL,
                metric=RiskMetric.LIQUIDATION_DISTANCE,
                symbol=symbol,
                current_value=distance,
                threshold=self.thresholds['liquidation_distance']['critical'],
                message=f"⚠️ LIQUIDATION RISK: {symbol} {distance:.1%} from liquidation",
                suggested_action="REDUCE_POSITION_IMMEDIATELY",
                priority=9
            )
            self._handle_alert(alert)

    def _check_unrealized_pnl(self, position):
        """미실현 손익 확인"""

        pnl_percent = position.percentage / 100
        symbol = position.symbol

        if pnl_percent <= self.thresholds['unrealized_pnl']['emergency']:
            alert = RiskAlert(
                timestamp=datetime.now(),
                alert_level=AlertLevel.EMERGENCY,
                metric=RiskMetric.UNREALIZED_PNL,
                symbol=symbol,
                current_value=pnl_percent,
                threshold=self.thresholds['unrealized_pnl']['emergency'],
                message=f"🚨 MAJOR LOSS: {symbol} unrealized loss: {pnl_percent:.1%}",
                suggested_action="CONSIDER_POSITION_CLOSE",
                priority=8
            )
            self._handle_alert(alert)

    def _check_adl_risk(self, position):
        """ADL (Auto-Deleveraging) 위험도 확인"""

        # ADL 위험도는 포지션 크기와 수익률에 따라 결정
        # 큰 포지션이면서 높은 수익률일 때 ADL 위험 증가

        position_size_usd = position.size * position.mark_price
        pnl_percent = position.percentage / 100

        # 큰 포지션 (>$50,000)이면서 높은 수익 (>20%)
        if position_size_usd > 50000 and pnl_percent > 0.2:
            alert = RiskAlert(
                timestamp=datetime.now(),
                alert_level=AlertLevel.WARNING,
                metric=RiskMetric.ADL_RISK,
                symbol=position.symbol,
                current_value=pnl_percent,
                threshold=0.2,
                message=f"📊 ADL RISK: {position.symbol} large profitable position may face ADL",
                suggested_action="CONSIDER_PARTIAL_PROFIT_TAKING",
                priority=6
            )
            self._handle_alert(alert)

    def _check_portfolio_risks(self, positions):
        """포트폴리오 전체 리스크 확인"""

        if not positions:
            return

        # 총 미실현 손익 계산
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in positions)

        # 계좌 정보 조회
        balance_info = self.position_manager.get_account_balance()
        total_balance = balance_info.get('total_wallet_balance', 0)

        if total_balance > 0:
            portfolio_pnl_percent = total_unrealized_pnl / total_balance

            # 포트폴리오 레벨 손실 확인
            if portfolio_pnl_percent <= -0.2:  # -20% 포트폴리오 손실
                alert = RiskAlert(
                    timestamp=datetime.now(),
                    alert_level=AlertLevel.CRITICAL,
                    metric=RiskMetric.PORTFOLIO_VAR,
                    symbol="PORTFOLIO",
                    current_value=portfolio_pnl_percent,
                    threshold=-0.2,
                    message=f"🚨 PORTFOLIO LOSS: {portfolio_pnl_percent:.1%} total unrealized loss",
                    suggested_action="REVIEW_ALL_POSITIONS",
                    priority=9
                )
                self._handle_alert(alert)

    def _handle_alert(self, alert: RiskAlert):
        """알림 처리"""

        # 중복 알림 방지 (같은 심볼, 같은 메트릭의 최근 5분 이내 알림)
        if self._is_duplicate_alert(alert):
            return

        # 알림 기록에 추가
        self.alert_history.append(alert)

        # 최근 100개 알림만 유지
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]

        # 로그 기록
        if self.auto_actions['log_all_alerts']:
            logger.warning(f"RISK ALERT: {alert.message}")

        # 텔레그램 알림
        if self.auto_actions['send_telegram_alerts'] and self.telegram_bot:
            self._send_telegram_alert(alert)

        # 자동 대응 조치
        self._execute_auto_actions(alert)

        # 커스텀 핸들러 실행
        for handler in self.notification_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")

    def _is_duplicate_alert(self, alert: RiskAlert, window_minutes: int = 5) -> bool:
        """중복 알림 확인"""

        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)

        for existing_alert in reversed(self.alert_history):
            if existing_alert.timestamp < cutoff_time:
                break

            if (existing_alert.symbol == alert.symbol and
                existing_alert.metric == alert.metric and
                existing_alert.alert_level == alert.alert_level):
                return True

        return False

    def _send_telegram_alert(self, alert: RiskAlert):
        """텔레그램 알림 발송"""

        try:
            # 알림 레벨에 따른 이모지
            level_emoji = {
                AlertLevel.INFO: "ℹ️",
                AlertLevel.WARNING: "⚠️",
                AlertLevel.CRITICAL: "🚨",
                AlertLevel.EMERGENCY: "🆘"
            }

            emoji = level_emoji.get(alert.alert_level, "📊")

            message = f"{emoji} RISK ALERT\n\n"
            message += f"Symbol: {alert.symbol}\n"
            message += f"Metric: {alert.metric.value}\n"
            message += f"Level: {alert.alert_level.value}\n"
            message += f"Current: {alert.current_value:.3f}\n"
            message += f"Threshold: {alert.threshold:.3f}\n\n"
            message += f"Message: {alert.message}\n"
            message += f"Action: {alert.suggested_action}\n"
            message += f"Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

            self.telegram_bot.send_message(message)

        except Exception as e:
            logger.error(f"Telegram alert failed: {e}")

    def _execute_auto_actions(self, alert: RiskAlert):
        """자동 대응 조치 실행"""

        if alert.alert_level == AlertLevel.EMERGENCY:

            # 긴급 상황 시 포지션 자동 감소 또는 청산
            if (self.auto_actions['close_position_on_emergency'] and
                alert.metric in [RiskMetric.MARGIN_RATIO, RiskMetric.LIQUIDATION_DISTANCE]):

                try:
                    if alert.metric == RiskMetric.LIQUIDATION_DISTANCE:
                        # 청산 위험 시 즉시 전체 청산
                        self.position_manager.close_position(alert.symbol, 100)
                        logger.warning(f"🚨 EMERGENCY AUTO-CLOSE: {alert.symbol} position closed")
                    else:
                        # 마진 위험 시 50% 감소
                        self.position_manager.close_position(alert.symbol, 50)
                        logger.warning(f"⚠️ EMERGENCY AUTO-REDUCE: {alert.symbol} position reduced by 50%")

                except Exception as e:
                    logger.error(f"Auto-action failed for {alert.symbol}: {e}")

        elif alert.alert_level == AlertLevel.CRITICAL:

            # 심각한 상황 시 포지션 부분 감소
            if (self.auto_actions['reduce_position_on_critical'] and
                alert.metric == RiskMetric.MARGIN_RATIO):

                try:
                    self.position_manager.close_position(alert.symbol, 25)
                    logger.warning(f"⚠️ AUTO-REDUCE: {alert.symbol} position reduced by 25%")
                except Exception as e:
                    logger.error(f"Auto-reduction failed for {alert.symbol}: {e}")

    def add_notification_handler(self, handler: Callable[[RiskAlert], None]):
        """커스텀 알림 핸들러 추가"""
        self.notification_handlers.append(handler)

    def get_risk_summary(self) -> Dict:
        """리스크 요약 정보"""

        positions = self.position_manager.get_position_info()
        if not positions:
            return {"status": "no_positions"}

        # 리스크 레벨별 포지션 분류
        risk_levels = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        total_unrealized_pnl = 0

        for position in positions:
            risk_levels[position.risk_level] += 1
            total_unrealized_pnl += position.unrealized_pnl

        # 최근 알림 통계
        recent_alerts = [a for a in self.alert_history
                        if a.timestamp > datetime.now() - timedelta(hours=24)]
        alert_counts = {}
        for level in AlertLevel:
            alert_counts[level.value] = len([a for a in recent_alerts
                                           if a.alert_level == level])

        return {
            'monitoring_active': self.monitoring,
            'total_positions': len(positions),
            'risk_distribution': risk_levels,
            'total_unrealized_pnl': total_unrealized_pnl,
            'recent_alerts_24h': alert_counts,
            'last_check': datetime.now().isoformat()
        }

    def generate_risk_report(self) -> str:
        """리스크 리포트 생성"""

        summary = self.get_risk_summary()

        report = "🛡️ RISK MONITORING REPORT\n"
        report += "=" * 50 + "\n\n"

        if summary.get('status') == 'no_positions':
            report += "✅ No active positions - No risk exposure\n"
            return report

        # 모니터링 상태
        status_emoji = "🟢" if summary['monitoring_active'] else "🔴"
        report += f"{status_emoji} Monitoring Status: {'ACTIVE' if summary['monitoring_active'] else 'INACTIVE'}\n\n"

        # 포지션 리스크 분포
        report += "📊 POSITION RISK DISTRIBUTION:\n"
        risk_dist = summary['risk_distribution']
        for level, count in risk_dist.items():
            if count > 0:
                emoji = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🟠", "CRITICAL": "🔴"}[level]
                report += f"   {emoji} {level}: {count} positions\n"

        # 총 미실현 손익
        pnl = summary['total_unrealized_pnl']
        pnl_emoji = "📈" if pnl >= 0 else "📉"
        report += f"\n{pnl_emoji} Total Unrealized PnL: ${pnl:.2f}\n\n"

        # 최근 알림 통계
        report += "🚨 RECENT ALERTS (24h):\n"
        alert_counts = summary['recent_alerts_24h']
        total_alerts = sum(alert_counts.values())

        if total_alerts == 0:
            report += "   ✅ No alerts in the last 24 hours\n"
        else:
            for level, count in alert_counts.items():
                if count > 0:
                    emoji = {"INFO": "ℹ️", "WARNING": "⚠️", "CRITICAL": "🚨", "EMERGENCY": "🆘"}[level]
                    report += f"   {emoji} {level}: {count} alerts\n"

        report += f"\n📅 Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

        return report