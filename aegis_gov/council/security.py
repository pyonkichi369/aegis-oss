"""
AEGIS Council Security — Input sanitization for governance operations.

Prevents prompt injection and enforces input length limits.
"""

import logging
import re

logger = logging.getLogger(__name__)

# Maximum input lengths
MAX_TOPIC_LENGTH = 2000
MAX_CONTEXT_LENGTH = 5000

# Patterns that indicate prompt injection attempts
_INJECTION_PATTERNS = [
    # System prompt overrides
    re.compile(r"```\s*system\s*```", re.IGNORECASE),
    re.compile(r"<\|im_start\|>", re.IGNORECASE),
    re.compile(r"<\|im_end\|>", re.IGNORECASE),
    # Role override attempts
    re.compile(r"\[SYSTEM\]", re.IGNORECASE),
    re.compile(r"\[INST\]", re.IGNORECASE),
    re.compile(r"<<SYS>>", re.IGNORECASE),
    re.compile(r"<</SYS>>", re.IGNORECASE),
    # Common prompt injection prefixes
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"ignore\s+(all\s+)?above\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?previous", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+", re.IGNORECASE),
    re.compile(r"new\s+instructions?\s*:", re.IGNORECASE),
    re.compile(r"system\s*:\s*you\s+are", re.IGNORECASE),
]


def sanitize_input(text: str, max_length: int = MAX_TOPIC_LENGTH, field_name: str = "input") -> str:
    """
    Sanitize user input to prevent prompt injection.

    Args:
        text: Raw user input
        max_length: Maximum allowed length
        field_name: Name of the field (for logging)

    Returns:
        Sanitized text, truncated to max_length
    """
    if not text:
        return text

    original_length = len(text)
    sanitized = text

    # Strip prompt injection patterns
    for pattern in _INJECTION_PATTERNS:
        match = pattern.search(sanitized)
        if match:
            logger.warning(
                "Prompt injection pattern detected in %s: %r",
                field_name,
                match.group()[:50],
            )
            sanitized = pattern.sub("", sanitized)

    # Truncate to max length
    if len(sanitized) > max_length:
        logger.warning(
            "%s truncated from %d to %d characters",
            field_name,
            original_length,
            max_length,
        )
        sanitized = sanitized[:max_length]

    # Strip leading/trailing whitespace
    sanitized = sanitized.strip()

    return sanitized


def sanitize_context(context: dict, max_length: int = MAX_CONTEXT_LENGTH) -> dict:
    """
    Sanitize a context dictionary by sanitizing all string values.

    Args:
        context: Dictionary of context values
        max_length: Maximum total serialized length

    Returns:
        Sanitized context dictionary
    """
    import json

    if not context:
        return context

    sanitized = {}
    for key, value in context.items():
        sanitized_key = sanitize_input(str(key), max_length=200, field_name=f"context_key:{key}")
        if isinstance(value, str):
            sanitized[sanitized_key] = sanitize_input(
                value, max_length=max_length, field_name=f"context:{key}"
            )
        elif isinstance(value, dict):
            sanitized[sanitized_key] = sanitize_context(value, max_length=max_length)
        else:
            sanitized[sanitized_key] = value

    # Check total serialized length — evict keys until within limit
    serialized = json.dumps(sanitized)
    if len(serialized) > max_length:
        logger.warning("Context serialized length %d exceeds max %d", len(serialized), max_length)
        keys = list(sanitized.keys())
        while len(json.dumps(sanitized)) > max_length and keys:
            removed = keys.pop()
            del sanitized[removed]
            logger.debug("Evicted context key %r to fit length limit", removed)

    return sanitized
