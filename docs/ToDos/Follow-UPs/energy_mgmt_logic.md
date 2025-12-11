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
  - 00–06: Grid laden nur, wenn laut „Forecast morgen" der Speicher sonst nicht voll wird.
  - 12–16: Grid laden nur, wenn der Speicher durch PV heute voraussichtlich nicht voll wird (Rest-vorhersage heute).
- Protections: enforce SOC min/max, cap currents, and avoid simultaneous grid + PV charging.

## Flow (Text-Bullets)
1) Tick (alle 5–10 min) starten.  
2) Zustände lesen: SOC, PV-Leistung, Hauslast, Tariffenster, Forecast heute (Rest), Forecast morgen.  
3) Ziel-SOC je Tariff setzen (low/medium/high) und Bedarf an Grid-Ladung ableiten.  
4) **PV-Surplus prüfen (PV > Last + Reserve) – höchste Priorität, aber Ziel: Akku vor 18:00 voll:**  
   - **Ja: PV nutzt vollen PV-Strom; falls SOC-Ziel vor 18:00 sonst nicht erreicht wird, erlaube zusätzlich Grid-Ladung als Ergänzung, zusammen maximal bis zum eingestellten max Charge-Current (parallel PV + Grid).**  
   - Nein: weiter mit Grid-Check.  
5) Grid-Check (nur wenn KEIN PV-Surplus + low/medium + Bedarf):  
   - Nein: Grid aus, Grid-Current = 0.  
   - Ja: Grid an, Grid-Current = Limit, Charge-Current = Limit.  
6) Forecast-Sperren (nur wenn KEIN PV-Surplus):  
   - 00–06: Grid nur, wenn Forecast morgen den Speicher sonst nicht füllt; sonst Grid aus.  
   - 12–16: Grid nur, wenn Rest-Forecast heute den Speicher sonst nicht füllt; sonst Grid aus.  
7) SOC-Regeln:  
   - Wenn SOC < Ziel: Charge-Current erhöhen (innerhalb Limits), Discharge drosseln.  
   - Wenn SOC > obere Guard: Discharge erhöhen für Lastdeckung, Charge drosseln.  
8) Schutz: SOC min/max einhalten, Stromlimits kappen, keine gleichzeitige Grid- und PV-Ladung.  
9) Ende des Ticks.  

## Next
- Translate this logic into Home Assistant automations/blueprints: conditions on time windows, SOC thresholds, forecasts; actions setting number.* and switch.* entities.
- Dry-run per window (low/medium/high) and verify current caps are enforced.




flowchart TD
    start[Tick] --> pv{PV > Last + Reserve?}
    pv -- Ja --> pvCharge[PV lädt Batterie bis max Charge-Current]
    pv -- Nein --> socMin{SOC > Mindestwert?}

    pvCharge --> pvGoal{SOC-Ziel vor 18:00 erreicht?}
    pvGoal -- Nein --> pvGridHelp[Ergänze Grid-Ladung parallel zu PV bis max Charge-Current]
    pvGoal -- Ja --> toTariff1[Geh zu Tarif-Logik]
    pvGridHelp --> toTariff1

    socMin -- Ja --> discharge[Entlade für Last]
    socMin -- Nein --> hold[Keine Entladung]

    discharge --> toTariff1
    hold --> toTariff1

    toTariff1 --> tariff{Tarif-Fenster?}

    tariff --> low12{Low 00-06}
    tariff --> low34{Low 06-12}
    tariff --> low56{Low 12-16}
    tariff --> normal1{Normal 21-02}
    tariff --> normal2{Normal 16-18}
    tariff --> high{High 18-21}

    low12 --> fTomorrow{Forecast morgen füllt voll?}
    fTomorrow -- Ja --> blockGrid12[Keine Grid-Ladung]
    fTomorrow -- Nein --> grid12[Grid-Ladung erlauben bis Ziel SOC]

    low56 --> fToday{Forecast heute Rest füllt voll?}
    fToday -- Ja --> blockGrid56[Keine Grid-Ladung]
    fToday -- Nein --> grid56[Grid-Ladung erlauben bis Ziel SOC]

    low34 --> grid34[Grid-Ladung erlauben Bedarf]
    normal1 --> gridN1[Optionale Ladung moderate Ziel SOC]
    normal2 --> gridN2[Optionale Ladung bis Ziel vor 18:00]
    high --> dischargeHigh[Entlade für Last; keine Grid-Ladung]

    blockGrid12 --> guard[Schutzkappen: SOC min/max, Stromlimits, kein Grid+PV > Limit]
    grid12 --> guard
    blockGrid56 --> guard
    grid56 --> guard
    grid34 --> guard
    gridN1 --> guard
    gridN2 --> guard
    dischargeHigh --> guard
    guard --> endNode[Ende Tick]


