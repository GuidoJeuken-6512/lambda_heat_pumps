---
title: "Release 2.4.0"
---

# Release 2.4.0

*Last modified: 2026-03-21*

> **Current Release** · Branch `V2.4.0`

---

## Summary

Release 2.4.0 fixes a critical bug in the offset logic for cycling sensors that caused configured offsets from `lambda_wp_config.yaml` to be re-added on every cycle event instead of once at startup. Additionally, the documentation, configuration template, and test suite were fully updated.

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

### Thermal energy offsets documented

`energy_consumption_offsets` supports thermal offsets (`{mode}_thermal_energy_total`) in addition to electrical offsets (`{mode}_energy_total`). This was previously undocumented:

```yaml
energy_consumption_offsets:
  hp1:
    heating_energy_total: 5000.0             # electrical
    heating_thermal_energy_total: 6500.0     # thermal (optional)
    hot_water_thermal_energy_total: 2600.0   # thermal (optional)
```

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
| `Anwender/lambda-wp-config.md` | Removed "buggy" warning banners; documented negative offsets; added thermal offsets to example |
| `Anwender/historische-daten.md` | Removed "buggy" warning banner; corrected functional description (point 2 previously described the buggy behavior); added thermal offsets |

> The notices `⚠️ die Funktion der Offsets ist fehlerhaft, bitte im Moment nicht einsetzen!` have been removed. Cycling offsets can be used without restriction from version 2.4.0.

### Developer Documentation

| File | Change |
|---|---|
| `Entwickler/cycling-sensoren.md` | Edge detection code example updated (no more `cycling_offsets` parameter); increment logic example brought up to correct state; section 8 (Cycling Offsets) completely rewritten; log message corrected |
| `Entwickler/modbus-wp-config.md` | `cycling_offsets` section: code example now shows `_apply_cycling_offset()` instead of old bug code; thermal offsets added; negative offsets documented; full example extended |

---

## Tests

New test file `tests/test_offset_features.py` with **23 tests**:

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
| `custom_components/lambda_heat_pumps/utils.py` | Bug fix: offset block removed from `increment_cycling_counter()` |
| `custom_components/lambda_heat_pumps/coordinator.py` | Adjustment: `cycling_offsets` parameter removed from both call sites |
| `custom_components/lambda_heat_pumps/const_base.py` | Extension: `LAMBDA_WP_CONFIG_TEMPLATE` |
| `tests/test_offset_features.py` | New: 23 offset tests |
| `docs/docs/Anwender/lambda-wp-config.md` | Documentation updated |
| `docs/docs/Anwender/historische-daten.md` | Documentation updated |
| `docs/docs/Entwickler/cycling-sensoren.md` | Documentation updated |
| `docs/docs/Entwickler/modbus-wp-config.md` | Documentation updated |
