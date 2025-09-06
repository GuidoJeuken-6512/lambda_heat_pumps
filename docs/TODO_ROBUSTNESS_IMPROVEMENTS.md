# Lambda Heat Pumps Integration - Robustheit Verbesserungen

## Übersicht

Dieses Dokument beschreibt geplante Verbesserungen zur Erhöhung der Robustheit der Lambda Wärmepumpen Integration bei Netzwerkunterbrechungen und Verbindungsproblemen.

**Prinzip: "Keep it Simple"** - Robustheit läuft automatisch im Hintergrund, ohne dass der Benutzer etwas konfigurieren muss.

## Status: IMPLEMENTIERT ✅

### 1. Konstanten-Zentralisierung ✅

**Status:** Alle Modbus-Konstanten wurden erfolgreich in `const.py` zentralisiert.

**Implementierte Struktur:**
```python
# In const.py - Alle Modbus-Konstanten zentralisiert
# Timeout-Konstanten
LAMBDA_MODBUS_TIMEOUT = 3  # Sehr kurzer Timeout um HA 10s Warnings zu vermeiden

# Retry-Konstanten
LAMBDA_MAX_RETRIES = 3      # Maximum retry attempts
LAMBDA_RETRY_DELAY = 5      # Delay between retries in seconds

# Modbus-Konstanten
LAMBDA_MODBUS_UNIT_ID = 1   # Lambda Unit ID
LAMBDA_MODBUS_PORT = 502    # Standard Modbus TCP port

# Register-spezifische Timeouts
LAMBDA_REGISTER_TIMEOUTS = {
    0: 2,     # error_state - sehr kurzer Timeout (deutlich unter HA 10s Limit)
    1: 3,     # Standard-Timeout (deutlich unter HA 10s Limit)
    2: 3,     # Standard-Timeout (deutlich unter HA 10s Limit)
}

# Individual-Reads für problematische Register
LAMBDA_INDIVIDUAL_READ_REGISTERS = [0]  # error_state einzeln lesen
LAMBDA_LOW_PRIORITY_REGISTERS = [0]     # error_state niedrige Priorität

# Multi-Client Anti-Synchronisation
LAMBDA_MULTI_CLIENT_SUPPORT = True
LAMBDA_BASE_UPDATE_INTERVAL = 30
LAMBDA_RANDOM_INTERVAL_RANGE = 2
LAMBDA_MIN_INTERVAL = 25
LAMBDA_MAX_INTERVAL = 35
LAMBDA_ANTI_SYNC_ENABLED = True
LAMBDA_ANTI_SYNC_FACTOR = 0.2
```

**Erreichte Vorteile:**
- ✅ **Einheitliche Konfiguration** - Alle Konstanten an einem Ort
- ✅ **Einfache Anpassung** - Timeout-Werte zentral änderbar
- ✅ **Keine Duplikate** - Vermeidet Inkonsistenzen
- ✅ **Bessere Wartbarkeit** - Klare Struktur

### 2. Dynamische Individual-Reads ✅

**Status:** Vollständig implementiert in beiden Coordinatoren (Standard und Modular) mit absoluten Adressen.

**Problem gelöst:** Register mit wiederholten Timeouts oder Fehlern werden automatisch zur Laufzeit zu Individual-Reads hinzugefügt.

**Implementierte Lösung:**
```python
# Statische Konfiguration in const.py (absolute Adressen)
LAMBDA_INDIVIDUAL_READ_REGISTERS = [0]  # Register 0 einzeln lesen
LAMBDA_REGISTER_TIMEOUTS = {0: 2}      # Register 0: 2s Timeout

# Dynamische Individual-Read-Verwaltung in beiden Coordinatoren
self._dynamic_individual_reads = set(LAMBDA_INDIVIDUAL_READ_REGISTERS)  # Startet mit statischen Registern
self._register_timeout_counters = {}  # Zähler für Timeout-Häufigkeit pro Register
self._register_failure_counters = {}  # Zähler für Fehler-Häufigkeit pro Register
self._dynamic_timeout_threshold = 3   # Nach 3 Timeouts -> Individual-Read
self._dynamic_failure_threshold = 5   # Nach 5 Fehlern -> Individual-Read

# Zentralisierte Funktion in modbus_utils.py
def check_dynamic_individual_read(
    dynamic_individual_reads: set,
    register_timeout_counters: dict,
    register_failure_counters: dict,
    address: int,
    relative_addr: int,
    error_type: str,
    dynamic_timeout_threshold: int = 3,
    dynamic_failure_threshold: int = 5
) -> None:
    """Prüft ob ein Register dynamisch zu Individual-Reads hinzugefügt werden soll."""
```

**Funktionsweise:**
1. **Statische Individual-Reads:** Register 0 wird sofort einzeln gelesen
2. **Dynamische Aufnahme:** Register mit 3+ Timeouts oder 5+ Fehlern werden automatisch hinzugefügt
3. **Absolute Adressen:** Alle Register werden als absolute Adressen behandelt
4. **Info-Messages:** Bestätigung der dynamischen Aufnahme mit detaillierten Logs
5. **Zentralisierte Logik:** Eine Funktion für beide Coordinatoren in `modbus_utils.py`

**Erreichte Vorteile:**
- ✅ **Präzise Kontrolle** - Nur Register 0 statisch konfiguriert
- ✅ **Automatische Anpassung** - Dynamische Aufnahme problematischer Register
- ✅ **Absolute Adressen** - Konsistente Behandlung aller Register
- ✅ **Bessere Performance** - Nur problematische Register werden einzeln gelesen
- ✅ **Zentralisierte Wartung** - Konsistente Logik in beiden Coordinatoren

**Tests implementiert:**
- ✅ **Unit Tests** - `test_individual_reads.py` mit 20+ Test-Cases
- ✅ **Konfiguration Tests** - Validierung der Konstanten
- ✅ **Timeout-Adjustment Tests** - Prüfung der Timeout-Anpassung
- ✅ **Dynamische Individual-Reads Tests** - Schwellenwert-Logik
- ✅ **Integration Tests** - Coordinator-Initialisierung
- ✅ **Circuit Breaker Tests** - Integration mit Robustheits-Features

### 3. Exponential Backoff (automatisch) ✅

**Status:** Vollständig implementiert in `modbus_utils.py` mit Jitter für Anti-Synchronisation.

**Problem gelöst:** Feste 5-Sekunden-Verzögerung zwischen Retry-Versuchen wurde durch intelligentes Exponential Backoff ersetzt.

**Implementierte Lösung:**
```python
# In modbus_utils.py - async_read_holding_registers_with_backoff
async def async_read_holding_registers_with_backoff(
    client, address: int, count: int, slave_id: int, timeout: int = LAMBDA_MODBUS_TIMEOUT
) -> Any:
    """Read holding registers with exponential backoff and jitter."""
    last_exception = None
    
    for attempt in range(LAMBDA_MAX_RETRIES):
        try:
            # Exponential Backoff mit Jitter
            if attempt > 0:
                base_delay = LAMBDA_RETRY_DELAY * (2 ** (attempt - 1))
                jitter = random.uniform(0.5, 1.5)  # 50-150% des Basis-Delays
                delay = base_delay * jitter
                await asyncio.sleep(delay)
            
            # Modbus-Read mit Timeout
            return await asyncio.wait_for(
                client.read_holding_registers(address, count=count, slave=slave_id),
                timeout=timeout
            )
        except asyncio.TimeoutError as e:
            last_exception = e
            _LOGGER.debug(f"Timeout attempt {attempt + 1}/{LAMBDA_MAX_RETRIES} for address {address}")
        except Exception as e:
            last_exception = e
            _LOGGER.debug(f"Error attempt {attempt + 1}/{LAMBDA_MAX_RETRIES} for address {address}: {e}")
    
    # Alle Versuche fehlgeschlagen
    raise last_exception
```

**Erreichte Vorteile:**
- ✅ **Intelligente Verzögerung** - Exponential Backoff verhindert Überlastung
- ✅ **Jitter-Integration** - Zufällige Verzögerung verhindert Synchronisation
- ✅ **Timeout-spezifisch** - Verschiedene Timeouts für verschiedene Register
- ✅ **Automatische Anpassung** - Keine manuelle Konfiguration erforderlich

### 4. Info-Messages für Robustheits-Features ✅

**Status:** Vollständig implementiert mit detaillierten Log-Messages für alle Robustheits-Features.

**Problem gelöst:** Benutzer können jetzt sehen, wann und warum Robustheits-Features aktiviert werden.

**Implementierte Messages:**
```python
# Individual-Read Messages
_LOGGER.info(f"🔧 INDIVIDUAL-READ: Using individual read for register {addr} (relative: {relative_addr}) - configured for individual reading")

# Dynamische Individual-Read Messages
_LOGGER.info(f"🔄 DYNAMIC-INDIVIDUAL: Register {address} (relative: {relative_addr}) added to Individual-Reads after {timeout_count} timeouts")

# Timeout-Adjustment Messages
_LOGGER.info(f"⏱️ TIMEOUT-ADJUST: Using sensor-specific timeout {timeout}s for relative address {relative_addr} (absolute: {address}) - reduced from default {default_timeout}s")

# Multi-Client Anti-Sync Messages
_LOGGER.debug(f"Multi-client anti-sync: Base interval {base_update_interval}s, adjusted to {adjusted_interval:.1f}s (jitter: {jitter:+.1f}s)")

# Robustness Features Status
_LOGGER.info(f"Robustness features enabled - Circuit Breaker: {LAMBDA_CIRCUIT_BREAKER_ENABLED}, Timeouts: {LAMBDA_REGISTER_TIMEOUTS}")
```

**Erreichte Vorteile:**
- ✅ **Transparenz** - Benutzer sehen, wann Robustheits-Features aktiv sind
- ✅ **Debugging** - Einfache Identifikation von problematischen Registern
- ✅ **Monitoring** - Überwachung der dynamischen Individual-Read-Aktivierung
- ✅ **Troubleshooting** - Detaillierte Logs für Problembehebung

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

## ✅ IMPLEMENTIERUNGS-STATUS ZUSAMMENFASSUNG

### Vollständig implementierte Features:

#### 1. Konstanten-Zentralisierung ✅
- Alle Modbus-Konstanten in `const.py` zentralisiert
- Register-spezifische Timeouts implementiert
- Multi-Client Anti-Synchronisation konfiguriert

#### 2. Dynamische Individual-Reads ✅
- Automatische Aufnahme problematischer Register zur Laufzeit
- Zentralisierte Funktion in `modbus_utils.py` für beide Coordinatoren
- Schwellenwerte: 3 Timeouts oder 5 Fehler → Individual-Read

#### 3. Exponential Backoff ✅
- Intelligente Retry-Logik mit Jitter
- Timeout-spezifische Anpassungen
- Automatische Verzögerungsberechnung

#### 4. Info-Messages ✅
- Detaillierte Log-Messages für alle Robustheits-Features
- Transparenz für Benutzer und Debugging
- Monitoring der dynamischen Individual-Read-Aktivierung

### Erwartete Verbesserungen:

#### ✅ Sofortige Verbesserungen:
- **Keine 10s Timeout-Warnings** mehr von Home Assistant
- **Schnellere Fehlerbehandlung** durch reduzierte Timeouts (2-3s)
- **Automatische Individual-Reads** für problematische Register

#### ✅ Langfristige Verbesserungen:
- **Selbstheilende Systeme** bei Netzwerkproblemen
- **Adaptive Robustheit** basierend auf tatsächlichen Problemen
- **Bessere Performance** durch intelligente Register-Behandlung

### Nächste Schritte:
1. **Integration neu starten** - Damit alle Features aktiv werden
2. **Logs überwachen** - Bestätigung der Individual-Read-Aktivierung
3. **Verhalten beobachten** - Überprüfung der Timeout-Eliminierung

## 🚨 KRITISCHE FRAGE: Warum wurde das Update-Intervall nicht angepasst?

### Problem-Analyse aus dem Log:
```
2025-08-28 14:41:17.178 WARNING (MainThread) [homeassistant.helpers.entity] Update of sensor.eu08l_hp1_error_state is taking over 10 seconds
2025-08-28 14:41:17.178 WARNING (MainThread) [homeassistant.components.sensor] Updating lambda_heat_pumps sensor took longer than the scheduled update interval 0:00:30
```

### Mögliche Ursachen:

#### 1. **Robustheits-Features noch nicht implementiert** ❌
- **Status:** Die in diesem TODO beschriebenen Features sind noch NICHT implementiert
- **Beweis:** Log zeigt weiterhin 10-Sekunden-Timeouts und 30-Sekunden-Update-Intervalle
- **Lösung:** Implementierung der Robustheits-Features aus diesem TODO

#### 2. **Multi-Client-Modbus-Problem** 🚨
- **Problem:** Mehrere Clients greifen gleichzeitig auf Lambda per Modbus zu
- **Symptom:** Immer der gleiche Sensor (`error_state`) verursacht Timeouts
- **Ursache:** Synchronisierte Update-Intervalle führen zu Modbus-Konflikten
- **Lösung:** Anti-Synchronisation mit ungleichmäßigen Update-Intervallen

#### 3. **Spezifischer Sensor-Problem** 🎯
- **Sensor:** `sensor.eu08l_hp1_error_state` (relative_address: 0)
- **Problem:** Dieser spezifische Sensor verursacht immer die 10-Sekunden-Timeouts
- **Mögliche Ursachen:**
  - Register 0 ist problematisch
  - Sensor wird in Batch-Reads mit anderen Registern gelesen
  - Timeout-Konfiguration für diesen Sensor ungeeignet

### Sofortige Lösungsansätze:

#### Option 1: Multi-Client Anti-Synchronisation (EMPFOHLEN)
```python
# In const.py - Multi-Client-Konfiguration
LAMBDA_MULTI_CLIENT_SUPPORT = True
LAMBDA_BASE_UPDATE_INTERVAL = 10  # Basis-Intervall
LAMBDA_RANDOM_INTERVAL_RANGE = 2  # ±2 Sekunden Zufall
LAMBDA_MIN_INTERVAL = 8           # Minimum
LAMBDA_MAX_INTERVAL = 15          # Maximum

# Anti-Synchronisation
LAMBDA_ANTI_SYNC_ENABLED = True
LAMBDA_ANTI_SYNC_FACTOR = 0.2     # 20% Zufallsschwankung
```

#### Option 2: Sensor-spezifische Timeouts
```python
# In const.py - Register-spezifische Timeouts
LAMBDA_REGISTER_TIMEOUTS = {
    0: 15,    # error_state - längerer Timeout
    1: 10,    # Standard-Timeout
    2: 10,    # Standard-Timeout
}

# Individual-Reads für problematische Register
LAMBDA_INDIVIDUAL_READ_REGISTERS = [0]  # error_state einzeln lesen
LAMBDA_LOW_PRIORITY_REGISTERS = [0]     # error_state niedrige Priorität
```

#### Option 3: Kombinierte Lösung
- **Multi-Client Anti-Synchronisation** für Update-Intervalle
- **Sensor-spezifische Timeouts** für problematische Register
- **Intelligenter Circuit Breaker** für Fehlerbehandlung

### Implementierungsreihenfolge:

1. **SOFORT:** Multi-Client Anti-Synchronisation implementieren
2. **DANN:** Sensor-spezifische Timeouts für `error_state`
3. **DANACH:** Vollständige Robustheits-Features aus diesem TODO

## Multi-Client Modbus Anti-Synchronisation

### Problem:
- Mehrere Clients greifen gleichzeitig auf Lambda per Modbus zu
- Synchronisierte Update-Intervalle führen zu Modbus-Konflikten
- Immer der gleiche Sensor (`error_state`) verursacht Timeouts

### Lösung: Ungleichmäßige Update-Intervalle
```python
# In coordinator.py - Anti-Synchronisation
import random

class LambdaCoordinator:
    def __init__(self, ...):
        # Anti-Synchronisation für Multi-Client-Umgebungen
        if LAMBDA_ANTI_SYNC_ENABLED:
            base_interval = LAMBDA_BASE_UPDATE_INTERVAL
            random_range = LAMBDA_RANDOM_INTERVAL_RANGE
            
            # Zufällige Abweichung hinzufügen
            jitter = random.uniform(-random_range, random_range)
            adjusted_interval = max(LAMBDA_MIN_INTERVAL, 
                                  min(LAMBDA_MAX_INTERVAL, 
                                      base_interval + jitter))
            
            self.update_interval = timedelta(seconds=adjusted_interval)
            _LOGGER.info(f"Multi-client anti-sync: Update interval set to {adjusted_interval}s")
        else:
            self.update_interval = timedelta(seconds=LAMBDA_BASE_UPDATE_INTERVAL)
```

### Vorteile:
- ✅ **Verhindert Modbus-Konflikte** - Clients greifen nicht gleichzeitig zu
- ✅ **Reduziert Timeouts** - Weniger Kollisionen zwischen Clients
- ✅ **Einfach zu implementieren** - Nur wenige Zeilen Code
- ✅ **Automatisch** - Benutzer muss nichts konfigurieren

## Fazit

**"Keep it Simple, but Smart"** - Die Integration soll robust und intelligent sein, aber nicht kompliziert. Benutzer wollen eine funktionierende Wärmepumpen-Integration mit intelligenter Fehlerbehandlung.

**KRITISCH:** Die Robustheits-Features aus diesem TODO sind noch NICHT implementiert! Das erklärt, warum das Update-Intervall nicht angepasst wurde und weiterhin Timeouts auftreten.

**SOFORTIGE LÖSUNG:** Multi-Client Anti-Synchronisation implementieren, um Modbus-Konflikte zu verhindern.

**Implementiere die wichtigsten Features automatisch im Hintergrund, mit Expertenoptionen für fortgeschrittene Benutzer.**

## 🔄 **Offene Punkte / Zukünftige Verbesserungen**

### 1. Konfigurierbare Update-Häufigkeit

**Problem:** Aktuell haben alle Sensoren das gleiche Update-Intervall (30s), was zu Modbus-Konflikten und Timeouts führen kann.

**Lösungsansätze:**

#### **A) Statische Konfiguration über const.py**
```python
# Sensor-spezifische Update-Intervalle
LAMBDA_SENSOR_UPDATE_INTERVALS = {
    "error_state": 10,      # Kritische Sensoren - schnelle Updates
    "temperature": 15,      # Wichtige Sensoren - mittlere Updates  
    "pressure": 30,         # Standard-Sensoren - normale Updates
    "statistics": 60,       # Stabile Sensoren - langsame Updates
    "firmware": 300,        # Selten ändernde Sensoren - minimale Updates
}
```

**Vorteile:**
- ✅ **Einfach zu implementieren** - nur const.py ändern
- ✅ **Vorhersagbar** - feste Intervalle, keine Überraschungen
- ✅ **Benutzerfreundlich** - klare Konfiguration
- ✅ **Stabil** - keine dynamischen Änderungen zur Laufzeit
- ✅ **Debugging-freundlich** - konstante Verhalten

**Nachteile:**
- ❌ **Nicht adaptiv** - kann nicht auf Netzwerk-Qualität reagieren
- ❌ **Manuelle Anpassung** - Benutzer muss Werte selbst optimieren
- ❌ **Einheitslösung** - gleiche Intervalle für alle Installationen

#### **B) Dynamische Konfiguration zur Laufzeit**
```python
# Adaptive Update-Intervalle basierend auf Performance
def calculate_dynamic_interval(sensor_type, error_rate, network_quality):
    base_interval = LAMBDA_SENSOR_UPDATE_INTERVALS[sensor_type]
    
    if error_rate > 0.5:  # Viele Fehler
        return min(base_interval * 2, 120)  # Verlangsamen
    elif network_quality > 0.9:  # Gute Verbindung
        return max(base_interval * 0.5, 5)  # Beschleunigen
    else:
        return base_interval
```

**Vorteile:**
- ✅ **Adaptiv** - passt sich an Netzwerk-Bedingungen an
- ✅ **Selbstoptimierend** - lernt aus Fehlern
- ✅ **Intelligent** - reagiert auf Performance-Änderungen
- ✅ **Automatisch** - keine manuelle Anpassung nötig

**Nachteile:**
- ❌ **Komplex** - schwieriger zu implementieren und debuggen
- ❌ **Unvorhersagbar** - Intervalle können sich unerwartet ändern
- ❌ **Risiko** - wichtige Sensoren könnten zu langsam werden
- ❌ **Debugging-schwierig** - variable Verhalten schwer nachvollziehbar

#### **C) Hybrid-Ansatz (Empfehlung)**
```python
# Statische Basis-Konfiguration + dynamische Anpassung
LAMBDA_SENSOR_UPDATE_INTERVALS = {
    "error_state": 10,      # Basis-Intervall
    "temperature": 15,      
    "pressure": 30,         
    "statistics": 60,       
    "firmware": 300,        
}

# Dynamische Anpassung nur in begrenztem Rahmen
LAMBDA_DYNAMIC_ADJUSTMENT_ENABLED = True
LAMBDA_MAX_INTERVAL_MULTIPLIER = 3.0  # Maximal 3x langsamer
LAMBDA_MIN_INTERVAL_MULTIPLIER = 0.5  # Maximal 2x schneller
```

**Vorteile:**
- ✅ **Best of both worlds** - statische Basis + dynamische Anpassung
- ✅ **Sicherheit** - wichtige Sensoren werden nicht zu langsam
- ✅ **Flexibilität** - kann auf Probleme reagieren
- ✅ **Kontrollierbar** - Benutzer kann dynamische Anpassung deaktivieren

**Nachteile:**
- ❌ **Komplexer** - mehr Code und Konfiguration
- ❌ **Mehr Parameter** - mehr Einstellungen zu verstehen

## 🎯 **Empfehlung:**

**Für Lambda Heat Pumps empfehle ich Ansatz A (Statische Konfiguration):**

**Begründung:**
1. **Einfachheit** - Wärmepumpen haben vorhersagbare Datenmuster
2. **Stabilität** - Kritische Sensoren (error_state, temperature) brauchen konstante Updates
3. **Debugging** - Bei Problemen ist konstantes Verhalten leichter zu analysieren
4. **Benutzerfreundlichkeit** - Klare, verständliche Konfiguration

**Implementierung:**
- Sensor-spezifische Intervalle in `const.py`
- Kategorisierung der Sensoren nach Wichtigkeit
- Anti-Synchronisation für Multi-Client-Umgebungen
- Optional: Dynamische Anpassung nur für unwichtige Sensoren

**Das würde die Timeout-Probleme deutlich reduzieren, ohne die Komplexität zu erhöhen!** 🚀

### 2. Statische Update-Häufigkeit implementieren

**Status:** Offen - Implementierung geplant

**Ziel:** Sensor-spezifische Update-Intervalle in `const.py` konfigurieren, um Modbus-Konflikte und Timeouts zu reduzieren.

**Implementierung in `const.py`:**
```python
# Sensor-spezifische Update-Intervalle (in Sekunden)
# Reduziert Modbus-Konflikte durch unterschiedliche Frequenzen
LAMBDA_SENSOR_UPDATE_INTERVALS = {
    "error_state": 10,      # Kritische Sensoren - sofortige Updates
    "temperature": 15,      # Wichtige Sensoren - schnelle Updates  
    "pressure": 30,         # Standard-Sensoren - normale Updates
    "statistics": 60,       # Stabile Sensoren - langsame Updates
    "firmware": 300,        # Selten ändernde Sensoren - minimale Updates
}

# Sensor-Kategorisierung für automatische Zuordnung
LAMBDA_SENSOR_CATEGORIES = {
    # Kritische Sensoren (10s)
    "error_state": "error_state",
    "alarm_state": "error_state",
    "fault_code": "error_state",
    
    # Wichtige Sensoren (15s)
    "temperature": "temperature",
    "flow_temperature": "temperature",
    "return_temperature": "temperature",
    "room_temperature": "temperature",
    
    # Standard-Sensoren (30s)
    "pressure": "pressure",
    "flow_rate": "pressure",
    "power": "pressure",
    "efficiency": "pressure",
    
    # Stabile Sensoren (60s)
    "statistics": "statistics",
    "energy_total": "statistics",
    "runtime_hours": "statistics",
    
    # Selten ändernde Sensoren (300s)
    "firmware": "firmware",
    "serial_number": "firmware",
    "model": "firmware",
}

# Fallback für unbekannte Sensoren
LAMBDA_DEFAULT_UPDATE_INTERVAL = 30
```

**Implementierung in `coordinator.py`:**
```python
def get_update_interval_for_sensor(sensor_type: str) -> int:
    """Ermittelt das Update-Intervall für einen Sensor-Typ."""
    category = LAMBDA_SENSOR_CATEGORIES.get(sensor_type, "pressure")
    return LAMBDA_SENSOR_UPDATE_INTERVALS.get(category, LAMBDA_DEFAULT_UPDATE_INTERVAL)

# In __init__:
self.sensor_update_intervals = {}
for sensor_type in self.sensor_types:
    interval = get_update_interval_for_sensor(sensor_type)
    self.sensor_update_intervals[sensor_type] = interval
    _LOGGER.info(f"📊 UPDATE-INTERVAL: {sensor_type} -> {interval}s")
```

**Erwartete Verbesserungen:**
- ✅ **Weniger Modbus-Konflikte** - verschiedene Frequenzen verhindern Kollisionen
- ✅ **Reduzierte Timeouts** - weniger Last auf Lambda Wärmepumpe
- ✅ **Bessere Performance** - kritische Sensoren (error_state) werden schneller aktualisiert
- ✅ **Einfache Konfiguration** - Benutzer kann Intervalle in `const.py` anpassen
- ✅ **Anti-Synchronisation** - verschiedene Intervalle verhindern Multi-Client-Konflikte

**Priorität:** Hoch - würde die aktuellen Timeout-Probleme deutlich reduzieren

## 🧪 **Test-Suite Übersicht**

### **Neue Test-Datei: `test_individual_reads.py`**
- **20+ Test-Cases** für Individual-Reads und Timeout-Adjustments
- **Konfiguration Tests** - Validierung der `const.py` Einstellungen
- **Timeout-Adjustment Tests** - Prüfung der sensor-spezifischen Timeouts
- **Dynamische Individual-Reads Tests** - Schwellenwert-Logik und automatische Aufnahme
- **Integration Tests** - Coordinator-Initialisierung und Feature-Integration
- **Circuit Breaker Tests** - Integration mit Robustheits-Features

### **Bestehende Test-Dateien:**
- **`test_utils_robustness.py`** - Exponential Backoff und Retry-Logik
- **`test_coordinator.py`** - Coordinator-Funktionalität
- **`test_circuit_breaker.py`** - Circuit Breaker Pattern
- **`test_offline_manager.py`** - Offline-Daten-Management

### **Test-Ausführung:**
```bash
# Alle Tests ausführen
pytest tests/

# Nur Individual-Reads Tests
pytest tests/test_individual_reads.py

# Mit Coverage
pytest tests/ --cov=custom_components.lambda_heat_pumps
```