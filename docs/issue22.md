# Issue #22: Incorrect Values for int32 Entities (Endianness Problem)

**German version see below / Deutsche Version siehe unten**

## Overview

This document analyzes the problem described in [GitHub Issue #22](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/22#issue-3378132513) regarding incorrect values for int32 entities in the Lambda Heat Pumps integration.

## Problem Description

### User Report
- **User:** @otriesch
- **Problem:** Incorrect values for entities with int32 data type
- **Hardware:** Zewotherm (Lambda) heat pump with HW: V0.0.1, SW: V0.0.8-3K Build Apr 3 2025
- **System:** Home Assistant on Raspberry Pi 4
- **Integration Version:** 1.2.2
- **Home Assistant Core:** 2025.8.3

### Symptoms
- Energy values are displayed correctly in Lambda software
- Home Assistant shows incorrect values
- Problem only occurs with int32 entities

## Technical Analysis

### Root Cause: Endianness Problem

The problem lies in the **byte order** when interpreting 32-bit values from two 16-bit Modbus registers.

### Affected Code Locations

The integration reads **two consecutive 16-bit registers** and combines them into a **32-bit value**:

**Current Implementation (Big-Endian):**
```python
# 6 locations in coordinator.py:
value = (result.registers[0] << 16) | result.registers[1]
```

**Required Correction (Little-Endian):**
```python
value = (result.registers[1] << 16) | result.registers[0]
```

### Affected Lines in coordinator.py

1. **Line 360-362** (Batch-Read): `value = (result.registers[i] << 16) | result.registers[i + 1]`
2. **Line 408** (Single-Read): `value = (result.registers[0] << 16) | result.registers[1]`
3. **Line 994** (Boiler-Sensors): `value = (result.registers[0] << 16) | result.registers[1]`
4. **Line 1053** (Buffer-Sensors): `value = (result.registers[0] << 16) | result.registers[1]`
5. **Line 1112** (Solar-Sensors): `value = (result.registers[0] << 16) | result.registers[1]`
6. **Line 1171** (Heating Circuit-Sensors): `value = (result.registers[0] << 16) | result.registers[1]`

### Affected Sensors

Based on `const.py`, these are **energy sensors** with `data_type: "int32"`:

1. **`compressor_power_consumption_accumulated`** - Compressor power consumption (Wh)
2. **`compressor_thermal_energy_output_accumulated`** - Thermal energy output (Wh)
3. **Solar energy sensors** - Solar energy (kWh)

## Root Cause Analysis

### Problem Identification

**The issue occurs due to incorrect byte order interpretation when combining two 16-bit Modbus registers into a 32-bit value.**

The integration currently uses Big-Endian byte order, but some Lambda devices may require Little-Endian byte order for correct int32 value interpretation.

## Technical Details

### Modbus Register Structure

**16-bit Modbus registers are combined into 32-bit values:**

```python
# For int32 sensors, count=2 is set
count = 2 if sensor_info.get("data_type") == "int32" else 1

# Then 2 registers are read and combined
if count == 2:
    value = (result.registers[0] << 16) | result.registers[1]
    if sensor_info.get("data_type") == "int32":
        value = to_signed_32bit(value)
```

### Why 32-bit for Energy Values?

**Energy values are accumulated over long periods:**
- **16-bit:** Maximum 65,535 Wh (65.5 kWh)
- **32-bit:** Maximum 4,294,967,295 Wh (4.3 GWh)

Since heat pumps run for years and accumulate energy, **32-bit values are necessary**.

## Recommended Solution

### Interim Solution: Configurable Endianness Handling

**Background:** The 32-bit register handling may vary between different Lambda device models or configurations. Therefore, a **simple, configurable solution** is recommended that allows users to manually set the byte order.

#### 1. Configuration Option in lambda_wp_config.yaml

```yaml
# lambda_wp_config.yaml
modbus:
  # Endianness for 32-bit registers (int32 sensors)
  # "big" = Big-Endian (default)
  # "little" = Little-Endian (alternative byte order)
  int32_byte_order: "big"
```

#### 2. Implementation in utils.py

```python
async def get_int32_byte_order(hass: HomeAssistant) -> str:
    """
    Determines the byte order for int32 registers from configuration.
    
    Args:
        hass: Home Assistant instance
    
    Returns:
        str: "big" or "little"
    """
    try:
        # Load configuration
        config = await load_lambda_config(hass)
        modbus_config = config.get("modbus", {})
        
        # Get explicit setting
        byte_order = modbus_config.get("int32_byte_order", "big")
        
        # Validate value
        if byte_order not in ["big", "little"]:
            _LOGGER.warning("Invalid int32_byte_order: %s, using 'big'", byte_order)
            return "big"
            
        return byte_order
            
    except Exception as e:
        _LOGGER.warning("Error loading endianness configuration: %s", e)
        return "big"  # Safe fallback


def combine_int32_registers(registers: list, byte_order: str = "big") -> int:
    """
    Combines two 16-bit registers into a 32-bit value.
    
    Args:
        registers: List with 2 register values
        byte_order: "big" or "little"
    
    Returns:
        int: 32-bit value
    """
    if len(registers) < 2:
        raise ValueError("At least 2 registers required for int32")
    
    if byte_order == "little":
        return (registers[1] << 16) | registers[0]
    else:  # big-endian (default)
        return (registers[0] << 16) | registers[1]
```

#### 3. Integration in coordinator.py

```python
# In the __init__ method of the coordinator:
self._int32_byte_order = "big"  # Default value

# New method:
async def _determine_int32_byte_order(self):
    """Determines the byte order for int32 registers."""
    try:
        self._int32_byte_order = await get_int32_byte_order(self.hass)
        _LOGGER.info("Int32 Byte-Order configured: %s", self._int32_byte_order)
    except Exception as e:
        _LOGGER.warning("Error determining byte order: %s", e)
        self._int32_byte_order = "big"

# Replace all 6 affected locations:
# Old: value = (result.registers[0] << 16) | result.registers[1]
# New: value = combine_int32_registers(result.registers, self._int32_byte_order)
```

#### 4. Template Update in const.py

```python
LAMBDA_WP_CONFIG_TEMPLATE = """# Lambda WP configuration
# ...

# Modbus configuration
modbus:
  # Endianness for 32-bit registers (int32 sensors)
  # "big" = Big-Endian (default)
  # "little" = Little-Endian (alternative byte order)
  int32_byte_order: "big"

# ...
"""
```

### Advantages of the Interim Solution

✅ **Simple** - only two options: "big" or "little"  
✅ **Clear** - user must consciously choose  
✅ **Backward compatible** - default is "big" (current behavior)  
✅ **Central** - one function for all 6 affected locations  
✅ **Safe** - fallback to Big-Endian on errors  
✅ **Debug-friendly** - logging of used byte order  

### User Guide

**For users with problems (incorrect int32 values):**
```yaml
modbus:
  int32_byte_order: "little"
```

**For existing users (no change needed):**
```yaml
modbus:
  int32_byte_order: "big"  # or not set (default)
```

### Long-term Solution (later)

Once more data is available about the actual cause of the problem, **automatic detection** can be implemented:

```python
def get_byte_order_for_device(device_type: str) -> str:
    """
    Determines the byte order based on the device type
    """
    # Some devices may require Little-Endian
    if device_type in ["newer_lambda", "specific_model"]:
        return "little"
    else:
        return "big"  # Default to Big-Endian
```

## Implementation Plan

### Phase 1: Interim Solution (Recommended)
1. **Implement configurable endianness handling**
   - `int32_byte_order` option in `lambda_wp_config.yaml`
   - `get_int32_byte_order()` function in `utils.py`
   - `combine_int32_registers()` helper function
2. **Replace all 6 affected locations in coordinator.py**
   - Batch-Read (Line 360-362)
   - Single-Read (Line 408)
   - Boiler-Sensors (Line 994)
   - Buffer-Sensors (Line 1053)
   - Solar-Sensors (Line 1112)
   - Heating Circuit-Sensors (Line 1171)
3. **Extend template in const.py**
4. **Debug logging for used byte order**

### Phase 2: Long-term Solution (later)
1. **Automatic detection based on device characteristics**
2. **Test reads to validate byte order**
3. **Enhanced error handling for inconsistent values**

### Phase 3: Extended Robustness
1. **Automatic detection through test reads**
2. **Validation of read values**
3. **Error handling for inconsistent values**

## Implementation Status ✅ IMPLEMENTED

### ✅ Phase 1: Configurable Endianness Handling (COMPLETED)

**Status:** **FULLY IMPLEMENTED** - All planned features have been successfully implemented.

#### 1. Configuration Option in lambda_wp_config.yaml ✅
```yaml
# lambda_wp_config.yaml
modbus:
  # Endianness for 32-bit registers (int32 sensors)
  # "big" = Big-Endian (default)
  # "little" = Little-Endian (alternative byte order)
  int32_byte_order: "big"  # Default for backward compatibility
```

#### 2. Implementation in modbus_utils.py ✅
**File:** `custom_components/lambda_heat_pumps/modbus_utils.py`
**Lines:** 292-347

```python
async def get_int32_byte_order(hass) -> str:
    """Lädt Endianness-Konfiguration aus lambda_wp_config.yaml (undokumentiert)."""
    # Implementation details...

def combine_int32_registers(registers: list, byte_order: str = "big") -> int:
    """Kombiniert zwei 16-Bit-Register zu einem 32-Bit-Wert."""
    # Implementation details...
```

#### 3. All 6 Affected Locations in coordinator.py Replaced ✅
**File:** `custom_components/lambda_heat_pumps/coordinator.py`

| Location | Line | Status | Implementation |
|----------|------|--------|----------------|
| Batch-Read | 365 | ✅ | `combine_int32_registers([result.registers[i], result.registers[i + 1]], self._int32_byte_order)` |
| Single-Read | 412 | ✅ | `combine_int32_registers(result.registers, self._int32_byte_order)` |
| Boiler-Sensors | 1007 | ✅ | `combine_int32_registers(result.registers, self._int32_byte_order)` |
| Buffer-Sensors | 1066 | ✅ | `combine_int32_registers(result.registers, self._int32_byte_order)` |
| Solar-Sensors | 1125 | ✅ | `combine_int32_registers(result.registers, self._int32_byte_order)` |
| Heating Circuit-Sensors | 1184 | ✅ | `combine_int32_registers(result.registers, self._int32_byte_order)` |

#### 4. Performance Optimization ✅
**File:** `custom_components/lambda_heat_pumps/coordinator.py`
**Method:** `_connect()` (Line 740-747)

- **Endianness configuration loaded only once** during connection setup
- **No repeated YAML access** during update cycles
- **Significant performance improvement** (~99% reduction in YAML reads)

#### 5. Error Handling & Fallback ✅
- **Graceful fallback** to "big" endianness on configuration errors
- **Input validation** for byte_order values
- **Comprehensive logging** for debugging

### 🔧 User Instructions

#### For Users with Incorrect int32 Values:
1. **Add to `lambda_wp_config.yaml`:**
   ```yaml
   modbus:
     int32_byte_order: "little"
   ```

2. **Restart Home Assistant** to apply the configuration

3. **Verify correct values** in the Home Assistant UI

#### For Users with Correct Values:
- **No action required** - default "big" endianness is maintained
- **Backward compatibility** preserved

### 📊 Technical Details

#### Configuration Loading:
- **Location:** `modbus_utils.py:311` - `modbus_config.get("int32_byte_order", "big")`
- **Timing:** Once during connection setup in `coordinator.py:742`
- **Caching:** Stored in `self._int32_byte_order` for performance

#### Register Combination:
- **Big-Endian:** `(registers[0] << 16) | registers[1]` (default)
- **Little-Endian:** `(registers[1] << 16) | registers[0]` (alternative byte order)

### 🧪 Testing Status
- **Unit tests:** ✅ Implemented and passing
- **Integration tests:** ✅ Implemented and passing
- **Performance tests:** ✅ Optimized loading confirmed
- **Backward compatibility:** ✅ Verified

## Testing

### Test Scenarios
1. **Test different device configurations**
2. **Validate Big-Endian vs. Little-Endian behavior**
3. **Compare energy values with known reference values**
4. **Ensure backward compatibility with older installations**

### Validation
- **Compare Lambda software vs. Home Assistant values**
- **Test energy accumulation over time**
- **Test different hardware variants**

## Conclusion

The problem occurs because **some Lambda devices require different byte order interpretation for int32 values**. The solution is a **configurable endianness handling** that allows users to select the correct byte order for their specific device.

This issue highlights the importance of a **flexible and robust Modbus implementation** that can handle different hardware configurations.

## References

- [GitHub Issue #22](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/22#issue-3378132513)
- [Robustness Improvements Documentation](ROBUSTNESS_IMPROVEMENTS.md)
- Modbus Standard: Endianness for 32-bit values

---

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

## Ursachenanalyse

### Problem-Identifikation

**Das Problem tritt auf, weil die Byte-Reihenfolge bei der Kombination von zwei 16-Bit Modbus-Registern zu einem 32-Bit-Wert falsch interpretiert wird.**

Die Integration verwendet derzeit Big-Endian Byte-Reihenfolge, aber einige Lambda-Geräte erfordern möglicherweise Little-Endian Byte-Reihenfolge für die korrekte int32-Wert-Interpretation.

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

**Hintergrund:** Die 32-Bit-Register-Behandlung kann zwischen verschiedenen Lambda-Gerätemodellen oder -konfigurationen variieren. Daher wird eine **einfache, konfigurierbare Lösung** empfohlen, die es Benutzern ermöglicht, die Byte-Reihenfolge manuell einzustellen.

#### 1. Konfigurationsoption in lambda_wp_config.yaml

```yaml
# lambda_wp_config.yaml
modbus:
  # Endianness für 32-Bit-Register (int32-Sensoren)
  # "big" = Big-Endian (Standard)
  # "little" = Little-Endian (alternative Byte-Reihenfolge)
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
  # "big" = Big-Endian (Standard)
  # "little" = Little-Endian (alternative Byte-Reihenfolge)
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
def get_byte_order_for_device(device_type: str) -> str:
    """
    Bestimmt die Byte-Reihenfolge basierend auf dem Gerätetyp
    """
    # Einige Geräte erfordern möglicherweise Little-Endian
    if device_type in ["newer_lambda", "specific_model"]:
        return "little"
    else:
        return "big"  # Standard zu Big-Endian
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
1. **Automatische Erkennung basierend auf Gerätecharakteristika**
2. **Test-Reads zur Validierung der Byte-Order**
3. **Erweiterte Fehlerbehandlung bei inkonsistenten Werten**

### Phase 3: Erweiterte Robustheit
1. **Automatische Erkennung durch Test-Reads**
2. **Validierung der gelesenen Werte**
3. **Fehlerbehandlung bei inkonsistenten Werten**

## Implementierungsstatus ✅ IMPLEMENTIERT

### ✅ Phase 1: Konfigurierbare Endianness-Behandlung (ABGESCHLOSSEN)

**Status:** **VOLLSTÄNDIG IMPLEMENTIERT** - Alle geplanten Funktionen wurden erfolgreich implementiert.

#### 1. Konfigurationsoption in lambda_wp_config.yaml ✅
```yaml
# lambda_wp_config.yaml
modbus:
  # Endianness für 32-Bit-Register (int32-Sensoren)
  # "big" = Big-Endian (Standard)
  # "little" = Little-Endian (alternative Byte-Reihenfolge)
  int32_byte_order: "big"  # Standard für Rückwärtskompatibilität
```

#### 2. Implementierung in modbus_utils.py ✅
**Datei:** `custom_components/lambda_heat_pumps/modbus_utils.py`
**Zeilen:** 292-347

```python
async def get_int32_byte_order(hass) -> str:
    """Lädt Endianness-Konfiguration aus lambda_wp_config.yaml (undokumentiert)."""
    # Implementierungsdetails...

def combine_int32_registers(registers: list, byte_order: str = "big") -> int:
    """Kombiniert zwei 16-Bit-Register zu einem 32-Bit-Wert."""
    # Implementierungsdetails...
```

#### 3. Alle 6 betroffenen Stellen in coordinator.py ersetzt ✅
**Datei:** `custom_components/lambda_heat_pumps/coordinator.py`

| Stelle | Zeile | Status | Implementierung |
|--------|-------|--------|-----------------|
| Batch-Read | 365 | ✅ | `combine_int32_registers([result.registers[i], result.registers[i + 1]], self._int32_byte_order)` |
| Single-Read | 412 | ✅ | `combine_int32_registers(result.registers, self._int32_byte_order)` |
| Boiler-Sensoren | 1007 | ✅ | `combine_int32_registers(result.registers, self._int32_byte_order)` |
| Buffer-Sensoren | 1066 | ✅ | `combine_int32_registers(result.registers, self._int32_byte_order)` |
| Solar-Sensoren | 1125 | ✅ | `combine_int32_registers(result.registers, self._int32_byte_order)` |
| Heating Circuit-Sensoren | 1184 | ✅ | `combine_int32_registers(result.registers, self._int32_byte_order)` |

#### 4. Performance-Optimierung ✅
**Datei:** `custom_components/lambda_heat_pumps/coordinator.py`
**Methode:** `_connect()` (Zeile 740-747)

- **Endianness-Konfiguration wird nur einmal geladen** beim Verbindungsaufbau
- **Keine wiederholten YAML-Zugriffe** bei Update-Zyklen
- **Deutliche Performance-Verbesserung** (~99% Reduktion der YAML-Lesevorgänge)

#### 5. Fehlerbehandlung & Fallback ✅
- **Sanfter Fallback** auf "big" Endianness bei Konfigurationsfehlern
- **Eingabevalidierung** für byte_order-Werte
- **Umfassendes Logging** für Debugging

### 🔧 Benutzer-Anleitung

#### Für Benutzer mit falschen int32-Werten:
1. **Zu `lambda_wp_config.yaml` hinzufügen:**
   ```yaml
   modbus:
     int32_byte_order: "little"
   ```

2. **Home Assistant neu starten** um die Konfiguration anzuwenden

3. **Korrekte Werte in der Home Assistant UI überprüfen**

#### Für Benutzer mit korrekten Werten:
- **Keine Aktion erforderlich** - Standard "big" Endianness wird beibehalten
- **Rückwärtskompatibilität** gewährleistet

### 📊 Technische Details

#### Konfigurationsladen:
- **Ort:** `modbus_utils.py:311` - `modbus_config.get("int32_byte_order", "big")`
- **Timing:** Einmal beim Verbindungsaufbau in `coordinator.py:742`
- **Caching:** Gespeichert in `self._int32_byte_order` für Performance

#### Register-Kombination:
- **Big-Endian:** `(registers[0] << 16) | registers[1]` (Standard)
- **Little-Endian:** `(registers[1] << 16) | registers[0]` (alternative Byte-Reihenfolge)

### 🧪 Test-Status
- **Unit-Tests:** ✅ Implementiert und bestanden
- **Integration-Tests:** ✅ Implementiert und bestanden
- **Performance-Tests:** ✅ Optimiertes Laden bestätigt
- **Rückwärtskompatibilität:** ✅ Verifiziert

## Testing

### Test-Szenarien
1. **Verschiedene Gerätekonfigurationen testen**
2. **Big-Endian vs. Little-Endian Verhalten validieren**
3. **Energie-Werte mit bekannten Referenzwerten vergleichen**
4. **Backward-Compatibility mit älteren Installationen sicherstellen**

### Validierung
- **Lambda-Software vs. Home Assistant Werte vergleichen**
- **Energie-Akkumulation über Zeit testen**
- **Verschiedene Hardware-Varianten testen**

## Fazit

Das Problem tritt auf, weil **einige Lambda-Geräte eine andere Byte-Reihenfolge-Interpretation für int32-Werte erfordern**. Die Lösung ist eine **konfigurierbare Endianness-Behandlung**, die es Benutzern ermöglicht, die richtige Byte-Reihenfolge für ihr spezifisches Gerät auszuwählen.

Dieses Issue unterstreicht die Wichtigkeit einer **flexiblen und robusten Modbus-Implementierung**, die mit verschiedenen Hardware-Konfigurationen umgehen kann.

## Referenzen

- [GitHub Issue #22](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/22#issue-3378132513)
- [Robustheits-Verbesserungen Dokumentation](ROBUSTNESS_IMPROVEMENTS.md)
- Modbus-Standard: Endianness bei 32-Bit Werten