#!/bin/bash
# Freqtrade Futures Bot Restore Script
# Phase 8: Backup Recovery System

set -e

# Configuration
PROJECT_DIR="/opt/freqtrade-futures"
BACKUP_DIR="/opt/backups/freqtrade"
LOG_FILE="/var/log/freqtrade-restore.log"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a $LOG_FILE
}

show_help() {
    echo "Freqtrade Futures Bot Restore Script"
    echo ""
    echo "Usage: $0 [OPTIONS] BACKUP_FILE"
    echo ""
    echo "OPTIONS:"
    echo "  -l, --list         List available backups"
    echo "  -f, --full         Full restore (includes configuration)"
    echo "  -d, --data-only    Restore user data only"
    echo "  -c, --config-only  Restore configuration only"
    echo "  -h, --help         Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 --list"
    echo "  $0 --full freqtrade_backup_20241228_120000.tar.gz"
    echo "  $0 --data-only freqtrade_backup_20241228_120000.tar.gz"
}

list_backups() {
    info "Available backups in $BACKUP_DIR:"
    echo ""

    if [ ! -d "$BACKUP_DIR" ]; then
        warn "Backup directory not found: $BACKUP_DIR"
        return 1
    fi

    cd $BACKUP_DIR
    for backup in freqtrade_backup_*.tar.gz; do
        if [ -f "$backup" ]; then
            size=$(du -sh "$backup" | cut -f1)
            date=$(echo "$backup" | sed 's/freqtrade_backup_\([0-9]*\)_\([0-9]*\).tar.gz/\1 \2/' | sed 's/\([0-9]\{4\}\)\([0-9]\{2\}\)\([0-9]\{2\}\) \([0-9]\{2\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)/\1-\2-\3 \4:\5:\6/')
            echo "  📦 $backup ($size) - $date"
        fi
    done
}

restore_backup() {
    local backup_file=$1
    local restore_type=$2

    if [ ! -f "$BACKUP_DIR/$backup_file" ]; then
        error "Backup file not found: $BACKUP_DIR/$backup_file"
    fi

    log "Starting restore process..."
    log "Backup file: $backup_file"
    log "Restore type: $restore_type"

    # Create temporary directory
    TEMP_DIR=$(mktemp -d)
    cd $TEMP_DIR

    # Extract backup
    log "Extracting backup..."
    tar -xzf "$BACKUP_DIR/$backup_file"

    BACKUP_NAME=$(basename "$backup_file" .tar.gz)
    cd "$BACKUP_NAME"

    # Verify backup integrity
    if [ ! -f "manifest.json" ]; then
        warn "Manifest file not found, proceeding with restore anyway..."
    else
        info "Backup manifest found, verifying contents..."
        cat manifest.json
    fi

    # Stop services before restore
    log "Stopping services..."
    cd $PROJECT_DIR
    docker-compose down

    case $restore_type in
        "full")
            log "Performing full restore..."

            # Backup current state
            CURRENT_BACKUP="current_$(date +%Y%m%d_%H%M%S)"
            mkdir -p "/tmp/$CURRENT_BACKUP"
            cp -r user_data/ "/tmp/$CURRENT_BACKUP/" 2>/dev/null || true
            log "Current state backed up to /tmp/$CURRENT_BACKUP"

            # Restore user data
            if [ -f "$TEMP_DIR/$BACKUP_NAME/user_data.tar.gz" ]; then
                log "Restoring user data..."
                rm -rf user_data/
                tar -xzf "$TEMP_DIR/$BACKUP_NAME/user_data.tar.gz"
            fi

            # Restore configuration
            if [ -f "$TEMP_DIR/$BACKUP_NAME/config.tar.gz" ]; then
                log "Restoring configuration..."
                tar -xzf "$TEMP_DIR/$BACKUP_NAME/config.tar.gz"
            fi

            # Restore database
            if [ -f "$TEMP_DIR/$BACKUP_NAME/tradesv3.sqlite" ]; then
                log "Restoring database..."
                cp "$TEMP_DIR/$BACKUP_NAME/tradesv3.sqlite" user_data/
            fi
            ;;

        "data-only")
            log "Performing data-only restore..."

            if [ -f "$TEMP_DIR/$BACKUP_NAME/user_data.tar.gz" ]; then
                # Backup current user data
                if [ -d "user_data" ]; then
                    mv user_data "user_data.backup.$(date +%Y%m%d_%H%M%S)"
                fi

                log "Restoring user data..."
                tar -xzf "$TEMP_DIR/$BACKUP_NAME/user_data.tar.gz"
            fi

            if [ -f "$TEMP_DIR/$BACKUP_NAME/tradesv3.sqlite" ]; then
                log "Restoring database..."
                cp "$TEMP_DIR/$BACKUP_NAME/tradesv3.sqlite" user_data/
            fi
            ;;

        "config-only")
            log "Performing configuration-only restore..."

            if [ -f "$TEMP_DIR/$BACKUP_NAME/config.tar.gz" ]; then
                log "Restoring configuration..."
                tar -xzf "$TEMP_DIR/$BACKUP_NAME/config.tar.gz"
            fi
            ;;
    esac

    # Set proper permissions
    log "Setting permissions..."
    chown -R $USER:$USER $PROJECT_DIR

    # Restart services
    log "Starting services..."
    docker-compose up -d

    # Wait for services to start
    log "Waiting for services to initialize..."
    sleep 60

    # Health check
    log "Running health checks..."
    if curl -f http://localhost:5000/health > /dev/null 2>&1; then
        log "✓ Web dashboard is accessible"
    else
        warn "✗ Web dashboard health check failed"
    fi

    # Cleanup
    rm -rf $TEMP_DIR

    log "Restore completed successfully!"

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
🔄 *Restore Completed*

📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📦 Backup: $backup_file
🔧 Type: $restore_type
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
}

# Parse command line arguments
RESTORE_TYPE=""
BACKUP_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -l|--list)
            list_backups
            exit 0
            ;;
        -f|--full)
            RESTORE_TYPE="full"
            shift
            ;;
        -d|--data-only)
            RESTORE_TYPE="data-only"
            shift
            ;;
        -c|--config-only)
            RESTORE_TYPE="config-only"
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            BACKUP_FILE="$1"
            shift
            ;;
    esac
done

# Check arguments
if [ -z "$BACKUP_FILE" ]; then
    error "No backup file specified. Use --help for usage information."
fi

if [ -z "$RESTORE_TYPE" ]; then
    RESTORE_TYPE="full"
    warn "No restore type specified, defaulting to full restore"
fi

# Confirm restore operation
echo ""
warn "⚠️  IMPORTANT: This will restore from backup and may overwrite existing data!"
echo "Backup file: $BACKUP_FILE"
echo "Restore type: $RESTORE_TYPE"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    log "Restore operation cancelled by user"
    exit 0
fi

# Perform restore
restore_backup "$BACKUP_FILE" "$RESTORE_TYPE"