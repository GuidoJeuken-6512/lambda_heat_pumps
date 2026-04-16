---
title: "Release 2.5.0"
---

# Release 2.5.0

*Last updated: 16.04.2026*

> **Current Release** · Branch `V2.5.0`

---

## Summary

Release 2.5.0 is a pure code quality and stability release with no breaking changes. It addresses 3 critical issues (race condition in the reload mechanism, event-loop-bound Modbus locks, unhandled exceptions in the auto-detection background task), 4 high-priority issues (entity registry listener without debounce, non-atomic sensor ID updates, missing persist flush on shutdown, state inconsistency on failed climate write), and 4 medium-priority issues (fragile JSON repair logic, missing temperature validation, batch limit optimization, missing version field in the persist file). Additionally, ~110 lines of hardcoded debug code and dead code were removed, and log levels were standardized.

**No impact on `unique_id`, `entity_id`, or `sensor_id` — all changes are non-destructive.**

---

## Critical Fixes

### K-01 · Race Condition in Reload Flag Fixed

**Affected:** `custom_components/lambda_heat_pumps/__init__.py` · `async_reload_entry()`

**Problem:** The fast-path check before acquiring the lock read `_entry_reload_flags` without holding the lock. Between the first check (False) and acquiring the lock, a parallel call could see the same state and also proceed.

**Fix:** The fast path now uses `lock.locked()` — an atomic, non-blocking check. The flag is set immediately after acquiring the lock (no window between check and set):

```python
# Before (buggy):
if _entry_reload_flags.get(entry_id, False):   # without lock — TOCTOU
    return True
async with reload_lock:
    if _entry_reload_flags.get(entry_id, False):
        return True
    _entry_reload_flags[entry_id] = True       # too late

# After (correct):
if reload_lock.locked():                       # atomic, no lock needed
    return True
async with reload_lock:
    _entry_reload_flags[entry_id] = True       # immediately after acquiring lock
```

---

### K-02 · Exception in Background Auto-Detection Task Properly Logged

**Affected:** `custom_components/lambda_heat_pumps/__init__.py` · `background_auto_detect()`

**Problem:** When the background module-detection task failed, the exception was only logged at `INFO` level — without a full traceback. Errors were nearly invisible in the log.

**Fix:** Log level raised to `WARNING`, `exc_info=True` added for full traceback:

```python
# Before:
_LOGGER.info("AUTO-DETECT: Background auto-detection failed: %s ...", ex)

# After:
_LOGGER.warning("AUTO-DETECT: Background auto-detection failed: %s ...", ex, exc_info=True)
```

---

### K-03 · Modbus Locks Lazily Initialized

**Affected:** `custom_components/lambda_heat_pumps/modbus_utils.py`

**Problem:** `asyncio.Lock()` objects were created at module level on import and are therefore bound to the asyncio event loop at import time. When the loop is recreated (e.g., in test environments), locks become invalid and can cause `RuntimeError`.

**Fix:** Lazy initialization via getter functions — the lock is only created on first call:

```python
# Before:
_modbus_read_lock = asyncio.Lock()   # bound at import time

# After:
_modbus_read_lock: asyncio.Lock | None = None

def _get_modbus_read_lock() -> asyncio.Lock:
    global _modbus_read_lock
    if _modbus_read_lock is None:
        _modbus_read_lock = asyncio.Lock()
    return _modbus_read_lock
```

---

## High Priority

### H-01 · Entity Registry Listener with Debounce

**Affected:** `custom_components/lambda_heat_pumps/coordinator.py` · `_on_entity_registry_changed()`

**Problem:** Every change in the entity registry immediately triggered a new `async_create_task` call for `_update_entity_address_mapping()`. When many entities changed simultaneously (e.g., during initial load), many parallel mapping updates with redundant Modbus reads were created.

**Fix:** 250ms debounce with `async_call_later` — overlapping events are merged into a single update:

```python
if self._registry_update_cancel is not None:
    self._registry_update_cancel()

@callback
def _delayed_update(_now):
    self._registry_update_cancel = None
    self.hass.async_create_task(self._update_entity_address_mapping())

self._registry_update_cancel = async_call_later(self.hass, 0.25, _delayed_update)
```

---

### H-02 · Sensor ID Updates Atomic

**Affected:** `custom_components/lambda_heat_pumps/coordinator.py` · `_detect_and_handle_sensor_changes()`

**Problem:** `self._sensor_ids` and `self._thermal_sensor_ids` were directly overwritten within the processing loop on each iteration. At `await` points between iterations, a concurrent `_persist_counters` call could see an inconsistent intermediate state.

**Fix:** Processing on local copies; atomic swap at the end — no `await` between assignments:

```python
local_sensor_ids = dict(self._sensor_ids)
local_thermal_sensor_ids = dict(self._thermal_sensor_ids)
# ... processing on local copies ...
# Atomic swap:
self._sensor_ids = persist_data["sensor_ids"]
self._thermal_sensor_ids = persist_data["thermal_sensor_ids"]
```

---

### H-03 · Persist Flush on Shutdown

**Affected:** `custom_components/lambda_heat_pumps/__init__.py` · `async_unload_entry()`  
**Affected:** `custom_components/lambda_heat_pumps/coordinator.py` · `_persist_counters()`

**Problem:** The 30-second debounce for disk writes could cause changes within the debounce window to be lost on HA shutdown (no forced flush).

**Fix:** `_persist_counters()` receives an optional `force` parameter; when the integration is unloaded, `force=True` is called:

```python
# In _persist_counters():
async def _persist_counters(self, force: bool = False):
    if not force and current_time - self._persist_last_write < self._persist_debounce_seconds:
        return  # debounce

# In async_unload_entry():
if getattr(coordinator, "_persist_dirty", False):
    await coordinator._persist_counters(force=True)
```

---

### H-04 · Climate Write Error State Inconsistency Fixed

**Affected:** `custom_components/lambda_heat_pumps/climate.py` · `async_set_temperature()`

**Problem:** When `async_write_registers()` returned `None` (no `isError` attribute), `coordinator.data[key] = temperature` was still set — a false local state update without a confirmed Modbus write.

**Fix:** Explicit check for `None` before state update; on error, the device value is reloaded via `async_request_refresh()`:

```python
if result is None or (hasattr(result, "isError") and result.isError()):
    _LOGGER.error("Failed to write target temperature: %s", result)
    await self.coordinator.async_request_refresh()
    return

# Only on success: local state update
self.coordinator.data[key] = temperature
self.async_write_ha_state()
await self.coordinator.async_request_refresh()
```

---

## Medium Priority

### M-01 · JSON Repair Logic Simplified

**Affected:** `custom_components/lambda_heat_pumps/coordinator.py` · `_repair_and_load_persist_file()`

**Problem:** The function contained fragile regex-based JSON repair for duplicate keys (which `json.loads()` resolves automatically anyway), as well as a bug where `required_fields` were only checked if `last_operating_states` was present in the JSON.

**Fix:** Regex repair removed. Clear strategy: normalize valid JSON + fill in missing fields; corrupted JSON → create backup → delete → start empty. `required_fields` are always checked:

```python
# On corruption (previously: Regex repair):
backup_file = self._persist_file + ".backup"
# Create backup, delete file, start empty
os.remove(self._persist_file)
return {}
```

---

### M-02 · Modbus Batch Size Optimized

**Affected:** `custom_components/lambda_heat_pumps/coordinator.py`

**Problem:** The batch size was set to 120 registers. The Modbus standard allows a maximum of 125 holding registers per request — without a safety buffer for protocol overhead.

**Fix:** Limit lowered to 100 registers (conservative buffer):

```python
# Before:
or len(current_batch) >= 120  # Modbus safety margin

# After:
or len(current_batch) >= 100  # Modbus max 125 holding regs; 100 = safe margin
```

---

### M-03 · Climate Temperature Range Validation

**Affected:** `custom_components/lambda_heat_pumps/climate.py` · `LambdaClimateEntity.__init__()`

**Problem:** `min_temp` and `max_temp` were taken from the entry options without checking whether `min_temp < max_temp`. With an invalid configuration, HA would no longer be able to set any temperature.

**Fix:** Validation with automatic fallback to defaults:

```python
if min_temp >= max_temp:
    _LOGGER.warning(
        "Invalid temperature range min=%s >= max=%s for %s, using defaults",
        min_temp, max_temp, climate_type,
    )
    min_temp, max_temp = default_min, default_max
```

---

### M-05 · Persist File with Version Field

**Affected:** `custom_components/lambda_heat_pumps/coordinator.py` · `_persist_counters()`

**Problem:** `cycle_energy_persist.json` contained no version field. Without a version field, structural changes in future versions cannot be migrated.

**Fix:** Field `"version": 1` is inserted into all newly written persist files:

```json
{
  "version": 1,
  "heating_cycles": { ... },
  ...
}
```

---

## Code Quality

### Q-01 · Log Levels Standardized

Connection errors and health check results in `modbus_utils.py` and `coordinator.py` were corrected from `INFO` to the semantically correct level:

| Situation | Before | After |
|-----------|--------|-------|
| Modbus connection failed | `INFO` | `WARNING` |
| Health check error / no client | `INFO` | `DEBUG` |
| Modbus read failed | `INFO` | `WARNING` |
| Background task error | `INFO` | `WARNING` |

---

### Q-02 · Hardcoded Register 1020/1022 Debug Blocks Removed

~110 lines of hardcoded INT32 register debug code for registers 1020 and 1022 were removed from `coordinator.py`. The code contained conditional log outputs that were not suitable for production use and reduced readability.

---

### Q-03 · Dead Code `_generate_entity_id()` Removed

`coordinator.py` contained a method `_generate_entity_id()` that according to its own DEAD-CODE-GUARD comment is never called. The method was removed after verification (no calls found in the entire codebase).

---

### Q-04 · Log Prefix Constants Defined

In `__init__.py`, log prefix constants were defined for the most common log categories:

```python
_LOG_RELOAD = "RELOAD"
_LOG_AUTODETECT = "AUTO-DETECT"
_LOG_SETUP = "SETUP"
```

---

### Q-05 · Inline Imports Moved to Top

Five utility functions (`detect_sensor_change`, `get_stored_sensor_id`, `store_sensor_id`, `get_stored_thermal_sensor_id`, `store_thermal_sensor_id`) were moved from inside the method body of `_detect_and_handle_sensor_changes()` to the top of `coordinator.py`.

---

## Affected Files

| File | Type |
|------|------|
| `custom_components/lambda_heat_pumps/__init__.py` | Fix: Race Condition (K-01), Warning Log (K-02), Persist Flush on Shutdown (H-03), Log Constants (Q-04) |
| `custom_components/lambda_heat_pumps/coordinator.py` | Fix: Debounce (H-01), Atomic Sensor Update (H-02), Persist Version (M-05), JSON Repair (M-01), Batch Limit (M-02), Lazy Import (Q-05), Debug Code Removal (Q-02), Dead Code Removal (Q-03), Log Level (Q-01) |
| `custom_components/lambda_heat_pumps/modbus_utils.py` | Fix: Lazy Locks (K-03), Log Level (Q-01) |
| `custom_components/lambda_heat_pumps/climate.py` | Fix: State Inconsistency (H-04), Temperature Validation (M-03) |
| `tests/test_climate.py` | Test adjustment: `async_request_refresh` instead of `async_refresh` |
| `tests/test_init_simple.py` | Test adjustment: `lock.locked()` instead of flag check; `_get_modbus_read_lock()` instead of direct lock access |

---

## Migration / Breaking Changes

**No breaking changes for end users.**

`unique_id`, `entity_id`, and `sensor_id` of all entities remain unchanged. Existing dashboards, automations, and entity registry entries are not affected.

For developers: The internal functions `_get_modbus_read_lock()` and `_get_health_check_lock()` replace direct access to `_modbus_read_lock` / `_health_check_lock`. Custom tests that import the lock directly must be updated to use the getter.
