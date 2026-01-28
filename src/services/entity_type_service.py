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

            types_data = json.loads(data)

            # Handle both array format (MCP server) and dict format (legacy)
            if isinstance(types_data, list):
                return [EntityType.from_dict(t) for t in types_data]
            else:
                return [EntityType.from_dict(t) for t in types_data.values()]
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

            types_data = json.loads(data)

            # Handle both array format (MCP server) and dict format (legacy)
            if isinstance(types_data, list):
                for t in types_data:
                    if t.get("name") == name:
                        return EntityType.from_dict(t)
                return None
            else:
                if name in types_data:
                    return EntityType.from_dict(types_data[name])
                return None
        except Exception as e:
            logger.error(f"Error getting entity type {name}: {e}")
            return None

    def _to_list(self, types_data: list | dict) -> list[dict[str, Any]]:
        """Convert entity types to list format (normalizes dict to list)."""
        if isinstance(types_data, list):
            return types_data
        return list(types_data.values())

    async def create(
        self,
        name: str,
        description: str,
        fields: list[dict[str, Any]] | None = None,
    ) -> EntityType:
        """Create a new entity type."""
        r = await self._get_redis()

        # Load existing (as list)
        data = await r.get(ENTITY_TYPES_KEY)
        types_list = self._to_list(json.loads(data)) if data else []

        # Check if exists
        if any(t.get("name") == name for t in types_list):
            raise ValueError(f"Entity type '{name}' already exists")

        # Create new
        entity_type = EntityType(
            name=name,
            description=description,
            fields=fields or [],
            source="api",
        )
        types_list.append(entity_type.to_dict())

        # Save as list
        await r.set(ENTITY_TYPES_KEY, json.dumps(types_list))
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

        # Load existing (as list)
        data = await r.get(ENTITY_TYPES_KEY)
        if not data:
            return None

        types_list = self._to_list(json.loads(data))

        # Find and update
        for i, t in enumerate(types_list):
            if t.get("name") == name:
                if description is not None:
                    types_list[i]["description"] = description
                if fields is not None:
                    types_list[i]["fields"] = fields
                types_list[i]["modified_at"] = datetime.now(timezone.utc).isoformat()
                types_list[i]["source"] = "api"

                # Save as list
                await r.set(ENTITY_TYPES_KEY, json.dumps(types_list))
                logger.info(f"Updated entity type: {name}")
                return EntityType.from_dict(types_list[i])

        return None

    async def delete(self, name: str) -> bool:
        """Delete an entity type."""
        r = await self._get_redis()

        # Load existing (as list)
        data = await r.get(ENTITY_TYPES_KEY)
        if not data:
            return False

        types_list = self._to_list(json.loads(data))
        original_len = len(types_list)

        # Filter out the one to delete
        types_list = [t for t in types_list if t.get("name") != name]

        if len(types_list) == original_len:
            return False  # Not found

        # Save as list
        await r.set(ENTITY_TYPES_KEY, json.dumps(types_list))
        logger.info(f"Deleted entity type: {name}")

        return True

    async def reset_to_defaults(self, default_types: list[dict[str, Any]]) -> list[EntityType]:
        """Reset entity types to defaults."""
        r = await self._get_redis()

        types_list = []
        for et in default_types:
            entity_type = EntityType(
                name=et["name"],
                description=et.get("description", ""),
                fields=et.get("fields", []),
                source="config",
            )
            types_list.append(entity_type.to_dict())

        await r.set(ENTITY_TYPES_KEY, json.dumps(types_list))
        logger.info(f"Reset {len(types_list)} entity types to defaults")

        return [EntityType.from_dict(t) for t in types_list]

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
