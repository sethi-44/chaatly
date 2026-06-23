#!/bin/bash
# Backup script for PostgreSQL database
# Recommended to run via cron daily: 0 3 * * * /path/to/backup.sh

set -e

BACKUP_DIR="$(pwd)/backups"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/chaatly_backup_$TIMESTAMP.sql"

if [ -f "../backend/.env" ]; then
  source ../backend/.env
fi

DB_URL=${DATABASE_URL:-"postgresql://harshit:harshit%40123@localhost/chaatly"}

echo "Starting backup to $BACKUP_FILE..."
pg_dump "$DB_URL" > "$BACKUP_FILE"

# Compress the backup
gzip "$BACKUP_FILE"
echo "Backup completed successfully: $BACKUP_FILE.gz"

# Keep only the last 7 days of backups
find "$BACKUP_DIR" -type f -name "*.sql.gz" -mtime +7 -delete
echo "Old backups cleaned up."
