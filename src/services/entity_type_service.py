"""Entity Type Service with direct Redis access.

Manages entity types stored in Redis under 'graphiti:entity_types'.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as redis

from ..config import get_settings

logger = logging.getLogger(__name__)

ENTITY_TYPES_KEY = "graphiti:entity_types"


class EntityType:
    """Entity type model."""

    def __init__(
        self,
        name: str,
        description: str,
        fields: list[dict[str, Any]] | None = None,
        source: str = "api",
        created_at: str | None = None,
        modified_at: str | None = None,
    ):
        self.name = name
        self.description = description
        self.fields = fields or []
        self.source = source
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.modified_at = modified_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "fields": self.fields,
            "source": self.source,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EntityType":
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            fields=data.get("fields", []),
            source=data.get("source", "api"),
            created_at=data.get("created_at"),
            modified_at=data.get("modified_at"),
        )


class EntityTypeService:
    """Service for managing entity types in Redis."""

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

    async def get_all(self) -> list[EntityType]:
        """Get all entity types."""
        try:
            r = await self._get_redis()
            data = await r.get(ENTITY_TYPES_KEY)
            if not data:
                return []

            types_dict = json.loads(data)
            return [EntityType.from_dict(t) for t in types_dict.values()]
        except Exception as e:
            logger.error(f"Error getting entity types: {e}")
            return []

    async def get_by_name(self, name: str) -> EntityType | None:
        """Get entity type by name."""
        try:
            r = await self._get_redis()
            data = await r.get(ENTITY_TYPES_KEY)
            if not data:
                return None

            types_dict = json.loads(data)
            if name in types_dict:
                return EntityType.from_dict(types_dict[name])
            return None
        except Exception as e:
            logger.error(f"Error getting entity type {name}: {e}")
            return None

    async def create(
        self,
        name: str,
        description: str,
        fields: list[dict[str, Any]] | None = None,
    ) -> EntityType:
        """Create a new entity type."""
        r = await self._get_redis()

        # Load existing
        data = await r.get(ENTITY_TYPES_KEY)
        types_dict = json.loads(data) if data else {}

        if name in types_dict:
            raise ValueError(f"Entity type '{name}' already exists")

        # Create new
        entity_type = EntityType(
            name=name,
            description=description,
            fields=fields or [],
            source="api",
        )
        types_dict[name] = entity_type.to_dict()

        # Save
        await r.set(ENTITY_TYPES_KEY, json.dumps(types_dict))
        logger.info(f"Created entity type: {name}")

        return entity_type

    async def update(
        self,
        name: str,
        description: str | None = None,
        fields: list[dict[str, Any]] | None = None,
    ) -> EntityType | None:
        """Update an entity type."""
        r = await self._get_redis()

        # Load existing
        data = await r.get(ENTITY_TYPES_KEY)
        if not data:
            return None

        types_dict = json.loads(data)
        if name not in types_dict:
            return None

        # Update
        if description is not None:
            types_dict[name]["description"] = description
        if fields is not None:
            types_dict[name]["fields"] = fields
        types_dict[name]["modified_at"] = datetime.now(timezone.utc).isoformat()
        types_dict[name]["source"] = "api"

        # Save
        await r.set(ENTITY_TYPES_KEY, json.dumps(types_dict))
        logger.info(f"Updated entity type: {name}")

        return EntityType.from_dict(types_dict[name])

    async def delete(self, name: str) -> bool:
        """Delete an entity type."""
        r = await self._get_redis()

        # Load existing
        data = await r.get(ENTITY_TYPES_KEY)
        if not data:
            return False

        types_dict = json.loads(data)
        if name not in types_dict:
            return False

        # Delete
        del types_dict[name]

        # Save
        await r.set(ENTITY_TYPES_KEY, json.dumps(types_dict))
        logger.info(f"Deleted entity type: {name}")

        return True

    async def reset_to_defaults(self, default_types: list[dict[str, Any]]) -> list[EntityType]:
        """Reset entity types to defaults."""
        r = await self._get_redis()

        types_dict = {}
        for et in default_types:
            entity_type = EntityType(
                name=et["name"],
                description=et.get("description", ""),
                fields=et.get("fields", []),
                source="config",
            )
            types_dict[et["name"]] = entity_type.to_dict()

        await r.set(ENTITY_TYPES_KEY, json.dumps(types_dict))
        logger.info(f"Reset {len(types_dict)} entity types to defaults")

        return [EntityType.from_dict(t) for t in types_dict.values()]

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.aclose()
            self._redis = None


# Singleton instance
_entity_type_service: EntityTypeService | None = None


def get_entity_type_service() -> EntityTypeService:
    """Get the EntityTypeService singleton."""
    global _entity_type_service
    if _entity_type_service is None:
        _entity_type_service = EntityTypeService()
    return _entity_type_service
