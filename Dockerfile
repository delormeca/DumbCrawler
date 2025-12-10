# DumbCrawler Docker Image
# Python-based Scrapy crawler with Playwright support

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .
COPY crawler/requirements.txt ./crawler/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r crawler/requirements.txt \
    && pip install --no-cache-dir supabase python-dotenv

# Install Playwright browsers (Chromium only to save space)
RUN pip install playwright \
    && playwright install chromium \
    && playwright install-deps chromium

# Copy application code
COPY . .

# Create output directory
RUN mkdir -p /app/crawler/output

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -f "crawler_watcher.py" || exit 1

# Default command - run the crawler watcher
CMD ["python", "crawler/crawler_watcher.py"]
