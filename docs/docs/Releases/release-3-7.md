---
title: "Release 3.7"
---

# Release 3.7

*Zuletzt geändert am 09.11.2026*

**3.7.0 ist das aktuelle Release** (09.11.2026). Es bringt das **Lambda Cockpit** mit: ein fertiges Dashboard für die Wärmepumpe, das die Integration auf Wunsch selbst anlegt. Dazu kommen neue Sensoren für Laufzeiten und Umschaltungen sowie einige Korrekturen. Voraussetzung bleibt **Home Assistant 2026.9.0 oder neuer**.

Alle Einzeländerungen stehen im [Changelog](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/blob/main/CHANGELOG.md){:target="_blank" rel="noopener noreferrer"}. Wer von 2.x kommt, liest zuerst [Release 3.6](release-3-6.md).

## Was neu ist

- **Lambda Cockpit:** Unter **Konfigurieren** → **Dashboard „Lambda Cockpit“ installieren** legt die Integration ein Dashboard an: Wärmepumpe mit Betriebszustand, Warmwasser, Heizkreis, Heizkurve mit Wärmefahrplan, Schaltpunkte, Laufzeiten, Energie und Arbeitszahlen, dazu eine Übersicht aller Entitäten mit Erklärung. Nach dem Einschalten erscheint eine Reparaturmeldung, über die Home Assistant neu startet. Ausschalten entfernt das Dashboard wieder. Anleitung: [Lambda Cockpit](../Anwender/lambda-cockpit.md).
- **Bedienung im Cockpit:** Warmwasser-Solltemperatur, Offset der Heizkurve, Raum-Soll und maximale Puffertemperatur lassen sich direkt einstellen; die Werte gehen per Modbus an die Lambda.
- **Neue Sensoren** (für alle, auch ohne Dashboard):
    - Laufzeit Heizen, Warmwasser, Abtauen und Heizstab, gesamt und täglich.
    - Umschaltungen Heizen → Warmwasser, gesamt und täglich.
    - Außentemperatur, mit der die Lambda laut Wärmefahrplan rechnet (aus Soll-Vorlauf und Heizkurve zurückgerechnet).
- **Neue Regler:** Raum-Soll (Register 5051) auch ohne Raumthermostat-Steuerung, maximale Puffertemperatur (Register 3050).
- **Karten für eigene Dashboards:** `custom:lambda-cockpit-card` und `custom:lambda-entities-card` stehen nach der Installation immer zur Verfügung, auch ohne die Option.
- **Aktion** `lambda_heat_pumps.generate_dashboard` stellt ein von Hand gelöschtes Cockpit wieder her.

## Korrekturen

- **Einzeln aktivierte Perioden-Sensoren bleiben aktiv.** Seit 3.6.1 hat das Speichern der Optionen aus einem beliebigen Grund (z. B. für das Cockpit) alle Perioden-Sensoren deaktiviert, wenn **Perioden-Energiesensoren aktivieren** aus war, auch einzeln eingeschaltete wie `hp1_compressor_start_cycling_daily`. Jetzt greift der Schalter nur noch, wenn Sie ihn tatsächlich umlegen.
- **Außentemperatur bei −0,1 °C** ([#153](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/153)): Der Wert wurde für einen Sonderwert gehalten, der Sensor sprang um den Gefrierpunkt ständig auf „unbekannt“.
- **Docker und ältere Installationen** ([#149](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/149)): `tmodbus` ab 0.6.1 ist jetzt eine eigene Anforderung.
- **Firefox:** Das Cockpit zeigte statt der Karten einen Konfigurationsfehler.

## Update

1. Integration in HACS aktualisieren und Home Assistant neu starten.
2. Wer das Cockpit möchte: Option einschalten und der Anleitung [Lambda Cockpit](../Anwender/lambda-cockpit.md) folgen. Danach die Seite im Browser einmal neu laden.
3. **Perioden-Sensoren prüfen**, falls Sie unter 3.6.1 die Optionen gespeichert und danach einzelne Tages- oder Monatszähler vermisst haben: Diese wurden damals deaktiviert. Unter **Einstellungen** → **Entitäten** wieder aktivieren; das Update holt sie nicht von selbst zurück.

## Versionen 3.7

| Version | Wichtigste Änderung |
|---|---|
| 3.7.0 | Lambda Cockpit; Sensoren für Laufzeiten und Umschaltungen; Außentemperatur Wärmefahrplan; Regler Raum-Soll und maximale Puffertemperatur; Perioden-Schalter greift nur noch beim Umlegen |
| 3.6.3 (nicht einzeln veröffentlicht, in 3.7.0 enthalten) | Außentemperatur −0,1 °C nicht mehr „unbekannt“ (#153); `tmodbus>=0.6.1` als eigene Anforderung (#149) |
