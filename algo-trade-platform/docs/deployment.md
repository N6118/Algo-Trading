# Deployment Guide

This document outlines the process for deploying the Algo Trading Platform to your remote server.

## Deployment Workflow

The deployment process follows these steps:

1. Push code changes from local machine to Git repository
2. SSH into the remote server
3. Pull the latest changes
4. Install/update dependencies
5. Restart services

## Manual Deployment Steps

### From your local machine:

```bash
# Push from local
git add .
git commit -m "feat: your feature description"
git push origin main
```

### On the remote server:

```bash
# SSH into your server
ssh ubuntu@your-vm-ip

# Navigate to project directory
cd ~/algo-trade-platform

# Pull latest changes
git pull origin main

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart algo-backend

# Update frontend
cd ../frontend
npm install
pm2 restart algo-frontend
```

## Automated Deployment Script

You can automate the deployment process with a script. Create a `deploy.sh` file in the project root:

```bash
#!/bin/bash
# deploy.sh - Automated deployment script for Algo Trading Platform

# Configuration
SERVER_IP="your-vm-ip"
SERVER_USER="ubuntu"
PROJECT_PATH="/home/ubuntu/algo-trade-platform"

# Local actions
echo "Pushing local changes to Git..."
git push origin main

# Remote actions
echo "Connecting to server and deploying..."
ssh $SERVER_USER@$SERVER_IP << EOF
  cd $PROJECT_PATH
  git pull origin main
  
  # Backend update
  cd backend
  source venv/bin/activate
  pip install -r requirements.txt
  sudo systemctl restart algo-backend
  
  # Frontend update
  cd ../frontend
  npm install
  pm2 restart algo-frontend
  
  echo "Deployment completed!"
EOF

echo "Deployment process finished!"
```

Make the script executable:

```bash
chmod +x deploy.sh
```

Then run it to deploy:

```bash
./deploy.sh
```

## Monitoring Deployment

After deployment, check the status of your services:

```bash
# Check backend status
sudo systemctl status algo-backend

# Check frontend status
pm2 status algo-frontend

# Check logs if needed
sudo journalctl -u algo-backend -f
pm2 logs algo-frontend
```

## Rollback Procedure

If you need to roll back to a previous version:

```bash
# On the server
cd ~/algo-trade-platform
git log --oneline  # Find the commit hash to roll back to
git checkout <commit-hash>

# Restart services
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart algo-backend

cd ../frontend
npm install
pm2 restart algo-frontend
```
