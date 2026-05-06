import asyncio
import logging
from contextlib import suppress

from app.core.config import get_settings
from app.db.database import AsyncSessionLocal
from app.services.claim_service import (
    cleanup_expired_idempotency_keys,
    process_next_queue_job,
)
from app.services.audit_service import purge_expired_audit_logs

logger = logging.getLogger(__name__)
settings = get_settings()


class QueueWorker:
    def __init__(self):
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()

    async def start(self):
        if not settings.worker_enabled:
            logger.info("Queue worker disabled by configuration.")
            return
        if self._task and not self._task.done():
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run(), name="claimiq-queue-worker")
        logger.info("Queue worker started.")

    async def stop(self):
        if not self._task:
            return
        self._stop_event.set()
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task
        logger.info("Queue worker stopped.")

    async def _run(self):
        cleanup_every = 60
        tick = 0
        while not self._stop_event.is_set():
            try:
                async with AsyncSessionLocal() as db:
                    worked = await process_next_queue_job(db)
                if tick % cleanup_every == 0:
                    async with AsyncSessionLocal() as db:
                        await cleanup_expired_idempotency_keys(db)
                    async with AsyncSessionLocal() as db:
                        await purge_expired_audit_logs(db)
                tick += 1
                if not worked:
                    await asyncio.sleep(settings.worker_poll_interval_seconds)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Queue worker loop iteration failed.")
                await asyncio.sleep(settings.worker_poll_interval_seconds)
