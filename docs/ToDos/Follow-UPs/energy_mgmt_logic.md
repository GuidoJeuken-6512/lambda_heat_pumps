# Energy Management Logic (Deye Battery + PV + Dynamic Tariffs)

**Goal:** Maximize self-consumption and savings by coordinating battery charge/discharge with PV production, tariff windows, and forecasts.

## Inputs (entities)
- Battery SOC: `sensor.deye8k_battery`
- PV power now: `sensor.pv_power_sum_calc`
- Home load now: `sensor.deye8k_load_power`
- Max charge current: `number.deye8k_battery_max_charging_current`
- Max discharge current: `number.deye8k_battery_max_discharging_current`
- Grid charge toggle: `switch.deye8k_battery_grid_charging`
- Grid charge current limit: `number.deye8k_battery_grid_charging_current`
- Tariff windows (local time):
  - 02–06: medium
  - 06–12: low
  - 12–16: low
  - 18–21: high
  - 21–02: medium
- Forecasts:
  - Tomorrow PV: `sensor.solcast_pv_forecast_prognose_morgen`
  - Remaining today PV: `sensor.solcast_pv_forecast_prognose_verbleibende_leistung_heute`

## Control objectives
- Use cheap windows to pre-charge when needed; avoid grid charge in high windows.
- Prefer PV for charging; avoid simultaneous grid + PV charging.
- Respect SOC min/max and current limits.

## Control strategy (logic sketch)
- Time-based targets:
  - Low tariff: allow grid charging; higher target SOC; raise charge current cap.
  - Medium tariff: moderate grid charging only if forecast + SOC are insufficient for upcoming demand.
  - High tariff: disable grid charging; allow discharge (within SOC min).
- PV surplus: if PV > load, prioritize PV charging; set grid charging current to 0 and keep toggle off to avoid grid use.
- Forecast-driven pre-charge: if tomorrow PV is low and SOC below tomorrow’s target, schedule grid charge in the next low/medium window.
- Protections: enforce SOC min/max, cap currents, and avoid simultaneous grid + PV charging.

## Flow (Mermaid)

```mermaid
flowchart TD
  start[Start Tick (e.g. every 5-10 min)]
  getState[Read states:\nSOC, PV, Load,\nTariff window,\nForecast today/tomorrow]
  defineTargets[Compute targets:\n- Tariff → target SOC\n- Forecast → grid need?\n- PV surplus?]
  pvSurplus{PV > Load + reserve?}
  setGridLimit0[Set grid_charging_current=0\nand switch grid_charging off\n(PV-only charging)]
  allowGridCharge{Tariff = low/medium\nAND forecast needs grid?}
  setGridOn[Grid charging on\nset grid_charging_current = limit\nset max_charge_current = limit]
  blockGrid[Grid charging off\nset grid_charging_current=0]
  socBelowTarget{SOC < target?}
  setCharge[Increase max_charge_current\n(within caps)\nreduce discharge]
  socAboveHigh{SOC > upper guard?}
  setDischarge[Increase max_discharging_current\n(for load support)\nreduce charge cap]
  protect[Guards:\nSOC min/max,\ncurrent caps,\nno simultaneous grid+PV charge]
  end[End Tick]

  start --> getState --> defineTargets --> pvSurplus
  pvSurplus -->|Yes| setGridLimit0 --> socBelowTarget
  pvSurplus -->|No| allowGridCharge
  allowGridCharge -->|Yes| setGridOn --> socBelowTarget
  allowGridCharge -->|No| blockGrid --> socBelowTarget
  socBelowTarget -->|Yes| setCharge --> protect --> end
  socBelowTarget -->|No| socAboveHigh
  socAboveHigh -->|Yes| setDischarge --> protect --> end
  socAboveHigh -->|No| protect --> end
```

## Next
- Translate this logic into Home Assistant automations/blueprints: conditions on time windows, SOC thresholds, forecasts; actions setting number.* and switch.* entities.
- Dry-run per window (low/medium/high) and verify current caps are enforced.

