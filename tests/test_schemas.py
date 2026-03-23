"""Tests for council schemas."""

from aegis_gov.council.schemas import (
    AgentRole,
    BoardroomSession,
    Decision,
    ReviewResult,
    ReviewVerdict,
    Severity,
    Vote,
    VotePosition,
)


def test_decision_auto_generates_id():
    d = Decision(title="Test", description="Test decision")
    assert d.decision_id
    assert d.timestamp


def test_review_result_to_dict():
    r = ReviewResult(
        reviewer="CTO",
        verdict=ReviewVerdict.FLAG,
        findings=["Missing test coverage"],
        severity=Severity.MEDIUM,
        confidence=0.7,
    )
    d = r.to_dict()
    assert d["reviewer"] == "CTO"
    assert d["verdict"] == "FLAG"
    assert d["severity"] == "medium"


def test_vote_to_dict():
    v = Vote(agent="CEO", position=VotePosition.APPROVE, reason="Strong technical case")
    d = v.to_dict()
    assert d["agent"] == "CEO"
    assert d["position"] == "approve"


def test_boardroom_session_vote_summary():
    session = BoardroomSession(topic="Test")
    session.votes = [
        Vote(agent="CEO", position=VotePosition.APPROVE),
        Vote(agent="CTO", position=VotePosition.APPROVE),
        Vote(agent="CFO", position=VotePosition.CONDITIONAL),
        Vote(agent="DevilsAdvocate", position=VotePosition.REJECT),
    ]
    summary = session.vote_summary
    assert summary["approve"] == 2
    assert summary["conditional"] == 1
    assert summary["reject"] == 1


def test_agent_role():
    a = AgentRole("CEO", "Chief Executive", "Strategy", "executive")
    d = a.to_dict()
    assert d["name"] == "CEO"
    assert d["tier"] == "executive"
