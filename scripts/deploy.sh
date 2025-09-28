#!/bin/bash
# Vultr VPS Deployment Script
# Phase 8: Production Deployment Automation

set -e

echo "========================================"
echo "FREQTRADE FUTURES BOT DEPLOYMENT"
echo "========================================"

# Configuration
PROJECT_DIR="/opt/freqtrade-futures"
BACKUP_DIR="/opt/backups/freqtrade"
LOG_FILE="/var/log/freqtrade-deploy.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a $LOG_FILE
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a $LOG_FILE
    exit 1
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a $LOG_FILE
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root for security reasons"
fi

# Create necessary directories
log "Creating directories..."
sudo mkdir -p $PROJECT_DIR
sudo mkdir -p $BACKUP_DIR
sudo mkdir -p /var/log

# System updates
log "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Docker and Docker Compose
log "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Install monitoring tools
log "Installing monitoring tools..."
sudo apt install -y htop iotop nethogs ncdu fail2ban ufw

# Configure firewall
log "Configuring firewall..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 5000/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 9090/tcp
sudo ufw --force enable

# Clone or update repository
log "Setting up project..."
if [ -d "$PROJECT_DIR/.git" ]; then
    log "Updating existing repository..."
    cd $PROJECT_DIR
    git fetch origin
    git reset --hard origin/production
else
    log "Cloning repository..."
    sudo git clone https://github.com/yourusername/freqtrade-futures.git $PROJECT_DIR
    cd $PROJECT_DIR
    git checkout production
fi

# Set permissions
sudo chown -R $USER:$USER $PROJECT_DIR

# Create environment file
log "Creating environment configuration..."
cat > $PROJECT_DIR/.env << EOF
# Production Environment Configuration
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=sqlite:///user_data/tradesv3.sqlite

# API Configuration
FREQTRADE_API_SERVER=true
FREQTRADE_API_LISTEN_IP_ADDRESS=0.0.0.0
FREQTRADE_API_SERVER_PORT=8080
FREQTRADE_API_USERNAME=freqtrade
FREQTRADE_API_PASSWORD=futures2024

# Web Dashboard
FLASK_ENV=production
FLASK_DEBUG=false

# Telegram Configuration
TELEGRAM_ENABLED=true
TELEGRAM_TOKEN=YOUR_BOT_TOKEN
TELEGRAM_CHAT_ID=YOUR_CHAT_ID

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
EOF

# Create SSL certificates directory
log "Setting up SSL certificates..."
sudo mkdir -p $PROJECT_DIR/nginx/ssl

# Generate self-signed certificates for development
if [ ! -f "$PROJECT_DIR/nginx/ssl/fullchain.pem" ]; then
    log "Generating self-signed SSL certificates..."
    sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout $PROJECT_DIR/nginx/ssl/privkey.pem \
        -out $PROJECT_DIR/nginx/ssl/fullchain.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    sudo chown -R $USER:$USER $PROJECT_DIR/nginx/ssl
fi

# Build and start services
log "Building and starting services..."
cd $PROJECT_DIR

# Pull latest images
docker-compose pull

# Build custom images
docker-compose build

# Start services
docker-compose up -d

# Wait for services to start
log "Waiting for services to initialize..."
sleep 60

# Health check
log "Running health checks..."
for service in web-dashboard freqtrade-bot redis prometheus grafana; do
    if docker-compose ps $service | grep -q "Up"; then
        log "✓ $service is running"
    else
        warn "✗ $service is not running properly"
    fi
done

# Test web dashboard
if curl -f http://localhost:5000/health > /dev/null 2>&1; then
    log "✓ Web dashboard is accessible"
else
    warn "✗ Web dashboard health check failed"
fi

# Setup log rotation
log "Setting up log rotation..."
sudo tee /etc/logrotate.d/freqtrade << EOF
/var/log/freqtrade*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 $USER $USER
}
EOF

# Create systemd service for monitoring
log "Creating monitoring service..."
sudo tee /etc/systemd/system/freqtrade-monitor.service << EOF
[Unit]
Description=Freqtrade Futures Monitor
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
User=$USER
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable freqtrade-monitor.service

# Setup backup script
log "Setting up backup automation..."
cat > $PROJECT_DIR/scripts/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups/freqtrade"
PROJECT_DIR="/opt/freqtrade-futures"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup user data
tar -czf $BACKUP_DIR/userdata_$DATE.tar.gz -C $PROJECT_DIR user_data/

# Backup database
cp $PROJECT_DIR/user_data/tradesv3.sqlite $BACKUP_DIR/tradesv3_$DATE.sqlite

# Keep only last 7 days of backups
find $BACKUP_DIR -name "userdata_*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "tradesv3_*.sqlite" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x $PROJECT_DIR/scripts/backup.sh

# Add backup to crontab
(crontab -l 2>/dev/null; echo "0 2 * * * $PROJECT_DIR/scripts/backup.sh >> /var/log/freqtrade-backup.log 2>&1") | crontab -

log "========================================"
log "DEPLOYMENT COMPLETED SUCCESSFULLY!"
log "========================================"
log "Web Dashboard: http://$(curl -s ifconfig.me):5000"
log "Grafana: http://$(curl -s ifconfig.me):3000"
log "Prometheus: http://$(curl -s ifconfig.me):9090"
log ""
log "Next steps:"
log "1. Configure your API keys in user_data/config_futures.json"
log "2. Set up Telegram bot token in telegram_config.json"
log "3. Obtain SSL certificates for production"
log "4. Configure domain name and DNS"
log "========================================"