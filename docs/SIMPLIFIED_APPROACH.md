# Vereinfachter Ansatz - Zurück zu Phase 1

**Problem:** Phase 2 ist überkompliziert mit zwei Signalen  
**Lösung:** Verwende Phase 1 Ansatz + nur die nützlichen Teile aus Phase 2

## Was behalten wir?

### ✅ **Aus Phase 1 (perfekt):**
```python
# Ein zentrales Signal für alle Sensoren
SIGNAL_RESET_DAILY = "lambda_heat_pumps_reset_daily"
SIGNAL_RESET_2H = "lambda_heat_pumps_reset_2h"
SIGNAL_RESET_4H = "lambda_heat_pumps_reset_4h"
```

### ✅ **Aus Phase 2 (nützlich):**
- **Factory-Funktionen** für Signal-Generierung
- **Registry-Klasse** für zentrale Verwaltung
- **Convenience-Funktionen** für einfache API

## Was entfernen wir?

### ❌ **Überkompliziert:**
- Spezifische Signale pro Sensor-Typ
- Komplexe Plugin-Architektur
- Unnötige Abstraktionsebenen

## Vereinfachte Architektur

### **Signal-System:**
```python
# Nur diese Signale (wie Phase 1)
SIGNAL_RESET_DAILY = "lambda_heat_pumps_reset_daily"
SIGNAL_RESET_2H = "lambda_heat_pumps_reset_2h"
SIGNAL_RESET_4H = "lambda_heat_pumps_reset_4h"

# Factory-Funktion (aus Phase 2)
def get_reset_signal_for_period(period: str) -> str:
    return f"lambda_heat_pumps_reset_{period}"
```

### **Registry (vereinfacht):**
```python
class SimpleSensorResetRegistry:
    def register(self, entry_id: str, period: str, callback):
        # Registriert Sensor für zentrale Signale
        
    def send_reset(self, period: str, entry_id: str = None):
        # Sendet zentrale Signale an alle Sensoren
```

## Vorteile der vereinfachten Lösung

1. **Einfach** - Nur ein Signal pro Periode
2. **Effizient** - Weniger Komplexität
3. **Wartbar** - Klare Struktur
4. **Erweiterbar** - Registry für zukünftige Features

## Implementierung

Soll ich die Architektur vereinfachen und die überkomplizierten Teile entfernen?
