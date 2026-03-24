[English](README.md) | [日本語](README_ja.md)

<div align="center">

# AEGIS

### Governance-First Framework for AI Agent Systems

**Your AI agents need adult supervision.**<br>
Structured boardroom debates. Mandatory red team. Governance guardrails that actually enforce.

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/Tests-32_passed-brightgreen.svg)]()
[![PyPI](https://img.shields.io/badge/PyPI-aegis--gov-orange.svg)](https://pypi.org/project/aegis-gov/)

[Quick Start](#quick-start) · [Why AEGIS?](#why-aegis) · [CLI](#cli) · [GitHub Action](#github-action) · [API](#api) · [Contributing](CONTRIBUTING.md)

</div>

---

## 60-Second Demo

```bash
pip install aegis-gov
export ANTHROPIC_API_KEY=sk-...

# Run a governance review on any decision
aegis convene "Should we mass-email all users about the new feature?" --category TACTICAL

# Check an action against governance rules (no LLM needed)
aegis check DevOps deploy --context environment=production tests_passed=true review_approved=false
# → ESCALATE_TO_HUMAN: Production deployment requires passing tests and review approval
```

```python
from aegis_gov import Boardroom

boardroom = Boardroom()
result = boardroom.convene(
    topic="Should we migrate to microservices?",
    category="STRATEGIC",
    context={"team_size": 5, "current_arch": "monolith"},
)

print(result.synthesis)       # CEO's final decision
print(result.vote_summary)    # {"approve": 7, "conditional": 2, "reject": 0, "abstain": 0}
print(result.confidence)      # 0.85
```

## Why AEGIS?

Every other multi-agent framework helps AI agents **do things**. AEGIS makes sure they **should**.

| | AEGIS | CrewAI | AutoGen | LangGraph | MetaGPT |
|---|:---:|:---:|:---:|:---:|:---:|
| Governance rule engine | **Yes** | No | No | No | No |
| Mandatory red team review | **Yes** | No | No | No | No |
| Constitutional manifesto | **Yes** | No | No | No | No |
| Decision audit trail | **Yes** | Partial | No | No | Partial |
| Verdict enforcement (BLOCK/HALT) | **Yes** | No | No | No | No |
| Human escalation gates | **Yes** | Manual | Manual | Manual | Manual |
| LLM-agnostic | **Yes** | Yes | Yes | Yes | No |

**AEGIS is not a replacement for these frameworks.** It's the governance layer you add on top.

### Who is this for?

- **Teams deploying AI agents** who need accountability and audit trails
- **Compliance-conscious orgs** preparing for EU AI Act, NIST AI RMF, ISO 42001
- **Anyone** who doesn't want their AI agents making irreversible decisions unsupervised

## Features

### Boardroom Meetings (6 phases)

17 AI agents with distinct roles debate every decision:

| Phase | What happens |
|-------|-------------|
| 1. CEO Opening | Classify topic (CRITICAL/STRATEGIC/TACTICAL/OPERATIONAL), set format |
| 2. Executive Council | 7 C-level perspectives (CEO, CTO, CFO, CRO, CMO, CPO, CDO) |
| 3. Advisory Input | 8 specialists contribute domain expertise |
| 4. Critical Review | **Red Team + reviewers challenge consensus** |
| 5. Open Debate | Cross-agent discussion |
| 6. CEO Synthesis | Final decision with vote tally, confidence score, and action items |

### Red Team (Non-Optional)

Every decision is stress-tested. The red team **cannot be disabled** in the default configuration.

- **DevilsAdvocate** -- Challenges assumptions, demands evidence, finds hidden risks
- **Skeptic** -- Explores alternatives, runs pre-mortem analysis, detects groupthink

### Rule Engine (5 built-in rules)

Governance guardrails that **enforce**, not advise:

```python
from aegis_gov import RuleEngine

engine = RuleEngine()

# Self-review → BLOCK (agents can't review their own work)
engine.evaluate("Agent", "review", {"author": "Agent"})

# Low confidence → FLAG
engine.evaluate("CTO", "approve", {"confidence": 0.3})

# Production deploy without review → ESCALATE_TO_HUMAN
engine.evaluate("DevOps", "deploy", {
    "environment": "production",
    "tests_passed": True,
    "review_approved": False,
})
```

| Verdict | Action |
|---------|--------|
| `PASS` | Execute normally |
| `FLAG` | Proceed with caution, log warning |
| `BLOCK` | Prevent action entirely |
| `ESCALATE_TO_HUMAN` | Requires human approval |
| `HALT` | Stop all processes immediately |

### Governance Manifesto

A constitutional framework (version-controlled, auditable):
- Human sovereignty -- humans always have final authority
- Decision categories with TTL and review requirements
- Role separation -- decision-makers, implementers, and reviewers are distinct
- Confidence scoring mandatory for all decisions

## Quick Start

### Option 1: pip install (recommended)

```bash
pip install aegis-gov[anthropic]   # or aegis-gov[openai] or aegis-gov[all]
export ANTHROPIC_API_KEY=sk-...

# Generate a starter config (customizable rules + agents)
aegis init

# Run your first boardroom meeting
aegis convene "Should we mass-email all users?" --category TACTICAL
```

### Option 2: Docker

```bash
git clone https://github.com/pyonkichi369/aegis-oss.git
cd aegis-oss
cp .env.example .env  # Add your ANTHROPIC_API_KEY
docker compose up
# API at http://localhost:8000/docs
```

### Option 3: From source

```bash
git clone https://github.com/pyonkichi369/aegis-oss.git
cd aegis-oss
pip install -e ".[dev]"
aegis convene "Test topic" --category OPERATIONAL
```

## CLI

```
aegis convene "topic"    Run a full boardroom meeting
aegis review "artifact"  Standalone red team review
aegis check AGENT ACTION Evaluate action against rules
aegis agents             List the agent roster
aegis rules              List governance rules
aegis init               Create starter config
aegis version            Print version
```

Options for `convene`:
```
--category    OPERATIONAL | TACTICAL | STRATEGIC | CRITICAL (default: TACTICAL)
--model       LLM model (default: claude-sonnet-4-20250514)
--provider    anthropic | openai (default: anthropic)
--rounds      Debate rounds (default: 2)
--output      json | text (default: text)
```

## GitHub Action

Add AI governance review to your pull requests:

```yaml
# .github/workflows/aegis-review.yml
name: AEGIS Governance Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: pyonkichi369/aegis-oss@v1
        with:
          api-key: ${{ secrets.ANTHROPIC_API_KEY }}
          category: TACTICAL
          fail-on: BLOCK  # BLOCK | ESCALATE | FLAG | never
```

The action runs a boardroom review on the PR diff and posts the verdict as a check result.

## API

Start the server: `uvicorn aegis_gov.api:app --reload`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check (public) |
| `/api/v1/boardroom` | POST | Run a boardroom meeting |
| `/api/v1/review` | POST | Standalone red team review |
| `/api/v1/rules/check` | POST | Evaluate action against rules |
| `/api/v1/rules` | GET | List active governance rules |
| `/api/v1/agents` | GET | List council agents |

Authentication: `X-API-Key` header (set `AEGIS_API_KEY` env var). Dev mode allows unauthenticated access.

Full docs: `http://localhost:8000/docs`

## Customization

### Add Domain-Specific Agents

```python
from aegis_gov import Boardroom, BoardroomConfig, AgentRole

config = BoardroomConfig(
    custom_agents=[
        AgentRole("HIPAAOfficer", "Compliance", "HIPAA, PHI, healthcare data", "reviewer"),
        AgentRole("MLEngineer", "ML Systems", "Model deployment, A/B testing", "specialist"),
    ],
)
boardroom = Boardroom(config)
```

### Add Custom Rules (Python)

Rules use `condition` expressions evaluated with `agent`, `action`, `context`, and `rule` variables:

```python
from aegis_gov import RuleEngine

engine = RuleEngine()
engine.add_rule("budget_gate", {
    "name": "Budget Approval",
    "condition": "context.get('amount', 0) > 10000",
    "verdict": "ESCALATE_TO_HUMAN",
    "message": "Spending over $10K needs CFO approval",
})

# Now this triggers the custom rule
result = engine.evaluate("Agent", "purchase", {"amount": 50000})
print(result.final_verdict)  # ESCALATE_TO_HUMAN
```

### Custom Rules from YAML

```yaml
# my_rules.yaml
rules:
  - id: pii_gate
    name: PII Access Gate
    condition: "context.get('data_type') == 'PII'"
    verdict: ESCALATE_TO_HUMAN
    message: Accessing PII requires privacy review

  - id: after_hours_block
    name: After Hours Deploy Block
    condition: "action == 'deploy' and context.get('hour', 12) >= 22"
    verdict: BLOCK
    message: No deployments after 10pm
```

```python
engine = RuleEngine(rules_path="my_rules.yaml")
```

### Quick Setup with `aegis init`

```bash
aegis init                    # Creates aegis.yaml with examples
aegis init --output custom.yaml  # Custom output path
# Edit the generated file, then use it:
# engine = RuleEngine(rules_path="aegis.yaml")
```

### Use with Any LLM

```python
# OpenAI
boardroom = Boardroom(BoardroomConfig(provider="openai", model="gpt-4o"))

# Ollama (local)
boardroom = Boardroom(BoardroomConfig(
    provider="openai",
    base_url="http://localhost:11434/v1",
    model="llama3",
))
```

## Architecture

```
aegis-oss/
├── aegis_gov/
│   ├── council/
│   │   ├── boardroom.py      # 6-phase meeting engine
│   │   ├── rule_engine.py    # 5-verdict governance rules
│   │   ├── schemas.py        # Type-safe data models
│   │   ├── agents.py         # 9 default + 8 specialist agents
│   │   ├── security.py       # Input sanitization & prompt injection defense
│   │   └── prompts/          # Agent system prompts + manifesto
│   ├── api.py                # FastAPI REST (auth, CORS)
│   └── cli.py                # CLI tool (aegis command)
├── action.yml                # GitHub Action definition
├── examples/                 # quick_start, custom_agents, rule_engine_demo
├── tests/                    # 32 tests
├── pyproject.toml            # Package config (aegis-gov)
└── docker/                   # Container setup
```

## Examples

| Example | What it shows |
|---------|---------------|
| [`quick_start.py`](examples/quick_start.py) | First boardroom meeting in 10 lines |
| [`custom_agents.py`](examples/custom_agents.py) | Adding healthcare compliance agents |
| [`rule_engine_demo.py`](examples/rule_engine_demo.py) | 4 governance scenarios |

## Compliance & Standards

AEGIS provides tooling support for:
- **EU AI Act** (Article 14: Human oversight of high-risk AI)
- **NIST AI Risk Management Framework** (AI RMF 1.0)
- **ISO/IEC 42001** (AI Management Systems)

The audit trail, decision categorization, and human escalation gates map directly to these standards' requirements.

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md).

**Good first issues:**
- Add agent prompts for new domains (finance, healthcare, legal)
- Add governance rules for specific compliance frameworks
- Improve test coverage

## License

Apache 2.0 -- see [LICENSE](LICENSE)
