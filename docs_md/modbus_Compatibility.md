# Modbus Compatibility in Lambda Heat Pumps Integration

## Goal

The integration supports different versions of the Python library `pymodbus` (from 1.x to 3.x) and remains compatible with different Home Assistant and system environments.

## Problem Statement

The `pymodbus` API has changed across versions:
- **pymodbus < 2.0**: no explicit slave parameter
- **pymodbus 2.x**: `unit` parameter
- **pymodbus >= 3.0**: `slave` parameter

Without adaptation, these differences lead to errors like:
```
TypeError: read_holding_registers() takes 2 positional arguments but 4 were given
```

## Solution: Central Wrapper

The integration uses a central wrapper approach in `modbus_utils.py`:

### Universal Wrapper Function

```python
def modbus_call(client, method, *args, **kwargs):
    """Universal Modbus compatibility wrapper."""
    slave_id = kwargs.pop('slave_id', 1)  # Default slave_id = 1
    
    if not hasattr(client, method):
        raise AttributeError(f"Modbus client missing method: {method}")
    
    try:
        # New API (pymodbus >= 3.0) - slave=
        result = getattr(client, method)(*args, **kwargs, slave=slave_id)
        return result
    except TypeError:
        try:
            # Old API (pymodbus 2.x) - unit=
            result = getattr(client, method)(*args, **kwargs, unit=slave_id)
            return result
        except TypeError:
            # Very old API (pymodbus < 2.0) - no parameter
            result = getattr(client, method)(*args, **kwargs)
            return result
    except Exception as e:
        _LOGGER.error("Modbus error in %s: %s", method, str(e))
        raise
```

### Specific Wrapper Functions

```python
def read_holding_registers(client, address, count, slave_id):
    return modbus_call(client, "read_holding_registers", address, count, slave_id=slave_id)

def write_registers(client, address, values, slave_id):
    return modbus_call(client, "write_registers", address, values, slave_id=slave_id)
```

## Usage in Code

### Before (incompatible)
```python
result = await self.hass.async_add_executor_job(
    self.client.read_holding_registers,
    address,
    count,
    slave_id,  # ❌ API version dependent
)
```

### After (compatible)
```python
result = await self.hass.async_add_executor_job(
    read_holding_registers,
    self.client,
    address,
    count,
    slave_id,  # ✅ Always works
)
```

## Benefits

1. **Centralized Management**: All Modbus calls in one place
2. **Automatic Compatibility**: Works with all pymodbus versions
3. **Error Handling**: Consistent error logging and handling
4. **Maintainability**: Easy to update and maintain
5. **Reusability**: Can be used in other integrations

## Supported pymodbus Versions

- **pymodbus 1.x**: Legacy support
- **pymodbus 2.x**: Full support
- **pymodbus 3.x**: Full support (recommended)

## Error Handling

The wrapper provides detailed error logging:
- Method existence check
- API version detection
- Detailed error messages
- Graceful fallback between API versions

---

# Modbus-Kompatibilität in der Lambda Heat Pumps Integration

## Ziel

Die Integration unterstützt verschiedene Versionen der Python-Bibliothek `pymodbus` (ab 1.x bis 3.x) und bleibt damit kompatibel mit unterschiedlichen Home Assistant- und Systemumgebungen.

## Problemstellung

Die API von `pymodbus` hat sich über die Versionen hinweg geändert:
- **pymodbus < 2.0**: kein expliziter Slave-Parameter
- **pymodbus 2.x**: `unit`-Parameter
- **pymodbus >= 3.0**: `slave`-Parameter

Ohne Anpassung führen diese Unterschiede zu Fehlern wie:
```
TypeError: read_holding_registers() takes 2 positional arguments but 4 were given
```

## Lösung: Zentrale Wrapper

Die Integration verwendet einen zentralen Wrapper-Ansatz in `modbus_utils.py`:

### Universeller Wrapper

```python
def modbus_call(client, method, *args, **kwargs):
    """Universal Modbus compatibility wrapper."""
    slave_id = kwargs.pop('slave_id', 1)  # Default slave_id = 1
    
    if not hasattr(client, method):
        raise AttributeError(f"Modbus client missing method: {method}")
    
    try:
        # Neue API (pymodbus >= 3.0) - slave=
        result = getattr(client, method)(*args, **kwargs, slave=slave_id)
        return result
    except TypeError:
        try:
            # Alte API (pymodbus 2.x) - unit=
            result = getattr(client, method)(*args, **kwargs, unit=slave_id)
            return result
        except TypeError:
            # Sehr alte API (pymodbus < 2.0) - kein Parameter
            result = getattr(client, method)(*args, **kwargs)
            return result
    except Exception as e:
        _LOGGER.error("Modbus error in %s: %s", method, str(e))
        raise
```

### Spezifische Wrapper-Funktionen

```python
def read_holding_registers(client, address, count, slave_id):
    return modbus_call(client, "read_holding_registers", address, count, slave_id=slave_id)

def write_registers(client, address, values, slave_id):
    return modbus_call(client, "write_registers", address, values, slave_id=slave_id)
```

## Verwendung im Code

### Vorher (inkompatibel)
```python
result = await self.hass.async_add_executor_job(
    self.client.read_holding_registers,
    address,
    count,
    slave_id,  # ❌ API-Version abhängig
)
```

### Nachher (kompatibel)
```python
result = await self.hass.async_add_executor_job(
    read_holding_registers,
    self.client,
    address,
    count,
    slave_id,  # ✅ Funktioniert immer
)
```

## Vorteile

1. **Zentrale Verwaltung**: Alle Modbus-Aufrufe an einem Ort
2. **Automatische Kompatibilität**: Funktioniert mit allen pymodbus-Versionen
3. **Fehlerbehandlung**: Konsistente Fehlerprotokollierung
4. **Wartbarkeit**: Einfach zu aktualisieren und zu warten
5. **Wiederverwendbarkeit**: Kann in anderen Integrations verwendet werden

## Unterstützte pymodbus-Versionen

- **pymodbus 1.x**: Legacy-Unterstützung
- **pymodbus 2.x**: Vollständige Unterstützung
- **pymodbus 3.x**: Vollständige Unterstützung (empfohlen)

## Fehlerbehandlung

Der Wrapper bietet detaillierte Fehlerprotokollierung:
- Methoden-Existenz-Prüfung
- API-Versions-Erkennung
- Detaillierte Fehlermeldungen
- Graceful Fallback zwischen API-Versionen 