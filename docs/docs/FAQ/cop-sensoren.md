---
title: "FAQ – COP-Sensoren"
---

# COP-Sensoren: Periodische Werte und Anzeige

## Periodische COP-Werte bauen sich erst auf

Die **periodischen** COP-Sensoren (Daily, Monthly, Yearly) beziehen ihre Werte aus den jeweiligen Energieverbrauchssensoren für den gleichen Zeitraum. Diese Werte **bauen sich erst im Lauf der Zeit auf**:

- **Daily (Täglich)**: Ein sinnvoller COP-Wert entsteht erst, wenn im laufenden Tag sowohl thermische als auch elektrische Energie für die Betriebsart erfasst wurden.
- **Monthly (Monatlich)**: Erst im Lauf des Monats füllen sich die zugrundeliegenden Monatswerte; der COP ist erst nach einiger Zeit aussagekräftig.
- **Yearly (Jährlich)**: Der Jahres-COP wird erst im Lauf des Jahres mit Werten gefüllt.

## Unknown oder 0, wenn noch keine Berechnung stattgefunden hat

Bis die Quellsensoren (thermische und elektrische Energie) für den jeweiligen Zeitraum Werte liefern, kann der COP-Sensor

- **`unknown`** anzeigen (wenn die Berechnung noch nicht möglich ist), oder  
- **`0`** anzeigen (wenn z. B. noch keine elektrische Energie erfasst wurde).

Das ist **kein Fehler**: Sobald in der Periode sowohl thermische als auch elektrische Energie anfällt, wird der COP berechnet und angezeigt.

So sind die COP Entitäten für das Kühlen solange "unknown" oder "0", bis die Wärmepumpe im Betriebsmodus Kühlen gewesen ist.

## Total-COP und Baseline

Der **Total-COP** nutzt eine **Baseline** (Stichtag), weil die elektrischen Verbrauchssensoren oft länger im System sind als die thermischen. Der Total-COP entspricht dem COP **seit Einführung der thermischen Sensoren** (Deltas seit Baseline). Direkt nach dem Setzen der Baseline kann der Total-COP kurzzeitig noch `unknown` oder `0` sein, bis beide Deltas (thermisch und elektrisch) positiv sind.

Vollständige Beschreibung der COP-Sensoren: [Anwender – COP-Sensoren (Leistungszahl)](../Anwender/cop-sensoren.md).
