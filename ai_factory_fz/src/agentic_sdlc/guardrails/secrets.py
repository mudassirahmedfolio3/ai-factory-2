"""Secret detection shared by the guardrails (design documents, code changes, deployment files).

Flags real-looking credentials. Obvious placeholders and test values ("sk_test_placeholder",
"staging_test_password", "${DB_PASSWORD}", "changeme") are allowed: agents are told to use them.
"""

import re

PATTERNS = [
    (re.compile(r"\bsk_(live|test)_[A-Za-z0-9]{10,}"), "a Stripe secret key"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "an AWS access key"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "a private key"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"), "a GitHub token"),
    (re.compile(r"\bxox[abpr]-[A-Za-z0-9-]{10,}"), "a Slack token"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"), "a JWT"),
    (re.compile(r"\b(postgres(?:ql)?|mysql|mongodb(?:\+srv)?)://[^\s:/@]+:[^\s@/]+@"), "a connection string with a password"),
]
_PLACEHOLDER = re.compile(r"placeholder|example|dummy|changeme|change_me|xxxx|test|local|\$\{|\$[A-Z_]|<[^>]+>",
                          re.IGNORECASE)


def find(text: str) -> list[str]:
    """What kinds of secrets the text contains (placeholders and test values excluded)."""
    found = []
    for pattern, what in PATTERNS:
        if any(not _PLACEHOLDER.search(m.group(0)) for m in pattern.finditer(text)):
            found.append(what)
    return found
