#!/bin/bash
# DumbCrawler Production Deployment Script
# Run this on your VPS to deploy the crawler

set -e  # Exit on error

echo "=========================================="
echo "DumbCrawler Production Deployment"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use: sudo bash PRODUCTION_DEPLOY.sh)"
  exit 1
fi

# Step 1: Check Docker is installed
echo ""
echo "[1/6] Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi
docker --version

# Step 2: Check .env file exists
echo ""
echo "[2/6] Checking environment configuration..."
if [ ! -f .env ]; then
    echo "Creating .env from template..."
    cp .env.production .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and update the API_URL"
    echo "Run: nano .env"
    echo "Update API_URL to your live app URL, then run this script again."
    exit 1
fi

# Verify API_URL is set
if grep -q "your-app-url-here" .env; then
    echo "❌ ERROR: API_URL not configured in .env"
    echo "Please edit .env and set your live app URL:"
    echo "  nano .env"
    exit 1
fi

echo "✓ Environment configured"

# Step 3: Stop any existing crawler
echo ""
echo "[3/6] Stopping any existing crawler..."
docker compose -f docker-compose.production.yml down 2>/dev/null || true

# Step 4: Build the image
echo ""
echo "[4/6] Building Docker image (this may take 5-10 minutes)..."
docker compose -f docker-compose.production.yml build --no-cache

# Step 5: Start the crawler
echo ""
echo "[5/6] Starting DumbCrawler..."
docker compose -f docker-compose.production.yml up -d

# Step 6: Show status
echo ""
echo "[6/6] Verifying deployment..."
sleep 5
docker compose -f docker-compose.production.yml ps
echo ""
docker compose -f docker-compose.production.yml logs --tail=20

echo ""
echo "=========================================="
echo "✓ Deployment Complete!"
echo "=========================================="
echo ""
echo "Crawler is now running and watching for jobs in Supabase."
echo ""
echo "Management commands:"
echo "  View logs:    docker compose -f docker-compose.production.yml logs -f"
echo "  Restart:      docker compose -f docker-compose.production.yml restart"
echo "  Stop:         docker compose -f docker-compose.production.yml down"
echo "  Status:       docker compose -f docker-compose.production.yml ps"
echo ""
echo "API Endpoints (if port 8080 is exposed):"
echo "  Health:       curl http://localhost:8080/health"
echo "  List jobs:    curl http://localhost:8080/jobs"
echo ""
echo "The crawler will automatically:"
echo "  ✓ Poll Supabase for pending jobs every 5 seconds"
echo "  ✓ Start crawling when jobs are found"
echo "  ✓ Retry failed jobs with exponential backoff"
echo "  ✓ Restart automatically if it crashes"
echo ""
