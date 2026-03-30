---
title: "Release 2.4.0"
---

# Release 2.4.0

*Last modified: 2026-03-29*

> **Current Release** · Branch `V2.4.0`

---

## Summary

Release 2.4.0 fixes several bugs: a critical error in the cycling sensor offset logic (offsets were re-added on every cycle event), a bug in mode detection for cycling counters (missed cycles due to shared state), a further critical bug where operating mode transitions were correctly detected but never counted (`cycling_entity` NameError in `increment_cycling_counter()`), and a bug where configured energy offsets were silently ignored at HA startup (`_apply_energy_offset()` was never called from `async_added_to_hass()`). Additionally, the configuration template, migration system, test suite, and documentation were fully updated.

---

## Bug Fixes

### Critical: Cycling offset was re-added on every cycle event

**Affected:** `custom_components/lambda_heat_pumps/utils.py` · `increment_cycling_counter()`

**Symptom:** Configured `cycling_offsets` from `lambda_wp_config.yaml` were not applied once but were re-added to the total counter on every detected operating mode change (e.g., heat pump switches to heating mode). With a configured offset of 1500 and 10 cycles:

```
Expected:  100 (base value) + 1500 (offset) + 10 (cycles) =  1610
Actual:    100 + 1500 × 11                                 = 16610
```

**Root cause:** `increment_cycling_counter()` read the full YAML offset value and added it on every call, without checking whether it was already included in the sensor value. In parallel, `_apply_cycling_offset()` in `sensor.py` correctly applied the offset once at HA startup — the two mechanisms competed.

**Fix:** The offset block was completely removed from `increment_cycling_counter()`. The `cycling_offsets` parameter was removed from the function signature. Sole responsibility for offsets now lies with `_apply_cycling_offset()` in `sensor.py`, which correctly uses differential-based application (`_applied_offset` tracking).

```python
# Before (buggy):
final_value = int(new_value + offset)   # offset = full YAML value, every time!

# After (correct):
final_value = new_value                 # only +1, no offset here
```

**How `_apply_cycling_offset()` works correctly (unchanged):**

```
HA startup:
  Stored value:       100
  _applied_offset:      0  (from attribute, last session)
  YAML offset:       1500
  Difference:        1500  → added
  Result:            1600  ✓
  _applied_offset = 1500  (saved for next restart)

Next HA startup:
  Stored value:      1600
  _applied_offset:   1500  (restored)
  YAML offset:       1500
  Difference:           0  → nothing added  ✓

Cycle event (after fix):
  increment_cycling_counter() adds only +1
  Result: 1600 + 1 = 1601  ✓
```

### Cycling counters: missed cycles due to shared state

**Affected:** `custom_components/lambda_heat_pumps/coordinator.py` · `_track_hp_energy_consumption()` and `_run_cycling_edge_detection()`
**Affected:** `custom_components/lambda_heat_pumps/utils.py` · `increment_cycling_counter()`

**Symptom:** Two HA systems monitoring the same heat pump showed diverging `heating_cycling_daily` values over time. Operating mode transitions were not always detected.

**Root cause:** `_last_operating_state` was written by two independent code paths with conflicting semantics:

- **Fast poll** (every 2 s, `coordinator.py:1615`): writes the last-seen Modbus value as edge-detection memory for cycling detection.
- **Full update** (every 30 s, `coordinator.py:2270` inside `_track_hp_energy_consumption`): writes the state read at the start of the full update as a side effect of energy attribution.

During a full update, all fast polls are blocked (`_full_update_running` flag). If the heat pump transitioned A → B → A during that window, the full update wrote `A` back to `_last_operating_state` on completion. The next fast poll saw `last=A, cur=A` → **no edge, both cycles silently lost**.

**Fix:** Energy attribution gets its own `_energy_last_operating_state` dict. The full update writes exclusively to `_energy_last_operating_state`; `_last_operating_state` is owned solely by the fast poll.

Additionally, `increment_cycling_counter()` now reads `cycling_entity._cycling_value` as the counter base instead of `hass.states.get()`, avoiding potential staleness after HA startup restoration.

```python
# _track_hp_energy_consumption – before:
last_state = self._last_operating_state.get(str(hp_idx), 0)   # ← fast poll state!
...
self._last_operating_state[str(hp_idx)] = current_state        # ← overwrites fast poll!

# After:
last_state = self._energy_last_operating_state.get(str(hp_idx), 0)
...
self._energy_last_operating_state[str(hp_idx)] = current_state
```

### Critical: Edge detection fired correctly but never counted cycles

**Affected:** `custom_components/lambda_heat_pumps/utils.py` · `increment_cycling_counter()`

**Symptom:** Operating mode transitions (e.g. STBY-FROST → CH) were detected correctly as edges internally — but the daily and total cycling counters remained at 0. No error messages appeared in the HA log at normal log levels.

**Root cause:** In `increment_cycling_counter()`, the variable `cycling_entity` was referenced on line 871 (check for `_cycling_value`) but was not defined until line 884. On the first execution of the `for sensor_id` loop, Python raised a `NameError`.

This propagated through `_run_cycling_edge_detection()` (no `try/except`) up to `_async_fast_update()`, where it was silently swallowed:

```python
except Exception as ex:
    _LOGGER.debug("Fast poll error (non-fatal): %s", ex)  # ← debug only, never visible
```

**Secondary consequence:** Because the exception occurred before writing `self._last_operating_state[str(hp_idx)] = op_state_val`, the stored state was never updated. On the next fast poll (2 s later), the edge detector saw the same transition again — detected it again, failed again. This loop ran every 2 seconds for the entire duration of CH mode without ever counting a single cycle.

**Fix:** The entity lookup (`cycling_entity = None` + lookup block) was moved **before** the read of `current`:

```python
# Before (buggy) — cycling_entity undefined on first call:
if cycling_entity is not None and hasattr(cycling_entity, "_cycling_value"):
    current = cycling_entity._cycling_value or 0
...
cycling_entity = None   # ← too late!
for entry_id, comp_data in ...:
    cycling_entity = comp_data["cycling_entities"].get(entity_id)

# After (correct):
cycling_entity = None   # ← defined first
for entry_id, comp_data in ...:
    cycling_entity = comp_data["cycling_entities"].get(entity_id)
...
if cycling_entity is not None and hasattr(cycling_entity, "_cycling_value"):
    current = cycling_entity._cycling_value or 0
```

### Critical: Configured energy offsets were silently ignored at HA startup

**Affected:** `custom_components/lambda_heat_pumps/sensor.py` · `LambdaEnergyConsumptionSensor.async_added_to_hass()`

**Symptom:** Configured `energy_consumption_offsets` from `lambda_wp_config.yaml` had no effect on HA startup. Sensors like `hot_water_energy_total` stayed at the raw persisted value — no offset applied, no log output.

**Root cause:** `_apply_energy_offset()` was correctly implemented (differential tracking, identical to the cycling offset mechanism) — but was never called. `async_added_to_hass()` called `restore_state()` and then `_apply_persisted_energy_state()` (which can overwrite `_energy_value` with the coordinator's raw value) — after which the function returned without ever calling `_apply_energy_offset()`.

**Fix:** `_apply_energy_offset()` is now called at the end of `async_added_to_hass()`, after `_apply_persisted_energy_state()`, so the offset is applied on top of the final raw value:

```python
# async_added_to_hass() – before (buggy):
await self.restore_state(last_state)
if our_state:
    self._apply_persisted_energy_state(our_state)
    self.async_write_ha_state()
# ← _apply_energy_offset() never called, offset silently ignored

# After (correct):
await self.restore_state(last_state)
if our_state:
    self._apply_persisted_energy_state(our_state)
    self.async_write_ha_state()
# Apply offset LAST — after _apply_persisted_energy_state()
if self._period == "total":
    await self._apply_energy_offset()
```

---

## New Features

### Negative offsets explicitly supported and documented

Both `cycling_offsets` and `energy_consumption_offsets` accept negative values. A negative offset subtracts the specified amount from the total counter — useful to correct an inflated starting value.

```yaml
cycling_offsets:
  hp1:
    heating_cycling_total: -200   # Subtracts 200 from the total count
```

Validation at load time only checks whether the value is numeric — no `>= 0` constraint.

### Thermal energy offsets documented and migrated

`energy_consumption_offsets` supports thermal offsets (`{mode}_thermal_energy_total`) in addition to electrical offsets (`{mode}_energy_total`). This was previously undocumented. All four thermal keys are now written to the `LAMBDA_WP_CONFIG_TEMPLATE` and are automatically inserted into existing `lambda_wp_config.yaml` files by the migration system:

```yaml
energy_consumption_offsets:
  hp1:
    heating_energy_total: 5000.0             # electrical
    heating_thermal_energy_total: 6500.0     # thermal (optional)
    hot_water_thermal_energy_total: 2600.0   # thermal (optional)
    cooling_thermal_energy_total: 800.0      # thermal (optional)
    defrost_thermal_energy_total: 120.0      # thermal (optional)
```

---

## Migration System

### New migration steps in `migrate_lambda_config_sections()`

On HA startup, the migration system checks existing `lambda_wp_config.yaml` files for missing keys and inserts them automatically — without modifying any other content.

**Step 1: `compressor_start_cycling_total` in `cycling_offsets`**

Files created before V2.4.0 were missing the `compressor_start_cycling_total` key in the `cycling_offsets` block. The migration detects the absence and inserts the line after `defrost_cycling_total:`, matching the existing indentation (commented or active):

```yaml
# Before:
cycling_offsets:
  hp1:
    defrost_cycling_total: 0

# After:
cycling_offsets:
  hp1:
    defrost_cycling_total: 0
    compressor_start_cycling_total: 0      # Offset for compressor start total
```

**Step 2: Thermal energy offset keys in `energy_consumption_offsets`**

The four thermal keys (`heating_thermal_energy_total`, `hot_water_thermal_energy_total`, `cooling_thermal_energy_total`, `defrost_thermal_energy_total`) are inserted in chain after `defrost_energy_total:` if missing. Already-present keys are skipped, so partial states are handled correctly.

---

## Configuration Template (`const_base.py`)

The `LAMBDA_WP_CONFIG_TEMPLATE` was extended:

- `compressor_start_cycling_total` was added to the cycling offset example (was missing despite being supported)
- Thermal energy offsets (`{mode}_thermal_energy_total`) were added as commented examples
- Note about negative offsets was inserted
- Comments unified in English

---

## Documentation

### User Documentation

| File | Change |
|---|---|
| `Anwender/offsets.md` | **New**: Standalone, comprehensive documentation for cycling and energy offsets; explains differential tracking, negative offsets, all use-case scenarios |
| `Anwender/lambda-wp-config.md` | Offset sections replaced with short summaries + link to `offsets.md`; negative and thermal offsets added to example |
| `Anwender/historische-daten.md` | Removed "buggy" warning banner; corrected functional description (point 2 previously described the buggy behavior); added thermal offsets |

> The notices `⚠️ die Funktion der Offsets ist fehlerhaft, bitte im Moment nicht einsetzen!` have been removed. Cycling offsets can be used without restriction from version 2.4.0.

### Developer Documentation

| File | Change |
|---|---|
| `Entwickler/migration-system.md` | **New**: Full technical description of the migration system (MigrationVersion enum, startup flow, all migration steps, backup logic, extension guide) |
| `Entwickler/offset-system.md` | **New**: Full technical description of the offset system (differential tracking, `applied_offset` persistence, sequence diagram, YAML structure) |
| `Entwickler/cycling-sensoren.md` | Edge detection code example updated (no more `cycling_offsets` parameter); increment logic example brought up to correct state; section 8 (Cycling Offsets) completely rewritten; log message corrected |
| `Entwickler/modbus-wp-config.md` | `cycling_offsets` section: code example now shows `_apply_cycling_offset()` instead of old bug code; thermal offsets added; negative offsets documented; full example extended |

---

## Tests

Test file `tests/test_offset_features.py` with **37 tests** (23 existing + 9 new migration tests + 5 new energy offset startup tests):

| Test Group | Scenarios Covered |
|---|---|
| `TestCyclingOffsetOnStartup` | Positive offset applied once; negative offset subtracted; offset 0 → no change; no config entry → no change |
| `TestCyclingOffsetDifferentialTracking` | Same offset not re-applied; increased offset adds only delta; decreased offset subtracts only delta |
| `TestCyclingOffsetPersistence` | `applied_offset` present in state attributes; restored after HA restart |
| `TestIncrementCyclingCounterNoOffset` | Increments exactly +1 without offset; `cycling_offsets` parameter no longer in signature (regression guard) |
| `TestEnergyOffsetApplication` | Electrical offset applied at startup; negative offset subtracted; same offset not applied twice |
| `TestEnergyOffsetIncrementDifferential` | First call updates `_applied_offset`; second call with same offset adds nothing extra |
| `TestOffsetConfigValidation` | Negative values pass validation; non-numeric values are set to 0; thermal keys are valid |
| `TestConfigTemplate` | Template contains `cycling_offsets`, `thermal_energy_total`, `compressor_start_cycling_total` |
| `TestMigrateCyclingOffsetCompressorStart` | **New**: Migration inserts `compressor_start_cycling_total` when missing; skips existing entries; correct indentation for active block |
| `TestMigrateThermalEnergyOffsets` | **New**: Migration inserts all 4 thermal energy keys; correct order; skips already-present keys; works across multiple HP blocks |
| `TestEnergyOffsetAppliedViaAsyncAddedToHass` | **New**: Energy offset applied via `async_added_to_hass()`; not re-applied on second restart; applied after coordinator state overwrites; call-site guard for total sensor; not called for daily sensor |

---

## Migration / Breaking Changes

**No breaking changes for end users.**

For developers: The `cycling_offsets` parameter was removed from `increment_cycling_counter()`. Any custom calls to this function must be updated:

```python
# Old (2.3.x):
await increment_cycling_counter(
    hass, mode=mode, hp_index=1, name_prefix="eu08l",
    cycling_offsets=self._cycling_offsets,   # ← remove this
)

# New (2.4.0):
await increment_cycling_counter(
    hass, mode=mode, hp_index=1, name_prefix="eu08l",
)
```

---

## Affected Files

| File | Type |
|---|---|
| `custom_components/lambda_heat_pumps/utils.py` | Bug fix: offset block removed from `increment_cycling_counter()`; entity lookup moved before `current` read (NameError fix); counter base now reads `_cycling_value` instead of HA state |
| `custom_components/lambda_heat_pumps/sensor.py` | Bug fix: `_apply_energy_offset()` now called in `async_added_to_hass()` after `_apply_persisted_energy_state()` (energy offsets were previously silently ignored) |
| `custom_components/lambda_heat_pumps/coordinator.py` | Bug fix: `_energy_last_operating_state` separated from `_last_operating_state`; `cycling_offsets` parameter removed from call sites |
| `custom_components/lambda_heat_pumps/const_base.py` | Extension: `LAMBDA_WP_CONFIG_TEMPLATE` (thermal offsets fully added) |
| `custom_components/lambda_heat_pumps/migration.py` | New: migration for `compressor_start_cycling_total` and thermal energy offset keys |
| `tests/test_offset_features.py` | Extended: 37 tests (9 new for migration scenarios, 5 new for energy offset startup regression) |
| `docs/docs/Anwender/offsets.md` | New: standalone offset documentation |
| `docs/docs/Anwender/lambda-wp-config.md` | Offset sections shortened + link to offsets.md |
| `docs/docs/Anwender/historische-daten.md` | Documentation updated |
| `docs/docs/Entwickler/migration-system.md` | New: technical documentation for migration system |
| `docs/docs/Entwickler/offset-system.md` | New: technical documentation for offset system |
| `docs/docs/Entwickler/cycling-sensoren.md` | Documentation updated |
| `docs/docs/Entwickler/modbus-wp-config.md` | Documentation updated |
