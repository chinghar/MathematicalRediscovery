"""Builds the local sqlite index from the downloaded OEIS bulk files."""

import sqlite3
from pathlib import Path
from typing import Dict

from . import keying, parse

MAX_STORE_TERMS = 40
BATCH_SIZE = 5000


def build_index(stripped_gz: Path, names_gz: Path, out_path: Path) -> Dict[str, int]:
    names = dict(parse.parse_names(names_gz))

    if out_path.exists():
        out_path.unlink()

    conn = sqlite3.connect(out_path)
    try:
        conn.execute("PRAGMA journal_mode=OFF")
        conn.execute("PRAGMA synchronous=OFF")
        conn.execute(
            """
            CREATE TABLE seq (
                anum TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                terms TEXT NOT NULL,
                key TEXT NOT NULL
            )
            """
        )

        count = 0
        batch = []
        for anum, terms in parse.parse_stripped(stripped_gz):
            key, _ = keying.canonical_key(terms)
            terms_str = ",".join(str(t) for t in terms[:MAX_STORE_TERMS])
            batch.append((anum, names.get(anum, ""), terms_str, key))
            count += 1
            if len(batch) >= BATCH_SIZE:
                conn.executemany("INSERT INTO seq VALUES (?,?,?,?)", batch)
                batch.clear()
        if batch:
            conn.executemany("INSERT INTO seq VALUES (?,?,?,?)", batch)

        conn.execute("CREATE INDEX idx_seq_key ON seq(key)")
        conn.commit()
    finally:
        conn.close()

    return {"count": count}
