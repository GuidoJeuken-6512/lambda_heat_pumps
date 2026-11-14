---
title: "Features"
---

# Features der Lambda Heat Pumps Integration

*Zuletzt geändert am 14.11.2026*

Die Lambda Heat Pumps Integration bietet umfassende Funktionen zur Steuerung und Überwachung Ihrer Lambda-Wärmepumpe über Home Assistant. Hier finden Sie eine Übersicht aller verfügbaren Features.

Diese Dokumentation beschreibt **Version 3.7**. Sie setzt **Home Assistant 2026.9.0 oder neuer** voraus.

## 🖥️ Lambda Cockpit (Dashboard) – neu ab 3.7.0

Die Integration bringt ein fertiges Dashboard mit, das sich mit einem Schalter in den Optionen anlegen lässt:

- **Cockpit:** Betriebszustand mit animierter Außeneinheit, Vorlauf/Rücklauf, Verdichter, Leistung und Arbeitszahl, Kompressorstarts heute, Warmwasser, Puffer und Heizkreis im Stil der Lambda-Regelung, Heizkurve mit Außentemperatur laut Wärmefahrplan, aktuelle Schaltpunkte, Laufzeiten, Energie heute und Jahresarbeitszahl.
- **Bedienung direkt im Cockpit:** Warmwasser-Solltemperatur, Heizkurven-Offset, Raum-Soll und maximale Puffertemperatur.
- **Mehrere Heizkreise (ab 3.7.1):** Kachel Heizbetrieb je Heizkreis auf der Hauptseite und ein Reiter je Heizkreis mit Heizkurve, Schaltpunkt und Grenzwerten; dazu die Karte **Lambda Heizkreis** für eigene Dashboards.
- **Hilfe zu jeder Kachel (ab 3.7.1):** Das **?** öffnet die Erklärung auf der Seite [Lambda Cockpit: die Kacheln](lambda-cockpit-kacheln.md).
- **Entitäten-Übersicht:** alle Entitäten der Integration nach Modulen sortiert, mit Suche und Erklärung zu jedem Wert.
- **Deutsch und Englisch**, je nach Sprache des Benutzerprofils.

Einrichtung und Details: [Lambda Cockpit](lambda-cockpit.md)

## 🔌 Modbus/TCP Kommunikation

- **Vollständige Modbus/TCP-Unterstützung**: Komplette Kommunikation mit Lambda-Wärmepumpen über das Modbus TCP-Protokoll. Alle Sensoren, die die Lambda über die Modbus Schnittstelle zur Verfügung stellt, sind in der Integration vorhanden.
- **Asynchrone Modbus-Operationen**: Nicht-blockierende Modbus-Kommunikation für optimale Performance
- **Automatische Verbindungsverwaltung**: Intelligente Verbindungsverwaltung mit automatischer Wiederverbindung bei Verbindungsabbrüchen
- **Register-Reihenfolge-Konfiguration**: Konfigurierbare Register-Reihenfolge für 32-Bit-Werte aus mehreren 16-Bit-Registern

## 🔍 Automatische Modulerkennung

- **Hardware-Erkennung**: Automatische Erkennung verfügbarer Module (Wärmepumpen, Warmwasser Modul, Puffer, Solar, Heizkreise)
- **Dynamische Entity-Erstellung**: Automatische Erstellung aller Sensoren und Entities basierend auf erkanntem Hardware
- **Automatische Erkennung im Netzwerk**: Home Assistant schlägt eine Lambda im Netzwerk als „Entdeckt“ vor
- **Konfigurationsvalidierung**: Verhindert doppelte Konfigurationen und prüft die Verbindung vor dem Anlegen

## 📊 Taktung-Sensoren

Umfassende Zähler für alle Betriebsmodi:

### Betriebsmodi
- **Heizen**: Zähler für Heizbetrieb
- **Warmwasser**: Zähler für Warmwasserbereitung
- **Kühlen**: Zähler für Kühlbetrieb
- **Abtauen**: Zähler für Abtauzyklen
- **Kompressor-Starts**: Spezieller Sensor für Kompressor-Start-Ereignisse

**Die Kompressor Starts sind die "schädlichen" Taktungen**

### Zeiträume

| Zeitraum | Heizen | Warmwasser | Kühlen | Abtauen | Kompressor-Start |
|----------|--------|------------|--------|---------|-----------------|
| Total | ✓ | ✓ | ✓ | ✓ | ✓ |
| Gestern | ✓ | ✓ | ✓ | ✓ | ✓ |
| Täglich | ✓ | ✓ | ✓ | ✓ | ✓ |
| 2 Stunden | ✓ | ✓ | ✓ | ✓ | ✓ |
| 4 Stunden | ✓ | ✓ | ✓ | ✓ | ✓ |
| Monatlich | — | — | — | — | ✓ |

Standardmäßig aktiv sind nur die Total-Zähler; die übrigen Zeiträume lassen sich beim Gerät unter „Entitäten“ einschalten.

### Umschaltungen und Laufzeiten (neu ab 3.7.0)
- **Umschaltungen Heizen → Warmwasser**: gesamt und täglich; gezählt wird ein direkter Wechsel oder einer über eine Pause von höchstens 10 Minuten
- **Laufzeit Heizen, Warmwasser, Abtauen und Heizstab**: gesamt und täglich, in Stunden

### Funktionen
- **Automatischer Reset**: Tägliche Sensoren werden automatisch um Mitternacht zurückgesetzt
- **Offset-Konfiguration**: Anpassbare Zählerstände für Wärmepumpenwechsel oder Zählerrücksetzungen

## ⚡ Energieverbrauchssensoren

Detaillierte Energieverfolgung nach Betriebsart:

### Betriebsmodi (elektrisch)
- **Heizen**: Energieverbrauch für Heizbetrieb
- **Warmwasser**: Energieverbrauch für Warmwasserbereitung
- **Kühlen**: Energieverbrauch für Kühlbetrieb
- **Abtauen**: Energieverbrauch für Abtauzyklen
- **Standby**: Energieverbrauch im Standby-Betrieb

### Betriebsmodi (thermisch / Wärmeabgabe)
- **Heizen**, **Warmwasser**, **Kühlen**, **Abtauen** (kein Standby-Thermik-Sensor)

### Zeiträume
- **Total**: Gesamtverbrauch seit Installation
- **Stündlich**: Stündlicher Energieverbrauch (nur Heizen, elektrisch und thermisch)
- **Täglich**: Täglicher Energieverbrauch
- **Monatlich**: Monatlicher Energieverbrauch
- **Jährlich**: Jährlicher Energieverbrauch

### Funktionen
- **Konfigurierbare Quellsensoren**: Beliebige Energiezähler als Datenquelle. Wenn ein externer Stromverbrauchssensor (z.B. Shelly 3EM) vor der Wärmepumpe verbaut wurde, so kann dieser für die Berechnung des Stromverbrauchs benutzt werden. Externe Stromverbrauchssensor sind meist genauer als der interne Sensor der Lambda.
Weitere Details und eine vollständige Auflistung aller Energieverbrauchssensoren finden Sie hier: [Energie- und Wärmeverbrauchsberechnung](Energieverbrauchsberechnung.md)


## 🌡️ Heizkurven-Konfiguration

Heizkurven-Berechnung und -Steuerung:

Die Funktion der Heizkurven-Berechnung ist hier näher erklärt: [Heizkurve](heizkurve.md)

Neu ab 3.7.0: Der Sensor **Außentemperatur Wärmefahrplan ber.** zeigt, mit welcher Außentemperatur die Lambda laut Wärmefahrplan gerade rechnet. Die Integration rechnet sie aus dem Soll-Vorlauf über die Heizkurve zurück.

## 🏠 Raumthermostat-Steuerung

Es kann ein beliebiges Thermometer aus Home Assistant zur Steuerung pro Heizkreis eingebudnen werden. Die Lambda erhöht / verringert dann die Vorlauftemperatur je nachdem, ob die Temperatur über oder unter dem Soll-Temperaturwert ist.

Die genaue Funktion und Einrichtung eines Raumthermometers zur Steuerung der Lambda ist hier erklärt: [Raumthermometer](raumthermometer.md)

## 🌞 PV-Überschuss-Steuerung

Optimale Nutzung von Solarstrom:

Ein beliebiger Sensor, der den PV-Überschuss eurer PV-Anlage darstellt, kann hier eingebunden werden. Die Integration übermittelt dann den Überschuss an die Lambda, die wiederum ihre Steuerung danach ausrichtet.

## 💧 Warmwasser-Steuerung
Über die Klima-Entität **Warmwasser** (`climate.<name>_boil1_hot_water`) lässt sich die Solltemperatur der Warmwasserbereitung einstellen.
- **Temperaturbereich**: Konfigurierbarer Bereich (Standard: 25-65°C)

## 🏠 Heizkreis und Kühlkreis
- **Heizkreis** (`climate.<name>_hc1_heating_circuit`): Raum-Ist- und Raum-Solltemperatur des Heizkreises
- **Kühlkreis** (`climate.<name>_hc1_cooling_circuit`, mit der Option „Kühlen“): Raum-Solltemperatur im Kühlbetrieb
- **Vorlauf-Offset** (`number.<name>_hc1_flow_line_offset_temperature_number`): verschiebt die Vorlauftemperatur der Lambda um bis zu ±10 K
- **Raum-Soll** (`number.<name>_hc1_target_room_temperature_number`, neu ab 3.7.0): Raum-Solltemperatur der Lambda (Register 5051), auch ohne Raumthermostat-Steuerung
- **Maximale Puffertemperatur** (`number.<name>_buff1_maximum_buffer_temp_number`, neu ab 3.7.0, nur mit Puffer): Register 3050


## 🎛️ Erweiterte Konfiguration

### YAML-basierte Konfiguration
- **`lambda_wp_config.yaml`**: Für die Dinge, die es sonst nirgends gibt
- **Cycling-Offsets**: Anpassung von Zählerständen
- **Energieverbrauchs-Offsets**: Anpassung von Energie-Zählerständen
- **Energieverbrauchssensoren**: Konfiguration externer Energiezähler

Register deaktivieren oder Sensoren umbenennen geht seit Version 3.5 direkt in Home Assistant (Entität deaktivieren/umbenennen), nicht mehr über diese Datei. Die optionale Konfiguration über die `lambda_wp_config.yaml` ist hier erklärt: [Optionale Konfiguration](lambda-wp-config.md)

### Integration-Optionen
Nach der Ersteinrichtung können Sie zusätzliche Einstellungen anpassen:
- Warmwassertemperaturbereich (min/max)
- Heizkreistemperaturbereich (min/max)
- Temperaturstufengröße
- Abfrage-Intervall
- Register-Reihenfolge (für 32-Bit-Register)
- Raumthermostatsteuerung
- Kühlen (Kühlkreis-Entität)
- PV-Überschuss-Steuerung und Kodierung des PV-Überschusses
- Perioden-Energiesensoren aktivieren
- Dashboard „Lambda Cockpit“ installieren (neu ab 3.7.0)

Alle Optionen im Detail: [Optionen des Config Flow](optionen-config-flow.md)

Die Firmware-Version gehört **nicht** zu diesen Optionen – sie wird nur beim Ersteinrichten oder über „Neu konfigurieren" gesetzt (siehe [Firmware-Version ändern](firmware-wechsel.md)).

## 🔧 Modbus-Aktionen

Direkter Zugriff auf Modbus-Register:
Über die EntwicklerTools in Home Assistant können Register der Lambda Wärmepumpe ausgelesen und auch geschreiben werden.
Damit kann jedes Register in einer Automatisierung in Home Assistant verwendet / gesteuert werden.

### Verfügbare Aktionen
- **`read_modbus_register`**: Lesen von Werten aus Modbus-Registern
- **`write_modbus_register`**: Schreiben von Werten in Modbus-Register
- **`update_room_temperature`**: Raumtemperaturen sofort an die Heizkreise senden (sonst alle 9 Sekunden)
- **`generate_dashboard`**: das Dashboard „Lambda Cockpit“ neu schreiben, z. B. nach dem Löschen (neu ab 3.7.0)

Details: [Aktionen](aktionen-modbus.md)


## 🌍 Mehrsprachige Unterstützung

- **Deutsch und Englisch**: Vollständige Übersetzungen für alle Entity-Namen
- **Automatische Lokalisierung**: Integration in Home Assistants Übersetzungssystem
- **Konsistente Namensgebung**: Verbesserte Entity-Namensgebung mit Geräte- und Sub-Geräte-Präfixen

## 📱 Geräte-Hierarchie

- **Haupt- und Sub-Geräte**: Klare Strukturierung für bessere Organisation
- **Klarere Entity-Struktur**: Verbesserte Übersichtlichkeit in Home Assistant


## 🛡️ Fehlerbehandlung

- **Detailliertes Logging**: Umfassende Protokollierung für Fehleranalyse, Info / Warning und Debug Meldungen sind etabliert. Siehe [Debug Logs erzeugen](debug-logs-erzeugen.md).
- **Diagnose-Download**: Enthält die Rohwerte aller Register, so wie die Lambda sie liefert.
- **Statistik-Schutz**: Die Gesamtzähler bleiben auch verfügbar, wenn die Lambda zeitweise nicht antwortet, damit die Langzeitstatistik keinen Zählerreset sieht.
- **Validierung**: Automatische Validierung von Konfigurationen und Werten.

## 📈 Monitoring & Statistiken

- **Historische Daten**: Alle Sensoren landen in den Home Assistant historischen Daten, es gibt eine Anleitung für die Übernahme historischer Daten, wenn z.B. von einer anderen Lösung zu dieser Integration gewechselt wird.
- **Firmware-Anpassungen**: Automatische Anpassung der Sensoren und der Register-Reihenfolge basierend auf der Firmware-Version (siehe [Firmware-Version ändern](firmware-wechsel.md))

## 🔐 Sicherheit & Zuverlässigkeit

- **Konfigurationsvalidierung**: Verhindert fehlerhafte Konfigurationen
- **Verbindungsüberwachung**: Automatische Überwachung der Modbus-Verbindung

---

**Weitere Informationen zu einzelnen Features finden Sie in der entsprechenden Dokumentation:**
- [Installation](installation.md)
- [Initiale Konfiguration](initiale-konfiguration.md)
- [Lambda Cockpit](lambda-cockpit.md)
- [Heizkurve](heizkurve.md)
- [Raumthermometer](raumthermometer.md)
- [WarmWasser-Steuerung](warmwasser-solltemperatur.md)
- [Energie- und Wärmeverbrauchsberechnung](Energieverbrauchsberechnung.md)

