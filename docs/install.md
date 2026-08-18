# Install

Python 3.11 or 3.12. Managed with [uv](https://docs.astral.sh/uv/).

Once a release is on PyPI:

```text
uv add varvaluation
```

Until then, install from GitHub:

```text
uv add git+https://github.com/tlorans/varvaluation
```

From a clone:

```text
git clone https://github.com/tlorans/varvaluation
cd varvaluation
uv sync --extra dev
uv run pytest -q
```

Core dependencies: numpy, scipy, polars, pandera, statsmodels.

## Publishing a release

The workflow `.github/workflows/publish.yml` uploads to PyPI when you publish a GitHub release (or run it by hand). First-time setup:

1. Create a PyPI account and a project named `varvaluation` (or let the first trusted upload create it).
2. On PyPI: **Publishing** → **Add a new pending publisher**:
   - Owner: `tlorans`
   - Repository: `varvaluation`
   - Workflow: `publish.yml`
   - Environment: `pypi`
3. On GitHub: **Settings → Environments** → create `pypi` (optional protection rules).
4. Tag and publish a release matching `pyproject.toml`, e.g. `v0.2.0`.

## Documentation site

```text
uv sync --extra docs
uv run mkdocs serve
```

Start at [The problem](guide/problem.md).
