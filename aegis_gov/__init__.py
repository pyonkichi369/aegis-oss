"""AEGIS — Governance-first framework for AI agent systems."""

__version__ = "0.1.1"

from .council.boardroom import Boardroom, BoardroomConfig
from .council.rule_engine import EvaluationResult, RuleEngine, RuleVerdict
from .council.schemas import (
    AgentRole,
    BoardroomSession,
    Decision,
    DecisionCategory,
    ReviewResult,
    ReviewVerdict,
    Severity,
    Vote,
    VotePosition,
)

__all__ = [
    "Boardroom",
    "BoardroomConfig",
    "RuleEngine",
    "RuleVerdict",
    "EvaluationResult",
    "AgentRole",
    "BoardroomSession",
    "Decision",
    "DecisionCategory",
    "ReviewResult",
    "ReviewVerdict",
    "Severity",
    "Vote",
    "VotePosition",
]
