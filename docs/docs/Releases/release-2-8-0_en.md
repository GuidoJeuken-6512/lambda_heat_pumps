---
title: "Release 2.8.0"
---

# Release 2.8.0

*Last updated: 2026-07-25*

> **Current Release** · Branch `V2.8.0`

---

## Summary

Release 2.8.0 fixes four findings from [Issue #100](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/100) (data corruption from implausible energy jumps, unfiltered Lambda sentinel raw values, a write-only register returning an invalid reading, and a firmware filter for general sensors that never actually worked) and introduces two new, generic mechanisms to support them: range notation for `firmware_versions` and opt-in sentinel values per sensor. It also fixes a race condition from [Issue #105](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/105) that could cause PV-surplus and room-temperature writes to sporadically never reach the device, even though the log reported success. No breaking changes; all existing `firmware_version: X` sensors are unaffected.

---

## New Features

### Range notation for firmware versions (`firmware_versions`)

**Affected:** `custom_components/lambda_heat_pumps/utils.py`

Previously, a sensor template could only require a **minimum** firmware version (`"firmware_version": X` → active from version X onward, no upper bound). That's insufficient for registers that disappear again on newer controller generations (see finding below). New helper `_parse_firmware_versions()`:

```python
def _parse_firmware_versions(spec: list) -> set:
    """
    "X-Y"  -> range X to Y inclusive
    "-X"   -> exclude version X
    X      -> include version X (int)
    """
```

`get_compatible_sensors()` now checks, in this order:

1. `firmware_versions` (range notation) — if present
2. `firmware_version` (minimum, existing behavior) — if no `firmware_versions`
3. Neither field → always active

Example: `"firmware_versions": ["1-7"]` — sensor only active for firmware integer 1 through 7, disappears from version 8 onward.

### Opt-in sentinel values per sensor (`sentinel_values`)

**Affected:** `custom_components/lambda_heat_pumps/utils.py`, `custom_components/lambda_heat_pumps/coordinator.py`

`is_sentinel_value()` (see finding 2 below) only filters `0x8000` and the temperature-sensor-disconnected sentinel `-3000` globally. `-1` (`0xFFFF`) is deliberately **not** a global sentinel, since it's a legitimate reading for some sensors (e.g. temperature offsets). For registers where `-1` genuinely means "not available", this can now be opted into per sensor template:

```python
"sentinel_values": [65535],
```

`is_sentinel_value(raw_value, data_type, extra_sentinels)` checks this list in addition to the global sentinels.

Already applied to the defined request registers where `-1` means "no request": buffer 3005-3009 (`request_type`, `request_flow_line_temp_setpoint`, `request_return_line_temp_setpoint`, `request_heat_sink_temp_diff_setpoint`, `modbus_request_heating_capacity`) and HC 5006 (`operating_mode`) — each with `"sentinel_values": [65535]`. All other buffer/HC sensors are unaffected.

---

## Bug Fixes ([#100](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/100))

### Finding 1 — `calculate_energy_delta` clamped implausible jumps instead of discarding them

**Affected:** Energy consumption sensors on all heat pumps.

**Symptom:** After an implausible register jump (e.g. caused by a changed `int32_register_order`, see Release 2.7.0), the difference was clamped to `max_delta` and booked as real consumption — data corruption in the counter.

**Fix:** `calculate_energy_delta()` now returns `None` for a delta exceeding `max_delta` instead of clamping it. The caller in `coordinator.py` detects `None`, resets the reference reading to the current value, and books **nothing**.

**Threshold extracted and tightened:** `max_delta` used to be hardcoded as the literal `100.0` (kWh) in two places (the function default in `utils.py` **and** an explicit call in `coordinator.py`). Now single source of truth: `MAX_ENERGY_DELTA_WH = 5000` in `const_base.py` (5 kWh instead of the previous 100 kWh). The `coordinator.py` call no longer passes `max_delta` explicitly, relying on the default instead. The value comes from an analysis in `docs_md/ToDos/auto_32bit_register_handling.md`: a real register-order flip jumps by multiples of 65,536 (typically several MWh), while realistic consumption jumps per update cycle are a few hundred Wh — `5000 Wh` is well above normal consumption but far below any flip. Only this threshold was adopted; the full automatic flip-detection concept sketched there is **not** part of this release.

**Affected files:** `custom_components/lambda_heat_pumps/const_base.py`, `custom_components/lambda_heat_pumps/utils.py`, `custom_components/lambda_heat_pumps/coordinator.py`

### Finding 2 — Lambda sentinel raw values were never filtered

**Affected:** All int16 registers, temperature sensors in particular.

**Symptom:** The Lambda Modbus protocol 1.0 defines sentinel raw values for "register not available" (`32768` / `0x8000`) and "sensor disconnected" (`62536`, `-3000` as `int16`). These were previously scaled and stored unfiltered as real readings (e.g. a "temperature" of −300°C).

**Fix:** New function `is_sentinel_value()` checks the unscaled raw value before `scale` is applied. Affected sensors are set to `None` (→ entity `unavailable`), with an `INFO` log entry (raw value, register address, sensor ID). Applied at all five places where registers are read and scaled: batch read, single-register fallback, boiler, buffer, solar.

**Affected files:** `custom_components/lambda_heat_pumps/utils.py`, `custom_components/lambda_heat_pumps/coordinator.py`

### Finding 4a — `ambient_temperature` (register 0002) returns an invalid reading on some firmware

**Affected:** Register 0002 (`ambient_temperature`), all firmware versions.

**Symptom:** Register 0002 is documented as write-only from a certain firmware generation onward (feeding in an external outdoor temperature) and returns `0xFFFF` = −300°C when read. On older firmware, however, the register can return real temperature values — so removing the sensor outright would have been too blunt.

**Fix:** `ambient_temperature` is kept, but is now only available up to `V0.0.9-3K` (firmware integer 7) via `"firmware_versions": ["1-7"]`, and additionally uses `"sentinel_values": [65535]` to filter `0xFFFF` as "not available" specifically for this sensor — other sensors with a legitimate `-1` value (e.g. temperature offsets) are unaffected.

**Affected files:** `custom_components/lambda_heat_pumps/const_sensor.py`

### Related finding — general sensors were never filtered by firmware version

**Affected:** All general sensors (`SENSOR_TYPES`), including `ambient_temperature`.

**Symptom:** While implementing finding 4a it turned out the general sensor group (`SENSOR_TYPES`) — unlike HP/boiler/buffer/solar/heating-circuit sensors — was never passed through `get_compatible_sensors()`: neither for entity creation (`sensor.py`) nor for register reads (`coordinator.py::_read_general_sensors_batch`). A `firmware_version`/`firmware_versions` field on a general sensor therefore **never** had any effect, even before this release. Without this fix, the firmware range gating on `ambient_temperature` would have had no effect either.

**Fix:** `sensor.py` now creates general sensor entities via `get_compatible_sensors(SENSOR_TYPES, fw_version)`; `coordinator.py::_read_general_sensors_batch()` now receives the filtered sensor list as a parameter instead of iterating `SENSOR_TYPES` directly.

**Affected files:** `custom_components/lambda_heat_pumps/sensor.py`, `custom_components/lambda_heat_pumps/coordinator.py`

---

## Bug Fixes ([#105](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/105))

### PV-surplus / room-temperature writes could sporadically never reach the device

**Affected:** Users with PV-surplus or room-thermostat control enabled (periodic Modbus writes via `services.py`).

**Symptom:** The log regularly shows `✅ MODBUS WRITE SUCCESS`, but the written value sporadically never arrives at the device.

**Root cause:** Before every write, `wait_for_stable_connection()` checks connection stability via a health-check read. This health check used its own, separate lock (`_health_check_lock`), while the actual coordinator reads and the writes themselves shared a different, common lock (`_modbus_read_lock`). Since the two locks didn't exclude each other, the health-check read could run **concurrently** with a real coordinator read or write on the same connection — which can desync Modbus transactions on the wire (Transaction ID collision, or on serial gateways a frame dropped due to overlap), so the write is reported successful at the protocol level while the device never actually applies the value. Made worse by two independent, unsynchronized timers (the write interval `DEFAULT_WRITE_INTERVAL` and the read interval `DEFAULT_UPDATE_INTERVAL = 30`), whose relative phase drifts through a collision window over time.

**Fix:** The health check now uses the same `_modbus_read_lock` as all other Modbus operations (`async_read_holding_registers`, `async_read_input_registers`, `async_write_registers`) — health checks, reads, and writes on a connection are now strictly serialized, regardless of the chosen timer intervals. The separate `_health_check_lock` was removed.

**Affected files:** `custom_components/lambda_heat_pumps/modbus_utils.py`

---

## Affected Files

| File | Change |
|---|---|
| `custom_components/lambda_heat_pumps/const_base.py` | `MAX_ENERGY_DELTA_WH = 5000` new — single source of truth for the `calculate_energy_delta` threshold |
| `custom_components/lambda_heat_pumps/modbus_utils.py` | `_test_connection_health()` now uses the shared `_modbus_read_lock` instead of a separate `_health_check_lock` (Issue #105) |
| `custom_components/lambda_heat_pumps/utils.py` | `_parse_firmware_versions()` new; `get_compatible_sensors()` extended with range notation; `calculate_energy_delta()` returns `None` instead of `max_delta`, default from `MAX_ENERGY_DELTA_WH`; `is_sentinel_value()` new, with opt-in `extra_sentinels` parameter |
| `custom_components/lambda_heat_pumps/coordinator.py` | Caller of `calculate_energy_delta` handles `None` and no longer passes `max_delta` explicitly; sentinel check (including template `sentinel_values`) before scaling in 5 places, with `INFO` log; `_read_general_sensors_batch()` receives the filtered sensor list as a parameter |
| `custom_components/lambda_heat_pumps/sensor.py` | General sensor (`SENSOR_TYPES`) entity creation now uses `get_compatible_sensors()` |
| `custom_components/lambda_heat_pumps/const_sensor.py` | `ambient_temperature`: `"firmware_versions": ["1-7"]` + `"sentinel_values": [65535]`; buffer request registers 3005-3009 (5 sensors) + HC 5006 (`operating_mode`): `"sentinel_values": [65535]` |

---

## Open (not part of this release)

- **Finding 3 (undocumented registers 1024–1060):** Only 4 registers in this range (`config_parameter_24/33/50/60`) are actually undocumented placeholders. The firmware boundary for the new controller generation still needs clarification with the issue author; until then, sentinel filtering (finding 2) already protects against bad values.
- **Finding 4b (`volume_flow_heat_sink` unit/scale):** Not yet implemented.

Details: [ToDo document Issue #100](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/blob/V2.8.0/docs_md/ToDos/issue100_firmware_range_v280.md).
