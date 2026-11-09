"""Small process-local rate limiter for authentication endpoints.

For multi-worker or multi-instance deployments, replace this with a shared
store (for example Redis) and configure trusted proxy IP handling.
"""

import math
import threading
import time
from collections import deque

from fastapi import HTTPException, Request

_attempts: dict[tuple[str, str], deque[float]] = {}
_lock = threading.Lock()
_checks = 0


def enforce_rate_limit(
    request: Request,
    *,
    scope: str,
    max_attempts: int,
    window_seconds: int,
) -> None:
    """Reject excessive requests from one client IP within a sliding window."""
    global _checks

    client_ip = request.client.host if request.client else "unknown"
    key = (scope, client_ip)
    now = time.monotonic()
    cutoff = now - window_seconds

    with _lock:
        bucket = _attempts.setdefault(key, deque())
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()

        if len(bucket) >= max_attempts:
            retry_after = max(1, math.ceil(window_seconds - (now - bucket[0])))
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Try again later.",
                headers={"Retry-After": str(retry_after)},
            )

        bucket.append(now)
        _checks += 1

        # Expire inactive client entries periodically so the map does not grow
        # forever when requests come from many different addresses.
        if _checks % 256 == 0:
            expired = [
                candidate
                for candidate, timestamps in _attempts.items()
                if not timestamps or timestamps[-1] <= cutoff
            ]
            for candidate in expired:
                _attempts.pop(candidate, None)
