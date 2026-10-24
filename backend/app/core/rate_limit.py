"""
Safe Client IP Resolution and In-Memory Token Bucket Rate Limiting.

SECURITY ARCHITECTURE & SPOOFING MITIGATION:
1. Client IP Resolution:
   - Direct connection IP (`request.client.host`) is the single ground truth by default.
   - `X-Forwarded-For` / `X-Real-IP` headers are NEVER trusted unless `settings.TRUSTED_PROXIES`
     is explicitly configured with trusted upstream reverse proxy addresses / CIDRs.
   - When trusted proxies are active, IP resolution walks the `X-Forwarded-For` chain backwards
     (right-to-left) to extract the first non-trusted upstream IP address, preventing spoofing
     by malicious clients prepending fake IPs to the header.

DOCUMENTED ARCHITECTURAL LIMITATIONS:
- Process-Local Memory: Rate limits are held in the heap memory of the active Python process.
- Volatility: All quota state resets whenever the process or uvicorn worker restarts.
- Multi-Worker / Clustered Scale: When running multiple uvicorn worker processes (--workers N)
  or horizontal container replicas, each worker maintains an isolated token bucket. The effective
  request quota is multiplied by the number of active workers.

REDIS FOLLOW-UP & PRODUCTION ROADMAP:
- In multi-instance or high-availability production deployments, this in-memory implementation
  must be migrated to a distributed store (e.g., Redis using atomic EVAL Lua token bucket scripts)
  or enforced at the edge/ingress layer (NGINX `limit_req`, Cloudflare Rate Limiting, or AWS WAF).
"""

import math
import time
import logging
import ipaddress
import threading
from typing import Dict, List, Tuple, Optional
from fastapi import Request, HTTPException, status

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


def is_ip_trusted(ip_str: str, trusted_proxies: List[str]) -> bool:
    """
    Checks whether an IP address matches any trusted proxy IP or CIDR network.
    """
    if not ip_str or not trusted_proxies:
        return False

    clean_ip_str = ip_str.strip()
    # Support literal hostnames (e.g., testclient, localhost)
    if clean_ip_str in trusted_proxies:
        return True

    try:
        ip = ipaddress.ip_address(clean_ip_str)
    except ValueError:
        return False

    for trusted in trusted_proxies:
        trusted_clean = trusted.strip()
        if not trusted_clean:
            continue
        try:
            if "/" in trusted_clean:
                network = ipaddress.ip_network(trusted_clean, strict=False)
                if ip in network:
                    return True
            else:
                if ip == ipaddress.ip_address(trusted_clean):
                    return True
        except ValueError:
            continue

    return False


def get_client_ip(request: Request) -> str:
    """
    Safely resolves the client IP address.

    Rules:
    1. If `settings.TRUSTED_PROXIES` is empty:
       Never trust `X-Forwarded-For` or `X-Real-IP`. Return `request.client.host`.
    2. If `settings.TRUSTED_PROXIES` is configured:
       Only trust `X-Forwarded-For` if the immediate peer (`request.client.host`)
       is an authorized trusted proxy. Walk `X-Forwarded-For` right-to-left and return
       the first non-trusted IP.
    """
    direct_ip = request.client.host if request.client else "127.0.0.1"

    # If no trusted proxies configured, never inspect forwarded headers
    if not settings.TRUSTED_PROXIES:
        return direct_ip

    # If the immediate peer is not trusted, ignore forwarded headers to avoid spoofing
    if not is_ip_trusted(direct_ip, settings.TRUSTED_PROXIES):
        return direct_ip

    # Peer is a trusted proxy: parse X-Forwarded-For right-to-left
    xff = (
        request.headers.get("X-Forwarded-For")
        or request.headers.get("x-forwarded-for")
    )
    if xff:
        ips = [item.strip() for item in xff.split(",") if item.strip()]
        for candidate_ip in reversed(ips):
            if not is_ip_trusted(candidate_ip, settings.TRUSTED_PROXIES):
                try:
                    # Validate that it is a well-formed IP
                    ipaddress.ip_address(candidate_ip)
                    return candidate_ip
                except ValueError:
                    continue

        if ips:
            return ips[0]

    # Fallback to X-Real-IP if present and valid
    x_real = (
        request.headers.get("X-Real-IP")
        or request.headers.get("x-real-ip")
    )
    if x_real:
        clean_real = x_real.strip()
        try:
            ipaddress.ip_address(clean_real)
            return clean_real
        except ValueError:
            pass

    return direct_ip


class TokenBucket:
    __slots__ = ("capacity", "fill_rate", "tokens", "last_update")

    def __init__(self, capacity: float, fill_rate: float, now: Optional[float] = None):
        self.capacity = capacity
        self.fill_rate = fill_rate
        self.tokens = capacity
        self.last_update = now if now is not None else time.monotonic()

    def consume(self, now: float) -> Tuple[bool, int]:
        elapsed = max(0.0, now - self.last_update)
        self.tokens = min(self.capacity, self.tokens + elapsed * self.fill_rate)
        self.last_update = now

        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True, 0
        else:
            needed = 1.0 - self.tokens
            retry_after = max(1, math.ceil(needed / self.fill_rate))
            return False, retry_after


class InMemoryRateLimiter:
    """
    Thread-safe process-local Token Bucket Rate Limiter.
    """
    def __init__(self):
        self._buckets: Dict[str, TokenBucket] = {}
        self._lock = threading.Lock()
        self._last_cleanup = time.monotonic()

    def check(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        now = time.monotonic()
        fill_rate = max_requests / float(window_seconds)

        with self._lock:
            # Periodic cleanup every 5 minutes to prevent memory leaks from one-off IPs
            if now - self._last_cleanup > 300:
                self._cleanup(now)

            bucket = self._buckets.get(key)
            if bucket is None or bucket.capacity != max_requests or bucket.fill_rate != fill_rate:
                bucket = TokenBucket(capacity=float(max_requests), fill_rate=fill_rate, now=now)
                self._buckets[key] = bucket

            return bucket.consume(now)

    def _cleanup(self, now: float):
        self._last_cleanup = now
        stale_cutoff = 3600  # 1 hour idle
        stale_keys = [
            k for k, b in self._buckets.items()
            if (now - b.last_update) > stale_cutoff
        ]
        for k in stale_keys:
            del self._buckets[k]

    def reset(self):
        """Testing utility to clear all rate limit state."""
        with self._lock:
            self._buckets.clear()


# Global singleton rate limiter instance
rate_limiter = InMemoryRateLimiter()


class RateLimiter:
    """
    FastAPI dependency enforcing endpoint rate limits per client IP.
    """
    def __init__(
        self,
        requests_per_window: Optional[int] = None,
        window_seconds: int = 60,
        key_prefix: str = "rate_limit"
    ):
        self._requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.key_prefix = key_prefix

    def get_limit(self) -> int:
        """Dynamically resolves the active limit to allow test overrides and live config."""
        if self._requests_per_window is not None:
            return self._requests_per_window
        if "auth" in self.key_prefix:
            return settings.RATE_LIMIT_AUTH_PER_MINUTE
        if "chat" in self.key_prefix:
            return settings.RATE_LIMIT_CHAT_PER_MINUTE
        if "upload" in self.key_prefix:
            return settings.RATE_LIMIT_UPLOAD_PER_MINUTE
        if "webhook" in self.key_prefix:
            return settings.RATE_LIMIT_WEBHOOK_PER_MINUTE
        return 60

    async def __call__(self, request: Request):
        if not settings.RATE_LIMIT_ENABLED:
            return

        client_ip = get_client_ip(request)
        key = f"{self.key_prefix}:{client_ip}"
        limit = self.get_limit()
        allowed, retry_after = rate_limiter.check(key, limit, self.window_seconds)
        if not allowed:
            logger.warning(
                "Rate limit exceeded for prefix=%s ip=%s retry_after=%ds",
                self.key_prefix, client_ip, retry_after
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Please retry after {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )
