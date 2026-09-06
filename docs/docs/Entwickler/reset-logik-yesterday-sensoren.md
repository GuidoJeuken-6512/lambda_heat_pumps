---
title: "Reset-Logik und Yesterday-Sensoren"
---

# Reset-Logik und Yesterday-Sensoren

*Zuletzt geändert am 06.09.2026*

**Stand:** Release 3.5.2 (Rewrite auf [`modbus-connection`](https://github.com/home-assistant-libs/modbus-connection)/`tmodbus`, Branch `3.5`; Hintergrund zum Rewrite: [Issue #99](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/99))

Diese Seite beschrieb bis 3.5.1 ein Differenzverfahren
(`daily = total - yesterday`) für Energie-Perioden-Sensoren, inklusive
mehrerer Restore-/Persistenz-Bugfixes rund um dieses Verfahren. Dieses
Verfahren gibt es seit dem Rewrite nicht mehr — Perioden-Zähler funktionieren
jetzt grundlegend anders und deutlich einfacher.

## Wie ein Perioden-Zähler heute zurückgesetzt wird

Jeder `LambdaCounterSensor` (`sensor.py`) — Cycling **und** Energie
gleichermaßen — hält genau **einen** Wert, `_value`, den er beim Neustart über
`RestoreSensor` unverändert zurückbekommt. Beim Rollover-Signal seiner Periode
wird dieser Wert schlicht auf `0.0` gesetzt:

```python
@callback
def _handle_rollover(self) -> None:
    """Start the period again at zero."""
    if self._yesterday is not None:
        self._yesterday.set_value(self._value)
    self._value = 0.0
    self.async_write_ha_state()
```

Es gibt kein separates „Total minus Vortag/Vormonat/Vorjahr“ mehr zu berechnen
und keine zweite, aus dem State-Attribut rekonstruierte Kennzahl — der
angezeigte Wert **ist** der gespeicherte Wert. Details zum Gesamtmechanismus:
[Ablaufdiagramm – Perioden-Rollover](Ablaufdiagramm.md#8-perioden-rollover-zähler-reset).

## Was aus „Yesterday“ geworden ist

„Yesterday“ existiert nur noch für **Cycling**-Tageszähler, als eigene,
zustandslose Sensor-Klasse `YesterdayCycleSensor`, die keinen eigenen Zähler
führt, sondern beim Rollover einfach den letzten Wert des Tageszählers
übernimmt (siehe Codeblock oben, `self._yesterday.set_value(self._value)` —
**vor** dem Zurücksetzen auf 0).

**Energie-Sensoren haben kein Yesterday-Gegenstück mehr.** Der alte
`_previous_monthly_value`/`_previous_yearly_value`/`_yesterday_value`-Zustand,
die dazugehörige Restore-Logik und sämtliche in der Vorversion dieser Seite
beschriebenen Konsistenzprüfungen (Basiswert ≤ Total nach Neustart) sind mit
diesem Zustand selbst entfallen — es gibt nichts mehr, was inkonsistent werden
könnte.

## Warum die alten Bugs strukturell nicht mehr auftreten können

Die früheren Probleme entstanden alle aus derselben Quelle: `_energy_value`
(der kumulative Zähler) und `native_value` (der angezeigte Perioden-Wert)
waren zwei verschiedene Zahlen, und mehrere Stellen im Code mussten synchron
bleiben, welche der beiden gerade gemeint war (Restore, Persistenz, Update).
Im aktuellen Modell gibt es diese Unterscheidung nicht: `_value` ist zugleich
der gespeicherte **und** der angezeigte Wert, `native_value` rundet ihn nur
noch für die Anzeige (siehe `LambdaCounterSensor.native_value` in
`sensor.py`). Eine Persistenzdatei (`cycle_energy_persist.json`), aus der
Werte beim Neustart hätten inkonsistent wiederhergestellt werden können,
existiert ebenfalls nicht mehr — `RestoreSensor` ist die einzige
Persistenzquelle.
