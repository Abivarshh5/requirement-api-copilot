"""
In-memory sliding-window rate limiter.
10 requests per minute per IP address by default.
"""

import os
import time
from typing import Dict, List, Tuple


class RateLimiter:
    def __init__(self):
        self.limit = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
        self.window = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
        self._store: Dict[str, List[float]] = {}

    def check(self, ip: str) -> Tuple[bool, int]:
        """
        Check if the IP is within rate limits.
        Returns (allowed: bool, retry_after_seconds: int).
        """
        now = time.time()
        cutoff = now - self.window

        # Clean old entries
        if ip in self._store:
            self._store[ip] = [ts for ts in self._store[ip] if ts > cutoff]
        else:
            self._store[ip] = []

        if len(self._store[ip]) >= self.limit:
            oldest = min(self._store[ip])
            retry_after = int(self.window - (now - oldest)) + 1
            return False, max(retry_after, 1)

        # Record this request
        self._store[ip].append(now)
        return True, 0


rate_limiter = RateLimiter()
