#!/bin/bash
# Freqtrade Futures Bot Backup Script
# Phase 8: Automated Backup and Recovery System

set -e

# Configuration
PROJECT_DIR="/opt/freqtrade-futures"
BACKUP_DIR="/opt/backups/freqtrade"
S3_BUCKET="freqtrade-futures-backups"
RETENTION_DAYS=30
LOG_FILE="/var/log/freqtrade-backup.log"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

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

# Create backup directory
mkdir -p $BACKUP_DIR
cd $BACKUP_DIR

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="freqtrade_backup_$DATE"

log "Starting backup process: $BACKUP_NAME"

# Stop services for consistent backup
log "Stopping services for backup..."
cd $PROJECT_DIR
docker-compose stop freqtrade-bot

# Create backup directory
mkdir -p $BACKUP_DIR/$BACKUP_NAME

# Backup user data
log "Backing up user data..."
tar -czf $BACKUP_DIR/$BACKUP_NAME/user_data.tar.gz -C $PROJECT_DIR user_data/

# Backup configuration files
log "Backing up configuration..."
tar -czf $BACKUP_DIR/$BACKUP_NAME/config.tar.gz -C $PROJECT_DIR \
    docker-compose.yml \
    Dockerfile \
    requirements.txt \
    .env \
    nginx/ \
    monitoring/

# Backup database
log "Backing up database..."
if [ -f "$PROJECT_DIR/user_data/tradesv3.sqlite" ]; then
    cp $PROJECT_DIR/user_data/tradesv3.sqlite $BACKUP_DIR/$BACKUP_NAME/
fi

# Backup logs
log "Backing up logs..."
tar -czf $BACKUP_DIR/$BACKUP_NAME/logs.tar.gz -C $PROJECT_DIR logs/ 2>/dev/null || true

# Create backup manifest
log "Creating backup manifest..."
cat > $BACKUP_DIR/$BACKUP_NAME/manifest.json << EOF
{
    "backup_name": "$BACKUP_NAME",
    "timestamp": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "project_dir": "$PROJECT_DIR",
    "files": [
        "user_data.tar.gz",
        "config.tar.gz",
        "logs.tar.gz",
        "tradesv3.sqlite"
    ],
    "size_mb": $(du -sm $BACKUP_DIR/$BACKUP_NAME | cut -f1)
}
EOF

# Restart services
log "Restarting services..."
cd $PROJECT_DIR
docker-compose start freqtrade-bot

# Compress entire backup
log "Compressing backup..."
cd $BACKUP_DIR
tar -czf $BACKUP_NAME.tar.gz $BACKUP_NAME/
rm -rf $BACKUP_NAME/

# Upload to cloud storage (if configured)
if command -v aws &> /dev/null && [ ! -z "$S3_BUCKET" ]; then
    log "Uploading to S3..."
    aws s3 cp $BACKUP_NAME.tar.gz s3://$S3_BUCKET/backups/
fi

# Verify backup integrity
log "Verifying backup integrity..."
if tar -tzf $BACKUP_NAME.tar.gz > /dev/null; then
    log "Backup verification successful"
else
    error "Backup verification failed"
fi

# Cleanup old backups
log "Cleaning up old backups..."
find $BACKUP_DIR -name "freqtrade_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

# Send notification
if [ -f "$PROJECT_DIR/telegram_config.json" ]; then
    python3 - << EOF
import json
import requests
from datetime import datetime

try:
    with open('$PROJECT_DIR/telegram_config.json', 'r') as f:
        config = json.load(f)

    if config.get('enabled', False):
        message = f"""
🔄 *Backup Completed*

📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📦 Name: $BACKUP_NAME
💾 Size: $(du -sh $BACKUP_DIR/$BACKUP_NAME.tar.gz | cut -f1)
✅ Status: Success
        """

        url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
        data = {
            'chat_id': config['chat_id'],
            'text': message,
            'parse_mode': 'Markdown'
        }
        requests.post(url, data=data)
except:
    pass
EOF
fi

BACKUP_SIZE=$(du -sh $BACKUP_DIR/$BACKUP_NAME.tar.gz | cut -f1)
log "Backup completed successfully: $BACKUP_NAME.tar.gz ($BACKUP_SIZE)"