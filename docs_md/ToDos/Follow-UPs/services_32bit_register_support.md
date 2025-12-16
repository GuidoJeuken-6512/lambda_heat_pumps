# Services 32-Bit Register Support

## Problem
Die Services `read_modbus_register` und `write_modbus_register` können derzeit **nicht** mit 32-Bit-Registern umgehen. Dies führt zu Fehlern beim Lesen/Schreiben von 32-Bit-Registern über die Home Assistant Developer Tools.

## Fehlermeldung im Log
```
ExceptionResponse(dev_id=1, function_code=131, exception_code=2)
```
**Modbus Exception Code 2** (Illegal Data Address) - tritt auf, wenn versucht wird, ein 32-Bit-Register mit nur einem 16-Bit-Read/Write zu bearbeiten.

## Identifizierte Probleme

### 1. Read Service (`_handle_read_modbus_register`)
- **Problem**: Liest nur 1 Register (16-Bit) statt 2 Register (32-Bit)
- **Code**: `count=1` in `async_read_holding_registers()`
- **Ergebnis**: Nur 16-Bit-Wert wird zurückgegeben

### 2. Write Service (`_handle_write_modbus_register`)
- **Problem**: Schreibt nur 1 Register (16-Bit) statt 2 Register (32-Bit)
- **Code**: `[value]` - nur ein Wert wird geschrieben
- **Ergebnis**: 32-Bit-Werte werden nicht korrekt geschrieben

### 3. Service Schema-Beschränkungen
- **Problem**: Wert-Bereich nur für 16-Bit-Werte (-32768 bis 65535)
- **Code**: `vol.Range(min=-32768, max=65535)` in `WRITE_MODBUS_REGISTER_SCHEMA`
- **Ergebnis**: 32-Bit-Werte werden abgelehnt

### 4. Fehlende Funktionalität
- **Keine Register-Typ-Erkennung**: Services wissen nicht, ob Register 16-Bit oder 32-Bit ist
- **Keine Endianness-Behandlung**: Keine Berücksichtigung von Big/Little-Endian für 32-Bit-Werte
- **Keine Datentyp-Erkennung**: Keine Unterscheidung zwischen INT16, UINT16, INT32, UINT32

## Betroffene 32-Bit-Register

Basierend auf `const.py` sind diese Register **32-Bit**:

1. **`compressor_power_consumption_accumulated`**
   - Adresse: 20
   - Datentyp: INT32
   - Einheit: Wh
   - Beschreibung: Kompressor-Stromverbrauch akkumuliert

2. **`compressor_thermal_energy_output_accumulated`**
   - Adresse: 22
   - Datentyp: INT32
   - Einheit: Wh
   - Beschreibung: Thermische Energie-Ausgabe akkumuliert

3. **Solar-Energie-Register**
   - Adresse: 904
   - Datentyp: INT32
   - Einheit: kWh
   - Beschreibung: Solar-Energie akkumuliert

## Lösungsansatz

### 1. Service Schema erweitern
```yaml
# Erweiterte Service-Parameter
register_address: int
value: int  # Erweitert für 32-Bit-Werte
data_type: str  # Optional: "int16", "uint16", "int32", "uint32"
byte_order: str  # Optional: "big", "little"
```

### 2. Register-Typ automatisch erkennen
- Laden der Register-Definitionen aus `const.py`
- Automatische Erkennung von 16-Bit vs 32-Bit-Registern
- Dynamische Anpassung der Register-Anzahl (count=1 oder count=2)

### 3. Endianness-Konfiguration berücksichtigen
- Laden der Endianness-Konfiguration aus `lambda_wp_config.yaml`
- Verwendung der bestehenden `get_int32_byte_order()` Funktion
- Korrekte Byte-Reihenfolge für 32-Bit-Werte

### 4. Intelligente Wert-Verarbeitung
- **16-Bit-Register**: Direkte Verarbeitung
- **32-Bit-Register**: Kombination von 2 Registern mit korrekter Endianness
- **Schreiben**: Aufteilen von 32-Bit-Werten in 2 Register

### 5. Erweiterte Fehlerbehandlung
- Validierung der Register-Adressen
- Prüfung auf gültige Datentypen
- Informative Fehlermeldungen bei ungültigen Operationen

## Implementierungsdetails

### Read Service Erweiterung
```python
async def _handle_read_modbus_register(hass: HomeAssistant, call: ServiceCall) -> dict:
    register_address = call.data.get("register_address")
    
    # Register-Typ erkennen
    register_info = get_register_info(register_address)
    if not register_info:
        return {"error": f"Unknown register address: {register_address}"}
    
    # Register-Anzahl bestimmen
    count = 2 if register_info["data_type"] in ["int32", "uint32"] else 1
    
    # Register lesen
    result = await async_read_holding_registers(
        coordinator.client,
        register_address,
        count,
    )
    
    # Wert verarbeiten
    if count == 2:
        # 32-Bit-Wert kombinieren
        byte_order = await get_int32_byte_order(hass)
        value = combine_int32_registers(result.registers, byte_order)
    else:
        # 16-Bit-Wert direkt verwenden
        value = result.registers[0]
    
    return {"value": value, "data_type": register_info["data_type"]}
```

### Write Service Erweiterung
```python
async def _handle_write_modbus_register(hass: HomeAssistant, call: ServiceCall) -> None:
    register_address = call.data.get("register_address")
    value = call.data.get("value")
    
    # Register-Typ erkennen
    register_info = get_register_info(register_address)
    if not register_info:
        _LOGGER.error(f"Unknown register address: {register_address}")
        return
    
    # Werte für Schreiben vorbereiten
    if register_info["data_type"] in ["int32", "uint32"]:
        # 32-Bit-Wert in 2 Register aufteilen
        byte_order = await get_int32_byte_order(hass)
        registers = split_int32_to_registers(value, byte_order)
    else:
        # 16-Bit-Wert direkt verwenden
        registers = [value]
    
    # Register schreiben
    result = await async_write_registers(
        coordinator.client,
        register_address,
        registers,
        entry_data.get("slave_id", 1),
    )
```

## Priorität
**Hoch** - Services sind wichtige Debugging-Tools und sollten alle Register-Typen unterstützen.

## Abhängigkeiten
- Bestehende Endianness-Unterstützung in `modbus_utils.py`
- Register-Definitionen in `const.py`
- Konfiguration in `lambda_wp_config.yaml`

## Tests erforderlich
- [ ] Test mit 16-Bit-Registern (sollte weiterhin funktionieren)
- [ ] Test mit 32-Bit-Registern (INT32, UINT32)
- [ ] Test mit verschiedenen Endianness-Einstellungen
- [ ] Test mit ungültigen Register-Adressen
- [ ] Test mit ungültigen Werten

## Status
**TODO** - Wartet auf Implementierung
