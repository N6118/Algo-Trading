#!/bin/bash

# PostgreSQL 17 Monitor Script
# This script ensures PostgreSQL 17 stays running and automatically restarts if needed

LOG_FILE="/var/log/postgres-monitor.log"
POSTGRES_SERVICE="postgresql@17-main"
CHECK_INTERVAL=60  # Check every 60 seconds

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Check if PostgreSQL 17 is running
check_postgres() {
    if systemctl is-active --quiet "$POSTGRES_SERVICE"; then
        return 0
    else
        return 1
    fi
}

# Stop PostgreSQL 16 if it's running and start PostgreSQL 17
fix_postgres() {
    log_message "PostgreSQL 17 is not running. Attempting to fix..."
    
    # Stop PostgreSQL 16 if it's running
    if systemctl is-active --quiet "postgresql@16-main"; then
        log_message "Stopping PostgreSQL 16..."
        systemctl stop postgresql@16-main
        sleep 5
    fi
    
    # Start PostgreSQL 17
    log_message "Starting PostgreSQL 17..."
    systemctl start "$POSTGRES_SERVICE"
    sleep 10
    
    # Check if it started successfully
    if check_postgres; then
        log_message "PostgreSQL 17 started successfully!"
    else
        log_message "ERROR: Failed to start PostgreSQL 17!"
        return 1
    fi
}

# Main monitoring loop
log_message "PostgreSQL 17 monitor started"

while true; do
    if ! check_postgres; then
        log_message "WARNING: PostgreSQL 17 is not running!"
        fix_postgres
    else
        log_message "PostgreSQL 17 is running normally"
    fi
    
    sleep "$CHECK_INTERVAL"
done 