# Algo Trading Platform

A comprehensive platform for algorithmic trading on US stock markets.

## Project Structure

```
/algo-trade-platform
├── backend/             # FastAPI backend
├── frontend/            # Next.js frontend
├── shared/              # Shared resources (API specs, etc.)
├── infra/               # Infrastructure configuration
└── docs/                # Project documentation
```

## Development Setup

This project follows a **Local Development + Remote Deployment** workflow:
- Database (PostgreSQL + TimescaleDB) runs on the remote server
- Backend (FastAPI) and Frontend (Next.js) are developed locally
- Code is deployed to the remote server via Git

See the [Development Workflow](./docs/development-workflow.md) document for detailed setup instructions.

## Infrastructure

The platform runs on a single VM with:
- PostgreSQL + TimescaleDB for data storage
- Redis for caching and pub/sub (if needed)
- Nginx as a reverse proxy
- systemd/pm2 for process management

See the [Infrastructure Setup](./docs/infrastructure-setup.md) document for details.

## Environment Configuration

Environment variables are managed through `.env` files:
- `.env.template` is committed to the repository as a reference
- `.env.local` contains actual values and is not committed

See the [Environment Configuration](./docs/environment-config.md) document for details.

## Deployment

Code is deployed to the remote server via Git. See the [Deployment Guide](./docs/deployment.md) for instructions.
