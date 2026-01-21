"""Entity Types API routes."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..auth.dependencies import CurrentUser
from ..services.config_service import read_config, write_config

router = APIRouter()


class EntityType(BaseModel):
    """Entity type model."""

    name: str = Field(..., pattern=r"^[A-Z][a-zA-Z0-9]*$", description="PascalCase name")
    description: str = Field(..., min_length=10, description="Description for LLM extraction")


class EntityTypeCreate(BaseModel):
    """Create entity type request."""

    name: str = Field(..., pattern=r"^[A-Z][a-zA-Z0-9]*$")
    description: str = Field(..., min_length=10)


class EntityTypeUpdate(BaseModel):
    """Update entity type request."""

    description: str = Field(..., min_length=10)


def get_entity_types_from_config(config: dict[str, Any]) -> list[dict]:
    """Extract entity types from config."""
    return config.get("graphiti", {}).get("entity_types", [])


def set_entity_types_in_config(config: dict[str, Any], entity_types: list[dict]) -> dict[str, Any]:
    """Set entity types in config."""
    if "graphiti" not in config:
        config["graphiti"] = {}
    config["graphiti"]["entity_types"] = entity_types
    return config


@router.get("", response_model=list[EntityType])
async def list_entity_types(current_user: CurrentUser) -> list[EntityType]:
    """List all configured entity types."""
    config = read_config()
    entity_types = get_entity_types_from_config(config)
    return [EntityType(**et) for et in entity_types]


@router.post("", response_model=EntityType)
async def create_entity_type(
    entity_type: EntityTypeCreate,
    current_user: CurrentUser,
) -> EntityType:
    """Create a new entity type."""
    config = read_config()
    entity_types = get_entity_types_from_config(config)

    # Check for duplicate
    if any(et["name"] == entity_type.name for et in entity_types):
        raise HTTPException(status_code=400, detail=f"Entity type '{entity_type.name}' already exists")

    # Add new entity type
    new_et = {"name": entity_type.name, "description": entity_type.description}
    entity_types.append(new_et)

    # Save config
    config = set_entity_types_in_config(config, entity_types)
    write_config(config)

    return EntityType(**new_et)


@router.get("/{name}", response_model=EntityType)
async def get_entity_type(name: str, current_user: CurrentUser) -> EntityType:
    """Get a specific entity type."""
    config = read_config()
    entity_types = get_entity_types_from_config(config)

    for et in entity_types:
        if et["name"] == name:
            return EntityType(**et)

    raise HTTPException(status_code=404, detail=f"Entity type '{name}' not found")


@router.put("/{name}", response_model=EntityType)
async def update_entity_type(
    name: str,
    update: EntityTypeUpdate,
    current_user: CurrentUser,
) -> EntityType:
    """Update an entity type."""
    config = read_config()
    entity_types = get_entity_types_from_config(config)

    for et in entity_types:
        if et["name"] == name:
            et["description"] = update.description
            config = set_entity_types_in_config(config, entity_types)
            write_config(config)
            return EntityType(**et)

    raise HTTPException(status_code=404, detail=f"Entity type '{name}' not found")


@router.delete("/{name}")
async def delete_entity_type(name: str, current_user: CurrentUser) -> dict:
    """Delete an entity type."""
    config = read_config()
    entity_types = get_entity_types_from_config(config)

    original_count = len(entity_types)
    entity_types = [et for et in entity_types if et["name"] != name]

    if len(entity_types) == original_count:
        raise HTTPException(status_code=404, detail=f"Entity type '{name}' not found")

    config = set_entity_types_in_config(config, entity_types)
    write_config(config)

    return {"message": f"Entity type '{name}' deleted", "restart_required": True}
