#!/bin/bash

# Algo Trading Services Restart Script
# This script restarts all services and verifies they're working

echo "🚀 Starting Algo Trading Services Restart Process..."
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check service status
check_service() {
    local service_name=$1
    echo -e "${BLUE}📊 Checking $service_name status...${NC}"
    sudo systemctl status $service_name --no-pager -l
    echo ""
}

# Function to restart service
restart_service() {
    local service_name=$1
    echo -e "${YELLOW}🔄 Restarting $service_name...${NC}"
    sudo systemctl restart $service_name
    sleep 3
    if sudo systemctl is-active --quiet $service_name; then
        echo -e "${GREEN}✅ $service_name is running${NC}"
    else
        echo -e "${RED}❌ $service_name failed to start${NC}"
    fi
    echo ""
}

# Function to check database connection
check_database() {
    echo -e "${BLUE}🗄️ Checking database connection...${NC}"
    psql "postgresql://postgres:password@100.121.186.86:5432/theodb" -c "SELECT NOW() as current_time, COUNT(*) as total_ticks FROM stock_ticks;" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Database connection successful${NC}"
    else
        echo -e "${RED}❌ Database connection failed${NC}"
    fi
    echo ""
}

# Function to check recent data
check_recent_data() {
    echo -e "${BLUE}📈 Checking recent data...${NC}"
    psql "postgresql://postgres:password@100.121.186.86:5432/theodb" -c "
    SELECT 
        'Tick Data' as data_type,
        MAX(timestamp) as latest_time,
        COUNT(*) as recent_count
    FROM stock_ticks 
    WHERE timestamp > NOW() - INTERVAL '1 hour'
    UNION ALL
    SELECT 
        'SH/SL Data' as data_type,
        MAX(created) as latest_time,
        COUNT(*) as recent_count
    FROM tbl_ohlc_fifteen_output 
    WHERE created > NOW() - INTERVAL '1 hour'
    UNION ALL
    SELECT 
        'Signals' as data_type,
        MAX(signal_time) as latest_time,
        COUNT(*) as recent_count
    FROM generated_signals 
    WHERE signal_time > NOW() - INTERVAL '1 hour';" 2>/dev/null
    echo ""
}

# Main restart process
echo -e "${YELLOW}🔄 Starting service restart sequence...${NC}"

# 1. Check current status
echo -e "${BLUE}📊 Current Service Status:${NC}"
check_service "algo-trading-streamdata.service"
check_service "algo-trading-signal-scanner.service"
check_service "algo-trading-attempt.service"
check_service "algo-trading-attempt-aggregator.service"

# 2. Restart services in order
echo -e "${YELLOW}🔄 Restarting services in dependency order...${NC}"

# Start with streamdata (data collection)
restart_service "algo-trading-streamdata.service"

# Wait a bit for data to start flowing
echo -e "${BLUE}⏳ Waiting for data collection to stabilize...${NC}"
sleep 10

# Restart signal scanner
restart_service "algo-trading-signal-scanner.service"

# Restart other services
restart_service "algo-trading-attempt.service"
restart_service "algo-trading-attempt-aggregator.service"

# 3. Verify all services are running
echo -e "${BLUE}✅ Final Service Status Check:${NC}"
check_service "algo-trading-streamdata.service"
check_service "algo-trading-signal-scanner.service"
check_service "algo-trading-attempt.service"
check_service "algo-trading-attempt-aggregator.service"

# 4. Check database and data
echo -e "${BLUE}📊 Data Verification:${NC}"
check_database
check_recent_data

# 5. Show recent logs
echo -e "${BLUE}📋 Recent Logs (last 10 lines):${NC}"
echo -e "${YELLOW}Streamdata logs:${NC}"
sudo journalctl -u algo-trading-streamdata.service -n 10 --no-pager
echo ""
echo -e "${YELLOW}Signal scanner logs:${NC}"
sudo journalctl -u algo-trading-signal-scanner.service -n 10 --no-pager
echo ""

# 6. Final status
echo -e "${GREEN}🎉 Service restart process completed!${NC}"
echo -e "${BLUE}📊 Monitor the services with:${NC}"
echo "sudo systemctl status algo-trading-*"
echo ""
echo -e "${BLUE}📋 View live logs with:${NC}"
echo "sudo journalctl -u algo-trading-streamdata.service -f"
echo "sudo journalctl -u algo-trading-signal-scanner.service -f"
echo ""
echo -e "${BLUE}📈 Check data flow with:${NC}"
echo "psql \"postgresql://postgres:password@100.121.186.86:5432/theodb\" -c \"SELECT COUNT(*) FROM stock_ticks WHERE timestamp > NOW() - INTERVAL '5 minutes';\""
