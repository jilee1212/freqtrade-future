# Freqtrade Future - Deployment Guide

## 🚀 Quick Start Deployment

### Prerequisites
- Docker & Docker Compose installed
- SSH access to Vultr server (141.164.42.93)
- Git repository access

### Option 1: Full Stack Deployment (Recommended)

Deploy all services (Freqtrade, Backend, Frontend) in one command:

```bash
./deploy.sh
```

This will:
1. Build all Docker images locally
2. Upload to Vultr server
3. Start all services

**Access URLs:**
- Frontend: http://141.164.42.93:3000
- Backend API: http://141.164.42.93:5000
- Freqtrade UI: http://141.164.42.93:8080

### Option 2: Manual Docker Compose Deployment

```bash
# On Vultr server
cd /root/freqtrade-future
docker-compose -f docker-compose.full.yml up -d

# Check status
docker-compose -f docker-compose.full.yml ps

# View logs
docker-compose -f docker-compose.full.yml logs -f
```

### Option 3: Individual Service Deployment

**Freqtrade only:**
```bash
docker-compose -f docker-compose.simple.yml up -d
```

**Backend only:**
```bash
cd backend
pip install -r requirements.txt
python app.py
```

**Frontend only:**
```bash
cd frontend
npm install
npm run build
npm start
```

## 🔧 Configuration

### Backend Environment (.env)
```
PORT=5000
FREQTRADE_URL=http://141.164.42.93:8080
FREQTRADE_USERNAME=freqtrade
FREQTRADE_PASSWORD=futures2024
FLASK_ENV=production
```

### Frontend Environment (.env.local)
```
NEXT_PUBLIC_API_URL=http://141.164.42.93:5000
NEXT_PUBLIC_WS_URL=ws://141.164.42.93:5000
NEXT_PUBLIC_FREQTRADE_URL=http://141.164.42.93:8080
```

## 📊 Service Ports

| Service | Port | URL |
|---------|------|-----|
| Frontend | 3000 | http://141.164.42.93:3000 |
| Backend API | 5000 | http://141.164.42.93:5000 |
| Freqtrade UI | 8080 | http://141.164.42.93:8080 |

## 🔍 Monitoring

**Check service status:**
```bash
docker-compose -f docker-compose.full.yml ps
```

**View logs:**
```bash
# All services
docker-compose -f docker-compose.full.yml logs -f

# Specific service
docker-compose -f docker-compose.full.yml logs -f frontend
docker-compose -f docker-compose.full.yml logs -f backend
docker-compose -f docker-compose.full.yml logs -f freqtrade
```

**Restart services:**
```bash
docker-compose -f docker-compose.full.yml restart
```

## 🛠️ Maintenance

**Update and redeploy:**
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose -f docker-compose.full.yml up -d --build
```

**Stop all services:**
```bash
docker-compose -f docker-compose.full.yml down
```

**Clean up:**
```bash
# Remove containers and volumes
docker-compose -f docker-compose.full.yml down -v

# Remove images
docker system prune -a
```

## 🐛 Troubleshooting

### Frontend not loading
```bash
# Check if running
docker-compose ps frontend

# View logs
docker-compose logs frontend

# Restart
docker-compose restart frontend
```

### Backend API errors
```bash
# Check Freqtrade connectivity
curl http://141.164.42.93:8080/api/v1/status

# Check backend health
curl http://141.164.42.93:5000/api/health
```

### Port conflicts
```bash
# Check what's using the port
netstat -tulpn | grep :3000

# Kill process
kill -9 $(lsof -t -i:3000)
```

## 📝 Notes

- Default Freqtrade credentials: `freqtrade` / `futures2024`
- All services run in Docker network for internal communication
- Logs are stored in Docker volumes
- Restart policy: `unless-stopped`

## 🔐 Security Recommendations

1. Change default Freqtrade password
2. Setup firewall rules (only allow necessary ports)
3. Use HTTPS with nginx reverse proxy
4. Enable 2FA for Freqtrade UI
5. Regular backups of user_data directory

## 📦 Backup & Restore

**Backup:**
```bash
tar -czf backup-$(date +%Y%m%d).tar.gz user_data/
```

**Restore:**
```bash
tar -xzf backup-YYYYMMDD.tar.gz
```

## 🆘 Support

For issues or questions:
- Check logs first: `docker-compose logs`
- Review Freqtrade docs: https://www.freqtrade.io/
- GitHub Issues: https://github.com/freqtrade/freqtrade/issues