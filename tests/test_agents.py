"""Tests for agent roster management."""

from aegis_gov.council.agents import (
    DEFAULT_AGENTS,
    DEFAULT_ROSTER,
    EXECUTIVE_COUNCIL,
    RED_TEAM,
    SPECIALIST_AGENTS,
    get_agents_by_tier,
    get_default_roster,
    get_full_roster,
    get_roster,
    get_roster_with_specialists,
    get_specialist_agents,
)
from aegis_gov.council.schemas import AgentRole

# =============================================================================
# Core roster (DEFAULT_AGENTS) — 9 agents
# =============================================================================

def test_default_agents_count():
    assert len(DEFAULT_AGENTS) == 9


def test_executive_council_count():
    assert len(EXECUTIVE_COUNCIL) == 7


def test_red_team_count():
    assert len(RED_TEAM) == 2


def test_default_agents_composition():
    """DEFAULT_AGENTS = 7 executives + 2 red team."""
    tiers = [a.tier for a in DEFAULT_AGENTS]
    assert tiers.count("executive") == 7
    assert tiers.count("red_team") == 2


# =============================================================================
# Specialist agents
# =============================================================================

def test_specialist_agents_count():
    assert len(SPECIALIST_AGENTS) == 8


def test_specialist_agents_tiers():
    tiers = [a.tier for a in SPECIALIST_AGENTS]
    assert tiers.count("reviewer") == 2
    assert tiers.count("specialist") == 6


# =============================================================================
# Full roster (backward compat)
# =============================================================================

def test_full_roster_count():
    """DEFAULT_ROSTER = DEFAULT_AGENTS + SPECIALIST_AGENTS."""
    assert len(DEFAULT_ROSTER) == 17
    assert len(DEFAULT_ROSTER) == len(DEFAULT_AGENTS) + len(SPECIALIST_AGENTS)


# =============================================================================
# Roster access functions
# =============================================================================

def test_get_default_roster():
    roster = get_default_roster()
    assert len(roster) == 9
    assert roster == DEFAULT_AGENTS


def test_get_specialist_agents():
    agents = get_specialist_agents()
    assert len(agents) == 8
    assert agents == SPECIALIST_AGENTS


def test_get_full_roster():
    roster = get_full_roster()
    assert len(roster) == 17
    assert roster == DEFAULT_ROSTER


def test_get_roster_default():
    """get_roster() returns full roster for backward compatibility."""
    roster = get_roster()
    assert len(roster) == len(DEFAULT_ROSTER)


def test_get_roster_with_custom():
    custom = [AgentRole("CustomAgent", "Custom Role", "Custom expertise")]
    roster = get_roster(custom)
    assert len(roster) == len(DEFAULT_ROSTER) + 1
    assert any(a.name == "CustomAgent" for a in roster)


def test_get_roster_with_specialists_default():
    roster = get_roster_with_specialists()
    assert len(roster) == len(DEFAULT_ROSTER)


def test_get_roster_with_specialists_custom():
    custom = [AgentRole("CustomAgent", "Custom Role", "Custom expertise")]
    roster = get_roster_with_specialists(custom)
    assert len(roster) == len(DEFAULT_ROSTER) + 1
    assert any(a.name == "CustomAgent" for a in roster)


# =============================================================================
# Tier filtering
# =============================================================================

def test_get_agents_by_tier():
    executives = get_agents_by_tier("executive")
    assert len(executives) == 7
    assert all(a.tier == "executive" for a in executives)

    red_team = get_agents_by_tier("red_team")
    assert len(red_team) == 2

    reviewers = get_agents_by_tier("reviewer")
    assert len(reviewers) == 2

    specialists = get_agents_by_tier("specialist")
    assert len(specialists) == 6


# =============================================================================
# Data integrity
# =============================================================================

def test_all_agents_have_required_fields():
    for agent in DEFAULT_ROSTER:
        assert agent.name
        assert agent.role
        assert agent.expertise
        assert agent.tier in ("executive", "reviewer", "specialist", "red_team")


def test_no_duplicate_agent_names():
    names = [a.name for a in DEFAULT_ROSTER]
    assert len(names) == len(set(names))
