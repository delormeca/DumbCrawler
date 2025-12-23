-- Reset stuck crawl job back to pending
-- This fixes jobs that were marked as "running" but never actually started by the crawler

UPDATE crawl_jobs
SET
  status = 'pending',
  started_at = NULL,
  external_job_id = NULL
WHERE
  id = 'c9b8da09-fca6-4fa1-83ae-da75a33a01ae'
  AND status = 'running'
  AND pages_crawled = 0
  AND external_job_id IS NULL;

-- Verify the update
SELECT id, status, pages_crawled, pages_queued, external_job_id, started_at
FROM crawl_jobs
WHERE id = 'c9b8da09-fca6-4fa1-83ae-da75a33a01ae';
