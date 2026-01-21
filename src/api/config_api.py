"""Configuration API routes.

Configuration is read-only from environment variables.
To change settings, edit .env or docker-compose.yml and restart the stack.
"""

from typing import Any

import httpx
from fastapi import APIRouter
from pydantic import BaseModel

from ..auth.dependencies import CurrentUser
from ..services.config_service import read_config
from ..services.credentials_service import (
    get_llm_credentials,
    get_embedder_credentials,
)

router = APIRouter()


# ============================================
# Configuration Models
# ============================================


class LLMConfigResponse(BaseModel):
    """LLM configuration response."""

    api_url: str
    model: str


class EmbedderConfigResponse(BaseModel):
    """Embedder configuration response."""

    api_url: str
    model: str
    dimensions: int


class LLMStatusResponse(BaseModel):
    """LLM status response with connectivity check."""

    api_url: str
    model: str
    reachable: bool
    model_available: bool = False
    available_models: list[str] = []
    error: str | None = None


class EmbedderStatusResponse(BaseModel):
    """Embedder status response with connectivity check."""

    api_url: str
    model: str
    dimensions: int
    reachable: bool
    model_available: bool = False
    available_models: list[str] = []
    error: str | None = None


# ============================================
# LLM Endpoints
# ============================================


@router.get("/llm", response_model=LLMConfigResponse)
async def get_llm_config(current_user: CurrentUser) -> LLMConfigResponse:
    """Get current LLM configuration (from environment variables)."""
    creds = get_llm_credentials()
    return LLMConfigResponse(
        api_url=creds.get("api_url", ""),
        model=creds.get("model", ""),
    )


@router.get("/llm/status", response_model=LLMStatusResponse)
async def get_llm_status(current_user: CurrentUser) -> LLMStatusResponse:
    """Get LLM configuration with connectivity and model availability status."""
    creds = get_llm_credentials()
    api_url = creds.get("api_url", "")
    api_key = creds.get("api_key", "")
    model = creds.get("model", "")

    reachable = False
    model_available = False
    available_models: list[str] = []
    error = None

    if not api_url:
        error = "API URL not configured"
    else:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                response = await client.get(f"{api_url}/models", headers=headers)
                reachable = response.status_code == 200
                if reachable:
                    data = response.json()
                    models = data.get("data", [])
                    available_models = [m.get("id", "") for m in models]
                    # Check if configured model exists (exact or prefix match)
                    model_available = any(
                        model == mid or mid.startswith(f"{model}:")
                        for mid in available_models
                    )
                    if not model_available:
                        error = f"Model '{model}' not found in available models"
                else:
                    error = f"HTTP {response.status_code}"
        except httpx.TimeoutException:
            error = "Connection timeout"
        except Exception as e:
            error = str(e)[:100]

    return LLMStatusResponse(
        api_url=api_url,
        model=model,
        reachable=reachable,
        model_available=model_available,
        available_models=available_models,
        error=error,
    )


# ============================================
# Embedder Endpoints
# ============================================


@router.get("/embedder", response_model=EmbedderConfigResponse)
async def get_embedder_config(current_user: CurrentUser) -> EmbedderConfigResponse:
    """Get current embedder configuration (from environment variables)."""
    creds = get_embedder_credentials()
    return EmbedderConfigResponse(
        api_url=creds.get("api_url", ""),
        model=creds.get("model", ""),
        dimensions=creds.get("dimensions", 768),
    )


@router.get("/embedder/status", response_model=EmbedderStatusResponse)
async def get_embedder_status(current_user: CurrentUser) -> EmbedderStatusResponse:
    """Get Embedder configuration with connectivity and model availability status."""
    creds = get_embedder_credentials()
    api_url = creds.get("api_url", "")
    api_key = creds.get("api_key", "")
    model = creds.get("model", "")
    dimensions = creds.get("dimensions", 768)

    reachable = False
    model_available = False
    available_models: list[str] = []
    error = None

    if not api_url:
        error = "API URL not configured"
    else:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                # First check available models
                response = await client.get(f"{api_url}/models", headers=headers)
                reachable = response.status_code == 200
                if reachable:
                    data = response.json()
                    models = data.get("data", [])
                    available_models = [m.get("id", "") for m in models]
                    # Check if configured model exists (exact or prefix match)
                    model_available = any(
                        model == mid or mid.startswith(f"{model}:")
                        for mid in available_models
                    )
                    if not model_available:
                        error = f"Model '{model}' not found in available models"
                else:
                    error = f"HTTP {response.status_code}"
        except httpx.TimeoutException:
            error = "Connection timeout"
        except Exception as e:
            error = str(e)[:100]

    return EmbedderStatusResponse(
        api_url=api_url,
        model=model,
        dimensions=dimensions,
        reachable=reachable,
        model_available=model_available,
        available_models=available_models,
        error=error,
    )


# ============================================
# General Config Endpoints
# ============================================


@router.get("")
async def get_full_config(current_user: CurrentUser) -> dict:
    """Get full configuration from config.yaml (masked)."""
    config = read_config()

    # Mask sensitive values
    if "llm" in config and "providers" in config["llm"]:
        for provider in config["llm"]["providers"].values():
            if isinstance(provider, dict) and "api_key" in provider:
                if not str(provider["api_key"]).startswith("${"):
                    provider["api_key"] = "***"

    if "embedder" in config and "providers" in config["embedder"]:
        for provider in config["embedder"]["providers"].values():
            if isinstance(provider, dict) and "api_key" in provider:
                if not str(provider["api_key"]).startswith("${"):
                    provider["api_key"] = "***"

    return {"config": config}
