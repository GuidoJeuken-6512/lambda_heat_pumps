---
title: "Features (Technische Übersicht)"
---

# Features – Technische Übersicht

*Zuletzt geändert am 06.09.2026*

**Stand:** Release 3.5.2 (Rewrite auf [`modbus-connection`](https://github.com/home-assistant-libs/modbus-connection)/`tmodbus`, Branch `3.5`; Hintergrund zum Rewrite: [Issue #99](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/99))

Diese Seite bietet eine technische Übersicht der wichtigsten Features der
Lambda Heat Pumps Integration mit Code-Beispielen aus dem aktuellen Code. Für
die Abläufe und Mermaid-Diagramme siehe [Ablaufdiagramm](Ablaufdiagramm.md).

## Architektur-Übersicht

```
custom_components/lambda_heat_pumps/
├── __init__.py           Setup, Unload, Entry-Migration
├── coordinator.py        Poll-Loop, Cycle-/Energie-Tracking, Rollover
├── entity.py             Gemeinsame Basis aller Entities
├── sensor.py             Register-, Zähler-, COP-, Heizkurven-Sensoren
├── climate.py            Thermostat-Entities
├── number.py             Heizkurven-Einstellungen, Flow-Line-Offset
├── services.py           PV-/Raumthermostat-Schreiber, Modbus-Debug-Services
├── config_flow.py        Verbindungs-Setup, Optionen
├── module_auto_detect.py Einmalige Modul-Erkennung
├── firmware.py           Firmware→Register-Kompatibilität
├── config_file.py        lambda_wp_config.yaml (Offsets, externe Zähler)
├── diagnostics.py        Rohregister-Dump
└── lambda_modbus/        Das Register-Modell selbst (kein HA-Import)
    ├── model.py           Basisklasse, Sentinel-Behandlung (gauge/enum)
    ├── ranges.py          Adress-Layout, lesbare Register-Läufe
    ├── heat_pump.py, boiler.py, buffer.py, solar.py,
    │   heating_circuit.py, general.py   je Modultyp ein Komponenten-Modell
    └── enums.py           Zustandscodes (LambdaState-Unterklassen)
```

`lambda_modbus/` ist bewusst von Home Assistant entkoppelt – es kennt nur
[`modbus_connection.ModbusUnit`](https://github.com/home-assistant-libs/modbus-connection)
und ist so geschnitten, dass es unverändert als eigenständiges PyPI-Paket
lebensfähig wäre (siehe Docstring in `lambda_modbus/__init__.py`).

## Modbus-Kommunikation

Die Integration öffnet eine `ModbusConnection` (Bibliothek
[`modbus-connection`](https://github.com/home-assistant-libs/modbus-connection),
Backend `tmodbus`) und nimmt darauf einen `ModbusUnit`-Handle für die
konfigurierte Slave-ID:

```python
# __init__.py
connection = ModbusConnection(
    ModbusTcpParams(host=entry.data[CONF_HOST], port=port),
    message_spacing=DEFAULT_MODBUS_MESSAGE_SPACING,  # 50 ms
)
entry.async_on_unload(connection.close)
unit = connection.for_unit(slave_id)
```

`message_spacing` ist kein Performance-Tuning, sondern erzwingt, dass die
Bibliothek ihr eigenes Serialisierungs-Lock tatsächlich benutzt – ohne
Spacing wäre es ein reiner Durchreicher und Poll-Loop und Schreib-Timer
könnten gleichzeitig auf derselben Verbindung senden. Details, warum das nötig
ist und was ohne es passiert: [Modbus-Serialisierung](modbus-serialisierung.md).

Weder `__init__.py` noch `lambda_modbus/` schreiben eigene Retry- oder
Timeout-Logik – das übernimmt `modbus-connection`/`tmodbus`. Was die
Integration selbst behandelt, ist eine **hartnäckig** hängende Verbindung
(drei Timeouts am Stück trennt der Coordinator sie, siehe
[Ablaufdiagramm](Ablaufdiagramm.md#5-voller-poll-zyklus-_async_update_data))
und ein Register, das der Controller nach dem Setup nicht mehr bedient (löst
einen Reload aus).

## Register-Modell: Sentinel-Werte

Der Controller lässt kein Register leer – ein nicht vorhandenes gibt `0x8000`
zurück, ein nicht angeschlossener Sensor `0xFFF448` (-3000). Skaliert sehen
diese wie plausible Messwerte aus (-327,68 °C bzw. -300,0 °C) und würden ohne
Behandlung in die Statistik einfließen:

```python
# lambda_modbus/model.py
NO_REGISTER = 0x8000  # die Firmware hat dieses Register nicht
NO_SENSOR = 0xF448    # -3000: nichts angeschlossen
SENTINELS = (NO_REGISTER, NO_SENSOR)

def gauge(address: int, scale: float, /, **kwargs):
    """Ein skalierter Messwert, der als unknown gelesen wird, wenn keiner da ist."""
    kwargs.setdefault("nan", SENTINELS)
    return _gauge(address, scale, **kwargs)
```

Ein weiterer Sentinel, `0xFFFF` (-1, „keine Anforderung“), gilt nur für
einzelne Felder (z. B. `Buffer.request_type`, `Ambient.temperature`) und wird
dort gezielt mit `nan=SENTINELS + (NO_REQUEST,)` ergänzt – global gilt er
nicht, weil -1 auf anderen Registern (z. B. Temperatur-Offsets) ein echter Wert
ist.

## Automatische Modulerkennung

Beim Setup wird für jeden Modultyp hochgezählt, bis der Controller nicht mehr
antwortet – nicht mehr in `entry.data` gespeichert, sondern bei **jedem**
Setup neu ermittelt:

```python
# module_auto_detect.py
async def _count(unit: ModbusUnit, module: str, maximum: int) -> int:
    for index in range(1, maximum + 1):
        register = base_address(module, index) + _PROBE_REGISTER
        try:
            await unit.read_holding_registers(register, 1)
        except (IllegalDataAddressError, ModbusTimeoutError):
            return index - 1
    return maximum
```

`MAX_MODULE_COUNTS = {"hp": 3, "boil": 5, "buff": 5, "sol": 2, "hc": 12}`
begrenzt, wie weit hochgezählt wird. Jeder andere Modbus-Fehler (nicht „Register
gibt es nicht“) propagiert als `ConfigEntryNotReady` – ein beschäftigter oder
gestörter Controller wird nicht fälschlich als kleineres System interpretiert.

## Firmware-Kompatibilität

Ein Sensor deklariert entweder gar nichts (gilt für jede Firmware),
`firmware_version` (ab dieser Version) oder `firmware_versions` (exakte,
möglicherweise lückenhafte Menge, Notation `"1-7"`, `"-4"`, `7`):

```python
# firmware.py
def serves(description, level: int) -> bool:
    if description.firmware_versions is not None:
        return level in parse_firmware_versions(description.firmware_versions)
    if description.firmware_version is not None:
        return description.firmware_version <= level
    return True
```

```python
# sensor.py – Beispiel: Außentemperatur nur bis einschließlich Firmware 7 lesbar
_temperature("ambient_temperature", firmware_versions=("1-7",)),
```

`firmware_level(entry)` löst den in den Config-Flow-Optionen gewählten
Firmware-Namen (`"V0.0.8-3K"`, …) über `FIRMWARE_CONFIG` in `const.py` auf die
Versions-Ordinalzahl auf; ein unbekannter Name (z. B. eine Entry aus einer
neueren Integrationsversion) fällt auf `1` zurück – die älteste, von jedem
Controller bediente Registerkarte.

## Cycling- und Energie-Zähler

Der Coordinator führt **keine** persistente Zählerdatei mehr – `Totals`
(`coordinator.py`) zählt nur, was seit dem Start von Home Assistant beobachtet
wurde:

```python
@dataclass
class Totals:
    cycles: dict[str, int] = field(default_factory=dict)
    electrical: dict[str, float] = field(default_factory=dict)
    thermal: dict[str, float] = field(default_factory=dict)
```

`LambdaCounterSensor` (`sensor.py`) macht daraus einen absoluten Zähler: Er
restauriert seinen eigenen Stand über `RestoreSensor`, merkt sich beim
Hinzufügen den aktuellen `Totals`-Wert als Baseline (`_counted`) und addiert
bei jedem Coordinator-Update nur die **Differenz**:

```python
@callback
def _handle_coordinator_update(self) -> None:
    total = self._total()
    self._value += total - self._counted
    self._counted = total
    super()._handle_coordinator_update()
```

Welche Perioden ein Zähler bekommt, ist absichtlich nicht symmetrisch – ändern
würde bestehende Entities verwaisen lassen:

```python
CYCLE_PERIODS = (PERIOD_TOTAL, PERIOD_DAILY, PERIOD_2H, PERIOD_4H)
COMPRESSOR_START_PERIODS = (*CYCLE_PERIODS, PERIOD_MONTHLY)
ENERGY_PERIODS = (PERIOD_TOTAL, PERIOD_DAILY, PERIOD_MONTHLY, PERIOD_YEARLY)
HEATING_ENERGY_PERIODS = (*ENERGY_PERIODS, PERIOD_HOURLY)  # nur "heating"
```

Nur die laufenden Total-Zähler sind standardmäßig aktiviert
(`entity_registry_enabled_default=period == PERIOD_TOTAL`) – die
Perioden-Zähler lassen sich aus dem Total ableiten (Energie-Dashboard,
`utility_meter`), und werden daher nicht als Dutzende zusätzliche Entities pro
Wärmepumpe ausgeliefert.

## COP-Sensoren

Ein COP ist nichts weiter als zwei bereits vorhandene Zähler (thermisch,
elektrisch) über dieselbe Periode geteilt – der Sensor hält selbst keinen
Zustand:

```python
# sensor.py – LambdaCopSensor.native_value
@property
def native_value(self) -> float | None:
    electrical = self._electrical.native_value
    if not electrical:
        return None
    return round(self._thermal.native_value / electrical, 2)
```

Daneben gibt es pro Wärmepumpe einen `LambdaLifetimeCopSensor`
(`sensor.py`, `unique_id`-Schlüssel `cop_calc`), der nicht die von der
Integration gezählten `Totals` verwendet, sondern die beiden **Lifetime**-Register
des Controllers selbst (`compressor_power_consumption_accumulated` /
`..._thermal_energy_output_accumulated`) – der einzige COP-Wert, der auch
zählt, was vor der ersten Home-Assistant-Installation passiert ist.

## Heizkurve

`LambdaHeatingCurveSensor` (`sensor.py`) liest die drei vom Nutzer gesetzten
Stützpunkte, interpoliert linear und addiert die konfigurierten Korrekturen:

```python
# const.py
CURVE_POINTS: Final = (
    (-22.0, "heating_curve_cold_outside_temp", 48.3),
    (0.0, "heating_curve_mid_outside_temp", 39.0),
    (22.0, "heating_curve_warm_outside_temp", 32.0),
)
```

```python
# sensor.py
flow = _read_curve(outside, curve)          # lineare Interpolation
circuit = self.coordinator.component("hc", self._index)
flow += self._room_correction(circuit)      # nur wenn Raumthermostat aktiv
flow += circuit.set_flow_line_offset_temperature or 0.0
if circuit.operating_state == HeatingCircuitOperatingState.ECO:
    flow += self._setting("eco_temp_reduction", DEFAULT_ECO_TEMP_REDUCTION)
```

Die drei Stützpunkte, die Eco-Reduktion sowie Offset/Faktor der
Raumthermostat-Korrektur sind **keine Register** – sie werden von
`LambdaSettingNumber`-Entities (`number.py`) gehalten, über einen Neustart
restauriert und direkt in `coordinator.settings` publiziert, damit der
Heizkurven-Sensor sie ohne Umweg über den State-Store lesen kann:

```python
# number.py – LambdaSettingNumber._publish
def _publish(self, value: float) -> None:
    self.coordinator.settings[(self._index, self.entity_description.key)] = value
```

Der **Flow-Line-Offset** dagegen ist ein echtes Register
(`LambdaFlowLineOffsetNumber`) – er wird geschrieben und vom Controller selbst
gehalten, es gibt nichts zu restaurieren.

## PV-Überschuss und Raumthermostat

Zwei Werte kann der Controller nicht selbst messen: die Raumtemperatur (kennt
eine andere Thermostat-Entity) und den PV-Überschuss (kennt der
Wechselrichter). Beide werden ihm auf einem Timer geschrieben, solange das
Feature aktiv ist – der Controller reagiert nur, solange der Wert
**weiterhin** ankommt:

```python
# services.py
async def async_write_pv_surplus(coordinator: LambdaCoordinator) -> None:
    ...
    if options.get(CONF_PV_SURPLUS_MODE, DEFAULT_PV_SURPLUS_MODE) == "neg":
        raw = max(-32768, min(32767, int(power))) & 0xFFFF  # signed möglich
    else:
        raw = max(0, min(65535, int(power)))
    await coordinator.unit.write_register(PV_SURPLUS_REGISTER, raw)
```

`async_setup_writers` armt den gemeinsamen Timer (`CONF_WRITE_INTERVAL`,
Default 9 s) nur, wenn mindestens eines der beiden Features in den Optionen
aktiv ist, und meldet ihn über `entry.async_on_unload` wieder ab.

Zwei weitere Services, `read_modbus_register`/`write_modbus_register`, lesen
oder schreiben ein beliebiges Register per Adresse – gedacht, um ein noch
undokumentiertes Register zu erkunden. Sie adressieren immer den (einzigen)
aktuell eingerichteten Controller und lehnen ab, sobald mehr als einer läuft
(`_only_controller`).

## Konfigurationsdatei (`lambda_wp_config.yaml`)

Fast alles, was früher in dieser Datei stand, hat heute einen
Home-Assistant-eigenen Weg (Entity umbenennen/deaktivieren in der
Entity-Registry, `int32_register_order` in den Integrations-Optionen). Übrig
bleiben drei Dinge, für die es keinen HA-eigenen Ort gibt – siehe
`config_file.py`:

```python
TEMPLATE = """# ...
#cycling_offsets:
#  hp1:
#    heating_cycling_total: 0
#energy_consumption_offsets:
#  hp1:
#    heating_energy_total: 0.0
#energy_consumption_sensors:
#  hp1:
#    sensor_entity_id: sensor.heat_pump_electricity_meter
#    thermal_sensor_entity_id: sensor.heat_pump_heat_meter
"""
```

Die Datei wird beim ersten Start aus diesem Template angelegt (vollständig
auskommentiert) und **einmal pro Setup** gelesen; ein fehlerhafter Abschnitt
wird gemeldet und einzeln übersprungen (`_salvage`), statt die ganze Datei zu
verwerfen. Details: [modbus_wp_config.yaml – Entwicklereinstellungen](modbus-wp-config.md).

## Diagnose-Download

Der Diagnose-Download liest die rohen, unskalierten Register – genau wie sie
auf dem Draht ankommen – block- oder registerweise, je nachdem, was der
Controller tatsächlich beantwortet:

```python
# diagnostics.py
async def _async_read_registers(coordinator) -> dict[str, Any]:
    for low, high in readable_ranges(coordinator.counts):
        try:
            values = await coordinator.unit.read_holding_registers(low, high - low + 1)
        except ModbusExceptionError:
            await _read_by_register(coordinator, low, high, registers)
        else:
            registers.update(zip(range(low, high + 1), values, strict=True))
```

Damit lässt sich ein falsch wirkender Wert direkt gegen das Lambda-Datenblatt
prüfen, ohne ein separates Modbus-Tool zu benötigen – und ein noch nicht
modelliertes Register ist im Dump trotzdem sichtbar. Der Download enthält
außerdem `coordinator.totals` (die von der Integration selbst gezählten
Zyklen/Energiewerte) und den Status des letzten Polls
(`coordinator.updated`/`coordinator.failed`), damit sich ein falscher
Zählerstand von einem falsch gelesenen Register unterscheiden lässt.

## Zusammenfassung

- **Modbus-Kommunikation** über `modbus-connection`/`tmodbus`, mit erzwungenem
  Pacing statt eigenem Lock.
- **Registermodell** probiert sich selbst gegen die tatsächliche Firmware ein,
  statt eine feste Karte anzunehmen.
- **Zähler** sind reine Home-Assistant-`RestoreSensor`s ohne eigene
  Persistenzdatei; der Coordinator liefert nur Deltas seit dem letzten Blick.
- **COP** und **Heizkurve** sind zustandslose Ableitungen aus anderen
  Sensoren bzw. aus vom Nutzer gesetzten Werten.
- **PV-Überschuss/Raumthermostat** laufen als eigener Schreib-Timer, unabhängig
  vom Poll-Loop.
- **Konfigurationsdatei** ist auf die drei Dinge geschrumpft, für die
  Home Assistant selbst keinen Platz hat.
