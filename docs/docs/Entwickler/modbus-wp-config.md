---
title: "modbus_wp_config.yaml (Entwickler)"
---

# modbus_wp_config.yaml – Entwicklereinstellungen

Die Datei `modbus_wp_config.yaml` ermöglicht Entwicklern, das Verhalten der Lambda Heat Pumps Integration auf Register‑Ebene anzupassen. Dies betrifft vor allem Register‑Deaktivierung, Sensor‑Namensüberschreibungen, Zähler‑Offsets, Energie‑Sensoren und Modbus‑Parameter.

**Pfad:** `config/lambda_wp_config.yaml`

## YAML wird eingelesen

Die Konfiguration wird beim Start der Integration über die Funktion `load_lambda_config()` in `utils.py` geladen. Die Funktion prüft zuerst, ob die Konfiguration bereits gecacht ist, erstellt die Datei falls nötig, führt Migrationen durch und lädt dann die YAML-Datei.

**Hauptfunktion:**

```454:470:custom_components/lambda_heat_pumps/utils.py
async def load_lambda_config(hass: HomeAssistant) -> dict:
    """Load complete Lambda configuration from lambda_wp_config.yaml."""
    # Check if config is already cached in hass.data
    if "_lambda_config_cache" in hass.data:
        _LOGGER.debug("Using cached Lambda config")
        return hass.data["_lambda_config_cache"]
    
    # First, ensure config file exists
    await ensure_lambda_config(hass)
    
    # Then, try to migrate if needed (only once per session)
    if "_lambda_migration_done" not in hass.data:
        await migrate_lambda_config_sections(hass)
        hass.data["_lambda_migration_done"] = True

    config_dir = hass.config.config_dir
    lambda_config_path = os.path.join(config_dir, "lambda_wp_config.yaml")
```

**Standard-Konfiguration:**

```472:479:custom_components/lambda_heat_pumps/utils.py
    default_config = {
        "disabled_registers": set(),
        "sensors_names_override": {},
        "cycling_offsets": {},
        "energy_consumption_sensors": {},
        "energy_consumption_offsets": {},
        "modbus": {},
    }
```

**YAML-Laden und Parsing:**

```485:495:custom_components/lambda_heat_pumps/utils.py
    try:
        content = await hass.async_add_executor_job(
            lambda: open(lambda_config_path, "r").read()
        )
        config = yaml.safe_load(content)

        if not config:
            _LOGGER.warning(
                "lambda_wp_config.yaml is empty, using default configuration"
            )
            return default_config
```

Die Konfiguration wird gecacht in `hass.data["_lambda_config_cache"]`, um wiederholtes Laden zu vermeiden.

## disabled_registers

Deaktiviert einzelne Register, z. B. bei Firmware‑Inkompatibilitäten oder Fehlern.

```yaml
disabled_registers:
  - 2004   # Beispiel: boil1_actual_circulation_temp
  - 100000 # beliebiges Register, das ignoriert werden soll
```

**Technische Verarbeitung:**

1. **Einlesen:** Die Liste wird in ein `set` konvertiert:

```497:504:custom_components/lambda_heat_pumps/utils.py
        # Load disabled registers
        disabled_registers = set()
        if "disabled_registers" in config:
            try:
                disabled_registers = set(int(x) for x in config["disabled_registers"])
            except (ValueError, TypeError) as e:
                _LOGGER.error("Invalid disabled_registers format: %s", e)
                disabled_registers = set()
```

2. **Verwendung:** Vor jedem Modbus-Lesevorgang wird geprüft, ob das Register deaktiviert ist:

```610:627:custom_components/lambda_heat_pumps/utils.py
def is_register_disabled(address: int, disabled_registers: set[int]) -> bool:
    """Check if a register is disabled.

    Args:
        address: The register address to check
        disabled_registers: Set of disabled register addresses

    Returns:
        bool: True if the register is disabled, False otherwise
    """
    is_disabled = address in disabled_registers
    if is_disabled:
        _LOGGER.debug(
            "Register %d is disabled (in set: %s)",
            address,
            disabled_registers,
        )
    return is_disabled
```

3. **Im Coordinator:** Deaktivierte Register werden beim Lesen übersprungen:

```1267:1279:custom_components/lambda_heat_pumps/coordinator.py
        is_disabled = is_register_disabled(address, self.disabled_registers)
        if is_disabled:
            _LOGGER.debug(
                "Register %d is disabled (in set: %s)",
                address,
                self.disabled_registers,
            )
        else:
            _LOGGER.debug(
                "Register %d is not disabled (checked against set: %s)",
                address,
                self.disabled_registers,
            )
```

**Wann verwenden:**
- Register verursacht Fehlermeldungen.
- Register wird von der vorhandenen Firmware nicht unterstützt.
- Reduzierung des Modbus‑Traffics.

## sensors_names_override

Überschreibt Standard‑Sensornamen für bessere Lesbarkeit oder Lokalisierung.

```yaml
sensors_names_override:
  - id: hp1_flow_temp
    override_name: "Vorlauf Wohnzimmer"
  - id: hp1_return_temp
    override_name: "Rücklauf Wohnzimmer"
  - id: hp1_operating_state
    override_name: "Betriebszustand"
```

**Technische Verarbeitung:**

1. **Einlesen:** Die Liste wird in ein Dictionary konvertiert (`id` → `override_name`):

```506:517:custom_components/lambda_heat_pumps/utils.py
        # Load sensor overrides
        sensors_names_override = {}
        if "sensors_names_override" in config:
            try:
                for override in config["sensors_names_override"]:
                    if "id" in override and "override_name" in override:
                        sensors_names_override[override["id"]] = override[
                            "override_name"
                        ]
            except (TypeError, KeyError) as e:
                _LOGGER.error("Invalid sensors_names_override format: %s", e)
                sensors_names_override = {}
```

2. **Verwendung:** Beim Erstellen der Sensoren wird der Override-Name verwendet:

```141:152:custom_components/lambda_heat_pumps/sensor.py
                override_name = None
                if use_legacy_modbus_names and hasattr(coordinator, "sensor_overrides"):
                    override_name = coordinator.sensor_overrides.get(
                        f"{prefix}{idx}_{sensor_id}"
                    )
                if override_name:
                    name = override_name
                    sensor_id_final = f"{prefix}{idx}_{sensor_id}"
                    # Data key (original format)
                    entity_id = f"sensor.{name_prefix_lc}_{override_name}"
                    unique_id = f"{name_prefix_lc}_{override_name}"
```

**Hinweise:**
- `id` muss einer internen Sensor‑ID entsprechen (siehe Sensorliste in der Integration).
- Nur Name wird überschrieben, nicht die Entity‑ID.
- Funktioniert nur, wenn `use_legacy_modbus_names` aktiviert ist.

## cycling_offsets

Offsets für Total‑Cycling‑Zähler (z. B. nach Pumpentausch oder Reset).

```yaml
cycling_offsets:
  hp1:
    heating_cycling_total: 1500
    hot_water_cycling_total: 800
    cooling_cycling_total: 200
    defrost_cycling_total: 50
    compressor_start_cycling_total: 5000
  hp2:
    heating_cycling_total: 0
    hot_water_cycling_total: 0
    cooling_cycling_total: 0
    defrost_cycling_total: 0
    compressor_start_cycling_total: 0
```

**Technische Verarbeitung:**

1. **Einlesen:** Die Struktur wird validiert und ungültige Werte auf 0 gesetzt:

```519:542:custom_components/lambda_heat_pumps/utils.py
        # Load cycling offsets
        cycling_offsets = {}
        if "cycling_offsets" in config:
            try:
                cycling_offsets = config["cycling_offsets"]
                # Validate cycling offsets structure
                for device, offsets in cycling_offsets.items():
                    if not isinstance(offsets, dict):
                        _LOGGER.warning(
                            "Invalid cycling_offsets format for device %s", device
                        )
                        continue
                    for offset_type, value in offsets.items():
                        if not isinstance(value, (int, float)):
                            _LOGGER.warning(
                                "Invalid cycling offset value for %s.%s: %s",
                                device,
                                offset_type,
                                value,
                            )
                            cycling_offsets[device][offset_type] = 0
            except (TypeError, KeyError) as e:
                _LOGGER.error("Invalid cycling_offsets format: %s", e)
                cycling_offsets = {}
```

2. **Laden im Coordinator:** Offsets werden beim Coordinator-Start geladen:

```375:383:custom_components/lambda_heat_pumps/coordinator.py
    async def _load_offsets_and_persisted(self):
        # Lade Offsets aus lambda_wp_config.yaml über das zentrale Config-System
        from .utils import load_lambda_config
        
        try:
            config = await load_lambda_config(self.hass)
            _LOGGER.info(f"Loaded config keys: {list(config.keys())}")
            self._cycling_offsets = config.get("cycling_offsets", {})
            self._energy_offsets = config.get("energy_consumption_offsets", {})
```

3. **Anwendung auf Sensoren:** Der Offset wird zum Sensorwert addiert:

```880:910:custom_components/lambda_heat_pumps/sensor.py
        """Apply cycling offset from configuration."""
        try:
            # Lade die Cycling-Offsets aus der Konfiguration
            from .utils import load_lambda_config
            config = await load_lambda_config(self.hass)
            cycling_offsets = config.get("cycling_offsets", {})
            
            if not cycling_offsets:
                _LOGGER.debug(f"No cycling offsets found for {self.entity_id}")
                return
            
            # Bestimme den Device-Key (z.B. "hp1")
            device_key = f"hp{self._hp_index}"
            
            if device_key not in cycling_offsets:
                _LOGGER.debug(f"No cycling offsets found for device {device_key}")
                return
            
            # Hole den aktuellen Offset für diesen Sensor
            current_offset = cycling_offsets[device_key].get(self._sensor_id, 0)
            
            # Hole den bereits angewendeten Offset aus den Attributen
            applied_offset = getattr(self, "_applied_offset", 0)
            
            # Berechne die Differenz zwischen aktuellem und bereits angewendetem Offset
            offset_difference = current_offset - applied_offset
            
            # Debug-Log für bessere Nachverfolgung
            _LOGGER.debug(
                f"Offset calculation for {self.entity_id}: current={current_offset}, applied={applied_offset}, difference={offset_difference}"
```

**Hinweise:**
- Gilt nur für **Total‑Sensoren**, nicht für Daily/Monthly/Yearly.
- Werte sind absolute Zähler (keine Deltas).
- Der Offset wird einmalig beim Sensor-Start angewendet.

## energy_consumption_sensors

Definiert pro HP die Quellsensoren für **elektrische** und **thermische** Energieverbrauchsdaten. Standard sind die Lambda-eigenen Modbus-Sensoren; externe Zähler (z. B. Shelly) können getrennt für Strom und Wärme eingebunden werden.

```yaml
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.shelly_lambda_gesamt_leistung"   # elektrischer Quellsensor
    thermal_sensor_entity_id: "sensor.waermemesser_hp1"       # optional, thermischer Quellsensor
  hp2:
    sensor_entity_id: "sensor.eu08l_hp2_compressor_power_consumption_accumulated"
    # thermal_sensor_entity_id weglassen = Default compressor_thermal_energy_output_accumulated
```

- **`sensor_entity_id`**: Quellsensor für elektrische Energie (Stromverbrauch). Fehlt → Default: `sensor.{name}_hp{n}_compressor_power_consumption_accumulated`.
- **`thermal_sensor_entity_id`** (optional): Quellsensor für thermische Energie (Wärmeabgabe). Fehlt oder ungültig → Default: `sensor.{name}_hp{n}_compressor_thermal_energy_output_accumulated`.

**Technische Verarbeitung:**

1. **Einlesen:** Die Konfiguration wird direkt aus der YAML übernommen:

```582:582:custom_components/lambda_heat_pumps/utils.py
            "energy_consumption_sensors": config.get("energy_consumption_sensors", {}),
```

2. **Validierung:** Externe Sensoren werden validiert:

```385:389:custom_components/lambda_heat_pumps/coordinator.py
            # Lade und validiere Energy Sensor Konfigurationen
            raw_energy_sensor_configs = config.get("energy_consumption_sensors", {})
            
            # Validiere externe Sensoren
            from .utils import validate_external_sensors
            self._energy_sensor_configs = validate_external_sensors(self.hass, raw_energy_sensor_configs)
```

3. **Verwendung:** Der konfigurierte Sensor wird für Energieverbrauchsberechnungen verwendet:

```1998:2002:custom_components/lambda_heat_pumps/coordinator.py
            sensor_config = self._energy_sensor_configs.get(hp_key, {})
            _LOGGER.debug(f"DEBUG-012: Sensor config: {sensor_config}")
            sensor_entity_id = sensor_config.get("sensor_entity_id")
            _LOGGER.debug(f"DEBUG-013: Sensor entity ID: {sensor_entity_id}")
            
            # If no custom sensor configured, use the default power consumption sensor
```

**Hinweise:**
- Quellsensoren müssen kumulative Energie in Wh oder kWh liefern; Konvertierung zu kWh erfolgt automatisch.
- Je HP optional ein **elektrischer** und ein **thermischer** Quellsensor; fehlt einer, wird der jeweilige Lambda-Standard-Sensor verwendet.
- Für thermische Quellsensoren gilt dieselbe Resilienz wie für elektrische (Sensor-Wechsel-Erkennung, Zweitwert abwarten, Persistierung von `thermal_sensor_ids` und `last_thermal_energy_readings`).

## energy_consumption_offsets

Offsets für Total‑Energieverbrauch (kWh). Nützlich nach Pumpentausch oder Zähler‑Reset.

```yaml
energy_consumption_offsets:
  hp1:
    heating_energy_total: 5000.0
    hot_water_energy_total: 2000.0
    cooling_energy_total: 500.0
    defrost_energy_total: 150.0
  hp2:
    heating_energy_total: 150.5
    hot_water_energy_total: 45.25
    cooling_energy_total: 12.8
    defrost_energy_total: 3.1
```

**Technische Verarbeitung:**

1. **Einlesen:** Die Struktur wird validiert und ungültige Werte auf 0.0 gesetzt:

```544:567:custom_components/lambda_heat_pumps/utils.py
        # Load energy consumption offsets
        energy_consumption_offsets = {}
        if "energy_consumption_offsets" in config:
            try:
                energy_consumption_offsets = config["energy_consumption_offsets"]
                # Validate energy consumption offsets structure
                for device, offsets in energy_consumption_offsets.items():
                    if not isinstance(offsets, dict):
                        _LOGGER.warning(
                            "Invalid energy_consumption_offsets format for device %s", device
                        )
                        continue
                    for offset_type, value in offsets.items():
                        if not isinstance(value, (int, float)):
                            _LOGGER.warning(
                                "Invalid energy consumption offset value for %s.%s: %s",
                                device,
                                offset_type,
                                value,
                            )
                            energy_consumption_offsets[device][offset_type] = 0.0
            except (TypeError, KeyError) as e:
                _LOGGER.error("Invalid energy_consumption_offsets format: %s", e)
                energy_consumption_offsets = {}
```

2. **Laden im Coordinator:** Offsets werden beim Coordinator-Start geladen:

```383:383:custom_components/lambda_heat_pumps/coordinator.py
            self._energy_offsets = config.get("energy_consumption_offsets", {})
```

3. **Anwendung:** Der Offset wird zu den Energieverbrauchswerten addiert (ähnlich wie bei cycling_offsets).

**Hinweise:**
- Alle Werte in **kWh**.
- Gilt nur für **Total‑Sensoren** (nicht Daily/Monthly/Yearly).

## modbus

Konfiguration für 32‑Bit‑Register‑Reihenfolge.

```yaml
modbus:
  int32_register_order: "high_first"  # oder "low_first"
```

**Technische Verarbeitung:**

1. **Einlesen:** Die Modbus-Konfiguration wird direkt übernommen:

```584:584:custom_components/lambda_heat_pumps/utils.py
            "modbus": config.get("modbus", {}),  # Include modbus configuration
```

2. **Laden der Register-Reihenfolge:** Beim Coordinator-Start wird die Reihenfolge geladen:

```313:362:custom_components/lambda_heat_pumps/modbus_utils.py
async def get_int32_register_order(hass) -> str:
    """
    Lädt Register-Reihenfolge-Konfiguration aus lambda_wp_config.yaml.
    
    Es handelt sich um die Reihenfolge der 16-Bit-Register bei 32-Bit-Werten
    (Register/Word Order), nicht um Byte-Endianness innerhalb eines Registers.
    
    Args:
        hass: Home Assistant Instanz
    
    Returns:
        str: "high_first" oder "low_first" (Standard: "high_first")
        
    Note:
        "high_first" = Höherwertiges Register zuerst (Register[0] << 16 | Register[1])
        "low_first" = Niedrigwertiges Register zuerst (Register[1] << 16 | Register[0])
        
        Rückwärtskompatibilität: "big" wird zu "high_first", "little" zu "low_first" konvertiert
    """
    try:
        from .utils import load_lambda_config
        config = await load_lambda_config(hass)
        modbus_config = config.get("modbus", {})
        
        # Prüfe zuerst neue Config, dann alte (für Rückwärtskompatibilität)
        register_order = modbus_config.get("int32_register_order")
        if register_order is None:
            # Rückwärtskompatibilität: Alte Config migrieren
            old_byte_order = modbus_config.get("int32_byte_order")
            if old_byte_order is not None:
                _LOGGER.info(
                    "Migration: int32_byte_order gefunden, verwende Wert für int32_register_order. "
                    "Bitte migrieren Sie Ihre Config zu modbus.int32_register_order"
                )
                register_order = old_byte_order
            else:
                register_order = "high_first"  # Standard
        
        # Rückwärtskompatibilität: Konvertiere alte Werte
        if register_order == "big":
            register_order = "high_first"
            _LOGGER.info(
                "Veralteter Wert 'big' verwendet. Bitte aktualisieren Sie Ihre Config auf 'high_first'"
            )
        elif register_order == "little":
            register_order = "low_first"
            _LOGGER.info(
                "Veralteter Wert 'little' verwendet. Bitte aktualisieren Sie Ihre Config auf 'low_first'"
            )
```

3. **Verwendung:** Bei 32‑Bit‑Registern wird die Reihenfolge beim Kombinieren der Register verwendet:

```866:876:custom_components/lambda_heat_pumps/coordinator.py
                                    register_order = sensor_info.get("register_order") or sensor_info.get("byte_order") or self._int32_register_order
                                    
                                    # DEBUG: Für 1020/1022
                                    if addr in [1020, 1022]:
                                        _LOGGER.debug(
                                            "INT32-REGISTER-DEBUG: Batch-Verarbeitung Register %d: "
                                            "Register[%d]=%d, Register[%d]=%d, order=%s",
                                            addr, i, value, i+1, next_value, register_order
                                        )
                                    
                                    value = combine_int32_registers([value, next_value], register_order)
```

**Optionen:**
- `high_first` (Standard): höherwertiges Register zuerst.
- `low_first`: niedrigeres Register zuerst (für bestimmte Geräte/Firmware).

**Wann verwenden:**
- Falsche Werte bei 32‑Bit‑Sensoren (Energieverbrauch, Zähler).
- Nach Firmware‑Updates mit geändertem Register‑Layout.

## Vollständiges Beispiel

```yaml
# Problematische Register deaktivieren
disabled_registers:
  - 2004
  - 100000

# Sensornamen überschreiben
sensors_names_override:
  - id: hp1_flow_temp
    override_name: "Wohnzimmer Temperatur"
  - id: hp1_return_temp
    override_name: "Rücklauf Temperatur"

# Cycling‑Offsets
cycling_offsets:
  hp1:
    heating_cycling_total: 2500
    hot_water_cycling_total: 1200
    cooling_cycling_total: 300
    defrost_cycling_total: 80
    compressor_start_cycling_total: 5000

# Energieverbrauchs‑Sensoren
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.eu08l_hp1_compressor_power_consumption_accumulated"
  hp2:
    sensor_entity_id: "sensor.shelly_lambda_gesamt_leistung"

# Energieverbrauchs‑Offsets (kWh)
energy_consumption_offsets:
  hp1:
    heating_energy_total: 5000.0
    hot_water_energy_total: 2000.0
    cooling_energy_total: 500.0
    defrost_energy_total: 150.0

# Modbus‑Parameter
modbus:
  int32_register_order: "high_first"
```

## Best Practices
- Änderungen dokumentieren und versionieren (z. B. per Git).
- Nach Anpassungen Home Assistant neu starten.
- Bei externen Energiesensoren sicherstellen, dass Einheit und Auflösung konsistent sind.
