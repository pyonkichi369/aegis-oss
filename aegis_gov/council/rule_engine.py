"""
AEGIS Rule Engine — Decision classification and auto-approval framework.

Evaluates actions against governance rules and determines whether to
PASS, FLAG, BLOCK, ESCALATE, or HALT.

Usage:
    from aegis_gov import RuleEngine

    engine = RuleEngine()
    result = engine.evaluate(
        agent="ImplementationAgent",
        action="deploy",
        context={"environment": "production", "tests_passed": True},
    )
    print(result.final_verdict)  # RuleVerdict.ESCALATE_TO_HUMAN

Custom rules:
    engine.add_rule("budget_gate", {
        "name": "Budget Approval",
        "condition": "context.get('amount', 0) > 10000",
        "verdict": "ESCALATE_TO_HUMAN",
        "message": "Spending over $10K needs CFO approval",
    })
"""

import ast
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class RuleVerdict(Enum):
    """Possible outcomes from rule evaluation."""
    PASS = 0
    FLAG = 1
    BLOCK = 2
    ESCALATE_TO_HUMAN = 3
    HALT = 4


@dataclass
class RuleResult:
    """Result of evaluating an action against governance rules."""
    rule_id: str
    rule_name: str
    verdict: RuleVerdict
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Aggregated result from all rule evaluations."""
    final_verdict: RuleVerdict
    results: list[RuleResult]
    agent: str
    action: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def passed(self) -> bool:
        return self.final_verdict in (RuleVerdict.PASS, RuleVerdict.FLAG)

    @property
    def blocked(self) -> bool:
        return self.final_verdict in (RuleVerdict.BLOCK, RuleVerdict.HALT)

    def to_dict(self) -> dict[str, Any]:
        return {
            "final_verdict": self.final_verdict.name,
            "agent": self.agent,
            "action": self.action,
            "passed": self.passed,
            "results": [
                {"rule": r.rule_name, "verdict": r.verdict.name, "message": r.message}
                for r in self.results
            ],
            "timestamp": self.timestamp,
        }


# =============================================================================
# Default Rules
# =============================================================================

DEFAULT_RULES = {
    "self_review_prohibition": {
        "name": "Self-Review Prohibition",
        "description": "Agents cannot review their own work",
        "condition": "action == 'review' and context.get('author') == agent",
        "verdict": "BLOCK",
        "message": "{agent} cannot review their own work",
    },
    "irreversible_action_gate": {
        "name": "Irreversible Action Gate",
        "description": "Irreversible actions require human approval",
        "condition": "context.get('irreversible', False)",
        "verdict": "ESCALATE_TO_HUMAN",
        "message": "Irreversible action '{action}' requires human approval",
    },
    "low_confidence_flag": {
        "name": "Low Confidence Flag",
        "description": "Flag actions with confidence below threshold",
        "condition": "context.get('confidence', 1.0) < rule.get('threshold', 0.6)",
        "verdict": "FLAG",
        "message": "Confidence {confidence} below threshold {threshold}",
        "threshold": 0.6,
    },
    "critical_decision_halt": {
        "name": "Critical Decision Requires Full Review",
        "description": "CRITICAL decisions need 5 reviews and human approval",
        "condition": "context.get('category') == 'CRITICAL' and len(context.get('completed_reviews', [])) < 5",
        "verdict": "ESCALATE_TO_HUMAN",
        "message": "CRITICAL decision has {review_count}/5 reviews",
    },
    "production_deploy_gate": {
        "name": "Production Deploy Gate",
        "description": "Production deployments need tests and review",
        "condition": (
            "action == 'deploy' and context.get('environment') == 'production'"
            " and (not context.get('tests_passed', False) or not context.get('review_approved', False))"
        ),
        "verdict": "ESCALATE_TO_HUMAN",
        "message": "Production deployment requires passing tests and review approval",
    },
}

# Safe builtins for condition evaluation (no __import__, exec, eval, etc.)
_SAFE_BUILTINS = {"len": len, "str": str, "int": int, "float": float, "bool": bool, "True": True, "False": False}

# AST node types allowed in condition expressions
_ALLOWED_AST_NODES = (
    ast.Expression, ast.BoolOp, ast.BinOp, ast.UnaryOp, ast.Compare,
    ast.Call, ast.Attribute, ast.Subscript, ast.Name, ast.Constant,
    ast.List, ast.Dict, ast.Tuple, ast.And, ast.Or, ast.Not,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.In, ast.NotIn, ast.Is, ast.IsNot,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.IfExp,
    # Python 3.9+
    *(getattr(ast, n) for n in ("Index", "Load", "Store") if hasattr(ast, n)),
)


def _validate_condition_ast(condition: str) -> None:
    """
    Validate a rule condition string is safe to eval.

    Blocks:
    - Dunder attribute access (__class__, __mro__, __subclasses__, etc.)
    - Import statements
    - Function definitions / lambda
    - Walrus operator / comprehensions
    Raises ValueError if the condition contains disallowed constructs.
    """
    try:
        tree = ast.parse(condition, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Invalid condition syntax: {e}") from e

    for node in ast.walk(tree):
        # Block any node type not in the allowlist
        if not isinstance(node, _ALLOWED_AST_NODES):
            raise ValueError(
                f"Disallowed construct in condition: {type(node).__name__}. "
                "Conditions must be simple comparison/boolean expressions."
            )
        # Block dunder attribute access (__class__, __mro__, etc.)
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise ValueError(
                f"Dunder attribute access disallowed in condition: .{node.attr}"
            )
        # Block dunder name references (__import__, __builtins__, etc.)
        if isinstance(node, ast.Name) and node.id.startswith("__"):
            raise ValueError(
                f"Dunder name reference disallowed in condition: {node.id}"
            )


class RuleEngine:
    """
    Governance rule engine for multi-agent systems.

    Evaluates agent actions against a set of configurable rules
    and returns a verdict determining whether the action should proceed.

    Rules can define a ``condition`` string that is evaluated as a Python
    expression with access to ``agent``, ``action``, ``context``, and ``rule``
    variables. Rules without a ``condition`` are always triggered.
    """

    def __init__(self, rules_path: str | None = None):
        """
        Initialize with optional custom rules YAML file.

        Args:
            rules_path: Path to custom rules YAML. Uses defaults if None.
        """
        self.rules = dict(DEFAULT_RULES)
        if rules_path:
            self._load_rules(rules_path)

    def _load_rules(self, path: str) -> None:
        """Load rules from a YAML file."""
        try:
            with open(path) as f:
                custom = yaml.safe_load(f) or {}
            if "rules" in custom:
                for rule in custom["rules"]:
                    rule_id = rule.get("id", rule.get("name", "").lower().replace(" ", "_"))
                    condition = rule.get("condition")
                    if condition:
                        try:
                            _validate_condition_ast(condition)
                        except ValueError as e:
                            logger.error("Skipping rule %s — unsafe condition: %s", rule_id, e)
                            continue
                    self.rules[rule_id] = rule
            else:
                self.rules.update(custom)
            logger.info("Loaded %d rules from %s", len(self.rules), path)
        except Exception as e:
            logger.warning("Failed to load rules from %s: %s", path, e)

    def _evaluate_condition(
        self, condition: str, agent: str, action: str, context: dict[str, Any], rule: dict[str, Any]
    ) -> bool:
        """
        Safely evaluate a rule condition expression.

        Validates the condition AST before evaluation to block sandbox-escape
        techniques (dunder attribute traversal, imports, comprehensions, etc.).
        Falls back to False (safe default) on any error.
        """
        try:
            _validate_condition_ast(condition)
        except ValueError as e:
            logger.error("Blocked unsafe rule condition: %s — %s", condition[:80], e)
            return False

        eval_globals = {"__builtins__": _SAFE_BUILTINS}
        eval_locals = {"agent": agent, "action": action, "context": context, "rule": rule}
        try:
            return bool(eval(condition, eval_globals, eval_locals))  # noqa: S307
        except Exception as e:
            logger.warning("Rule condition evaluation failed: %s — %s", condition[:80], e)
            return False

    def evaluate(
        self,
        agent: str,
        action: str,
        context: dict[str, Any] | None = None,
    ) -> EvaluationResult:
        """
        Evaluate an action against all governance rules.

        Each rule with a ``condition`` field is evaluated. If the condition
        is true (or absent), the rule triggers and its verdict is recorded.

        Args:
            agent: Name of the agent performing the action
            action: Type of action (e.g., "deploy", "review", "implement")
            context: Additional context for rule evaluation

        Returns:
            EvaluationResult with aggregated verdict
        """
        ctx = context or {}
        results = []

        for rule_id, rule in self.rules.items():
            condition = rule.get("condition")
            if condition is None:
                # Rules without conditions always trigger
                triggered = True
            else:
                triggered = self._evaluate_condition(condition, agent, action, ctx, rule)

            if triggered:
                verdict_str = rule.get("verdict", "FLAG")
                try:
                    verdict = RuleVerdict[verdict_str]
                except KeyError:
                    logger.warning("Unknown verdict '%s' in rule %s, defaulting to FLAG", verdict_str, rule_id)
                    verdict = RuleVerdict.FLAG

                # Build message with template variables
                msg_template = rule.get("message", rule.get("description", f"Rule {rule_id} triggered"))
                try:
                    msg = msg_template.format(
                        agent=agent, action=action,
                        confidence=ctx.get("confidence", "N/A"),
                        threshold=rule.get("threshold", "N/A"),
                        review_count=len(ctx.get("completed_reviews", [])),
                    )
                except (KeyError, IndexError):
                    msg = msg_template

                # Special case: production deploy gate differentiates tests vs review
                if rule_id == "production_deploy_gate" and triggered:
                    if not ctx.get("tests_passed", False):
                        verdict = RuleVerdict.BLOCK
                        msg = "Cannot deploy to production without passing tests"
                    else:
                        verdict = RuleVerdict.ESCALATE_TO_HUMAN
                        msg = "Production deployment requires review approval"

                results.append(RuleResult(
                    rule_id=rule_id,
                    rule_name=rule.get("name", rule_id),
                    verdict=verdict,
                    message=msg,
                ))

        # If no rules triggered, PASS
        if not results:
            results.append(RuleResult(
                rule_id="default_pass",
                rule_name="Default Pass",
                verdict=RuleVerdict.PASS,
                message="No rules triggered",
            ))

        # Aggregate: highest severity wins
        final = max(results, key=lambda r: r.verdict.value)

        return EvaluationResult(
            final_verdict=final.verdict,
            results=results,
            agent=agent,
            action=action,
        )

    def add_rule(self, rule_id: str, rule: dict[str, Any]) -> None:
        """
        Add or update a governance rule.

        If ``rule`` contains a ``condition`` key, it will be evaluated as
        a Python expression during ``evaluate()``. Available variables:
        ``agent``, ``action``, ``context``, ``rule``.

        Raises ValueError if the condition contains disallowed constructs
        (dunder access, imports, comprehensions, etc.).

        Args:
            rule_id: Unique identifier for the rule
            rule: Rule definition dict with keys: name, condition, verdict, message
        """
        condition = rule.get("condition")
        if condition:
            _validate_condition_ast(condition)  # raises ValueError on unsafe condition
        self.rules[rule_id] = rule
        logger.info("Rule added/updated: %s", rule_id)

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule by ID. Returns True if the rule existed."""
        if rule_id in self.rules:
            del self.rules[rule_id]
            return True
        return False
