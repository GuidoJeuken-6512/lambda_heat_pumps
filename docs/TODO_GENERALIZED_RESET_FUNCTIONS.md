# TODO: Generalisierte Reset-Funktionen für alle Sensor-Typen

**Status:** 🟡 Pending  
**Priorität:** Mittel  
**Erstellt:** 2025-01-14  
**Zugewiesen:** AI Assistant  

## Problem

Die Energy Consumption Sensoren werden nicht um Mitternacht zurückgesetzt, da sie individuelle Signale verwenden statt der zentralen Automation. Das bestehende Cycling-System funktioniert korrekt, aber Energy Sensoren verwenden ein separates Signal-System.

### Aktuelle Architektur

**Cycling Sensoren (funktionieren):**
- Verwenden zentrale Signale aus `automations.py`:
  - `SIGNAL_RESET_DAILY` 
  - `SIGNAL_RESET_2H`
  - `SIGNAL_RESET_4H`
- Werden von zentraler Automation um Mitternacht zurückgesetzt

**Energy Consumption Sensoren (funktionieren NICHT):**
- Verwenden individuelle Signale pro Sensor:
  - `f"lambda_energy_reset_{self._hp_index}_{self._mode}_{self._period}"`
- Keine zentrale Automation sendet diese Signale!

## Lösungsansatz

Erstelle generalisierte, wiederverwendbare Reset-Funktionen, die:

1. **Das bestehende System erweitern** (nicht ersetzen)
2. **Alle Sensor-Typen unterstützen** (Cycling, Energy, zukünftige)
3. **Plugin-Architektur** für neue Sensor-Typen bieten
4. **Zentrale Verwaltung** aller Resets ermöglichen

## TODO-Liste

### 1. Hauptaufgabe: Generalisierte Reset-Funktionen
- [ ] **Status:** Pending
- [ ] **Beschreibung:** Erstelle generalisierte, wiederverwendbare Reset-Funktionen für alle Sensor-Typen
- [ ] **Dateien:** `automations.py`, `sensor.py`
- [ ] **Komplexität:** Hoch

### 2. Sofortiges Problem: Energy Sensoren Reset-Fix
- [ ] **Status:** Pending  
- [ ] **Beschreibung:** Behebe das Problem mit Energy Consumption Sensoren, die nicht um Mitternacht zurückgesetzt werden
- [ ] **Dateien:** `sensor.py` (Energy Consumption Sensoren)
- [ ] **Komplexität:** Mittel

### 3. Architektur-Erweiterung: automations.py
- [ ] **Status:** Pending
- [ ] **Beschreibung:** Erweitere automations.py mit generalisierten Reset-Signalen
- [ ] **Neue Signale:**
  ```python
  SIGNAL_RESET_DAILY_CYCLING = "lambda_heat_pumps_reset_daily_cycling"
  SIGNAL_RESET_DAILY_ENERGY = "lambda_heat_pumps_reset_daily_energy" 
  SIGNAL_RESET_DAILY_GENERAL = "lambda_heat_pumps_reset_daily_general"
  SIGNAL_RESET_2H_CYCLING = "lambda_heat_pumps_reset_2h_cycling"
  SIGNAL_RESET_2H_ENERGY = "lambda_heat_pumps_reset_2h_energy"
  SIGNAL_RESET_4H_CYCLING = "lambda_heat_pumps_reset_4h_cycling"
  SIGNAL_RESET_4H_ENERGY = "lambda_heat_pumps_reset_4h_energy"
  ```
- [ ] **Dateien:** `automations.py`
- [ ] **Komplexität:** Mittel

### 4. Funktions-Implementierung: Wiederverwendbare Handler
- [ ] **Status:** Pending
- [ ] **Beschreibung:** Implementiere wiederverwendbare Funktionen für Reset-Handling
- [ ] **Neue Funktionen:**
  ```python
  def register_sensor_reset_handler(hass, sensor_type, entry_id, reset_callback):
      """Registriert einen Sensor für automatische Resets."""
      
  def create_reset_signal(sensor_type, period):
      """Erstellt ein standardisiertes Reset-Signal."""
      
  def setup_generalized_automations(hass, entry_id):
      """Setzt generalisierte Automations für alle Sensor-Typen auf."""
      
  def get_sensor_reset_signal(sensor_type, period):
      """Holt das korrekte Reset-Signal für einen Sensor-Typ."""
  ```
- [ ] **Dateien:** `automations.py`, `utils.py`
- [ ] **Komplexität:** Hoch

### 5. Plugin-Architektur: Zukünftige Sensor-Typen
- [ ] **Status:** Pending
- [ ] **Beschreibung:** Schaffe Plugin-Architektur für zukünftige Sensor-Typen
- [ ] **Features:**
  - Automatische Registrierung neuer Sensor-Typen
  - Konfigurierbare Reset-Zeiten
  - Erweiterbare Reset-Logik
- [ ] **Dateien:** `automations.py`, neue `plugin_system.py`
- [ ] **Komplexität:** Hoch

### 6. Migration: Energy Sensoren
- [ ] **Status:** Pending
- [ ] **Beschreibung:** Migriere Energy Consumption Sensoren von individuellen Signalen zu zentralen Reset-Signalen
- [ ] **Änderungen:**
  - Entferne individuelle Signal-Registrierung
  - Verwende generalisierte Reset-Handler
  - Teste Reset-Funktionalität
- [ ] **Dateien:** `sensor.py` (LambdaEnergyConsumptionSensor)
- [ ] **Komplexität:** Mittel

## Technische Details

### Signal-System Architektur

```python
# Zentrale Signale (bestehend)
SIGNAL_RESET_DAILY = "lambda_heat_pumps_reset_daily"
SIGNAL_RESET_2H = "lambda_heat_pumps_reset_2h" 
SIGNAL_RESET_4H = "lambda_heat_pumps_reset_4h"

# Erweiterte Signale (neu)
SIGNAL_RESET_DAILY_CYCLING = "lambda_heat_pumps_reset_daily_cycling"
SIGNAL_RESET_DAILY_ENERGY = "lambda_heat_pumps_reset_daily_energy"
SIGNAL_RESET_DAILY_GENERAL = "lambda_heat_pumps_reset_daily_general"
```

### Sensor-Registrierung

```python
# Beispiel für Energy Consumption Sensoren
register_sensor_reset_handler(
    hass=hass,
    sensor_type="energy",
    entry_id=entry_id,
    reset_callback=sensor._handle_reset
)
```

### Reset-Automation

```python
def reset_daily_sensors(now: datetime) -> None:
    """Reset daily sensors at midnight."""
    # Sende Signale an alle registrierten Sensor-Typen
    async_dispatcher_send(hass, SIGNAL_RESET_DAILY_CYCLING, entry_id)
    async_dispatcher_send(hass, SIGNAL_RESET_DAILY_ENERGY, entry_id)
    async_dispatcher_send(hass, SIGNAL_RESET_DAILY_GENERAL, entry_id)
```

## Vorteile der Lösung

1. **Wiederverwendbar:** Neue Sensor-Typen können einfach hinzugefügt werden
2. **Zentralisiert:** Alle Resets laufen über ein einheitliches System
3. **Erweiterbar:** Plugin-Architektur für zukünftige Features
4. **Konsistent:** Einheitliches Verhalten für alle Sensoren
5. **Wartbar:** Ein Ort für alle Reset-Logik
6. **Rückwärtskompatibel:** Bestehende Cycling-Sensoren funktionieren weiter

## Implementierungsreihenfolge

1. **Phase 1:** Erweitere `automations.py` mit neuen Signalen
2. **Phase 2:** Implementiere generalisierte Handler-Funktionen
3. **Phase 3:** Migriere Energy Consumption Sensoren
4. **Phase 4:** Teste und validiere das System
5. **Phase 5:** Implementiere Plugin-Architektur (optional)

## Test-Plan

- [ ] Energy Consumption Sensoren werden um Mitternacht zurückgesetzt
- [ ] Cycling Sensoren funktionieren weiterhin korrekt
- [ ] Neue Sensor-Typen können einfach hinzugefügt werden
- [ ] Reset-Signale werden korrekt gesendet und empfangen
- [ ] Keine Regressionen im bestehenden System

## Notizen

- Das bestehende Cycling-System soll **nicht** geändert werden
- Energy Sensoren sollen **nahtlos** in das bestehende System integriert werden
- Die Lösung soll **zukunftssicher** und **erweiterbar** sein
- **Performance** und **Zuverlässigkeit** haben höchste Priorität

---

**Nächste Schritte:** Beginne mit Phase 1 - Erweitere `automations.py` mit neuen Signalen
