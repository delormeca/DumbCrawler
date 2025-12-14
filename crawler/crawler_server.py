#!/usr/bin/env python3
"""
Crawler Server - REST API for managing crawl jobs.

This server exposes HTTP endpoints for:
- Spawning new crawl jobs
- Pausing/resuming running jobs
- Killing jobs
- Getting job status
- Automatic retry of failed jobs

Usage:
    python crawler_server.py --port 8080

Endpoints:
    POST /spawn          - Start a new crawl job
    POST /pause/:pid     - Pause a running job
    POST /resume/:pid    - Resume a paused job
    POST /kill/:pid      - Kill a running job
    GET  /status/:pid    - Get job status
    GET  /jobs           - List all jobs
    GET  /health         - Health check
"""

import argparse
import sys
import os
import json
import signal
import subprocess
import threading
import time
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Optional, Any
import traceback

# Add the scrapy_app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scrapy_app'))

try:
    from supabase import create_client, Client
except ImportError:
    print("Error: supabase package not installed. Run: pip install supabase")
    sys.exit(1)


class ProcessManager:
    """Manages crawler subprocesses with pause/resume/kill capabilities."""

    def __init__(self):
        self.processes: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()

    def spawn(self, job_id: str, api_url: str, log_level: str = "INFO") -> Dict[str, Any]:
        """Spawn a new crawler process."""
        with self.lock:
            if job_id in self.processes:
                return {"error": f"Job {job_id} is already running", "status": "error"}

            script_dir = os.path.dirname(os.path.abspath(__file__))
            crawler_script = os.path.join(script_dir, "run_crawl_job.py")

            try:
                # Copy environment and ensure PATH is properly set for Playwright
                env = os.environ.copy()

                process = subprocess.Popen(
                    [
                        sys.executable,
                        crawler_script,
                        "--job-id", job_id,
                        "--api-url", api_url,
                        "--log-level", log_level
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=script_dir,
                    env=env,  # Pass full environment for Playwright/Chromium
                    # On Windows, we need to use different flags
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
                )

                process_info = {
                    "job_id": job_id,
                    "pid": process.pid,
                    "process": process,
                    "status": "running",
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "paused_at": None,
                    "output_lines": [],
                }

                self.processes[job_id] = process_info

                # Start output reader thread
                reader_thread = threading.Thread(
                    target=self._read_output,
                    args=(job_id, process),
                    daemon=True
                )
                reader_thread.start()

                return {
                    "job_id": job_id,
                    "pid": process.pid,
                    "status": "running",
                    "message": f"Crawler started for job {job_id}"
                }

            except Exception as e:
                return {"error": str(e), "status": "error"}

    def _read_output(self, job_id: str, process: subprocess.Popen):
        """Read and store process output."""
        try:
            for line in process.stdout:
                line = line.rstrip()
                with self.lock:
                    if job_id in self.processes:
                        # Keep last 100 lines
                        self.processes[job_id]["output_lines"].append(line)
                        if len(self.processes[job_id]["output_lines"]) > 100:
                            self.processes[job_id]["output_lines"].pop(0)
                print(f"[{job_id[:8]}] {line}")

            # Process finished
            process.wait()
            with self.lock:
                if job_id in self.processes:
                    exit_code = process.returncode
                    self.processes[job_id]["status"] = "completed" if exit_code == 0 else "failed"
                    self.processes[job_id]["exit_code"] = exit_code
                    self.processes[job_id]["finished_at"] = datetime.now(timezone.utc).isoformat()

        except Exception as e:
            print(f"Error reading output for {job_id}: {e}")

    def pause(self, job_id: str) -> Dict[str, Any]:
        """Pause a running crawler process."""
        with self.lock:
            if job_id not in self.processes:
                return {"error": f"Job {job_id} not found", "status": "error"}

            proc_info = self.processes[job_id]
            if proc_info["status"] != "running":
                return {"error": f"Job {job_id} is not running (status: {proc_info['status']})", "status": "error"}

            try:
                process = proc_info["process"]
                if os.name == 'nt':
                    # Windows: Send CTRL+BREAK
                    os.kill(process.pid, signal.CTRL_BREAK_EVENT)
                else:
                    # Unix: Send SIGSTOP
                    os.kill(process.pid, signal.SIGSTOP)

                proc_info["status"] = "paused"
                proc_info["paused_at"] = datetime.now(timezone.utc).isoformat()

                return {
                    "job_id": job_id,
                    "pid": process.pid,
                    "status": "paused",
                    "message": f"Job {job_id} paused"
                }

            except Exception as e:
                return {"error": str(e), "status": "error"}

    def resume(self, job_id: str) -> Dict[str, Any]:
        """Resume a paused crawler process."""
        with self.lock:
            if job_id not in self.processes:
                return {"error": f"Job {job_id} not found", "status": "error"}

            proc_info = self.processes[job_id]
            if proc_info["status"] != "paused":
                return {"error": f"Job {job_id} is not paused (status: {proc_info['status']})", "status": "error"}

            try:
                process = proc_info["process"]
                if os.name == 'nt':
                    # Windows: Resume is more complex, may need different approach
                    # For now, we'll mark as running
                    pass
                else:
                    # Unix: Send SIGCONT
                    os.kill(process.pid, signal.SIGCONT)

                proc_info["status"] = "running"
                proc_info["paused_at"] = None

                return {
                    "job_id": job_id,
                    "pid": process.pid,
                    "status": "running",
                    "message": f"Job {job_id} resumed"
                }

            except Exception as e:
                return {"error": str(e), "status": "error"}

    def kill(self, job_id: str) -> Dict[str, Any]:
        """Kill a running or paused crawler process."""
        with self.lock:
            if job_id not in self.processes:
                return {"error": f"Job {job_id} not found", "status": "error"}

            proc_info = self.processes[job_id]
            if proc_info["status"] in ["completed", "failed", "killed"]:
                return {"error": f"Job {job_id} already finished (status: {proc_info['status']})", "status": "error"}

            try:
                process = proc_info["process"]
                process.terminate()
                process.wait(timeout=5)

                proc_info["status"] = "killed"
                proc_info["finished_at"] = datetime.now(timezone.utc).isoformat()

                return {
                    "job_id": job_id,
                    "pid": process.pid,
                    "status": "killed",
                    "message": f"Job {job_id} killed"
                }

            except subprocess.TimeoutExpired:
                process.kill()
                proc_info["status"] = "killed"
                return {
                    "job_id": job_id,
                    "status": "killed",
                    "message": f"Job {job_id} force killed"
                }
            except Exception as e:
                return {"error": str(e), "status": "error"}

    def get_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of a crawler process."""
        with self.lock:
            if job_id not in self.processes:
                return {"error": f"Job {job_id} not found", "status": "error"}

            proc_info = self.processes[job_id]

            # Check if process is still running
            if proc_info["status"] == "running":
                if proc_info["process"].poll() is not None:
                    # Process finished
                    exit_code = proc_info["process"].returncode
                    proc_info["status"] = "completed" if exit_code == 0 else "failed"
                    proc_info["exit_code"] = exit_code
                    proc_info["finished_at"] = datetime.now(timezone.utc).isoformat()

            return {
                "job_id": proc_info["job_id"],
                "pid": proc_info["pid"],
                "status": proc_info["status"],
                "started_at": proc_info["started_at"],
                "paused_at": proc_info.get("paused_at"),
                "finished_at": proc_info.get("finished_at"),
                "exit_code": proc_info.get("exit_code"),
                "recent_output": proc_info["output_lines"][-10:] if proc_info["output_lines"] else []
            }

    def list_jobs(self) -> list:
        """List all jobs with their status."""
        with self.lock:
            return [
                {
                    "job_id": info["job_id"],
                    "pid": info["pid"],
                    "status": info["status"],
                    "started_at": info["started_at"],
                }
                for info in self.processes.values()
            ]

    def cleanup_finished(self):
        """Remove finished jobs from memory (keep last 50)."""
        with self.lock:
            finished = [
                jid for jid, info in self.processes.items()
                if info["status"] in ["completed", "failed", "killed"]
            ]
            if len(finished) > 50:
                # Remove oldest finished jobs
                finished.sort(key=lambda jid: self.processes[jid].get("finished_at", ""))
                for jid in finished[:-50]:
                    del self.processes[jid]


class RetryManager:
    """Manages automatic retry of failed jobs."""

    def __init__(self, supabase: Client, process_manager: ProcessManager, api_url: str):
        self.supabase = supabase
        self.process_manager = process_manager
        self.api_url = api_url
        self.max_retries = 3
        self.running = False
        self.check_interval = 30  # seconds
        self.disabled = False
        self.disable_reason = None

    def start(self):
        """Start the retry manager background thread."""
        self.running = True
        thread = threading.Thread(target=self._retry_loop, daemon=True)
        thread.start()

    def stop(self):
        """Stop the retry manager."""
        self.running = False

    def _retry_loop(self):
        """Background loop that checks for failed jobs to retry."""
        while self.running:
            if self.disabled:
                # Already disabled, just sleep
                time.sleep(self.check_interval)
                continue
            try:
                self._check_and_retry_jobs()
            except Exception as e:
                error_str = str(e)
                # Check if this is a missing column error - disable retry manager
                if "retry_count does not exist" in error_str or "42703" in error_str:
                    self.disabled = True
                    self.disable_reason = "retry_count column missing"
                    print(f"[RetryManager] Disabled - retry_count column not found in database. "
                          f"Retry functionality requires database migration.")
                else:
                    print(f"Error in retry loop: {e}")
            time.sleep(self.check_interval)

    def _check_and_retry_jobs(self):
        """Check for failed jobs that should be retried."""
        # Fetch failed jobs with retry_count < max_retries
        response = self.supabase.table("crawl_jobs") \
            .select("id, project_id, status, retry_count, failed_at") \
            .eq("status", "failed") \
            .lt("retry_count", self.max_retries) \
            .execute()

        jobs = response.data or []

        for job in jobs:
            job_id = job["id"]
            retry_count = job.get("retry_count", 0)

            # Calculate backoff: 2^retry_count minutes
            backoff_minutes = 2 ** retry_count
            failed_at = job.get("failed_at")

            if failed_at:
                # Check if enough time has passed
                failed_time = datetime.fromisoformat(failed_at.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                elapsed_minutes = (now - failed_time).total_seconds() / 60

                if elapsed_minutes >= backoff_minutes:
                    print(f"Retrying job {job_id} (attempt {retry_count + 1}/{self.max_retries})")
                    self._retry_job(job_id, retry_count + 1)

    def _retry_job(self, job_id: str, retry_count: int):
        """Retry a failed job."""
        try:
            # Update job status to pending and increment retry count
            self.supabase.table("crawl_jobs") \
                .update({
                    "status": "pending",
                    "retry_count": retry_count,
                    "started_at": None,
                    "completed_at": None,
                    "failed_at": None,
                }) \
                .eq("id", job_id) \
                .execute()

            # Spawn the crawler
            result = self.process_manager.spawn(job_id, self.api_url)
            if "error" in result:
                print(f"Failed to spawn retry for {job_id}: {result['error']}")

        except Exception as e:
            print(f"Error retrying job {job_id}: {e}")


class JobWatcher:
    """Watches for pending jobs and spawns crawlers (replaces crawler_watcher.py polling)."""

    def __init__(self, supabase: Client, process_manager: ProcessManager, api_url: str):
        self.supabase = supabase
        self.process_manager = process_manager
        self.api_url = api_url
        self.running = False
        self.poll_interval = 5  # seconds
        self.connection_error_shown = False  # Track if we've shown the connection error
        self.consecutive_errors = 0

    def start(self):
        """Start the job watcher background thread."""
        self.running = True
        thread = threading.Thread(target=self._watch_loop, daemon=True)
        thread.start()

    def stop(self):
        """Stop the job watcher."""
        self.running = False

    def _watch_loop(self):
        """Background loop that polls for pending jobs."""
        print(f"[JobWatcher] Started - polling every {self.poll_interval}s")
        while self.running:
            try:
                self._process_pending_jobs()
                # Reset error state on success
                if self.connection_error_shown:
                    print("[JobWatcher] Connection restored - resuming normal operation")
                    self.connection_error_shown = False
                self.consecutive_errors = 0
            except Exception as e:
                self._handle_error(e)
            time.sleep(self.poll_interval)

    def _handle_error(self, e: Exception):
        """Handle errors with rate limiting to avoid log spam."""
        error_str = str(e)
        self.consecutive_errors += 1

        # Detect Supabase/Cloudflare connection errors
        is_connection_error = any(x in error_str for x in [
            "500", "502", "503", "504",  # Server errors
            "cloudflare", "Cloudflare",
            "Internal server error",
            "Connection refused",
            "Connection reset",
            "timed out",
            "JSON could not be generated",
        ])

        if is_connection_error:
            if not self.connection_error_shown:
                print("[JobWatcher] Supabase temporarily unavailable - will keep trying in background")
                self.connection_error_shown = True
            # After many failures, remind user periodically (every 60 attempts = ~5 min)
            elif self.consecutive_errors % 60 == 0:
                print(f"[JobWatcher] Still waiting for Supabase connection ({self.consecutive_errors} attempts)")
        else:
            # For other errors, always print
            print(f"[JobWatcher] Error processing pending jobs: {e}")

    def _process_pending_jobs(self):
        """Check for and process pending jobs."""
        response = self.supabase.table("crawl_jobs") \
            .select("id, project_id, status, created_at") \
            .eq("status", "pending") \
            .order("created_at", desc=False) \
            .execute()

        jobs = response.data or []

        for job in jobs:
            job_id = job["id"]

            # Mark as running in database
            self.supabase.table("crawl_jobs") \
                .update({
                    "status": "running",
                    "started_at": datetime.now(timezone.utc).isoformat()
                }) \
                .eq("id", job_id) \
                .eq("status", "pending") \
                .execute()

            # Spawn the crawler
            result = self.process_manager.spawn(job_id, self.api_url)
            if "error" in result:
                print(f"Failed to spawn {job_id}: {result['error']}")


class CrawlerAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for crawler API."""

    process_manager: ProcessManager = None
    api_url: str = None
    api_key: str = None  # API key for authentication

    def log_message(self, format, *args):
        """Custom log format."""
        print(f"[API] {args[0]}")

    def _check_auth(self) -> bool:
        """Check if request has valid API key. Returns True if authenticated."""
        if not self.api_key:
            # No API key configured - allow all requests
            return True

        # Get Authorization header
        auth_header = self.headers.get('Authorization', '')

        # Check for Bearer token
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            return token == self.api_key

        return False

    def _send_auth_error(self):
        """Send 401 Unauthorized response."""
        self._send_json({
            "error": "Unauthorized",
            "message": "Valid API key required. Use: Authorization: Bearer YOUR_API_KEY"
        }, 401)

    def _send_json(self, data: dict, status: int = 200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _read_json(self) -> dict:
        """Read JSON from request body."""
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length:
            body = self.rfile.read(content_length)
            return json.loads(body.decode())
        return {}

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path

        # Health check is always public (no auth required)
        if path == '/health':
            self._send_json({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()})
            return

        # All other endpoints require authentication
        if not self._check_auth():
            self._send_auth_error()
            return

        if path == '/jobs':
            jobs = self.process_manager.list_jobs()
            self._send_json({"jobs": jobs})

        elif path.startswith('/status/'):
            job_id = path.split('/status/')[-1]
            result = self.process_manager.get_status(job_id)
            status = 200 if "error" not in result else 404
            self._send_json(result, status)

        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        """Handle POST requests."""
        # All POST endpoints require authentication
        if not self._check_auth():
            self._send_auth_error()
            return

        parsed = urlparse(self.path)
        path = parsed.path

        if path == '/spawn':
            data = self._read_json()
            job_id = data.get('job_id')
            log_level = data.get('log_level', 'INFO')

            if not job_id:
                self._send_json({"error": "job_id is required"}, 400)
                return

            result = self.process_manager.spawn(job_id, self.api_url, log_level)
            status = 200 if "error" not in result else 400
            self._send_json(result, status)

        elif path.startswith('/pause/'):
            job_id = path.split('/pause/')[-1]
            result = self.process_manager.pause(job_id)
            status = 200 if "error" not in result else 400
            self._send_json(result, status)

        elif path.startswith('/resume/'):
            job_id = path.split('/resume/')[-1]
            result = self.process_manager.resume(job_id)
            status = 200 if "error" not in result else 400
            self._send_json(result, status)

        elif path.startswith('/kill/'):
            job_id = path.split('/kill/')[-1]
            result = self.process_manager.kill(job_id)
            status = 200 if "error" not in result else 400
            self._send_json(result, status)

        else:
            self._send_json({"error": "Not found"}, 404)


def main():
    parser = argparse.ArgumentParser(
        description="Crawler Server - REST API for managing crawl jobs"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to listen on (default: 8080)"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:3000",
        help="Base URL for the SaaS API (default: http://localhost:3000)"
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
    parser.add_argument(
        "--no-watcher",
        action="store_true",
        help="Disable automatic job watching (API-only mode)"
    )
    parser.add_argument(
        "--no-retry",
        action="store_true",
        help="Disable automatic retry of failed jobs"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=os.environ.get("API_KEY", ""),
        help="API key for authentication (optional, from API_KEY env var)"
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
        sys.exit(1)

    # Initialize components
    supabase = create_client(args.supabase_url, args.supabase_key)
    process_manager = ProcessManager()

    # Set class variables for handler
    CrawlerAPIHandler.process_manager = process_manager
    CrawlerAPIHandler.api_url = args.api_url
    CrawlerAPIHandler.api_key = args.api_key if args.api_key else None

    # Start job watcher if enabled
    if not args.no_watcher:
        job_watcher = JobWatcher(supabase, process_manager, args.api_url)
        job_watcher.start()
        print(f"Job watcher enabled - polling for pending jobs")

    # Start retry manager if enabled
    if not args.no_retry:
        retry_manager = RetryManager(supabase, process_manager, args.api_url)
        retry_manager.start()
        print(f"Retry manager enabled - max {retry_manager.max_retries} retries with exponential backoff")

    # Start HTTP server
    server = HTTPServer(('0.0.0.0', args.port), CrawlerAPIHandler)
    print(f"=" * 60)
    print(f"Crawler Server started on port {args.port}")
    print(f"API URL: {args.api_url}")
    if args.api_key:
        print(f"🔐 Authentication: ENABLED (API key required)")
    else:
        print(f"⚠️  Authentication: DISABLED (no API key configured)")
    print(f"=" * 60)
    print(f"Endpoints:")
    print(f"  GET  /health        - Health check")
    print(f"  GET  /jobs          - List all jobs")
    print(f"  GET  /status/:id    - Get job status")
    print(f"  POST /spawn         - Start a crawl job")
    print(f"  POST /pause/:id     - Pause a job")
    print(f"  POST /resume/:id    - Resume a job")
    print(f"  POST /kill/:id      - Kill a job")
    print(f"=" * 60)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
