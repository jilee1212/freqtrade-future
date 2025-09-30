# 🚀 Deployment Checklist

## Pre-Deployment Verification

### ✅ Local Testing Complete
- [x] Backend API running on localhost:5000
- [x] Frontend running on localhost:3000
- [x] Integration tests passed (8/8)
- [x] All API endpoints responding correctly
- [x] Mock data working as fallback

### 📦 Files Ready
- [x] `backend/app.py` - Flask API with 8 endpoints
- [x] `backend/requirements.txt` - Python dependencies
- [x] `backend/Dockerfile` - Backend containerization
- [x] `frontend/Dockerfile` - Frontend production build
- [x] `docker-compose.full.yml` - Full stack orchestration
- [x] `deploy.sh` - Automated deployment script
- [x] `DEPLOYMENT.md` - Comprehensive guide

## Deployment Steps

### 1. Prepare Environment Variables

**On Vultr Server (141.164.42.93):**

```bash
# Create backend/.env
PORT=5000
FREQTRADE_URL=http://freqtrade:8080
FREQTRADE_USERNAME=freqtrade
FREQTRADE_PASSWORD=futures2024
FLASK_ENV=production
```

```bash
# Create frontend/.env.production
NEXT_PUBLIC_API_URL=http://141.164.42.93:5000
NEXT_PUBLIC_WS_URL=ws://141.164.42.93:5000
NEXT_PUBLIC_FREQTRADE_URL=http://141.164.42.93:8080
```

### 2. SSH Access Verification

```bash
ssh root@141.164.42.93
# Verify connection
```

### 3. Option A: Automated Deployment

```bash
# On local machine
chmod +x deploy.sh
./deploy.sh
```

**This will:**
1. Build Docker images locally
2. Save images to tar file
3. Upload to Vultr server
4. Load images on server
5. Start all services

### 4. Option B: Manual Deployment

**Step 1: Upload files to server**
```bash
scp -r backend frontend docker-compose.full.yml root@141.164.42.93:/root/freqtrade-future/
```

**Step 2: SSH to server and build**
```bash
ssh root@141.164.42.93
cd /root/freqtrade-future
docker-compose -f docker-compose.full.yml build
docker-compose -f docker-compose.full.yml up -d
```

### 5. Verify Deployment

**Check services are running:**
```bash
docker-compose -f docker-compose.full.yml ps
```

**Test endpoints:**
```bash
curl http://141.164.42.93:5000/api/health
curl http://141.164.42.93:5000/api/status
curl http://141.164.42.93:3000
curl http://141.164.42.93:8080/api/v1/status
```

**Check logs:**
```bash
docker-compose -f docker-compose.full.yml logs -f
```

## Post-Deployment

### Service URLs
- ✅ Frontend: http://141.164.42.93:3000
- ✅ Backend API: http://141.164.42.93:5000
- ✅ Freqtrade UI: http://141.164.42.93:8080

### Health Checks
```bash
# Backend health
curl http://141.164.42.93:5000/api/health

# Frontend (should return HTML)
curl http://141.164.42.93:3000

# Backend status
curl http://141.164.42.93:5000/api/status
```

### Monitor Services
```bash
# View all logs
docker-compose -f docker-compose.full.yml logs -f

# View specific service
docker-compose -f docker-compose.full.yml logs -f frontend
docker-compose -f docker-compose.full.yml logs -f backend
docker-compose -f docker-compose.full.yml logs -f freqtrade

# Check resource usage
docker stats
```

## Rollback Plan

If deployment fails:

```bash
# Stop new services
docker-compose -f docker-compose.full.yml down

# Restart previous Freqtrade-only setup
docker-compose -f docker-compose.simple.yml up -d
```

## Security Checklist

- [ ] Change default Freqtrade password
- [ ] Setup firewall rules (UFW)
  ```bash
  ufw allow 22/tcp    # SSH
  ufw allow 3000/tcp  # Frontend
  ufw allow 5000/tcp  # Backend
  ufw allow 8080/tcp  # Freqtrade
  ufw enable
  ```
- [ ] Setup nginx reverse proxy with SSL
- [ ] Enable 2FA for Freqtrade
- [ ] Configure backup schedule

## Troubleshooting

### Frontend not loading
```bash
docker-compose logs frontend
docker-compose restart frontend
```

### Backend API errors
```bash
# Check if Freqtrade is accessible
docker exec -it freqtrade-backend curl http://freqtrade:8080/api/v1/status

# Restart backend
docker-compose restart backend
```

### Port conflicts
```bash
# Check ports in use
netstat -tulpn | grep -E ':(3000|5000|8080)'

# Kill conflicting processes
kill -9 $(lsof -t -i:3000)
```

## Performance Monitoring

### Key Metrics to Watch
- API response time (should be < 200ms)
- Memory usage (< 80%)
- CPU usage (< 70%)
- WebSocket connections

### Monitoring Commands
```bash
# Resource usage
docker stats --no-stream

# API latency test
time curl http://141.164.42.93:5000/api/status

# Check WebSocket
wscat -c ws://141.164.42.93:5000
```

## Backup Strategy

### Daily Backup
```bash
# Backup user data
tar -czf backup-$(date +%Y%m%d).tar.gz user_data/

# Backup environment files
tar -czf env-backup-$(date +%Y%m%d).tar.gz backend/.env frontend/.env.production
```

### Restore from Backup
```bash
tar -xzf backup-YYYYMMDD.tar.gz
docker-compose restart
```

## Update Procedure

### Code Updates
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose -f docker-compose.full.yml up -d --build
```

### Zero-Downtime Updates
```bash
# Update one service at a time
docker-compose up -d --no-deps --build frontend
docker-compose up -d --no-deps --build backend
```

## Contact & Support

### Logs Location
- Docker logs: `docker-compose logs`
- Freqtrade logs: `user_data/logs/`

### Important Files
- Configuration: `user_data/config_futures.json`
- Environment: `backend/.env`, `frontend/.env.production`
- Deployment: `docker-compose.full.yml`

### Quick Reference
```bash
# Start all services
docker-compose -f docker-compose.full.yml up -d

# Stop all services
docker-compose -f docker-compose.full.yml down

# Restart services
docker-compose -f docker-compose.full.yml restart

# View logs
docker-compose -f docker-compose.full.yml logs -f

# Check status
docker-compose -f docker-compose.full.yml ps
```

---

**Status:** Ready for deployment ✅
**Last Updated:** 2025-09-30
**Version:** 1.0.0