"""Local path management and cleanup."""

from __future__ import annotations

import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .models import JobState


def get_jobs_dir(working_dir: str) -> Path:
    """Get the jobs base directory."""
    return Path(working_dir)


def list_jobs(
    working_dir: str,
    status: str | None = None,
) -> list[JobState]:
    """List all jobs, optionally filtered by status."""
    jobs_dir = Path(working_dir)
    if not jobs_dir.exists():
        return []

    jobs = []
    for job_dir in sorted(jobs_dir.iterdir()):
        state_file = job_dir / "job_state.json"
        if state_file.exists():
            try:
                job = JobState.load(str(job_dir))
                if status is None or _job_has_status(job, status):
                    jobs.append(job)
            except Exception:
                continue
    return jobs


def get_latest_job(working_dir: str) -> JobState | None:
    """Get the most recently created job."""
    jobs = list_jobs(working_dir)
    if not jobs:
        return None
    return max(jobs, key=lambda j: j.created_at)


def cleanup_jobs(working_dir: str, older_than_days: int = 7) -> int:
    """Delete completed jobs older than the specified age. Returns count deleted."""
    jobs_dir = Path(working_dir)
    if not jobs_dir.exists():
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
    deleted = 0

    for job_dir in list(jobs_dir.iterdir()):
        state_file = job_dir / "job_state.json"
        if not state_file.exists():
            continue
        try:
            job = JobState.load(str(job_dir))
            if job.created_at < cutoff and _job_has_status(job, "completed"):
                shutil.rmtree(job_dir)
                deleted += 1
        except Exception:
            continue

    return deleted


def _job_has_status(job: JobState, status: str) -> str:
    """Check if a job matches the given status filter."""
    statuses = {s.status.value for s in job.stages.values()}
    if status == "completed":
        return all(s == "completed" or s == "skipped" for s in statuses)
    elif status == "failed":
        return "failed" in statuses
    elif status == "running":
        return "running" in statuses
    return True
