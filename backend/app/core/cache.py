"""Redis client factory. Used for the refresh-token denylist and the readiness probe."""

from __future__ import annotations

import logging

from redis.asyncio import Redis

from app.core.config import Settings

logger = logging.getLogger(__name__)


def create_redis(settings: Settings) -> Redis | None:
    if not settings.redis_url:
        logger.warning("APP_REDIS_URL not set; refresh-token revocation is disabled")
        return None
    return Redis.from_url(
        settings.redis_url, decode_responses=True, socket_connect_timeout=2, socket_timeout=2
    )


class TokenDenylist:
    """Revoked refresh-token jtis, expiring with the token itself."""

    def __init__(self, redis: Redis | None) -> None:
        self.redis = redis
        self._memory: set[str] = set()  # fallback when Redis is not configured

    async def revoke(self, jti: str, ttl_seconds: int) -> None:
        if self.redis is None:
            self._memory.add(jti)
            return
        await self.redis.set(f"revoked:{jti}", "1", ex=ttl_seconds)

    async def is_revoked(self, jti: str) -> bool:
        if self.redis is None:
            return jti in self._memory
        return bool(await self.redis.exists(f"revoked:{jti}"))

    async def ping(self) -> bool:
        if self.redis is None:
            return True
        try:
            return bool(await self.redis.ping())
        except Exception:  # noqa: BLE001
            return False
