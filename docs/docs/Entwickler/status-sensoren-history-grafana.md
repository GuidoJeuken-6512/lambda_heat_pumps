---
title: "Status-Sensoren: History und Grafana"
---

# Status-Sensoren: History und Grafana

*Zuletzt geändert am 06.09.2026*

**Stand:** Release 3.5.2 (Rewrite auf [`modbus-connection`](https://github.com/home-assistant-libs/modbus-connection)/`tmodbus`, Branch `3.5`; Hintergrund zum Rewrite: [Issue #99](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/99))

Diese Seite beschrieb ursprünglich einen Plan, Status-Sensoren (`operating_state`,
`state`, `error_state`, `operating_mode`, …) als `device_class: enum` zu
deklarieren, damit Home Assistant sie korrekt einordnet. Mit dem 3.5-Rewrite
ist das bereits umgesetzt.

## Aktueller Stand

Jeder Status-Sensor wird über den `_state()`-Helfer in `sensor.py` erzeugt:

```python
def _state(key: str, **kwargs) -> LambdaSensorDescription:
    """A register holding one of the controller's own state codes."""
    return LambdaSensorDescription(key=key, device_class=SensorDeviceClass.ENUM, **kwargs)
```

Die erlaubten Zustände (`options`) werden nicht mehr von Hand in einer
Konstanten gepflegt, sondern zur Laufzeit aus dem Register-Feld selbst
abgeleitet — jedes state-codierte Feld im Modell (`lambda_modbus/enums.py`)
kennt seine eigenen Labels:

```python
# entity.py – LambdaRegisterEntity.__init__
if description.device_class is SensorDeviceClass.ENUM:
    self._attr_options = [
        state.label for state in self._field(coordinator).convert
    ]
```

Damit sind alle Status-Sensoren als Enum-Entity mit vollständiger
`options`-Liste deklariert, sobald sie erzeugt werden — nicht mehr
nachträglich pro Sensor-Template gepflegt. Das entspricht Phase 1 des
ursprünglichen Plans.

## Was daraus nicht umgesetzt wurde

Die ursprünglich als Phase 2/3 skizzierten Ideen — den rohen Registerwert
zusätzlich als `raw_value`-Attribut zu exponieren, oder dedizierte numerische
Companion-Sensoren pro Status-Sensor anzulegen, um eine Zeitreihe direkt in
Grafana darstellen zu können — existieren im aktuellen Code nicht. Wer den
Betriebszustand als Zeitreihe braucht, muss weiterhin selbst einen
Template-Sensor bauen, der den Enum-Zustand auf eine Zahl abbildet, oder die
InfluxDB-Anbindung so konfigurieren, dass sie den Enum-State als Feld statt als
Tag exportiert.

## Betroffene Dateien

| Datei | Rolle |
|---|---|
| `sensor.py` | `_state()`-Helfer, `LambdaSensorDescription` |
| `entity.py` | `LambdaRegisterEntity.__init__` löst `options` aus dem Modell auf |
| `lambda_modbus/enums.py` | `LambdaState`-Unterklassen mit Code und Label je Zustand |
