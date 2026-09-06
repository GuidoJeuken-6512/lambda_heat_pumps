---
title: "lambda_wp_config.yaml (Entwickler)"
---

# lambda_wp_config.yaml – Entwicklereinstellungen

*Zuletzt geändert am 06.09.2026*

**Stand:** Release 3.5.2 (Rewrite auf [`modbus-connection`](https://github.com/home-assistant-libs/modbus-connection)/`tmodbus`, Branch `3.5`; Hintergrund zum Rewrite: [Issue #99](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/99))

Die Datei `lambda_wp_config.yaml` (Pfad: `config/lambda_wp_config.yaml`)
deckt seit 3.5 nur noch die drei Dinge ab, für die Home Assistant selbst
keinen Platz hat. Alles andere aus der alten Datei — deaktivierte Register,
Sensor-Namensüberschreibungen, die Modbus-Registerreihenfolge — hat einen
eigenen, HA-nativen Weg bekommen (Entity deaktivieren/umbenennen in der
Entity-Registry, bzw. eine Integrations-Option).

## Die Datei wird nicht mehr migriert

`config_file.py::async_load()` liest die Datei einmal pro Setup und legt sie
beim ersten Start unverändert aus einem festen Template an — vollständig
auskommentiert:

```python
TEMPLATE = """# Configuration for the Lambda Heat Pumps integration.
#
# Everything here is optional, and everything here is commented out. Uncomment
# what you need and reload the integration.
#
# Renaming an entity, hiding one, or disabling one is done in Home Assistant
# itself now, not here.

#cycling_offsets:
#  hp1:
#    heating_cycling_total: 0
#    hot_water_cycling_total: 0
#    cooling_cycling_total: 0
#    defrost_cycling_total: 0
#    compressor_start_cycling_total: 0

#energy_consumption_offsets:
#  hp1:
#    heating_energy_total: 0.0
#    hot_water_energy_total: 0.0
#    cooling_energy_total: 0.0
#    defrost_energy_total: 0.0
#    heating_thermal_energy_total: 0.0
#    hot_water_thermal_energy_total: 0.0
#    cooling_thermal_energy_total: 0.0
#    defrost_thermal_energy_total: 0.0

#energy_consumption_sensors:
#  hp1:
#    sensor_entity_id: sensor.heat_pump_electricity_meter
#    thermal_sensor_entity_id: sensor.heat_pump_heat_meter
"""
```

Es gibt keine Funktion mehr, die fehlende Abschnitte nachträglich einfügt oder
Kommentar-Header aktualisiert — das Template ist die einzige Quelle, und nur
für eine **neue** Datei relevant. Eine bestehende Datei wird nie
umgeschrieben, nur gelesen.

## Validierung: pro Abschnitt, nicht pro Datei

`config_file.py` beschreibt die Datei mit einem `voluptuous`-Schema und lässt
unbekannte Top-Level-Schlüssel ausdrücklich zu (`extra=vol.ALLOW_EXTRA`) — so
bricht ein alter, nicht mehr unterstützter Abschnitt (z. B. das frühere
`modbus:`) das Einlesen nicht ab. Ist ein **bekannter** Abschnitt fehlerhaft,
wird nur dieser eine übersprungen und geloggt; die übrigen Abschnitte bleiben
nutzbar (`_salvage()`):

```python
_HEAT_PUMP = vol.Match(r"^hp\d+$", msg="expected a heat pump named hp1, hp2, ...")

_SCHEMA = vol.Schema(
    {
        vol.Optional("cycling_offsets", default=dict): {_HEAT_PUMP: {str: vol.Coerce(int)}},
        vol.Optional("energy_consumption_offsets", default=dict): {_HEAT_PUMP: {str: vol.Coerce(float)}},
        vol.Optional("energy_consumption_sensors", default=dict): {
            _HEAT_PUMP: {
                vol.Optional("sensor_entity_id"): str,
                vol.Optional("thermal_sensor_entity_id"): str,
            }
        },
    },
    extra=vol.ALLOW_EXTRA,
)
```

### Bekanntes Problem: ein falsch benannter Wärmepumpen-Schlüssel wird nicht gemeldet

`_HEAT_PUMP` soll laut Kommentar im Code dafür sorgen, dass ein Abschnitt mit
einem Schlüssel, der nicht `hp<Zahl>` entspricht (Tippfehler wie
`hp_1`, `wp1` oder `not_a_heat_pump`), als fehlerhaft erkannt, geloggt und via
`_salvage()` verworfen wird — genau wie ein falscher Werttyp. Das passiert in
der Praxis nicht: `extra=vol.ALLOW_EXTRA` steht zwar nur auf dem
Top-Level-Schema, `voluptuous` vererbt diese Einstellung aber an die
automatisch aus den Dict-Literalen kompilierten Sub-Schemas (`{_HEAT_PUMP:
{...}}`) weiter. Ein Schlüssel, der nicht auf `_HEAT_PUMP` passt, gilt damit
dort ebenfalls als "extra" und wird unverändert durchgereicht, statt eine
`vol.Invalid` auszulösen — der `_salvage()`-Pfad wird für diesen Fall nie
erreicht, es erscheint kein Logeintrag.

Der praktische Schaden bleibt klein: `LambdaFileConfig.offset()` und
`.meter()` schlagen nur unter dem exakten Schlüssel `hp{index}` nach, ein
Tippfehler wird dort also ohnehin nie gefunden. Der Offset/Meter wirkt für
niemanden — es fehlt lediglich die im Code versprochene Diagnose, die dem
Nutzer erklären würde, warum der Eintrag ohne Effekt bleibt. Ein falscher
**Werttyp** (z. B. Text statt Zahl) wird weiterhin korrekt erkannt und
gemeldet, weil `vol.Coerce()` dafür unabhängig vom `extra`-Modus prüft.

Regressionstests: `tests/test_config_file.py::test_a_malformed_value_is_dropped_but_the_rest_of_the_file_is_kept`
(Werttyp-Fehler, wird erkannt) und `test_a_broken_section_does_not_cost_the_others`
(falscher Schlüsselname, wird *nicht* erkannt — der Abschnitt bleibt
wirkungslos statt gemeldet zu werden). Gefunden bei der Testabdeckungs-Analyse
im September 2026; noch nicht behoben, da es sich um Integrationscode und
nicht um die Tests handelt.

## `cycling_offsets`

Offsets für Total-Cycling-Zähler (z. B. nach Pumpentausch). Nur ganzzahlige
Werte, positiv oder negativ; nur `*_cycling_total`-Sensoren.

```yaml
cycling_offsets:
  hp1:
    heating_cycling_total: 1500
    hot_water_cycling_total: 800
    cooling_cycling_total: 200
    defrost_cycling_total: 50
    compressor_start_cycling_total: 5000
```

## `energy_consumption_offsets`

Offsets für Total-Energieverbrauch (kWh), elektrisch und optional thermisch.
Nur `*_total`-Sensoren, positiv oder negativ.

```yaml
energy_consumption_offsets:
  hp1:
    heating_energy_total: 5000.0
    heating_thermal_energy_total: 6500.0
```

Wie beide Offset-Arten technisch angewendet werden (dieselbe Mechanik für
Cycling und Energie): [Offset-System](offset-system.md).

## `energy_consumption_sensors`

Ein externer Zähler statt des Controller-eigenen Registers, getrennt für
elektrisch und thermisch:

```yaml
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.shelly_lambda_gesamt_leistung"   # elektrisch
    thermal_sensor_entity_id: "sensor.waermemesser_hp1"        # optional, thermisch
```

Beide Felder sind optional; fehlt eines, verwendet der Coordinator das
Controller-Register für diese Energieart (`_meter_reading()` in
`coordinator.py`). Der konfigurierte Sensor muss eine **kumulative** Energie
in Wh, kWh oder MWh liefern — die Umrechnung nach Wh übernimmt der
Coordinator selbst. Ist der State `unknown`/`unavailable`, wird für diesen
Poll nichts gebucht statt auf das Controller-Register umzuschalten. Details:
[Features – Cycling- und Energie-Zähler](features.md).

## Was daraus entfallen ist

| Alter Abschnitt | Heutiger Ersatz |
|---|---|
| `disabled_registers` | Entity in der Home-Assistant-Entity-Registry deaktivieren |
| `sensors_names_override` | Entity in Home Assistant umbenennen |
| `modbus.int32_register_order` | Integrations-Option, siehe [Register-Reihenfolge](register-reihenfolge-int32.md) |

## Betroffene Dateien

| Datei | Rolle |
|---|---|
| `config_file.py` | `LambdaFileConfig`, `TEMPLATE`, Schema, `async_load()` |
| `coordinator.py` | `self.file_config`, gelesen in `_async_setup()` |
| `sensor.py` | `LambdaCounterSensor._apply_offset()` liest `file_config.offset()` |
