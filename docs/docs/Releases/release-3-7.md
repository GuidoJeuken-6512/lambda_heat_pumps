---
title: "Release 3.7"
---

# Release 3.7

*Zuletzt geändert am 14.11.2026*

**3.7.1 ist das aktuelle Release** (14.11.2026). Es erweitert das Lambda Cockpit um mehrere Heizkreise, Kompressorstarts und eine Hilfe zu jeder Kachel. 3.7.0 (09.11.2026) brachte das **Lambda Cockpit** mit: ein fertiges Dashboard für die Wärmepumpe, das die Integration auf Wunsch selbst anlegt. Dazu kommen neue Sensoren für Laufzeiten und Umschaltungen sowie einige Korrekturen. Voraussetzung bleibt **Home Assistant 2026.9.0 oder neuer**.

Alle Einzeländerungen stehen im [Changelog](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/blob/main/CHANGELOG.md){:target="_blank" rel="noopener noreferrer"}. Wer von 2.x kommt, liest zuerst [Release 3.6](release-3-6.md).

## Neu in 3.7.1

- **Mehrere Heizkreise** ([#157](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/157)): Das Cockpit zeigt auf der Hauptseite die Kachel Heizbetrieb für jeden Heizkreis. Jeder Heizkreis bekommt einen eigenen Reiter mit Kachel, Heizkurve, Schaltpunkt und Grenzwerten. Mit einem Heizkreis bleibt alles wie bisher. Ein bestehendes Cockpit wird nicht von selbst neu geschrieben: Unter **Reparaturen** erscheint eine Meldung, die das anbietet und warnt, dass eigene Änderungen am Dashboard verloren gehen. Details: [Mehrere Heizkreise](../Anwender/lambda-cockpit.md#mehrere-heizkreise).
- **Neue Karte „Lambda Heizkreis“** (`custom:lambda-heating-circuit-card`) für eigene Dashboards, mit `circuit:` für den Heizkreis und `heating_type: radiator` für Heizkörper.
- **Kompressorstarts heute** im oberen Bereich ([#167](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/167)). Die drei Außentemperaturen stehen dafür neben dem Betriebszustand.
- **Vorlauf-Werte unter der Heizkurve** ([#156](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/156), [#128](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/128)): VL berechnet, VL Soll, VL ist und die Abweichung zwischen dem Soll der Lambda und dem berechneten Wert.
- **Hilfe zu jeder Kachel:** Ein kleines **?** öffnet den passenden Abschnitt der neuen Seite [Lambda Cockpit: die Kacheln](../Anwender/lambda-cockpit-kacheln.md) in einem neuen Tab. Dort steht auch, welche Werte vom Lambda-Display von Hand übertragen werden müssen.
- **Hinweise im Cockpit** ([#163](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/163)): Die Schaltpunkte erinnern daran, die kopierten Einstellwerte mit dem Display abzugleichen; die Heizkurve weist auf eine nicht passende Kopie der Heizkurve hin.

### Korrekturen in 3.7.1

- **Home Assistant 2026.11:** keine Veraltet-Warnungen mehr zu den Thermostaten für Warmwasser und Raum.
- **Suche in der Entitäten-Übersicht** ([#160](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/160)): Das Suchfeld verliert nach jedem Buchstaben nicht mehr den Fokus.
- **Heizkreis ohne eigenen Rücklauffühler:** kein leeres Rücklauf-Feld und kein leerer Schaltpunkt mehr.
- **Dashboard entfernen:** Ausschalten der Option entfernt das Dashboard auch dann, wenn die Integration früher gelöscht und neu eingerichtet wurde.

## Was neu ist in 3.7.0

- **Lambda Cockpit:** Unter **Konfigurieren** → **Dashboard „Lambda Cockpit“ installieren** legt die Integration ein Dashboard an: Wärmepumpe mit Betriebszustand, Warmwasser, Heizkreis, Heizkurve mit Wärmefahrplan, Schaltpunkte, Laufzeiten, Energie und Arbeitszahlen, dazu eine Übersicht aller Entitäten mit Erklärung. Nach dem Einschalten erscheint eine Reparaturmeldung, über die Home Assistant neu startet. Ausschalten entfernt das Dashboard wieder. Anleitung: [Lambda Cockpit](../Anwender/lambda-cockpit.md).
- **Bedienung im Cockpit:** Warmwasser-Solltemperatur, Offset der Heizkurve, Raum-Soll und maximale Puffertemperatur lassen sich direkt einstellen; die Werte gehen per Modbus an die Lambda.
- **Neue Sensoren** (für alle, auch ohne Dashboard):
    - Laufzeit Heizen, Warmwasser, Abtauen und Heizstab, gesamt und täglich.
    - Umschaltungen Heizen → Warmwasser, gesamt und täglich.
    - Außentemperatur, mit der die Lambda laut Wärmefahrplan rechnet (aus Soll-Vorlauf und Heizkurve zurückgerechnet).
- **Neue Regler:** Raum-Soll (Register 5051) auch ohne Raumthermostat-Steuerung, maximale Puffertemperatur (Register 3050).
- **Karten für eigene Dashboards:** `custom:lambda-cockpit-card` und `custom:lambda-entities-card` stehen nach der Installation immer zur Verfügung, auch ohne die Option.
- **Aktion** `lambda_heat_pumps.generate_dashboard` stellt ein von Hand gelöschtes Cockpit wieder her.

## Korrekturen in 3.7.0

- **Einzeln aktivierte Perioden-Sensoren bleiben aktiv.** Seit 3.6.1 hat das Speichern der Optionen aus einem beliebigen Grund (z. B. für das Cockpit) alle Perioden-Sensoren deaktiviert, wenn **Perioden-Energiesensoren aktivieren** aus war, auch einzeln eingeschaltete wie `hp1_compressor_start_cycling_daily`. Jetzt greift der Schalter nur noch, wenn Sie ihn tatsächlich umlegen.
- **Außentemperatur bei −0,1 °C** ([#153](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/153)): Der Wert wurde für einen Sonderwert gehalten, der Sensor sprang um den Gefrierpunkt ständig auf „unbekannt“.
- **Docker und ältere Installationen** ([#149](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/149)): `tmodbus` ab 0.6.1 ist jetzt eine eigene Anforderung.
- **Firefox:** Das Cockpit zeigte statt der Karten einen Konfigurationsfehler.

## Update

1. Integration in HACS aktualisieren und Home Assistant neu starten.
1. **Nach dem Update auf 3.7.1** die Cockpit-Seite im Browser einmal neu laden (Strg+F5; in der Companion App den Frontend-Cache zurücksetzen). Bei mehreren Heizkreisen die Reparaturmeldung **„Weitere Heizkreise zum Lambda Cockpit hinzufügen“** absenden, wenn Sie die neuen Reiter möchten.
2. Wer das Cockpit möchte: Option einschalten und der Anleitung [Lambda Cockpit](../Anwender/lambda-cockpit.md) folgen. Danach die Seite im Browser einmal neu laden.
3. **Perioden-Sensoren prüfen**, falls Sie unter 3.6.1 die Optionen gespeichert und danach einzelne Tages- oder Monatszähler vermisst haben: Diese wurden damals deaktiviert. Unter **Einstellungen** → **Entitäten** wieder aktivieren; das Update holt sie nicht von selbst zurück.

## Versionen 3.7

| Version | Wichtigste Änderung |
|---|---|
| 3.7.1 | Mehrere Heizkreise im Cockpit, Karte „Lambda Heizkreis“, Kompressorstarts heute, Vorlauf-Werte unter der Heizkurve, Hilfeseite je Kachel; Thermostate ohne Veraltet-Warnung in HA 2026.11 |
| 3.7.0 | Lambda Cockpit; Sensoren für Laufzeiten und Umschaltungen; Außentemperatur Wärmefahrplan; Regler Raum-Soll und maximale Puffertemperatur; Perioden-Schalter greift nur noch beim Umlegen |
| 3.6.3 (nicht einzeln veröffentlicht, in 3.7.0 enthalten) | Außentemperatur −0,1 °C nicht mehr „unbekannt“ (#153); `tmodbus>=0.6.1` als eigene Anforderung (#149) |
