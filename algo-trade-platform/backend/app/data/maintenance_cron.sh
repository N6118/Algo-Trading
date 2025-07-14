#!/bin/bash

# Run weekly database maintenance on Saturday at 2 AM
0 2 * * 6 /usr/bin/python3 /Users/na61/Desktop/US stockmarket Algotrading /algo-trade-platform/backend/app/data/db_maintenance.py >> /var/log/db_maintenance.log 2>&1
