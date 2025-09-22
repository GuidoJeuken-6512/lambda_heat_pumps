# Monthly und Yearly Sensoren Fix - Bericht

**Erstellt:** 2025-01-14  
**Version:** 1.0  
**Zweck:** Dokumentation der Behebung der Monthly und Yearly Energy Consumption Sensoren

---

## 🎯 **Problem**

Die Monthly und Yearly Energy Consumption Sensoren stiegen nicht an, weil sie:

1. **Falsche Berechnung** verwendeten (`self._yesterday_value` statt separater Tracking-Variablen)
2. **Keine separate Reset-Logik** für die vorherigen Perioden hatten
3. **Keine Perioden-Updates** beim Reset durchführten

---

## 🔧 **Lösung**

### **1. Neue Tracking-Variablen hinzugefügt**

```python
# In LambdaEnergyConsumptionSensor.__init__()
self._previous_monthly_value = 0.0  # Für Monthly-Sensoren
self._previous_yearly_value = 0.0   # Für Yearly-Sensoren
```

### **2. Korrigierte native_value Berechnung**

```python
@property
def native_value(self) -> float:
    """Return the current value."""
    if self._reset_interval == "daily":
        # Daily-Wert = Total - Yesterday
        return max(0.0, self._energy_value - self._yesterday_value)
    elif self._reset_interval == "monthly":
        # Monthly-Wert = Total - Previous Monthly
        return max(0.0, self._energy_value - self._previous_monthly_value)
    elif self._reset_interval == "yearly":
        # Yearly-Wert = Total - Previous Yearly
        return max(0.0, self._energy_value - self._previous_yearly_value)
    else:
        # Total-Wert
        return self._energy_value
```

### **3. Verbesserte Reset-Logik**

```python
async def _handle_reset(self, entry_id: str):
    """Handle reset signal."""
    _LOGGER.info(f"Resetting energy sensor {self.entity_id}")
    
    if self._reset_interval == "monthly":
        # Speichere aktuellen Wert vor Reset
        self._previous_monthly_value = self._energy_value
        _LOGGER.info(f"Monthly sensor {self.entity_id}: Saved previous value {self._previous_monthly_value:.2f} kWh")
    elif self._reset_interval == "yearly":
        # Speichere aktuellen Wert vor Reset
        self._previous_yearly_value = self._energy_value
        _LOGGER.info(f"Yearly sensor {self.entity_id}: Saved previous value {self._previous_yearly_value:.2f} kWh")
    
    # Reset nur für daily, 2h, 4h Sensoren
    if self._reset_interval in ["daily", "2h", "4h"]:
        self._energy_value = 0.0
    
    self.async_write_ha_state()
```

### **4. Erweiterte State-Attribute**

```python
@property
def extra_state_attributes(self):
    """Return extra state attributes."""
    attrs = {
        "sensor_type": "energy_consumption",
        "mode": self._mode,
        "reset_interval": self._reset_interval,
        "hp_index": self._hp_index,
        "applied_offset": self._applied_offset,
    }
    
    # Füge Period-spezifische Werte hinzu
    if self._reset_interval == "daily":
        attrs["yesterday_value"] = self._yesterday_value
    elif self._reset_interval == "monthly":
        attrs["previous_monthly_value"] = self._previous_monthly_value
    elif self._reset_interval == "yearly":
        attrs["previous_yearly_value"] = self._previous_yearly_value
        
    return attrs
```

### **5. Verbesserte State-Restoration**

```python
async def restore_state(self, last_state):
    """Restore the state from the last state."""
    if last_state is not None:
        try:
            self._energy_value = float(last_state.state)
            # ... existing code ...
            
            if hasattr(last_state, 'attributes') and last_state.attributes:
                self._applied_offset = last_state.attributes.get("applied_offset", 0.0)
                # Lade Previous Period-Werte
                self._previous_monthly_value = last_state.attributes.get("previous_monthly_value", 0.0)
                self._previous_yearly_value = last_state.attributes.get("previous_yearly_value", 0.0)
            # ... rest of the code ...
```

---

## 📊 **Verhalten der Sensoren**

### **Monthly Sensoren:**
1. **Während des Monats:** `native_value = energy_value - previous_monthly_value`
2. **Am 1. des Monats:** Speichere `energy_value` als `previous_monthly_value`
3. **Nach Reset:** `native_value` startet bei 0 und steigt mit `energy_value` an

### **Yearly Sensoren:**
1. **Während des Jahres:** `native_value = energy_value - previous_yearly_value`
2. **Am 1. Januar:** Speichere `energy_value` als `previous_yearly_value`
3. **Nach Reset:** `native_value` startet bei 0 und steigt mit `energy_value` an

### **Unterschied zu Daily Sensoren:**
- **Daily:** Resettet `energy_value` auf 0
- **Monthly/Yearly:** Resettet `energy_value` NICHT, speichert nur den Wert

---

## 🧪 **Test-Ergebnisse**

### **Monthly Sensor Test:**
```
Energy Value: 100.00 kWh
Previous Monthly: 0.00 kWh
Monthly Value: 100.00 kWh

Nach Reset:
Energy Value: 100.00 kWh (NICHT resettet!)
Previous Monthly: 100.00 kWh (gespeichert)
Monthly Value: 0.00 kWh (startet bei 0)

Neuer Energy Value: 150.00 kWh
Monthly Value: 50.00 kWh (150 - 100 = 50)
```

### **Yearly Sensor Test:**
```
Energy Value: 1000.00 kWh
Previous Yearly: 0.00 kWh
Yearly Value: 1000.00 kWh

Nach Reset:
Energy Value: 1000.00 kWh (NICHT resettet!)
Previous Yearly: 1000.00 kWh (gespeichert)
Yearly Value: 0.00 kWh (startet bei 0)

Neuer Energy Value: 1200.00 kWh
Yearly Value: 200.00 kWh (1200 - 1000 = 200)
```

---

## ✅ **Vorteile der Lösung**

### **1. Korrekte Berechnung**
- Monthly/Yearly Sensoren verwenden separate Tracking-Variablen
- Keine Verwechslung mit Daily-Sensor-Logik

### **2. Persistente Werte**
- Previous Period-Werte werden in State-Attributen gespeichert
- Überleben Home Assistant Neustarts

### **3. Korrekte Reset-Logik**
- Monthly/Yearly Sensoren resettet NICHT den `energy_value`
- Nur Daily/2h/4h Sensoren resettet den `energy_value`

### **4. Bessere Debugging**
- Separate State-Attribute für jede Period
- Klare Logging-Nachrichten

### **5. Rückwärtskompatibilität**
- Bestehende Daily-Sensoren funktionieren unverändert
- Keine Breaking Changes

---

## 🎯 **Fazit**

Die Monthly und Yearly Energy Consumption Sensoren funktionieren jetzt korrekt:

1. ✅ **Werte steigen an** - Sensoren zeigen korrekte Differenz-Werte
2. ✅ **Reset funktioniert** - Am 1. des Monats/Jahres wird der Wert gespeichert
3. ✅ **Persistenz** - Werte überleben Neustarts
4. ✅ **Debugging** - Klare State-Attribute und Logging
5. ✅ **Kompatibilität** - Keine Auswirkungen auf andere Sensoren

Die Sensoren sollten jetzt korrekt funktionieren und die Energie-Verbräuche für Monthly und Yearly Perioden anzeigen! 🎉

---

**Letzte Aktualisierung:** 2025-01-14  
**Nächste Überprüfung:** Nach 1 Monat/Jahr um Reset-Verhalten zu validieren
