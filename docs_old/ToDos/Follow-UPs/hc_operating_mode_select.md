# HC Operating Mode Select Entity mit State-Speicher

## Problem

Das Modbus-Register für `operating_mode` (Register 6, relativ zur HC Base-Adresse) gibt immer 65535 zurück und kann nicht gelesen werden. Daher benötigen wir eine Möglichkeit, den Wert zu speichern, ohne eine echte Helper-Entity zu erstellen.

## Lösung

Eine Select-Entity, die:

- Den Wert in `cycle_energy_persist.json` speichert (Key: `hc_last_operating_modes`, ähnlich wie `last_operating_states`)
- NICHT aus Modbus liest (da Register nicht lesbar)
- Bei Änderung den Wert auf Modbus schreibt (Register base_address + 6) UND in JSON speichert
- Beim Restart: Wert auf `None` setzen (nicht auf Modbus schreiben, da wir den tatsächlichen Wert nicht kennen)
- Ein Dropdown mit 8 Optionen anzeigt (0-7: OFF, MANUAL, AUTOMATIK, etc.)

## Implementierung

### 1. Neue Datei: `select.py`

Erstelle `custom_components/lambda_heat_pumps/select.py` mit:

- **LambdaOperatingModeSelect Klasse**:
  - Erbt von `CoordinatorEntity` und `SelectEntity`
  - Verwendet `HC_OPERATING_MODE` Mapping aus `const_mapping.py` für Optionen
  - Liest Wert aus `coordinator._last_operating_modes.get(hc_index)` (nicht aus Modbus)
  - Bei `async_select_option()`: Wert auf Modbus schreiben (Register base_address + 6) UND in JSON speichern
  - Verwendet `async_write_registers()` aus `modbus_utils.py`

### 2. Integration in `__init__.py`

- Füge `Platform.SELECT` zu `PLATFORMS` hinzu
- Importiere `select.py` Setup-Funktion

### 3. Setup-Funktion in `select.py`

- `async_setup_entry()` Funktion
- Erstellt `LambdaOperatingModeSelect` Entity für jeden Heizkreis (HC1, HC2, etc.)
- Verwendet `generate_sensor_names()` für Entity-Namen
- Verwendet `build_subdevice_info()` für Device-Info

### 4. State-Speicherung in JSON-Datei

- **Coordinator erweitern** (`coordinator.py`):
  - Füge `self._last_operating_modes = {}` hinzu (analog zu `self._last_operating_states`)
  - Lade `hc_last_operating_modes` aus JSON-Datei in `_repair_and_load_persist_file()`
  - Speichere `hc_last_operating_modes` in `_persist_counters()` (Key: `"hc_last_operating_modes"`)
  - **WICHTIG**: Beim Restart: Setze alle Werte auf `None` (nicht auf Modbus schreiben)
  
- **Select-Entity**:
  - Liest Wert aus `coordinator._last_operating_modes.get(hc_index)`
  - Bei Änderung: Aktualisiere `coordinator._last_operating_modes[hc_index]` und markiere als dirty
  - Zeigt "unknown" wenn Wert `None` ist
  - Initialwert: `None` (nicht "OFF", da wir den tatsächlichen Wert nicht kennen)

### 5. Modbus-Schreiben

- Bei `async_select_option()`:
  - Konvertiere Option (String) zu Wert (Integer) über `HC_OPERATING_MODE` Reverse-Mapping
  - Berechne Register-Adresse: `base_address + 6`
  - Verwende `async_write_registers()` aus `modbus_utils.py`
  - Aktualisiere `coordinator._last_operating_modes[hc_index]` mit neuem Wert
  - Markiere Coordinator als dirty für JSON-Persistierung
  - Logge Erfolg/Fehler
  - **NICHT beim Restart**: Beim Restart wird nichts auf Modbus geschrieben, da wir den tatsächlichen Wert nicht kennen

### 6. Übersetzungen

- Füge "Operating Mode" zu `translations/de.json` und `translations/en.json` hinzu
- Bereits vorhanden in Zeile 150 (de) und 157 (en)

### 7. Konfiguration

- Register: `relative_address: 6` (bereits in `HC_SENSOR_TEMPLATES` definiert)
- Mapping: `HC_OPERATING_MODE` (bereits in `const_mapping.py` definiert)
- Optionen: 0-7 (OFF, MANUAL, AUTOMATIK, AUTO-HEATING, AUTO-COOLING, FROST, SUMMER, FLOOR-DRY)

## Dateien

### Neue Datei

- `custom_components/lambda_heat_pumps/select.py`

### Zu ändernde Dateien

- `custom_components/lambda_heat_pumps/__init__.py` - PLATFORMS erweitern
- `custom_components/lambda_heat_pumps/coordinator.py` - `hc_last_operating_modes` hinzufügen (laden, speichern, beim Restart auf None setzen)
- `custom_components/lambda_heat_pumps/const_mapping.py` - Reverse-Mapping für Option-zu-Wert-Konvertierung (falls nötig)

## Technische Details

### Register-Adresse

- HC1: base_address = 5000, Register = 5000 + 6 = 5006
- HC2: base_address = 5100, Register = 5100 + 6 = 5106
- HC3: base_address = 5200, Register = 5200 + 6 = 5206

### Option-zu-Wert-Mapping

```python
HC_OPERATING_MODE = {
    0: "OFF",
    1: "MANUAL",
    2: "AUTOMATIK",
    3: "AUTO-HEATING",
    4: "AUTO-COOLING",
    5: "FROST",
    6: "SUMMER",
    7: "FLOOR-DRY",
    -1: "Unknown",
}
# Reverse: {"OFF": 0, "MANUAL": 1, "AUTOMATIK": 2, ...}
```

### State-Speicherung in JSON

- **Struktur in JSON**:
  ```json
  {
    "hc_last_operating_modes": {
      "1": 2,  // HC1 = AUTOMATIK
      "2": 1,  // HC2 = MANUAL
      "3": null  // HC3 = unbekannt (nach Restart)
    }
  }
  ```

- **Initialisierung**:
  - Beim Start: Lade `hc_last_operating_modes` aus JSON
  - **Beim Restart**: Setze alle Werte auf `None` (nicht auf Modbus schreiben)
  - Select-Entity zeigt "unknown" wenn Wert `None` ist

- **Bei Änderung**:
  - Neuer Wert wird in `coordinator._last_operating_modes[hc_index]` gespeichert
  - Coordinator markiert als dirty für JSON-Persistierung
  - Wert wird auf Modbus geschrieben (Register base_address + 6)

## Todos

- [ ] Erstelle `select.py` mit `LambdaOperatingModeSelect` Klasse
- [ ] Erweitere Coordinator um `hc_last_operating_modes` (laden, speichern, beim Restart auf None setzen)
- [ ] Implementiere State-Speicherung in JSON-Datei (via Coordinator)
- [ ] Implementiere Modbus-Schreiben bei `async_select_option()`
- [ ] Füge `Platform.SELECT` zu PLATFORMS in `__init__.py` hinzu
- [ ] Erstelle `async_setup_entry()` Funktion in `select.py`
- [ ] Füge Reverse-Mapping für Option-zu-Wert-Konvertierung hinzu (falls nötig)

