# VPS Deployment - Step by Step

Run these commands in your VPS terminal (you're already SSH'd in at `root@srv1150047`):

## Step 1: Clone the repository

```bash
cd /opt
git clone https://github.com/delormeca/delorme-os-go.git
cd delorme-os-go/DumbCrawler
```

## Step 2: Verify environment file

```bash
# Check if .env.production has correct URL
cat .env.production
```

You should see:
```
API_URL=https://delorme-os2.tommy-260.workers.dev
```

## Step 3: Create active .env file

```bash
cp .env.production .env
```

## Step 4: Run deployment script

```bash
chmod +x PRODUCTION_DEPLOY.sh
bash PRODUCTION_DEPLOY.sh
```

This will:
- ✓ Install Docker (if needed)
- ✓ Build the crawler image (~5-10 min first time)
- ✓ Start the container with auto-restart
- ✓ Expose API on port 8080
- ✓ Show you the logs

## Step 5: Verify it's running

```bash
# Check container is up
docker ps

# Check health endpoint
curl http://localhost:8080/health

# View logs
docker compose -f docker-compose.production.yml logs -f
```

You should see:
```
[JobWatcher] Started - polling every 5s
Crawler Server started on port 8080
```

## Step 6: Test from your web app

Go to: https://delorme-os2.tommy-260.workers.dev

1. Click "Test Connection" → Should show green success ❌ (this will fail - API not exposed yet)
2. Create a crawl job → Crawler should pick it up within 5 seconds ✅

---

## 🔧 Management Commands

```bash
# View logs
docker compose -f docker-compose.production.yml logs -f

# Restart crawler
docker compose -f docker-compose.production.yml restart

# Stop crawler
docker compose -f docker-compose.production.yml down

# Update crawler (after git push)
cd /opt/delorme-os-go/DumbCrawler
git pull
docker compose -f docker-compose.production.yml up -d --build
```

---

## 📊 What You'll Get

After deployment:

1. **Crawler runs 24/7**
   - Auto-watches Supabase for pending jobs
   - Auto-restart on crash
   - Auto-start on VPS reboot

2. **REST API on port 8080** (VPS only for now)
   - `curl http://localhost:8080/health` ✅
   - `curl http://72.61.64.93:8080/health` ✅ (if port exposed)
   - From n8n: `curl http://dumbcrawler:8080/health` ✅

3. **Your web app**
   - Creates jobs in Supabase
   - Reads results from Supabase
   - VPS picks up and processes automatically

---

## ⚠️ About the "Test Connection" Button

The "Test Connection" button in your UI tries to connect to `http://localhost:8080`, which **only works when testing locally**.

**For production, you have 2 options:**

### Option A: Remove the Test Connection feature
It's not really needed - if jobs are processing, crawler is working.

### Option B: Expose API with Traefik (HTTPS)
Set up `crawler.yourdomain.com` with SSL - see `API_ACCESS_OPTIONS.md`

For now, **just ignore the Test Connection button** - it will fail but that's OK! The crawler will still work perfectly.

---

Ready to deploy? Run the commands above in your VPS terminal!
