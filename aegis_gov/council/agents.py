"""
Default agent roster for AEGIS Council.

Defines the standard executive council, review board, advisory team,
and red team. Users can customize by adding/removing agents.

Core roster (9): 7 executives + 2 red team.
Specialist roster (8): 2 reviewers + 6 advisory specialists.
"""

from .schemas import AgentRole

# =============================================================================
# Core Council (DEFAULT_AGENTS) — always included
# =============================================================================

EXECUTIVE_COUNCIL = [
    AgentRole("CEO", "Chief Executive Officer", "Strategic alignment, organizational impact", "executive"),
    AgentRole("CTO", "Chief Technology Officer", "Technical feasibility, architecture, scalability", "executive"),
    AgentRole("CFO", "Chief Financial Officer", "Financial impact, ROI, budget", "executive"),
    AgentRole("CRO", "Chief Risk Officer", "Risk exposure, compliance, downside scenarios", "executive"),
    AgentRole("CMO", "Chief Marketing Officer", "Market positioning, brand, go-to-market", "executive"),
    AgentRole("CPO", "Chief Product Officer", "Product-market fit, user value, roadmap", "executive"),
    AgentRole("CDO", "Chief Design Officer", "Design strategy, brand consistency, UX vision", "executive"),
]

RED_TEAM = [
    AgentRole(
        "DevilsAdvocate", "Adversarial Reviewer",
        "Challenge assumptions, find hidden risks, stress-test", "red_team",
        prompt_file="devils_advocate.prompt",
    ),
    AgentRole("Skeptic", "Alternative Analyst", "Explore alternatives, pre-mortem, blind spots", "red_team",
              prompt_file="skeptic.prompt"),
]

# Core roster: executives + red team (9 agents)
DEFAULT_AGENTS = EXECUTIVE_COUNCIL + RED_TEAM


# =============================================================================
# Specialist Agents — opt-in for deeper analysis
# =============================================================================

REVIEW_BOARD = [
    AgentRole("TechnicalReviewer", "Technical Reviewer", "Architecture risks, scalability, code quality", "reviewer"),
    AgentRole("SecurityReviewer", "Security Reviewer", "Vulnerabilities, compliance, data privacy", "reviewer"),
]

ADVISORY = [
    AgentRole("Investor", "Investment Advisor", "Investment thesis, valuation, exit strategy", "specialist"),
    AgentRole("Designer", "UX/UI Designer", "Interaction design, accessibility, visual design", "specialist"),
    AgentRole("Growth", "Growth Hacker", "Acquisition, activation, retention, referral", "specialist"),
    AgentRole("Researcher", "Market Researcher", "Competitive analysis, market data, evidence", "specialist"),
    AgentRole("QA", "Quality Assurance", "Testing, edge cases, quality risks", "specialist"),
    AgentRole("PromptEngineer", "Prompt Engineer", "AI/LLM implications, prompt design", "specialist"),
]

SPECIALIST_AGENTS = REVIEW_BOARD + ADVISORY


# =============================================================================
# Backward-compatible alias — full roster (all 17 agents)
# =============================================================================

DEFAULT_ROSTER = DEFAULT_AGENTS + SPECIALIST_AGENTS


# =============================================================================
# Roster access functions
# =============================================================================

def get_default_roster() -> list[AgentRole]:
    """Get the core roster only (9 agents: executives + red team)."""
    return list(DEFAULT_AGENTS)


def get_specialist_agents() -> list[AgentRole]:
    """Get specialist agents only (reviewers + advisory)."""
    return list(SPECIALIST_AGENTS)


def get_full_roster() -> list[AgentRole]:
    """Get the complete roster (core + specialists)."""
    return list(DEFAULT_ROSTER)


def get_roster(custom_agents: list[AgentRole] | None = None) -> list[AgentRole]:
    """Get the default roster, optionally extended with custom agents.

    For backward compatibility, this returns the full roster (all agents).
    """
    roster = list(DEFAULT_ROSTER)
    if custom_agents:
        roster.extend(custom_agents)
    return roster


def get_roster_with_specialists(custom_agents: list[AgentRole] | None = None) -> list[AgentRole]:
    """Get the full roster (core + specialists), optionally extended with custom agents."""
    roster = list(DEFAULT_ROSTER)
    if custom_agents:
        roster.extend(custom_agents)
    return roster


def get_agents_by_tier(tier: str) -> list[AgentRole]:
    """Get agents filtered by tier (searches full roster)."""
    return [a for a in DEFAULT_ROSTER if a.tier == tier]
