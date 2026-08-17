# Reproduce the paper

[Giacotto, Lin, and Zhao (2020)](../references.md#glz-2020), *Insurance: Mathematics and Economics* 95, 147–158. Sample: 1972 Q4 – 2018 Q4. Five portfolios.

| Portfolio | SIC | What to check |
|---|---|---|
| All insurers | 6300–6399 | Hump. $\rho(1)\approx 9.6$, $\rho(10)\approx 10.5$, $\rho(30)\approx 9.0$. CAPM $\approx 11.7$. |
| P/C | 6330–6331 | Same shape, a little lower. |
| Life | 6310–6319 | Higher level than P/C and health. |
| Health | 6320–6329 | Close to P/C. |
| All stocks excl. insurers | not 6300–6399 | Higher still. Average $\beta\approx 0.97$ vs $0.65$. |

Those cells are Table 2. We will not hit them to the basis point (link-table vintage, Cosemans priors, the log-versus-simple ROE choice). The check is the same industries, the same objects, the same ranking, and a hump on the insurance curve.

## Offline (no downloads)

```text
uv run python examples/reproduce_glz2020.py
```

This draws a synthetic four-state VAR, one per paper portfolio, and prints Fig. 1 points, Tables 2–3, and a Table 4 annuity. It is the API, not the sample. $\tau=1$ equals the CCAPM. Life sits above P/C because its $\beta$ is higher. That is all the simulator is for.

## Live (WRDS)

```text
uv add "varvaluation[data,wrds]"
# WRDS_USERNAME / WRDS_PASSWORD in the environment or a .env file
uv run python examples/reproduce_glz2020.py --wrds
```

The script loads Compustat quarterly (`ibq`, `ceqq`), CRSP monthly for the CCM link, CRSP daily for the 125-day beta, FRED Treasuries and corporate yields, and Ken French T-bills. Queries cache under `~/.cache/varvaluation`. The first daily pull is large; later runs read parquet.

The body of the live path is the same four calls as the offline path:

```python
from varvaluation import (
    CCAPMSpec, INSURANCE, ResidualIncome, TermStructureModel,
    capm_tests, estimate_var, paper_state_spec, prepare_industry_state,
    slope_tests,
)
from varvaluation.industry import curve_panel

spec = paper_state_spec()                    # horizon=4
state = prepare_industry_state(panel, macro, spec, sic=INSURANCE["all"])
fit = estimate_var(state, spec)
model = TermStructureModel.from_var(fit, ResidualIncome(), CCAPMSpec())
rho_bar = model.unconditional_curve(y_bar, n=30)
rho_ts = curve_panel(model, state, y_bar, n=30)
capm_ts = y_bar + state["beta"] * state["mrp"]
capm_tests(rho_ts, capm_ts)
slope_tests(rho_ts)
```

## What “close” means

| Check | Paper | Pass |
|---|---|---|
| $\rho(1)$ equals the CCAPM at every date | identity | exact, offline |
| Insurance curve hump-shaped at $\bar x$ | Fig. 1A | qualitative, live |
| Life above P/C and health | Fig. 1C vs 1B, 1D | ranking, live |
| All-ex-insurers above insurance | Fig. 1E; $\beta$ 0.97 vs 0.65 | ranking, live |
| Mean $\rho(\tau)$ below CAPM for insurers | Table 2, all $t<0$ | sign, live |
| Slope $\rho(5)-\rho(1)>0$ for insurers | Table 3 | sign, live |
| 30-year annuity discrepancy | Table 4 | same formula |

Figs. 2–5 overlay BXP (2018) and Berry-Stölzle–Xu (2018). Those series are not public here. Pass a flat rate of your own into `flat_annuity_value` if you want the same picture.

The next page changes one argument — `sic=` — and keeps everything else.
