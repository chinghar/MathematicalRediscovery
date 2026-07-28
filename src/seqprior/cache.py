"""Local cache directory layout. Never used to store files inside the repo."""

import os
from pathlib import Path


def get_cache_dir() -> Path:
    override = os.environ.get("SEQPRIOR_CACHE")
    base = Path(override) if override else Path.home() / ".cache" / "seqprior"
    base.mkdir(parents=True, exist_ok=True)
    return base


def stripped_path() -> Path:
    return get_cache_dir() / "stripped.gz"


def names_path() -> Path:
    return get_cache_dir() / "names.gz"


def index_path() -> Path:
    return get_cache_dir() / "index.sqlite3"


def meta_path() -> Path:
    return get_cache_dir() / "meta.json"
