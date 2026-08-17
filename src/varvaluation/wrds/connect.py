"""WRDS connection and parquet cache."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from varvaluation.exceptions import ExtraNotInstalled


def cache_dir() -> Path:
    env = os.environ.get("VARVALUATION_CACHE")
    root = Path(env) if env else Path.home() / ".cache" / "varvaluation"
    path = root / "wrds"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _load_env() -> None:
    """Load .env from cwd, then the package repo root if present."""
    load_dotenv()
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / ".env"
        if candidate.is_file():
            load_dotenv(candidate, override=False)
            break


def get_wrds_connection():
    """Open a wrds.Connection using WRDS_USERNAME / WRDS_USER and WRDS_PASSWORD."""
    _load_env()
    user = os.environ.get("WRDS_USERNAME") or os.environ.get("WRDS_USER")
    password = os.environ.get("WRDS_PASSWORD")
    try:
        import wrds
    except ImportError as exc:
        raise ExtraNotInstalled(
            "varvaluation.wrds requires the [wrds] extra. "
            "Install with: uv add 'varvaluation[wrds]'"
        ) from exc
    if user:
        return wrds.Connection(wrds_username=user, wrds_password=password)
    return wrds.Connection()


def load_or_cache(name: str, builder, *, use_cache: bool = True):
    path = cache_dir() / f"{name}.parquet"
    if use_cache and path.exists():
        import polars as pl

        return pl.read_parquet(path)
    df = builder()
    if use_cache:
        df.write_parquet(path)
    return df
