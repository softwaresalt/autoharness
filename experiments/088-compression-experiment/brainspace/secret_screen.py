"""Secret/PII pre-screen (088.002-T, 088.004-T).

A conservative, regex-based detector used to force a decline (never store,
never compress) before any durable write. False positives are acceptable —
false negatives are not. This is deliberately simple/dependency-free; it is
not a production secret scanner.

PII coverage is intentionally narrow and explicit: email addresses (the most
common PII incidentally present in ordinary tool output, e.g. `git log`
author lines) are detected. This is not a general-purpose PII scanner (no
phone numbers, physical addresses, SSNs, etc.) -- treat any broader PII
claim as out of scope for this throwaway experiment.
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
    re.compile(
        r'(?i)["\']?[A-Za-z0-9_]*(SECRET|TOKEN|API[_-]?KEY|PASSWORD|'
        r'PRIVATE[_-]?KEY|ACCESS[_-]?KEY)[A-Za-z0-9_]*["\']?\s*[:=]\s*'
        r'["\']?[^\s,"\']{6,}'
    ),  # structured key/value forms (JSON/YAML/etc.), not just dotenv KEY=value
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),  # email address (PII)
]


def contains_secret(text: str) -> bool:
    """Return True if ``text`` appears to contain a secret/credential."""
    if not text:
        return False
    return any(pattern.search(text) for pattern in _PATTERNS)
