# Const.py Verbesserungen

## Übersicht
Die `const.py` Datei ist mit **1817 Zeilen** sehr umfangreich und enthält viele Redundanzen und Verbesserungsmöglichkeiten. Diese Dokumentation beschreibt die identifizierten Probleme und Lösungsansätze.

## Identifizierte Probleme

### 1. **OPERATING_STATE_MAP Redundanz** ⚠️
**Problem:** Separate Map für Operating States, obwohl diese Information bereits in den Sensor-Templates vorhanden ist.

**Aktuell:**
```python
OPERATING_STATE_MAP = {
    0: "STBY", 1: "CH", 2: "DHW", 3: "CC", 4: "CIRCULATE",
    5: "DEFROST", 6: "OFF", 7: "FROST", 8: "STBY-FROST",
    # ... weitere Einträge
}
```

**Besser:**
```python
# In Sensor-Templates integrieren
"heating_energy_daily": {
    "name": "Heating Energy Daily",
    "operating_state": "heating",
    "mode_value": 1,  # CH
    "reset_interval": "daily",
    "reset_signal": "lambda_heat_pumps_reset_daily"
}
```

### 2. **Duplizierte Konfiguration** ⚠️
**Problem:** Mehrfache Definitionen von Listen und Konstanten.

**Aktuell:**
```python
ENERGY_CONSUMPTION_MODES = ["heating", "hot_water", "cooling", "defrost", "stby"]
ENERGY_CONSUMPTION_PERIODS = ["total", "daily"]
```

**Besser:**
```python
# Aus Templates ableiten
def get_energy_modes():
    return list(set(template.get("operating_state") for template in ENERGY_CONSUMPTION_SENSOR_TEMPLATES.values()))

def get_energy_periods():
    return list(set(template.get("period") for template in ENERGY_CONSUMPTION_SENSOR_TEMPLATES.values()))
```

### 3. **Sensor-Templates Fragmentierung** ⚠️
**Problem:** Separate Templates für ähnliche Sensoren mit viel Duplikation.

**Aktuell:**
```python
HP_SENSOR_TEMPLATES = {...}
BOIL_SENSOR_TEMPLATES = {...}
BUFF_SENSOR_TEMPLATES = {...}
SOL_SENSOR_TEMPLATES = {...}
HC_SENSOR_TEMPLATES = {...}
```

**Besser:**
```python
# Einheitliche Template-Struktur
UNIFIED_SENSOR_TEMPLATES = {
    "hp_error_state": {
        "device_type": "hp",
        "relative_address": 0,
        "name": "Error State",
        # ... gemeinsame Attribute
    }
}
```

### 4. **Magic Numbers** ⚠️
**Problem:** Hardcoded Werte ohne Kontext.

**Aktuell:**
```python
DEFAULT_UPDATE_INTERVAL = 30
LAMBDA_MODBUS_TIMEOUT = 60
LAMBDA_MAX_RETRIES = 3
LAMBDA_RETRY_DELAY = 5
```

**Besser:**
```python
# Konfigurierbare Konstanten
MODBUS_CONFIG = {
    "update_interval": 30,
    "timeout": 60,
    "max_retries": 3,
    "retry_delay": 5
}
```

### 5. **Firmware-Versionen Komplexität** ⚠️
**Problem:** Komplexe Firmware-Map mit numerischen Werten.

**Aktuell:**
```python
FIRMWARE_VERSION = {
    "V0.0.9-3K": 7,
    "V0.0.8-3K": 6,
    "V0.0.7-3K": 5,
    # ...
}
```

**Besser:**
```python
# Einfache Liste mit Versionsnummern
SUPPORTED_FIRMWARES = ["V0.0.9-3K", "V0.0.8-3K", "V0.0.7-3K"]
```

### 6. **Konfigurationstemplate Monolith** ⚠️
**Problem:** Riesiges Template (200+ Zeilen) schwer wartbar.

**Aktuell:**
```python
LAMBDA_WP_CONFIG_TEMPLATE = """# Lambda WP configuration..."""
```

**Besser:**
```python
# Modulares Template
CONFIG_SECTIONS = {
    "disabled_registers": "...",
    "sensor_overrides": "...",
    "cycling_offsets": "...",
    "energy_consumption": "..."
}
```

## Implementierungsplan

### Phase 1: Kritische Verbesserungen ✅
1. **OPERATING_STATE_MAP auflösen** - In Sensor-Templates integrieren
2. **Duplizierte Konfiguration eliminieren** - Aus Templates ableiten

### Phase 2: Strukturelle Verbesserungen
3. **Sensor-Templates konsolidieren** - Einheitliche Struktur
4. **Magic Numbers eliminieren** - Konfigurierbare Konstanten

### Phase 3: Wartbarkeitsverbesserungen
5. **Firmware-Versionen vereinfachen** - Einfache Liste
6. **Konfigurationstemplate modularisieren** - Aufgeteilte Sektionen

## Erwartete Verbesserungen

### ✅ **Code-Reduktion**
- Von **1817 Zeilen** auf **1200-1300 Zeilen** (-30%)
- Weniger Duplikation und Redundanz

### ✅ **Wartbarkeit**
- Einheitliche Template-Struktur
- Konfiguration an einem Ort
- Weniger Code-Sprünge

### ✅ **Erweiterbarkeit**
- Einfache Hinzufügung neuer Sensoren
- Modulare Konfiguration
- Bessere Testbarkeit

### ✅ **Lesbarkeit**
- Klarere Struktur
- Weniger Magic Numbers
- Bessere Dokumentation

## Nächste Schritte

1. **Phase 1 implementieren** (Punkte 1 & 2)
2. **Tests aktualisieren** für neue Struktur
3. **Dokumentation anpassen** für neue Konfiguration
4. **Phase 2 & 3** schrittweise umsetzen

## Risiken und Mitigation

### ⚠️ **Breaking Changes**
- **Risiko:** Bestehender Code bricht
- **Mitigation:** Schrittweise Migration mit Kompatibilitätslayer

### ⚠️ **Test-Updates**
- **Risiko:** Tests müssen angepasst werden
- **Mitigation:** Umfassende Test-Suite vor Änderungen

### ⚠️ **Konfiguration**
- **Risiko:** Bestehende Konfigurationen funktionieren nicht
- **Mitigation:** Migrationstools und Dokumentation
