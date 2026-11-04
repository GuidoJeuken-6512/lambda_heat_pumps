---
title: "Lambda Cockpit"
---

# Lambda Cockpit

*Zuletzt geändert am 04.11.2026*

Ab Version 3.7.0 bringt die Integration ein fertiges Dashboard mit: das **Lambda Cockpit**. Es zeigt die Wärmepumpe auf einer Seite, mit animierter Außeneinheit, Warmwasser, Puffer und Heizkreis im Stil der Lambda-Regelung, Heizkurve mit Wärmefahrplan, Schaltpunkten, Laufzeiten, Energie und Jahresarbeitszahl. Dazu kommt eine Übersicht aller Entitäten der Integration, sortiert nach Modulen und mit einer Erklärung zu jedem Wert.

Die Texte erscheinen auf Deutsch oder Englisch, je nach Sprache Ihres Benutzerprofils in Home Assistant.

## Dashboard installieren

1. **Einstellungen** → **Geräte & Dienste** → Lambda → **Konfigurieren**.
2. **Dashboard „Lambda Cockpit“ installieren** einschalten und **Absenden**.

    <img src="../assets/options_cockpit_de.png" alt="Options-Dialog mit dem Schalter Dashboard Lambda Cockpit installieren" style="max-width: 480px; width: 100%; height: auto; border-radius: 8px;">

3. Die Integration legt das Dashboard an. Kurz danach erscheint unter **Einstellungen** → **Reparaturen** der Eintrag **„Home Assistant neu starten, um das Lambda Cockpit anzuzeigen“** (Warnung, gemeldet von Lambda Heat Pumps).
4. Den Eintrag öffnen. Der Dialog **„Home Assistant neu starten“** erklärt, dass das Dashboard erst nach einem Neustart erscheint. Mit **OK** startet Home Assistant sofort neu.

    <img src="../assets/repair_cockpit_restart_de.png" alt="Reparatur Home Assistant neu starten, um das Lambda Cockpit anzuzeigen, mit dem Dialog Home Assistant neu starten und dem Knopf OK" style="width: 100%; height: auto; border-radius: 8px;">

5. Nach dem Neustart ist das Dashboard eingebunden: **Lambda Cockpit** steht in der Seitenleiste, und der Reparatur-Eintrag ist verschwunden.
6. Fehlt der Eintrag in der Seitenleiste oder meldet das Dashboard statt der Karten einen Fehler zu `lambda-cockpit-card`, die Seite im Browser neu laden (F5; in der Companion App die Seite herunterziehen bzw. den Frontend-Cache zurücksetzen). Der Browser zeigt dann noch den Stand von vor dem Neustart.

!!! note "Warum ein Neustart?"
    Home Assistant liest die Liste der Dashboards nur beim Start. Ein neu angelegtes Dashboard erscheint deshalb erst danach. Spätere Aktualisierungen des Dashboards durch die Integration brauchen keinen Neustart mehr.

Das Dashboard können Sie wie jedes andere bearbeiten. Ändert eine neue Version der Integration den Aufbau, wird es einmal neu geschrieben; eigene Änderungen gehen dann verloren. Wer viel anpasst, kopiert sich die Karten besser in ein eigenes Dashboard.

## Dashboard entfernen

Schalten Sie **Dashboard „Lambda Cockpit“ installieren** unter **Konfigurieren** wieder aus und **Absenden**. Die Integration entfernt dann das Dashboard und die Einstellwerte, die nur das Cockpit brauchte. Ein Neustart ist dafür nicht nötig; steht der Eintrag noch in der Seitenleiste, die Seite im Browser neu laden.

!!! warning "Eigene Änderungen gehen verloren"
    Haben Sie das Dashboard angepasst, sind diese Änderungen nach dem Ausschalten weg. Wer etwas behalten will, kopiert die Karten vorher in ein eigenes Dashboard.

Ein von Hand gelöschtes Dashboard (**Einstellungen** → **Dashboards**) stellt die Aktion `lambda_heat_pumps.generate_dashboard` (Entwicklerwerkzeuge → Aktionen) wieder her.

## Was die Integration dafür anlegt

Mit der Option entstehen zusätzlich **Einstellwerte**, die das Cockpit für die Schaltpunkte braucht. Die Lambda stellt sie nicht per Modbus bereit, sie sind eine **Kopie** der Werte aus dem Lambda-Display. Tragen Sie sie einmal ein (Gerät → **Konfiguration**):

| Gerät | Einstellung |
|---|---|
| Boiler | Warmwasser Einschalthysterese, Ausschalthysterese, maximale Solltemperatur |
| Puffer | Einschalthysterese bei 25 °C und bei 50 °C, Ausschalthysterese, Solltemperaturoffset Heizbetrieb |
| Heizkreis | Einschalthysterese, Ausschalthysterese, Temperaturspreizung, Heizgrenze Außentemperatur, maximale Vorlauftemperatur |

Eine Änderung dieser Werte verstellt die Lambda nicht. Ändern Sie sie bei Bedarf in der Lambda selbst mit.

Die Tageszähler, die das Cockpit zeigt (Energie, Starts, Abtauungen, Laufzeiten), schaltet die Option ein, auch wenn **Perioden-Energiesensoren aktivieren** aus ist.

## Neue Sensoren und Regler (für alle, auch ohne Dashboard)

- **Laufzeit Heizen / Warmwasser / Abtauen / Heizstab**, gesamt und täglich, in Stunden.
- **Umschaltungen Heizen-Warmwasser**, gesamt und täglich. Gezählt wird ein Wechsel direkt von Heizen zu Warmwasser oder über eine Pause von höchstens 10 Minuten.
- **Außentemperatur Wärmefahrplan ber.** (Heizkreis): die Außentemperatur, mit der die Lambda laut Wärmefahrplan gerade rechnet. Die Integration rechnet sie aus dem Soll-Vorlauf (Register 5007) über die [Heizkurve](heizkurve.md) zurück, abzüglich des Offsets. Die Genauigkeit liegt bei etwa ±0,4 K und hängt davon ab, dass die Stützpunkte der Heizkurve mit der Lambda übereinstimmen.
- **Raum-Soll** (Heizkreis, Register 5051) als Regler, auch ohne Raumthermostat-Steuerung.
- **Maximale Puffertemperatur** (Puffer, Register 3050) als Regler.

## Was das Cockpit zeigt und was nicht

- **Raumtemperatur:** nur bei eingeschalteter Raumthermostat-Steuerung, dann vom dort gewählten Fühler.
- **PV-Überschuss:** nur bei eingeschalteter PV-Überschuss-Steuerung.

### Optionale Angaben in der Karten-YAML

PV-Leistung, Hausbatterie, Stromquelle der Wärmepumpe und Netzentgelt-Fenster gehören nicht zur Integration. Wer sie sehen möchte, trägt sie im Karten-Editor ein (Dashboard bearbeiten → Karte → Code-Editor):

```yaml
type: custom:lambda-cockpit-card
entities:
  pv_power: sensor.mein_wechselrichter_leistung   # W
  bat_soc: sensor.mein_speicher_ladezustand       # %
  bat_charge: sensor.mein_speicher_laden          # W
  bat_discharge: sensor.mein_speicher_entladen    # W
tariffs:
  standard: { name: Standard, price: 12.00, color: "#60a5fa" }
  windows:
    - { from: 0, to: 6, name: Niedrig, price: 2.00, color: "#34d399" }
    - { from: 17, to: 20, name: Hoch, price: 20.00, color: "#f87171" }
```

Die übrigen Einträge unter `entities:` hat die Integration beim Anlegen selbst eingetragen, die bleiben stehen.

## Mehrere Wärmepumpen oder Heizkreise

Das Cockpit zeigt Wärmepumpe 1, Boiler 1, Puffer 1 und Heizkreis 1. Mit mehreren Lambda-Anlagen wird das Dashboard für die zuletzt eingerichtete geschrieben. Andere Module lassen sich in der Karten-YAML eintragen, indem Sie die Entitäten unter `entities:` austauschen.

## Die Karten in einem eigenen Dashboard

Die Karten `custom:lambda-cockpit-card` und `custom:lambda-entities-card` sind nach der Installation der Integration immer verfügbar, auch ohne die Option. Fügen Sie die Cockpit-Karte ohne `entities:` hinzu, sucht sie sich die Entitäten der ersten Lambda selbst.

Weitere Informationen: [Optionen des Config Flow](optionen-config-flow.md), [Heizkurve](heizkurve.md)
