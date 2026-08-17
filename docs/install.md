# Install

Python 3.11 or 3.12. The project is managed with [uv](https://docs.astral.sh/uv/).

```text
uv add varvaluation
uv add "varvaluation[data]"    # Ken French, FRED Treasuries, DEF, TERM
uv add "varvaluation[wrds]"    # Compustat quarterly + CRSP daily
```

From a clone:

```text
git clone https://github.com/tlorans/varvaluation
cd varvaluation
uv sync --extra dev --extra data
uv run pytest -q --ignore=tests/wrds
```

## What each extra pulls in

| Extra | Extra dependencies |
|---|---|
| core | numpy, scipy, polars, pandera, statsmodels |
| `[data]` | pandas-datareader, pyarrow, openpyxl |
| `[wrds]` | wrds, python-dotenv, pyarrow |

Importing `varvaluation.data` or `varvaluation.wrds` without the extra raises `ExtraNotInstalled` and names the extra to add.

## Caches and secrets

Public downloads go to `~/.cache/varvaluation` (override with `VARVALUATION_CACHE`). Pass `path=` to any loader to skip the network.

WRDS credentials: `WRDS_USERNAME` or `WRDS_USER`, and `WRDS_PASSWORD`, in the environment or a `.env` file at the repo root. Do not commit `.env`. The first CRSP daily pull is large; later runs read parquet.

## Documentation site

```text
uv sync --extra docs --extra data
uv run mkdocs serve
```

The insurance illustration is
[`examples/reproduce_glz2020.py`](https://github.com/tlorans/varvaluation/blob/main/examples/reproduce_glz2020.py).
Start at [The problem](guide/problem.md).
