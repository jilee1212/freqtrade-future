# 🚀 Freqtrade Future - Modern Trading Dashboard

Full-stack cryptocurrency futures trading bot with modern Next.js 14 frontend and Flask backend API.

## 🎯 Features

- **Modern Frontend**: Next.js 14 with TypeScript + shadcn/ui components
- **Real-time Data**: WebSocket connections for live updates
- **Backend API**: Flask middleware with Freqtrade integration
- **Trading Dashboard**: Interactive charts with TradingView Lightweight Charts
- **Risk Management**: AI-powered risk monitoring and alerts
- **Strategy Manager**: Multiple trading strategies with backtesting
- **Docker Ready**: Full containerization with docker-compose

## 🏗️ Architecture

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Next.js   │ ───► │   Flask     │ ───► │  Freqtrade  │
│  Frontend   │      │   Backend   │      │    Bot      │
│   (3000)    │      │   (5000)    │      │   (8080)    │
└─────────────┘      └─────────────┘      └─────────────┘
```

## 📦 Tech Stack

### Frontend
- Next.js 14.2.x (App Router)
- TypeScript 5.x
- Tailwind CSS 3.4.x
- shadcn/ui components
- TradingView Lightweight Charts
- React Query
- Socket.IO Client

### Backend
- Flask 3.0.0
- Flask-SocketIO
- Python 3.11
- Freqtrade API integration

### DevOps
- Docker & Docker Compose
- Multi-stage builds
- Production optimization

## 🚀 Quick Start

### Local Development

1. **Clone repository**
```bash
git clone <your-repo-url>
cd freqtrade-future
```

2. **Backend setup**
```bash
cd backend
pip install -r requirements.txt
python app.py
```

3. **Frontend setup**
```bash
cd frontend
npm install
npm run dev
```

4. **Access services**
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- Freqtrade: http://localhost:8080

### Docker Deployment

```bash
docker-compose -f docker-compose.full.yml up -d
```

## 📁 Project Structure

```
freqtrade-future/
├── backend/
│   ├── app.py              # Flask API
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile          # Backend container
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js pages
│   │   ├── components/    # React components
│   │   └── lib/           # API & hooks
│   ├── package.json
│   └── Dockerfile         # Frontend container
├── user_data/
│   └── config_futures.json
└── docker-compose.full.yml
```

## 🌐 Pages

- **/** - Landing page with features
- **/dashboard** - Main trading dashboard with charts
- **/trades** - Trade history and open positions
- **/strategies** - Strategy management and backtesting
- **/risk** - Risk monitoring and alerts
- **/settings** - Bot configuration and API keys

## 🔧 Configuration

### Backend (.env)
```env
PORT=5000
FREQTRADE_URL=http://localhost:8080
FREQTRADE_USERNAME=freqtrade
FREQTRADE_PASSWORD=your_password
FLASK_ENV=production
```

### Frontend (.env.production)
```env
NEXT_PUBLIC_API_URL=http://your-server:5000
NEXT_PUBLIC_WS_URL=ws://your-server:5000
NEXT_PUBLIC_FREQTRADE_URL=http://your-server:8080
```

## 📊 API Endpoints

### Backend API

- `GET /api/health` - Health check
- `GET /api/status` - Bot status
- `GET /api/balance` - Account balance
- `GET /api/trades` - Trade history
- `GET /api/profit` - Profit statistics
- `GET /api/performance` - Performance by pair
- `GET /api/daily` - Daily profit data
- `GET /api/strategies` - Available strategies

### WebSocket Events

- `trade_update` - New trade executed
- `balance_update` - Balance changed
- `status_update` - Bot status changed

## 🚢 Deployment

### Vultr/VPS Deployment

1. **Clone on server**
```bash
git clone <your-repo-url>
cd freqtrade-future
```

2. **Configure environment**
```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your settings
```

3. **Build and run**
```bash
docker-compose -f docker-compose.full.yml build
docker-compose -f docker-compose.full.yml up -d
```

4. **Verify deployment**
```bash
docker-compose ps
docker-compose logs -f
```

### Production URLs

- Frontend: http://your-server:3000
- Backend API: http://your-server:5000
- Freqtrade UI: http://your-server:8080

## 🛡️ Security

- Change default Freqtrade password
- Setup UFW firewall
- Use Nginx reverse proxy with SSL
- Enable 2FA for Freqtrade
- Configure regular backups

## 📈 Performance

- API response time: < 200ms
- WebSocket latency: < 50ms
- Docker optimized builds
- Next.js standalone output

## 🐛 Troubleshooting

### Frontend not loading
```bash
docker-compose logs frontend
docker-compose restart frontend
```

### Backend API errors
```bash
docker exec -it freqtrade-backend curl http://freqtrade:8080/api/v1/status
docker-compose restart backend
```

### Port conflicts
```bash
netstat -tulpn | grep -E ':(3000|5000|8080)'
docker-compose down
```

## 📚 Documentation

- [Deployment Guide](DEPLOYMENT.md)
- [Manual Deployment](MANUAL_DEPLOYMENT.md)
- [Deployment Checklist](DEPLOYMENT_CHECKLIST.md)
- [UI Modernization Plan](UI_MODERNIZATION_PLAN.md)

## 🔄 Updates

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose -f docker-compose.full.yml up -d --build
```

## 📝 License

MIT License

## 🤝 Contributing

Contributions welcome! Please open an issue or PR.

## 📞 Support

- Issues: GitHub Issues
- Docs: See `/docs` folder
- Logs: `docker-compose logs -f`

## ⚡ Quick Commands

```bash
# Start all services
docker-compose -f docker-compose.full.yml up -d

# Stop all services
docker-compose -f docker-compose.full.yml down

# View logs
docker-compose -f docker-compose.full.yml logs -f

# Restart service
docker-compose restart [service-name]

# Check status
docker-compose ps
```

---

**Version:** 1.0.0
**Status:** Production Ready 🟢
**Last Updated:** 2025-09-30