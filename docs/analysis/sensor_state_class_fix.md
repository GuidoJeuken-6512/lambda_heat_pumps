# Sensor state_class Fix — Lambda Heat Pump Integration

## Warning
Historical Date will be lost for all changed entities


## Context
Home Assistant stores long-term statistics only for sensors that have a `state_class` set. The class must be semantically correct:
- `measurement` — instantaneous values that can go up/down (temperatures, flow rates, %, COP)
- `total` — cumulative counters with a `last_reset` (e.g., daily energy periods)
- `total_increasing` — monotonically increasing counters (e.g., accumulated energy)

Several sensors in `const_sensor.py` are incorrectly assigned `state_class: "total"` for values that are **not** cumulative counters. HA will attempt to track these as resettable totals, producing incorrect statistics (and logs warnings for `total` sensors with no unit). The fix is to change them to `"measurement"`.

## Issues Found

All in `custom_components/lambda_heat_pumps/const_sensor.py`:

| Dict | Key | Current | Unit | Correct | Reason |
|------|-----|---------|------|---------|--------|
| `HP_SENSOR_TEMPLATES` | `error_number` | `total` | None | `measurement` | Error code, fluctuates freely |
| `HP_SENSOR_TEMPLATES` | `volume_flow_heat_sink` | `total` | l/h | `measurement` | Instantaneous flow rate |
| `HP_SENSOR_TEMPLATES` | `volume_flow_energy_source` | `total` | l/min | `measurement` | Instantaneous flow rate |
| `HP_SENSOR_TEMPLATES` | `compressor_unit_rating` | `total` | % | `measurement` | Instantaneous percentage |
| `HP_SENSOR_TEMPLATES` | `cop` | `total` | None | `measurement` | Instantaneous COP ratio |
| `HP_SENSOR_TEMPLATES` | `request_type` | `total` | None | `measurement` | Numeric enum code |
| `BOIL_SENSOR_TEMPLATES` | `error_number` | `total` | None | `measurement` | Error code |
| `BUFF_SENSOR_TEMPLATES` | `error_number` | `total` | None | `measurement` | Error code |
| `SOL_SENSOR_TEMPLATES` | `error_number` | `total` | None | `measurement` | Error code |
| `HC_SENSOR_TEMPLATES` | `error_number` | `total` | None | `measurement` | Error code |
| `SENSOR_TYPES` | `ambient_error_number` | `total` | None | `measurement` | Error code |
| `SENSOR_TYPES` | `emgr_error_number` | `total` | None | `measurement` | Error code |

**Out of scope:** Text/enum sensors (`operating_state`, `relais_state_2nd_heating_stage`, etc.) intentionally have no `state_class` — HA statistics require numeric values, so these cannot be included in long-term statistics. They will remain as-is.

## File to Modify
- `custom_components/lambda_heat_pumps/const_sensor.py`

## Changes
12 targeted edits: change `"state_class": "total"` → `"state_class": "measurement"` for each sensor listed above. No other changes needed.

## Impact on Existing Historical Data

When `state_class` changes for a sensor, HA detects a **metadata mismatch** in its `statistics_meta` table:

**Sensors with `total` + no unit** (`error_number` × 5, `ambient_error_number`, `emgr_error_number`, `cop`, `request_type`):
- HA almost certainly was **not** recording long-term statistics for these at all — `total` sensors without a unit cause HA to skip statistics silently (and log warnings internally). No existing statistics data to lose.
- After the fix, HA will start recording them correctly as `measurement` statistics.

**Sensors with `total` + unit** (`volume_flow_heat_sink` l/h, `volume_flow_energy_source` l/min, `compressor_unit_rating` %):
- HA **may** have been recording statistics for these, but treating cumulative/rising behavior as a "total" — incorrect data.
- After the fix, HA will detect the `state_class` metadata mismatch and show these sensors in **Developer Tools → Statistics** as needing attention.
- Action needed: go to **Developer Tools → Statistics**, find the 3 sensors, and click **Fix issue** to clear the old malformed metadata. New data will then be recorded correctly as `measurement`.
- Old incorrect statistics rows remain in the DB but are effectively abandoned — they won't appear in history graphs once the metadata is corrected.

**No data loss risk** — short-term history in the `states` table is entirely unaffected by this change.

## Verification
1. Restart HA after deploying the change
2. Check `home-assistant.log` — warnings about `total` sensors without units should be gone
3. Open **Developer Tools → Statistics** in HA and confirm the 12 sensors now appear with correct `state_class: measurement` and are accumulating long-term statistics
4. For the 3 sensors with `total` + unit: go to **Developer Tools → Statistics** and click **Fix issue** on any metadata mismatch warnings
