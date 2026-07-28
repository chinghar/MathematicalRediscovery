import argparse
from pathlib import Path
from typing import List, Optional, Sequence

from . import benchmark as benchmark_mod
from . import cache
from . import fetch as fetch_mod
from .match import match


def _parse_sequence(raw: str) -> List[int]:
    parts = [p for p in raw.replace(" ", ",").split(",") if p.strip() != ""]
    try:
        return [int(p) for p in parts]
    except ValueError as exc:
        raise SystemExit(f"error: could not parse sequence '{raw}': {exc}")


def cmd_fetch(args: argparse.Namespace) -> None:
    meta = fetch_mod.fetch(force=args.force)
    size_mb = meta["index_bytes"] / 1e6
    print(f"Indexed {meta['sequence_count']:,} OEIS sequences.")
    print(f"Index size: {size_mb:.1f} MB at {cache.index_path()}")


def cmd_match(args: argparse.Namespace) -> None:
    seq = _parse_sequence(args.sequence)
    results = match(seq, top_k=args.top)
    if not results:
        print("No match found. This is weak evidence, not proof of novelty.")
        return
    header = f"{'A-number':<12}{'Confidence':<12}{'Transform':<14}{'Overlap':<9}Name"
    print(header)
    for r in results:
        name = r.name if len(r.name) <= 70 else r.name[:67] + "..."
        print(f"{r.anum:<12}{r.confidence:<12}{r.transform:<14}{r.overlap:<9}{name}")


def cmd_benchmark(args: argparse.Namespace) -> None:
    benchmark_mod.run_benchmark(
        seed=args.seed,
        k_positive=args.k,
        k_negative=args.neg_k,
        out_path=Path(args.out),
    )
    print(f"Benchmark results written to {args.out}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="seqprior",
        description=(
            "Offline prior-art search for integer sequences against the OEIS bulk data. "
            "Reimplements the transform-battery matching idea behind OEIS Superseeker "
            "(see https://oeis.org/superhelp.txt) for local, offline use."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_fetch = sub.add_parser("fetch", help="Download OEIS bulk data and build the local index")
    p_fetch.add_argument("--force", action="store_true", help="Re-download even if cached files exist")
    p_fetch.set_defaults(func=cmd_fetch)

    p_match = sub.add_parser("match", help="Find candidate OEIS matches for a sequence")
    p_match.add_argument("sequence", help="Comma or space separated integers, e.g. '1,2,5,14,42'")
    p_match.add_argument("--top", type=int, default=10, help="Max results to show (default 10)")
    p_match.set_defaults(func=cmd_match)

    p_bench = sub.add_parser("benchmark", help="Run the recall/precision evaluation harness")
    p_bench.add_argument("--seed", type=int, default=42, help="Random seed (default 42)")
    p_bench.add_argument("--k", type=int, default=400, help="Positive (recall) samples, split across transforms")
    p_bench.add_argument("--neg-k", type=int, default=100, help="Negative (specificity) samples")
    p_bench.add_argument("--out", default="benchmark/results.md", help="Output path for the report")
    p_bench.set_defaults(func=cmd_benchmark)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
