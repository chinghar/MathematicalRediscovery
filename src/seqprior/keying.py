"""Canonical-key derivation shared by index building and query lookup.

Both sides must use identical logic, since matching works by exact string
comparison on this key.
"""

from typing import List, Sequence, Tuple

MAX_KEY_TERMS = 8
MIN_KEY_TERMS = 4

_AMBIGUOUS = (0, 1)


def strip_leading_ambiguous(terms: Sequence[int]) -> List[int]:
    """Drop a leading run of 0/1 values.

    Many OEIS sequences share a 0/1-heavy prefix (offset conventions, indicator
    sequences, etc.), so those terms carry little identifying signal and are
    dropped before keying. Always leaves at least one term.
    """
    i = 0
    while i < len(terms) - 1 and terms[i] in _AMBIGUOUS:
        i += 1
    return list(terms[i:])


def canonical_key(terms: Sequence[int], max_terms: int = MAX_KEY_TERMS) -> Tuple[str, int]:
    """Return (key_string, key_length) for a term sequence."""
    trimmed = strip_leading_ambiguous(terms)[:max_terms]
    return ",".join(str(t) for t in trimmed), len(trimmed)
