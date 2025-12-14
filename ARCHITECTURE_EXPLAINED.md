# DumbCrawler Architecture - Complete Explanation

## What We're Building

A **production-grade web crawler** that runs 24/7 on your VPS and can be controlled via REST API.

---

## 🎯 Your Requirements

1. **VPS is ALWAYS the crawler** (never use local machine)
2. **REST API access** (for frontend and n8n integration)
3. **Runs FOREVER** (auto-restart, auto-recover from failures)
4. **No manual intervention needed**

---

## 📊 The Complete Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR WEB APPLICATION                      │
│              (Cloudflare/wherever it's hosted)               │
│                                                               │
│  User clicks "Start Crawl" → Creates job in Supabase        │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ Writes job to database
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    SUPABASE (Cloud DB)                       │
│                                                               │
│  ┌──────────────────────────────────────────────────┐       │
│  │  crawl_jobs table                                 │       │
│  │  ┌────────┬──────────┬────────────────┐          │       │
│  │  │ job_id │  status  │   project_id   │          │       │
│  │  ├────────┼──────────┼────────────────┤          │       │
│  │  │ abc123 │ pending  │  proj-xyz-456  │ ← NEW!   │       │
│  │  └────────┴──────────┴────────────────┘          │       │
│  └──────────────────────────────────────────────────┘       │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ Polls every 5 seconds
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              YOUR VPS (72.61.64.93)                          │
│              Hostinger VPS - Ubuntu 24.04                    │
│              8GB RAM, 2 CPUs                                 │
│                                                               │
│  ┌───────────────────────────────────────────────────┐      │
│  │   Docker Container: dumbcrawler                   │      │
│  │                                                     │      │
│  │   ┌─────────────────────────────────────────┐     │      │
│  │   │   crawler_server.py                      │     │      │
│  │   │   (Port 8080)                           │     │      │
│  │   │                                          │     │      │
│  │   │   [1] Job Watcher Thread                │     │      │
│  │   │       ↓ Polls Supabase every 5s         │     │      │
│  │   │       ↓ Finds "pending" jobs            │     │      │
│  │   │       ↓ Spawns crawler subprocess       │     │      │
│  │   │                                          │     │      │
│  │   │   [2] REST API Server                   │     │      │
│  │   │       GET  /health                       │     │      │
│  │   │       GET  /jobs                         │     │      │
│  │   │       GET  /status/:job_id              │     │      │
│  │   │       POST /spawn                        │     │      │
│  │   │       POST /pause/:job_id               │     │      │
│  │   │       POST /resume/:job_id              │     │      │
│  │   │       POST /kill/:job_id                │     │      │
│  │   │                                          │     │      │
│  │   │   [3] Retry Manager Thread              │     │      │
│  │   │       ↓ Auto-retries failed jobs        │     │      │
│  │   │       ↓ Exponential backoff             │     │      │
│  │   │                                          │     │      │
│  │   │   [4] Process Manager                   │     │      │
│  │   │       ↓ Manages crawler subprocesses    │     │      │
│  │   │       ↓ Tracks output/logs              │     │      │
│  │   └─────────────────────────────────────────┘     │      │
│  │                                                     │      │
│  │   When crawl finishes → Sends results to Supabase │      │
│  └───────────────────────────────────────────────────┘      │
│                                                               │
│  Docker settings:                                            │
│  • restart: unless-stopped  ← Always restarts on crash      │
│  • healthcheck: checks /health every 30s                     │
│  • resource limits: 4GB RAM max                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 How It Works (Step by Step)

### **Scenario: User Starts a Crawl**

1. **User clicks "Start Crawl" in your web app**
   - Your app (running on Cloudflare/wherever) creates a record in Supabase:
   ```sql
   INSERT INTO crawl_jobs (id, project_id, status, settings)
   VALUES ('abc123', 'proj-xyz', 'pending', {...})
   ```

2. **Job Watcher on VPS detects it (within 5 seconds)**
   - The `crawler_server.py` running in Docker polls Supabase:
   ```python
   # Every 5 seconds, checks:
   SELECT * FROM crawl_jobs WHERE status = 'pending'
   ```
   - Finds your new job `abc123`

3. **VPS marks job as "running"**
   ```sql
   UPDATE crawl_jobs SET status = 'running' WHERE id = 'abc123'
   ```

4. **VPS spawns crawler subprocess**
   ```bash
   # Starts actual crawler
   python run_crawl_job.py --job-id abc123
   ```

5. **Crawler scrapes the website**
   - Visits pages
   - Extracts data (title, meta, content, etc.)
   - Takes screenshots
   - Follows links

6. **Crawler sends results back to Supabase (in batches)**
   ```python
   # Every 50 pages, sends results:
   POST /api/crawl/results
   {
     "crawl_job_id": "abc123",
     "pages": [...100 pages of data...]
   }
   ```

7. **Your web app reads results from Supabase**
   - User sees progress in real-time
   - No direct connection to VPS needed!

8. **Job completes**
   ```sql
   UPDATE crawl_jobs SET status = 'completed' WHERE id = 'abc123'
   ```

---

## 🛡️ How We Ensure "FOREVER" Operation

### **1. Docker Auto-Restart**
```yaml
restart: unless-stopped
```
- If crawler crashes → Docker restarts it within seconds
- If VPS reboots → Docker auto-starts container
- Only stops if YOU manually stop it

### **2. Health Checks**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```
- Docker checks `/health` endpoint every 30 seconds
- If unhealthy 3 times in a row → Docker restarts container

### **3. Automatic Job Retry**
Built-in retry manager:
- Failed job → Retries after 2 minutes
- Failed again → Retries after 4 minutes
- Failed again → Retries after 8 minutes
- Max 3 retries per job

### **4. Error Isolation**
- Each crawl runs in its own subprocess
- If one crawl crashes → others keep running
- Main server keeps watching for new jobs

### **5. Resource Limits**
```yaml
resources:
  limits:
    memory: 4G  # Won't crash VPS by using all RAM
    cpus: 2.0
```

---

## 🌐 REST API - How to Use It

The crawler exposes a REST API on port 8080.

### **Option A: Local Access (VPS only)**
```bash
# On VPS:
curl http://localhost:8080/health
```

### **Option B: Expose to Internet (Optional)**
Add to `docker-compose.production.yml`:
```yaml
ports:
  - "8080:8080"  # This exposes it
```

Then access from anywhere:
```bash
curl http://72.61.64.93:8080/health
```

### **Option C: Through Traefik (Secure with SSL)**
Uncomment Traefik labels in `docker-compose.production.yml`:
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.crawler.rule=Host(`crawler.yourdomain.com`)"
```

Then access:
```bash
curl https://crawler.yourdomain.com/health
```

### **API Endpoints**

| Endpoint | Method | Purpose | Example |
|----------|--------|---------|---------|
| `/health` | GET | Check if crawler is alive | `curl http://vps:8080/health` |
| `/jobs` | GET | List all running jobs | `curl http://vps:8080/jobs` |
| `/status/:id` | GET | Get job status + recent logs | `curl http://vps:8080/status/abc123` |
| `/spawn` | POST | Manually start a crawl | `curl -X POST http://vps:8080/spawn -d '{"job_id":"xyz"}'` |
| `/pause/:id` | POST | Pause a running job | `curl -X POST http://vps:8080/pause/abc123` |
| `/resume/:id` | POST | Resume a paused job | `curl -X POST http://vps:8080/resume/abc123` |
| `/kill/:id` | POST | Kill a running job | `curl -X POST http://vps:8080/kill/abc123` |

---

## 🔌 n8n Integration

You can control the crawler from n8n workflows!

### **Example: Trigger Crawl from n8n**

1. **HTTP Request Node** in n8n:
   ```
   Method: POST
   URL: http://localhost:8080/spawn
   Body:
   {
     "job_id": "{{ $json.crawl_job_id }}",
     "log_level": "INFO"
   }
   ```

2. **Check Status** (polling):
   ```
   Method: GET
   URL: http://localhost:8080/status/{{ $json.job_id }}
   ```

3. **Wait for Completion** (n8n Wait node)
   - Poll every 30 seconds
   - Check if status == "completed"

### **Example: Auto-Crawl on Schedule**

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│  Schedule   │───>│  Create Job  │───>│  Spawn Crawler  │
│  (Daily)    │    │  in Supabase │    │  via API        │
└─────────────┘    └──────────────┘    └─────────────────┘
```

---

## 🚀 Why VPS is ALWAYS Used (Never Local)

### **Problem Before:**
- Your web app had a "Test Connection" button that tried `http://localhost:8080`
- This only works on your local machine
- When deployed, it fails because there's no local crawler

### **Solution Now:**

1. **Web app NEVER talks directly to crawler**
   - App writes to Supabase → VPS reads from Supabase
   - App reads from Supabase → VPS writes to Supabase
   - **Supabase is the bridge**

2. **Local crawler removed**
   - We killed the local crawler_server.py I started earlier
   - No confusion about which crawler is running

3. **VPS is the single source of truth**
   - Only ONE crawler server exists: on VPS
   - Even if you run locally for development, it still uses VPS crawler

---

## 📝 Deployment Checklist

### **What We're About to Do:**

1. ✅ **Files created locally** (already done)
   - `docker-compose.production.yml` - Production config
   - `.env.production` - Template for credentials
   - `PRODUCTION_DEPLOY.sh` - Automated deployment script

2. ⏳ **Clone to VPS**
   ```bash
   cd /opt
   git clone https://github.com/delormeca/delorme-os-go.git
   cd delorme-os-go/DumbCrawler
   ```

3. ⏳ **Configure environment**
   ```bash
   cp .env.production .env
   nano .env  # Edit API_URL to your live app URL
   ```

4. ⏳ **Run deployment script**
   ```bash
   chmod +x PRODUCTION_DEPLOY.sh
   bash PRODUCTION_DEPLOY.sh
   ```

   This script will:
   - ✓ Install Docker (if needed)
   - ✓ Build the crawler image (~5-10 min first time)
   - ✓ Start the container
   - ✓ Show you the logs

5. ⏳ **Verify it's running**
   ```bash
   docker compose -f docker-compose.production.yml ps
   curl http://localhost:8080/health
   ```

---

## 🔧 Daily Operations

### **View Logs**
```bash
cd /opt/delorme-os-go/DumbCrawler
docker compose -f docker-compose.production.yml logs -f
```

### **Restart Crawler**
```bash
docker compose -f docker-compose.production.yml restart
```

### **Stop Crawler**
```bash
docker compose -f docker-compose.production.yml down
```

### **Update Crawler (when you push new code)**
```bash
cd /opt/delorme-os-go/DumbCrawler
git pull
docker compose -f docker-compose.production.yml up -d --build
```

### **Check Resource Usage**
```bash
docker stats dumbcrawler
```

---

## ❓ Common Questions

### **Q: What if VPS runs out of memory?**
A: Resource limits prevent this:
```yaml
limits:
  memory: 4G  # Max 4GB (VPS has 8GB total)
```

### **Q: What if Supabase goes down?**
A: Job Watcher handles this gracefully:
- Prints warning once
- Keeps trying in background
- Resumes when Supabase comes back

### **Q: What if I deploy new code?**
A: Zero-downtime update:
```bash
git pull
docker compose -f docker-compose.production.yml up -d --build
```
Docker recreates container, preserves running jobs.

### **Q: How do I monitor it?**
A: Multiple ways:
1. Logs: `docker compose logs -f`
2. Health endpoint: `curl http://localhost:8080/health`
3. n8n monitoring workflow (ping every 5 min)
4. Your web app shows jobs from Supabase

### **Q: What if I want to crawl locally for testing?**
A: You can, but it will still use VPS database:
```bash
# On your local machine
cd DumbCrawler/crawler
python run_crawl_job.py --job-id test-123 --api-url http://localhost:3001
```
Results still go to Supabase, so VPS sees them too.

---

## 🎯 Summary

**What you get:**
- ✅ Crawler runs 24/7 on VPS (never local)
- ✅ REST API on port 8080 for control
- ✅ Auto-restart on crashes
- ✅ Auto-retry failed jobs
- ✅ n8n integration ready
- ✅ Health monitoring
- ✅ Resource protection
- ✅ Easy updates via git pull

**Your web app:**
- Writes jobs to Supabase
- Reads results from Supabase
- Never talks to VPS directly (unless you want API access)

**VPS crawler:**
- Watches Supabase for jobs
- Processes them automatically
- Writes results back to Supabase
- Restarts forever if it crashes

**You:**
- Push code to GitHub
- SSH to VPS
- Run `git pull && docker compose up -d --build`
- Done!

---

## 🚦 Ready to Deploy?

Once you tell me your **live app URL**, I'll update the `.env.production` file and we'll deploy to VPS!

What's your deployed app URL? (e.g., `https://your-app.pages.dev`)
