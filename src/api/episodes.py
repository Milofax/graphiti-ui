"""Episodes API routes."""

from fastapi import APIRouter
from pydantic import BaseModel

from ..auth.dependencies import CurrentUser

router = APIRouter()


class EpisodeCreate(BaseModel):
    """Create episode request."""

    name: str
    content: str
    source: str = "text"  # text, json, message
    source_description: str | None = None
    group_id: str | None = None


class Episode(BaseModel):
    """Episode model."""

    uuid: str
    name: str
    content: str
    source: str
    created_at: str | None = None


@router.get("")
async def list_episodes(
    current_user: CurrentUser,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """List recent episodes."""
    # TODO: Implement via Graphiti MCP client
    return {
        "episodes": [],
        "total": 0,
        "limit": limit,
        "offset": offset,
    }


@router.post("", response_model=Episode)
async def create_episode(episode: EpisodeCreate, current_user: CurrentUser) -> Episode:
    """Create a new episode."""
    # TODO: Implement via Graphiti MCP add_episode
    raise NotImplementedError("Episode creation not yet implemented")


@router.get("/{uuid}")
async def get_episode(uuid: str, current_user: CurrentUser) -> Episode:
    """Get episode details."""
    # TODO: Implement via Graphiti MCP
    raise NotImplementedError("Get episode not yet implemented")


@router.delete("/{uuid}")
async def delete_episode(uuid: str, current_user: CurrentUser) -> dict:
    """Delete an episode."""
    # TODO: Implement via Graphiti MCP delete_episode
    raise NotImplementedError("Delete episode not yet implemented")
