"""Queue Status Service with direct Redis access.

Monitors episode processing queue via Redis Streams.
"""

import logging

import redis.asyncio as redis

from ..config import get_settings

logger = logging.getLogger(__name__)


class QueueService:
    """Service for monitoring queue status in Redis."""

    def __init__(self):
        self._redis: redis.Redis | None = None

    async def _get_redis(self) -> redis.Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            settings = get_settings()
            self._redis = redis.Redis(
                host=settings.falkordb_host,
                port=settings.falkordb_port,
                password=settings.falkordb_password or None,
                decode_responses=True,
            )
        return self._redis

    def _stream_key(self, group_id: str) -> str:
        """Get Redis stream key for a group."""
        return f"graphiti:queue:{group_id}"

    async def get_all_group_ids(self) -> list[str]:
        """Get all group IDs from Redis keys."""
        try:
            r = await self._get_redis()
            all_keys = await r.keys("*")
            group_ids = [
                k for k in all_keys
                if not k.startswith("telemetry{")
                and not k.startswith("graphiti:")
                and k not in ["graphiti"]
            ]
            return sorted(group_ids)
        except Exception as e:
            logger.error(f"Error getting group IDs: {e}")
            return []

    async def get_status(self) -> dict:
        """Get queue processing status."""
        try:
            r = await self._get_redis()
            group_ids = await self.get_all_group_ids()

            total_pending = 0
            active_streams = 0

            for gid in group_ids:
                stream_key = self._stream_key(gid)
                try:
                    # Check if stream exists and has pending messages
                    stream_info = await r.xinfo_stream(stream_key)
                    if stream_info:
                        length = stream_info.get("length", 0)
                        if length > 0:
                            total_pending += length
                            active_streams += 1
                except redis.ResponseError:
                    # Stream doesn't exist
                    pass
                except Exception as e:
                    logger.debug(f"Error checking stream {stream_key}: {e}")

            # Also check consumer groups for pending messages
            for gid in group_ids:
                stream_key = self._stream_key(gid)
                try:
                    groups = await r.xinfo_groups(stream_key)
                    for group in groups:
                        pending = group.get("pending", 0)
                        if pending > 0:
                            total_pending += pending
                except redis.ResponseError:
                    pass
                except Exception:
                    pass

            return {
                "success": True,
                "processing": total_pending > 0,
                "pending_count": total_pending,
                "active_streams": active_streams,
            }
        except Exception as e:
            logger.error(f"Error getting queue status: {e}")
            return {
                "success": False,
                "processing": False,
                "pending_count": 0,
                "active_streams": 0,
                "error": str(e),
            }

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.aclose()
            self._redis = None


# Singleton instance
_queue_service: QueueService | None = None


def get_queue_service() -> QueueService:
    """Get the QueueService singleton."""
    global _queue_service
    if _queue_service is None:
        _queue_service = QueueService()
    return _queue_service
