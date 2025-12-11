# External Energy Sensor Normalization

Goal: Make custom energy-consumption sensors resilient to missing domains and persist the normalized entity_id back into coordinator state.

## Current Status (Already Implemented)

✅ **Entity Registry Check**: Wenn Sensor nicht im State ist, wird Entity Registry geprüft (Zeilen 1541-1585 in `utils.py`)
  - Sensor wird akzeptiert, wenn er in Registry existiert, auch ohne State
  - Zero-Value Protection wird automatisch aktiviert bis Sensor verfügbar ist

✅ **Runtime Retry Mechanism**: In `_track_hp_energy_consumption` (Zeile 2015-2021)
  - Bei `unknown`/`unavailable` State wird einfach beim nächsten Update-Zyklus erneut versucht
  - Kein permanenter Fehler, nur temporäres Warten

✅ **Zero-Value Protection**: Verhindert Sprünge durch initiale 0-Werte beim Start

## Planned Steps (To Be Implemented)

- [ ] **Normalization in `utils.validate_external_sensors`**:
  - Prepend `sensor.` when no domain is present in sensor_entity_id
  - Try both raw and normalized IDs before giving up
  - Return config with normalized `sensor_entity_id` (always store full entity_id format)
  
- [ ] **Coordinator Integration**:
  - In `coordinator._load_offsets_and_persisted`: ensure the validated config (with normalized IDs) is stored in `_energy_sensor_configs`
  - Verify normalized IDs are persisted via `_sensor_ids` in sensor-change detection
  
- [ ] **Sensor-Change Detection**:
  - Verify sensor-change detection still logs and persists normalized IDs correctly
  - Ensure normalized IDs are used in `_detect_and_handle_sensor_changes()`

- [ ] **Testing**:
  - Add/adjust tests in `tests/test_energy_consumption_sensors.py` (and related)
  - Cover raw name without domain (e.g., `"lambda_wp_verbrauch"` should become `"sensor.lambda_wp_verbrauch"`)
  - Test persistence of normalized IDs in coordinator state
  - Test Entity Registry fallback with normalized IDs

- [ ] **Optional Enhancement - Runtime Re-Validation** (Future):
  - Consider periodic re-validation of external sensors (e.g., every 5-10 minutes)
  - Would allow detection of sensors created after coordinator startup
  - Low priority: normal use case is covered by Entity Registry check

## Notes

- Keep logging consistent with existing EXTERNAL-SENSOR-VALIDATION messages
- No change to default Modbus fallback behaviour
- Maintain backward compatibility: existing configs with full entity_ids should continue to work

## Proposed Code Changes

```python
def validate_external_sensors(hass: HomeAssistant, energy_sensor_configs: dict) -> dict:
    """
    Validiere externe Sensoren und gib bereinigte Konfiguration zurück.
    
    ENHANCEMENT: Normalisiert Sensor-IDs (fügt 'sensor.' Prefix hinzu wenn fehlend).
    Prüft zuerst Entity Registry bei fehlendem State (bereits implementiert).
    """
    validated_configs = {}
    fallback_used = False

    for hp_key, sensor_config in energy_sensor_configs.items():
        raw_id = sensor_config.get("sensor_entity_id")
        if not raw_id:
            _LOGGER.warning(f"EXTERNAL-SENSOR-VALIDATION: {hp_key} - Keine sensor_entity_id konfiguriert")
            continue

        # NORMALIZATION: Füge 'sensor.' Prefix hinzu wenn kein Domain vorhanden
        sensor_id = raw_id if "." in raw_id else f"sensor.{raw_id}"

        # Prüfe zuerst normalisierte ID
        sensor_state = hass.states.get(sensor_id)
        
        # Fallback: Wenn normalisierte ID nicht funktioniert, versuche Original
        if sensor_state is None and sensor_id != raw_id:
            sensor_state = hass.states.get(raw_id)
            if sensor_state is not None:
                _LOGGER.info(f"EXTERNAL-SENSOR-VALIDATION: {hp_key} - Sensor mit Original-ID gefunden, normalisiere zu '{sensor_id}'")

        if sensor_state is None:
            # Sensor nicht im State gefunden - prüfe Entity Registry (bereits implementiert)
            _LOGGER.warning(
                f"EXTERNAL-SENSOR-VALIDATION: {hp_key} - Sensor '{sensor_id}' "
                f"nicht im State gefunden, prüfe Entity Registry..."
            )
            
            entity_registry = async_get_entity_registry(hass)
            entity_entry = entity_registry.async_get(sensor_id)
            
            # Wenn nicht gefunden, versuche auch mit Original-ID
            if entity_entry is None and sensor_id != raw_id:
                entity_entry = entity_registry.async_get(raw_id)
                if entity_entry is not None:
                    _LOGGER.info(f"EXTERNAL-SENSOR-VALIDATION: {hp_key} - Sensor mit Original-ID in Registry gefunden, normalisiere zu '{sensor_id}'")
            
            if entity_entry is None:
                _LOGGER.error(
                    f"EXTERNAL-SENSOR-VALIDATION: {hp_key} - Sensor '{raw_id}'/'{sensor_id}' "
                    f"existiert weder im State noch in der Entity Registry!"
                )
                fallback_used = True
                continue
            
            # Sensor existiert in Registry, aber noch nicht im State - akzeptiere ihn
            _LOGGER.info(
                f"EXTERNAL-SENSOR-VALIDATION: {hp_key} - Sensor '{sensor_id}' "
                f"in Entity Registry gefunden, wird akzeptiert"
            )
            # IMPORTANT: Speichere normalisierte ID
            validated_configs[hp_key] = {**sensor_config, "sensor_entity_id": sensor_id}
            continue
        
        # Prüfe ob Sensor verfügbar ist
        if sensor_state.state in ("unknown", "unavailable", None):
            _LOGGER.info(f"EXTERNAL-SENSOR-VALIDATION: {hp_key} - Sensor '{sensor_id}' ist nicht verfügbar (State: {sensor_state.state})")
            _LOGGER.info(f"EXTERNAL-SENSOR-VALIDATION: {hp_key} - Zero-Value Protection aktiviert")

        # IMPORTANT: Speichere normalisierte ID zurückschreiben
        validated_configs[hp_key] = {**sensor_config, "sensor_entity_id": sensor_id}
        _LOGGER.info(f"EXTERNAL-SENSOR-VALIDATION: {hp_key} - Sensor '{sensor_id}' ist gültig und verfügbar")

    if fallback_used:
        _LOGGER.info("EXTERNAL-SENSOR-VALIDATION: Einige externe Sensoren fehlerhaft - verwende interne Modbus-Sensoren als Fallback")
    return validated_configs
```

## Implementation Checklist

- [ ] Update `validate_external_sensors()` in `utils.py` with normalization logic
- [ ] Test normalization with various input formats (with/without domain, mixed)
- [ ] Verify normalized IDs are stored in `_energy_sensor_configs` in coordinator
- [ ] Verify normalized IDs are persisted in `_sensor_ids` during sensor-change detection
- [ ] Update unit tests to cover normalization scenarios
- [ ] Test Entity Registry fallback with normalized IDs
- [ ] Verify logging messages are consistent
- [ ] Test backward compatibility with existing configs