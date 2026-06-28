#!/bin/sh
# Structured logging POSIX backup script for Kairos SQLite database with retention

DATA_DIR="data"
BACKUP_DIR="backups"
DB_NAME="kairos-local"
TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S")

log() {
    level="$1"
    message="$2"
    utc_time=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    printf "[%s] [%s] [backup-script] %s\n" "$utc_time" "$level" "$message"
}

log "INFO" "Starting database backup..."

# Ensure we are in a directory where data/ exists
if [ ! -d "$DATA_DIR" ]; then
    if [ -d "../$DATA_DIR" ]; then
        cd ..
    fi
fi

if [ ! -f "$DATA_DIR/$DB_NAME.sqlite3" ]; then
    log "ERROR" "Database file $DATA_DIR/$DB_NAME.sqlite3 not found."
    exit 1
fi

mkdir -p "$BACKUP_DIR"

BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_$TIMESTAMP.sqlite3"

if cp "$DATA_DIR/$DB_NAME.sqlite3" "$BACKUP_FILE"; then
    log "INFO" "Backup successful: $BACKUP_FILE"

    # Retention support: keep latest 14 backups using safe alphabetical (chronological) sorting
    cd "$BACKUP_DIR" || { log "ERROR" "Failed to access backups directory"; exit 1; }

    # Wildcard expands sorted alphabetically in POSIX compliant shells
    BACKUPS=""
    for f in ${DB_NAME}_*.sqlite3; do
        if [ -f "$f" ]; then
            BACKUPS="$BACKUPS
$f"
        fi
    done

    # Filter out empty lines
    BACKUPS=$(echo "$BACKUPS" | grep -v '^$')
    COUNT=$(echo "$BACKUPS" | grep -c '^' || echo 0)

    if [ "$COUNT" -gt 14 ]; then
        DELETE_COUNT=$((COUNT - 14))
        log "INFO" "Retention policy: found $COUNT backups, deleting oldest $DELETE_COUNT..."

        echo "$BACKUPS" | head -n "$DELETE_COUNT" | while read -r old_file; do
            if [ -n "$old_file" ] && [ -f "$old_file" ]; then
                rm "$old_file"
                log "INFO" "Deleted old backup file: $old_file"
            fi
        done
    fi
else
    log "ERROR" "Failed to copy database file to $BACKUP_FILE"
    exit 1
fi
