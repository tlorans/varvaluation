# Software

The library `varvaluation` is the computational form of Sections 2–4.
Python 3.11 or 3.12. The project is managed with
[uv](https://docs.astral.sh/uv/).

```text
uv add varvaluation
uv add "varvaluation[data]"
uv add "varvaluation[wrds]"
```

Or, from a clone:

```text
git clone https://github.com/tlorans/varvaluation
cd varvaluation
uv sync --extra dev --extra data
uv run pytest -q
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

WRDS credentials: `WRDS_USERNAME` or `WRDS_USER`, and `WRDS_PASSWORD`, in the environment or a `.env` file at the repo root. Do not commit `.env`.

## Documentation site

```text
uv sync --extra docs --extra data
uv run mkdocs serve
```

Figures in the guide are produced by `uv run python examples/build_docs_figures.py` and committed under `docs/assets/figures/`.

Section 5 is the software demonstration:
[`examples/walkthrough.py`](https://github.com/tlorans/varvaluation/blob/main/examples/walkthrough.py).
The argument begins at the [Introduction](guide/introduction.md).
