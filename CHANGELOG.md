# Changelog

All notable changes to aegis-gov are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

---

## [0.1.1] — 2026-04-04

### Changed
- **Default model updated**: `claude-sonnet-4-20250514` → `claude-sonnet-4-6` in `BoardroomConfig`, API request models, CLI defaults, and `aegis init` template
- **Ollama provider support** (`provider="ollama"`): boardroom meetings and red-team reviews now run against any locally-hosted model via Ollama's OpenAI-compatible API (`http://localhost:11434/v1`). No API key required.
  ```bash
  aegis convene "Should we adopt microservices?" --provider ollama --model gemma4:latest
  ```
- API endpoints no longer reject Ollama requests when `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` are absent
- `pyproject.toml`: added `ollama = ["openai>=1.0"]` optional dependency group
- Provider comment updated across codebase: `anthropic | openai | ollama`

### Fixed
- `_get_api_key()` in CLI now returns empty string (instead of exiting with error) when `provider=ollama`

---

## [0.1.0] — 2026-03-24

### Added
- **Boardroom Engine** — 6-phase structured multi-agent governance meeting (CEO Opening → Executive Council → Advisory Input → Critical Review → Open Debate → CEO Synthesis)
- **17 Agent Roles** — 7 C-level executives, 2 mandatory Red Team agents (DevilsAdvocate + Skeptic), 8 specialists
- **Rule Engine** — 5-verdict governance system (PASS / FLAG / BLOCK / ESCALATE_TO_HUMAN / HALT) with YAML and Python rule definitions
- **Constitutional Manifesto** — version-controlled governance framework
- **CLI** — `aegis convene`, `aegis review`, `aegis check`, `aegis agents`, `aegis rules`, `aegis init`, `aegis version`
- **REST API** — FastAPI endpoints with SSE streaming, HMAC API key auth, configurable CORS
- **Streaming** — Server-Sent Events for real-time boardroom progress
- **Security** — Input sanitization, prompt injection defense, configurable CORS origins
- **LLM providers** — Anthropic Claude and OpenAI GPT support
- **Compliance annotations** — EU AI Act Article 14, NIST AI RMF, ISO 42001
- **GitHub Action** — `action.yml` for CI/CD governance review integration
- **32 tests** — pytest suite covering rule engine, schemas, agents, streaming
- Apache 2.0 license
