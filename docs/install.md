# Install

Python 3.11 or 3.12. Managed with [uv](https://docs.astral.sh/uv/).

```text
uv add varvaluation
```

From a clone:

```text
git clone https://github.com/tlorans/varvaluation
cd varvaluation
uv sync --extra dev
uv run pytest -q
```

Core dependencies: numpy, scipy, polars, pandera, statsmodels.

## Documentation site

```text
uv sync --extra docs
uv run mkdocs serve
```

Start at [The problem](guide/problem.md).
