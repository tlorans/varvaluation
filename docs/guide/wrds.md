<p class="part-kicker">Part 06 · Firms</p>

# WRDS / firm panel

<p class="you-will"><strong>You will.</strong> Build a firm-level state from the academic US equity files, without using one firm to forecast another.</p>

Public files gave you a curve. A firm panel is the next state.
**WRDS** is the academic vendor. **CRSP** is the monthly stock-return
file; **Compustat** is the annual fundamentals file; a **permno** is
CRSP’s permanent firm identifier. Yesterday-and-today pairs are
formed only inside one permno, so one name is never used to forecast
another. Extra: `uv add "varvaluation[wrds]"`.

Credentials: `WRDS_USERNAME` or `WRDS_USER`, and `WRDS_PASSWORD`, in the environment or a `.env` file. Queries cache as parquet under `~/.cache/varvaluation/wrds`.

```python
from varvaluation import StateSpec, estimate_var_panel
from varvaluation.wrds import load_firm_panel, prepare_firm_state

panel = load_firm_panel(start="1965-07")
spec = StateSpec(
    names=("g", "beta", "bm", "r", "cay", "pi"),
    cashflow="g",
    group="permno",
)
state = prepare_firm_state(panel, macro, spec, start="1965-07")
fit = estimate_var_panel(state, spec)
```

`prepare_firm_state` also accepts a local panel — no live WRDS required.
It builds `g`, `roe`, `bm`, and `beta` when those names are in the
spec. Financials and utilities are dropped.

`g` is log growth of trailing twelve-month dividends implied by CRSP
returns with and without dividends (`ret` and `retx`). The trailing
level stays on the frame as `div` (CRSP thousands of dollars). Firms
that do not pay stay out of the state: there is no growth of zero.
That `g` is the cash-flow path. `value(X, C=div)` is a present value
of the equity.

`roe` is still available as a *level* — log NI over lagged book —
if you put it in `spec.names`. It is not growth of cash. Do not set
`cashflow="roe"` and call `value`.

## Sample overlap

Cay (published or reconstructed) must overlap the CRSP window *after* the beta burn-in. A 2019–2021 CRSP pull with a 12-month beta window and cay ending 2019-09 produces an empty state. Use a window such as CRSP 2014–2019 if you need cay in the firm VAR.

`estimate_var_panel` forms lag pairs only within `permno`. You need more months per firm than `spec.horizon`.

The illustration in [Three curves](walkthrough.md) uses `cashflow="g"`
on a short window of dividend payers and reports `value`. The sample
is still short; the object is now a present value, not a
profitability path.

Live queries are not run in CI. With credentials:

```text
uv run pytest tests/wrds/test_live.py -v
```
