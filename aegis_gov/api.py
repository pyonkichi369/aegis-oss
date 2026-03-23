"""
AEGIS Council API — FastAPI endpoints for governance operations.

Provides REST endpoints for running boardroom meetings, reviews,
and rule engine evaluations.

Run:
    uvicorn aegis_gov.api:app --reload
"""

import hmac
import logging
import os
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import __version__
from .council.boardroom import Boardroom, BoardroomConfig
from .council.rule_engine import RuleEngine
from .council.security import sanitize_context, sanitize_input

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AEGIS Council",
    description="AI Governance & Multi-Agent Council Framework",
    version=__version__,
)


# =============================================================================
# CORS — configurable origins (not allow-all)
# =============================================================================

def _get_cors_origins() -> list:
    """Get allowed CORS origins from env or use safe defaults."""
    env_origins = os.environ.get("AEGIS_CORS_ORIGINS", "")
    if env_origins:
        return [o.strip() for o in env_origins.split(",") if o.strip()]
    return ["http://localhost:3000", "http://localhost:8000"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)


# =============================================================================
# API Key Authentication
# =============================================================================

_AEGIS_API_KEY = os.environ.get("AEGIS_API_KEY", "")

if not _AEGIS_API_KEY:
    logger.warning(
        "AEGIS_API_KEY not set — running in DEVELOPMENT mode (no auth). "
        "Set AEGIS_API_KEY environment variable for production."
    )


def verify_api_key(request: Request) -> None:
    """
    Verify the X-API-Key header matches the configured API key.

    If AEGIS_API_KEY is not set, all requests are allowed (dev mode).
    """
    if not _AEGIS_API_KEY:
        return  # Dev mode — no auth required

    provided_key = request.headers.get("X-API-Key", "")
    if not provided_key or not hmac.compare_digest(provided_key, _AEGIS_API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


# =============================================================================
# Global instances
# =============================================================================

rule_engine = RuleEngine()


# =============================================================================
# Request/Response Models
# =============================================================================

class BoardroomRequest(BaseModel):
    topic: str
    category: str = "TACTICAL"
    context: dict[str, Any] = {}
    model: str = "claude-sonnet-4-20250514"
    provider: str = "anthropic"
    synthesis_language: str = "en"
    max_debate_rounds: int = 2


class ReviewRequest(BaseModel):
    artifact: str
    reviewer_tiers: list[str] = ["reviewer", "red_team"]
    model: str = "claude-sonnet-4-20250514"
    provider: str = "anthropic"


class RuleCheckRequest(BaseModel):
    agent: str
    action: str
    context: dict[str, Any] = {}


class HealthResponse(BaseModel):
    status: str
    version: str


# =============================================================================
# Endpoints
# =============================================================================

@app.get("/health", response_model=HealthResponse)
def health():
    """Health check — always public, no auth required."""
    return {"status": "ok", "version": __version__}


@app.post("/api/v1/boardroom", dependencies=[Depends(verify_api_key)])
def run_boardroom(req: BoardroomRequest):
    """Run a full boardroom meeting with structured agent debate."""
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(400, "Set ANTHROPIC_API_KEY or OPENAI_API_KEY in environment")

    # Sanitize inputs
    sanitized_topic = sanitize_input(req.topic, max_length=2000, field_name="topic")
    sanitized_context = sanitize_context(req.context, max_length=5000)

    if not sanitized_topic:
        raise HTTPException(422, "Topic cannot be empty after sanitization")

    config = BoardroomConfig(
        api_key=api_key,
        model=req.model,
        provider=req.provider,
        synthesis_language=req.synthesis_language,
        max_debate_rounds=req.max_debate_rounds,
    )
    boardroom = Boardroom(config=config)

    try:
        session = boardroom.convene(
            topic=sanitized_topic,
            category=req.category,
            context=sanitized_context,
        )
        return session.to_dict()
    except Exception as e:
        logger.error(f"Boardroom failed: {e}")
        raise HTTPException(500, "Boardroom session failed")


@app.post("/api/v1/review", dependencies=[Depends(verify_api_key)])
def run_review(req: ReviewRequest):
    """Run a standalone red-team review of an artifact."""
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(400, "Set ANTHROPIC_API_KEY or OPENAI_API_KEY in environment")

    # Sanitize artifact input
    sanitized_artifact = sanitize_input(req.artifact, max_length=5000, field_name="artifact")

    if not sanitized_artifact:
        raise HTTPException(422, "Artifact cannot be empty after sanitization")

    config = BoardroomConfig(
        api_key=api_key,
        model=req.model,
        provider=req.provider,
    )
    boardroom = Boardroom(config=config)

    try:
        results = boardroom.review(sanitized_artifact, req.reviewer_tiers)
        return {"reviews": [r.to_dict() for r in results]}
    except Exception as e:
        logger.error(f"Review failed: {e}")
        raise HTTPException(500, "Review failed")


@app.post("/api/v1/rules/check", dependencies=[Depends(verify_api_key)])
def check_rules(req: RuleCheckRequest):
    """Evaluate an agent action against governance rules."""
    # Sanitize inputs
    sanitized_agent = sanitize_input(req.agent, max_length=200, field_name="agent")
    sanitized_action = sanitize_input(req.action, max_length=2000, field_name="action")
    sanitized_context = sanitize_context(req.context, max_length=5000)

    result = rule_engine.evaluate(sanitized_agent, sanitized_action, sanitized_context)
    return result.to_dict()


@app.get("/api/v1/rules", dependencies=[Depends(verify_api_key)])
def list_rules():
    """List all active governance rules."""
    return {"rules": rule_engine.rules}


@app.get("/api/v1/agents", dependencies=[Depends(verify_api_key)])
def list_agents():
    """List all agents in the council roster."""
    from .council.agents import DEFAULT_ROSTER
    return {"agents": [a.to_dict() for a in DEFAULT_ROSTER]}
