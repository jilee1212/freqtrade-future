#!/usr/bin/env python3
"""
Telegram Notification System
============================

Phase 7 텔레그램 알림 시스템
- 거래 실행 알림
- 리스크 경고 메시지
- 일일/주간 성과 리포트
- 봇 상태 변경 알림
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os
import sys
from telegram import Bot
from telegram.error import TelegramError
import requests
from dataclasses import dataclass

# 프로젝트 루트 디렉토리 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'user_data', 'strategies', 'modules'))

logger = logging.getLogger(__name__)

@dataclass
class TelegramConfig:
    """텔레그램 설정"""
    bot_token: str
    chat_id: str
    enabled: bool = True
    trade_notifications: bool = True
    risk_notifications: bool = True
    performance_reports: bool = True

class TelegramNotifier:
    """텔레그램 알림 시스템"""

    def __init__(self, config: TelegramConfig):
        self.config = config
        self.bot = Bot(token=config.bot_token) if config.bot_token else None
        self.last_notification_time = {}
        self.notification_cooldown = 300  # 5분 쿨다운

    async def send_message(self, message: str, parse_mode: str = 'HTML') -> bool:
        """메시지 전송"""
        if not self.config.enabled or not self.bot:
            return False

        try:
            await self.bot.send_message(
                chat_id=self.config.chat_id,
                text=message,
                parse_mode=parse_mode
            )
            return True
        except TelegramError as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    async def send_trade_notification(self, trade_data: Dict) -> bool:
        """거래 알림 전송"""
        if not self.config.trade_notifications:
            return False

        # 쿨다운 확인
        if not self._check_cooldown('trade'):
            return False

        try:
            side = trade_data.get('side', 'UNKNOWN').upper()
            pair = trade_data.get('pair', 'UNKNOWN')
            profit = trade_data.get('profit_abs', 0)
            profit_percent = trade_data.get('profit_ratio', 0) * 100
            leverage = trade_data.get('leverage', 1)

            # 이모지 설정
            side_emoji = "🟢" if side == "LONG" else "🔴"
            profit_emoji = "📈" if profit > 0 else "📉" if profit < 0 else "➖"

            message = f"""
{side_emoji} <b>TRADE EXECUTED</b>

<b>Pair:</b> {pair}
<b>Side:</b> {side}
<b>Leverage:</b> {leverage}x

{profit_emoji} <b>P&L:</b> ${profit:.2f} ({profit_percent:+.2f}%)

<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

            await self.send_message(message)
            self._update_cooldown('trade')
            return True

        except Exception as e:
            logger.error(f"Failed to send trade notification: {e}")
            return False

    async def send_risk_alert(self, alert_data: Dict) -> bool:
        """리스크 알림 전송"""
        if not self.config.risk_notifications:
            return False

        try:
            level = alert_data.get('level', 'INFO')
            message_text = alert_data.get('message', 'Risk alert')
            metric = alert_data.get('metric', 'Unknown')
            current_value = alert_data.get('current_value', 0)

            # 레벨별 이모지
            level_emoji = {
                'INFO': '🔵',
                'WARNING': '🟡',
                'CRITICAL': '🔴',
                'EMERGENCY': '🚨'
            }.get(level, '⚠️')

            message = f"""
{level_emoji} <b>RISK ALERT - {level}</b>

<b>Metric:</b> {metric}
<b>Current Value:</b> {current_value}

<b>Message:</b> {message_text}

<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

            await self.send_message(message)
            return True

        except Exception as e:
            logger.error(f"Failed to send risk alert: {e}")
            return False

    async def send_daily_report(self, performance_data: Dict) -> bool:
        """일일 성과 리포트 전송"""
        if not self.config.performance_reports:
            return False

        try:
            total_trades = performance_data.get('total_trades', 0)
            total_profit = performance_data.get('total_profit', 0)
            win_rate = performance_data.get('win_rate', 0)
            current_balance = performance_data.get('current_balance', 0)
            max_drawdown = performance_data.get('max_drawdown', 0)

            profit_emoji = "📈" if total_profit > 0 else "📉" if total_profit < 0 else "➖"

            message = f"""
📊 <b>DAILY PERFORMANCE REPORT</b>

💰 <b>Current Balance:</b> ${current_balance:,.2f}
{profit_emoji} <b>Daily P&L:</b> ${total_profit:+.2f}

📋 <b>Trading Statistics:</b>
• Total Trades: {total_trades}
• Win Rate: {win_rate:.1f}%
• Max Drawdown: {max_drawdown:.2f}%

📅 <b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}
"""

            await self.send_message(message)
            return True

        except Exception as e:
            logger.error(f"Failed to send daily report: {e}")
            return False

    async def send_bot_status_change(self, old_status: str, new_status: str) -> bool:
        """봇 상태 변경 알림"""
        try:
            status_emoji = {
                'running': '🟢',
                'stopped': '🔴',
                'stopping': '🟡',
                'starting': '🟡'
            }

            old_emoji = status_emoji.get(old_status.lower(), '⚪')
            new_emoji = status_emoji.get(new_status.lower(), '⚪')

            message = f"""
🤖 <b>BOT STATUS CHANGE</b>

{old_emoji} <b>Previous:</b> {old_status.upper()}
{new_emoji} <b>Current:</b> {new_status.upper()}

<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

            await self.send_message(message)
            return True

        except Exception as e:
            logger.error(f"Failed to send status change notification: {e}")
            return False

    async def send_weekly_report(self, performance_data: Dict) -> bool:
        """주간 성과 리포트 전송"""
        if not self.config.performance_reports:
            return False

        try:
            weekly_trades = performance_data.get('weekly_trades', 0)
            weekly_profit = performance_data.get('weekly_profit', 0)
            weekly_win_rate = performance_data.get('weekly_win_rate', 0)
            best_trade = performance_data.get('best_trade', 0)
            worst_trade = performance_data.get('worst_trade', 0)
            total_volume = performance_data.get('total_volume', 0)

            profit_emoji = "📈" if weekly_profit > 0 else "📉" if weekly_profit < 0 else "➖"

            message = f"""
📊 <b>WEEKLY PERFORMANCE REPORT</b>

{profit_emoji} <b>Weekly P&L:</b> ${weekly_profit:+.2f}

📈 <b>Trading Statistics:</b>
• Total Trades: {weekly_trades}
• Win Rate: {weekly_win_rate:.1f}%
• Best Trade: ${best_trade:+.2f}
• Worst Trade: ${worst_trade:+.2f}
• Total Volume: ${total_volume:,.2f}

📅 <b>Week Ending:</b> {datetime.now().strftime('%Y-%m-%d')}
"""

            await self.send_message(message)
            return True

        except Exception as e:
            logger.error(f"Failed to send weekly report: {e}")
            return False

    async def send_emergency_alert(self, alert_message: str) -> bool:
        """긴급 알림 전송"""
        try:
            message = f"""
🚨 <b>EMERGENCY ALERT</b> 🚨

{alert_message}

<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

⚠️ <b>Immediate action may be required!</b>
"""

            await self.send_message(message)
            return True

        except Exception as e:
            logger.error(f"Failed to send emergency alert: {e}")
            return False

    def _check_cooldown(self, notification_type: str) -> bool:
        """쿨다운 확인"""
        last_time = self.last_notification_time.get(notification_type, 0)
        current_time = datetime.now().timestamp()

        return (current_time - last_time) >= self.notification_cooldown

    def _update_cooldown(self, notification_type: str):
        """쿨다운 업데이트"""
        self.last_notification_time[notification_type] = datetime.now().timestamp()

class TelegramService:
    """텔레그램 서비스 관리자"""

    def __init__(self, config_file: str = "telegram_config.json"):
        self.config_file = config_file
        self.notifier = None
        self.load_config()

    def load_config(self):
        """설정 로드"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                self.telegram_config = TelegramConfig(
                    bot_token=config_data.get('bot_token', ''),
                    chat_id=config_data.get('chat_id', ''),
                    enabled=config_data.get('enabled', False),
                    trade_notifications=config_data.get('trade_notifications', True),
                    risk_notifications=config_data.get('risk_notifications', True),
                    performance_reports=config_data.get('performance_reports', True)
                )
            else:
                # 기본 설정 생성
                self.telegram_config = TelegramConfig(
                    bot_token='YOUR_BOT_TOKEN_HERE',
                    chat_id='YOUR_CHAT_ID_HERE',
                    enabled=False
                )
                self.save_config()

            if self.telegram_config.enabled and self.telegram_config.bot_token:
                self.notifier = TelegramNotifier(self.telegram_config)

        except Exception as e:
            logger.error(f"Failed to load Telegram config: {e}")
            self.telegram_config = TelegramConfig(
                bot_token='',
                chat_id='',
                enabled=False
            )

    def save_config(self):
        """설정 저장"""
        try:
            config_data = {
                'bot_token': self.telegram_config.bot_token,
                'chat_id': self.telegram_config.chat_id,
                'enabled': self.telegram_config.enabled,
                'trade_notifications': self.telegram_config.trade_notifications,
                'risk_notifications': self.telegram_config.risk_notifications,
                'performance_reports': self.telegram_config.performance_reports
            }

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save Telegram config: {e}")

    async def notify_trade(self, trade_data: Dict) -> bool:
        """거래 알림"""
        if self.notifier:
            return await self.notifier.send_trade_notification(trade_data)
        return False

    async def notify_risk(self, alert_data: Dict) -> bool:
        """리스크 알림"""
        if self.notifier:
            return await self.notifier.send_risk_alert(alert_data)
        return False

    async def send_daily_report(self, performance_data: Dict) -> bool:
        """일일 리포트"""
        if self.notifier:
            return await self.notifier.send_daily_report(performance_data)
        return False

    async def send_status_change(self, old_status: str, new_status: str) -> bool:
        """상태 변경 알림"""
        if self.notifier:
            return await self.notifier.send_bot_status_change(old_status, new_status)
        return False

    async def test_connection(self) -> bool:
        """연결 테스트"""
        if self.notifier:
            test_message = f"""
🤖 <b>TELEGRAM CONNECTION TEST</b>

✅ Connection successful!

<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            return await self.notifier.send_message(test_message)
        return False

# 싱글톤 인스턴스
telegram_service = TelegramService()

async def main():
    """메인 함수 - 테스트용"""
    print("Telegram Notification System Test")
    print("=" * 50)

    # 설정 확인
    if not telegram_service.telegram_config.enabled:
        print("❌ Telegram notifications are disabled")
        print("📝 Please edit telegram_config.json to enable notifications")
        return

    # 연결 테스트
    print("🔗 Testing Telegram connection...")
    success = await telegram_service.test_connection()

    if success:
        print("✅ Telegram connection successful!")

        # 테스트 알림들
        test_trade = {
            'side': 'short',
            'pair': 'BTC/USDT:USDT',
            'profit_abs': -45.23,
            'profit_ratio': -0.045,
            'leverage': 5
        }

        test_risk = {
            'level': 'WARNING',
            'message': 'Portfolio risk above normal threshold',
            'metric': 'portfolio_risk',
            'current_value': '7.5%'
        }

        print("📤 Sending test notifications...")
        await telegram_service.notify_trade(test_trade)
        await telegram_service.notify_risk(test_risk)

        print("✅ Test notifications sent!")

    else:
        print("❌ Telegram connection failed!")
        print("🔧 Please check your bot token and chat ID")

if __name__ == "__main__":
    asyncio.run(main())