"""
AEGIS Council Schemas — Structured types for agent governance.

Provides validated schemas for agent messages, decisions, reviews, and votes.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

# =============================================================================
# Enums — shared vocabulary
# =============================================================================

class DecisionCategory(Enum):
    """Decision categories with different review requirements."""
    CRITICAL = "CRITICAL"      # 1h TTL, 5 reviews, human always
    STRATEGIC = "STRATEGIC"    # 7d TTL, 3 reviews, human required
    TACTICAL = "TACTICAL"      # 24h TTL, 2 reviews, human if low confidence
    OPERATIONAL = "OPERATIONAL"  # 4h TTL, 1 review, human if flagged


class ReviewVerdict(Enum):
    """Standardized review outcomes."""
    PASS = "PASS"
    FLAG = "FLAG"
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE"
    HALT = "HALT"


class Severity(Enum):
    """Risk severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class VotePosition(Enum):
    """Agent vote positions in boardroom decisions."""
    APPROVE = "approve"
    CONDITIONAL = "conditional"
    REJECT = "reject"
    ABSTAIN = "abstain"


# =============================================================================
# Agent Definition
# =============================================================================

@dataclass
class AgentRole:
    """Definition of an agent participating in governance."""
    name: str
    role: str
    expertise: str
    tier: str = "specialist"  # executive | reviewer | specialist | red_team
    prompt_file: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "expertise": self.expertise,
            "tier": self.tier,
        }


# =============================================================================
# Decision & Review
# =============================================================================

@dataclass
class Decision:
    """A governance decision to be reviewed by the council."""
    decision_id: str = ""
    title: str = ""
    description: str = ""
    category: DecisionCategory = DecisionCategory.TACTICAL
    proposed_by: str = ""
    confidence: float = 0.0
    timestamp: str = ""
    context: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.decision_id:
            self.decision_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class ReviewResult:
    """Structured review from a council member."""
    reviewer: str = ""
    verdict: ReviewVerdict = ReviewVerdict.PASS
    findings: list[str] = field(default_factory=list)
    risks: list[dict[str, str]] = field(default_factory=list)
    severity: Severity = Severity.LOW
    confidence: float = 0.0
    reasoning: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "reviewer": self.reviewer,
            "verdict": self.verdict.value,
            "findings": self.findings,
            "risks": self.risks,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp,
        }


@dataclass
class Vote:
    """Agent vote in a boardroom decision."""
    agent: str = ""
    position: VotePosition = VotePosition.ABSTAIN
    reason: str = ""
    conditions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, str]:
        d = {"agent": self.agent, "position": self.position.value, "reason": self.reason}
        if self.conditions:
            d["conditions"] = self.conditions
        return d


# =============================================================================
# Boardroom Session
# =============================================================================

@dataclass
class BoardroomSession:
    """Complete record of a boardroom meeting."""
    session_id: str = ""
    topic: str = ""
    category: DecisionCategory = DecisionCategory.TACTICAL
    phases: list[dict[str, Any]] = field(default_factory=list)
    reviews: list[ReviewResult] = field(default_factory=list)
    votes: list[Vote] = field(default_factory=list)
    synthesis: str = ""
    verdict: ReviewVerdict = ReviewVerdict.PASS
    confidence: float = 0.0
    timestamp: str = ""

    def __post_init__(self):
        if not self.session_id:
            self.session_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    @property
    def vote_summary(self) -> dict[str, int]:
        counts = {"approve": 0, "conditional": 0, "reject": 0, "abstain": 0}
        for v in self.votes:
            counts[v.position.value] = counts.get(v.position.value, 0) + 1
        return counts

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "topic": self.topic,
            "category": self.category.value,
            "phases": self.phases,
            "reviews": [r.to_dict() for r in self.reviews],
            "votes": [v.to_dict() for v in self.votes],
            "vote_summary": self.vote_summary,
            "synthesis": self.synthesis,
            "verdict": self.verdict.value,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }
