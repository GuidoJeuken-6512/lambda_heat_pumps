# Reset-Attribute Vereinfachung

## Problem: Redundante Attribute

**Aktuell haben wir 3 redundante Attribute pro Sensor:**
```python
"heating_cycling_daily": {
    "period": "daily",                    # ❌ Redundant
    "reset_interval": "daily",            # ✅ Reicht aus
    "reset_signal": "lambda_heat_pumps_reset_daily",  # ❌ Redundant
}
```

## Lösung: Nur `reset_interval` verwenden

### **1. `period` ist redundant**
- `period` = `reset_interval` (immer identisch)
- Kann eliminiert werden

### **2. `reset_signal` ist redundant**
- Wird bereits generisch erstellt: `f"lambda_heat_pumps_reset_{period}"`
- Kann aus `reset_interval` abgeleitet werden

### **3. Vereinfachte Struktur:**
```python
"heating_cycling_daily": {
    "operating_state": "heating",
    "reset_interval": "daily",  # ✅ Einzige benötigte Angabe
    "description": "Tägliche Cycling-Zähler für Heizen",
}
```

## Implementierung

### **Schritt 1: `period` entfernen**
- Alle `"period": "daily"` Einträge löschen
- Alle `"period": "2h"` Einträge löschen  
- Alle `"period": "4h"` Einträge löschen

### **Schritt 2: `reset_signal` entfernen**
- Alle `"reset_signal": "lambda_heat_pumps_reset_*"` Einträge löschen

### **Schritt 3: Code anpassen**
- `get_reset_signal_for_period(reset_interval)` verwenden
- `period` durch `reset_interval` ersetzen

## Vorteile

1. ✅ **Weniger Redundanz** - Nur noch 1 statt 3 Attribute
2. ✅ **Einfachere Wartung** - Weniger zu pflegende Daten
3. ✅ **Konsistenz** - Ein zentraler Wert für Reset-Intervall
4. ✅ **Weniger Fehler** - Keine Inkonsistenzen zwischen period/reset_interval
5. ✅ **Bessere Lesbarkeit** - Klarere Sensor-Definitionen

## Beispiel nach Vereinfachung

**Vorher:**
```python
"heating_cycling_daily": {
    "operating_state": "heating",
    "period": "daily",
    "reset_interval": "daily", 
    "reset_signal": "lambda_heat_pumps_reset_daily",
    "description": "Tägliche Cycling-Zähler für Heizen",
}
```

**Nachher:**
```python
"heating_cycling_daily": {
    "operating_state": "heating",
    "reset_interval": "daily",
    "description": "Tägliche Cycling-Zähler für Heizen",
}
```

**Signal wird generiert:**
```python
signal = get_reset_signal_for_period("daily")  # → "lambda_heat_pumps_reset_daily"
```

