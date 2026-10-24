import time
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import Request

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.rate_limit import (
    get_client_ip,
    is_ip_trusted,
    InMemoryRateLimiter,
    rate_limiter
)

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest.fixture(autouse=True)
def reset_limiter_and_settings():
    """Resets rate limiter state and restores default settings for test isolation."""
    rate_limiter.reset()
    original_trusted = list(settings.TRUSTED_PROXIES)
    original_enabled = settings.RATE_LIMIT_ENABLED
    original_auth_limit = settings.RATE_LIMIT_AUTH_PER_MINUTE
    original_chat_limit = settings.RATE_LIMIT_CHAT_PER_MINUTE
    try:
        yield
    finally:
        rate_limiter.reset()
        settings.TRUSTED_PROXIES = original_trusted
        settings.RATE_LIMIT_ENABLED = original_enabled
        settings.RATE_LIMIT_AUTH_PER_MINUTE = original_auth_limit
        settings.RATE_LIMIT_CHAT_PER_MINUTE = original_chat_limit


class MockRequest:
    """Mock Request object for unit testing safe IP resolution without full HTTP stack."""
    def __init__(self, host: str, headers: dict = None):
        class Client:
            def __init__(self, h):
                self.host = h
        self.client = Client(host) if host else None
        self.headers = headers or {}


def test_client_ip_resolution_untrusted_by_default():
    """
    G-10 IP Spoofing Defense:
    When TRUSTED_PROXIES is empty, X-Forwarded-For and X-Real-IP MUST NOT be trusted.
    """
    settings.TRUSTED_PROXIES = []
    
    # Attacker attempts to spoof an IP via X-Forwarded-For
    req = MockRequest(
        host="198.51.100.5",
        headers={"x-forwarded-for": "1.1.1.1, 203.0.113.50", "x-real-ip": "8.8.8.8"}
    )
    resolved_ip = get_client_ip(req)
    # Must strictly resolve to the direct socket IP
    assert resolved_ip == "198.51.100.5"


def test_client_ip_resolution_untrusted_peer_ignored():
    """
    G-10: When TRUSTED_PROXIES is configured, but direct connection is NOT from a trusted proxy,
    X-Forwarded-For headers are ignored.
    """
    settings.TRUSTED_PROXIES = ["127.0.0.1", "10.0.0.1"]

    # Direct connection from untrusted IP sending forged headers
    req = MockRequest(
        host="203.0.113.99",
        headers={"x-forwarded-for": "10.0.0.1, 1.2.3.4"}
    )
    resolved_ip = get_client_ip(req)
    assert resolved_ip == "203.0.113.99"


def test_client_ip_resolution_trusted_proxy_right_to_left():
    """
    G-10: When request arrives from a trusted proxy, walk X-Forwarded-For right-to-left
    to safely determine the real client IP.
    """
    settings.TRUSTED_PROXIES = ["127.0.0.1", "10.0.0.0/8"]

    # Request arrives via trusted reverse proxy (127.0.0.1)
    # Chain: [client: 203.0.113.195] -> [internal proxy: 10.0.0.2] -> [app: 127.0.0.1]
    req = MockRequest(
        host="127.0.0.1",
        headers={"x-forwarded-for": "203.0.113.195, 10.0.0.2"}
    )
    resolved_ip = get_client_ip(req)
    assert resolved_ip == "203.0.113.195"


def test_token_bucket_rate_limiter_unit():
    """
    G-10: Token bucket allows up to capacity and denies subsequent requests
    returning Retry-After.
    """
    limiter = InMemoryRateLimiter()
    key = "test_key"
    max_requests = 3
    window_seconds = 60

    # First 3 requests allowed
    for _ in range(3):
        allowed, retry_after = limiter.check(key, max_requests, window_seconds)
        assert allowed is True
        assert retry_after == 0

    # 4th request blocked
    allowed, retry_after = limiter.check(key, max_requests, window_seconds)
    assert allowed is False
    assert retry_after > 0


@pytest.mark.asyncio
async def test_auth_login_rate_limiting_returns_429(client):
    """
    G-10 HTTP Integration:
    Exceeding the login rate limit triggers HTTP 429 Too Many Requests with Retry-After header.
    """
    settings.RATE_LIMIT_AUTH_PER_MINUTE = 3
    settings.RATE_LIMIT_ENABLED = True

    # First 3 failed login attempts return 401 Unauthorized
    for _ in range(3):
        res = await client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "WrongPassword123!"
        })
        assert res.status_code == 401

    # 4th attempt is rate-limited: 429 Too Many Requests
    blocked_res = await client.post("/api/v1/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "WrongPassword123!"
    })
    assert blocked_res.status_code == 429
    assert "Retry-After" in blocked_res.headers
    assert int(blocked_res.headers["Retry-After"]) >= 1
    assert "Rate limit exceeded" in blocked_res.json()["detail"]


@pytest.mark.asyncio
async def test_chat_endpoint_rate_limiting(client):
    """
    G-10 HTTP Integration:
    Exceeding the chat rate limit triggers HTTP 429.
    """
    settings.RATE_LIMIT_CHAT_PER_MINUTE = 2
    settings.RATE_LIMIT_ENABLED = True

    # 2 requests succeed
    for _ in range(2):
        res = await client.post("/api/v1/chat", json={
            "message": "வணக்கம், சாதிச் சான்றிதழ் தேவை"
        })
        assert res.status_code == 200

    # 3rd request blocked
    res_3 = await client.post("/api/v1/chat", json={
        "message": "வணக்கம், சாதிச் சான்றிதழ் தேவை"
    })
    assert res_3.status_code == 429
    assert "Retry-After" in res_3.headers
    assert "Rate limit exceeded" in res_3.json()["detail"]


@pytest.mark.asyncio
async def test_rate_limiter_isolated_by_ip(client):
    """
    G-10: Rate limit buckets are keyed per client IP.
    Exhausting quota for IP A (via trusted proxy forwarding) does not block IP B.
    """
    settings.TRUSTED_PROXIES = ["testclient", "127.0.0.1"]
    settings.RATE_LIMIT_AUTH_PER_MINUTE = 1
    settings.RATE_LIMIT_ENABLED = True

    # IP A consumes quota and gets blocked
    res_a1 = await client.post(
        "/api/v1/auth/login",
        json={"email": "ipa@example.com", "password": "WrongPassword1!"},
        headers={"X-Forwarded-For": "203.0.113.10"}
    )
    assert res_a1.status_code == 401

    res_a2 = await client.post(
        "/api/v1/auth/login",
        json={"email": "ipa@example.com", "password": "WrongPassword1!"},
        headers={"X-Forwarded-For": "203.0.113.10"}
    )
    assert res_a2.status_code == 429

    # IP B makes a request: not blocked
    res_b1 = await client.post(
        "/api/v1/auth/login",
        json={"email": "ipb@example.com", "password": "WrongPassword1!"},
        headers={"X-Forwarded-For": "203.0.113.20"}
    )
    assert res_b1.status_code == 401

