# Setup dc.delorme.ca - Complete Guide

This guide sets up your DumbCrawler API at: **https://dc.delorme.ca**

---

## Step 1: Add DNS Record (In DirectAdmin)

**In your DirectAdmin DNS Management panel:**

1. Click **"ADD RECORD"** button
2. Fill in:
   - **Name**: `dc`
   - **TTL**: `3600` (or leave default)
   - **Type**: `A`
   - **Value**: `72.61.64.93` (your VPS IP)
3. Click **Save**

**Result**: `dc.delorme.ca` → `72.61.64.93`

Wait 5-10 minutes for DNS to propagate.

---

## Step 2: Update Docker Compose Configuration

**On your VPS**, edit the docker-compose file:

```bash
cd /opt/DumbCrawler
nano docker-compose.production.yml
```

**Find this section** (around line 48):
```yaml
# Optional: Uncomment labels below to expose via Traefik with HTTPS
# labels:
#   - "traefik.enable=true"
#   - "traefik.http.routers.crawler.rule=Host(`crawler.yourdomain.com`)"
#   - "traefik.http.routers.crawler.entrypoints=websecure"
#   - "traefik.http.routers.crawler.tls.certresolver=letsencrypt"
#   - "traefik.http.services.crawler.loadbalancer.server.port=8080"
```

**Replace with** (uncommented and updated):
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.crawler.rule=Host(`dc.delorme.ca`)"
  - "traefik.http.routers.crawler.entrypoints=websecure"
  - "traefik.http.routers.crawler.tls.certresolver=letsencrypt"
  - "traefik.http.services.crawler.loadbalancer.server.port=8080"
  - "traefik.docker.network=root_default"
networks:
  - default
  - root_default

networks:
  root_default:
    external: true
```

**Save and exit**: `Ctrl+X`, then `Y`, then `Enter`

---

## Step 3: Check Traefik Configuration

Make sure Traefik has Let's Encrypt configured. Check your existing Traefik setup:

```bash
cd ~
cat docker-compose.yml | grep -A 10 certificatesResolvers
```

You should see something like:
```yaml
certificatesResolvers:
  letsencrypt:
    acme:
      email: your@email.com
      storage: /letsencrypt/acme.json
      httpChallenge:
        entryPoint: web
```

If not configured, your n8n might already have set this up.

---

## Step 4: Restart Crawler with New Configuration

```bash
cd /opt/DumbCrawler
docker compose -f docker-compose.production.yml down
docker compose -f docker-compose.production.yml up -d
```

---

## Step 5: Verify HTTPS is Working

Wait 2-3 minutes for Let's Encrypt SSL certificate to be issued, then test:

```bash
# From VPS
curl https://dc.delorme.ca/health

# Expected response:
# {"status": "ok", "timestamp": "2025-12-14T..."}
```

---

## Step 6: Test API Endpoints

Your friend (or you) can now use:

```bash
# Health check
curl https://dc.delorme.ca/health

# List jobs
curl https://dc.delorme.ca/jobs

# Get job status
curl https://dc.delorme.ca/status/job-id-here

# Spawn a job (requires job ID from Supabase)
curl -X POST https://dc.delorme.ca/spawn \
  -H "Content-Type: application/json" \
  -d '{"job_id": "your-job-id-here"}'
```

---

## 🔐 IMPORTANT: Add Authentication (Next Step)

Right now, **anyone can access your API** if they know the URL.

We should add API key authentication. Let me know when you want to add this!

---

## 🎉 What You Get

- ✅ **Professional URL**: `https://dc.delorme.ca`
- ✅ **HTTPS/SSL**: Automatic Let's Encrypt certificate
- ✅ **Auto-renewal**: SSL renews automatically
- ✅ **Works everywhere**: Browsers, n8n, curl, Postman, etc.
- ✅ **No CORS issues**: HTTPS to HTTPS works perfectly
- ⚠️ **No auth yet**: Anyone with URL can use it (fix in next step)

---

## 📱 Share with Your Friend

Once deployed, give your friend:

```
API Endpoint: https://dc.delorme.ca
Documentation: https://github.com/delormeca/DumbCrawler

Available endpoints:
- GET  /health         - Check if API is alive
- GET  /jobs           - List all running jobs
- GET  /status/:id     - Get job status
- POST /spawn          - Start a new crawl job
- POST /pause/:id      - Pause a running job
- POST /resume/:id     - Resume a paused job
- POST /kill/:id       - Kill a running job
```

---

Ready to proceed? Let me know when you've added the DNS record!
