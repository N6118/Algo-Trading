# Infrastructure Setup

This document outlines the infrastructure setup for the Algo Trading Platform on a single VM without containers.

## System Prerequisites

* **Ubuntu 22.04 LTS** (or your distro of choice)
* **Python 3.11** & **pip**
* **Node.js** (via nvm) & **npm**
* **PostgreSQL + TimescaleDB**
* **Redis** (for pub/sub if you need real-time updates)
* **Nginx** (as a reverse-proxy / SSL terminator)

## Folder Structure (Monorepo)

```
/home/ubuntu/algo-trade-platform
├── backend/
│   ├── venv/                   # Python virtualenv
│   ├── app/                    # Your FastAPI code
│   ├── requirements.txt
│   ├── alembic/                # DB migrations
│   └── start-backend.sh        # launch script
├── frontend/
│   ├── node_modules/           # managed by npm/yarn
│   ├── pages/                  # Next.js pages
│   ├── package.json
│   └── start-frontend.sh       # launch script
├── shared/
│   └── openapi.yaml            # API spec
└── infra/
    └── nginx.conf              # proxy config
```

## Dependency Management

### Backend

1. Create & activate a venv

   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Freeze updates as you go:

   ```bash
   pip install fastapi uvicorn[standard] ...
   pip freeze > requirements.txt
   ```

### Frontend

1. Install via nvm

   ```bash
   cd frontend
   nvm install 18
   nvm use 18
   npm install
   ```

2. Add/update deps in `package.json` and `npm install` again.

## Process Management

Since you're not using Docker, you need something to keep your services running and auto-restart on crash:

* **Supervisor** or **systemd** for the backend
* **pm2** or **systemd** for the frontend

### Example systemd Unit for Backend

Create a file at `/etc/systemd/system/algo-backend.service`:

```ini
[Unit]
Description=Algo Trading Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/algo-trade-platform/backend
ExecStart=/home/ubuntu/algo-trade-platform/backend/venv/bin/uvicorn app.main:app \
  --host 0.0.0.0 --port 8000 --reload
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable & start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable algo-backend
sudo systemctl start algo-backend
```

### Example pm2 for Frontend

```bash
cd frontend
pm2 start npm --name algo-frontend -- start
pm2 save
pm2 startup systemd  # generates a systemd unit
```

## Reverse Proxy with Nginx

Create a configuration file in `infra/nginx.conf`:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
}

server {
    listen 80;
    server_name app.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
    }
}
```

Activate the configuration:

```bash
sudo ln -s /home/ubuntu/algo-trade-platform/infra/nginx.conf \
            /etc/nginx/sites-enabled/algo-trade
sudo nginx -t
sudo systemctl reload nginx
```
