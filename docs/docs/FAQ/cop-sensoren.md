---
title: "FAQ – COP-Sensoren"
---

# COP-Sensoren: Periodische Werte und Anzeige

*Zuletzt geändert am 06.09.2026*

## Periodische COP-Werte bauen sich erst auf

Die **periodischen** COP-Sensoren (Daily, Monthly, Yearly) beziehen ihre Werte aus den jeweiligen Energieverbrauchssensoren für den gleichen Zeitraum. Diese Werte **bauen sich erst im Lauf der Zeit auf**:

- **Daily (Täglich)**: Ein sinnvoller COP-Wert entsteht erst, wenn im laufenden Tag sowohl thermische als auch elektrische Energie für die Betriebsart erfasst wurden.
- **Monthly (Monatlich)**: Erst im Lauf des Monats füllen sich die zugrundeliegenden Monatswerte; der COP ist erst nach einiger Zeit aussagekräftig.
- **Yearly (Jährlich)**: Der Jahres-COP wird erst im Lauf des Jahres mit Werten gefüllt.

## Unknown, wenn noch keine Berechnung möglich ist

Bis die Quellsensoren (thermische und elektrische Energie) für den jeweiligen Zeitraum Werte liefern, zeigt der COP-Sensor **`unknown`** – nie `0`, weil ein COP von 0 fälschlich eine (schlechte) Effizienz behaupten würde statt „noch keine Daten“.

Das ist **kein Fehler**: Sobald in der Periode sowohl thermische als auch elektrische Energie anfällt, wird der COP berechnet und angezeigt.

So bleiben die COP-Entitäten für das Kühlen so lange `unknown`, bis die Wärmepumpe im Betriebsmodus Kühlen gelaufen ist.

## Kein Baseline-Mechanismus mehr nötig (seit 3.5)

Bis Version 3.4 nutzte der Total-COP eine **Baseline** (Stichtag), weil die thermischen Energiezähler erst nachträglich zur Integration hinzukamen, während die elektrischen schon länger liefen. Seit dem 3.5-Rewrite werden pro Wärmepumpe **beide** Zähler eines Modus gleichzeitig angelegt und zählen ab demselben Zeitpunkt; eine Baseline-Korrektur ist dafür nicht mehr nötig, der Total-COP ist eine direkte Division der beiden Zähler.

Vollständige Beschreibung der COP-Sensoren: [Anwender – COP-Sensoren (Leistungszahl)](../Anwender/cop-sensoren.md).
