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
    names=("roe", "beta", "bm", "r", "cay", "pi"),
    cashflow="roe",
    group="permno",
)
state = prepare_firm_state(panel, macro, spec, start="1965-07")
fit = estimate_var_panel(state, spec)
```

`prepare_firm_state` also accepts a local panel — no live WRDS required. It builds `roe` (log NI over lagged book equity), `bm`, and `beta` when those names are in the spec. Financials and utilities are dropped. `roe` is built only when $\mathrm{NI}>0$. It is a profitability *level*, not log dividend growth and not Vuolteenaho’s $e_t=\log(1+X_t/B_{t-1})$.

Firm-level `roe` mean-reverts ($\Phi_{\mathit{roe},\mathit{roe}}=0.46$
on the 80-firm companion in Section 5). Inspect
`fit.Phi[spec.cashflow_index(), spec.cashflow_index()]` before calling
`value`. Do not feed `roe` into `value` as if it were log
dividend growth. Discount a cash-flow path you already have at
`spot_rates`, or report `perpetuity`.

## Sample overlap

Cay (published or reconstructed) must overlap the CRSP window *after* the beta burn-in. A 2019–2021 CRSP pull with a 12-month beta window and cay ending 2019-09 produces an empty state. Use a window such as CRSP 2014–2019 if you need cay in the firm VAR.

`estimate_var_panel` forms lag pairs only within `permno`. You need more months per firm than `spec.horizon`.

On a cached 2014–2019 CRSP / Compustat pull the state after the beta
burn-in is 2,673 firms and 67,884 firm-months (2015-03 → 2019-09). A
pooled VAR on the 80 longest firms gives
$\Phi_{\mathit{roe},\mathit{roe}}=0.46$ and a spectral radius of 0.995.
`roe` is $\log(\mathrm{NI}/\mathrm{BE}_{\mathrm{lag}})$: a reading of
$-2.08$ is an ROE of about 12.5%, not a −208% growth rate. The full
terminal is in [Section 5](walkthrough.md).

Live queries are not run in CI. With credentials:

```text
uv run pytest tests/wrds/test_live.py -v
```
