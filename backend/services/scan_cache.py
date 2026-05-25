import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse, urlunparse

from redis.asyncio import Redis

from config import Settings
from models import ScanJobStatus


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"
    return urlunparse((scheme, netloc, path, "", "", ""))


def cache_key_for_url(url: str) -> str:
    digest = hashlib.sha256(normalize_url(url).encode()).hexdigest()
    return f"scan:website:{digest}"


async def get_cached_scan(redis: Redis, url: str) -> dict[str, Any] | None:
    raw = await redis.get(cache_key_for_url(url))
    if raw is None:
        return None
    return json.loads(raw)


async def set_scan_completed(
    redis: Redis,
    url: str,
    result: dict[str, Any],
    settings: Settings,
) -> str:
    scanned_at = datetime.now(UTC).isoformat()
    payload = {
        "status": ScanJobStatus.COMPLETED.value,
        "url": normalize_url(url),
        "result": result,
        "scanned_at": scanned_at,
    }
    await redis.set(
        cache_key_for_url(url),
        json.dumps(payload),
        ex=settings.scan_cache_ttl_seconds,
    )
    return scanned_at
