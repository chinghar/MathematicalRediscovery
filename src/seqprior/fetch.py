"""Downloads OEIS bulk data and builds the local index.

OEIS content is licensed CC BY-SA 4.0 (see https://oeis.org/wiki/The_OEIS_End-User_License_Agreement).
These files are cached locally for offline lookups only; seqprior never
redistributes them and never commits them to the repo.
"""

import json
import time
from pathlib import Path
from typing import Dict

import requests

from . import cache, indexer

STRIPPED_URL = "https://oeis.org/stripped.gz"
NAMES_URL = "https://oeis.org/names.gz"
USER_AGENT = "seqprior/0.1 (offline OEIS prior-art matcher; https://github.com/)"


def _download(url: str, dest: Path, chunk_size: int = 1 << 20) -> None:
    tmp = dest.with_suffix(dest.suffix + ".part")
    with requests.get(url, stream=True, timeout=60, headers={"User-Agent": USER_AGENT}) as resp:
        resp.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in resp.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
    tmp.replace(dest)


def fetch(force: bool = False) -> Dict:
    stripped = cache.stripped_path()
    names = cache.names_path()
    idx = cache.index_path()

    if force or not stripped.exists():
        _download(STRIPPED_URL, stripped)
    if force or not names.exists():
        _download(NAMES_URL, names)

    stats = indexer.build_index(stripped, names, idx)

    meta = {
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sequence_count": stats["count"],
        "index_bytes": idx.stat().st_size,
        "source": {"stripped": STRIPPED_URL, "names": NAMES_URL},
        "license": "OEIS content is CC BY-SA 4.0; see https://oeis.org/wiki/The_OEIS_End-User_License_Agreement",
    }
    cache.meta_path().write_text(json.dumps(meta, indent=2))
    return meta
