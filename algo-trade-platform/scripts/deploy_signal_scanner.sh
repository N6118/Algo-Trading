#!/bin/bash

# Signal Scanner Deployment Script
# This script sets up the signal scanner on the server

set -e

echo "🚀 Deploying Signal Scanner..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're on the server
if [[ "$(hostname)" != "vignes-SER8" ]]; then
    print_error "This script should be run on the server (anurag@100.121.186.86)"
    exit 1
fi

# Navigate to the project directory
cd /home/anurag/Desktop/Algo-Trading/algo-trade-platform

print_status "Setting up Signal Scanner..."

# Activate virtual environment
source backend/app/data/venv/bin/activate

# Set environment variables
export DB_PASSWORD=password
export PYTHONPATH=/home/anurag/Desktop/Algo-Trading/algo-trade-platform
export VIRTUAL_ENV=/home/anurag/Desktop/Algo-Trading/algo-trade-platform/backend/app/data/venv
export PATH=/home/anurag/Desktop/Algo-Trading/algo-trade-platform/backend/app/data/venv/bin:$PATH

# Initialize the signal scanner database
print_status "Initializing signal scanner database..."
python backend/app/signal_scanner/setup_signal_scanner.py

if [ $? -eq 0 ]; then
    print_status "Database initialization completed successfully"
else
    print_error "Database initialization failed"
    exit 1
fi

# Copy the service file to systemd
print_status "Installing systemd service..."
sudo cp server/algo-trading-signal-scanner.service /etc/systemd/system/

# Reload systemd
print_status "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable the service
print_status "Enabling signal scanner service..."
sudo systemctl enable algo-trading-signal-scanner

# Start the service
print_status "Starting signal scanner service..."
sudo systemctl start algo-trading-signal-scanner

# Check service status
print_status "Checking service status..."
sudo systemctl status algo-trading-signal-scanner --no-pager

print_status "✅ Signal Scanner deployment completed!"
print_status "📋 Service commands:"
print_status "   - Check status: sudo systemctl status algo-trading-signal-scanner"
print_status "   - View logs: sudo journalctl -u algo-trading-signal-scanner -f"
print_status "   - Stop service: sudo systemctl stop algo-trading-signal-scanner"
print_status "   - Restart service: sudo systemctl restart algo-trading-signal-scanner" 