---
title: "Lambda Cockpit: die Kacheln"
---

# Lambda Cockpit: die Kacheln

*Zuletzt geändert am 14.11.2026*

Diese Seite erklärt jeden Teil des [Lambda Cockpits](lambda-cockpit.md). Das Symbol **?** oben an einer Kachel führt direkt zum passenden Abschnitt. Die kleinen **i** in den Kacheln klappen dagegen eine Kurzinfo direkt im Cockpit auf.

Ein Klick auf einen Wert öffnet seinen Verlauf. Ein „–“ heißt: Die Entität hat gerade keinen Wert oder ist deaktiviert.

!!! note "Werte aus dem Lambda-Display von Hand übertragen"
    Einige Werte im Cockpit sind **Kopien** der Einstellungen am Lambda-Display: die Stützpunkte der Heizkurve, die Hysteresen, die Spreizung, die Heizgrenze und die maximalen Temperaturen. Sie lassen sich leider nicht automatisch auslesen, weil die Lambda sie nicht per Modbus bereitstellt. Übertragen Sie sie einmal von Hand (Gerät → **Konfiguration**). Solange sie nicht stimmen, stimmen auch Heizkurve, Schaltpunkte und Heizgrenze im Cockpit nicht. Eine Änderung dieser Kopien verstellt die Lambda nicht.

## Oberer Bereich

**Betriebszustand** der Wärmepumpe (z. B. Heizbetrieb, Warmwasser, Abtauen) und seit wann er gilt. Daneben erscheinen bei Bedarf eine Fehlermeldung mit Nummer und der Hinweis **Heizstab**, wenn der Heizstab läuft.

**Außentemperaturen** rechts daneben:

- **AT Wärmefahrplan:** die Außentemperatur, mit der die Lambda laut Wärmefahrplan gerade rechnet. Die Integration rechnet sie aus dem Soll-Vorlauf über die Heizkurve zurück; sie stimmt nur, wenn die Kopie der Heizkurve zur Lambda passt (siehe [Heizkurve](#heizkurve)).
- **AT berechnet:** die von der Lambda berechnete (gemittelte) Außentemperatur.
- **AT ist:** die gemessene Lufttemperatur am Eingang der Wärmepumpe.

**Die Grafik der Wärmepumpe:** Der Lüfter dreht, solange der Verdichter läuft, und umso schneller, je höher die Leistung ist. Steht der Verdichter, steht auch der Lüfter. Links darüber und darunter erscheinen PV-Leistung und Hausbatterie, wenn sie in der Karte eingetragen sind (siehe [Stromquelle und Netzentgelt](#stromquelle-und-netzentgelt)).

**Die Werte der Wärmepumpe:**

| Wert | Bedeutung |
|---|---|
| Soll-VL / Soll WW | Vorlauf-Soll für den Heizbetrieb, im Warmwasserbetrieb das Warmwasser-Soll |
| VL, RL | Vorlauf und Rücklauf der Wärmepumpe |
| Verdichter | Leistung des Verdichters in Prozent |
| Abgabe, Aufnahme | Wärmeleistung und elektrische Leistung gerade jetzt |
| AZ | Arbeitszahl gerade jetzt (Abgabe ÷ Aufnahme) |
| Strom heute, AZ Tag | Strom seit Mitternacht und die Arbeitszahl des Tages |
| Laufzeit heute | Laufzeit des Verdichters seit Mitternacht; bei eingeschalteter PV-Überschuss-Steuerung steht hier stattdessen der **PV-Überschuss** |
| Abtauungen, Umschaltungen | Abtauungen und Wechsel von Heizen zu Warmwasser seit Mitternacht |
| Kompressorstarts heute | Starts des Verdichters seit Mitternacht. Zusammen mit der Laufzeit zeigt der Wert, wie stark die Wärmepumpe taktet |

## Brauchwasser

Der Warmwasserspeicher. Oben links steht die eingestellte Solltemperatur, oben rechts der Zustand (z. B. „STBY“, „Heizen“). Im Speicher steht die Temperatur am oberen Fühler.

Läuft die Zirkulationspumpe oder lief sie vor kurzem, steht daneben „Zirku läuft“ bzw. „vor … min“.

**Solltemperatur:** stellt die Warmwasser-Temperatur der Lambda (wird in die Lambda geschrieben).

## Puffer

Der Pufferspeicher mit den Temperaturen oben und unten. Oben links steht das Puffer-Soll: Soll-Vorlauf des Heizkreises plus **Solltemperaturoffset Heizbetrieb**. Der Offset ist eine Kopie vom Display (siehe Hinweis oben).

## Heizkreis

Die Kachel **Heizbetrieb** für einen Heizkreis. Oben links steht der Soll-Vorlauf, den die Lambda für den Heizkreis berechnet, oben rechts der Zustand des Heizkreises.

Im Bild: Rücklauf, Vorlauf und Raum-Soll; bei eingeschalteter Raumthermostat-Steuerung zusätzlich die Raumtemperatur vom gewählten Fühler. Hat der Heizkreis keinen eigenen Rücklauffühler, entfällt das Rücklauf-Feld.

**Raum-Soll:** die Raum-Solltemperatur des Heizkreises (wird in die Lambda geschrieben).

Das Bild zeigt eine Fußbodenheizung. Für Heizkörper in der Karten-YAML `heating_type: radiator` eintragen.

Bei mehreren Heizkreisen steht diese Kachel für jeden Heizkreis auf der Hauptseite, nummeriert („Heizkreis 1“, „Heizkreis 2“ …). Heizkurve, Schaltpunkt und Grenzwerte stehen dann auf dem Reiter des jeweiligen Heizkreises (siehe [Karte Lambda Heizkreis](#karte-lambda-heizkreis)).

## Heizkurve

Die Heizkurve des Heizkreises: Vorlauf-Soll abhängig von der Außentemperatur, gezeichnet durch die drei Stützpunkte bei −22 °C, 0 °C und +22 °C. Der Punkt zeigt, wo der Heizkreis gerade steht. Der **Offset Heizkurve** verschiebt die ganze Kurve nach oben oder unten (wird in die Lambda geschrieben).

!!! note "Stützpunkte von Hand übertragen"
    Die drei Stützpunkte sind Kopien der Heizkurve am Lambda-Display. Sie lassen sich leider nicht automatisch auslesen. Bitte von Hand übertragen, am Gerät des Heizkreises unter **Konfiguration**. Mehr dazu unter [Heizkurve](heizkurve.md).

**Wärmefahrplan:** Rechnet die Lambda gerade mit einer anderen Außentemperatur als der berechneten, zeigt die Kachel die Verschiebung. Zeigt sie eine Verschiebung, obwohl der Wärmefahrplan an der Lambda aus ist, passen die Stützpunkte nicht zur Lambda.

**Die Zeile unter der Kurve:**

- **VL berechnet:** der Vorlauf, den die Integration aus der Kopie der Heizkurve berechnet.
- **VL Soll:** der Soll-Vorlauf, den die Lambda vorgibt.
- **VL ist:** der gemessene Vorlauf des Heizkreises.
- **Soll − berechnet:** die Abweichung. Ab 1 K ist sie hervorgehoben; meist passt dann die Kopie der Heizkurve nicht.

## Schaltpunkte

Wann die Wärmepumpe für Warmwasser, Puffer und Heizkreis startet und stoppt. Je Block: die Temperatur, an der die Lambda schaltet, Start- und Stopp-Schwelle und der Zustand („läuft – Stopp ab …“, „wartet – Start unter …“). Das **i** am Block erklärt die Rechnung mit den eingetragenen Werten.

- **Warmwasser:** Start = Soll + Einschalthysterese, Stopp = Soll + Ausschalthysterese, verglichen mit dem oberen Fühler.
- **Puffer:** wie Warmwasser; die Einschalthysterese wird zwischen dem Wert bei 25 °C und dem bei 50 °C umgerechnet, so wie die Lambda „T-Ein“ anzeigt.
- **Heizkreis:** Rücklauf-Soll = Soll-Vorlauf − Spreizung; Start und Stopp über die Hysteresen des Heizkreises. Ohne eigenen Rücklauffühler des Heizkreises entfällt dieser Block.

Rechts oben steht, ob gerade PV-Überschuss eingerechnet ist.

!!! note "Hysteresen von Hand übertragen"
    Hysteresen, Spreizung und Solltemperaturoffset sind Kopien der Einstellungen am Lambda-Display. Sie lassen sich leider nicht automatisch auslesen und starten mit Standardwerten. Bitte von Hand übertragen (Gerät Boiler, Puffer bzw. Heizkreis → **Konfiguration**). Danach den Hinweis in der Kachel mit **ausblenden** schließen; das gilt für den jeweiligen Browser.

## Grenzwerte

Maximale Temperaturen und die Heizgrenze. Jede Zeile trägt ein Etikett:

- **Lambda:** wird direkt in die Lambda geschrieben (z. B. Puffer max.).
- **Kopie:** Für diesen Wert gibt es kein Modbus-Register. Er wird nur im Cockpit verwendet, z. B. für die Heizgrenze bei den Schaltpunkten. Eine Änderung hier verstellt die Lambda nicht.

!!! note "Kopien von Hand übertragen"
    Die Werte mit dem Etikett **Kopie** (Heizkreis max. VL, WW max. Soll, Heizgrenze AT) lassen sich leider nicht automatisch auslesen. Bitte vom Lambda-Display von Hand übertragen und bei einer Änderung in der Lambda hier mitändern.

## Laufzeiten heute

Der Ring zeigt die Laufzeit des Verdichters seit Mitternacht, oben rechts den Anteil am bisherigen Tag. Daneben die Aufteilung auf Heizen, Warmwasser, Abtauen und Heizstab; der Rest ist „Ruhe/Sonst.“.

Darunter: **Starts Heizen**, **Starts WW** und **Umschaltungen** von Heizen zu Warmwasser seit Mitternacht.

Am Tag der Installation beginnen die Zähler erst ab diesem Zeitpunkt. Die Zeit davor erscheint als „Ruhe/Sonst.“, auch wenn die Wärmepumpe lief.

## Energie heute

Strom und Wärme seit Mitternacht, getrennt für Heizen und Warmwasser, jeweils mit der Arbeitszahl (AZ). Oben rechts der Strom des Tages insgesamt.

**Herkunft heute** (PV + Speicher gegenüber Netz) erscheint nur, wenn die passenden Sensoren in der Karte eingetragen sind (`eigen_tag`, `netz_tag`).

## Effizienz

Jahresarbeitszahlen (JAZ) aus den Zählern:

- **gesamt:** aus den Energiezählern der Lambda selbst, also über die ganze Laufzeit der Wärmepumpe.
- **Heizen** und **Warmwasser:** aus den Zählern der Integration, also erst seit sie in Home Assistant zählen („seit HA“).

## Stromquelle und Netzentgelt

Beide Kacheln sind optional und erscheinen nur, wenn die Angaben in der Karten-YAML stehen (siehe [Optionale Angaben in der Karten-YAML](lambda-cockpit.md#optionale-angaben-in-der-karten-yaml)).

- **Stromquelle aktuell:** woher der Strom der Wärmepumpe gerade kommt: PV, Speicher, Netz.
- **Netzentgelt-Fenster:** die Tarifzonen des Tages mit Preis, die aktuelle Zone und wie lange sie noch gilt.

## Aktionen

**Funktionen & Zähler** öffnet ein Fenster mit:

- **Zähler:** Abtauungen heute und gesamt, Laufzeit seit dem Start bzw. Stillstand seit.
- **Alle Lambda-Entitäten:** die Übersicht aller Entitäten der Integration mit Erklärung und Suche.
- **Funktionen der Integration:** ob PV-Überschuss an Lambda und Raumtemperatur an Lambda eingeschaltet sind. Geschaltet werden sie unter **Einstellungen** → **Geräte & Dienste** → Lambda → **Konfigurieren**.

## Karte Lambda Heizkreis

Die Karte für einen einzelnen Heizkreis, im Cockpit auf dem Reiter **Heizkreis 1**, **Heizkreis 2** … bei mehreren Heizkreisen. Sie enthält die Kachel [Heizkreis](#heizkreis), die [Heizkurve](#heizkurve), den [Schaltpunkt](#schaltpunkte) des Heizkreises sowie Heizgrenze und maximalen Vorlauf (siehe [Grenzwerte](#grenzwerte)). Die Werte gelten für den Heizkreis aus `circuit:`.

Wie Sie die Karte in ein eigenes Dashboard einfügen, steht unter [Mehrere Heizkreise](lambda-cockpit.md#mehrere-heizkreise).
