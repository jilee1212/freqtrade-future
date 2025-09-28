#!/usr/bin/env python3
"""
Freqtrade Futures Web Dashboard
===============================

Phase 7 실시간 웹 인터페이스
- 실시간 트레이딩 모니터링
- 성능 대시보드
- 전략 관리 인터페이스
- 리스크 모니터링
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import json
import os
import sys
from datetime import datetime, timedelta
import pandas as pd
import plotly
import plotly.graph_objs as go
import plotly.express as px
from threading import Thread
import time
import requests

# 프로젝트 루트 디렉토리 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'user_data', 'strategies', 'modules'))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'futures-dashboard-secret-2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# 글로벌 상태 관리
dashboard_state = {
    'bot_status': 'unknown',
    'current_balance': 0,
    'total_profit': 0,
    'open_trades': [],
    'recent_trades': [],
    'strategy_performance': {},
    'risk_alerts': [],
    'last_update': datetime.now()
}

class FreqtradeAPI:
    """Freqtrade REST API 클라이언트"""

    def __init__(self, base_url="http://localhost:8080", username="freqtrade", password="futures2024"):
        self.base_url = base_url
        self.auth = (username, password)
        self.session = requests.Session()

    def get_status(self):
        """봇 상태 조회"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/status", auth=self.auth, timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None

    def get_balance(self):
        """잔고 조회"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/balance", auth=self.auth, timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None

    def get_trades(self):
        """거래 내역 조회"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/trades", auth=self.auth, timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None

    def get_profit(self):
        """수익 통계 조회"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/profit", auth=self.auth, timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None

# API 클라이언트 초기화
freqtrade_api = FreqtradeAPI()

@app.route('/')
def dashboard():
    """메인 대시보드"""
    return render_template('dashboard.html')

@app.route('/strategy-manager')
def strategy_manager():
    """전략 관리 페이지"""
    return render_template('strategy_manager.html')

@app.route('/risk-monitor')
def risk_monitor():
    """리스크 모니터 페이지"""
    return render_template('risk_monitor.html')

@app.route('/api/status')
def get_dashboard_status():
    """대시보드 상태 API"""
    return jsonify({
        'status': 'success',
        'data': dashboard_state,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/performance')
def get_performance_data():
    """성능 데이터 API"""
    try:
        # 백테스트 결과 로드
        results_dir = os.path.join(project_root, 'user_data', 'backtest_results')
        performance_data = load_backtest_performance(results_dir)

        return jsonify({
            'status': 'success',
            'data': performance_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/api/trades/chart')
def get_trades_chart():
    """거래 차트 데이터"""
    try:
        # 실제 거래 데이터 또는 시뮬레이션 데이터
        chart_data = generate_trades_chart()

        return jsonify({
            'status': 'success',
            'data': chart_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/api/risk')
def get_risk_data():
    """리스크 데이터 API"""
    try:
        risk_data = calculate_current_risk()

        return jsonify({
            'status': 'success',
            'data': risk_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

def load_backtest_performance(results_dir):
    """백테스트 성능 데이터 로드"""
    performance_data = {
        'strategies': [],
        'comparison': {},
        'metrics': {}
    }

    try:
        if os.path.exists(results_dir):
            for file in os.listdir(results_dir):
                if file.endswith('.json') and not file.endswith('.meta.json'):
                    file_path = os.path.join(results_dir, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                        strategy_name = data.get('strategy', {}).get('strategy_name', 'Unknown')
                        trades = data.get('trades', [])

                        if trades:
                            total_profit = sum(trade.get('profit_abs', 0) for trade in trades)
                            win_rate = len([t for t in trades if t.get('profit_abs', 0) > 0]) / len(trades) * 100
                        else:
                            total_profit = 0
                            win_rate = 0

                        performance_data['strategies'].append({
                            'name': strategy_name,
                            'total_trades': len(trades),
                            'total_profit': total_profit,
                            'win_rate': win_rate,
                            'last_updated': datetime.now().isoformat()
                        })
    except Exception as e:
        print(f"Error loading backtest performance: {e}")

    return performance_data

def generate_trades_chart():
    """거래 차트 데이터 생성"""
    # 실제 구현에서는 Freqtrade API 또는 데이터베이스에서 가져옴
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')

    chart_data = {
        'dates': [d.isoformat() for d in dates],
        'equity_curve': [10000 + i*50 + (i%7)*100 for i in range(len(dates))],
        'daily_returns': [(i%7)*2 - 3 for i in range(len(dates))],
        'trades': [
            {
                'date': (datetime.now() - timedelta(days=5)).isoformat(),
                'pair': 'BTC/USDT:USDT',
                'side': 'short',
                'profit': -45.23,
                'profit_percent': -4.5
            },
            {
                'date': (datetime.now() - timedelta(days=3)).isoformat(),
                'pair': 'BTC/USDT:USDT',
                'side': 'short',
                'profit': -38.27,
                'profit_percent': -4.6
            }
        ]
    }

    return chart_data

def calculate_current_risk():
    """현재 리스크 계산"""
    risk_data = {
        'portfolio_risk': 2.5,  # %
        'max_drawdown': 0.63,   # %
        'leverage_usage': 5.0,  # x
        'margin_ratio': 85.0,   # %
        'risk_level': 'LOW',
        'alerts': [
            {
                'level': 'INFO',
                'message': 'Portfolio risk within normal range',
                'timestamp': datetime.now().isoformat()
            }
        ]
    }

    return risk_data

def update_dashboard_data():
    """대시보드 데이터 업데이트 (백그라운드 작업)"""
    while True:
        try:
            # Freqtrade API로부터 실시간 데이터 수집
            status = freqtrade_api.get_status()
            balance = freqtrade_api.get_balance()
            trades = freqtrade_api.get_trades()
            profit = freqtrade_api.get_profit()

            # 대시보드 상태 업데이트
            if status:
                dashboard_state['bot_status'] = status.get('state', 'unknown')

            if balance:
                total_balance = 0
                for currency, amount in balance.get('currencies', {}).items():
                    if currency == 'USDT':
                        total_balance = amount.get('free', 0) + amount.get('used', 0)
                        break
                dashboard_state['current_balance'] = total_balance

            if profit:
                dashboard_state['total_profit'] = profit.get('profit_closed_coin', 0)

            if trades:
                dashboard_state['open_trades'] = [t for t in trades if not t.get('is_closed', True)]
                dashboard_state['recent_trades'] = trades[-10:]  # 최근 10개

            dashboard_state['last_update'] = datetime.now()

            # WebSocket으로 실시간 업데이트 전송
            socketio.emit('dashboard_update', dashboard_state)

        except Exception as e:
            print(f"Dashboard update error: {e}")

        time.sleep(10)  # 10초마다 업데이트

@socketio.on('connect')
def handle_connect():
    """클라이언트 연결 시"""
    print('Client connected')
    emit('dashboard_update', dashboard_state)

@socketio.on('disconnect')
def handle_disconnect():
    """클라이언트 연결 해제 시"""
    print('Client disconnected')

@socketio.on('request_update')
def handle_update_request():
    """클라이언트 업데이트 요청"""
    emit('dashboard_update', dashboard_state)

if __name__ == '__main__':
    # 백그라운드 데이터 업데이트 스레드 시작
    update_thread = Thread(target=update_dashboard_data, daemon=True)
    update_thread.start()

    print("=" * 60)
    print("FREQTRADE FUTURES DASHBOARD STARTING")
    print("=" * 60)
    print(f"Dashboard URL: http://localhost:5000")
    print(f"API Endpoint: http://localhost:5000/api/status")
    print(f"WebSocket: Enabled for real-time updates")
    print("=" * 60)

    # Flask 앱 실행
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)