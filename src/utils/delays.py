"""Anti-blocking delay utilities."""

import asyncio
import random

import structlog

logger = structlog.get_logger()


async def random_delay(min_seconds: float, max_seconds: float) -> None:
    """Apply a random delay between min and max seconds.

    This is used for anti-blocking between page requests.

    Args:
        min_seconds: Minimum delay in seconds
        max_seconds: Maximum delay in seconds
    """
    delay = random.uniform(min_seconds, max_seconds)
    logger.debug("applying_delay", seconds=round(delay, 2))
    await asyncio.sleep(delay)
