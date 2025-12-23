# ✅ Delorme OS2 Successfully Deployed!

## 🚀 Your Production URL

**Your app is now live at:**
```
https://delorme-os2.tommy-260.workers.dev
```

---

## 📝 Next Step: Update DumbCrawler on VPS

Your DumbCrawler on the VPS needs to be updated to use this production URL.

### SSH into your VPS and update the `.env` file:

```bash
# SSH into your VPS
ssh your-vps-username@your-vps-ip

# Navigate to DumbCrawler directory
cd /path/to/DumbCrawler

# Edit the .env file
nano .env
```

### Update the `.env` file with these values:

```bash
# Supabase Configuration (same as before)
VITE_SUPABASE_URL=https://dkxxtpgvkhlymqezkucq.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRreHh0cGd2a2hseW1xZXprdWNxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQyMDAxNTEsImV4cCI6MjA3OTc3NjE1MX0.TicF7p6G-FlWSElntKB-iFNJ-1gGqXbkLMQ0osFhd2s

# IMPORTANT: Update this line with your production API URL
API_URL=https://delorme-os2.tommy-260.workers.dev
```

### Restart the Docker container:

```bash
# Stop the current container
docker-compose down

# Start with updated configuration
docker-compose up -d

# Check logs to verify it's working
docker-compose logs -f dumbcrawler
```

You should see:
```
[2025-12-11 XX:XX:XX] Crawler Watcher started
[2025-12-11 XX:XX:XX] API URL: https://delorme-os2.tommy-260.workers.dev
[2025-12-11 XX:XX:XX] Polling interval: 5s
[2025-12-11 XX:XX:XX] Waiting for pending jobs...
```

---

## ✅ Verification Steps

### 1. Test your deployed app:
Visit: https://delorme-os2.tommy-260.workers.dev

### 2. Test a crawl job:
1. Go to your app → Projects → Select a project
2. Start a new crawl job
3. Watch the DumbCrawler logs on your VPS
4. The crawler should pick up the job and start crawling!

### 3. Check the logs:
```bash
# On your VPS
docker-compose logs -f dumbcrawler
```

You should see the crawler processing jobs.

---

## 🔄 Future Deployments

To deploy updates to your app in the future:

```bash
# In the user-application directory
cd delorme-os2/apps/user-application

# Build and deploy
pnpm run deploy
```

That's it! Wrangler will handle everything.

---

## 🌐 Custom Domain (Optional)

If you want to use a custom domain instead of `delorme-os2.tommy-260.workers.dev`:

1. Go to Cloudflare Dashboard → Workers & Pages
2. Click on `delorme-os2`
3. Go to Settings → Domains & Routes
4. Click "Add" and enter your custom domain
5. Update the DumbCrawler `.env` file with your custom domain

---

## 📊 Monitoring

- **Cloudflare Dashboard**: https://dash.cloudflare.com
  - View worker logs
  - Monitor requests and errors
  - Check performance metrics

- **Supabase Dashboard**: https://supabase.com/dashboard
  - View database tables
  - Monitor crawl jobs
  - Check crawler data

---

## 🐛 Troubleshooting

### If the crawler isn't picking up jobs:

1. **Check VPS Docker logs:**
   ```bash
   docker-compose logs -f dumbcrawler
   ```

2. **Verify API_URL is correct:**
   ```bash
   docker-compose exec dumbcrawler env | grep API_URL
   ```
   Should show: `API_URL=https://delorme-os2.tommy-260.workers.dev`

3. **Test API connectivity from VPS:**
   ```bash
   curl https://delorme-os2.tommy-260.workers.dev
   ```

4. **Restart the crawler:**
   ```bash
   docker-compose restart dumbcrawler
   ```

### If you see database connection errors:

The DATABASE_URL secret is already set. If you need to update it:

```bash
cd delorme-os2/apps/user-application
echo "your-new-database-url" | pnpx wrangler secret put DATABASE_URL
```

---

## 🎉 You're All Set!

Your delorme-os2 app is now:
✅ Deployed to Cloudflare Workers
✅ Connected to Supabase
✅ Ready to receive crawl jobs

Next time you start a crawl, the DumbCrawler on your VPS will automatically pick it up and process it!
