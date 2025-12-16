# Lambda Wärmepumpen Integration für Home Assistant

Die Lambda Wärmepumpen Integration ist eine benutzerdefinierte Komponente für Home Assistant, die eine Verbindung zu Lambda Wärmepumpen über das Modbus TCP/RTU-Protokoll herstellt. Diese Dokumentation beschreibt den Aufbau und die Funktionsweise der Integration.

## Inhaltsverzeichnis

1. [Aufbau der Integration](#aufbau-der-integration)
2. [Typen von Sensoren](#typen-von-sensoren)
3. [Sensor-Initialisierung](#sensor-initialisierung)
4. [Sensor-Abruf](#sensor-abruf)
5. [Konfiguration](#konfiguration)
6. [Funktionsübersicht](#funktionsübersicht)
7. [Modbus-Register-Services](#modbus-register-services)
8. [Dynamische Entity-Erstellung](#dynamische-entity-erstellung)
9. [Template-basierte Climate-Entities](#template-basierte-climate-entities)
10. [Neue Features (Version 1.4.0)](#neue-features-version-140)
11. [Automatische Konfiguration](#automatische-konfiguration)
12. [Energieverbrauchssensoren](#energieverbrauchssensoren)
13. [Cycling-Sensoren](#cycling-sensoren)
14. [Endianness-Konfiguration](#endianness-konfiguration)
15. [Sensor-Wechsel-Erkennung](#sensor-wechsel-erkennung)
16. [Modbus-Tools für Tests](#modbus-tools-für-tests)

## Aufbau der Integration

Die Integration besteht aus folgenden Hauptkomponenten:

- **__init__.py**: Haupteinstiegspunkt der Integration, registriert die Komponente bei Home Assistant
- **config_flow.py**: Benutzeroberfläche für die Konfiguration der Integration
- **const.py**: Konstanten und Konfigurationswerte, einschließlich Sensortypen und Register-Adressen
- **coordinator.py**: Datenkoordinator, der den Datenaustausch mit der Wärmepumpe verwaltet
- **sensor.py**: Implementierung der Sensoren für verschiedene Wärmepumpen-Parameter
- **climate.py**: Implementierung der Klima-Entitäten für Heizung und Warmwasser
- **services.py**: Servicefunktionen, z.B. für den Raumtemperatur-Abruf
- **utils.py**: Hilfsfunktionen für die gesamte Integration

Die Integration unterstützt verschiedene Geräte:
- Bis zu 3 Wärmepumpen (Heat Pumps)
- Bis zu 5 Warmwasserspeicher (Boiler)
- Bis zu 12 Heizkreise (Heating Circuits)
- Bis zu 5 Pufferspeicher (Buffer)
- Bis zu 2 Solaranlagen (Solar)

## Typen von Sensoren

Die Integration unterstützt verschiedene Sensortypen, die in `const.py` definiert sind:

### Allgemeine Sensoren (SENSOR_TYPES)
- Umgebungstemperatur
- Fehler-Nummern
- Betriebszustände
- E-Manager-Werte (Leistungsaufnahme, Sollwerte)

### Wärmepumpen-Sensoren (HP_SENSOR_TEMPLATES)
- Vorlauf- und Rücklauftemperaturen
- Volumenstrom
- Energiequellen-Temperaturen
- Kompressorleistung
- COP (Coefficient of Performance)
- Leistungsaufnahme
- Energieverbrauch

### Warmwasserspeicher-Sensoren (BOIL_SENSOR_TEMPLATES)
- Temperaturen (oben/unten)
- Betriebszustände
- Zirkulation

### Heizkreis-Sensoren (HC_SENSOR_TEMPLATES)
- Vorlauf- und Rücklauftemperaturen
- Raumtemperaturen
- Betriebsmodi
- Sollwerte

### Pufferspeicher-Sensoren (BUFFER_SENSOR_TEMPLATES)
- Temperaturen (oben/unten)
- Betriebszustände
- Anforderungstypen

### Solar-Sensoren (SOLAR_SENSOR_TEMPLATES)
- Kollektortemperaturen
- Speichertemperaturen
- Leistung und Energieertrag

## Sensor-Initialisierung

Die Sensoren werden beim Start der Integration in `sensor.py` initialisiert:

1. Der Datenkoordinator wird geladen
2. Die konfigurierte Firmware-Version wird bestimmt
3. Sensoren werden basierend auf ihrer Kompatibilität mit der Firmware gefiltert
4. Für jede Sensor-Kategorie werden entsprechende Objekte erstellt und registriert
5. Jeder Sensor erhält eine eindeutige ID und wird mit dem Datenkoordinator verbunden

Beispiel aus `sensor.py`:
```python
entities = []
name_prefix = entry.data.get("name", "lambda_wp").lower().replace(" ", "")
prefix = f"{name_prefix}_"

compatible_static_sensors = get_compatible_sensors(SENSOR_TYPES, fw_version)
for sensor_id, sensor_config in compatible_static_sensors.items():
    # Prüfung auf deaktivierte Register
    if coordinator.is_register_disabled(sensor_config["address"]):
        continue
    
    # Entitäten erstellen und hinzufügen
    entities.append(
        LambdaSensor(
            coordinator=coordinator,
            config_entry=entry,
            sensor_id=sensor_id,
            sensor_config=sensor_config_with_name,
            unique_id=f"{entry.entry_id}_{sensor_id}",
        )
    )
```

## Sensor-Abruf

Der Datenabruf erfolgt über den `LambdaDataUpdateCoordinator` in `coordinator.py`:

1. Eine Modbus-TCP/RTU-Verbindung wird zur Wärmepumpe hergestellt
2. Die Register werden entsprechend der Konfiguration abgefragt
3. Die Daten werden verarbeitet und in ein strukturiertes Format umgewandelt
4. Die Sensoren werden mit den neuen Daten aktualisiert

Der Abruf erfolgt regelmäßig nach dem konfigurierten Intervall (Standard: 30 Sekunden).

```python
async def _async_update_data(self):
    """Fetch data from Lambda device."""
    from pymodbus.client import ModbusTcpClient
    
    # Verbindung aufbauen
    if not self.client:
        self.client = ModbusTcpClient(self.host, port=self.port)
        if not await self.hass.async_add_executor_job(self.client.connect):
            raise ConnectionError("Could not connect to Modbus TCP")
    
    # Daten abrufen (Statische Sensoren, HP, Boiler, HC, etc.)
    try:
        data = {}
        # 1. Statische Sensoren abfragen
        for sensor_id, sensor_config in compatible_static_sensors.items():
            if self.is_register_disabled(sensor_config["address"]):
                continue
                
            result = await self.hass.async_add_executor_job(
                self.client.read_holding_registers,
                sensor_config["address"],
                count,
                self.slave_id,
            )
            
            # Daten verarbeiten und speichern
            # ...
    except Exception as ex:
        _LOGGER.error("Exception during data update: %s", ex)
    
    return data
```

## Konfiguration

Die Konfiguration erfolgt über die Home Assistant Benutzeroberfläche mit dem `config_flow.py`:

### Grundeinstellungen
- **Name**: Name der Installation
- **Host**: IP-Adresse oder Hostname der Wärmepumpe
- **Port**: Modbus-TCP-Port (Standard: 502)
- **Slave-ID**: Modbus-Slave-ID (Standard: 1)
- **Firmware-Version**: Firmware der Wärmepumpe (bestimmt verfügbare Sensoren)

### Geräteanzahl
- Anzahl der Wärmepumpen (1-3)
- Anzahl der Warmwasserspeicher (0-5)
- Anzahl der Heizkreise (0-12)
- Anzahl der Pufferspeicher (0-5)
- Anzahl der Solaranlagen (0-2)

### Temperatureinstellungen
- Warmwasser-Temperaturbereich (Min/Max)
- Heizkreis-Temperaturbereich (Min/Max)
- Temperaturschrittweite für Heizkreise

### Raumtemperatursteuerung
- Option zur Nutzung externer Temperatursensoren für Heizkreise

## Funktionsübersicht

### __init__.py
- **async_setup**: Initialisiert die Integration in Home Assistant
- **async_setup_entry**: Richtet eine konfigurierte Integration ein
- **async_unload_entry**: Entlädt eine Integration
- **async_reload_entry**: Lädt eine Integration neu nach Konfigurationsänderungen

### config_flow.py
- **LambdaConfigFlow**: Konfigurationsfluss für die Ersteinrichtung
- **LambdaOptionsFlow**: Konfigurationsfluss für die Optionen (z.B. Temperatureinstellungen)
- **async_step_user**: Erster Schritt der Konfiguration
- **async_step_init**: Verwaltung der Optionen
- **async_step_room_sensor**: Konfiguration von Raumtemperatursensoren

### coordinator.py
- **LambdaDataUpdateCoordinator**: Koordiniert Datenabrufe von der Wärmepumpe
- **async_init**: Initialisiert den Koordinator
- **_async_update_data**: Ruft Daten von der Wärmepumpe ab
- **is_register_disabled**: Prüft, ob ein Register deaktiviert ist

### sensor.py
- **async_setup_entry**: Richtet Sensoren basierend auf der Konfiguration ein
- **LambdaSensor**: Sensorklasse für Lambda-Wärmepumpen-Daten

### climate.py
- **async_setup_entry**: Richtet Klima-Entitäten ein
- **LambdaClimateBoiler**: Klasse für Warmwasserspeicher als Klima-Entität
- **LambdaClimateHC**: Klasse für Heizkreise als Klima-Entität

### services.py
- **async_setup_services**: Registriert Services für die Integration
- **async_update_room_temperature**: Service zum Aktualisieren der Raumtemperatur

### utils.py
- **get_compatible_sensors**: Filtert Sensoren nach Firmware-Kompatibilität
- **build_device_info**: Erstellt Geräteinformationen für das HA-Geräteregister
- **load_disabled_registers**: Lädt deaktivierte Register aus YAML-Datei
- **is_register_disabled**: Prüft, ob ein Register deaktiviert ist

## Firmware-Filterung

Die Integration unterstützt verschiedene Firmware-Versionen und filtert verfügbare Sensoren entsprechend:

```python
def get_compatible_sensors(sensor_templates: dict, fw_version: int) -> dict:
    """Return only sensors compatible with the given firmware version."""
    return {
        k: v
        for k, v in sensor_templates.items()
        if v.get("firmware_version", 1) <= fw_version
    }
```

Jeder Sensor hat ein `firmware_version`-Attribut, das die Mindestversion angibt, ab der der Sensor verfügbar ist.

## Modbus-Register-Services

Die Integration stellt zwei Home Assistant-Services für den direkten Zugriff auf Modbus-Register bereit:
- `lambda_heat_pumps.read_modbus_register`: Liest einen beliebigen Modbus-Registerwert aus.
- `lambda_heat_pumps.write_modbus_register`: Schreibt einen Wert in ein beliebiges Modbus-Register.

Diese Services können über die Entwicklerwerkzeuge genutzt werden. Die Registeradressen werden dynamisch berechnet und müssen entsprechend der Modbus-Dokumentation angegeben werden.

## Dynamische Entity-Erstellung

- Heizkreis-Klima-Entitäten werden nur erstellt, wenn für den jeweiligen Heizkreis ein Raumthermostat-Sensor in den Integrationsoptionen konfiguriert ist.
- Boiler- und andere Geräte-Entitäten werden entsprechend der konfigurierten Geräteanzahl erstellt.

## Template-basierte Climate-Entities

- Alle Climate-Entities (Boiler, Heizkreis) sind jetzt zentral in `const.py` als Templates definiert.
- Dadurch können Eigenschaften zentral gepflegt und erweitert werden.

## Neue Features (Version 1.4.0)

Version 1.4.0 führt bedeutende neue Features und Verbesserungen in die Lambda Wärmepumpen Integration ein:

### Wichtige neue Features

- **Energieverbrauchssensoren nach Betriebsart**: Konfigurierbare Energieverbrauchssensoren, die den Energieverbrauch nach Betriebsart (Heizen, Warmwasser, Kühlen, Abtauen) mit anpassbaren Quellsensoren verfolgen
- **Endianness-Konfiguration**: Konfigurierbare Byte-Reihenfolge (Big-Endian/Little-Endian) für verschiedene Lambda-Modelle
- **Sensor-Wechsel-Erkennung**: Automatische Erkennung von Energie-Sensor-Wechseln mit intelligenter Behandlung von Sensor-Wert-Übergängen
- **Erweiterte Cycling-Sensoren**: Umfassende Cycling-Zähler mit monatlicher und jährlicher Verfolgung
- **Automatische Konfiguration**: DHCP-Erkennung und Auto-Detection bestehender Konfigurationen
- **Konfigurationsdatei-Unterstützung**: YAML-basierte Konfiguration über `lambda_wp_config.yaml`

## Automatische Konfiguration

Die Integration unterstützt jetzt automatische Konfigurationserkennung und -einrichtung:

### DHCP-Erkennung
- **Auto-Detection**: Erkennt automatisch Lambda Wärmepumpen im Netzwerk
- **Bestehende Konfiguration prüfen**: Verhindert doppelte Konfigurationen
- **Intelligente Standardwerte**: Verwendet sinnvolle Standardwerte für IP, Port und Slave-ID

### Konfigurationsfluss-Verbesserungen
- **Vereinfachter Setup**: Vereinfachter Konfigurationsprozess
- **Validierung**: Erweiterte Konfigurationsvalidierung
- **Fehlerbehandlung**: Bessere Fehlermeldungen und Wiederherstellung

Beispiel für automatische Konfiguration:
```python
async def async_step_dhcp(self, discovery_info):
    """Handle DHCP discovery."""
    # Auto-Detection bestehender Konfigurationen
    existing_entries = self._async_current_entries()
    for entry in existing_entries:
        if entry.data.get("host") == discovery_info.ip:
            return self.async_abort(reason="already_configured")
    
    # Neue Eintrag mit entdeckter IP erstellen
    return self.async_create_entry(
        title=f"Lambda Wärmepumpe ({discovery_info.ip})",
        data={
            "host": discovery_info.ip,
            "port": 502,
            "slave_id": 1,
        }
    )
```

## Energieverbrauchssensoren

Erweiterte Energieverfolgung mit konfigurierbaren Quellsensoren und Betriebsart-Erkennung:

### Features
- **Betriebsart-Verfolgung**: Verfolgt Energieverbrauch nach Heizen, Warmwasser, Kühlen und Abtauen
- **Konfigurierbare Quellsensoren**: Verwendet beliebige bestehende Leistungsverbrauchssensoren als Datenquelle
- **Automatische Einheiten-Konvertierung**: Unterstützt Wh, kWh und MWh mit automatischer Konvertierung zu kWh
- **Monatliche und jährliche Verfolgung**: Langzeit-Energieverbrauchsüberwachung
- **Sensor-Wechsel-Erkennung**: Automatische Behandlung von Sensor-Wechseln zur Vermeidung falscher Berechnungen

### Konfiguration
Konfigurieren Sie Energieverbrauchssensoren in `lambda_wp_config.yaml`:

```yaml
energy_consumption_sensors:
  1:
    sensor_entity_id: "sensor.lambda_wp_verbrauch"
  2:
    sensor_entity_id: "sensor.lambda_wp_verbrauch_2"
```

### Implementierung
```python
async def _track_hp_energy_consumption(self, hp_idx: int, current_mode: int):
    """Verfolge Energieverbrauch nach Betriebsart."""
    hp_key = f"hp{hp_idx}"
    sensor_config = self._energy_sensor_configs.get(hp_idx, {})
    source_sensor_id = sensor_config.get("sensor_entity_id")
    
    if not source_sensor_id:
        return
    
    # Aktuellen Sensor-Wert mit Einheiten-Konvertierung abrufen
    source_state = self.hass.states.get(source_sensor_id)
    if source_state and source_state.state not in ("unknown", "unavailable"):
        current_value = float(source_state.state)
        unit = source_state.attributes.get("unit_of_measurement", "")
        
        # Zu kWh konvertieren
        current_kwh = convert_energy_to_kwh(current_value, unit)
        
        # Delta berechnen und Zähler aktualisieren
        last_value = self._last_energy_reading.get(hp_key, 0.0)
        delta = max(0, current_kwh - last_value)
        
        # Energieverbrauch nach Betriebsart aktualisieren
        mode_key = f"{hp_key}_{current_mode}"
        if mode_key in self._energy_consumption:
            self._energy_consumption[mode_key] += delta
        
        self._last_energy_reading[hp_key] = current_kwh
```

## Cycling-Sensoren

Umfassende Cycling-Verfolgung mit mehreren Zeiträumen und automatischer Reset-Funktionalität:

### Features
- **Mehrere Zeiträume**: Total, täglich, gestern, 2h, 4h, monatlich und jährlich Cycling-Sensoren
- **Automatischer Reset**: Täglicher Reset um Mitternacht, monatlicher Reset am 1. des Monats, jährlicher Reset am 1. Januar
- **Generalized Reset Functions**: Einheitlicher Reset-Mechanismus für alle Sensor-Typen
- **Erweiterte Automatisierung**: Verbesserte tägliche Reset-Automatisierung mit ordnungsgemäßer Gestern-Wert-Behandlung
- **Konfigurierbare Offsets**: Unterstützung für Cycling-Offsets beim Austausch von Wärmepumpen

### Sensor-Typen
- **Total-Sensoren**: Kumulative Cycling-Anzahl seit Installation
- **Tägliche Sensoren**: Tägliche Cycling-Werte (täglich um Mitternacht auf 0 zurückgesetzt)
- **Gestern-Sensoren**: Speichern die gestrigen täglichen Werte
- **2H/4H-Sensoren**: Kurzzeit-Cycling-Werte (alle 2/4 Stunden zurückgesetzt)
- **Monatliche Sensoren**: Monatliche Cycling-Werte (am 1. jedes Monats zurückgesetzt)
- **Jährliche Sensoren**: Jährliche Cycling-Werte (am 1. Januar zurückgesetzt)

### Konfiguration
Konfigurieren Sie Cycling-Offsets in `lambda_wp_config.yaml`:

```yaml
cycling_offsets:
  1:
    total: 1000
    daily: 50
  2:
    total: 2000
    daily: 100
```

### Implementierung
```python
async def _track_hp_cycling(self, hp_idx: int, current_mode: int):
    """Verfolge Cycling mit generalized Reset Functions."""
    hp_key = f"hp{hp_idx}"
    
    # Alle Cycling-Sensoren gleichzeitig erhöhen
    for sensor_type in ["total", "daily", "yesterday", "2h", "4h", "monthly", "yearly"]:
        if sensor_type in self._cycling_counters[hp_key]:
            self._cycling_counters[hp_key][sensor_type] += 1
    
    # Resets behandeln
    await self._handle_cycling_resets(hp_idx)

async def _handle_cycling_resets(self, hp_idx: int):
    """Behandle alle Cycling-Resets mit ordnungsgemäßer Gestern-Wert-Behandlung."""
    hp_key = f"hp{hp_idx}"
    
    # Täglicher Reset um Mitternacht
    if self._should_reset_daily():
        # Gestern-Wert vor Reset speichern
        self._cycling_counters[hp_key]["yesterday"] = self._cycling_counters[hp_key]["daily"]
        self._cycling_counters[hp_key]["daily"] = 0
    
    # Monatlicher Reset am 1. des Monats
    if self._should_reset_monthly():
        self._cycling_counters[hp_key]["monthly"] = 0
    
    # Jährlicher Reset am 1. Januar
    if self._should_reset_yearly():
        self._cycling_counters[hp_key]["yearly"] = 0
```

## Endianness-Konfiguration

Die Integration unterstützt jetzt konfigurierbare Byte-Reihenfolge (Endianness) für verschiedene Lambda-Modelle:

### Konfiguration
Setzen Sie Endianness in `lambda_wp_config.yaml`:

```yaml
# Endianness-Konfiguration
endianness: "big"    # Big-Endian (Standard)
# oder
endianness: "little" # Little-Endian
```

### Wann ist das wichtig?
- **Big-Endian**: Standard für die meisten Lambda-Modelle
- **Little-Endian**: Erforderlich für bestimmte Lambda-Modelle oder Firmware-Versionen
- **Automatische Erkennung**: Die Integration versucht automatisch die richtige Endianness zu erkennen

### Implementierung
```python
async def _load_endianness_config(self):
    """Lade Endianness-Konfiguration aus lambda_wp_config.yaml."""
    config = await load_lambda_config(self.hass)
    self._endianness = config.get("endianness", "big")  # Standard: big-endian
    
    # Legacy-Support für alte Konfiguration
    if not self._endianness:
        modbus_config = config.get("modbus", {})
        int32_byte_order = modbus_config.get("int32_byte_order", "big")
        self._endianness = "little" if int32_byte_order == "little" else "big"
```

### Datenverarbeitung
```python
# Datenverarbeitung mit Endianness-Unterstützung
if data_type == "int32":
    # Konfigurierte Endianness für ordnungsgemäße Byte-Reihenfolge verwenden
    if self._endianness == "little":
        value = result.registers[0] | (result.registers[1] << 16)
    else:  # big-endian (Standard)
        value = (result.registers[0] << 16) | result.registers[1]
else:
    value = result.registers[0]
```

## Sensor-Wechsel-Erkennung

Automatische Erkennung und Behandlung von Energie-Sensor-Wechseln zur Vermeidung falscher Energieverbrauchsberechnungen:

### Features
- **Automatische Erkennung**: Erkennt, wenn der konfigurierte Energie-Sensor wechselt
- **Intelligente Behandlung**: Passt `last_energy_readings` an den Anfangswert des neuen Sensors an
- **Retry-Mechanismus**: Robuste Behandlung der Sensor-Verfügbarkeit beim Start
- **Persistierung**: Speichert Sensor-IDs über Home Assistant-Neustarts hinweg
- **Umfassendes Logging**: Detailliertes Logging für einfache Verfolgung von Änderungen

### Implementierung
```python
async def _detect_and_handle_sensor_changes(self):
    """Erkenne und behandle Energie-Sensor-Wechsel."""
    for hp_idx, sensor_config in self._energy_sensor_configs.items():
        current_sensor_id = sensor_config.get("sensor_entity_id")
        stored_sensor_id = self._sensor_ids.get(f"hp{hp_idx}")
        
        if detect_sensor_change(stored_sensor_id, current_sensor_id):
            await self._handle_sensor_change(hp_idx, current_sensor_id)
        
        # Neue Sensor-ID speichern
        store_sensor_id(self._persist_data, hp_idx, current_sensor_id)

async def _handle_sensor_change(self, hp_idx: int, new_sensor_id: str):
    """Behandle Sensor-Wechsel mit Retry-Mechanismus."""
    max_retries = 5
    retry_delay = 2.0
    
    for attempt in range(max_retries):
        new_sensor_state = self.hass.states.get(new_sensor_id)
        if new_sensor_state and new_sensor_state.state not in ("unknown", "unavailable"):
            new_sensor_value = float(new_sensor_state.state)
            self._last_energy_reading[f"hp{hp_idx}"] = new_sensor_value
            await self._persist_counters()
            return
        
        if attempt < max_retries - 1:
            await asyncio.sleep(retry_delay)
    
    # Fallback auf 0 wenn Sensor nicht verfügbar
    self._last_energy_reading[f"hp{hp_idx}"] = 0.0
```

### Hilfsfunktionen
```python
def detect_sensor_change(stored_sensor_id: str, current_sensor_id: str) -> bool:
    """Erkenne Sensor-Wechsel durch Vergleich gespeicherter und aktueller Sensor-IDs."""
    if not stored_sensor_id:
        return False
    
    return stored_sensor_id != current_sensor_id

def convert_energy_to_kwh(value: float, unit: str) -> float:
    """Konvertiere Energie-Werte zu kWh basierend auf der Einheit."""
    if not unit:
        # Basierend auf der Wertgröße schätzen
        if value > 10000:  # Wahrscheinlich Wh
            return value / 1000.0
        return value
    
    unit_lower = unit.lower().strip()
    
    if unit_lower in ["wh", "wattstunden"]:
        return value / 1000.0
    elif unit_lower in ["kwh", "kilowattstunden"]:
        return value
    elif unit_lower in ["mwh", "megawattstunden"]:
        return value * 1000.0
    else:
        # Unbekannte Einheit - basierend auf der Wertgröße schätzen
        if value > 10000:
            return value / 1000.0
        return value
```

## Modbus-Tools für Tests

Für umfassende Tests und Entwicklung der Lambda Wärmepumpen Integration wurde ein dedizierter Satz von Modbus-Tools entwickelt. Diese Tools sind im [modbus_tools Repository](https://github.com/GuidoJeuken-6512/modbus_tools) verfügbar und bieten Simulationsmöglichkeiten für Lambda Wärmepumpen-Verhalten.

### Überblick

Das Modbus-Tools-Projekt enthält drei Hauptkomponenten, die speziell für die Lambda Wärmepumpen Integration-Entwicklung entwickelt wurden:

### 1. Modbus Client (GUI) (`client_gui.py`)

Eine grafische Benutzeroberfläche für interaktive Modbus TCP-Server-Abfragen:

- **Interaktive GUI**: Benutzerfreundliche Oberfläche zum Testen des Register-Zugriffs
- **Vorkonfigurierte Werte**: Vorausgefüllt mit gängigen Lambda Wärmepumpen-Register-Adressen
- **Flexible Konfiguration**: Alle Werte (Host-IP, Register-Adressen, Register-Typen) sind editierbar
- **Echtzeit-Antwort**: Zeigt Server-Antworten in Dialogfenstern an
- **Perfekt für**: Manuelle Tests und Debugging spezifischer Register-Werte

### 2. Modbus Client (CLI) (`client_cli.py`)

Ein Kommandozeilen-Tool für automatisierte Modbus TCP-Abfragen:

- **Automatisierte Tests**: Liest vordefinierte Register-Gruppen (Temperatur, Solar, etc.)
- **Automatische Skalierung**: Wendet Skalierungsfaktoren automatisch basierend auf der Register-Konfiguration an
- **Umfassendes Logging**: INFO/ERROR-Logging für Debugging und Entwicklung
- **Skriptierbar**: Ideal für automatisierte Tests und CI/CD-Pipelines
- **Beispiel-Verwendung**: `python client_cli.py`
- **Perfekt für**: Automatisierte Tests und schnelle Register-Wert-Verifikation

### 3. Modbus Server (`server.py`)

Eine vollständige Modbus TCP-Server-Implementierung für Simulation:

- **Lambda-Simulation**: Simuliert Lambda Wärmepumpen-Verhalten und Register-Antworten
- **Konfigurierbare Register**: Register-Werte können über `registers.yaml` angepasst werden
- **Realistische Daten**: Bietet realistische Sensor-Werte und Betriebsmodi
- **Flexibles Logging**: Konfigurierbare Logging-Optionen für verschiedene Entwicklungsbedürfnisse
- **Perfekt für**: Integration-Tests ohne physische Hardware

#### Server-Logging-Konfiguration

Der Server bietet flexible Logging-Optionen für verschiedene Entwicklungs-Szenarien:

```python
# Logging-Konfigurationskonstanten in server.py
LOG_ERRORS = True        # Steuert das Logging von Fehlermeldungen
LOG_WRITE_REGISTERS = True  # Steuert das Logging von Schreiboperationen
LOG_READ_REGISTERS = False  # Steuert das Logging von Leseoperationen
```

**Verfügbare Logging-Optionen:**

1. **Fehler-Logging** (`LOG_ERRORS`)
   - Bei `True`: Loggt alle Fehlermeldungen und Schreibverifizierungsfehler
   - Bei `False`: Unterdrückt Fehlermeldungen für sauberere Ausgabe
   - Standard: `True`

2. **Register-Schreib-Logging** (`LOG_WRITE_REGISTERS`)
   - Bei `True`: Loggt alle Schreiboperationen auf Register
   - Bei `False`: Unterdrückt Schreiboperationen-Logs
   - Standard: `True`

3. **Register-Lese-Logging** (`LOG_READ_REGISTERS`)
   - Bei `True`: Loggt alle Leseoperationen von Registern
   - Bei `False`: Unterdrückt Leseoperationen-Logs (empfohlen für hochfrequente Lesevorgänge)
   - Standard: `False`

### Setup und Verwendung

1. **Repository klonen**:
   ```bash
   git clone https://github.com/GuidoJeuken-6512/modbus_tools.git
   cd modbus_tools
   ```

2. **Abhängigkeiten installieren**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Register-Werte konfigurieren** (für Server):
   - Bearbeiten Sie `registers.yaml` um Register-Werte anzupassen
   - Modifizieren Sie `lambda.txt` für spezifische Lambda Wärmepumpen-Konfigurationen

4. **Modbus-Server starten**:
   ```bash
   python server.py
   ```

5. **Mit Client-Tools testen**:
   ```bash
   # GUI Client
   python client_gui.py
   
   # CLI Client
   python client_cli.py
   ```

### Integration mit Lambda Wärmepumpen-Entwicklung

Diese Tools sind speziell dafür entwickelt, die Entwicklung der Lambda Wärmepumpen Home Assistant Integration zu unterstützen:

- **Register-Tests**: Verifizieren Sie, dass die Integration Register-Werte korrekt liest und interpretiert
- **Endianness-Tests**: Testen Sie sowohl Big-Endian- als auch Little-Endian-Konfigurationen
- **Fehlerbehandlung**: Simulieren Sie verschiedene Fehlerbedingungen und Netzwerkprobleme
- **Leistungstests**: Testen Sie das Integrationsverhalten unter verschiedenen Lastbedingungen
- **Feature-Entwicklung**: Entwickeln und testen Sie neue Features ohne physische Hardware

### Abhängigkeiten

- **Python 3.7+**: Erforderlich für alle Komponenten
- **PyYAML**: Für Register-Konfigurationsdatei-Parsing (verwendet automatisch C-optimiertes `_yaml` falls verfügbar)
- **pymodbus**: Für Modbus TCP-Kommunikation
- **tkinter**: Für GUI-Client (meist mit Python enthalten)

### Haftungsausschluss

Diese Tools werden für Entwicklungs- und Testzwecke bereitgestellt. Die Nutzung erfolgt auf eigene Gefahr. Es wird keine Haftung für Schäden, Datenverluste oder andere Folgen übernommen, die durch die Verwendung dieser Tools entstehen.

Für weitere Informationen und die neuesten Updates besuchen Sie das [modbus_tools Repository](https://github.com/GuidoJeuken-6512/modbus_tools).
