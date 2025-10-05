# Programming Principles - Lambda Heat Pumps Integration

**Erstellt:** 2025-01-14  
**Version:** 1.0  
**Zweck:** Dokumentation der Programmierprinzipien und -richtlinien für die Lambda Heat Pumps Integration

---

## Grundprinzipien

### 1. Generalisierung bei mehrfacher Verwendung

**Prinzip:** Immer generalisierte, wiederverwendbare Funktionen erstellen, wenn absehbar ist, dass Funktionen mehrfach eingesetzt werden können.

**Vorgehen:** Bei Unsicherheit lieber nachfragen als eine spezifische Lösung zu implementieren.

**Beispiele:**
- **Reset-Funktionen:** Statt individuelle Signale → generalisierte Reset-Handler
- **Sensor-Erstellung:** Statt Copy-Paste → wiederverwendbare Factory-Funktionen
- **Name-Generierung:** Statt hardcoded → konfigurierbare Name-Generatoren

**Vorteile:**
- ✅ **Code-Wiederverwendung** - Weniger Duplikation
- ✅ **Wartbarkeit** - Ein Ort für Änderungen
- ✅ **Konsistenz** - Einheitliches Verhalten
- ✅ **Erweiterbarkeit** - Einfache Anpassungen
- ✅ **Testbarkeit** - Weniger Code zu testen

### 2. DRY (Don't Repeat Yourself)

**Prinzip:** Vermeide Code-Duplikation durch Wiederverwendung bestehender Funktionen.

**Anwendung:**
- Erstelle gemeinsame Utility-Funktionen
- Verwende Template-Systeme für ähnliche Strukturen
- Zentralisiere Konfigurationen

### 3. Single Responsibility Principle

**Prinzip:** Jede Funktion/Klasse sollte nur eine Verantwortlichkeit haben.

**Anwendung:**
- Trenne Sensor-Erstellung von Sensor-Logik
- Separate Reset-Handler von Sensor-Entitäten
- Isoliere Modbus-Kommunikation von Business-Logik

### 4. Open/Closed Principle

**Prinzip:** Code sollte offen für Erweiterungen, aber geschlossen für Modifikationen sein.

**Anwendung:**
- Plugin-Architektur für neue Sensor-Typen
- Konfigurierbare Templates
- Erweiterbare Reset-Systeme

---

## Architektur-Prinzipien

### 1. Zentrale Verwaltung

**Prinzip:** Ähnliche Funktionalitäten zentral verwalten.

**Beispiele:**
- Alle Reset-Signale in `automations.py`
- Sensor-Templates in `const.py`
- Utility-Funktionen in `utils.py`

### 2. Konfiguration über Code

**Prinzip:** Verwende Konfigurationsdateien statt hardcoded Werte.

**Anwendung:**
- Sensor-Templates als Konfiguration
- Modbus-Register als Templates
- Zeitintervalle als Konstanten

### 3. Fehlerbehandlung

**Prinzip:** Robuste Fehlerbehandlung mit aussagekräftigen Logs.

**Anwendung:**
- Try-Catch-Blöcke mit spezifischen Exceptions
- Debug-Logs für Troubleshooting
- Graceful Degradation bei Fehlern

---

## Code-Qualität

### 1. Lesbarkeit

**Prinzip:** Code sollte selbsterklärend sein.

**Anwendung:**
- Aussagekräftige Variablennamen
- Kommentare für komplexe Logik
- Konsistente Namenskonventionen

### 2. Dokumentation

**Prinzip:** Dokumentiere öffentliche APIs und komplexe Logik.

**Anwendung:**
- Docstrings für alle Funktionen
- README-Dateien für Module
- Inline-Kommentare für Business-Logik

### 3. Testing

**Prinzip:** Teste kritische Funktionalitäten.

**Anwendung:**
- Unit-Tests für Utility-Funktionen
- Integration-Tests für Sensor-Erstellung
- Manuelle Tests für Reset-Funktionalitäten

---

## Home Assistant Integration

### 1. Entity Lifecycle

**Prinzip:** Respektiere Home Assistant Entity Lifecycle.

**Anwendung:**
- `async_added_to_hass()` für Initialisierung
- `async_will_remove_from_hass()` für Cleanup
- `RestoreEntity` für Persistierung

### 2. Signal-System

**Prinzip:** Verwende Home Assistant Dispatcher für Kommunikation.

**Anwendung:**
- Zentrale Signale für Reset-Events
- Async-Dispatcher für Entity-Kommunikation
- Proper Cleanup von Signal-Handlern

### 3. Performance

**Prinzip:** Optimiere für Home Assistant Performance.

**Anwendung:**
- Minimale Polling-Intervalle
- Effiziente State-Updates
- Lazy Loading von Daten

---

## Implementierungsrichtlinien

### 1. Vor der Implementierung

1. **Analysiere** die Anforderung auf Wiederholungspotential
2. **Frage nach** wenn unsicher über den Scope
3. **Entwerfe** generalisierte Lösung
4. **Dokumentiere** den Entwurf

### 2. Während der Implementierung

1. **Implementiere** wiederverwendbare Funktionen
2. **Teste** die Funktionalität
3. **Dokumentiere** die Verwendung
4. **Refactore** bei Bedarf

### 3. Nach der Implementierung

1. **Validiere** die Wiederverwendbarkeit
2. **Dokumentiere** für zukünftige Verwendung
3. **Aktualisiere** bestehende Verwendungen
4. **Teile** mit dem Team

---

## Beispiele

### ✅ Gute Implementierung

```python
# Generalisierte Reset-Handler
def register_sensor_reset_handler(hass, sensor_type, entry_id, reset_callback):
    """Registriert einen Sensor für automatische Resets."""
    signal = create_reset_signal(sensor_type, "daily")
    async_dispatcher_connect(hass, signal, reset_callback)

def create_reset_signal(sensor_type, period):
    """Erstellt ein standardisiertes Reset-Signal."""
    return f"lambda_heat_pumps_reset_{period}_{sensor_type}"
```

### ❌ Schlechte Implementierung

```python
# Spezifische Implementierung für jeden Sensor-Typ
def register_energy_sensor_reset(hass, entry_id, callback):
    signal = f"lambda_energy_reset_{entry_id}_daily"
    async_dispatcher_connect(hass, signal, callback)

def register_cycling_sensor_reset(hass, entry_id, callback):
    signal = f"lambda_cycling_reset_{entry_id}_daily"
    async_dispatcher_connect(hass, signal, callback)
```

---

## Checkliste

Vor jeder Implementierung prüfen:

- [ ] Wird diese Funktion mehrfach verwendet?
- [ ] Kann ich sie generalisieren?
- [ ] Ist sie wiederverwendbar?
- [ ] Folgt sie den Architektur-Prinzipien?
- [ ] Ist sie gut dokumentiert?
- [ ] Ist sie testbar?

---

**Letzte Aktualisierung:** 2025-01-14  
**Nächste Überprüfung:** Bei größeren Architektur-Änderungen
