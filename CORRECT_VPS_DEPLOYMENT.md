# ✅ CORRECT VPS Deployment Commands

## ⚠️ IMPORTANT: Clone DumbCrawler, NOT delorme-os-go!

**delorme-os-go** is NOT a GitHub repository - it's just a local directory name.

---

## 🚀 Correct Deployment Steps

Run these commands in your VPS terminal:

### Step 1: Clone the DumbCrawler repository

```bash
cd /opt
git clone https://github.com/delormeca/DumbCrawler.git
cd DumbCrawler
```

### Step 2: Create .env file

```bash
cp .env.production .env
```

### Step 3: Run deployment script

```bash
chmod +x PRODUCTION_DEPLOY.sh
bash PRODUCTION_DEPLOY.sh
```

---

## 📋 What This Does

1. Clones the public **DumbCrawler** repository
2. Copies `.env.production` to `.env` (contains your live app URL)
3. Runs automated deployment script which:
   - Installs Docker (if needed)
   - Builds the crawler image
   - Starts container with auto-restart
   - Shows you the logs

---

## ✅ After Deployment

Verify it's running:

```bash
# Check container
docker ps

# Check health
curl http://localhost:8080/health

# View logs
docker compose -f docker-compose.production.yml logs -f
```

You should see:
```
[JobWatcher] Started - polling every 5s
Crawler Server started on port 8080
```

---

## 🔧 Management Commands

```bash
# View logs
cd /opt/DumbCrawler
docker compose -f docker-compose.production.yml logs -f

# Restart
docker compose -f docker-compose.production.yml restart

# Stop
docker compose -f docker-compose.production.yml down

# Update (after git push)
git pull
docker compose -f docker-compose.production.yml up -d --build
```

---

Ready! Run the commands above starting with Step 1.
