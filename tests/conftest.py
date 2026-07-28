import sqlite3

import pytest

from seqprior import keying

FIXTURE_SEQUENCES = {
    "A000108": (
        "Catalan numbers",
        [1, 1, 2, 5, 14, 42, 132, 429, 1430, 4862, 16796, 58786, 208012,
         742900, 2674440, 9694845, 35357670, 129644790, 477638700, 1767263190],
    ),
    "A000045": (
        "Fibonacci numbers",
        [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181],
    ),
    "A000027": (
        "The positive integers",
        list(range(1, 21)),
    ),
    "A000079": (
        "Powers of 2",
        [2 ** n for n in range(20)],
    ),
    "A000217": (
        "Triangular numbers",
        [n * (n + 1) // 2 for n in range(20)],
    ),
}


@pytest.fixture()
def tiny_index(tmp_path):
    """A small sqlite index (schema matching the real one) for offline tests."""
    path = tmp_path / "tiny_index.sqlite3"
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE seq (anum TEXT PRIMARY KEY, name TEXT NOT NULL, terms TEXT NOT NULL, key TEXT NOT NULL)"
    )
    for anum, (name, terms) in FIXTURE_SEQUENCES.items():
        terms_str = ",".join(str(t) for t in terms)
        key, _ = keying.canonical_key(terms)
        conn.execute("INSERT INTO seq VALUES (?, ?, ?, ?)", (anum, name, terms_str, key))
    conn.execute("CREATE INDEX idx_seq_key ON seq(key)")
    conn.commit()
    conn.close()
    return str(path)
