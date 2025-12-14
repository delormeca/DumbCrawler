# DumbCrawler REST API - Access Options

## Current Situation

The `docker-compose.production.yml` I created **DOES expose the API publicly**, but there are **better ways** to do it securely.

---

## 🌐 Option 1: Direct Port Exposure (Current Setup)

### **What it does:**
Exposes port 8080 directly to the internet.

### **Access from:**
```bash
# From anywhere on the internet:
curl http://72.61.64.93:8080/health

# From your frontend (JavaScript):
fetch('http://72.61.64.93:8080/health')

# From n8n (on same VPS):
curl http://localhost:8080/health
# OR
curl http://dumbcrawler:8080/health  # Docker network name
```

### **Pros:**
✅ Simple - just works
✅ No extra configuration needed
✅ n8n can connect easily

### **Cons:**
❌ **HTTP only** (not secure, no SSL)
❌ Exposes raw IP address
❌ Browser blocks HTTP requests from HTTPS sites (CORS)
❌ Port 8080 might be blocked by some firewalls

### **Security Risk:**
⚠️ Anyone can access your crawler API if they know your IP

---

## 🔒 Option 2: Traefik Integration (RECOMMENDED)

### **What it does:**
Uses your existing Traefik reverse proxy to expose API with **HTTPS + custom domain**.

You already have Traefik running (I saw it in `docker ps`)!

### **Access from:**
```bash
# From anywhere on the internet (HTTPS):
curl https://crawler.yourdomain.com/health

# From your frontend (JavaScript):
fetch('https://crawler.yourdomain.com/health')

# From n8n (on same VPS):
curl http://dumbcrawler:8080/health  # Docker network
```

### **Pros:**
✅ **HTTPS/SSL** (secure, encrypted)
✅ Custom domain (professional)
✅ Works with CORS from your web app
✅ Let's Encrypt auto-renewal
✅ Can add authentication middleware

### **Cons:**
❌ Requires DNS configuration
❌ Need to add subdomain to your domain

### **How to set up:**

#### Step 1: Add DNS record
In your domain registrar (Cloudflare, etc.):
```
Type: A
Name: crawler
Value: 72.61.64.93
TTL: Auto
```

Result: `crawler.yourdomain.com` → `72.61.64.93`

#### Step 2: Update docker-compose.production.yml
Uncomment the Traefik labels:
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.crawler.rule=Host(`crawler.yourdomain.com`)"
  - "traefik.http.routers.crawler.entrypoints=websecure"
  - "traefik.http.routers.crawler.tls.certresolver=letsencrypt"
  - "traefik.http.services.crawler.loadbalancer.server.port=8080"
```

#### Step 3: Remove port exposure (only Traefik connects)
```yaml
# Comment out:
# ports:
#   - "8080:8080"
```

#### Step 4: Add to Traefik's Docker network
```yaml
networks:
  - default
  - traefik_default  # Connect to Traefik

networks:
  traefik_default:
    external: true
```

Done! Now accessible via HTTPS: `https://crawler.yourdomain.com/health`

---

## 🔐 Option 3: VPS-Only Access (Most Secure)

### **What it does:**
API only accessible from within VPS (n8n only, no internet access).

### **Access from:**
```bash
# From n8n on VPS:
curl http://dumbcrawler:8080/health
curl http://localhost:8080/health

# From internet:
❌ NOT ACCESSIBLE
```

### **Pros:**
✅ **Most secure** - no internet exposure
✅ Perfect if you only need n8n integration

### **Cons:**
❌ Your frontend can't connect directly
❌ Must use Supabase as intermediary

### **How to set up:**
Remove port exposure entirely:
```yaml
# Comment out:
# ports:
#   - "8080:8080"
```

---

## 🎯 **Which Option Should You Choose?**

### **If you need frontend to call API directly:**
→ **Option 2: Traefik Integration** (HTTPS, secure)

### **If you only need n8n integration:**
→ **Option 3: VPS-Only** (most secure)

### **For quick testing (not production):**
→ **Option 1: Direct Port** (works but not secure)

---

## 🤔 **My Recommendation**

Since you mentioned:
1. ✅ "Connect from frontend or n8n"
2. ✅ "Everything must be deployed and live"

I recommend: **Option 2 (Traefik Integration)**

**Why?**
- Your frontend can call `https://crawler.yourdomain.com/health` securely
- n8n can call `http://dumbcrawler:8080` (internal Docker network)
- Proper SSL/HTTPS
- No browser CORS issues
- Professional setup

---

## 📋 What I Need From You

To set up Option 2 (Traefik), I need:

1. **Your domain name** (e.g., `yourdomain.com`)
2. **Your live app URL** (so I can update API_URL in .env)

Then I'll:
1. Update `docker-compose.production.yml` with Traefik labels
2. Give you exact DNS settings to add
3. Deploy everything with one command

---

## 🚀 Alternative: Use Supabase as API Bridge (No Direct API)

If you want to keep it simple and avoid exposing the crawler API:

**Frontend** → **Supabase Edge Functions** → **Crawler on VPS**

Your frontend calls a Supabase Edge Function, which then:
- Reads from Supabase DB (job status)
- Or creates jobs in Supabase
- Crawler picks them up automatically

**Pros:**
- No API exposure needed
- Everything through Supabase
- Most secure

**Cons:**
- Slightly more complex setup
- Less direct control

---

## ❓ Questions for You

1. **Do you need your frontend to directly call the crawler API?**
   - Or is it enough to just read/write jobs via Supabase?

2. **What's your domain name?**
   - For Traefik setup: `crawler.yourdomain.com`

3. **Do you want to expose the API to the internet, or only n8n?**
   - Internet + n8n → Option 2 (Traefik)
   - Only n8n → Option 3 (VPS-only)

Let me know your preference and I'll configure it accordingly!
