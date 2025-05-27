# Environment Configuration

This document outlines how environment variables are managed in the Algo Trading Platform.

## Environment Variables

Environment variables are used to configure the application without changing the code. This includes database connection strings, API keys, and other sensitive information.

## Managing Secrets

Use a shared `.env.template` in your repo:

```env
# .env.template
DATABASE_URL=
SECRET_KEY=
REDIS_URL=
```

Then on each machine:

```bash
cp .env.template .env.local  # and fill in values
```

Never commit `.env.local` to git—add it to `.gitignore`.

## Environment File Setup

### Backend

Create a `.env` file in the backend directory:

```bash
# backend/.env
DATABASE_URL=postgresql://user:pass@your-vm-ip:5432/algo_db
SECRET_KEY=your-secret-key
REDIS_URL=redis://your-vm-ip:6379/0
```

In your `start-backend.sh`:

```bash
#!/bin/bash
set -a
. ./.env
set +a
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Make it executable: `chmod +x start-backend.sh`

### Frontend

For the frontend, create a `.env.local` file:

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://api.yourdomain.com
```

## Local vs. Remote Configuration

When developing locally but connecting to a remote database:

```env
# Local .env.local pointing to remote DB
DATABASE_URL=postgresql://user:pass@your-vm-ip:5432/algo_db
```

For fully local development:

```env
# Local .env.local pointing to local DB
DATABASE_URL=postgresql://user:pass@localhost:5432/algo_db
```

## Security Best Practices

1. Never commit sensitive information to Git
2. Add `.env.local` and other files containing secrets to `.gitignore`
3. Use different secrets for development, staging, and production
4. Rotate secrets regularly
5. Consider using a secrets manager for production environments
