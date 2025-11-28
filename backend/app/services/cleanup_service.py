"""
Background cleanup service for expired tokens.

This module provides functions to clean up expired authentication tokens
from the database. Can be run as:
1. Scheduled task (cron job)
2. FastAPI background task
3. Celery task
4. Manual cleanup script
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.services import token_service

logger = logging.getLogger(__name__)


async def cleanup_expired_tokens(db: AsyncSession) -> int:
    """
    Remove expired tokens from database.

    This function should be called periodically to prevent database bloat
    from accumulating expired tokens. Recommended schedule: once per hour
    or once per day depending on token volume.

    Args:
        db: Database session

    Returns:
        int: Number of tokens deleted

    Example:
        >>> deleted = await cleanup_expired_tokens(db)
        >>> logger.info(f"Cleaned up {deleted} expired tokens")

    Usage as scheduled task:
        # In main.py or separate script
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            cleanup_expired_tokens,
            'interval',
            hours=1,
            args=[db]
        )
        scheduler.start()

    Usage as FastAPI background task:
        from fastapi import BackgroundTasks

        @app.on_event("startup")
        async def startup_event():
            background_tasks.add_task(periodic_cleanup)
    """
    logger.info("Starting expired token cleanup")

    try:
        deleted_count = await token_service.cleanup_expired_tokens(db)
        logger.info(f"Successfully cleaned up {deleted_count} expired tokens")
        return deleted_count

    except Exception as e:
        logger.error(f"Error during token cleanup: {str(e)}", exc_info=True)
        raise
