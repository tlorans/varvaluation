<p class="part-kicker">Part 04 · Measurement</p>

# Public data

<p class="you-will"><strong>You will.</strong> Load Ken French / FRED and print a real $\mu(n)$ with no WRDS.</p>

This is the first *real* discount curve. Ken French portfolios and
FRED macros are enough to estimate $\Phi$ and print $\mu_t(n)$.
Firm-level CRSP–Compustat work is [Part 06](wrds.md).

Extra: `uv add "varvaluation[data]"`.

| Function | Source | Columns |
|---|---|---|
| `load_ff3()` | Ken French | `date, mkt_rf, smb, hml, rf, mkt` |
| `load_bm_deciles()` | Ken French, with and without dividends | `date`, `D1`…`D10` |
| `load_industry49()` | Ken French industries | `date` + names |
| `load_gs1()` | FRED GS1 | `date, r` (continuously compounded) |
| `load_cpi()` | FRED CPIAUCSL | `date, pi` (12-month log) |
| `load_cay()` | Lettau–Ludvigson, or FRED reconstruction | `date, cay` |
| `load_macro()` | join of FF3 + GS1 + CPI + cay | one monthly frame |

Downloads cache under `~/.cache/varvaluation`. Pass `path=` (or `path_total` / `path_exdiv`) to read a local file.

`load_macro()` **requires** FF3, GS1, and CPI. Cay is optional. If the published CSV 404s, `load_cay()` estimates the cointegrating residual from FRED (PCEC, household net worth `TNWBSHNO`, wages) on 1952–2019Q3 and applies it through the latest quarter.

## Portfolio state

```python
from varvaluation.data import prepare_portfolio_state

state = prepare_portfolio_state(
    total, capgains, macro, spec, portfolio="D10", start="1965-07"
)
```

`g`, `beta`, and `dpo` are built only when those names appear in
`spec.names`. Every other name is joined from `macro` by column.

- **`g`** — monthly dividends are backed out of the gap between returns
  with and without dividends, then summed over twelve months to remove
  seasonality
  ([Hodrick, 1992](../references.md#hodrick-1992)).
  $g_t=\log(D_t/D_{t-1})$.
- **`beta`** — 60-month rolling CAPM slope of log excess returns on the
  market. Section 5 uses 12 months because that extract is short.
- **`dpo`** — log payout when both dividends and a positive earnings
  proxy exist.

The five-stage pipeline is [Estimation](estimate.md). Section 5
illustrates it on firms (`load_macro` plus WRDS), not on these
portfolio loaders. Why the names in $X_t$ are these, rather than
dividend yield, is [Section 2.3](spec.md#where-the-names-come-from).
