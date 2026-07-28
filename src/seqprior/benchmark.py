"""Reproducible recall/precision evaluation harness.

Samples real OEIS sequences from the local index, mangles each one with a
transform from the registry to produce a synthetic query, and checks whether
`match()` recovers the original A-number. This directly measures how well
each transform round-trips through the matcher: some transforms (bisection,
second differences, partial products) discard information and have no
general inverse in the registry, so low recall for those rows is expected —
the benchmark's job is to make that visible, not to hide it.

A second, negative track runs the matcher against random noise sequences and
checks that it (mostly) reports no match, as a sanity check on false-positive
calibration.
"""

import random
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from . import keying
from .match import _connect, match as run_match
from .transforms import TRANSFORMS

MIN_SAMPLE_TERMS = 10
MAX_QUERY_TERMS = 12
NEGATIVE_LENGTH = 7
NEGATIVE_LO = 1237
NEGATIVE_HI = 987654


@dataclass
class TransformStats:
    name: str
    attempted: int = 0
    skipped: int = 0
    top1_correct: int = 0
    in_top5: int = 0
    confidences: List[str] = field(default_factory=list)

    @property
    def recall_at_1(self) -> float:
        return self.top1_correct / self.attempted if self.attempted else 0.0

    @property
    def recall_at_5(self) -> float:
        return self.in_top5 / self.attempted if self.attempted else 0.0


@dataclass
class NegativeStats:
    attempted: int = 0
    false_positives: int = 0
    fp_transforms: List[str] = field(default_factory=list)
    fp_confidences: List[str] = field(default_factory=list)


def _fetch_row(conn, anum: str) -> Optional[Tuple[str, str]]:
    return conn.execute("SELECT name, terms FROM seq WHERE anum = ?", (anum,)).fetchone()


def _sample_pool(
    conn, rng: random.Random, all_anums: List[str], needed: int, exclude: Set[str]
) -> List[Tuple[str, str, List[int]]]:
    pool: List[Tuple[str, str, List[int]]] = []
    seen: Set[str] = set()
    max_attempts = needed * 50 + 2000
    attempts = 0
    while len(pool) < needed and attempts < max_attempts:
        attempts += 1
        anum = rng.choice(all_anums)
        if anum in seen or anum in exclude:
            continue
        seen.add(anum)
        row = _fetch_row(conn, anum)
        if row is None:
            continue
        name, terms_str = row
        terms = [int(x) for x in terms_str.split(",") if x != ""]
        if len(terms) < MIN_SAMPLE_TERMS:
            continue
        pool.append((anum, name, terms[:MAX_QUERY_TERMS]))
    return pool


def _run_positive_track(conn, rng: random.Random, k_positive: int, index_path) -> Dict[str, TransformStats]:
    all_anums = [r[0] for r in conn.execute("SELECT anum FROM seq ORDER BY anum").fetchall()]
    transform_names = list(TRANSFORMS.keys())
    per_transform = max(1, k_positive // len(transform_names))

    stats = {name: TransformStats(name) for name in transform_names}
    used: Set[str] = set()

    for name in transform_names:
        fn = TRANSFORMS[name]
        sample = _sample_pool(conn, rng, all_anums, per_transform, used)
        used.update(a for a, _, _ in sample)
        st = stats[name]
        for anum, _db_name, terms in sample:
            query = fn(terms)
            if not query or len(query) < keying.MIN_KEY_TERMS:
                st.skipped += 1
                continue
            st.attempted += 1
            results = run_match(query, top_k=5, index_path=index_path)
            anums_ranked = [r.anum for r in results]
            if anums_ranked and anums_ranked[0] == anum:
                st.top1_correct += 1
                st.confidences.append(results[0].confidence)
            if anum in anums_ranked:
                st.in_top5 += 1
    return stats


def _run_negative_track(rng: random.Random, k_negative: int, index_path) -> NegativeStats:
    st = NegativeStats()
    for _ in range(k_negative):
        seq = [rng.randint(NEGATIVE_LO, NEGATIVE_HI) for _ in range(NEGATIVE_LENGTH)]
        st.attempted += 1
        results = run_match(seq, top_k=1, index_path=index_path)
        if results:
            st.false_positives += 1
            st.fp_transforms.append(results[0].transform)
            st.fp_confidences.append(results[0].confidence)
    return st


def _render_report(
    *,
    seed: int,
    sequence_count: int,
    positive_stats: Dict[str, TransformStats],
    negative_stats: NegativeStats,
    elapsed_s: float,
) -> str:
    total_attempted = sum(s.attempted for s in positive_stats.values())
    total_top1 = sum(s.top1_correct for s in positive_stats.values())
    total_top5 = sum(s.in_top5 for s in positive_stats.values())

    tp = total_top1
    fn = total_attempted - total_top1
    tn = negative_stats.attempted - negative_stats.false_positives
    fp = negative_stats.false_positives

    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    specificity = tn / (tn + fp) if (tn + fp) else float("nan")

    lines: List[str] = []
    lines.append("# seqprior benchmark results")
    lines.append("")
    lines.append(f"- Seed: `{seed}`")
    lines.append(f"- Index size at run time: {sequence_count:,} sequences")
    lines.append(f"- Runtime: {elapsed_s:.1f}s")
    lines.append(
        "- Method: sample real OEIS sequences, apply one transform to produce a synthetic "
        "query, and check whether `match()` recovers the original A-number at rank 1 (recall@1) "
        "and within the top 5 (recall@5). A separate negative track feeds random noise sequences "
        "through the matcher and checks that it reports no match."
    )
    lines.append("")
    lines.append("## Recall per transform (ground-truth transform applied to a known sequence)")
    lines.append("")
    lines.append("| Transform | Attempted | Skipped (n/a) | Recall@1 | Recall@5 |")
    lines.append("|---|---:|---:|---:|---:|")
    for name in TRANSFORMS:
        s = positive_stats[name]
        lines.append(f"| {name} | {s.attempted} | {s.skipped} | {s.recall_at_1:.0%} | {s.recall_at_5:.0%} |")
    lines.append("")
    if total_attempted:
        lines.append(
            f"**Overall recall@1: {total_top1}/{total_attempted} = {total_top1 / total_attempted:.1%}** "
            f"&nbsp;&nbsp; **Overall recall@5: {total_top5}/{total_attempted} = {total_top5 / total_attempted:.1%}**"
        )
    lines.append("")
    lines.append(
        "Transforms that discard information to build the query (`bisect_even`, `bisect_odd`, "
        "`diff2`, `partial_products`) have no general inverse in the registry, so low recall for "
        "those rows is expected, not a bug — it's the benchmark doing its job of surfacing weak spots. "
        "`drop1`/`drop2`/`drop3` (offset shifts) only recover when the dropped terms happen to be the "
        "leading 0/1 run that the canonical key already strips; partial recall there reflects that "
        "real limitation, not a measurement error."
    )
    lines.append("")
    lines.append("## Negative track (random noise, no true match expected)")
    lines.append("")
    lines.append(f"- Attempted: {negative_stats.attempted}")
    lines.append(f"- False positives (any candidate surfaced): {negative_stats.false_positives}")
    if negative_stats.attempted:
        fpr = negative_stats.false_positives / negative_stats.attempted
        lines.append(f"- False positive rate: {fpr:.1%}")
    if negative_stats.fp_confidences:
        conf_counts = Counter(negative_stats.fp_confidences)
        transform_counts = Counter(negative_stats.fp_transforms)
        lines.append(f"- False-positive confidence breakdown: {dict(conf_counts)}")
        lines.append(f"- False-positive transform breakdown: {dict(transform_counts)}")
    lines.append("")
    lines.append("## Confusion matrix (top-1 prediction vs. ground truth)")
    lines.append("")
    lines.append("| | Predicted: match | Predicted: no match |")
    lines.append("|---|---:|---:|")
    lines.append(f"| **Actually known (positive track)** | TP = {tp} | FN = {fn} |")
    lines.append(f"| **Actually novel/noise (negative track)** | FP = {fp} | TN = {tn} |")
    lines.append("")
    lines.append(f"- Precision: {precision:.1%}")
    lines.append(f"- Recall: {recall:.1%}")
    lines.append(f"- Specificity (true negative rate): {specificity:.1%}")
    lines.append("")
    lines.append(
        "Recall is intentionally prioritized over precision in the tool's design: a missed known "
        "sequence (a false 'novel') is worse than a spurious low-confidence candidate, which is why "
        "every hit is shown with a confidence band instead of being filtered to a binary yes/no."
    )
    lines.append("")
    return "\n".join(lines)


def run_benchmark(
    *,
    seed: int = 42,
    k_positive: int = 400,
    k_negative: int = 100,
    out_path: Path = Path("benchmark/results.md"),
    index_path: Optional[str] = None,
) -> Path:
    start = time.time()
    rng = random.Random(seed)

    conn = _connect(Path(index_path) if index_path else None)
    try:
        sequence_count = conn.execute("SELECT COUNT(*) FROM seq").fetchone()[0]
        positive_stats = _run_positive_track(conn, rng, k_positive, index_path)
    finally:
        conn.close()

    negative_stats = _run_negative_track(rng, k_negative, index_path)

    elapsed = time.time() - start
    report = _render_report(
        seed=seed,
        sequence_count=sequence_count,
        positive_stats=positive_stats,
        negative_stats=negative_stats,
        elapsed_s=elapsed,
    )

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report)
    return out_path
