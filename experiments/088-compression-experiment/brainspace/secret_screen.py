"""Secret/PII pre-screen (088.002-T, 088.004-T).

A conservative, regex-based detector used to force a decline (never store,
never compress) before any durable write. False positives are acceptable —
false negatives are not. This is deliberately simple/dependency-free; it is
not a production secret scanner.
"""

import re

_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS access key id
    re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"),  # GitHub tokens (ghp_/gho_/ghu_/ghs_/ghr_)
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),  # GitHub fine-grained PAT
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),  # PEM private key headers
    re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),  # JWT-shaped
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]{20,}"),  # generic bearer token
    re.compile(
        r"(?im)^\s*[A-Z0-9_]*(SECRET|TOKEN|API_KEY|PASSWORD|PRIVATE_KEY)[A-Z0-9_]*\s*=\s*\S{8,}"
    ),  # .env-style secret assignment
]


def contains_secret(text: str) -> bool:
    """Return True if ``text`` appears to contain a secret/credential."""
    if not text:
        return False
    return any(pattern.search(text) for pattern in _PATTERNS)
