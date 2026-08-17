# API

Top-level imports (`import varvaluation as v`):

| Name | Role |
|---|---|
| `StateSpec` | Named state layout |
| `ExpectedReturnSpec` | $\xi$, $\Lambda$ from $b_0, b_r, b_z$ |
| `estimate_var` / `estimate_var_panel` | Newey–West VAR(1) |
| `VARFit` | Companion, intercept, $\Sigma$, residuals |
| `AngLiuModel` | Price / cash-flow recursions, spot curve |
| `isolate_channels` | Named counterfactual PV |
| `ValuationResult` | `pv`, `n_used`, `tail_rate` |
| `news_decomposition` | Chen-aware CF / DR news |
| `treasury_test` | Known-cash-flow diagnostic |
| `NewsResult` / `NewsShares` | Series and variance shares |
| `state_schema` / `returns_schema` | Pandera inbound contracts |

Exceptions: `StateSpecError`, `SchemaError`, `NonStationaryVARError`, `RecursionDivergedError`, `PerpetuityDivergesError`, `EstimationError`, `ExtraNotInstalled`.

Subpackages (not re-exported at top level):

- `varvaluation.data` — public loaders and `prepare_portfolio_state`
- `varvaluation.climate` — `build_climate_state`, `scenario_dynamics`, `override_var`
- `varvaluation.wrds` — `load_firm_panel`, `prepare_firm_state`

Docstrings on the objects are the contract. The design note in the repo (`docs/superpowers/specs/`) is the longer specification.
