"""On-disk cache for public downloads."""

from __future__ import annotations

import os
import urllib.request
from pathlib import Path

USER_AGENT = "varvaluation/0.1 (+https://github.com/tlorans/varvaluation)"


def cache_dir() -> Path:
    env = os.environ.get("VARVALUATION_CACHE")
    if env:
        path = Path(env)
    else:
        path = Path.home() / ".cache" / "varvaluation"
    path.mkdir(parents=True, exist_ok=True)
    return path


def cached_download(url: str, name: str, *, refresh: bool = False) -> Path:
    """Download ``url`` to the cache as ``name`` unless it already exists."""
    dest = cache_dir() / name
    if dest.exists() and not refresh:
        return dest
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        dest.write_bytes(resp.read())
    return dest
