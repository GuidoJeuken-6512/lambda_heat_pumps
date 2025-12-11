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
- **PV surplus priority (highest):** If PV > load, prioritize PV charging; set grid charging current to 0 and keep toggle off to avoid grid use. **Grid charging is blocked regardless of forecast when PV surplus exists.**
- Time-based targets (only when NO PV surplus):
  - Low tariff: allow grid charging; higher target SOC; raise charge current cap.
  - Medium tariff: moderate grid charging only if forecast + SOC are insufficient for upcoming demand.
  - High tariff: disable grid charging; allow discharge (within SOC min).
- Forecast-driven pre-charge (only when NO PV surplus):
  - 00–06: Grid charge only if "Forecast tomorrow" indicates the battery won't be full otherwise.
  - 12–16: Grid charge only if the battery won't be full from today's remaining PV forecast.
- Protections: enforce SOC min/max, cap currents, and avoid simultaneous grid + PV charging.

## Flow (Text-Bullets)
1) Start tick (every 5–10 min).  
2) Read states: SOC, PV power, home load, tariff window, forecast today (remaining), forecast tomorrow.  
3) Set target SOC per tariff (low/medium/high) and derive grid charging need.  
4) **PV surplus check (PV > Load + Reserve) – highest priority, but goal: battery full before 18:00:**  
   - **Yes: PV uses full PV power; if SOC target before 18:00 won't be reached otherwise, allow additional grid charging as supplement, together maximum up to configured max Charge-Current (parallel PV + Grid).**  
   - No: continue with grid check.  
5) Grid check (only when NO PV surplus + low/medium + need):  
   - No: Grid off, Grid-Current = 0.  
   - Yes: Grid on, Grid-Current = Limit, Charge-Current = Limit.  
6) Forecast guards (only when NO PV surplus):  
   - 00–06: Grid only if forecast tomorrow won't fill battery otherwise; else grid off.  
   - 12–16: Grid only if remaining forecast today won't fill battery; else grid off.  
7) SOC rules:  
   - If SOC < target: Increase Charge-Current (within limits), reduce discharge.  
   - If SOC > upper guard: Increase discharge for load coverage, reduce charge.  
8) Protection: Enforce SOC min/max, cap current limits, avoid simultaneous grid + PV charging.  
9) End of tick.  

## Next
- Translate this logic into Home Assistant automations/blueprints: conditions on time windows, SOC thresholds, forecasts; actions setting number.* and switch.* entities.
- Dry-run per window (low/medium/high) and verify current caps are enforced.




flowchart TD
    start[Tick] --> pv{PV > Load + Reserve?}
    pv -- Yes --> pvCharge[PV charges battery up to max Charge-Current]
    pv -- No --> socMin{SOC > Minimum?}

    pvCharge --> pvGoal{SOC target before 18:00 reached?}
    pvGoal -- No --> pvGridHelp[Supplement grid charging parallel to PV up to max Charge-Current]
    pvGoal -- Yes --> toTariff1[Go to tariff logic]
    pvGridHelp --> toTariff1

    socMin -- Yes --> discharge[Discharge for load]
    socMin -- No --> hold[No discharge]

    discharge --> toTariff1
    hold --> toTariff1

    toTariff1 --> tariff{Tariff window?}

    tariff --> low12{Low 00-06}
    tariff --> low34{Low 06-12}
    tariff --> low56{Low 12-16}
    tariff --> normal1{Medium 21-02}
    tariff --> normal2{Medium 16-18}
    tariff --> high{High 18-21}

    low12 --> fTomorrow{Forecast tomorrow fills full?}
    fTomorrow -- Yes --> blockGrid12[No grid charging]
    fTomorrow -- No --> grid12[Allow grid charging up to target SOC]

    low56 --> fToday{Forecast today remaining fills full?}
    fToday -- Yes --> blockGrid56[No grid charging]
    fToday -- No --> grid56[Allow grid charging up to target SOC]

    low34 --> grid34[Allow grid charging as needed]
    normal1 --> gridN1[Optional charging moderate target SOC]
    normal2 --> gridN2[Optional charging up to target before 18:00]
    high --> dischargeHigh[Discharge for load; no grid charging]

    blockGrid12 --> guard[Protection caps: SOC min/max, current limits, no Grid+PV > Limit]
    grid12 --> guard
    blockGrid56 --> guard
    grid56 --> guard
    grid34 --> guard
    gridN1 --> guard
    gridN2 --> guard
    dischargeHigh --> guard
    guard --> endNode[End Tick]

