# Issue #22: Falsche Werte für int32-Entitäten (Endianness-Problem)

## Übersicht

Dieses Dokument analysiert das in [GitHub Issue #22](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/22#issue-3378132513) beschriebene Problem mit falschen Werten für int32-Entitäten in der Lambda Wärmepumpen-Integration.

## Problembeschreibung

### Benutzer-Bericht
- **Benutzer:** @otriesch
- **Problem:** Falsche Werte für Entitäten mit dem Datentyp int32
- **Hardware:** Zewotherm (Lambda) Wärmepumpe mit HW: V0.0.1, SW: V0.0.8-3K Build Apr 3 2025
- **System:** Home Assistant auf Raspberry Pi 4
- **Integration Version:** 1.2.2
- **Home Assistant Core:** 2025.8.3

### Symptome
- Energie-Werte werden in der Lambda-Software korrekt angezeigt
- In Home Assistant werden falsche Werte dargestellt
- Problem tritt nur bei int32-Entitäten auf

## Technische Analyse

### Root Cause: Endianness-Problem

Das Problem liegt in der **Byte-Reihenfolge** bei der Interpretation von 32-Bit-Werten aus zwei 16-Bit-Modbus-Registern.

### Betroffene Code-Stellen

Die Integration liest **zwei aufeinanderfolgende 16-Bit Register** und kombiniert sie zu einem **32-Bit Wert**:

**Aktuelle Implementierung (Big-Endian):**
```python
# 6 Stellen in coordinator.py:
value = (result.registers[0] << 16) | result.registers[1]
```

**Benötigte Korrektur (Little-Endian):**
```python
value = (result.registers[1] << 16) | result.registers[0]
```

### Betroffene Zeilen in coordinator.py

1. **Zeile 360-362** (Batch-Read): `value = (result.registers[i] << 16) | result.registers[i + 1]`
2. **Zeile 408** (Single-Read): `value = (result.registers[0] << 16) | result.registers[1]`
3. **Zeile 994** (Boiler-Sensoren): `value = (result.registers[0] << 16) | result.registers[1]`
4. **Zeile 1053** (Buffer-Sensoren): `value = (result.registers[0] << 16) | result.registers[1]`
5. **Zeile 1112** (Solar-Sensoren): `value = (result.registers[0] << 16) | result.registers[1]`
6. **Zeile 1171** (Heating Circuit-Sensoren): `value = (result.registers[0] << 16) | result.registers[1]`

### Betroffene Sensoren

Basierend auf der `const.py` sind das **Energie-Sensoren** mit `data_type: "int32"`:

1. **`compressor_power_consumption_accumulated`** - Kompressor-Stromverbrauch (Wh)
2. **`compressor_thermal_energy_output_accumulated`** - Thermische Energie-Ausgabe (Wh)
3. **Solar-Energie-Sensoren** - Solar-Energie (kWh)

## Annahme: Firmware-Änderung bei Lambda

### Wahrscheinliche Ursache

**Lambda hat wahrscheinlich das Endianness-Verhalten ab einer bestimmten Firmware-Version geändert:**

- **Ältere Firmware-Versionen:** Verwendeten Big-Endian für int32-Werte
- **Neuere Firmware-Versionen (ab V0.0.8-3K):** Verwenden Little-Endian für int32-Werte

### Warum tritt das Problem nicht bei allen Installationen auf?

1. **Verschiedene Firmware-Versionen:**
   - **Benutzer:** SW: V0.0.8-3K Build Apr 3 2025 (sehr neue Version)
   - **Andere Installationen:** Wahrscheinlich ältere Firmware-Versionen

2. **Firmware-Versionen in der Integration:**
   ```python
   FIRMWARE_VERSION = {
       "V0.0.8-3K": 6,  # Current firmware - most common
       "V0.0.7-3K": 5,
       "V0.0.6-3K": 4,
       "V0.0.5-3K": 3,
       "V0.0.4-3K": 2,
       "V0.0.3-3K": 1,
   }
   ```

3. **Mögliche Szenarien:**
   - **V0.0.7-3K und älter:** Big-Endian (funktioniert mit aktueller Integration)
   - **V0.0.8-3K und neuer:** Little-Endian (Problem tritt auf)

## Technische Details

### Modbus-Register-Struktur

**16-Bit Modbus-Register werden zu 32-Bit Werten kombiniert:**

```python
# Für int32-Sensoren wird count=2 gesetzt
count = 2 if sensor_info.get("data_type") == "int32" else 1

# Dann werden 2 Register gelesen und kombiniert
if count == 2:
    value = (result.registers[0] << 16) | result.registers[1]
    if sensor_info.get("data_type") == "int32":
        value = to_signed_32bit(value)
```

### Warum 32-Bit für Energie-Werte?

**Energie-Werte werden über lange Zeiträume akkumuliert:**
- **16-Bit:** Maximal 65.535 Wh (65,5 kWh)
- **32-Bit:** Maximal 4.294.967.295 Wh (4,3 GWh)

Da Wärmepumpen über Jahre laufen und Energie akkumulieren, sind **32-Bit Werte notwendig**.

## Empfohlene Lösung

### Zwischenlösung: Konfigurierbare Endianness-Behandlung

**Hintergrund:** Es ist unklar, ob die 32-Bit-Register-Behandlung tatsächlich an der Firmware der Lambda-Wärmepumpe hängt. Daher wird eine **einfache, konfigurierbare Lösung** empfohlen, die es Benutzern ermöglicht, die Byte-Reihenfolge manuell einzustellen.

#### 1. Konfigurationsoption in lambda_wp_config.yaml

```yaml
# lambda_wp_config.yaml
modbus:
  # Endianness für 32-Bit-Register (int32-Sensoren)
  # "big" = Big-Endian (Standard, ältere Firmware-Versionen)
  # "little" = Little-Endian (neuere Firmware ab V0.0.8-3K)
  int32_byte_order: "big"
```

#### 2. Implementierung in utils.py

```python
async def get_int32_byte_order(hass: HomeAssistant) -> str:
    """
    Bestimmt die Byte-Reihenfolge für int32-Register aus der Konfiguration.
    
    Args:
        hass: Home Assistant Instanz
    
    Returns:
        str: "big" oder "little"
    """
    try:
        # Lade Konfiguration
        config = await load_lambda_config(hass)
        modbus_config = config.get("modbus", {})
        
        # Hole explizite Einstellung
        byte_order = modbus_config.get("int32_byte_order", "big")
        
        # Validiere Wert
        if byte_order not in ["big", "little"]:
            _LOGGER.warning("Ungültige int32_byte_order: %s, verwende 'big'", byte_order)
            return "big"
            
        return byte_order
            
    except Exception as e:
        _LOGGER.warning("Fehler beim Laden der Endianness-Konfiguration: %s", e)
        return "big"  # Sicherer Fallback


def combine_int32_registers(registers: list, byte_order: str = "big") -> int:
    """
    Kombiniert zwei 16-Bit-Register zu einem 32-Bit-Wert.
    
    Args:
        registers: Liste mit 2 Register-Werten
        byte_order: "big" oder "little"
    
    Returns:
        int: 32-Bit-Wert
    """
    if len(registers) < 2:
        raise ValueError("Mindestens 2 Register erforderlich für int32")
    
    if byte_order == "little":
        return (registers[1] << 16) | registers[0]
    else:  # big-endian (Standard)
        return (registers[0] << 16) | registers[1]
```

#### 3. Integration in coordinator.py

```python
# In der __init__ Methode des Coordinators:
self._int32_byte_order = "big"  # Standard-Wert

# Neue Methode:
async def _determine_int32_byte_order(self):
    """Bestimmt die Byte-Reihenfolge für int32-Register."""
    try:
        self._int32_byte_order = await get_int32_byte_order(self.hass)
        _LOGGER.info("Int32 Byte-Order konfiguriert: %s", self._int32_byte_order)
    except Exception as e:
        _LOGGER.warning("Fehler bei Byte-Order-Bestimmung: %s", e)
        self._int32_byte_order = "big"

# Ersetze alle 6 betroffenen Stellen:
# Alt: value = (result.registers[0] << 16) | result.registers[1]
# Neu: value = combine_int32_registers(result.registers, self._int32_byte_order)
```

#### 4. Template-Update in const.py

```python
LAMBDA_WP_CONFIG_TEMPLATE = """# Lambda WP configuration
# ...

# Modbus-Konfiguration
modbus:
  # Endianness für 32-Bit-Register (int32-Sensoren)
  # "big" = Big-Endian (Standard, ältere Firmware-Versionen)
  # "little" = Little-Endian (neuere Firmware ab V0.0.8-3K)
  int32_byte_order: "big"

# ...
"""
```

### Vorteile der Zwischenlösung

✅ **Einfach** - nur zwei Optionen: "big" oder "little"  
✅ **Klar** - Benutzer muss bewusst wählen  
✅ **Rückwärtskompatibel** - Standard ist "big" (aktuelles Verhalten)  
✅ **Zentral** - eine Funktion für alle 6 betroffenen Stellen  
✅ **Sicher** - Fallback auf Big-Endian bei Fehlern  
✅ **Debug-freundlich** - Logging der verwendeten Byte-Order  

### Benutzer-Anleitung

**Für Benutzer mit Problem (falsche int32-Werte):**
```yaml
modbus:
  int32_byte_order: "little"
```

**Für bestehende Benutzer (keine Änderung nötig):**
```yaml
modbus:
  int32_byte_order: "big"  # oder gar nicht setzen (Standard)
```

### Langfristige Lösung (später)

Sobald mehr Daten über die tatsächliche Ursache des Problems vorliegen, kann eine **automatische Erkennung** implementiert werden:

```python
def get_byte_order_for_firmware(firmware_version: str) -> str:
    """
    Bestimmt die Byte-Reihenfolge basierend auf der Firmware-Version
    """
    # Neuere Firmware-Versionen verwenden Little-Endian
    if firmware_version in ["V0.0.8-3K", "V0.0.7-3K"]:
        return "little"
    else:
        return "big"  # Ältere Versionen verwenden Big-Endian
```

## Implementierungsplan

### Phase 1: Zwischenlösung (Empfohlen)
1. **Konfigurierbare Endianness-Behandlung implementieren**
   - `int32_byte_order` Option in `lambda_wp_config.yaml`
   - `get_int32_byte_order()` Funktion in `utils.py`
   - `combine_int32_registers()` Hilfsfunktion
2. **Alle 6 betroffenen Stellen in coordinator.py ersetzen**
   - Batch-Read (Zeile 360-362)
   - Single-Read (Zeile 408)
   - Boiler-Sensoren (Zeile 994)
   - Buffer-Sensoren (Zeile 1053)
   - Solar-Sensoren (Zeile 1112)
   - Heating Circuit-Sensoren (Zeile 1171)
3. **Template in const.py erweitern**
4. **Debug-Logging für verwendete Byte-Order**

### Phase 2: Langfristige Lösung (später)
1. **Automatische Erkennung basierend auf Firmware-Version**
2. **Test-Reads zur Validierung der Byte-Order**
3. **Erweiterte Fehlerbehandlung bei inkonsistenten Werten**

### Phase 3: Erweiterte Robustheit
1. **Automatische Erkennung durch Test-Reads**
2. **Validierung der gelesenen Werte**
3. **Fehlerbehandlung bei inkonsistenten Werten**

## Testing

### Test-Szenarien
1. **Verschiedene Firmware-Versionen testen**
2. **Big-Endian vs. Little-Endian Verhalten validieren**
3. **Energie-Werte mit bekannten Referenzwerten vergleichen**
4. **Backward-Compatibility mit älteren Installationen sicherstellen**

### Validierung
- **Lambda-Software vs. Home Assistant Werte vergleichen**
- **Energie-Akkumulation über Zeit testen**
- **Verschiedene Hardware-Varianten testen**

## Fazit

Das Problem tritt auf, weil **Lambda wahrscheinlich das Endianness-Verhalten ab Firmware V0.0.8-3K geändert hat**. Die Lösung sollte eine **firmware-basierte oder konfigurierbare Endianness-Behandlung** sein, die automatisch die richtige Byte-Reihenfolge basierend auf der erkannten Firmware-Version wählt.

Dieses Issue unterstreicht die Wichtigkeit einer **flexiblen und robusten Modbus-Implementierung**, die mit verschiedenen Hardware- und Firmware-Varianten umgehen kann.

## Referenzen

- [GitHub Issue #22](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/22#issue-3378132513)
- [Robustheits-Verbesserungen Dokumentation](ROBUSTNESS_IMPROVEMENTS.md)
- Modbus-Standard: Endianness bei 32-Bit Werten
