# Development Workflow

This document outlines the recommended development workflow for the Algo Trading Platform.

## Local Development + Remote Deployment

| Layer                                 | Runs Where                          | Why                                                                        |
| ------------------------------------- | ----------------------------------- | -------------------------------------------------------------------------- |
| **Database (Postgres + TimescaleDB)** | **On your server**                  | Heavy setup, persistent state, not worth replicating locally unless needed |
| **Backend (FastAPI)**                | **Locally for development**         | Fast feedback, hot reload, local debugging                                 |
| **Frontend (Next.js)**                | **Locally for development**         | React/Next.js dev servers are fast and optimized for local                 |
| **Code deployment**                   | Push → Pull → Restart service on VM | Clean separation between dev and prod/staging                              |

## Initial Setup

### On your VM

1. Set up PostgreSQL + TimescaleDB, Redis.
2. Set up reverse proxy (Nginx), systemd units for backend/frontend.
3. Create a `~/algo-trade-platform` directory and clone the repo.
4. Set up `.env` files with secrets (DB URLs, etc.).

### On your local machine

1. Clone the same repo.
2. Set up local Python venv and Node.js.
3. Create a `.env.local` file pointing to **your remote server's DB**:

   ```bash
   DATABASE_URL=postgresql://user:pass@your-vm-ip:5432/algo_db
   ```
4. Connect your local code editor (e.g., VSCode) to remote via SSH if needed.

## Daily Development

### Frontend or Backend Code Changes

```bash
# Local dev - fast feedback
cd frontend && npm run dev
cd backend && uvicorn app.main:app --reload
```

* APIs call the **remote DB**, but you develop entirely locally.
* You use mock/stub services for any components not ready.

### Deploying Changes to the Server

```bash
# Push from local
git add .
git commit -m "feat: new endpoint for trade history"
git push origin main
```

Then, **SSH into your server**:

```bash
ssh ubuntu@your-vm-ip
cd ~/algo-trade-platform
git pull origin main
source backend/venv/bin/activate
pip install -r backend/requirements.txt
systemctl restart algo-backend

cd frontend
npm install
pm2 restart algo-frontend
```

💡 Tip: You can script this with a `deploy.sh` later.

## Offline/Local Development

If you need to develop completely locally:

| Tool                     | Install on Local       | Notes                                 |
| ------------------------ | ---------------------- | ------------------------------------- |
| PostgreSQL + TimescaleDB | ✅                      | Sync schema with remote via `pg_dump` |
| Redis                    | ✅                      | Optional unless using WebSockets      |
| Nginx                    | ❌ (not needed for dev) |                                       |
| FastAPI                  | ✅                      | `uvicorn app.main:app --reload`       |
| Next.js                  | ✅                      | `npm run dev`                         |

You'll also need a `.env.local` with `localhost` DB creds instead of remote IPs.
