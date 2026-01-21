"""Graphiti MCP Server communication service.

Provides methods to interact with the Graphiti MCP server for
searching nodes, facts, and managing episodes.
"""

import httpx
from typing import Any

from ..config import get_settings


class GraphitiClient:
    """Client for Graphiti MCP Server."""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.graphiti_mcp_url

    async def health_check(self) -> dict:
        """Check if the MCP server is healthy."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    return {"healthy": True, "data": response.json()}
                return {"healthy": False, "error": f"Status {response.status_code}"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    async def get_status(self) -> dict:
        """Get server status including graph statistics."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/status")
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                return {"success": False, "error": f"Status {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict:
        """Call an MCP tool via the server.

        The Graphiti MCP server exposes tools via JSON-RPC at /mcp/ endpoint.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # MCP uses JSON-RPC 2.0 format
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments,
                    },
                }

                response = await client.post(
                    f"{self.base_url}/mcp/",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code == 200:
                    result = response.json()
                    if "error" in result:
                        return {"success": False, "error": result["error"]}
                    return {"success": True, "data": result.get("result", {})}
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def search_nodes(
        self,
        query: str,
        limit: int = 10,
        entity_types: list[str] | None = None,
        group_ids: list[str] | None = None,
    ) -> dict:
        """Search for nodes (entities) in the knowledge graph.

        Args:
            query: Search query
            limit: Maximum number of results
            entity_types: Filter by entity types
            group_ids: Filter by group IDs
        """
        arguments = {
            "query": query,
            "limit": limit,
        }
        if entity_types:
            arguments["entity_types"] = entity_types
        if group_ids:
            arguments["group_ids"] = group_ids

        return await self.call_tool("search_nodes", arguments)

    async def search_facts(
        self,
        query: str,
        limit: int = 10,
        group_ids: list[str] | None = None,
    ) -> dict:
        """Search for facts (relationships) in the knowledge graph.

        Args:
            query: Search query
            limit: Maximum number of results
            group_ids: Filter by group IDs
        """
        arguments = {
            "query": query,
            "limit": limit,
        }
        if group_ids:
            arguments["group_ids"] = group_ids

        return await self.call_tool("search_facts", arguments)

    async def get_episodes(
        self,
        limit: int = 10,
        group_ids: list[str] | None = None,
    ) -> dict:
        """Get recent episodes from the knowledge graph.

        Args:
            limit: Maximum number of results
            group_ids: Filter by group IDs
        """
        arguments = {"limit": limit}
        if group_ids:
            arguments["group_ids"] = group_ids

        return await self.call_tool("get_episodes", arguments)

    async def delete_episode(self, episode_uuid: str) -> dict:
        """Delete an episode from the knowledge graph.

        Args:
            episode_uuid: UUID of the episode to delete
        """
        return await self.call_tool("delete_episode", {"episode_uuid": episode_uuid})


# Global client instance
_client: GraphitiClient | None = None


def get_graphiti_client() -> GraphitiClient:
    """Get the Graphiti client singleton."""
    global _client
    if _client is None:
        _client = GraphitiClient()
    return _client
