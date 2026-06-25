"""APScheduler wiring (blueprint/07). Off by default; enable via ENABLE_SCHEDULER=true.

Kept tiny + guarded so the TestClient/CI lifespan never starts background jobs.
3:30 PM IST daily pipeline, 3:45 PM IST exit checker (Asia/Kolkata).
"""
from __future__ import annotations

import logging

logger = logging.getLogger("scheduler")
_scheduler = None


def start_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger
    except Exception as e:  # apscheduler optional in minimal installs
        logger.warning("APScheduler unavailable (%s); jobs not scheduled", e)
        return

    from .daily_pipeline import run as daily_run
    from .exit_checker import run as exit_run

    _scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")
    _scheduler.add_job(daily_run, CronTrigger(hour=15, minute=30), id="daily_pipeline",
                       replace_existing=True, misfire_grace_time=3600)
    _scheduler.add_job(exit_run, CronTrigger(hour=15, minute=45), id="exit_checker",
                       replace_existing=True, misfire_grace_time=3600)
    _scheduler.start()
    logger.info("scheduler started: daily_pipeline 15:30 IST, exit_checker 15:45 IST")


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
