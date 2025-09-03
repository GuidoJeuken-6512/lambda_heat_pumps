# Lambda Heat Pumps Integration - Robustheit Verbesserungen

## Übersicht

Dieses Dokument beschreibt geplante Verbesserungen zur Erhöhung der Robustheit der Lambda Wärmepumpen Integration bei Netzwerkunterbrechungen und Verbindungsproblemen.

## Konfiguration

Die Robustheits-Features werden über die `lambda_wp_config.yaml` konfiguriert:

> **⚠️ Wichtig:** Wenn Sie die Robustheits-Features aktivieren, müssen Sie die `version` in der `lambda_wp_config.yaml` auf `3` erhöhen, damit die Migration korrekt durchgeführt wird.

```yaml
robustness:
  # Exponential Backoff für Retry-Versuche
  exponential_backoff:
    enabled: true
    base_delay: 5          # Basis-Verzögerung in Sekunden
    max_delay: 60          # Maximale Verzögerung in Sekunden
    jitter_factor: 0.2     # Jitter-Faktor (±20% Zufallsschwankung)
  
  # Circuit Breaker Pattern
  circuit_breaker:
    enabled: true
    failure_threshold: 5   # Anzahl Fehler bis Circuit öffnet
    recovery_timeout: 300  # Wartezeit bis Test-Versuch (5 Minuten)
    half_open_max_requests: 3  # Max. Requests im HALF_OPEN Zustand
  
  # Offline-Datenbehandlung
  offline_data:
    enabled: true
    max_offline_duration: 3600  # Max. Offline-Dauer in Sekunden (1 Stunde)
    cache_file: "offline_data_cache.json"
    preserve_last_values: true  # Letzte Werte bei Offline-Zustand beibehalten
  
  # Adaptive Update-Intervalle
  adaptive_intervals:
    enabled: true
    base_interval: 30      # Basis-Update-Intervall in Sekunden
    min_interval: 10       # Minimum-Intervall in Sekunden
    max_interval: 300      # Maximum-Intervall in Sekunden (5 Minuten)
    stability_threshold: 5 # Anzahl erfolgreicher Updates für Stabilität
    adjustment_cooldown: 60 # Cooldown zwischen Anpassungen in Sekunden
  
  # Health-Monitoring
  health_monitoring:
    enabled: false         # Standardmäßig deaktiviert (Performance)
    max_history: 100       # Maximale Anzahl gespeicherter Metriken
    health_check_interval: 300  # Health-Check-Intervall in Sekunden
    quality_score_threshold: 70 # Mindest-Quality-Score für "gut"
```

## Priorität: HOCH

### 1. Exponential Backoff implementieren

**Problem:** Aktuell wird eine feste 5-Sekunden-Verzögerung zwischen Retry-Versuchen verwendet, was bei anhaltenden Netzwerkproblemen ineffizient ist.

**Lösung:** Exponential Backoff mit Jitter implementieren.

**Implementierung:**
```python
# In const.py - Timeout-Konstanten zentralisieren
LAMBDA_MODBUS_TIMEOUT = 3  # Reduziert von 60 auf 3 Sekunden für bessere Responsivität
LAMBDA_MODBUS_TIMEOUT_FAST = 1  # Schneller Timeout für Health-Checks
LAMBDA_MODBUS_TIMEOUT_SLOW = 10  # Längerer Timeout für kritische Operationen

# In modbus_utils.py - async_read_holding_registers()
import random

async def async_read_holding_registers_with_backoff(client, address, count, slave_id):
    last_exception = None
    
    for attempt in range(LAMBDA_MAX_RETRIES):
        try:
            return await asyncio.wait_for(
                client.read_holding_registers(address, count=count, slave=slave_id),
                timeout=LAMBDA_MODBUS_TIMEOUT  # Verwendet zentralisierte Konstante
            )
        except Exception as e:
            last_exception = e
            if attempt < LAMBDA_MAX_RETRIES - 1:
                # Exponential backoff mit Jitter
                base_delay = LAMBDA_RETRY_DELAY * (2 ** attempt)
                max_delay = 60  # Maximum 60 Sekunden
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

### 1.1. Konstanten-Zentralisierung

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
LAMBDA_MODBUS_TIMEOUT = 3  # Standard-Timeout (reduziert von 60s)
LAMBDA_MODBUS_TIMEOUT_FAST = 1  # Schneller Timeout für Health-Checks
LAMBDA_MODBUS_TIMEOUT_SLOW = 10  # Längerer Timeout für kritische Operationen

# Retry-Konstanten
LAMBDA_MAX_RETRIES = 3      # Maximum retry attempts
LAMBDA_RETRY_DELAY = 5      # Delay between retries in seconds

# Modbus-Konstanten
LAMBDA_MODBUS_UNIT_ID = 1   # Lambda Unit ID
LAMBDA_MODBUS_PORT = 502    # Standard Modbus TCP port
```

**Weitere zu zentralisierende Konstanten:**
```python
# In coordinator.py (PROBLEMATISCH)
self._max_batch_failures = 3  # Nach 3 Fehlern auf Individual-Reads umstellen
self._max_cycling_warnings = 3  # Nach 3 Warnings unterdrücken

# In const.py (NEU)
LAMBDA_MAX_BATCH_FAILURES = 3  # Nach 3 Fehlern auf Individual-Reads umstellen
LAMBDA_MAX_CYCLING_WARNINGS = 3  # Nach 3 Warnings unterdrücken
LAMBDA_MODBUS_SAFETY_MARGIN = 120  # Modbus safety margin für Batch-Reads
```

**Vorteile der Zentralisierung:**
- ✅ **Einheitliche Konfiguration** - Alle Konstanten an einem Ort
- ✅ **Einfache Anpassung** - Timeout-Werte zentral änderbar
- ✅ **Keine Duplikate** - Vermeidet Inkonsistenzen
- ✅ **Bessere Wartbarkeit** - Klare Struktur
- ✅ **Konfigurierbarkeit** - Konstanten können später in YAML ausgelagert werden

### 1.2. Gefundene Konstanten außerhalb von const.py

**Analyse der aktuellen Codebase zeigt folgende Konstanten, die zentralisiert werden sollten:**

#### **In modbus_utils.py (Duplikate):**
```python
# PROBLEMATISCH: Duplikate von const.py
LAMBDA_MODBUS_TIMEOUT = 60  # Sollte aus const.py importiert werden
LAMBDA_MODBUS_UNIT_ID = 1   # Sollte aus const.py importiert werden
LAMBDA_MAX_RETRIES = 3      # Sollte aus const.py importiert werden
LAMBDA_RETRY_DELAY = 5      # Sollte aus const.py importiert werden
```

#### **In coordinator.py (Hardcoded):**
```python
# PROBLEMATISCH: Hardcoded Konstanten
self._max_batch_failures = 3  # Nach 3 Fehlern auf Individual-Reads umstellen
self._max_cycling_warnings = 3  # Nach 3 Warnings unterdrücken
# In Batch-Read-Logik:
or len(current_batch) >= 120  # Modbus safety margin
```

#### **In const_migration.py (Migration-spezifisch):**
```python
# OK: Migration-spezifische Konstanten (können bleiben)
MIGRATION_BACKUP_RETENTION_DAYS = 30
CLEANUP_INTERVAL_DAYS = 7
CLEANUP_MIN_FREE_SPACE_MB = 100
MIGRATION_TIMEOUT_SECONDS = 300
BACKUP_TIMEOUT_SECONDS = 60
CLEANUP_TIMEOUT_SECONDS = 120
MIGRATION_MAX_RETRIES = 3
MIGRATION_RETRY_DELAY_SECONDS = 5
```

#### **Empfohlene Zentralisierung:**
```python
# In const.py - Neue Konstanten hinzufügen
# Batch-Read-Konstanten
LAMBDA_MAX_BATCH_FAILURES = 3  # Nach 3 Fehlern auf Individual-Reads umstellen
LAMBDA_MAX_CYCLING_WARNINGS = 3  # Nach 3 Warnings unterdrücken
LAMBDA_MODBUS_SAFETY_MARGIN = 120  # Modbus safety margin für Batch-Reads

# Timeout-Konstanten (erweitert)
LAMBDA_MODBUS_TIMEOUT = 3  # Standard-Timeout (reduziert von 60s)
LAMBDA_MODBUS_TIMEOUT_FAST = 1  # Schneller Timeout für Health-Checks
LAMBDA_MODBUS_TIMEOUT_SLOW = 10  # Längerer Timeout für kritische Operationen
LAMBDA_MODBUS_TIMEOUT_BATCH = 5  # Timeout für Batch-Reads
```

#### **Implementierungsplan:**
1. **Konstanten in const.py hinzufügen**
2. **Duplikate in modbus_utils.py entfernen**
3. **Hardcoded Werte in coordinator.py ersetzen**
4. **Imports in allen Dateien anpassen**
5. **Tests aktualisieren**

### 2. Circuit Breaker Logik

**Problem:** Bei anhaltenden Verbindungsproblemen werden weiterhin Versuche unternommen, was Ressourcen verschwendet.

**Lösung:** Circuit Breaker Pattern implementieren, das bei wiederholten Fehlern die Verbindung temporär "öffnet".

**Implementierung:**
```python
# Neue Datei: circuit_breaker.py
import time
import logging
from enum import Enum
from typing import Callable, Any

_LOGGER = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, no requests allowed
    HALF_OPEN = "half_open"  # Testing if service is back

class CircuitBreaker:
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 300,  # 5 Minuten
                 expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        
    def can_execute(self) -> bool:
        """Prüft ob eine Ausführung erlaubt ist."""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            # Prüfe ob Recovery-Timeout abgelaufen ist
            if (self.last_failure_time and 
                time.time() - self.last_failure_time > self.recovery_timeout):
                self.state = CircuitState.HALF_OPEN
                _LOGGER.info("Circuit breaker transitioning to HALF_OPEN state")
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self):
        """Registriert erfolgreiche Ausführung."""
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            _LOGGER.info("Circuit breaker transitioning to CLOSED state - service recovered")
    
    def record_failure(self, exception: Exception):
        """Registriert fehlgeschlagene Ausführung."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            _LOGGER.warning(
                "Circuit breaker OPENED after %d failures. "
                "Will retry in %d seconds. Last error: %s",
                self.failure_count, self.recovery_timeout, exception
            )
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Führt Funktion mit Circuit Breaker aus."""
        if not self.can_execute():
            raise Exception(f"Circuit breaker is OPEN. Last failure: {self.last_failure_time}")
        
        try:
            result = await func(*args, **kwargs)
            self.record_success()
            return result
        except self.expected_exception as e:
            self.record_failure(e)
            raise
```

**Integration in Coordinator:**
```python
# In coordinator.py
from .circuit_breaker import CircuitBreaker

class LambdaDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        # ... existing code ...
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,      # Nach 5 Fehlern öffnen
            recovery_timeout=300,     # 5 Minuten warten
            expected_exception=Exception
        )
    
    async def _async_update_data(self):
        try:
            # Prüfe Circuit Breaker vor Datenabfrage
            if not self.circuit_breaker.can_execute():
                _LOGGER.warning("Circuit breaker is OPEN, skipping data update")
                return self.data  # Verwende letzte bekannte Daten
            
            # ... existing data fetching code ...
            
        except Exception as ex:
            self.circuit_breaker.record_failure(ex)
            raise
```

**Wie prüfen wir den Status:**
- **CLOSED:** Normale Operation, alle Requests werden durchgelassen
- **OPEN:** Nach 5 aufeinanderfolgenden Fehlern, keine Requests für 5 Minuten
- **HALF_OPEN:** Nach 5 Minuten wird ein Test-Request gemacht
- **Zurück zu CLOSED:** Wenn Test-Request erfolgreich ist

**Wie gehen wir wieder online:**
1. Nach 5 Minuten (recovery_timeout) wechselt Circuit zu HALF_OPEN
2. Ein Test-Request wird gemacht (Health Check)
3. Bei Erfolg: Circuit wird CLOSED, normale Operation
4. Bei Fehler: Circuit bleibt OPEN für weitere 5 Minuten

### 3. Offline-Behandlung - Letzte Werte weiterschreiben

**Problem:** Bei Netzwerkausfällen werden alle Sensoren "unavailable", auch wenn letzte bekannte Werte verfügbar sind.

**Lösung:** Offline-Datenmanager implementieren, der letzte bekannte Werte bereitstellt.

**Implementierung:**
```python
# Neue Datei: offline_manager.py
import json
import os
import time
import logging
from typing import Dict, Any, Optional
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

class OfflineDataManager:
    def __init__(self, hass: HomeAssistant, config_path: str):
        self.hass = hass
        self.config_path = config_path
        self.cache_file = os.path.join(config_path, "offline_data_cache.json")
        self.last_known_data = {}
        self.offline_since = None
        self.max_offline_duration = 3600  # 1 Stunde
        
    async def load_cached_data(self):
        """Lädt gecachte Daten beim Start."""
        try:
            if os.path.exists(self.cache_file):
                def _read_cache():
                    with open(self.cache_file, 'r') as f:
                        return json.load(f)
                
                cached_data = await self.hass.async_add_executor_job(_read_cache)
                self.last_known_data = cached_data.get('data', {})
                self.offline_since = cached_data.get('offline_since')
                
                if self.offline_since:
                    offline_duration = time.time() - self.offline_since
                    _LOGGER.info(
                        "Loaded cached data from offline period of %.1f minutes",
                        offline_duration / 60
                    )
        except Exception as e:
            _LOGGER.error("Failed to load cached data: %s", e)
    
    async def save_cached_data(self, data: Dict[str, Any]):
        """Speichert aktuelle Daten im Cache."""
        try:
            cache_data = {
                'data': data,
                'timestamp': time.time(),
                'offline_since': self.offline_since
            }
            
            def _write_cache():
                with open(self.cache_file, 'w') as f:
                    json.dump(cache_data, f, indent=2)
            
            await self.hass.async_add_executor_job(_write_cache)
            self.last_known_data = data.copy()
            
        except Exception as e:
            _LOGGER.error("Failed to save cached data: %s", e)
    
    def handle_offline_state(self) -> Dict[str, Any]:
        """Behandelt Offline-Zustand und gibt letzte bekannte Daten zurück."""
        if not self.offline_since:
            self.offline_since = time.time()
            _LOGGER.warning("Lambda device went offline, using cached data")
        
        # Prüfe ob Offline-Dauer zu lang ist
        offline_duration = time.time() - self.offline_since
        if offline_duration > self.max_offline_duration:
            _LOGGER.warning(
                "Device offline for %.1f hours, marking sensors as unavailable",
                offline_duration / 3600
            )
            return {}  # Leere Daten = unavailable
        
        # Erstelle "Offline"-Daten mit Zeitstempel
        offline_data = {}
        for key, value in self.last_known_data.items():
            if isinstance(value, (int, float)):
                # Für numerische Werte: Behalte letzten Wert
                offline_data[key] = value
            else:
                # Für andere Werte: Behalte auch
                offline_data[key] = value
        
        # Füge Offline-Status hinzu
        offline_data['_offline_since'] = self.offline_since
        offline_data['_offline_duration'] = offline_duration
        
        return offline_data
    
    def handle_online_state(self):
        """Behandelt Rückkehr zum Online-Zustand."""
        if self.offline_since:
            offline_duration = time.time() - self.offline_since
            _LOGGER.info(
                "Lambda device back online after %.1f minutes offline",
                offline_duration / 60
            )
            self.offline_since = None
    
    def is_offline(self) -> bool:
        """Prüft ob Gerät offline ist."""
        return self.offline_since is not None
    
    def get_offline_duration(self) -> Optional[float]:
        """Gibt Offline-Dauer in Sekunden zurück."""
        if self.offline_since:
            return time.time() - self.offline_since
        return None
```

**Integration in Coordinator:**
```python
# In coordinator.py
from .offline_manager import OfflineDataManager

class LambdaDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        # ... existing code ...
        self.offline_manager = OfflineDataManager(hass, self._config_path)
    
    async def async_init(self):
        # ... existing code ...
        await self.offline_manager.load_cached_data()
    
    async def _async_update_data(self):
        try:
            # ... existing connection and data fetching code ...
            
            # Bei erfolgreicher Datenabfrage
            if data:
                await self.offline_manager.save_cached_data(data)
                self.offline_manager.handle_online_state()
                return data
            
        except Exception as ex:
            _LOGGER.error("Error updating data: %s", ex)
            
            # Bei Fehler: Verwende Offline-Daten
            offline_data = self.offline_manager.handle_offline_state()
            if offline_data:
                _LOGGER.info("Using cached data due to connection error")
                return offline_data
            
            # Wenn keine Offline-Daten verfügbar, werfe Fehler
            raise UpdateFailed(f"Error fetching Lambda data: {ex}")
```

**Sensor-Anpassung für Offline-Daten:**
```python
# In sensor.py - LambdaSensor Klasse
@property
def available(self) -> bool:
    """Return if entity is available."""
    if not self.coordinator.last_update_success:
        # Prüfe ob Offline-Daten verfügbar sind
        if hasattr(self.coordinator, 'offline_manager'):
            return not self.coordinator.offline_manager.is_offline()
        return False
    return True

@property
def state(self):
    """Return the state of the sensor."""
    if not self.available:
        return None
    
    # Wenn Offline-Daten verwendet werden, markiere entsprechend
    if (hasattr(self.coordinator, 'offline_manager') and 
        self.coordinator.offline_manager.is_offline()):
        # Für Offline-Sensoren: Zeige letzten Wert mit Hinweis
        value = self.coordinator.data.get(self._sensor_id)
        if value is not None:
            return value
    
    return self.coordinator.data.get(self._sensor_id)
```

## Priorität: MITTEL

### 4. Adaptive Update-Intervalle

**Problem:** Feste 30-Sekunden-Update-Intervalle sind bei stabilen Verbindungen zu langsam und bei instabilen Verbindungen zu aggressiv.

**Lösung:** Dynamische Anpassung der Update-Intervalle basierend auf Verbindungsqualität.

**Implementierung:**
```python
# Neue Datei: adaptive_intervals.py
import time
import logging
from typing import Dict, Any
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

class AdaptiveIntervalManager:
    def __init__(self, 
                 base_interval: int = 30,
                 min_interval: int = 10,
                 max_interval: int = 300,
                 stability_threshold: int = 5):
        self.base_interval = base_interval
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.stability_threshold = stability_threshold
        
        self.current_interval = base_interval
        self.consecutive_successes = 0
        self.consecutive_failures = 0
        self.last_adjustment_time = time.time()
        self.adjustment_cooldown = 60  # 1 Minute zwischen Anpassungen
        
        # Metriken für Verbindungsqualität
        self.latency_history = []
        self.error_history = []
        self.max_history_size = 10
    
    def record_success(self, latency: float = None):
        """Registriert erfolgreichen Update."""
        self.consecutive_successes += 1
        self.consecutive_failures = 0
        
        if latency is not None:
            self.latency_history.append(latency)
            if len(self.latency_history) > self.max_history_size:
                self.latency_history.pop(0)
        
        self._adjust_interval()
    
    def record_failure(self, error_type: str = "unknown"):
        """Registriert fehlgeschlagene Update."""
        self.consecutive_failures += 1
        self.consecutive_successes = 0
        
        self.error_history.append({
            'type': error_type,
            'timestamp': time.time()
        })
        if len(self.error_history) > self.max_history_size:
            self.error_history.pop(0)
        
        self._adjust_interval()
    
    def _adjust_interval(self):
        """Passt Update-Intervall basierend auf Verbindungsqualität an."""
        current_time = time.time()
        
        # Cooldown zwischen Anpassungen
        if current_time - self.last_adjustment_time < self.adjustment_cooldown:
            return
        
        old_interval = self.current_interval
        
        # Bei stabiler Verbindung: Intervall reduzieren
        if self.consecutive_successes >= self.stability_threshold:
            # Berechne durchschnittliche Latenz
            avg_latency = sum(self.latency_history) / len(self.latency_history) if self.latency_history else 0
            
            if avg_latency < 1.0:  # Sehr schnelle Verbindung
                self.current_interval = max(self.min_interval, self.current_interval - 5)
            elif avg_latency < 2.0:  # Gute Verbindung
                self.current_interval = max(self.min_interval, self.current_interval - 2)
            else:  # Langsamere Verbindung
                self.current_interval = max(self.min_interval, self.current_interval - 1)
        
        # Bei Problemen: Intervall erhöhen
        elif self.consecutive_failures >= 2:
            if self.consecutive_failures >= 5:  # Viele Fehler
                self.current_interval = min(self.max_interval, self.current_interval + 60)
            elif self.consecutive_failures >= 3:  # Einige Fehler
                self.current_interval = min(self.max_interval, self.current_interval + 30)
            else:  # Wenige Fehler
                self.current_interval = min(self.max_interval, self.current_interval + 15)
        
        # Logge Änderungen
        if self.current_interval != old_interval:
            _LOGGER.info(
                "Update interval adjusted: %ds -> %ds (successes: %d, failures: %d)",
                old_interval, self.current_interval, 
                self.consecutive_successes, self.consecutive_failures
            )
            self.last_adjustment_time = current_time
    
    def get_current_interval(self) -> int:
        """Gibt aktuelles Update-Intervall zurück."""
        return self.current_interval
    
    def get_connection_quality(self) -> Dict[str, Any]:
        """Gibt Verbindungsqualitäts-Metriken zurück."""
        avg_latency = sum(self.latency_history) / len(self.latency_history) if self.latency_history else 0
        
        return {
            'current_interval': self.current_interval,
            'consecutive_successes': self.consecutive_successes,
            'consecutive_failures': self.consecutive_failures,
            'average_latency': avg_latency,
            'recent_errors': len(self.error_history),
            'quality_score': self._calculate_quality_score()
        }
    
    def _calculate_quality_score(self) -> float:
        """Berechnet Verbindungsqualitäts-Score (0-100)."""
        score = 100.0
        
        # Abzug für Fehler
        score -= min(50, self.consecutive_failures * 10)
        
        # Abzug für hohe Latenz
        if self.latency_history:
            avg_latency = sum(self.latency_history) / len(self.latency_history)
            score -= min(30, avg_latency * 10)
        
        # Bonus für stabile Verbindung
        if self.consecutive_successes >= self.stability_threshold:
            score += min(20, self.consecutive_successes * 2)
        
        return max(0, min(100, score))
```

**Integration in Coordinator:**
```python
# In coordinator.py
from .adaptive_intervals import AdaptiveIntervalManager

class LambdaDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        # ... existing code ...
        self.adaptive_intervals = AdaptiveIntervalManager(
            base_interval=entry.options.get("update_interval", DEFAULT_UPDATE_INTERVAL),
            min_interval=10,   # Minimum 10 Sekunden
            max_interval=300   # Maximum 5 Minuten
        )
        
        # Überschreibe update_interval mit adaptivem Intervall
        super().__init__(
            hass,
            _LOGGER,
            name="Lambda Coordinator",
            update_interval=timedelta(seconds=self.adaptive_intervals.get_current_interval()),
        )
    
    async def _async_update_data(self):
        start_time = time.time()
        
        try:
            # ... existing data fetching code ...
            
            # Bei Erfolg: Registriere Erfolg mit Latenz
            latency = (time.time() - start_time) * 1000  # in ms
            self.adaptive_intervals.record_success(latency)
            
            # Aktualisiere Update-Intervall falls nötig
            new_interval = self.adaptive_intervals.get_current_interval()
            if new_interval != self.update_interval.total_seconds():
                self.update_interval = timedelta(seconds=new_interval)
                _LOGGER.debug("Updated coordinator interval to %d seconds", new_interval)
            
            return data
            
        except Exception as ex:
            # Bei Fehler: Registriere Fehler
            self.adaptive_intervals.record_failure(str(type(ex).__name__))
            
            # Erhöhe Update-Intervall bei Problemen
            new_interval = self.adaptive_intervals.get_current_interval()
            if new_interval != self.update_interval.total_seconds():
                self.update_interval = timedelta(seconds=new_interval)
                _LOGGER.debug("Updated coordinator interval to %d seconds due to errors", new_interval)
            
            raise
```

**Erklärung der adaptiven Update-Intervalle:**

1. **Basis-Intervall:** 30 Sekunden (konfigurierbar)
2. **Minimum-Intervall:** 10 Sekunden (bei sehr stabiler Verbindung)
3. **Maximum-Intervall:** 5 Minuten (bei anhaltenden Problemen)

**Anpassungslogik:**
- **Bei stabiler Verbindung (5+ erfolgreiche Updates):**
  - Latenz < 1s: Intervall um 5s reduzieren
  - Latenz < 2s: Intervall um 2s reduzieren
  - Latenz > 2s: Intervall um 1s reduzieren

- **Bei Problemen (2+ aufeinanderfolgende Fehler):**
  - 2 Fehler: Intervall um 15s erhöhen
  - 3 Fehler: Intervall um 30s erhöhen
  - 5+ Fehler: Intervall um 60s erhöhen

- **Cooldown:** 1 Minute zwischen Anpassungen

**Vorteile:**
- Bessere Performance bei stabiler Verbindung
- Reduzierte Netzwerklast bei Problemen
- Automatische Anpassung an Verbindungsqualität
- Verhindert Überlastung des Lambda-Geräts

## Priorität: NIEDRIG

### 5. Erweiterte Health-Monitoring

**Implementierung:** Umfassende Überwachung der Verbindungsqualität mit Metriken.

```python
# Neue Datei: health_monitor.py
import time
import statistics
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class HealthMetrics:
    latency: float
    packet_loss: float
    connection_stable: bool
    error_rate: float
    quality_score: float

class HealthMonitor:
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.latency_history: List[float] = []
        self.error_history: List[Dict[str, Any]] = []
        self.connection_history: List[bool] = []
    
    async def perform_health_check(self, coordinator) -> HealthMetrics:
        """Führt umfassende Gesundheitsprüfung durch."""
        start_time = time.time()
        
        try:
            # Test-Read mit Latenz-Messung
            result = await asyncio.wait_for(
                coordinator.client.read_holding_registers(0, count=1, slave=coordinator.slave_id),
                timeout=5
            )
            
            latency = (time.time() - start_time) * 1000
            connection_stable = result is not None and not result.isError()
            
        except Exception as e:
            latency = 5000  # 5 Sekunden Timeout
            connection_stable = False
            self.error_history.append({
                'timestamp': time.time(),
                'error': str(e),
                'type': type(e).__name__
            })
        
        # Aktualisiere Historie
        self.latency_history.append(latency)
        self.connection_history.append(connection_stable)
        
        # Begrenze Historie
        if len(self.latency_history) > self.max_history:
            self.latency_history.pop(0)
        if len(self.connection_history) > self.max_history:
            self.connection_history.pop(0)
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)
        
        # Berechne Metriken
        avg_latency = statistics.mean(self.latency_history) if self.latency_history else 0
        error_rate = len(self.error_history) / max(1, len(self.connection_history)) * 100
        connection_stability = sum(self.connection_history) / len(self.connection_history) * 100 if self.connection_history else 0
        
        # Berechne Quality Score
        quality_score = self._calculate_quality_score(avg_latency, error_rate, connection_stability)
        
        return HealthMetrics(
            latency=avg_latency,
            packet_loss=error_rate,
            connection_stable=connection_stability > 80,
            error_rate=error_rate,
            quality_score=quality_score
        )
    
    def _calculate_quality_score(self, latency: float, error_rate: float, stability: float) -> float:
        """Berechnet Gesamt-Qualitäts-Score."""
        score = 100.0
        
        # Latenz-Bewertung (0-40 Punkte)
        if latency < 100:
            score -= 0
        elif latency < 500:
            score -= 10
        elif latency < 1000:
            score -= 20
        else:
            score -= 40
        
        # Fehlerrate-Bewertung (0-40 Punkte)
        score -= min(40, error_rate * 2)
        
        # Stabilität-Bewertung (0-20 Punkte)
        score -= max(0, 20 - stability * 0.2)
        
        return max(0, min(100, score))
```

## Migration und Versionsverwaltung

### Automatische Migration

Die Integration erkennt automatisch, wenn die `lambda_wp_config.yaml` auf Version 3 aktualisiert wird und führt die notwendigen Migrationen durch:

1. **Backup der bestehenden Konfiguration** wird erstellt
2. **Neue Robustheits-Sektion** wird hinzugefügt (falls nicht vorhanden)
3. **Standardwerte** werden für fehlende Optionen gesetzt
4. **Kompatibilität** mit bestehenden Konfigurationen wird gewährleistet

### Versionshistorie

- **Version 1:** Grundlegende Konfiguration
- **Version 2:** Cycling-Offsets und Sensor-Overrides
- **Version 3:** Robustheits-Features (Exponential Backoff, Circuit Breaker, Offline-Daten, Adaptive Intervalle)

### Manuelle Migration

Falls die automatische Migration nicht funktioniert, können Sie die Robustheits-Konfiguration manuell hinzufügen:

```yaml
# Fügen Sie diese Sektion zu Ihrer lambda_wp_config.yaml hinzu:
robustness:
  exponential_backoff:
    enabled: true
    base_delay: 5
    max_delay: 60
    jitter_factor: 0.2
  # ... weitere Optionen siehe oben

# Erhöhen Sie die Version:
version: 3
```

## Implementierungsreihenfolge

1. **Phase 1 (Sofort):** Exponential Backoff
2. **Phase 2 (1-2 Wochen):** Offline-Datenmanager
3. **Phase 3 (2-3 Wochen):** Circuit Breaker
4. **Phase 4 (3-4 Wochen):** Adaptive Update-Intervalle
5. **Phase 5 (Optional):** Erweiterte Health-Monitoring

## Testing

Für jede Verbesserung sollten umfassende Tests implementiert werden:

```python
# tests/test_robustness.py
import pytest
import asyncio
from unittest.mock import AsyncMock, patch

class TestRobustnessImprovements:
    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """Test exponential backoff behavior."""
        # Mock network failures
        # Verify backoff timing
        pass
    
    @pytest.mark.asyncio
    async def test_circuit_breaker(self):
        """Test circuit breaker functionality."""
        # Mock consecutive failures
        # Verify circuit opening/closing
        pass
    
    @pytest.mark.asyncio
    async def test_offline_data_manager(self):
        """Test offline data handling."""
        # Mock network disconnection
        # Verify cached data usage
        pass
    
    @pytest.mark.asyncio
    async def test_adaptive_intervals(self):
        """Test adaptive interval adjustment."""
        # Mock connection quality changes
        # Verify interval adjustments
        pass
```

## Konfigurationsoptionen

Die Robustheits-Features werden über die `lambda_wp_config.yaml` konfiguriert. Alle Einstellungen sind optional und haben sinnvolle Standardwerte.

### Verfügbare Konfigurationsoptionen:

- **exponential_backoff.enabled**: Aktiviert/deaktiviert Exponential Backoff
- **exponential_backoff.base_delay**: Basis-Verzögerung für Retry-Versuche
- **exponential_backoff.max_delay**: Maximale Verzögerung (verhindert zu lange Wartezeiten)
- **exponential_backoff.jitter_factor**: Zufallsschwankung zur Vermeidung von Synchronisation

- **circuit_breaker.enabled**: Aktiviert/deaktiviert Circuit Breaker Pattern
- **circuit_breaker.failure_threshold**: Anzahl Fehler bis Circuit öffnet
- **circuit_breaker.recovery_timeout**: Wartezeit bis Test-Versuch
- **circuit_breaker.half_open_max_requests**: Max. Requests im HALF_OPEN Zustand

- **offline_data.enabled**: Aktiviert/deaktiviert Offline-Datenbehandlung
- **offline_data.max_offline_duration**: Maximale Offline-Dauer (danach unavailable)
- **offline_data.cache_file**: Dateiname für Offline-Cache
- **offline_data.preserve_last_values**: Letzte Werte bei Offline-Zustand beibehalten

- **adaptive_intervals.enabled**: Aktiviert/deaktiviert adaptive Update-Intervalle
- **adaptive_intervals.base_interval**: Basis-Update-Intervall
- **adaptive_intervals.min_interval**: Minimum-Intervall (bei stabiler Verbindung)
- **adaptive_intervals.max_interval**: Maximum-Intervall (bei Problemen)
- **adaptive_intervals.stability_threshold**: Anzahl erfolgreicher Updates für Stabilität
- **adaptive_intervals.adjustment_cooldown**: Cooldown zwischen Anpassungen

- **health_monitoring.enabled**: Aktiviert/deaktiviert erweiterte Health-Monitoring
- **health_monitoring.max_history**: Maximale Anzahl gespeicherter Metriken
- **health_monitoring.health_check_interval**: Health-Check-Intervall
- **health_monitoring.quality_score_threshold**: Mindest-Quality-Score für "gut"

## Monitoring und Logging

Erweiterte Logging-Funktionen für bessere Überwachung:

```python
# Neue Logging-Kategorien
_LOGGER_ROBUSTNESS = logging.getLogger(f"{__name__}.robustness")
_LOGGER_CIRCUIT = logging.getLogger(f"{__name__}.circuit_breaker")
_LOGGER_OFFLINE = logging.getLogger(f"{__name__}.offline")
_LOGGER_ADAPTIVE = logging.getLogger(f"{__name__}.adaptive")
```

## Fazit

Diese Verbesserungen werden die Robustheit der Lambda Wärmepumpen Integration erheblich erhöhen und eine zuverlässige Operation auch bei instabilen Netzwerkverbindungen gewährleisten. Die Implementierung sollte schrittweise erfolgen, wobei jede Phase gründlich getestet wird.
