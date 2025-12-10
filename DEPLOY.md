# DumbCrawler Deployment Guide

Deploy DumbCrawler to your VPS using Docker.

## Prerequisites

- VPS with Docker installed (your Hostinger VPS already has Docker)
- SSH access to your server
- Your Supabase credentials

## Quick Deploy (5 minutes)

### Step 1: SSH into your VPS

```bash
ssh root@72.61.64.93
```

### Step 2: Clone the repository

```bash
cd /opt
git clone https://github.com/delormeca/DumbCrawler.git
cd DumbCrawler
```

### Step 3: Create environment file

```bash
cp .env.example .env
nano .env
```

Fill in your credentials:
```
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here
API_URL=https://your-deployed-app-url.com
```

Save and exit (Ctrl+X, Y, Enter)

### Step 4: Build and start the crawler

```bash
docker compose up -d --build
```

### Step 5: Verify it's running

```bash
docker compose logs -f
```

You should see:
```
Crawler Watcher started
Waiting for pending jobs...
```

Press `Ctrl+C` to exit logs (container keeps running).

---

## Management Commands

### View logs
```bash
docker compose logs -f dumbcrawler
```

### Restart crawler
```bash
docker compose restart
```

### Stop crawler
```bash
docker compose down
```

### Update to latest version
```bash
cd /opt/DumbCrawler
git pull
docker compose up -d --build
```

### Check status
```bash
docker compose ps
```

---

## Troubleshooting

### Crawler not picking up jobs?
1. Check your Supabase credentials in `.env`
2. Verify the API_URL is correct
3. Check logs: `docker compose logs -f`

### Out of memory?
Edit `docker-compose.yml` and adjust memory limits:
```yaml
deploy:
  resources:
    limits:
      memory: 2G  # Reduce if needed
```

### Rebuild from scratch
```bash
docker compose down
docker system prune -f
docker compose up -d --build
```

---

## Resource Usage

Expected resource usage:
- **Idle**: ~200MB RAM, 0% CPU
- **Crawling**: ~1-2GB RAM, 20-50% CPU (depends on site complexity)

Your VPS (8GB RAM) can handle this easily alongside n8n.
