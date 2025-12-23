# Security Documentation

## Overview

This document outlines the security measures implemented in DumbCrawler and the delorme-os2 application to protect against common vulnerabilities and attacks.

## Authentication & Authorization

### API Key Authentication

**Crawler Server** (`crawler_server.py`)
- All API endpoints (except `/health`) require Bearer token authentication
- API key must be at least 32 characters long for security
- Set via `API_KEY` environment variable
- Example header: `Authorization: Bearer <your-api-key>`

**Generating a Strong API Key:**
```bash
openssl rand -base64 32
```

**Failed Authentication Logging:**
- All failed authentication attempts are logged with:
  - Client IP address
  - Requested endpoint
  - Timestamp (ISO 8601 UTC)
  - Token preview (first 8 characters only, for security)
- Monitor logs for suspicious patterns (e.g., brute force attempts)
- Log pattern: `[AUTH FAIL] IP: {ip} | Endpoint: {path} | Token: {preview}... | Time: {timestamp}`

## CORS Policy

**Crawler API CORS Restrictions:**
- Cross-origin requests are restricted to allowed origins only
- Configure via `ALLOWED_ORIGINS` environment variable (comma-separated list)
- Default: `https://delorme-os2.tommy-260.workers.dev`
- Unauthorized origins will be blocked by the browser (no CORS header sent)

**Example Configuration:**
```bash
ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com
```

## SSRF Protection

### Sitemap URL Validation

**Frontend Validation** (`url-security.ts`)
- Validates sitemap URLs before submission
- Blocks:
  - Localhost addresses (127.x.x.x, ::1, localhost)
  - Private IP ranges (10.x.x.x, 192.168.x.x, 172.16-31.x.x)
  - Link-local addresses (169.254.x.x)
  - Cloud metadata endpoints (169.254.169.254)
- Requires HTTPS protocol only

**Backend Validation** (`crawler_spider.py`)
- Double-checks sitemap URLs before fetching (defense in depth)
- Performs DNS resolution to check if hostname resolves to private IP
- Prevents DNS rebinding attacks

**Blocked URL Examples:**
- `https://localhost/sitemap.xml`
- `https://10.0.0.1/sitemap.xml`
- `https://192.168.1.1/sitemap.xml`
- `https://169.254.169.254/latest/meta-data/` (AWS metadata)
- `http://example.com/sitemap.xml` (not HTTPS)

## DoS Protection

### Sitemap Crawl Limits

**Request Timeout:**
- All sitemap requests timeout after 30 seconds
- Prevents slowloris-style DoS attacks where server responds very slowly
- Configured via `SITEMAP_REQUEST_TIMEOUT` constant

**Recursion Depth Limit:**
- Maximum 5 levels of sitemap index recursion
- Prevents infinite loops from circular sitemap references
- Configured via `SITEMAP_MAX_RECURSION_DEPTH` constant
- Error logged when limit exceeded

**Total URL Limit:**
- Maximum 100,000 URLs extracted from all sitemaps
- Prevents memory exhaustion from massive sitemaps
- Configured via `SITEMAP_MAX_URLS` constant
- Progress logged every 1,000 URLs
- Crawl stops immediately when limit reached

### Job Creation Limits

**Maximum URLs Per Job:**
- Maximum 10,000 URLs per crawl job
- Prevents resource exhaustion from large job submissions
- Returns HTTP 400 error with counts if limit exceeded

**Request Size Limit:**
- Maximum 10MB request body size
- Prevents DoS via oversized payloads
- Returns HTTP 413 (Payload Too Large) if exceeded

## Credential Management

### Environment Variables

**Required Secrets:**
- `API_KEY` - Crawler API authentication key (min 32 chars)
- `VITE_SUPABASE_URL` - Supabase project URL
- `VITE_SUPABASE_ANON_KEY` - Supabase anonymous key
- `ALLOWED_ORIGINS` - Comma-separated list of allowed CORS origins

**Never Commit:**
- `.claude/settings.local.json` - Contains credential references
- `.env` files - Contains actual secrets
- `.hostinger-credentials.json` - VPS credentials
- `.LIVE_APP_CONFIG.md` - Live deployment details

**See `.gitignore` for complete exclusion list**

### SSH Access

**VPS Deployment Security:**
- Use SSH key-based authentication ONLY
- Password authentication should be disabled on VPS
- Never use `StrictHostKeyChecking=no` in production

**Generate SSH Key:**
```bash
ssh-keygen -t ed25519 -C "your-email@example.com"
```

**Add Public Key to VPS:**
```bash
ssh-copy-id user@vps-ip-address
```

**Disable Password Authentication (VPS `/etc/ssh/sshd_config`):**
```
PermitRootLogin prohibit-password
PasswordAuthentication no
```

Then restart SSH:
```bash
systemctl restart sshd
```

### Database Security (Supabase)

**Row Level Security (RLS):**
- MUST be enabled on all tables
- Anonymous key is public but protected by RLS policies
- Service key must NEVER be exposed to frontend

**RLS Policy Checklist:**
- ✅ `crawl_jobs` table - users can only access their own jobs
- ✅ `projects` table - users can only access their own projects
- ✅ `crawled_urls` table - users can only access URLs from their projects
- ✅ `url_data` table - users can only access data from their projects

## Error Handling & Logging

### Structured Error Logging

**API Endpoints** (`url-security.ts: logApiError()`)
- All API errors logged with structured context
- Includes:
  - Error type and message
  - Stack trace (server-side only, never sent to client)
  - Request context (endpoint, parameters)
  - Timestamp (ISO 8601)
- Log format: JSON object for easy parsing
- Client receives generic error message (no stack traces)

**Example Log Output:**
```json
{
  "type": "API_ERROR",
  "endpoint": "/api/crawl/start",
  "error": "Failed to validate sitemap URL",
  "stack": "Error: ...",
  "context": {
    "hasProjectId": true,
    "crawlType": "sitemap",
    "hasSitemapUrl": true
  },
  "timestamp": "2025-12-14T10:30:00.000Z"
}
```

## Security Monitoring

### What to Monitor

**Authentication Failures:**
- Log pattern: `[AUTH FAIL]`
- Alert threshold: >10 failures/minute from single IP
- Action: Investigate IP for suspicious activity, consider IP blocking

**SSRF Blocks:**
- Log pattern: `Sitemap URL failed security validation`
- Alert threshold: >5 blocks/hour
- Action: Review if legitimate users affected, check for attack patterns

**Job Timeouts:**
- Log pattern: `[TIMEOUT] Job .* stuck`
- Alert threshold: >3 timeouts/day
- Action: Investigate crawler stability, check VPS resources

**Sitemap Limits Hit:**
- Log pattern: `Sitemap URL limit reached` or `recursion depth limit`
- Alert threshold: Any occurrence
- Action: Review if limit too restrictive, check for malicious sitemaps

## Security Checklist

### Before Deploying to Production

- [ ] All API keys rotated and stored in environment variables
- [ ] API keys are at least 32 characters long
- [ ] VPS SSH password changed and key-based auth enabled
- [ ] Password authentication disabled on VPS (`/etc/ssh/sshd_config`)
- [ ] Supabase RLS policies reviewed and enabled on all tables
- [ ] `.claude/settings.local.json` added to `.gitignore`
- [ ] No credentials in git history (check with `git log --all -- .claude/settings.local.json`)
- [ ] CORS origins restricted to production domains
- [ ] All sitemap URLs validated for SSRF
- [ ] Request size limits enforced (10MB)
- [ ] Authentication failure logging enabled
- [ ] Job timeout monitoring active (if implemented)
- [ ] Error logging uses structured format
- [ ] Sensitive files excluded from git (`.env`, credentials, etc.)

### After Deployment

- [ ] Monitor authentication failure logs for first 48 hours
- [ ] Verify CORS restrictions working (unauthorized origins blocked)
- [ ] Test sitemap crawl with legitimate URL (should work)
- [ ] Test sitemap crawl with private IP URL (should reject)
- [ ] Check error logs for unexpected failures
- [ ] Verify health check endpoint accessible without auth
- [ ] Test API endpoints require authentication
- [ ] Confirm weak API key rejected on startup

## Incident Response

### If Credentials are Exposed

**Immediate Actions:**
1. Rotate exposed credentials immediately
2. Check access logs for unauthorized usage
3. Review git history for exposure timeline
4. Notify affected users if data breach occurred

**Supabase Anon Key Exposed:**
1. Review RLS policies (verify they're working)
2. Check Supabase logs for unauthorized queries
3. Rotate anon key in dashboard if RLS is weak
4. Update all environments with new key

**VPS SSH Credentials Exposed:**
1. Change root password immediately
2. Generate new SSH key pair
3. Remove old public key from `~/.ssh/authorized_keys`
4. Review VPS logs for unauthorized access
5. Check for backdoors or suspicious files

**API Key Exposed:**
1. Generate new 32+ character key
2. Update all deployment environments
3. Restart crawler server with new key
4. Monitor logs for failed auth attempts with old key

## Best Practices

### Development

1. **Never commit secrets** - Use `.gitignore` and environment variables
2. **Use strong keys** - Minimum 32 characters, cryptographically random
3. **Fail closed** - If validation fails, reject the request (don't allow)
4. **Defense in depth** - Validate inputs on both frontend and backend
5. **Log security events** - Authentication failures, SSRF blocks, limit hits
6. **Monitor logs** - Set up alerts for suspicious patterns

### Production

1. **Principle of least privilege** - Only grant necessary permissions
2. **Regular audits** - Review security logs and RLS policies
3. **Keep dependencies updated** - Apply security patches promptly
4. **Use HTTPS everywhere** - Never allow HTTP for sensitive operations
5. **Rate limiting** - Consider adding rate limits to prevent abuse
6. **Backup credentials** - Store securely in password manager

## Security Contacts

For security vulnerabilities, please report to:
- **GitHub Issues**: https://github.com/your-repo/issues (for non-critical issues)
- **Email**: security@yourdomain.com (for critical vulnerabilities)

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [SSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)
- [Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [Supabase Row Level Security](https://supabase.com/docs/guides/auth/row-level-security)
