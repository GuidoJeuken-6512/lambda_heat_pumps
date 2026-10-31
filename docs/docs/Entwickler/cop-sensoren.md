---
title: "COP-Sensoren - Technische Dokumentation"
---

# COP-Sensoren - Technische Dokumentation

*Zuletzt geändert am 06.09.2026*

**Stand:** Release 3.5.2 (Rewrite auf [`modbus-connection`](https://github.com/home-assistant-libs/modbus-connection)/`tmodbus`, Branch `3.5`; Hintergrund zum Rewrite: [Issue #99](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/99))

Diese Dokumentation beschreibt die technische Implementierung der COP-Sensoren (Coefficient of Performance) in der Lambda Heat Pumps Integration.

## Übersicht

**Formel:** `COP = Thermal Energy (kWh) / Electrical Energy (kWh)`

Es gibt zwei Arten von COP-Sensoren, beide in `sensor.py`, beide zustandslos
— keiner der beiden hält einen eigenen Wert oder muss über einen Neustart
restauriert werden:

| Klasse | Rechnet mit | Deckt ab |
|---|---|---|
| `LambdaCopSensor` | Zwei `LambdaCounterSensor`-Instanzen (von der Integration seit HA-Start gezählt) | Je Modus und Periode: `heating`/`hot_water`/`cooling` × `daily`/`monthly`/`yearly`/`total` (`heating` zusätzlich `hourly`) |
| `LambdaLifetimeCopSensor` | Die zwei Lifetime-Register des Controllers selbst | Ein Wert pro Wärmepumpe, unique_id-Schlüssel `cop_calc` |

## `LambdaCopSensor`: Verhältnis zweier Zähler

```python
# sensor.py
class LambdaCopSensor(LambdaEntity, SensorEntity):
    def __init__(self, coordinator, mode, period, index, *, thermal, electrical):
        ...
        self._thermal = thermal        # LambdaCounterSensor (thermisch)
        self._electrical = electrical  # LambdaCounterSensor (elektrisch)

    @property
    def native_value(self) -> float | None:
        electrical = self._electrical.native_value
        if not electrical:
            return None
        return round(self._thermal.native_value / electrical, 2)
```

Die beiden `LambdaCounterSensor`-Instanzen werden bereits bei der
Sensor-Erstellung als Paar übergeben (`sensor.py::async_setup_entry`) —
`LambdaCopSensor` sucht sie nicht selbst über den State-Store, sondern liest
sie als Python-Objekte direkt aus:

```python
for mode in COP_MODES:                       # heating, hot_water, cooling
    periods = COP_HEATING_PERIODS if mode == MODE_HEATING else COP_PERIODS
    entities += [
        LambdaCopSensor(
            coordinator, mode, period, index,
            thermal=counters[f"{mode}_thermal_energy_{period}"],
            electrical=counters[f"{mode}_energy_{period}"],
        )
        for period in periods
    ]
```

Weil eine Wärmepumpe im Standby zwar elektrisch, aber nicht thermisch
gezählt wird (siehe [Features – Cycling- und Energie-Zähler](features.md)),
gibt es keinen COP für `stby`/`defrost` — nur für die drei Modi, in denen
beide Seiten der Division existieren (`COP_MODES`).

### Warum keine Baseline mehr nötig ist

In der Vor-Rewrite-Integration kamen die thermischen Energy-Sensoren zeitlich
**nach** den bereits vorhandenen elektrischen hinzu — ein reiner
`Total_thermal / Total_electrical` hätte den COP über einen längeren
elektrischen als thermischen Zeitraum berechnet und verfälscht. Eine
"Baseline" (Differenz seit Stichtag) glich das aus.

Seit 3.5 werden **beide** Zähler eines Modus gleichzeitig mit derselben
Integration angelegt und zählen ab demselben Zeitpunkt (HA-Start bzw.
Neustart-Restore). Es gibt keinen Zeitversatz mehr auszugleichen — die
direkte Division ist bereits korrekt, `LambdaCopSensor` braucht keinen
eigenen State.

## `LambdaLifetimeCopSensor`: Controller-eigene Lifetime-Zähler

```python
# sensor.py
class LambdaLifetimeCopSensor(LambdaEntity, SensorEntity):
    @property
    def native_value(self) -> float | None:
        heat_pump = self.coordinator.component("hp", self._index)
        electrical = heat_pump.compressor_power_consumption_accumulated
        thermal = heat_pump.compressor_thermal_energy_output_accumulated
        if not electrical or thermal is None:
            return None
        return round(thermal / electrical, 2)
```

Dieser Sensor liest nicht die von der Integration gezählten Werte, sondern
die zwei 32-Bit-Register, die der Controller selbst seit seiner Installation
führt (`compressor_power_consumption_accumulated`/
`..._thermal_energy_output_accumulated`, siehe
[Sensoren-Übersicht](sensoren-uebersicht.md)). Das ist der einzige COP-Wert,
der auch Betriebsstunden vor der ersten Home-Assistant-Installation
einschließt — und der einzige, der bei einem Firmware- oder Zählerreset des
Controllers ebenfalls zurückspringt.

## Sensoren pro Wärmepumpe

| Mode | Perioden | Anzahl |
|------|----------|-------:|
| `heating` | daily, monthly, yearly, total, **hourly** | 5 |
| `hot_water` | daily, monthly, yearly, total | 4 |
| `cooling` | daily, monthly, yearly, total | 4 |
| Lifetime (`cop_calc`) | — | 1 |

**Total: 14 COP-Sensoren pro Wärmepumpe.** Nur die Total-Perioden (`_cop_total`
je Modus) sowie `cop_calc` sind standardmäßig aktiviert
(`entity_registry_enabled_default=period == PERIOD_TOTAL` in
`LambdaCopSensor.__init__`) — die übrigen Perioden folgen den
Zählern, die sie dividieren, welche ihrerseits nur als Total aktiviert sind.

## Division durch Null

`native_value` gibt `None` zurück, solange die Wärmepumpe in diesem Modus und
dieser Periode noch keine Elektroenergie verbraucht hat (`if not electrical`)
— nicht `0.0`. Ein COP von exakt 0 wäre eine irreführende Aussage über die
Effizienz; „noch keine Daten“ ist das, was tatsächlich der Fall ist.

## Betroffene Dateien

- **Klassen**: `custom_components/lambda_heat_pumps/sensor.py`
  (`LambdaCopSensor`, `LambdaLifetimeCopSensor`)
- **Registrierung**: `sensor.py::async_setup_entry`
- **Translations**: `custom_components/lambda_heat_pumps/translations/de.json` und `en.json`

## Verwandte Dokumentation

- [Features – COP-Sensoren](features.md#cop-sensoren)
- [Cycling- und Energie-Zähler](features.md) – Quelle der beiden Zähler pro COP
- [Sensoren-Übersicht](sensoren-uebersicht.md) – alle Sensoren im Überblick
