---
title: "Register-Reihenfolge für int32-Sensoren"
---

# Register-Reihenfolge für int32-Sensoren

*Zuletzt geändert am 06.09.2026*

**Stand:** Release 3.5.2 (Rewrite auf [`modbus-connection`](https://github.com/home-assistant-libs/modbus-connection)/`tmodbus`, Branch `3.5`; Hintergrund zum Rewrite: [Issue #99](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/99))

Technische Dokumentation zur konfigurierbaren Register-Reihenfolge
(Register/Word Order) bei den zwei 32-Bit-Zählern jeder Wärmepumpe
(`compressor_power_consumption_accumulated`,
`compressor_thermal_energy_output_accumulated`) und beim Solar-Energiezähler
(`energy_total`). Hintergrund: [Issue #22](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/22).

## Was sich geändert hat

Die Einstellung lebt nicht mehr in `lambda_wp_config.yaml`, sondern als
Options-Flow-Auswahl direkt an der Integration (`CONF_INT32_REGISTER_ORDER`,
`config_flow.py`) — änderbar unter Einstellungen → Integrationen → Lambda Heat
Pumps → Konfigurieren. Eine Änderung lädt die Integration automatisch neu
(`LambdaOptionsFlow` erbt von `OptionsFlowWithReload`).

## Firmware-abhängiger Standard

Anders als vorher ist `high_first` nicht mehr für jede Firmware der Standard.
`FIRMWARE_CONFIG` (`const.py`) hinterlegt pro Firmware-Version die tatsächlich
beobachtete Reihenfolge:

```python
FIRMWARE_CONFIG: Final[dict[str, dict[str, Any]]] = {
    "V1.1.0-3K": {"version": 9, "reg_order": "low_first"},
    "V0.0.10-3K": {"version": 8, "reg_order": "low_first"},
    "V0.0.9-3K": {"version": 7, "reg_order": "high_first"},
    # ... ältere Firmware-Versionen: "high_first"
}
```

`firmware.py::default_register_order(name)` liest diesen Wert aus; der
Coordinator verwendet ihn nur, wenn der Nutzer die Option nicht selbst gesetzt
hat:

```python
# coordinator.py – LambdaCoordinator.__init__
order = entry.options.get(CONF_INT32_REGISTER_ORDER) or default_register_order(
    self.firmware_version
)
```

## Wo die Reihenfolge tatsächlich wirkt

Anders als vorher gibt es keine eigene `combine_int32_registers()`-Funktion in
diesem Repository mehr — das Kombinieren zweier 16-Bit-Register zu einem
32-Bit-Wert übernimmt die Bibliothek `modbus-connection` selbst, gesteuert
über den `word_order`-Parameter (`"big"` = high_first, `"little"` =
low_first), den `LambdaHeatPump` beim Bau des Register-Modells entgegennimmt:

```python
# coordinator.py
word_order = "little" if order == REGISTER_ORDER_LOW_FIRST else "big"
self.device = LambdaHeatPump(unit, ..., word_order=word_order)
```

`lambda_modbus/__init__.py::LambdaHeatPump.async_setup()` wählt daraufhin die
passende Modell-Klasse für die beiden Module mit 32-Bit-Zählern:

```python
heat_pump_class = HeatPump if self._word_order == "big" else HeatPumpLowFirst
solar_class = Solar if self._word_order == "big" else SolarLowFirst
```

`HeatPumpLowFirst`/`SolarLowFirst` (`lambda_modbus/heat_pump.py`,
`lambda_modbus/solar.py`) sind schlichte Unterklassen, die nur die beiden
betroffenen Felder mit `word_order="little"` neu deklarieren — die restlichen
Register bleiben identisch zur Basisklasse.

## Migration bestehender Installationen

Eine Entry, die vor 3.5 angelegt wurde und die Option noch nicht gesetzt hat,
bekommt beim ersten Setup nach dem Update einmalig den bisherigen Wert aus der
**alten** `lambda_wp_config.yaml` übernommen (`modbus.int32_register_order`,
mit Rückwärtskompatibilität für das noch ältere `int32_byte_order`/`big`/
`little`) — siehe `_async_read_register_order()` in `__init__.py` und
[Migrationssystem](migration-system.md). Ist die Datei nicht lesbar oder der
Wert nicht gesetzt, greift der Firmware-Standard aus der Tabelle oben.

## Fehlerbehebung für Anwender

1. Falsche int32-Werte (Energiezähler springen unrealistisch oder zeigen
   negative/riesige Zahlen) → unter den Integrations-Optionen die
   Register-Reihenfolge auf den jeweils anderen Wert stellen.
2. Werte mit der Lambda-Software abgleichen.

Siehe auch: [FAQ – Falsche/keine Sensorwerte](../FAQ/falsche-keine-sensorwerte.md).
