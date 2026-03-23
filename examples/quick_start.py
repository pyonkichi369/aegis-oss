"""
Quick Start — Run a boardroom meeting in 5 lines of code.

Requirements:
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-...

Usage:
    python examples/quick_start.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aegis_gov.council.boardroom import Boardroom

# Create a boardroom with your API key
boardroom = Boardroom(api_key=os.environ["ANTHROPIC_API_KEY"])

# Convene a meeting
result = boardroom.convene(
    topic="Should we rewrite our monolith as microservices?",
    category="STRATEGIC",
    context={
        "current_architecture": "Django monolith",
        "team_size": 5,
        "monthly_users": 50000,
        "pain_points": ["slow deployments", "coupled modules", "scaling issues"],
    },
)

# Print the synthesis (CEO's final decision)
print("=" * 60)
print("BOARDROOM SYNTHESIS")
print("=" * 60)
print(result.synthesis)
print()
print(f"Vote Summary: {result.vote_summary}")
print(f"Session ID: {result.session_id}")
