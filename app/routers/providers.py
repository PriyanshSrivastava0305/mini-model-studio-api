# app/routers/providers.py
from fastapi import APIRouter
import os

router = APIRouter(prefix="/providers", tags=["providers"])

# curated model catalog (small curated list)
MODEL_CATALOG = {
    "openai": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
    "anthropic": ["claude-2", "claude-instant-1"]
}

@router.get("/")
async def list_providers():
    """Return list of enabled providers based on env keys."""
    providers = []
    if os.getenv("OPENAI_API_KEY"):
        providers.append({"id": "openai", "name": "OpenAI"})
    if os.getenv("ANTHROPIC_API_KEY"):
        providers.append({"id": "anthropic", "name": "Anthropic"})
    # allow client to see mock providers if ALLOW_MOCK
    if os.getenv("ALLOW_MOCK", "false").lower() == "true":
        providers.append({"id":"openai", "name":"OpenAI (mockable)"})
        providers.append({"id":"anthropic","name":"Anthropic (mockable)"})
    return {"providers": providers}

@router.get("/models")
async def get_models(provider: str):
    if provider not in MODEL_CATALOG:
        return {"models": []}
    return {"provider": provider, "models": MODEL_CATALOG[provider]}


# Why: Simple curated catalog is ok per spec. This endpoint is used by frontend to show base model choices filtered by provider.