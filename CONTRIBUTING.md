# Contributing to AEGIS

Thank you for your interest in contributing to AEGIS! This guide will help you get started.

## Quick Start — Your First PR in 10 Minutes

1. Fork and clone the repository
2. Run the project:
   ```bash
   docker compose up
   ```
3. Open `http://localhost:8000/docs` to see the API
4. Pick a [good first issue](https://github.com/pyonkichi369/aegis-oss/labels/good%20first%20issue)
5. Make your changes and submit a PR

## Development Setup

### Prerequisites

- Python 3.10+
- Docker & Docker Compose (optional)

### Local Development (without Docker)

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment config
cp .env.example .env
# Edit .env with your API key

# Run the server
uvicorn aegis_gov.api:app --reload
```

### Running Tests

```bash
# All tests
pytest tests/

# Specific test file
pytest tests/test_rule_engine.py -v

# With coverage
pytest tests/ --cov=aegis_gov --cov-report=html
```

## What to Contribute

### High-Impact Areas

- **New agent prompts** — Add specialized roles in `aegis_gov/council/prompts/`
- **Governance templates** — Create manifesto variants for different domains
- **LLM provider support** — Add providers beyond Anthropic/OpenAI
- **Custom rules** — Add governance rules for specific compliance frameworks
- **Documentation** — Improve guides and examples
- **Tests** — Increase coverage

### Contribution Guidelines

1. **One PR per feature/fix** — Keep PRs focused and reviewable
2. **Tests required** — New features need tests; bug fixes need regression tests
3. **Follow existing patterns** — Read the code before writing new code
4. **No secrets** — Never commit API keys. Use `.env.example` for templates
5. **Type hints** — Use Python type hints for all function signatures

## Code Style

- **Python**: Follow PEP 8, enforced by `ruff`
- **Commits**: Conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`)

## Pull Request Process

1. Create a feature branch: `git checkout -b feat/my-feature`
2. Make your changes with tests
3. Run linting: `ruff check aegis_gov/`
4. Submit PR with a clear description
5. Address review feedback
6. Maintainer merges after approval

## Code of Conduct

Be respectful, constructive, and inclusive. We follow the [Contributor Covenant](https://www.contributor-covenant.org/).

## Questions?

- Open a [Discussion](https://github.com/pyonkichi369/aegis-oss/discussions)
- Check existing issues before creating new ones
