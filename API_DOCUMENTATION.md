# DumbCrawler REST API Documentation

**Base URL**: `https://dc.delorme.ca`

**Status**: ✅ LIVE and running 24/7

---

## 🔗 Quick Test

```bash
curl https://dc.delorme.ca/health
```

**Response:**
```json
{"status": "ok", "timestamp": "2025-12-14T23:32:31.755641+00:00"}
```

---

## 📋 Available Endpoints

### 1. Health Check
**GET** `/health`

Check if the API is alive and responding.

```bash
curl https://dc.delorme.ca/health
```

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-12-14T23:32:31.755641+00:00"
}
```

---

### 2. List All Jobs
**GET** `/jobs`

Get a list of all running/completed crawler jobs.

```bash
curl https://dc.delorme.ca/jobs
```

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "abc-123-def",
      "pid": 12345,
      "status": "running",
      "started_at": "2025-12-14T23:00:00Z"
    }
  ]
}
```

---

### 3. Get Job Status
**GET** `/status/:job_id`

Get detailed status and recent logs for a specific job.

```bash
curl https://dc.delorme.ca/status/abc-123-def
```

**Response:**
```json
{
  "job_id": "abc-123-def",
  "pid": 12345,
  "status": "running",
  "started_at": "2025-12-14T23:00:00Z",
  "recent_output": [
    "[INFO] Crawling page 1/100",
    "[INFO] Crawling page 2/100"
  ]
}
```

**Status values:**
- `running` - Job is currently crawling
- `completed` - Job finished successfully
- `failed` - Job encountered an error
- `paused` - Job is paused
- `killed` - Job was manually stopped

---

### 4. Spawn a New Job
**POST** `/spawn`

Start a new crawl job.

⚠️ **Note**: You need a valid `job_id` from the Supabase database.

```bash
curl -X POST https://dc.delorme.ca/spawn \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "abc-123-def",
    "log_level": "INFO"
  }'
```

**Request Body:**
```json
{
  "job_id": "abc-123-def",      // Required: Job ID from Supabase
  "log_level": "INFO"            // Optional: INFO, DEBUG, WARNING, ERROR
}
```

**Response:**
```json
{
  "job_id": "abc-123-def",
  "pid": 12345,
  "status": "running",
  "message": "Crawler started for job abc-123-def"
}
```

---

### 5. Pause a Job
**POST** `/pause/:job_id`

Pause a running crawler job.

```bash
curl -X POST https://dc.delorme.ca/pause/abc-123-def
```

**Response:**
```json
{
  "job_id": "abc-123-def",
  "pid": 12345,
  "status": "paused",
  "message": "Job abc-123-def paused"
}
```

---

### 6. Resume a Job
**POST** `/resume/:job_id`

Resume a paused crawler job.

```bash
curl -X POST https://dc.delorme.ca/resume/abc-123-def
```

**Response:**
```json
{
  "job_id": "abc-123-def",
  "pid": 12345,
  "status": "running",
  "message": "Job abc-123-def resumed"
}
```

---

### 7. Kill a Job
**POST** `/kill/:job_id`

Forcefully stop a running or paused job.

```bash
curl -X POST https://dc.delorme.ca/kill/abc-123-def
```

**Response:**
```json
{
  "job_id": "abc-123-def",
  "pid": 12345,
  "status": "killed",
  "message": "Job abc-123-def killed"
}
```

---

## 🔐 Authentication

⚠️ **IMPORTANT**: Currently, the API has **NO AUTHENTICATION**.

Anyone with the URL can access it. For production use, you should add API key authentication.

**Coming Soon**: API key authentication will be added.

---

## 🌐 Integration Examples

### JavaScript/TypeScript

```typescript
// Health check
const response = await fetch('https://dc.delorme.ca/health');
const data = await response.json();
console.log(data); // { status: 'ok', timestamp: '...' }

// Spawn a job
const spawnResponse = await fetch('https://dc.delorme.ca/spawn', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    job_id: 'your-job-id-here',
    log_level: 'INFO'
  })
});
const jobData = await spawnResponse.json();
```

---

### Python

```python
import requests

# Health check
response = requests.get('https://dc.delorme.ca/health')
print(response.json())

# Spawn a job
spawn_data = {
    "job_id": "your-job-id-here",
    "log_level": "INFO"
}
response = requests.post('https://dc.delorme.ca/spawn', json=spawn_data)
print(response.json())
```

---

### n8n Workflow

**HTTP Request Node:**
- Method: `GET` or `POST`
- URL: `https://dc.delorme.ca/health`
- Authentication: None (for now)

---

## 📊 System Info

**Infrastructure:**
- **Hosted on**: Hostinger VPS (Ubuntu 24.04)
- **IP Address**: 72.61.64.93
- **Domain**: dc.delorme.ca
- **SSL/TLS**: Let's Encrypt (Auto-renewal)
- **Uptime**: 24/7 with auto-restart
- **Container**: Docker (restart: unless-stopped)

**Features:**
- ✅ Automatic job watching (polls Supabase every 5s)
- ✅ Auto-retry failed jobs (exponential backoff, max 3 retries)
- ✅ Auto-restart on crash
- ✅ HTTPS/SSL with Let's Encrypt
- ✅ Health monitoring

---

## 🐛 Troubleshooting

### API returns 404
- The crawler container might not be running
- Check: `docker ps` on VPS

### SSL certificate error
- Certificate might be renewing
- Wait 2-3 minutes and try again

### Job not starting
- Check if job exists in Supabase database
- Job status must be 'pending' or 'running'
- Check logs: `docker logs dumbcrawler`

---

## 📞 Support

**GitHub Repository**: https://github.com/delormeca/DumbCrawler

**VPS Access** (for owner):
```bash
ssh root@72.61.64.93
cd /opt/DumbCrawler
docker logs dumbcrawler -f
```

---

## 🔄 Updates

To update the API with new features:

```bash
# On VPS
cd /opt/DumbCrawler
git pull
docker compose -f docker-compose.production.yml up -d --build
```

---

**Last Updated**: 2025-12-14
**Version**: 1.0.0
**Status**: Production Ready ✅
