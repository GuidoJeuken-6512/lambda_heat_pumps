# Lambda Heat Pumps Integration - Robustheit Verbesserungen

## Übersicht

Dieses Dokument beschreibt geplante Verbesserungen zur Erhöhung der Robustheit der Lambda Wärmepumpen Integration bei Netzwerkunterbrechungen und Verbindungsproblemen.

**Prinzip: "Keep it Simple"** - Robustheit läuft automatisch im Hintergrund, ohne dass der Benutzer etwas konfigurieren muss.

## Priorität: HOCH

### 1. Konstanten-Zentralisierung

**Problem:** Timeout-Konstanten sind in verschiedenen Dateien verstreut und nicht zentralisiert.

**Lösung:** Alle Modbus-Konstanten in `const.py` zentralisieren.

**Aktuelle Situation:**
```python
# In modbus_utils.py (PROBLEMATISCH)
LAMBDA_MODBUS_TIMEOUT = 60  # Duplikat in modbus_utils.py
LAMBDA_MODBUS_UNIT_ID = 1   # Duplikat in modbus_utils.py
LAMBDA_MAX_RETRIES = 3      # Duplikat in modbus_utils.py
LAMBDA_RETRY_DELAY = 5      # Duplikat in modbus_utils.py
```

**Neue zentralisierte Struktur:**
```python
# In const.py - Alle Modbus-Konstanten zentralisiert
# Timeout-Konstanten
LAMBDA_MODBUS_TIMEOUT = 10  # Standard-Timeout (realistisch für Modbus)

# Retry-Konstanten
LAMBDA_MAX_RETRIES = 3      # Maximum retry attempts
LAMBDA_RETRY_DELAY = 5      # Delay between retries in seconds

# Modbus-Konstanten
LAMBDA_MODBUS_UNIT_ID = 1   # Lambda Unit ID
LAMBDA_MODBUS_PORT = 502    # Standard Modbus TCP port

# Batch-Read-Konstanten
LAMBDA_MAX_BATCH_FAILURES = 3  # Nach 3 Fehlern auf Individual-Reads umstellen
LAMBDA_MAX_CYCLING_WARNINGS = 3  # Nach 3 Warnings unterdrücken
LAMBDA_MODBUS_SAFETY_MARGIN = 120  # Modbus safety margin für Batch-Reads
```

**Vorteile der Zentralisierung:**
- ✅ **Einheitliche Konfiguration** - Alle Konstanten an einem Ort
- ✅ **Einfache Anpassung** - Timeout-Werte zentral änderbar
- ✅ **Keine Duplikate** - Vermeidet Inkonsistenzen
- ✅ **Bessere Wartbarkeit** - Klare Struktur

### 2. Exponential Backoff (automatisch)

**Problem:** Aktuell wird eine feste 5-Sekunden-Verzögerung zwischen Retry-Versuchen verwendet, was bei anhaltenden Netzwerkproblemen ineffizient ist.

**Lösung:** Exponential Backoff automatisch implementieren.

**Implementierung:**
```python
# In modbus_utils.py - async_read_holding_registers()
import random

async def async_read_holding_registers_with_backoff(client, address, count, slave_id):
    last_exception = None
    
    for attempt in range(LAMBDA_MAX_RETRIES):
        try:
            return await asyncio.wait_for(
                client.read_holding_registers(address, count=count, slave=slave_id),
                timeout=LAMBDA_MODBUS_TIMEOUT
            )
        except Exception as e:
            last_exception = e
            if attempt < LAMBDA_MAX_RETRIES - 1:
                # Exponential backoff mit Jitter
                base_delay = LAMBDA_RETRY_DELAY * (2 ** attempt)
                max_delay = 30  # Maximum 30 Sekunden
                delay = min(base_delay, max_delay)
                
                # Jitter hinzufügen (±20% Zufallsschwankung)
                jitter = random.uniform(-0.2, 0.2) * delay
                final_delay = max(1, delay + jitter)  # Minimum 1 Sekunde
                
                _LOGGER.debug(
                    "Modbus read error at address %d (attempt %d/%d): %s, retrying in %.1fs",
                    address, attempt + 1, LAMBDA_MAX_RETRIES, e, final_delay
                )
                await asyncio.sleep(final_delay)
            else:
                break
    
    # Fehlerbehandlung wie bisher...
    raise last_exception
```

**Vorteile:**
- Reduziert Netzwerklast bei anhaltenden Problemen
- Verhindert "Thundering Herd" Effekte
- Jitter verhindert synchronisierte Retry-Versuche mehrerer Instanzen
- **Automatisch** - Benutzer muss nichts konfigurieren

### 3. Intelligenter Circuit Breaker (automatisch)

**Problem:** Bei anhaltenden Verbindungsproblemen werden weiterhin Versuche unternommen, was Ressourcen verschwendet. Zusätzlich werden Netzwerkfehler und Protokollfehler gleich behandelt.

**Lösung:** Intelligenter Circuit Breaker mit Fehlerdifferenzierung automatisch implementieren.

**Implementierung:**
```python
# In coordinator.py - Intelligenter Circuit Breaker
import time
from pymodbus.exceptions import ModbusException

class SmartCircuitBreaker:
    def __init__(self):
        self.failure_count = 0
        self.last_failure_time = None
        self.is_open = False
        self.force_open = False  # Für Protokollfehler
        
    def can_execute(self) -> bool:
        """Prüft ob eine Ausführung erlaubt ist."""
        if not self.is_open:
            return True
        
        # Nach 60 Sekunden wieder versuchen (außer bei force_open)
            if (self.last_failure_time and 
            time.time() - self.last_failure_time > 60 and
            not self.force_open):
            self.is_open = False
            self.failure_count = 0
            _LOGGER.info("Circuit breaker reset - attempting connection again")
            return True
        
        return False
    
    def record_success(self):
        """Registriert erfolgreiche Ausführung."""
        self.failure_count = 0
        self.is_open = False
        self.force_open = False
        _LOGGER.info("Circuit breaker CLOSED - Modbus connection restored")
    
    def record_failure(self, exception: Exception):
        """Registriert fehlgeschlagene Ausführung mit intelligenter Fehlerbehandlung."""
        if isinstance(exception, (ConnectionError, asyncio.TimeoutError)):
            # Netzwerkfehler - normaler Circuit Breaker
        self.failure_count += 1
        self.last_failure_time = time.time()
        
            _LOGGER.warning(
                "Network error (attempt %d/%d): %s - Circuit breaker will open after 3 failures",
                self.failure_count, 3, exception
            )
            
            if self.failure_count >= 3:
                self.is_open = True
                _LOGGER.warning("Circuit breaker OPENED due to network issues - will retry in 60 seconds")
                
        elif isinstance(exception, ModbusException):
            # Protokollfehler - sofortiger Abbruch
            self.is_open = True
            self.force_open = True
            self.failure_count = 999  # Markiere als kritisch
            self.last_failure_time = time.time()
            _LOGGER.error("Circuit breaker FORCE OPENED due to Modbus protocol error: %s", exception)
        else:
            # Andere Fehler - normaler Circuit Breaker
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= 3:
                self.is_open = True
                _LOGGER.warning("Circuit breaker OPENED after %d failures", self.failure_count)

# In LambdaCoordinator.__init__()
self._circuit_breaker = SmartCircuitBreaker()

# In _read_modbus_data()
if not self._circuit_breaker.can_execute():
    _LOGGER.debug("Circuit breaker is OPEN - skipping Modbus read")
    return

try:
    result = await self._modbus_client.read_holding_registers(address, count=count, slave=slave_id)
    self._circuit_breaker.record_success()
            return result
except Exception as e:
    self._circuit_breaker.record_failure(e)
            raise
```

**Vorteile:**
- **Intelligente Fehlerbehandlung** - Netzwerk vs. Protokollfehler
- **Sofortiger Abbruch** bei Protokollfehlern (verhindert weitere Versuche)
- **Bessere Diagnose** - Unterscheidung zwischen temporären und permanenten Problemen
- **Automatisch** - Benutzer muss nichts konfigurieren

### 4. HA-kompatible Last-Known-Value (automatisch)

**Problem:** Bei Verbindungsproblemen werden alle Sensoren als "unavailable" angezeigt. Zusätzlich gehen device_class und state_class verloren.

**Lösung:** HA-kompatible letzte bekannte Werte automatisch beibehalten.

**Implementierung:**
```python
# In coordinator.py - HA-kompatibler Offline-Manager
class HACompatibleOfflineManager:
    def __init__(self):
        self.last_known_data = {}
        self.offline_since = None
        self.max_offline_duration = 1800  # 30 Minuten
    
    def update_data(self, data: dict):
        """Aktualisiert letzte bekannte Daten."""
            self.last_known_data = data.copy()
        self.offline_since = None
    
    def get_offline_data(self) -> dict:
        """Gibt letzte bekannte Daten zurück wenn offline - HA-kompatibel."""
        if not self.offline_since:
            self.offline_since = time.time()
        
        # Prüfe ob Offline-Dauer zu lang ist
        if time.time() - self.offline_since > self.max_offline_duration:
            return {}  # Zu lange offline = unavailable
        
        # Wichtig: device_class und state_class beibehalten
        offline_data = self.last_known_data.copy()
        
        # Für Energie-Sensoren: last_reset beibehalten
        for sensor_id, data in offline_data.items():
            if "last_reset" in data:
                # last_reset nicht ändern - Energie-Sensoren brauchen das
                pass
            
            # State-Klassen beibehalten (device_class, state_class)
            if "device_class" in data:
                # device_class beibehalten
                pass
            
            if "state_class" in data:
                # state_class beibehalten
                pass
        
        return offline_data
    
    def is_offline(self) -> bool:
        return self.offline_since is not None
    
# In LambdaCoordinator.__init__()
self._offline_manager = HACompatibleOfflineManager()

# In _async_update_data()
try:
    # Modbus-Daten lesen
    data = await self._read_modbus_data()
    self._offline_manager.update_data(data)
                return data
except Exception as e:
    # Bei Fehler: Letzte bekannte Daten zurückgeben
    offline_data = self._offline_manager.get_offline_data()
            if offline_data:
        _LOGGER.debug("Using last known data due to connection error: %s", e)
                return offline_data
    else:
            raise
```

**Vorteile:**
- **HA-Kompatibilität** - device_class und state_class bleiben erhalten
- **Energie-Sensoren** - last_reset wird korrekt behandelt
- **State-Klassen** - Sensoren behalten ihre Eigenschaften
- **Automatisch** - Benutzer muss nichts konfigurieren

### 5. Circuit-Breaker-Status als Binary Sensor (automatisch)

**Problem:** Benutzer können den Status des Circuit Breakers nicht sehen.

**Lösung:** Circuit-Breaker-Status als binary_sensor verfügbar machen.

**Implementierung:**
```python
# In coordinator.py - Circuit-Breaker-Sensor
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass

class CircuitBreakerSensor(BinarySensorEntity):
    def __init__(self, circuit_breaker: SmartCircuitBreaker, device_info):
        self._circuit_breaker = circuit_breaker
        self._attr_name = "Lambda Modbus Circuit Breaker"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_device_info = device_info
        self._attr_unique_id = f"{device_info['identifiers']}_circuit_breaker"
    
    @property
    def is_on(self) -> bool:
        """True wenn Circuit Breaker geschlossen (Verbindung OK)."""
        return not self._circuit_breaker.is_open
    
    @property
    def extra_state_attributes(self) -> dict:
        """Zusätzliche Informationen über den Circuit Breaker."""
        return {
            "failure_count": self._circuit_breaker.failure_count,
            "last_failure_time": self._circuit_breaker.last_failure_time,
            "state": "open" if self._circuit_breaker.is_open else "closed",
            "force_open": self._circuit_breaker.force_open
        }

# In LambdaCoordinator.__init__()
self._circuit_breaker_sensor = CircuitBreakerSensor(self._circuit_breaker, device_info)

# In async_add_entities()
entities.append(self._circuit_breaker_sensor)
```

**Vorteile:**
- **Sichtbarkeit** - Benutzer sehen Circuit-Breaker-Status
- **Debugging** - Bessere Fehlerdiagnose
- **Monitoring** - HA kann Circuit-Breaker-Status überwachen
- **Automatisch** - Benutzer muss nichts konfigurieren

### 6. Expertenoptionen (optional)

**Problem:** Fortgeschrittene Benutzer möchten Timeout-Werte anpassen.

**Lösung:** Expertenoptionen über HA-Konfiguration verfügbar machen.

**Implementierung:**
```python
# In const.py - Expertenoptionen
LAMBDA_MODBUS_TIMEOUT = 10  # Standard
LAMBDA_MAX_RETRIES = 3      # Standard
LAMBDA_CIRCUIT_BREAKER_ENABLED = True  # Standard

# In __init__.py - Konfiguration aus HA-Config lesen
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Expertenoptionen aus HA-Config lesen
    config = entry.data
    modbus_timeout = config.get("modbus_timeout", LAMBDA_MODBUS_TIMEOUT)
    max_retries = config.get("max_retries", LAMBDA_MAX_RETRIES)
    circuit_breaker_enabled = config.get("circuit_breaker_enable", LAMBDA_CIRCUIT_BREAKER_ENABLED)
    
    # Konfiguration an Coordinator weitergeben
    coordinator = LambdaCoordinator(
        hass=hass,
        entry=entry,
        modbus_timeout=modbus_timeout,
        max_retries=max_retries,
        circuit_breaker_enabled=circuit_breaker_enabled
    )
```

**Vorteile:**
- **Expertenoptionen** - Für fortgeschrittene Benutzer
- **Standardwerte** - Einfache Benutzer müssen nichts konfigurieren
- **Flexibilität** - Anpassung bei speziellen Netzwerkumgebungen

## Implementierungsplan

### Phase 1: Konstanten-Zentralisierung (sofort)
1. **Konstanten in const.py hinzufügen**
2. **Duplikate in modbus_utils.py entfernen**
3. **Hardcoded Werte in coordinator.py ersetzen**
4. **Imports in allen Dateien anpassen**

### Phase 2: Exponential Backoff (automatisch)
1. **Backoff-Logik in modbus_utils.py implementieren**
2. **Tests aktualisieren**

### Phase 3: Intelligenter Circuit Breaker (automatisch)
1. **SmartCircuitBreaker-Klasse in coordinator.py implementieren**
2. **Fehlerdifferenzierung implementieren**
3. **Integration in _read_modbus_data()**

### Phase 4: HA-kompatible Last-Known-Value (automatisch)
1. **HACompatibleOfflineManager-Klasse in coordinator.py implementieren**
2. **HA-Kompatibilität implementieren**
3. **Integration in _async_update_data()**

### Phase 5: Circuit-Breaker-Status als Binary Sensor (automatisch)
1. **CircuitBreakerSensor-Klasse implementieren**
2. **Integration in async_add_entities()**

### Phase 6: Expertenoptionen (optional)
1. **Konfiguration aus HA-Config lesen**
2. **Parameter an Coordinator weitergeben**

## Vorteile der verbesserten Lösung

### ✅ Vorteile:
- **Einfachheit** - Benutzer müssen nichts konfigurieren (Standardwerte)
- **Intelligente Fehlerbehandlung** - Netzwerk vs. Protokollfehler
- **HA-Kompatibilität** - device_class und state_class bleiben erhalten
- **Sichtbarkeit** - Circuit-Breaker-Status als binary_sensor
- **Expertenoptionen** - Konfigurierbarkeit für fortgeschrittene Benutzer
- **Wartbarkeit** - Weniger Code, weniger Fehler
- **Automatisch** - Robustheit läuft im Hintergrund

### ✅ Was implementiert wird:
- **Konstanten-Zentralisierung** - Alle Konstanten an einem Ort
- **Exponential Backoff** - Intelligente Retry-Logik
- **Intelligenter Circuit Breaker** - Fehlerdifferenzierung
- **HA-kompatible Last-Known-Value** - Sensoren behalten Eigenschaften
- **Circuit-Breaker-Status** - Sichtbarkeit für Benutzer
- **Expertenoptionen** - Konfigurierbarkeit für Fortgeschrittene

### ❌ Was NICHT implementiert wird:
- **Komplexe YAML-Konfiguration** - Nur einfache Expertenoptionen
- **Health-Monitoring** - Überflüssig für einfache Integration
- **Adaptive Intervalle** - Zu komplex
- **Komplexer Offline-Datenmanager** - Einfache Last-Known-Value reicht

## Fazit

**"Keep it Simple, but Smart"** - Die Integration soll robust und intelligent sein, aber nicht kompliziert. Benutzer wollen eine funktionierende Wärmepumpen-Integration mit intelligenter Fehlerbehandlung.

**Implementiere die wichtigsten Features automatisch im Hintergrund, mit Expertenoptionen für fortgeschrittene Benutzer.**