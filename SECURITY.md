# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT** open a public GitHub issue
2. X (Twitter): [@th19930828](https://x.com/th19930828) or use GitHub's private vulnerability reporting
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Response Timeline

| Severity | Initial Response | Fix Target |
|----------|-----------------|------------|
| Critical | 24 hours | 48 hours |
| High | 48 hours | 7 days |
| Medium | 7 days | 30 days |
| Low | 14 days | Next release |

## Scope

The following are **in scope**:
- `aegis_gov/` — Python governance engine and API
- Docker configurations
- Authentication and authorization logic (`AEGIS_API_KEY`, HMAC comparison)
- Rule condition evaluation (`eval()` sandbox, AST validation)
- Input sanitization and prompt injection defenses

The following are **out of scope**:
- Third-party dependencies (report upstream)
- Social engineering
- Denial of service (no rate limiting by design — operators should place a reverse proxy)
- Vulnerabilities requiring physical access to the host machine

## Rule Condition Security Model

Rule conditions are evaluated via `eval()` with AST pre-validation (`_validate_condition_ast`).

**Blocked constructs:**
- Dunder attribute access (`.__class__`, `.__mro__`, `.__subclasses__`, etc.)
- Dunder name references (`__import__`, `__builtins__`, etc.)
- List/set/dict comprehensions, generator expressions
- Lambda expressions, function definitions
- Import statements

**Safe to use in conditions:**
```python
# These are allowed
"context.get('confidence', 1.0) < 0.6"
"action == 'deploy' and context.get('environment') == 'production'"
"len(context.get('completed_reviews', [])) < 5"
```

**Warning:** `RuleEngine(rules_path=...)` should only be used with **trusted YAML files**.
Never load rule files from untrusted user input. Unsafe conditions are rejected at load time
with an error log entry — they do not silently execute.

## Security Best Practices

When contributing:
- **No hardcoded secrets** (ZERO TOLERANCE) — no API keys, passwords, or tokens as string literals in code
- All credentials via environment variables with empty defaults (e.g., `os.environ.get("KEY", "")`)
- Use `.env.example` as a template — never `.env`
- Validate all user inputs
- Follow the principle of least privilege for agent permissions
- Run `detect-secrets scan` after any auth-related code changes
- Run `pip-audit` when dependencies change (added to CI pipeline)
