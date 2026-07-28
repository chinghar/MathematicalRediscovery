"""Core matching: apply the transform battery to a query and rank hits.

Calibrated toward false positives: every candidate the index turns up is
surfaced (rather than hidden behind a binary yes/no), but tagged with an
honest confidence band derived from how much of the sequence actually lined
up and how trustworthy the transform that produced the hit tends to be.
"""

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set

from . import cache, keying
from .transforms import TRANSFORMS

# Evidentiary weight per transform: higher means a given overlap length is
# stronger evidence of a real match (e.g. an exact value hit via `identity`
# is far less likely to be coincidence than one recovered from `bisect_even`,
# which throws away half the information before comparing).
TRANSFORM_TIER: Dict[str, int] = {
    "identity": 3,
    "offset": 3,  # identity match that only lined up after offset realignment
    "drop1": 3,
    "drop2": 3,
    "drop3": 3,
    "negate": 2,
    "alt_sign": 2,
    "plus1": 2,
    "minus1": 2,
    "scale_x2": 2,
    "scale_x3": 2,
    "scale_div2": 2,
    "scale_div3": 2,
    "diff1": 2,
    "partial_sums": 2,
    "plus_n": 1,
    "minus_n": 1,
    "diff2": 1,
    "partial_products": 1,
    "bisect_even": 1,
    "bisect_odd": 1,
    "abs": 1,
}

CONFIDENCE_ORDER = {"high": 2, "medium": 1, "low": 0}


@dataclass(frozen=True)
class MatchResult:
    anum: str
    name: str
    transform: str
    confidence: str
    overlap: int

    def __str__(self) -> str:
        return f"{self.anum}  [{self.confidence}, {self.transform}, overlap={self.overlap}]  {self.name}"


def _connect(index_path: Optional[Path] = None) -> sqlite3.Connection:
    path = index_path or cache.index_path()
    if not path.exists():
        raise FileNotFoundError(f"No index found at {path}. Run `seqprior fetch` first.")
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def _lookup_candidates(conn: sqlite3.Connection, terms: Sequence[int]) -> Set[str]:
    key, klen = keying.canonical_key(terms)
    if klen < keying.MIN_KEY_TERMS:
        return set()

    cur = conn.cursor()
    candidates: Set[str] = set()
    parts = key.split(",")

    # Exact matches, including cases where the DB entry's own key is shorter
    # than ours (a short/rare OEIS sequence).
    for length in range(len(parts), keying.MIN_KEY_TERMS - 1, -1):
        sub_key = ",".join(parts[:length])
        cur.execute("SELECT anum FROM seq WHERE key = ?", (sub_key,))
        candidates.update(row[0] for row in cur.fetchall())

    # DB entries whose key extends ours (our query key was truncated below
    # the max, so allow it to match as a prefix of a longer stored key).
    if klen < keying.MAX_KEY_TERMS:
        cur.execute("SELECT anum FROM seq WHERE key LIKE ?", (key + ",%",))
        candidates.update(row[0] for row in cur.fetchall())

    return candidates


def _overlap(a: Sequence[int], b: Sequence[int]) -> int:
    n = min(len(a), len(b))
    overlap = 0
    for x, y in zip(a[:n], b[:n]):
        if x != y:
            break
        overlap += 1
    return overlap


def _verify(transformed: Sequence[int], stored_terms: Sequence[int]) -> tuple:
    """Return (overlap_length, needed_offset_realignment).

    If the query and the stored sequence already agree on their first term,
    compare them as-is so a real match isn't docked for terms that happen to
    be 0/1. Only fall back to comparing the 0/1-stripped versions (crediting
    the "offset" label) when the raw first terms disagree.
    """
    if not transformed or not stored_terms:
        return 0, False
    if transformed[0] == stored_terms[0]:
        return _overlap(transformed, stored_terms), False
    t = keying.strip_leading_ambiguous(transformed)
    s = keying.strip_leading_ambiguous(stored_terms)
    return _overlap(t, s), True


def _confidence(overlap: int, transform: str) -> str:
    score = overlap + TRANSFORM_TIER.get(transform, 1)
    if score >= 10:
        return "high"
    if score >= 7:
        return "medium"
    return "low"


def _rank_key(r: MatchResult):
    return (-CONFIDENCE_ORDER[r.confidence], -r.overlap, -TRANSFORM_TIER.get(r.transform, 0), r.anum)


def match(
    seq: Sequence[int],
    *,
    top_k: int = 10,
    index_path: Optional[str] = None,
) -> List[MatchResult]:
    """Return ranked candidate OEIS matches for an integer sequence.

    Never asserts novelty: an empty list means no candidate was found under
    any of the registered transforms, which is weak evidence, not proof.
    """
    seq = list(seq)
    if not seq:
        return []

    conn = _connect(Path(index_path) if index_path else None)
    try:
        best: Dict[str, MatchResult] = {}
        for name, fn in TRANSFORMS.items():
            transformed = fn(seq)
            if not transformed or len(transformed) < keying.MIN_KEY_TERMS:
                continue

            for anum in _lookup_candidates(conn, transformed):
                row = conn.execute("SELECT name, terms FROM seq WHERE anum = ?", (anum,)).fetchone()
                if row is None:
                    continue
                db_name, terms_str = row
                stored_terms = [int(x) for x in terms_str.split(",") if x != ""]

                overlap, shifted = _verify(transformed, stored_terms)
                if overlap < keying.MIN_KEY_TERMS:
                    continue

                label = "offset" if (name == "identity" and shifted) else name
                candidate = MatchResult(anum, db_name, label, _confidence(overlap, label), overlap)

                existing = best.get(anum)
                if existing is None or _rank_key(candidate) < _rank_key(existing):
                    best[anum] = candidate

        return sorted(best.values(), key=_rank_key)[:top_k]
    finally:
        conn.close()
