"""Evidence oracle (088.004-T).

Extracts "required facts" from an original tool output — exit status lines,
stderr markers, gate/readiness verdict lines, and reference IDs (PR/issue/
commit numbers) — and asserts each fact remains visible verbatim in the
compressed view *without* retrieval. This is the gate that must pass before
any positive-savings claim can be reported (plan condition: byte-equivalent
retrieval and evidence preservation must be PROVEN by tests before reporting
savings).
"""

import re
from dataclasses import dataclass, field

# Horizontal-only failure-signal separator (parity with policy._SEP): a colon
# (optionally followed by spaces/tabs) or one-or-more spaces/tabs, never a
# newline. Because this oracle scans the complete multi-line string, a
# "colon-optional + \s*" form could synthesize a fact across unrelated lines
# ("exit code\n1 item completed"); the horizontal-only delimiter keeps fact
# extraction line-local (093.002-T review finding). The oracle uses \d+ (zero-
# exit forms are also flagged, by design).
_SEP = r"(?::[ \t]*|[ \t]+)"
_RC_SEP = r"(?:=[ \t]*|[ \t]+)"

_FACT_PATTERNS = [
    re.compile(rf"(?i)exit code{_SEP}\d+"),
    re.compile(rf"(?i)exit status{_SEP}\d+"),
    # "exited with code 1", "Process finished with exit code 1"
    # (zero-exit forms also flagged -- evidence preservation is form-based).
    re.compile(rf"(?i)(?:exited|finished) with (?:exit )?code{_SEP}\d+"),
    re.compile(rf"(?i)returncode{_RC_SEP}\d+"),
    # GNU make failure line: "*** [target] Error 1".
    re.compile(r"\*\*\*[ \t]*\[[^\]]*\][ \t]+Error[ \t]+\d+"),
    # npm failure marker -- whole-line match so the full marker line is the
    # required fact.
    re.compile(r"(?im)^.*npm ERR!.*$"),
    re.compile(r"(?im)^stderr:.*$"),
    re.compile(r"P-0\d\d\s+(?:GATE|VIOLATION)[^\n]*"),
    re.compile(r"\bHEAD=\S+"),
    re.compile(r"#\d+"),  # PR / issue reference numbers
]


@dataclass
class OracleResult:
    passed: bool
    required_facts: list = field(default_factory=list)
    missing_facts: list = field(default_factory=list)


def _extract_required_facts(original: str):
    facts = []
    for pattern in _FACT_PATTERNS:
        for match in pattern.finditer(original):
            fact = match.group(0).strip()
            if fact and fact not in facts:
                facts.append(fact)
    return facts


def evaluate_oracle(original: str, compressed: str) -> OracleResult:
    """Evaluate whether ``compressed`` preserves every required fact in ``original``."""
    required_facts = _extract_required_facts(original)
    missing = [fact for fact in required_facts if fact not in compressed]
    return OracleResult(
        passed=len(missing) == 0,
        required_facts=required_facts,
        missing_facts=missing,
    )
