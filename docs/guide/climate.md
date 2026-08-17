# Climate

Extra: `uv add "varvaluation[climate]"` (no extra dependencies). The package is always importable.

## Persistent temperature state

$$
Y_{t+1} = \phi Y_t + (T_{t+1}-T_t)
$$

```python
from varvaluation.climate import build_climate_state

Y = build_climate_state(temp, persistence=0.962, burn_in=240)
# columns: date, Y
```

`temp` is any monthly frame with `date` and `temp` (GISTEMP via `load_temperature()`, or your own series).

## Scenario override

The historical VAR cannot speak to a pathway that has not occurred. Replace the named state's *own* AR(1) with moments from a scenario, and leave every other equation alone.

```python
from varvaluation.climate import scenario_dynamics, override_var
from varvaluation import AngLiuModel

dyn = scenario_dynamics("Net Zero 2050")
Phi_s, c_s, Sigma_s = override_var(fit, dyn, state="Y")
model_s = AngLiuModel(fit.spec, Phi_s, c_s, Sigma_s, xi, Lambda, alpha)
```

Shipped scenarios (NGFS / Melin–Zhang parameterisation): `Net Zero 2050`, `Below 2C`, `Current Policies`, `Climate Destabilization`, `Climate Breakdown`, and the others in `load_scenario_parameters()`.

`override_var` is generic. The state name does not have to be `"Y"`.
