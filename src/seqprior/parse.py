"""Parsers for the OEIS bulk files (stripped.gz, names.gz)."""

import gzip
from pathlib import Path
from typing import Iterator, List, Tuple


def parse_stripped(path: Path) -> Iterator[Tuple[str, List[int]]]:
    """Yield (A-number, terms) from a stripped.gz file.

    Lines look like: ``A000108 ,1,1,2,5,14,42,132,429,...,``
    """
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            anum, _, rest = line.partition(" ")
            rest = rest.strip().strip(",")
            if not rest:
                continue
            terms = [int(x) for x in rest.split(",") if x != ""]
            if terms:
                yield anum, terms


def parse_names(path: Path) -> Iterator[Tuple[str, str]]:
    """Yield (A-number, name) from a names.gz file."""
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            anum, _, name = line.partition(" ")
            yield anum, name
