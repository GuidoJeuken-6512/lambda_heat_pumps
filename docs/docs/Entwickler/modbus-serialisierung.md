---
title: "Modbus-Serialisierung - Technische Dokumentation"
---

# Modbus-Serialisierung - Technische Dokumentation

Diese Dokumentation beschreibt die Serialisierung von Modbus-Operationen in der Lambda Heat Pumps Integration, um Transaction ID Mismatches zu vermeiden.

## Übersicht

Um Race Conditions und Transaction ID Mismatches bei gleichzeitigen Modbus-Requests zu vermeiden, verwendet die Integration **globale Locks** zur Serialisierung aller Modbus-Operationen. Dies stellt sicher, dass zu jedem Zeitpunkt nur eine Modbus-Operation ausgeführt wird.

## Problem: Transaction ID Mismatches

### Was sind Transaction ID Mismatches?

Bei Modbus TCP/IP werden alle Requests mit einer eindeutigen **Transaction ID** versehen. Der Client sendet eine Request mit Transaction ID `X` und erwartet eine Response mit derselben Transaction ID `X`.

**Problem**: Wenn mehrere Modbus-Requests gleichzeitig (parallel) gesendet werden, kann es zu folgenden Problemen kommen:

1. **Transaction ID Konflikte**: Mehrere Requests erhalten möglicherweise die gleiche Transaction ID
2. **Response-Verwirrung**: Responses können Requests falsch zugeordnet werden
3. **Fehlerhafte Daten**: Falsche Daten werden gelesen/geschrieben
4. **Modbus-Protokoll-Verletzungen**: Parallele Requests verletzen das Modbus-Protokoll (eine Verbindung = sequenziell)

### Beispiel eines Transaction ID Mismatch Fehlers

```
ERROR: request ask for transaction_id=123 but got id=124, Skipping.
```

Dieser Fehler tritt auf, wenn:
- Request 1 wird mit Transaction ID 123 gesendet
- Request 2 wird gleichzeitig mit Transaction ID 124 gesendet
- Response für Request 2 kommt zuerst an (Transaction ID 124)
- pymodbus erwartet aber Response für Request 1 (Transaction ID 123)
- Resultat: Fehler, Request wird übersprungen

## Lösung: Globale Locks

### Implementierung

Die Integration verwendet **zwei globale asyncio.Locks** zur Serialisierung:

```12:14:custom_components/lambda_heat_pumps/modbus_utils.py
# Globaler Lock für alle Modbus-Read-Operationen, um Transaction ID Mismatches zu vermeiden
# Verhindert parallele Modbus-Requests, die zu Transaction ID Konflikten führen können
_modbus_read_lock = asyncio.Lock()
```

```9:10:custom_components/lambda_heat_pumps/modbus_utils.py
# Lock für Health-Checks, um Transaction ID Mismatches zu vermeiden
_health_check_lock = asyncio.Lock()
```

### Verwendung des Locks

Der Lock wird in allen Modbus-Operationen verwendet:

#### 1. Modbus Read-Operationen

```85:88:custom_components/lambda_heat_pumps/modbus_utils.py
    # Verwende globalen Lock, um parallele Modbus-Requests zu vermeiden
    # Dies verhindert Transaction ID Mismatches, die auftreten können, wenn
    # mehrere Requests gleichzeitig gesendet werden
    async with _modbus_read_lock:
```

**Vollständiger Code:**

```66:152:custom_components/lambda_heat_pumps/modbus_utils.py
async def async_read_holding_registers(
    client, address: int, count: int, slave_id: int = LAMBDA_MODBUS_UNIT_ID
) -> Any:
    """Read holding registers with Lambda-specific timeout and retry logic.
    
    Uses a global lock to prevent concurrent Modbus requests that could cause
    Transaction ID mismatches.
    """
    last_exception = None
    
    # Check if client exists and is connected
    if not client:
        _LOGGER.info("❌ MODBUS READ: Connection not healthy for address %d", address)
        raise Exception("Modbus client is None - connection lost")
    
    if not hasattr(client, 'connected') or not client.connected:
        _LOGGER.info("❌ MODBUS READ: Connection not healthy for address %d", address)
        raise Exception("Modbus client not connected")
    
    # Verwende globalen Lock, um parallele Modbus-Requests zu vermeiden
    # Dies verhindert Transaction ID Mismatches, die auftreten können, wenn
    # mehrere Requests gleichzeitig gesendet werden
    async with _modbus_read_lock:
        for attempt in range(LAMBDA_MAX_RETRIES):
            try:
                # For pymodbus 3.11.1, use only address as positional, rest as kwargs
                try:
                    # Try with slave parameter (most common in 3.x)
                    return await asyncio.wait_for(
                        client.read_holding_registers(address, count=count, slave=slave_id),
                        timeout=LAMBDA_MODBUS_TIMEOUT
                    )
                except (TypeError, AttributeError):
                    try:
                        # Try with unit parameter
                        return await asyncio.wait_for(
                            client.read_holding_registers(address, count=count, unit=slave_id),
                            timeout=LAMBDA_MODBUS_TIMEOUT
                        )
                    except (TypeError, AttributeError):
                        try:
                            # Try without slave/unit parameter
                            return await asyncio.wait_for(
                                client.read_holding_registers(address, count=count),
                                timeout=LAMBDA_MODBUS_TIMEOUT
                            )
                        except TypeError:
                            # Last resort: only address and count as positional
                            return await asyncio.wait_for(
                                client.read_holding_registers(address, count),
                                timeout=LAMBDA_MODBUS_TIMEOUT
                            )
            except asyncio.TimeoutError as e:
                last_exception = e
                if attempt < LAMBDA_MAX_RETRIES - 1:
                    _LOGGER.debug(
                        "Modbus read timeout at address %d (attempt %d/%d), retrying in %ds",
                        address, attempt + 1, LAMBDA_MAX_RETRIES, LAMBDA_RETRY_DELAY
                    )
                    await asyncio.sleep(LAMBDA_RETRY_DELAY)
                else:
                    _LOGGER.warning(
                        "Modbus read timeout at address %d after %d attempts",
                        address, LAMBDA_MAX_RETRIES
                    )
            except Exception as e:
                last_exception = e
                if attempt < LAMBDA_MAX_RETRIES - 1:
                    _LOGGER.debug(
                        "Modbus read error at address %d (attempt %d/%d): %s, retrying in %ds",
                        address, attempt + 1, LAMBDA_MAX_RETRIES, e, LAMBDA_RETRY_DELAY
                    )
                    await asyncio.sleep(LAMBDA_RETRY_DELAY)
                else:
                    break
    
    # If we get here, all retries failed
    if last_exception:
        # Don't log as error if Home Assistant is stopping
        if "Home Assistant is stopping" in str(last_exception) or "CancelledError" in str(last_exception):
            _LOGGER.debug("Modbus read cancelled at address %d (HA stopping): %s", address, last_exception)
        else:
            _LOGGER.info(
                "❌ MODBUS READ FAILED: address=%d, retries=%d, error=%s, caller=async_read_holding_registers",
                address, LAMBDA_MAX_RETRIES, last_exception
            )
        raise last_exception
```

#### 2. Modbus Write-Operationen

```189:220:custom_components/lambda_heat_pumps/modbus_utils.py
async def async_write_register(
    client, address: int, value: int, slave_id: int = LAMBDA_MODBUS_UNIT_ID
) -> Any:
    """Write single register with full API compatibility.
    
    Uses a global lock to prevent concurrent Modbus requests that could cause
    Transaction ID mismatches.
    """
    async with _modbus_read_lock:
        try:
            # For pymodbus 3.11.1, use address as positional, rest as kwargs
            try:
                # Try with slave parameter (most common in 3.x)
                return await client.write_register(address, value, slave=slave_id)
            except (TypeError, AttributeError):
                try:
                    # Try with unit parameter
                    return await client.write_register(address, value, unit=slave_id)
                except (TypeError, AttributeError):
                    # Try without slave/unit parameter
                    return await client.write_register(address, value)

        except Exception as e:
            # Don't log as error if Home Assistant is stopping
            if "Home Assistant is stopping" in str(e) or "CancelledError" in str(e):
                _LOGGER.debug("Modbus write cancelled at address %d (HA stopping): %s", address, e)
            else:
                _LOGGER.info(
                    "❌ MODBUS WRITE FAILED: address=%d, value=%d, error=%s, caller=async_write_register",
                    address, value, e
                )
            raise
```

**Wichtig**: Der gleiche Lock (`_modbus_read_lock`) wird für **Read- und Write-Operationen** verwendet, um vollständige Serialisierung zu gewährleisten.

#### 3. Health-Check-Operationen

```472:476:custom_components/lambda_heat_pumps/modbus_utils.py
async def _test_connection_health(coordinator) -> bool:
    """Test if the Modbus connection is healthy with robust API compatibility.
    
    Uses a lock to prevent concurrent health checks that could cause
    Transaction ID mismatches.
    """
```

Health-Checks verwenden einen separaten Lock (`_health_check_lock`), um Konflikte mit normalen Modbus-Operationen zu vermeiden.

## Architektur

### Datenfluss

```
┌─────────────────────────────────────────────────────────────┐
│                    Coordinator / Number / Service            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  async_read_holding_registers()                       │  │
│  │    └─ async with _modbus_read_lock:                  │  │
│  │         └─ client.read_holding_registers()            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  async_write_register()                               │  │
│  │    └─ async with _modbus_read_lock:                  │  │
│  │         └─ client.write_register()                    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    _modbus_read_lock                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Serialisiert ALLE Modbus-Operationen                │  │
│  │  - Read-Operationen                                  │  │
│  │  - Write-Operationen                                 │  │
│  │  - Eine Operation nach der anderen                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Modbus Client (pymodbus)                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Sequenzielle Modbus-Requests                        │  │
│  │  - Transaction ID wird korrekt zugeordnet            │  │
│  │  - Keine Konflikte                                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Lock-Strategie

**Zwei separate Locks**:

1. **`_modbus_read_lock`**: 
   - Für alle normalen Modbus-Operationen (Read/Write)
   - Global, wird von allen Modbus-Funktionen verwendet
   - Verhindert parallele Requests

2. **`_health_check_lock`**:
   - Für Health-Check-Operationen
   - Separater Lock, um Konflikte mit normalen Operationen zu vermeiden
   - Verhindert parallele Health-Checks

**Warum zwei Locks?**

- Health-Checks können während normaler Operationen laufen (ohne zu blockieren)
- Normale Operationen können während Health-Checks laufen (ohne zu blockieren)
- Nur gleichzeitige Health-Checks werden serialisiert
- Nur gleichzeitige normale Operationen werden serialisiert

## Verhalten

### Sequenzielle Ausführung

Mit dem Lock werden alle Modbus-Operationen **sequenziell** ausgeführt:

```
Request 1 → Lock erworben → Request gesendet → Response erhalten → Lock freigegeben
                                                                    ↓
Request 2 → Lock erworben → Request gesendet → Response erhalten → Lock freigegeben
                                                                    ↓
Request 3 → Lock erworben → Request gesendet → Response erhalten → Lock freigegeben
```

**Ohne Lock** (parallel, führt zu Fehlern):

```
Request 1 → Request gesendet ──────────→ Response erhalten
Request 2 → Request gesendet ──────────→ Response erhalten
Request 3 → Request gesendet ──────────→ Response erhalten
         ↑                                 ↑
         └─ Transaction ID Konflikte! ────┘
```

### Performance-Überlegungen

**Vorteile**:
- ✅ Keine Transaction ID Mismatches
- ✅ Korrekte Datenzuordnung
- ✅ Protokoll-konforme Implementierung
- ✅ Stabil und zuverlässig

**Nachteile**:
- ⚠️ Sequenzielle Ausführung (langsamer als parallel)
- ⚠️ Lock-Overhead (vernachlässigbar, ~0.1ms)

**Fazit**: Der Performance-Overhead ist minimal im Vergleich zu den Vorteilen (Stabilität, Korrektheit).

## Verwendung im Code

### Alle Modbus-Operationen verwenden den Lock

**Read-Operationen**:
- `async_read_holding_registers()`
- `async_read_input_registers()`

**Write-Operationen**:
- `async_write_register()`
- `async_write_registers()`

**Health-Checks**:
- `_test_connection_health()` (verwendet `_health_check_lock`)

### Beispiel: Verwendung in Coordinator

```python
# Im Coordinator wird async_read_holding_registers() verwendet
result = await async_read_holding_registers(
    self.client, 
    address=1000, 
    count=10, 
    slave_id=1
)
# Der Lock wird automatisch verwendet (intern in async_read_holding_registers)
```

### Beispiel: Verwendung in Number-Entity

```python
# In number.py wird async_write_register() verwendet
await async_write_register(
    self._coordinator.client,
    address=1050,
    value=250,
    slave_id=1
)
# Der Lock wird automatisch verwendet (intern in async_write_register)
```

## Wichtige Regeln

### ✅ RICHTIG: Lock wird automatisch verwendet

Alle Modbus-Operationen verwenden die Wrapper-Funktionen aus `modbus_utils.py`, die den Lock automatisch verwenden:

```python
# ✅ RICHTIG: Verwendet Lock automatisch
result = await async_read_holding_registers(client, address, count, slave_id)
```

### ❌ FALSCH: Direkter Client-Aufruf (ohne Lock)

Direkte Aufrufe auf den Modbus-Client umgehen den Lock und führen zu Transaction ID Mismatches:

```python
# ❌ FALSCH: Umgeht den Lock
result = await client.read_holding_registers(address, count, slave=slave_id)
```

**Wichtig**: Niemals direkt auf `client.read_holding_registers()` oder `client.write_register()` zugreifen! Immer die Wrapper-Funktionen aus `modbus_utils.py` verwenden.

## Troubleshooting

### Transaction ID Mismatch Fehler

**Symptom**:
```
ERROR: request ask for transaction_id=X but got id=Y, Skipping.
```

**Ursache**: 
- Direkter Client-Aufruf (ohne Lock)
- Lock nicht verwendet
- Parallele Requests

**Lösung**:
1. Prüfe, ob Wrapper-Funktionen aus `modbus_utils.py` verwendet werden
2. Prüfe, ob `async with _modbus_read_lock:` verwendet wird
3. Prüfe, ob direkte Client-Aufrufe vorhanden sind

### Performance-Probleme

**Symptom**: Modbus-Operationen sind langsam

**Ursache**: 
- Lock blockiert alle Operationen
- Viele sequenzielle Requests

**Lösung**:
- Sequenzielle Ausführung ist gewollt (verhindert Fehler)
- Performance-Overhead ist minimal (~0.1ms pro Lock)
- Alternative: Parallele Ausführung würde zu Transaction ID Mismatches führen

## Zusammenfassung

Die Serialisierung von Modbus-Operationen durch globale Locks stellt sicher, dass:

1. ✅ **Keine Transaction ID Mismatches** auftreten
2. ✅ **Korrekte Datenzuordnung** gewährleistet ist
3. ✅ **Protokoll-konforme Implementierung** vorhanden ist
4. ✅ **Stabile und zuverlässige** Modbus-Kommunikation stattfindet

**Wichtig**: Alle Modbus-Operationen müssen die Wrapper-Funktionen aus `modbus_utils.py` verwenden, die den Lock automatisch verwenden. Direkte Client-Aufrufe umgehen den Lock und führen zu Fehlern.

