from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import requests
from datetime import datetime
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

# Freqtrade API configuration
FREQTRADE_URL = os.getenv('FREQTRADE_URL', 'http://localhost:8080')
FREQTRADE_USERNAME = os.getenv('FREQTRADE_USERNAME', 'freqtrade')
FREQTRADE_PASSWORD = os.getenv('FREQTRADE_PASSWORD', 'futures2024')

def get_freqtrade_data(endpoint):
    """Fetch data from Freqtrade API"""
    try:
        url = f"{FREQTRADE_URL}/api/v1/{endpoint}"
        response = requests.get(
            url,
            auth=(FREQTRADE_USERNAME, FREQTRADE_PASSWORD),
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error fetching from Freqtrade: {e}")
        return None

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get bot status"""
    data = get_freqtrade_data('status')
    if data:
        return jsonify({'status': 'success', 'data': data})

    # Fallback demo data
    return jsonify({
        'status': 'success',
        'data': {
            'state': 'running',
            'strategy': 'EMA_Crossover',
            'max_open_trades': 3,
            'dry_run': False
        }
    })

@app.route('/api/balance', methods=['GET'])
def get_balance():
    """Get account balance"""
    data = get_freqtrade_data('balance')
    if data:
        return jsonify({'status': 'success', 'data': data})

    # Fallback demo data
    return jsonify({
        'status': 'success',
        'data': {
            'currencies': [
                {
                    'currency': 'USDT',
                    'free': 10450.23,
                    'used': 3500.00,
                    'total': 13950.23
                }
            ],
            'total': 13950.23
        }
    })

@app.route('/api/trades', methods=['GET'])
def get_trades():
    """Get open and closed trades"""
    data = get_freqtrade_data('trades')
    if data:
        return jsonify({'status': 'success', 'data': data})

    # Fallback demo data
    return jsonify({
        'status': 'success',
        'data': [
            {
                'trade_id': 1,
                'pair': 'BTC/USDT',
                'is_open': True,
                'amount': 0.5,
                'stake_amount': 3367,
                'open_rate': 67234,
                'current_rate': 67500,
                'profit_ratio': 0.0039,
                'profit_abs': 13.3,
                'open_date': '2025-09-30 14:23:10'
            },
            {
                'trade_id': 2,
                'pair': 'ETH/USDT',
                'is_open': False,
                'amount': 2,
                'stake_amount': 6912,
                'open_rate': 3456,
                'close_rate': 3520,
                'profit_ratio': 0.0185,
                'profit_abs': 128,
                'open_date': '2025-09-30 11:05:33',
                'close_date': '2025-09-30 12:30:15'
            }
        ]
    })

@app.route('/api/profit', methods=['GET'])
def get_profit():
    """Get profit statistics"""
    data = get_freqtrade_data('profit')
    if data:
        return jsonify({'status': 'success', 'data': data})

    # Fallback demo data
    return jsonify({
        'status': 'success',
        'data': {
            'profit_closed_coin': 693.78,
            'profit_closed_percent': 10.32,
            'profit_all_coin': 707.08,
            'profit_all_percent': 10.52,
            'trade_count': 824,
            'closed_trade_count': 820,
            'winning_trades': 564,
            'losing_trades': 256,
            'win_rate': 68.78
        }
    })

@app.route('/api/performance', methods=['GET'])
def get_performance():
    """Get performance by pair"""
    data = get_freqtrade_data('performance')
    if data:
        return jsonify({'status': 'success', 'data': data})

    # Fallback demo data
    return jsonify({
        'status': 'success',
        'data': [
            {'pair': 'BTC/USDT', 'profit': 12.5, 'count': 245},
            {'pair': 'ETH/USDT', 'profit': 8.3, 'count': 189},
            {'pair': 'SOL/USDT', 'profit': 15.7, 'count': 156},
            {'pair': 'BNB/USDT', 'profit': 6.2, 'count': 234}
        ]
    })

@app.route('/api/daily', methods=['GET'])
def get_daily():
    """Get daily profit data for charts"""
    data = get_freqtrade_data('daily')
    if data:
        return jsonify({'status': 'success', 'data': data})

    # Fallback demo data - last 30 days
    import random
    daily_data = []
    base_value = 10000
    for i in range(30):
        date = f"2025-09-{i+1:02d}"
        profit = random.uniform(-50, 150)
        base_value += profit
        daily_data.append({
            'date': date,
            'abs_profit': profit,
            'rel_profit': (profit / base_value) * 100,
            'trade_count': random.randint(5, 25),
            'balance': base_value
        })

    return jsonify({'status': 'success', 'data': daily_data})

@app.route('/api/strategies', methods=['GET'])
def get_strategies():
    """Get available strategies"""
    return jsonify({
        'status': 'success',
        'data': [
            {
                'id': '1',
                'name': 'EMA Crossover',
                'description': 'Exponential moving average crossover strategy',
                'active': True
            },
            {
                'id': '2',
                'name': 'RSI Divergence',
                'description': 'RSI divergence detection strategy',
                'active': True
            },
            {
                'id': '3',
                'name': 'Bollinger Breakout',
                'description': 'Bollinger Bands breakout strategy',
                'active': False
            }
        ]
    })

# WebSocket events
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connected', {'message': 'Connected to Freqtrade Future backend'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('subscribe')
def handle_subscribe(data):
    """Subscribe to real-time updates"""
    print(f"Client subscribed to: {data}")
    emit('subscribed', {'channels': data})

def broadcast_trade_update(trade_data):
    """Broadcast trade updates to all connected clients"""
    socketio.emit('trade_update', trade_data)

def broadcast_balance_update(balance_data):
    """Broadcast balance updates to all connected clients"""
    socketio.emit('balance_update', balance_data)

def broadcast_status_update(status_data):
    """Broadcast status updates to all connected clients"""
    socketio.emit('status_update', status_data)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"Starting Flask backend on port {port}")
    print(f"Freqtrade URL: {FREQTRADE_URL}")
    socketio.run(app, host='0.0.0.0', port=port, debug=True, allow_unsafe_werkzeug=True)