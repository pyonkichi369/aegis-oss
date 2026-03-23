"""
Custom Agents — Add your own agents to the council.

Shows how to extend the default roster with domain-specific agents.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aegis_gov.council.boardroom import Boardroom, BoardroomConfig
from aegis_gov.council.schemas import AgentRole

# Define custom agents for your domain
custom_agents = [
    AgentRole(
        name="RegulationExpert",
        role="Regulatory Compliance",
        expertise="GDPR, CCPA, SOC2, HIPAA compliance and data protection",
        tier="specialist",
    ),
    AgentRole(
        name="DomainExpert",
        role="Healthcare Domain Expert",
        expertise="Clinical workflows, patient safety, medical device regulations",
        tier="specialist",
    ),
    AgentRole(
        name="EthicsReviewer",
        role="AI Ethics Reviewer",
        expertise="Algorithmic fairness, bias detection, responsible AI",
        tier="reviewer",
    ),
]

# Configure with custom agents
config = BoardroomConfig(
    api_key=os.environ["ANTHROPIC_API_KEY"],
    custom_agents=custom_agents,
    synthesis_language="en",
    max_debate_rounds=2,
)

boardroom = Boardroom(config=config)

# Run a domain-specific meeting
result = boardroom.convene(
    topic="Should we use LLMs for patient triage recommendations?",
    category="CRITICAL",
    context={
        "domain": "healthcare",
        "risk_level": "patient safety",
        "regulation": "FDA 21 CFR Part 11",
        "data_sensitivity": "PHI (HIPAA protected)",
    },
)

print(result.synthesis)
