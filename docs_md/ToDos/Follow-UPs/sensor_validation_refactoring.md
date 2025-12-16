# Sensor-Validierung Refaktorierung

**Ziel:** Doppelten Code bei Sensor-Prüfungen für die Verbrauchsberechnung zusammenfassen und eine gemeinsame, robuste Prüf-Funktion erstellen.

## Problem

Aktuell gibt es doppelten Code an drei Stellen, die alle ähnliche Sensor-Prüfungen durchführen:

1. **`validate_external_sensors`** (utils.py, Zeile 1516-1559)
   - Prüft ob Sensor-State existiert
   - Prüft ob State "unknown", "unavailable", None ist
   - Prüft Entity Registry (wenn State nicht gefunden)

2. **`_update_energy_consumption`** (coordinator.py, Zeile 1997-2005)
   - Prüft ob Sensor-State existiert
   - Prüft ob State "unknown", "unavailable" ist
   - Gibt früh zurück wenn nicht verfügbar

3. **`_handle_sensor_change`** (coordinator.py, Zeile 518-550)
   - Prüft ob Sensor-State existiert
   - Prüft ob State "unknown", "unavailable", "None" ist
   - Liest DB-Wert und setzt Referenzwerte
   - Aktiviert Zero-Value Protection

## Lösung

### Gemeinsame Hilfsfunktion erstellen

Erstelle eine neue Funktion `check_sensor_availability()` in `utils.py`, die:
- Sensor-State prüft
- Optional Entity Registry prüft (falls State nicht gefunden)
- Einheitliches Ergebnis-Dictionary zurückgibt
- Robuste Fehlerbehandlung bietet

### Funktion-Signatur

```python
def check_sensor_availability(
    hass: HomeAssistant, 
    sensor_id: str,
    check_registry: bool = True
) -> dict:
    """
    Prüfe ob ein Sensor existiert und verfügbar ist.
    
    Prüft zuerst den Sensor-State, dann (optional) die Entity Registry.
    Gibt ein Dictionary mit allen relevanten Informationen zurück.
    
    Args:
        hass: Home Assistant Instanz
        sensor_id: Entity-ID des Sensors
        check_registry: Ob Entity Registry geprüft werden soll (Standard: True)
    
    Returns:
        dict mit folgenden Keys:
            - exists: bool - Sensor existiert (in State oder Registry)
            - available: bool - Sensor ist verfügbar (State nicht unknown/unavailable)
            - state: State-Objekt oder None
            - state_value: str oder None - State-Wert
            - in_registry: bool - Sensor existiert in Entity Registry
            - is_unknown: bool - State ist "unknown"
            - is_unavailable: bool - State ist "unavailable"
    """
```

### Implementierung

```python
def check_sensor_availability(
    hass: HomeAssistant, 
    sensor_id: str,
    check_registry: bool = True
) -> dict:
    """Prüfe ob ein Sensor existiert und verfügbar ist."""
    result = {
        "exists": False,
        "available": False,
        "state": None,
        "state_value": None,
        "in_registry": False,
        "is_unknown": False,
        "is_unavailable": False,
    }
    
    # Schritt 1: Prüfe Sensor-State
    sensor_state = hass.states.get(sensor_id)
    
    if sensor_state is not None:
        result["exists"] = True
        result["state"] = sensor_state
        result["state_value"] = sensor_state.state
        
        # Prüfe Verfügbarkeit
        if sensor_state.state in ("unknown", "unavailable", None):
            if sensor_state.state == "unknown":
                result["is_unknown"] = True
            elif sensor_state.state == "unavailable":
                result["is_unavailable"] = True
        else:
            result["available"] = True
        
        return result
    
    # Schritt 2: Sensor nicht im State - prüfe Entity Registry (falls gewünscht)
    if check_registry:
        entity_registry = async_get_entity_registry(hass)
        entity_entry = entity_registry.async_get(sensor_id)
        
        if entity_entry is not None:
            result["exists"] = True
            result["in_registry"] = True
            # Sensor existiert in Registry, aber noch nicht im State
            # (kann beim Start noch nicht verfügbar sein)
    
    return result
```

## Refaktorierung der drei Stellen

### 1. `validate_external_sensors` (utils.py)

**Vorher:**
```python
sensor_state = hass.states.get(sensor_id)
if sensor_state is None:
    # Fehlerbehandlung
if sensor_state.state in ("unknown", "unavailable", None):
    # Logging
```

**Nachher:**
```python
sensor_check = check_sensor_availability(hass, sensor_id, check_registry=True)

if not sensor_check["exists"]:
    # Fehlerbehandlung
    fallback_used = True
    continue

if not sensor_check["available"]:
    if sensor_check["in_registry"]:
        # Sensor in Registry, aber noch nicht im State
        _LOGGER.info("Sensor wird akzeptiert, Zero-Value Protection aktiviert")
    else:
        # Sensor im State, aber nicht verfügbar
        _LOGGER.info("Sensor nicht verfügbar, Zero-Value Protection aktiviert")
```

### 2. `_update_energy_consumption` (coordinator.py, ~Zeile 1997)

**Vorher:**
```python
current_energy_state = self.hass.states.get(sensor_entity_id)
if not current_energy_state or current_energy_state.state in ["unknown", "unavailable"]:
    if current_energy_state and current_energy_state.state == "unknown":
        _LOGGER.debug("Sensor not ready yet")
    else:
        _LOGGER.warning("Sensor not available")
    return
```

**Nachher:**
```python
from .utils import check_sensor_availability

sensor_check = check_sensor_availability(self.hass, sensor_entity_id, check_registry=False)
if not sensor_check["available"]:
    if sensor_check["is_unknown"]:
        _LOGGER.debug(f"Energy sensor {sensor_entity_id} not ready yet (state: unknown) - will retry on next update")
    else:
        _LOGGER.warning(f"Energy sensor {sensor_entity_id} not available (state: {sensor_check['state_value']})")
    return

current_energy_state = sensor_check["state"]
```

### 3. `_handle_sensor_change` (coordinator.py, ~Zeile 518)

**Wichtig:** Diese Funktion macht mehr als nur Sensor-Prüfung:
- Prüft ob Default-Sensor oder Custom-Sensor
- Liest DB-Wert vom Default-Sensor
- Setzt Referenzwerte (`_last_energy_reading`, `_energy_first_value_seen`)
- Aktiviert Zero-Value Protection wenn nötig
- Persistiert die Werte

**Nur die Sensor-Prüfung wird refaktoriert:**

**Vorher:**
```python
db_state = self.hass.states.get(new_sensor_id)
if db_state and db_state.state not in ("unknown", "unavailable", "None"):
    # DB-Wert lesen und verarbeiten
```

**Nachher:**
```python
from .utils import check_sensor_availability

sensor_check = check_sensor_availability(self.hass, new_sensor_id, check_registry=False)
if sensor_check["available"]:
    db_state = sensor_check["state"]
    # DB-Wert lesen und verarbeiten (rest der Logik bleibt unverändert)
else:
    # Zero-Value Protection (rest der Logik bleibt unverändert)
```

## Vorteile

1. **DRY-Prinzip:** Kein doppelter Code mehr
2. **Konsistenz:** Einheitliche Sensor-Prüfung an allen Stellen
3. **Wartbarkeit:** Änderungen nur an einer Stelle nötig
4. **Robustheit:** Entity Registry Prüfung wird konsistent verwendet
5. **Testbarkeit:** Gemeinsame Funktion kann isoliert getestet werden

## Wichtige Hinweise

- **`_handle_sensor_change` Logik bleibt erhalten:** Die gesamte Logik (DB-Wert lesen, Referenzwerte setzen, Zero-Value Protection) bleibt unverändert. Nur die Sensor-Prüfung wird durch die gemeinsame Funktion ersetzt.
- **Zero-Value Protection:** Die Zero-Value Protection Logik in `_update_energy_consumption` (Zeile 2057-2086) bleibt vollständig erhalten und funktioniert weiterhin wie bisher.
- **Entity Registry Prüfung:** Wird nur in `validate_external_sensors` verwendet (beim Setup), nicht in den laufenden Prüfungen (`_update_energy_consumption`, `_handle_sensor_change`).

## Umsetzung

1. Funktion `check_sensor_availability()` in `utils.py` erstellen
2. `validate_external_sensors()` refaktorieren
3. `_update_energy_consumption()` refaktorieren
4. `_handle_sensor_change()` refaktorieren (nur Sensor-Prüfung)
5. Tests durchführen
6. Dokumentation aktualisieren
