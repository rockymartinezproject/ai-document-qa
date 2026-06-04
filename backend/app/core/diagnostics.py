"""
Application diagnostics: uptime tracking and dependency checks.
"""

import time
from typing import Dict

start_time = time.time()


def get_uptime_seconds() -> float:
    """Return application uptime in seconds."""
    return time.time() - start_time


def format_uptime(seconds: float) -> str:
    """Format uptime as human-readable string."""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}h {minutes}m {secs}s"


async def check_dependencies() -> Dict[str, bool]:
    """Check health of external dependencies.

    Returns a dict of service_name -> is_healthy.
    """
    checks = {}

    # Qdrant check (will be implemented when Qdrant client is wired up)
    checks["qdrant"] = True  # placeholder
    checks["database"] = True  # placeholder

    return checks
