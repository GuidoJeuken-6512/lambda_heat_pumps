---
title: "Release 2.8.3"
---

# Release 2.8.3

*Last updated: 2026-08-08*

> **Current Release** · Branch `V2.8.3`

---

## Summary

Release 2.8.3 actually fully fixes [Issue #107](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/107) — the fix released as 2.8.2 (**retracted**, see below) only covered one of four affected locations and not the actual root cause. At its core, this is a recurring bug class: entity references were **reconstructed** from the device name instead of **resolved** via the stable `unique_id` in the entity registry. With a special character in the device name (underscore, hyphen, dot), a second heat pump/heating circuit with a diverging `entity_id`, or an entity the user manually renamed, that reconstruction drifted away from the actually registered `entity_id` — with different, sometimes very hard-to-spot symptoms (counters silently freeze, COP sensors stay `unknown`, heating curve computes with wrong set points). This release also includes a retrospective review of everything changed since V2.6.0, aimed at replacing custom code with Home Assistant's own building blocks and removing duplication — with no behavior change. No breaking changes; no existing entity's `entity_id`/`unique_id` changes.

**Fully tested live against a real migration path:** V2.6.0 → V2.8.0 (bug reproduced) → V2.8.3 (bug fixed, 0 regressions), plus a targeted scenario with artificially diverging `entity_id`s (simulating a user rename).

---

## Bug Fixes ([#107](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/107))

### Finding 1 — The 2.8.2 fix only covered the read side, not the write side

**Affected:** Mode-dependent consumption values and cycling counters on all existing installations with a special character in the device name.

**Symptom:** `hot_water_energy_daily/total`, `stby_energy_*`, `cooling_energy_*`, `defrost_energy_*`, and all `*_cycling_total/daily/2h/4h` sensors stopped advancing even after the 2.8.2 fix was released.

**Root cause:** `increment_energy_consumption_counter()` and `increment_cycling_counter()` (`utils.py`) still located their target sensors by reconstructing an `entity_id` from the device name and matching it textually against the entity registry — the 2.8.2 fix had only corrected the read path in `coordinator.py`.

**Fix:** Both functions now resolve their target entity via `unique_id`, using the shared helper `resolve_entity_id_by_unique_id()` (new in `utils.py`). The previous text-based construction remains as a self-healing fallback for the first cycle after an entity is newly created.

**Affected files:** `custom_components/lambda_heat_pumps/utils.py`

### Finding 2 — The actual root cause: a separator bug in `slugify_name_prefix_for_lookup()`

**Affected:** Any installation with an underscore, hyphen, or dot in the device name.

**Symptom:** `slugify_name_prefix_for_lookup()` called `slugify(name, separator="")`. Home Assistant's `slugify()` collapses *every* separator character (space, `_`, `-`, `.`, parentheses) uniformly to the chosen separator — regardless of its value. `normalize_name_prefix()` (which builds the `unique_id`) does not: it only removes spaces and leaves `_` untouched. A simple switch to `separator="_"` would have fixed underscores but broken names with spaces (`"Lambda WP"` → `"lambda_wp"` instead of `"lambdawp"`).

**Fix:** The function now decouples two concerns that were previously conflated: unicode transliteration first (umlauts etc., via the same `unidecode` library `homeassistant.util.slugify()` already depends on internally), then the existing, unchanged separator rule from `normalize_name_prefix()`. `entity_id` and `unique_id` agree on underscores again without regressing the space-handling case fixed in 2.7.0.

**Known, deliberately open residual gap:** A literal hyphen/dot/parenthesis in the device name is still passed through as-is in `entity_id` rather than collapsed to `_` — not a valid HA `entity_id` character, but consistent with `unique_id` handling and not part of what was reported in #107.

**Affected files:** `custom_components/lambda_heat_pumps/utils.py`

### Finding 3 — Energy/cycling counters stopped updating for a second heat pump (in-memory cache)

**Affected:** Installations with more than one heat pump where the actually registered `entity_id`s of the second (third, …) heat pump diverge from the currently computed form (e.g. discovered by auto-detection under an older version, or manually renamed).

**Symptom:** Even after finding 1, `hp2` counters kept freezing while `hp1` worked normally.

**Root cause:** `sensor.py` stores each created entity in `energy_entities`/`cycling_entities` (`hass.data`) keyed by the entity's own `entity_id` attribute — read *before* `async_add_entities()` has actually registered the entity with Home Assistant. The increment functions correctly resolve the real `entity_id` via the registry, but then looked up the entity *instance* in the cache using that resolved value — a miss, since the cache was keyed by the diverging, pre-registration value.

**Fix:** Both caches are now keyed by `unique_id` (stable by construction), applied consistently to the other consumers too: the daily "yesterday" sensor rollover (`automations.py`) and the energy-state persistence used to survive restarts (`coordinator.py`).

**Affected files:** `custom_components/lambda_heat_pumps/sensor.py`, `custom_components/lambda_heat_pumps/automations.py`, `custom_components/lambda_heat_pumps/coordinator.py`

### Finding 4 — COP sensors on a second heat pump permanently `unknown`

**Affected:** Same as finding 3.

**Symptom:** All `*_cop_daily/monthly/yearly/total/hourly` sensors on the second heat pump showed `unknown` permanently.

**Root cause:** `LambdaCOPSensor` reads its thermal/electrical source sensors via `self._thermal_energy_entity_id`/`self._electrical_energy_entity_id`, set once at construction from raw `generate_sensor_names()` text — never corrected against the entity registry. `hass.states.get()` looked up a non-existent entity_id, and the `async_track_state_change_event()` subscription never fired.

**Fix:** Both source `entity_id`s are resolved via `resolve_entity_id_by_unique_id()`, called once in `async_setup_entry()` before constructing each `LambdaCOPSensor`.

**Affected files:** `custom_components/lambda_heat_pumps/sensor.py`

### Finding 5 — Template sensors: fourth and last place of the same bug class

**Affected:** Same as findings 3/4 — plus the calculated COP (`*_cop_calc`) and the heating curve.

**Symptom:** Two user-visible consequences: the **calculated COP** (`*_cop_calc`) was stuck at `0.0` forever, because the generated template referenced `sensor.<name>_hp2_compressor_*_accumulated` while the registered entity is `sensor.<name-without-underscore>_hp2_…`; and the **heating curve** (`*_heating_curve_flow_line_temperature_calc`) silently fell back to the built-in default set points, while the **ECO reduction** never applied at all.

**Fix:** Two new shared helpers in `utils.py`:

- `resolve_sensor_entity_id()` bundles the recurring "generate names → adjust domain → resolve via `unique_id`" pattern (including the `_number` suffix that `number.py` appends to its `unique_id`).
- `resolve_template_entity_ids()` resolves entity references inside a rendered template string generically, without touching the template definitions themselves.

Where the registry has no match, the previous name-based form is kept — self-heals on the next start.

**Affected files:** `custom_components/lambda_heat_pumps/utils.py`, `custom_components/lambda_heat_pumps/template_sensor.py`

### Related finding — `Template not found` warning on every setup

**Affected:** Setup/reload log for `cooling`/`defrost`/`hot_water`/`stby`.

**Symptom:** `Template not found for <mode>_energy_hourly` was logged at `WARNING`, even though nothing is wrong — `hourly` is only defined as a template for `heating`, and the guard correctly skips the other four modes.

**Fix:** Downgraded to `DEBUG`.

**Affected files:** `custom_components/lambda_heat_pumps/sensor.py`

---

## Internal Refactoring (no behavior change)

Retrospective review of everything changed since V2.6.0, aimed at reusing Home Assistant's own building blocks and removing duplication — **no** `entity_id`/`unique_id` changes.

| Change | File |
|---|---|
| `get_int32_register_order()` now uses `utils.get_firmware_version()` instead of its own fallback cascade; dead import removed | `modbus_utils.py` |
| Six identical constructions of the internal energy sensor's `entity_id` → one helper `_default_internal_energy_entity_id()` | `coordinator.py` |
| Five identical blocks filling the cycling entity cache → one loop | `sensor.py` |
| `LambdaCyclingSensor._handle_reset()`: five identical `if`/`elif` branches → one condition (`CYCLING_RESET_INTERVALS`) | `sensor.py` |
| Sevenfold `[65535]` literal → named constant `SENTINEL_NO_REQUEST` | `const_sensor.py` |

**Deliberately *not* changed** (reviewed, replacing would have reintroduced bugs or was already optimal): the shared `asyncio.Lock` in `modbus_utils.py`, `MAX_ENERGY_DELTA_WH`, `FIRMWARE_CONFIG` — already using the right building blocks. `slugify_name_prefix_for_lookup()` must **not** be replaced by `homeassistant.util.slugify()` (live-verified, would reintroduce the #107 regression). The six sensor-change-detection sites in `coordinator.py` deliberately keep their name-based form (compared against a persisted value — resolving via the registry would report a spurious sensor change on existing installations and reset the energy baseline).

---

## Affected Files

| File | Change |
|---|---|
| `custom_components/lambda_heat_pumps/utils.py` | `resolve_entity_id_by_unique_id()`, `resolve_sensor_entity_id()`, `resolve_template_entity_ids()` new; `slugify_name_prefix_for_lookup()` separator fix; `increment_energy_consumption_counter()`/`increment_cycling_counter()` use registry lookup |
| `custom_components/lambda_heat_pumps/coordinator.py` | Energy-state persistence switched to `unique_id` keying; `_default_internal_energy_entity_id()` new |
| `custom_components/lambda_heat_pumps/sensor.py` | `energy_entities`/`cycling_entities` cache switched to `unique_id` keying; COP source `entity_id`s resolved via registry; cache loop and `_handle_reset()` deduplicated; log downgrade |
| `custom_components/lambda_heat_pumps/template_sensor.py` | Heating curve sensor resolves source entities (ambient temperature, set points, `operating_state`, `eco_temp_reduction`) via the registry |
| `custom_components/lambda_heat_pumps/automations.py` | "Yesterday" sensor rollover switched to `unique_id` keying |
| `custom_components/lambda_heat_pumps/modbus_utils.py` | `get_int32_register_order()` deduplicated |
| `custom_components/lambda_heat_pumps/const_sensor.py` | New `SENTINEL_NO_REQUEST` constant |

---

## Verification

- **Unit tests:** 541 → 559 passing (18 new tests), 1 skipped.
- **Full migration test** in a Docker test instance (2 heat pumps, device name `Lambda_EU10L`): installed V2.6.0 and recreated the config (baseline: counters advance) → upgraded to V2.8.0 (bug reproduced: base sensor advanced, all derived counters frozen, 26 of 30 COP sensors `unknown`, 8 `Template not found` warnings) → upgraded to V2.8.3 (all counters advance again, 0 of 30 COP sensors `unknown`, 0 `Template not found` warnings, 0 ERROR lines, all 330 `entity_id`/`unique_id` unchanged).
- **Additional divergence scenario:** 5 entities deliberately renamed (only `entity_id`, `unique_id` unchanged — simulating a user rename or a second heat pump created under an older version). Calculated COP jumped from `0.0` to the correct value; heating curve reacted to a changed set point on the renamed entity (log evidence: `mid=number.lambdaeu10l_hc2_heating_curve_mid_outside_temp` was correctly resolved).

Details on the registry-lookup architecture: [Energie-Sensor-Lookup über die Entity Registry](../Entwickler/energie-sensor-lookup-registry.md) (German).

---

## [2.8.2] - 2026-08-05 (retracted)

Pulled from releases — the fix only partially covered Issue #107 (see finding 1 above). Also included the `ambient_temperature` firmware-range correction ([#108](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/108)), which is unchanged and included in 2.8.3. Details: [CHANGELOG.md](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/blob/main/CHANGELOG.md).
