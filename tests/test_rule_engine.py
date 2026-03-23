"""Tests for the governance rule engine."""

from aegis_gov.council.rule_engine import RuleEngine, RuleVerdict


def test_self_review_blocked():
    engine = RuleEngine()
    result = engine.evaluate(
        agent="Impl",
        action="review",
        context={"author": "Impl"},
    )
    assert result.final_verdict == RuleVerdict.BLOCK
    assert result.blocked


def test_irreversible_action_escalates():
    engine = RuleEngine()
    result = engine.evaluate(
        agent="DevOps",
        action="delete",
        context={"irreversible": True},
    )
    assert result.final_verdict == RuleVerdict.ESCALATE_TO_HUMAN


def test_low_confidence_flagged():
    engine = RuleEngine()
    result = engine.evaluate(
        agent="CTO",
        action="approve",
        context={"confidence": 0.3},
    )
    assert result.final_verdict == RuleVerdict.FLAG


def test_production_deploy_without_tests_blocked():
    engine = RuleEngine()
    result = engine.evaluate(
        agent="DevOps",
        action="deploy",
        context={"environment": "production", "tests_passed": False},
    )
    assert result.final_verdict == RuleVerdict.BLOCK
    assert result.blocked


def test_production_deploy_without_review_escalates():
    engine = RuleEngine()
    result = engine.evaluate(
        agent="DevOps",
        action="deploy",
        context={"environment": "production", "tests_passed": True, "review_approved": False},
    )
    assert result.final_verdict == RuleVerdict.ESCALATE_TO_HUMAN


def test_normal_action_passes():
    engine = RuleEngine()
    result = engine.evaluate(
        agent="Researcher",
        action="analyze",
        context={"confidence": 0.9},
    )
    assert result.final_verdict == RuleVerdict.PASS
    assert result.passed


def test_critical_decision_without_reviews():
    engine = RuleEngine()
    result = engine.evaluate(
        agent="CEO",
        action="approve",
        context={"category": "CRITICAL", "completed_reviews": ["CTO", "CFO"]},
    )
    assert result.final_verdict == RuleVerdict.ESCALATE_TO_HUMAN


def test_add_custom_rule():
    engine = RuleEngine()
    engine.add_rule("custom_rule", {"name": "Custom", "verdict": "BLOCK"})
    assert "custom_rule" in engine.rules


def test_custom_rule_with_condition_evaluates():
    """Custom rules with conditions must actually trigger during evaluate()."""
    engine = RuleEngine()
    engine.add_rule("budget_gate", {
        "name": "Budget Approval",
        "condition": "context.get('amount', 0) > 10000",
        "verdict": "ESCALATE_TO_HUMAN",
        "message": "Spending over $10K needs CFO approval",
    })
    # Should trigger
    result = engine.evaluate("Agent", "purchase", {"amount": 50000})
    triggered_rules = [r.rule_id for r in result.results]
    assert "budget_gate" in triggered_rules

    # Should not trigger
    result2 = engine.evaluate("Agent", "purchase", {"amount": 100})
    triggered_rules2 = [r.rule_id for r in result2.results]
    assert "budget_gate" not in triggered_rules2


def test_remove_rule():
    engine = RuleEngine()
    engine.add_rule("temp_rule", {"name": "Temp"})
    assert engine.remove_rule("temp_rule")
    assert "temp_rule" not in engine.rules


def test_evaluation_result_to_dict():
    engine = RuleEngine()
    result = engine.evaluate("Agent", "test", {})
    d = result.to_dict()
    assert "final_verdict" in d
    assert "agent" in d
    assert "results" in d
