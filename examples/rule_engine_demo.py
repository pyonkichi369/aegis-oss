"""
Rule Engine Demo — Governance guardrails for AI agent actions.

Shows how the rule engine evaluates agent actions and returns verdicts.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aegis_gov.council.rule_engine import RuleEngine

engine = RuleEngine()

print("=" * 50)
print("AEGIS Rule Engine Demo")
print("=" * 50)

# Example 1: Self-review (BLOCKED)
print("\n--- Test 1: Self-Review ---")
result = engine.evaluate(
    agent="ImplementationAgent",
    action="review",
    context={"author": "ImplementationAgent"},
)
print(f"Verdict: {result.final_verdict.name}")
print(f"Passed: {result.passed}")
for r in result.results:
    print(f"  Rule: {r.rule_name} → {r.verdict.name}: {r.message}")

# Example 2: Low confidence action (FLAGGED)
print("\n--- Test 2: Low Confidence ---")
result = engine.evaluate(
    agent="AI_CTO",
    action="approve",
    context={"confidence": 0.4},
)
print(f"Verdict: {result.final_verdict.name}")

# Example 3: Production deploy without tests (BLOCKED)
print("\n--- Test 3: Unsafe Deploy ---")
result = engine.evaluate(
    agent="DevOps",
    action="deploy",
    context={"environment": "production", "tests_passed": False},
)
print(f"Verdict: {result.final_verdict.name}")
print(f"Blocked: {result.blocked}")

# Example 4: Normal operation (PASS)
print("\n--- Test 4: Normal Operation ---")
result = engine.evaluate(
    agent="Researcher",
    action="analyze",
    context={"confidence": 0.9},
)
print(f"Verdict: {result.final_verdict.name}")
print(f"Passed: {result.passed}")
