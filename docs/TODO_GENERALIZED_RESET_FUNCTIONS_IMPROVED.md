# TODO: Generalisierte Reset-Funktionen für alle Sensor-Typen (Verbessert)

**Status:** 🟡 Pending  
**Priorität:** Hoch  
**Erstellt:** 2025-01-14  
**Letzte Überarbeitung:** 2025-01-14  
**Zugewiesen:** AI Assistant  

## Problem (Präzisiert)

**Hauptproblem:** Energy Consumption Sensoren werden nicht um Mitternacht zurückgesetzt.

**Ursache:** Individuelle Signale statt zentraler Automation.

**Auswirkung:** Inkonsistente Reset-Zeiten zwischen Sensor-Typen.

## Lösungsansatz (Vereinfacht)

**Prinzip:** Erweitere das bestehende System minimal, statt komplett neu zu bauen.

**Fokus:** Sofortige Lösung für Energy Sensoren + zukunftssichere Architektur.

## Implementierungsplan (Verbessert)

### **Phase 1: Sofortige Lösung (1-2 Tage)**
**Ziel:** Energy Sensoren funktionieren sofort

#### 1.1 Energy Sensoren Reset-Fix
- [ ] **Status:** Pending
- [ ] **Beschreibung:** Verwende bestehende `SIGNAL_RESET_DAILY` für Energy Sensoren
- [ ] **Dateien:** `sensor.py` (LambdaEnergyConsumptionSensor)
- [ ] **Änderung:** Ersetze individuelle Signale durch `SIGNAL_RESET_DAILY`
- [ ] **Komplexität:** Niedrig
- [ ] **Zeit:** 2-3 Stunden

#### 1.2 Test Energy Sensoren Reset
- [ ] **Status:** Pending
- [ ] **Beschreibung:** Teste dass Energy Sensoren um Mitternacht zurückgesetzt werden
- [ ] **Dateien:** `test_energy_consumption.py`
- [ ] **Komplexität:** Niedrig
- [ ] **Zeit:** 1 Stunde

### **Phase 2: Architektur-Verbesserung (3-5 Tage)**
**Ziel:** Generalisierte, wiederverwendbare Reset-Funktionen

#### 2.1 Reset-Signal Factory
- [ ] **Status:** Pending
- [ ] **Beschreibung:** Erstelle Factory-Funktion für Reset-Signale
- [ ] **Neue Funktion:**
  ```python
  def create_reset_signal(sensor_type: str, period: str) -> str:
      """Erstellt standardisiertes Reset-Signal.
      
      Args:
          sensor_type: 'cycling', 'energy', 'general'
          period: 'daily', '2h', '4h'
          
      Returns:
          Signal-Name: 'lambda_heat_pumps_reset_{period}_{sensor_type}'
      """
  ```
- [ ] **Dateien:** `utils.py`
- [ ] **Komplexität:** Niedrig
- [ ] **Zeit:** 1 Stunde

#### 2.2 Sensor Reset Registry
- [ ] **Status:** Pending
- [ ] **Beschreibung:** Zentrales Registry für Sensor-Reset-Handler
- [ ] **Neue Funktionen:**
  ```python
  class SensorResetRegistry:
      """Zentrales Registry für alle Sensor-Reset-Handler."""
      
      def register(self, sensor_type: str, entry_id: str, callback: Callable):
          """Registriert einen Sensor für automatische Resets."""
          
      def get_signal(self, sensor_type: str, period: str) -> str:
          """Holt das korrekte Reset-Signal."""
          
      def send_reset(self, sensor_type: str, period: str, entry_id: str):
          """Sendet Reset-Signal an alle registrierten Sensoren."""
  ```
- [ ] **Dateien:** `utils.py`
- [ ] **Komplexität:** Mittel
- [ ] **Zeit:** 3-4 Stunden

#### 2.3 Erweiterte Reset-Automation
- [ ] **Status:** Pending
- [ ] **Beschreibung:** Erweitere `automations.py` mit generalisierten Reset-Funktionen
- [ ] **Neue Signale:**
  ```python
  # Erweiterte Signale (zusätzlich zu bestehenden)
  SIGNAL_RESET_DAILY_CYCLING = "lambda_heat_pumps_reset_daily_cycling"
  SIGNAL_RESET_DAILY_ENERGY = "lambda_heat_pumps_reset_daily_energy"
  SIGNAL_RESET_2H_CYCLING = "lambda_heat_pumps_reset_2h_cycling"
  SIGNAL_RESET_2H_ENERGY = "lambda_heat_pumps_reset_2h_energy"
  SIGNAL_RESET_4H_CYCLING = "lambda_heat_pumps_reset_4h_cycling"
  SIGNAL_RESET_4H_ENERGY = "lambda_heat_pumps_reset_4h_energy"
  ```
- [ ] **Dateien:** `automations.py`
- [ ] **Komplexität:** Mittel
- [ ] **Zeit:** 2-3 Stunden

#### 2.4 Migration bestehender Sensoren
- [ ] **Status:** Pending
- [ ] **Beschreibung:** Migriere alle Sensoren zu generalisiertem System
- [ ] **Cycling Sensoren:** Verwende neue Signale
- [ ] **Energy Sensoren:** Verwende neue Signale
- [ ] **Dateien:** `sensor.py` (alle Sensor-Klassen)
- [ ] **Komplexität:** Mittel
- [ ] **Zeit:** 4-5 Stunden

### **Phase 3: Plugin-System (Optional, 5-7 Tage)**
**Ziel:** Vollständig erweiterbares Plugin-System

#### 3.1 Sensor-Type Plugin Interface
- [ ] **Status:** Pending
- [ ] **Beschreibung:** Interface für neue Sensor-Typen
- [ ] **Neue Klassen:**
  ```python
  class SensorTypePlugin(ABC):
      """Base class für Sensor-Type Plugins."""
      
      @abstractmethod
      def get_reset_periods(self) -> List[str]:
          """Gibt unterstützte Reset-Perioden zurück."""
          
      @abstractmethod
      def create_reset_callback(self, sensor) -> Callable:
          """Erstellt Reset-Callback für Sensor."""
  ```
- [ ] **Dateien:** `plugin_system.py`
- [ ] **Komplexität:** Hoch
- [ ] **Zeit:** 6-8 Stunden

#### 3.2 Plugin Registry
- [ ] **Status:** Pending
- [ ] **Beschreibung:** Automatische Plugin-Registrierung
- [ ] **Dateien:** `plugin_system.py`
- [ ] **Komplexität:** Hoch
- [ ] **Zeit:** 4-5 Stunden

## Technische Details (Vereinfacht)

### Signal-System Architektur

```python
# Bestehende Signale (bleiben unverändert)
SIGNAL_RESET_DAILY = "lambda_heat_pumps_reset_daily"
SIGNAL_RESET_2H = "lambda_heat_pumps_reset_2h" 
SIGNAL_RESET_4H = "lambda_heat_pumps_reset_4h"

# Erweiterte Signale (neu, zusätzlich)
SIGNAL_RESET_DAILY_CYCLING = "lambda_heat_pumps_reset_daily_cycling"
SIGNAL_RESET_DAILY_ENERGY = "lambda_heat_pumps_reset_daily_energy"
SIGNAL_RESET_2H_CYCLING = "lambda_heat_pumps_reset_2h_cycling"
SIGNAL_RESET_2H_ENERGY = "lambda_heat_pumps_reset_2h_energy"
```

### Sensor-Registrierung (Vereinfacht)

```python
# Beispiel für Energy Consumption Sensoren
registry = SensorResetRegistry()
registry.register(
    sensor_type="energy",
    entry_id=entry_id,
    callback=sensor._handle_reset
)
```

### Reset-Automation (Erweitert)

```python
def reset_daily_sensors(now: datetime) -> None:
    """Reset daily sensors at midnight."""
    # Bestehende Funktionalität (bleibt unverändert)
    async_dispatcher_send(hass, SIGNAL_RESET_DAILY, entry_id)
    
    # Neue Funktionalität (zusätzlich)
    registry.send_reset("cycling", "daily", entry_id)
    registry.send_reset("energy", "daily", entry_id)
```

## Vorteile der verbesserten Lösung

1. **Sofortige Lösung:** Energy Sensoren funktionieren sofort
2. **Minimale Änderungen:** Bestehendes System bleibt unverändert
3. **Schrittweise Migration:** Jede Phase ist funktionsfähig
4. **Wiederverwendbar:** Neue Sensor-Typen einfach hinzufügbar
5. **Rückwärtskompatibel:** Bestehende Sensoren funktionieren weiter
6. **Testbar:** Jede Phase kann einzeln getestet werden

## Implementierungsrichtlinien

### 1. Vor jeder Implementierung
- [ ] **Analysiere** die Anforderung auf Wiederholungspotential
- [ ] **Frage nach** wenn unsicher über den Scope
- [ ] **Entwerfe** generalisierte Lösung
- [ ] **Dokumentiere** den Entwurf

### 2. Während der Implementierung
- [ ] **Implementiere** wiederverwendbare Funktionen
- [ ] **Teste** die Funktionalität
- [ ] **Dokumentiere** die Verwendung
- [ ] **Refactore** bei Bedarf

### 3. Nach der Implementierung
- [ ] **Validiere** die Wiederverwendbarkeit
- [ ] **Dokumentiere** für zukünftige Verwendung
- [ ] **Aktualisiere** bestehende Verwendungen
- [ ] **Teile** mit dem Team

## Test-Plan (Detailliert)

### Phase 1 Tests
- [ ] Energy Sensoren werden um Mitternacht zurückgesetzt
- [ ] Bestehende Cycling Sensoren funktionieren weiterhin
- [ ] Keine Regressionen im bestehenden System

### Phase 2 Tests
- [ ] Alle Sensoren verwenden generalisierte Signale
- [ ] Reset-Registry funktioniert korrekt
- [ ] Neue Signale werden korrekt gesendet
- [ ] Migration verläuft ohne Datenverlust

### Phase 3 Tests (Optional)
- [ ] Plugin-System funktioniert
- [ ] Neue Sensor-Typen können hinzugefügt werden
- [ ] Automatische Registrierung funktioniert

## Risiken und Mitigation

### Risiko 1: Regressionen im bestehenden System
**Mitigation:** Phase 1 verwendet bestehende Signale, Phase 2 ist optional

### Risiko 2: Komplexität der Plugin-Architektur
**Mitigation:** Phase 3 ist optional, kann später implementiert werden

### Risiko 3: Performance-Impact
**Mitigation:** Registry verwendet effiziente Datenstrukturen

## Notizen

- **Phase 1 ist kritisch** - muss sofort implementiert werden
- **Phase 2 ist wichtig** - für zukunftssichere Architektur
- **Phase 3 ist optional** - kann bei Bedarf implementiert werden
- **Bestehendes System** bleibt unverändert bis Phase 2
- **Performance** und **Zuverlässigkeit** haben höchste Priorität

---

**Nächste Schritte:** Beginne mit Phase 1.1 - Energy Sensoren Reset-Fix

