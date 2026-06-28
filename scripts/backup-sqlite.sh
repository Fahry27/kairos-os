#!/bin/sh

# Simple POSIX backup script for Kairos SQLite database

DATA_DIR="data"
BACKUP_DIR="backups"
DB_NAME="kairos-local.sqlite3"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$BACKUP_DIR"

if [ -f "$DATA_DIR/$DB_NAME" ]; then
    cp "$DATA_DIR/$DB_NAME" "$BACKUP_DIR/${DB_NAME%.sqlite3}_$TIMESTAMP.sqlite3"
    echo "Backup successful: $BACKUP_DIR/${DB_NAME%.sqlite3}_$TIMESTAMP.sqlite3"
else
    echo "Error: Database file $DATA_DIR/$DB_NAME not found."
    exit 1
fi
