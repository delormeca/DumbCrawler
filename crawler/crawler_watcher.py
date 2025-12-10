#!/usr/bin/env python3
"""
Crawler Watcher Service - Automatically runs crawl jobs when they're created.

This service polls the database for pending crawl jobs and automatically
starts the DumbCrawler for each one.

Usage:
    python crawler_watcher.py --api-url "http://localhost:3001"

The watcher will:
1. Poll the Supabase database for pending jobs every 5 seconds
2. When a pending job is found, start the crawler
3. Mark the job as "running" to prevent duplicate runs
4. Continue monitoring for new jobs
"""

import argparse
import sys
import os
import time
import json
import subprocess
import threading
from datetime import datetime, timezone

# Add the scrapy_app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scrapy_app'))

try:
    from supabase import create_client, Client
except ImportError:
    print("Error: supabase package not installed. Run: pip install supabase")
    sys.exit(1)


class CrawlerWatcher:
    def __init__(self, supabase_url: str, supabase_key: str, api_url: str):
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.api_url = api_url
        self.running_jobs = set()  # Track currently running jobs
        self.poll_interval = 5  # seconds

    def get_pending_jobs(self) -> list:
        """Fetch all pending crawl jobs from the database."""
        try:
            response = self.supabase.table("crawl_jobs") \
                .select("id, project_id, status, created_at") \
                .eq("status", "pending") \
                .order("created_at", desc=False) \
                .execute()
            return response.data or []
        except Exception as e:
            print(f"[{self._timestamp()}] Error fetching pending jobs: {e}")
            return []

    def mark_job_running(self, job_id: str) -> bool:
        """Mark a job as running to prevent duplicate processing."""
        try:
            self.supabase.table("crawl_jobs") \
                .update({"status": "running", "started_at": datetime.now(timezone.utc).isoformat()}) \
                .eq("id", job_id) \
                .eq("status", "pending") \
                .execute()
            return True
        except Exception as e:
            print(f"[{self._timestamp()}] Error marking job {job_id} as running: {e}")
            return False

    def run_crawler(self, job_id: str):
        """Run the DumbCrawler for a specific job."""
        print(f"[{self._timestamp()}] Starting crawler for job: {job_id}")

        try:
            # Get the directory where this script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            crawler_script = os.path.join(script_dir, "run_crawl_job.py")

            # Run the crawler as a subprocess
            process = subprocess.Popen(
                [
                    sys.executable,
                    crawler_script,
                    "--job-id", job_id,
                    "--api-url", self.api_url,
                    "--log-level", "INFO"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=script_dir
            )

            # Stream output in real-time
            for line in process.stdout:
                print(f"  [{job_id[:8]}] {line.rstrip()}")

            process.wait()

            if process.returncode == 0:
                print(f"[{self._timestamp()}] Crawler completed successfully for job: {job_id}")
            else:
                print(f"[{self._timestamp()}] Crawler failed for job: {job_id} (exit code: {process.returncode})")

        except Exception as e:
            print(f"[{self._timestamp()}] Error running crawler for job {job_id}: {e}")
        finally:
            self.running_jobs.discard(job_id)

    def process_job(self, job: dict):
        """Process a single pending job."""
        job_id = job["id"]

        # Skip if already running
        if job_id in self.running_jobs:
            return

        # Mark as running in our set
        self.running_jobs.add(job_id)

        # Mark as running in database
        if not self.mark_job_running(job_id):
            self.running_jobs.discard(job_id)
            return

        # Run crawler in a separate thread
        thread = threading.Thread(target=self.run_crawler, args=(job_id,))
        thread.daemon = True
        thread.start()

    def _timestamp(self) -> str:
        """Get current timestamp for logging."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def run(self):
        """Main loop - poll for pending jobs and process them."""
        print(f"[{self._timestamp()}] Crawler Watcher started", flush=True)
        print(f"[{self._timestamp()}] API URL: {self.api_url}", flush=True)
        print(f"[{self._timestamp()}] Polling interval: {self.poll_interval}s", flush=True)
        print(f"[{self._timestamp()}] Waiting for pending jobs...", flush=True)
        print("-" * 60, flush=True)

        while True:
            try:
                pending_jobs = self.get_pending_jobs()

                for job in pending_jobs:
                    self.process_job(job)

                time.sleep(self.poll_interval)

            except KeyboardInterrupt:
                print(f"\n[{self._timestamp()}] Shutting down...")
                break
            except Exception as e:
                print(f"[{self._timestamp()}] Error in main loop: {e}")
                time.sleep(self.poll_interval)


def main():
    parser = argparse.ArgumentParser(
        description="Crawler Watcher - Automatically runs pending crawl jobs"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:3001",
        help="Base URL for the SaaS API (default: http://localhost:3001)"
    )
    parser.add_argument(
        "--supabase-url",
        type=str,
        default=os.environ.get("VITE_SUPABASE_URL", ""),
        help="Supabase project URL"
    )
    parser.add_argument(
        "--supabase-key",
        type=str,
        default=os.environ.get("VITE_SUPABASE_ANON_KEY", ""),
        help="Supabase anon key"
    )

    args = parser.parse_args()

    # Try to load from .env file if not provided
    if not args.supabase_url or not args.supabase_key:
        env_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "delorme-os2", "apps", "user-application", ".env"
        )
        if os.path.exists(env_path):
            print(f"Loading environment from: {env_path}")
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        if key == "VITE_SUPABASE_URL" and not args.supabase_url:
                            args.supabase_url = value
                        elif key == "VITE_SUPABASE_ANON_KEY" and not args.supabase_key:
                            args.supabase_key = value

    if not args.supabase_url or not args.supabase_key:
        print("Error: Supabase URL and key are required.")
        print("Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY environment variables")
        print("or use --supabase-url and --supabase-key arguments")
        sys.exit(1)

    watcher = CrawlerWatcher(
        supabase_url=args.supabase_url,
        supabase_key=args.supabase_key,
        api_url=args.api_url
    )
    watcher.run()


if __name__ == "__main__":
    main()
