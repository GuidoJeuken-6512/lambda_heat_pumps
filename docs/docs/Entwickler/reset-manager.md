---
title: "Perioden-Reset (früher: Reset-Manager)"
---

# Perioden-Reset (früher: Reset-Manager)

*Zuletzt geändert am 06.09.2026*

**Stand:** Release 3.5.2 (Rewrite auf [`modbus-connection`](https://github.com/home-assistant-libs/modbus-connection)/`tmodbus`, Branch `3.5`; Hintergrund zum Rewrite: [Issue #99](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/99))

Die Klasse `ResetManager` (`reset_manager.py`) gibt es seit dem 3.5-Rewrite
nicht mehr. Was sie leistete — pro Periode einen eigenen Timer registrieren
und beim Unload wieder abmelden — übernimmt jetzt ein einziger stündlicher
Timer im Coordinator selbst.

## Was an ihre Stelle getreten ist

`LambdaCoordinator._rollover()` läuft stündlich (`async_track_time_change`,
Minute/Sekunde 0) und ermittelt über `_periods_ending(now)`, welche der sechs
Perioden (`hourly`, `2h`, `4h`, `daily`, `monthly`, `yearly`) genau in dieser
Stunde enden — kein separates `asyncio`-Ereignis pro Periode mehr, keine
eigene Klasse, kein eigenes Cleanup: Der Timer wird wie jeder andere über
`entry.async_on_unload(...)` registriert und meldet sich beim Unload
automatisch ab.

Vollständiger Ablauf mit Diagramm:
[Ablaufdiagramm – Perioden-Rollover](Ablaufdiagramm.md#8-perioden-rollover-zähler-reset).

## Cycling- und Energie-Zähler laufen jetzt identisch

Der frühere Hauptvorteil des `ResetManager` — Cycling- und Energie-Sensoren auf
dieselbe Handler-Struktur zu bringen — ist heute kein Migrationsschritt mehr,
sondern der Ausgangszustand: **beide** sind Instanzen derselben Klasse,
`LambdaCounterSensor` (`sensor.py`), und ihr Reset-Handler ist dieselbe
Methode, `_handle_rollover()`, die für **jede** Periode außer `total` einfach
`self._value = 0.0` setzt (bei einem Cycling-Tageszähler zusätzlich den
aktuellen Wert an den `YesterdayCycleSensor` übergeben, bevor er auf 0 fällt).
Es gibt keine zwei parallelen Reset-Mechanismen mehr, die vereinheitlicht
werden müssten. Details zum Zähler selbst:
[Features – Cycling- und Energie-Zähler](features.md).
