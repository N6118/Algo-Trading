# Algo Trading Pipeline Setup Guide

This guide explains how to set up the automated pipeline for continuous data collection and strategy execution on your server.

## Prerequisites

- Python 3.8 or higher
- PostgreSQL database
- Interactive Brokers TWS or IB Gateway running
- Required Python packages: `schedule`, `requests`

## Architecture Overview

The pipeline consists of two main services:

1. **Data Collection Service**: Continuously collects market data from IBKR
2. **Strategy Service**: Processes the collected data to calculate stop-hit (SH) and stop-loss (SL) values

## Files Overview

1. **Pipeline Manager**: `backend/app/pipeline/pipeline_manager.py`
   - Main orchestrator that runs data collection and triggers strategy execution
   - Makes HTTP requests to the strategy service
   
2. **Configuration**: `config/pipeline_config.json`
   - Settings for scheduling, database connection, and logging

3. **Service Files**:
   - `server/algo-trading-pipeline.service`: Systemd service for the pipeline manager
   - `server/algo-trading-strategy.service`: Systemd service for the strategy component

## Installation Steps

### 1. Install Dependencies

```bash
pip install schedule requests
```

### 2. Update Configuration

Edit `config/pipeline_config.json` to match your requirements:
- Adjust the schedule for running initialization and update processes
- Update database credentials if needed

### 3. Configure the Service Files

Edit both service files in the `server/` directory:
- Replace `/path/to/algo-trade-platform` with the actual path to your repository on the server
- Update the `DB_PASSWORD` environment variable if needed

### 4. Install the Systemd Services

```bash
# Copy the service files to systemd directory
sudo cp server/algo-trading-strategy.service /etc/systemd/system/
sudo cp server/algo-trading-pipeline.service /etc/systemd/system/

# Reload systemd to recognize the new services
sudo systemctl daemon-reload

# Enable the services to start on boot
sudo systemctl enable algo-trading-strategy.service
sudo systemctl enable algo-trading-pipeline.service

# Start the services
sudo systemctl start algo-trading-strategy.service
sudo systemctl start algo-trading-pipeline.service
```

### 5. Check Service Status

```bash
# Check if the services are running
sudo systemctl status algo-trading-strategy.service
sudo systemctl status algo-trading-pipeline.service

# View logs
sudo journalctl -u algo-trading-strategy.service -f
sudo journalctl -u algo-trading-pipeline.service -f
```

## Manual Operation

If you prefer to run the components manually:

```bash
# Navigate to the project directory
cd /path/to/algo-trade-platform

# Start the strategy service in one terminal
python backend/app/strategies/Stocks/attempt.py

# Start the pipeline manager in another terminal
python backend/app/pipeline/pipeline_manager.py
```

## Customization

- **Scheduling**: Modify the `schedule` section in `config/pipeline_config.json` to change when processes run
- **Logging**: Adjust logging settings in the configuration file

## Troubleshooting

- **Service won't start**: Check logs with `journalctl -u algo-trading-pipeline.service`
- **Strategy service not responding**: Ensure it's running with `systemctl status algo-trading-strategy.service`
- **Database connection issues**: Verify database credentials in the config file
- **TWS/IB Gateway connection**: Ensure TWS or IB Gateway is running and accepting API connections
