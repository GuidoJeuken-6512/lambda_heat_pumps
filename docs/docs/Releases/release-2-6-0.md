---
title: "Release 2.6.0"
---

# Release 2.6.0

*Zuletzt geändert am 24.06.2026*

> **Aktueller Release** · Branch `V2.6.0`

---

## Zusammenfassung

Release 2.6.0 führt eine neue Climate-Entity für den Kühlbetrieb je Heizkreis ein (`cooling_circuit`), analog zur bestehenden `heating_circuit`-Entity. Sie nutzt dieselbe Quelle für die Ist-Raumtemperatur, schreibt ihren Sollwert aber auf das dedizierte Kühl-Sollwert-Register. Die Funktion ist standardmäßig deaktiviert und wird über eine neue Option im Options-Flow der Integration aktiviert. Keine Breaking Changes.

---

## Neue Funktionen

### Kühlkreis-Climate-Entity (`cooling_circuit`)

**Betroffen:** `custom_components/lambda_heat_pumps/climate.py` · `custom_components/lambda_heat_pumps/const_sensor.py`

Für jeden erkannten Heizkreis kann jetzt zusätzlich zur Heizkreis-Entity (`climate.<prefix>_hc<n>_heating_circuit`) eine Kühlkreis-Entity erzeugt werden: `climate.<prefix>_hc<n>_cooling_circuit`.

- **Ist-Temperatur**: identische Quelle wie `heating_circuit` (`room_device_temperature`, relative Registeradresse 4)
- **Soll-Temperatur**: eigenes Kühl-Sollwert-Register (`set_cooling_mode_room_temperature`, relative Registeradresse 52) — ergibt z. B. Register **5052** für HC1, **5152** für HC2, **5252** für HC3, …
- **HVAC-Modus**: `cool` (statt `heat` bei der Heizkreis-Entity)
- **Temperaturbereich**: nutzt dieselben Optionen wie der Heizkreis (`heating_circuit_min_temp` / `heating_circuit_max_temp`), da es sich um denselben physischen Raum handelt

Neuer Eintrag in `CLIMATE_TEMPLATES` (`const_sensor.py`):

```python
"cooling_circuit": {
    "relative_address": 4,         # room_device_temperature (wie heating_circuit)
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

Die Entity wird pro Heizkreis in `async_setup_entry()` (`climate.py`) erzeugt — mit denselben zentralen Routinen wie die bestehenden Climate-Entities (`generate_base_addresses`, `generate_sensor_names`, `build_subdevice_info`, `get_compatible_sensors`).

### Neue Option: Kühlbetrieb (`cooling_mode_enabled`)

**Betroffen:** `custom_components/lambda_heat_pumps/config_flow.py` · `custom_components/lambda_heat_pumps/const_base.py`

Im Options-Flow der Integration steht eine neue Schaltfläche **„Kühlbetrieb"** zur Verfügung (`cooling_mode_enabled`, Standard: `Aus`). Erst wenn sie aktiviert ist, werden die `cooling_circuit`-Entities für alle konfigurierten Heizkreise angelegt:

```python
if entry.options.get("cooling_mode_enabled", DEFAULT_COOLING_MODE_ENABLED):
    for idx in range(1, num_hc + 1):
        if "cooling_circuit" not in compatible_climates:
            continue
        entities.append(
            LambdaClimateEntity(coordinator, entry, "cooling_circuit", idx, hc_addresses[idx], sensor_translations)
        )
```

### Übersetzungen

Die neue Option und die neue Entity wurden in den deutschen und englischen Übersetzungen ergänzt (`translations/de.json`, `translations/en.json`):

- Options-Flow: Label „Kühlbetrieb" / „Cooling Mode" mit Beschreibungstext
- Entity-Name: „Kühlkreis" / „Cooling Circuit" (analog zu „Heizkreis" / „Heating Circuit")

---

## Migration / Breaking Changes

**Keine Breaking Changes.**

Die neue Entity wird nur erzeugt, wenn die Option `cooling_mode_enabled` explizit aktiviert wird. Bestehende Installationen sind ohne Aktivierung der Option vollständig unverändert — `unique_id`, `entity_id` und Verhalten aller bestehenden Entities bleiben gleich.

---

## Betroffene Dateien

| Datei | Änderung |
|---|---|
| `custom_components/lambda_heat_pumps/const_base.py` | Neue Konstante `DEFAULT_COOLING_MODE_ENABLED = False` |
| `custom_components/lambda_heat_pumps/const_sensor.py` | Neuer `CLIMATE_TEMPLATES`-Eintrag `cooling_circuit` |
| `custom_components/lambda_heat_pumps/climate.py` | Neue Entity-Erzeugung je Heizkreis (gegated durch `cooling_mode_enabled`); HVAC-Mode-Default und Sollwert-Key-Mapping erweitert |
| `custom_components/lambda_heat_pumps/config_flow.py` | Neue Boolean-Option `cooling_mode_enabled` im Options-Flow |
| `custom_components/lambda_heat_pumps/translations/de.json` | Übersetzungen für Option und Entity ergänzt |
| `custom_components/lambda_heat_pumps/translations/en.json` | Übersetzungen für Option und Entity ergänzt |
