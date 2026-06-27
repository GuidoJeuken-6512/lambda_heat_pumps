---
title: "Release 2.6.0"
---

# Release 2.6.0

*Last updated: 2026-06-24*

> **Current Release** · Branch `V2.6.0`

---

## Summary

Release 2.6.0 introduces a new climate entity for cooling mode per heating circuit (`cooling_circuit`), analogous to the existing `heating_circuit` entity. It shares the same current-room-temperature source but writes its setpoint to the dedicated cooling setpoint register. The feature is disabled by default and is enabled via a new option in the integration's Options Flow. No breaking changes.

---

## New Features

### Cooling Circuit Climate Entity (`cooling_circuit`)

**Affected:** `custom_components/lambda_heat_pumps/climate.py` · `custom_components/lambda_heat_pumps/const_sensor.py`

For each detected heating circuit, an additional entity can now be created alongside the heating circuit entity (`climate.<prefix>_hc<n>_heating_circuit`): `climate.<prefix>_hc<n>_cooling_circuit`.

- **Current temperature**: identical source as `heating_circuit` (`room_device_temperature`, relative register address 4)
- **Target temperature**: dedicated cooling setpoint register (`set_cooling_mode_room_temperature`, relative register address 52) — e.g. register **5052** for HC1, **5152** for HC2, **5252** for HC3, …
- **HVAC mode**: `cool` (instead of `heat` for the heating circuit entity)
- **Temperature range**: reuses the same options as the heating circuit (`heating_circuit_min_temp` / `heating_circuit_max_temp`), since it's the same physical room

New entry in `CLIMATE_TEMPLATES` (`const_sensor.py`):

```python
"cooling_circuit": {
    "relative_address": 4,         # room_device_temperature (same as heating_circuit)
    "relative_set_address": 52,    # set_cooling_mode_room_temperature
    "name": "Cooling Circuit",
    "unit": "°C",
    "scale": 0.1,
    "precision": 0.1,
    "data_type": "uint16",
    "firmware_version": 1,
    "device_type": "hc",
    "writeable": True,
    "hvac_mode": {"cool"},
    "state_class": "measurement",
},
```

The entity is created per heating circuit in `async_setup_entry()` (`climate.py`) — reusing the same central utility functions as the existing climate entities (`generate_base_addresses`, `generate_sensor_names`, `build_subdevice_info`, `get_compatible_sensors`).

### New Option: Cooling Mode (`cooling_mode_enabled`)

**Affected:** `custom_components/lambda_heat_pumps/config_flow.py` · `custom_components/lambda_heat_pumps/const_base.py`

The integration's Options Flow now has a new **"Cooling Mode"** toggle (`cooling_mode_enabled`, default: `Off`). Only when enabled are the `cooling_circuit` entities created for all configured heating circuits:

```python
if entry.options.get("cooling_mode_enabled", DEFAULT_COOLING_MODE_ENABLED):
    for idx in range(1, num_hc + 1):
        if "cooling_circuit" not in compatible_climates:
            continue
        entities.append(
            LambdaClimateEntity(coordinator, entry, "cooling_circuit", idx, hc_addresses[idx], sensor_translations)
        )
```

### Translations

The new option and the new entity were added to both the German and English translations (`translations/de.json`, `translations/en.json`):

- Options Flow: label "Cooling Mode" / "Kühlbetrieb" with description text
- Entity name: "Cooling Circuit" / "Kühlkreis" (analogous to "Heating Circuit" / "Heizkreis")

---

## Affected Files

| File | Change |
|---|---|
| `custom_components/lambda_heat_pumps/const_base.py` | New constant `DEFAULT_COOLING_MODE_ENABLED = False` |
| `custom_components/lambda_heat_pumps/const_sensor.py` | New `CLIMATE_TEMPLATES` entry `cooling_circuit` |
| `custom_components/lambda_heat_pumps/climate.py` | New per-heating-circuit entity creation (gated by `cooling_mode_enabled`); HVAC mode default and setpoint key mapping extended |
| `custom_components/lambda_heat_pumps/config_flow.py` | New boolean option `cooling_mode_enabled` in the Options Flow |
| `custom_components/lambda_heat_pumps/translations/de.json` | Translations added for option and entity |
| `custom_components/lambda_heat_pumps/translations/en.json` | Translations added for option and entity |
