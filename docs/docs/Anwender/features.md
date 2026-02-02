---
title: "Features"
---

# Features der Lambda Heat Pumps Integration

Die Lambda Heat Pumps Integration bietet umfassende Funktionen zur Steuerung und Überwachung Ihrer Lambda-Wärmepumpe über Home Assistant. Hier finden Sie eine Übersicht aller verfügbaren Features.

## 🔌 Modbus/TCP Kommunikation

- **Vollständige Modbus/TCP-Unterstützung**: Komplette Kommunikation mit Lambda-Wärmepumpen über das Modbus TCP-Protokoll. Alle Sensoren, die die Lambda über die Modbus Schnittstelle zur Verfügung stellt, sind in der Integration vorhanden.
- **Asynchrone Modbus-Operationen**: Nicht-blockierende Modbus-Kommunikation für optimale Performance
- **Automatische Verbindungsverwaltung**: Intelligente Verbindungsverwaltung mit automatischer Wiederverbindung bei Verbindungsabbrüchen
- **Register-Reihenfolge-Konfiguration**: Konfigurierbare Register-Reihenfolge für 32-Bit-Werte aus mehreren 16-Bit-Registern

## 🔍 Automatische Modulerkennung

- **Hardware-Erkennung**: Automatische Erkennung verfügbarer Module (Wärmepumpen, Warmwasser Modul, Puffer, Solar, Heizkreise)
- **Dynamische Entity-Erstellung**: Automatische Erstellung aller Sensoren und Entities basierend auf erkanntem Hardware
- **Konfigurationsvalidierung**: Verhindert doppelte Konfigurationen und validiert bestehende Verbindungen

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
- **Total**: Gesamtzähler seit Installation
- **Täglich**: Tageszähler (Reset um Mitternacht)
- **Gestern**: Zählerstand vom Vortag
- **2 Stunden**: 2-Stunden-Zähler (Reset alle 2 Stunden)
- **4 Stunden**: 4-Stunden-Zähler (Reset alle 4 Stunden)
- **Monatlich**: Monatszähler (Reset am 1. des Monats)

### Funktionen
- **Automatischer Reset**: Tägliche Sensoren werden automatisch um Mitternacht zurückgesetzt
- **Offset-Konfiguration**: Anpassbare Zählerstände für Wärmepumpenwechsel oder Zählerrücksetzungen 

> ⚠️ **Warnung:** Die Offset-Funktion ist aktuell fehlerhaft implementiert und sollte **nicht genutzt werden**! Bitte warten Sie auf ein zukünftiges Release, bevor Sie Offsets verwenden.


## ⚡ Energieverbrauchssensoren

Detaillierte Energieverfolgung nach Betriebsart:

### Betriebsmodi
- **Heizen**: Energieverbrauch für Heizbetrieb
- **Warmwasser**: Energieverbrauch für Warmwasserbereitung
- **Kühlen**: Energieverbrauch für Kühlbetrieb
- **Abtauen**: Energieverbrauch für Abtauzyklen

### Zeiträume
- **Täglich**: Täglicher Energieverbrauch
- **Monatlich**: Monatlicher Energieverbrauch
- **Jährlich**: Jährlicher Energieverbrauch

### Funktionen
- **Konfigurierbare Quellsensoren**: Beliebige Energiezähler als Datenquelle. Wenn ein externer Stromverbrauchssensor (z.B. Shelly 3EM) vor der Wärmepumpe verbaut wurde, so kann dieser für die Berechnung des Stromverbrauchs benutzt werden. Externe Stromverbrauchssensor sind meist genauer als der interne Sensor der Lambda.
Weitere Details und eine vollständige Auflistung aller Energieverbrauchssensoren finden Sie hier: [Energie- und Wärmeverbrauchsberechnung](Energieverbrauchsberechnung.md)


## 🌡️ Heizkurven-Konfiguration

Heizkurven-Berechnung und -Steuerung:

Die Funktion der Heizkurven-Berechnung ist hier näher erklärt: [Heizkurve](heizkurve.md)

## 🏠 Raumthermostat-Steuerung

Es kann ein beliebiges Thermometer aus Home Assistant zur Steuerung pro Heizkreis eingebudnen werden. Die Lambda erhöht / verringert dann die Vorlauftemperatur je nachdem, ob die Temperatur über oder unter dem Soll-Temperaturwert ist.

Die genaue Funktion und Einrichtung eines Raumthermometers zur Steuerung der Lambda ist hier erklärt: [Raumthermometer](raumthermometer.md)

## 🌞 PV-Überschuss-Steuerung

Optimale Nutzung von Solarstrom:

Ein beliebiger Sensor, der den PV-Überschuss eurer PV-Anlage darstellt, kann hier eingebunden werden. Die Integration übermittelt dann den Überschuss an die Lambda, die wiederum ihre Steuerung danach ausrichtet.

## 💧 Warmwasser-Steuerung
Über die Integration kann die Solltemperatur der WarmWasser Bereitung einfach konfiguriert werden.
- **Temperaturbereich**: Konfigurierbarer Bereich (Standard: 25-65°C)


## 🎛️ Erweiterte Konfiguration

### YAML-basierte Konfiguration
- **`lambda_wp_config.yaml`**: Erweiterte Konfigurationsmöglichkeiten
- **Register-Deaktivierung**: Deaktivierung einzelner Register bei Firmware-Inkompatibilitäten
- **Sensor-Namensüberschreibungen**: Anpassung von Sensor-Namen
- **Cycling-Offsets**: Anpassung von Zählerständen
- **Energieverbrauchssensoren**: Konfiguration externer Energiezähler
- **Register-Reihenfolge**: Konfiguration für 32-Bit-Register

Die optionene Konfiguration über die Lambda_wp_config.yaml ist hier erklärt [Optionale Konfiguration](lambda-wp-config.md)

### Integration-Optionen
Nach der Ersteinrichtung können Sie zusätzliche Einstellungen anpassen:
- Warmwassertemperaturbereich (min/max)
- Heizkreistemperaturbereich (min/max)
- Temperaturstufengröße
- Raumthermostatsteuerung
- PV-Überschuss-Steuerung

## 🔧 Modbus-Aktionen

Direkter Zugriff auf Modbus-Register:
Über die EntwicklerTools in Home Assistant können Register der Lambda Wärmepumpe ausgelesen und auch geschreiben werden.
Damit kann jedes Register in einer Automatisierung in Home Assistant verwendet / gesteuert werden.

### Verfügbare Aktionen
- **`read_modbus_register`**: Lesen von Werten aus Modbus-Registern
- **`write_modbus_register`**: Schreiben von Werten in Modbus-Register


## 🌍 Mehrsprachige Unterstützung

- **Deutsch und Englisch**: Vollständige Übersetzungen für alle Entity-Namen
- **Automatische Lokalisierung**: Integration in Home Assistants Übersetzungssystem
- **Konsistente Namensgebung**: Verbesserte Entity-Namensgebung mit Geräte- und Sub-Geräte-Präfixen

## 📱 Geräte-Hierarchie

- **Haupt- und Sub-Geräte**: Klare Strukturierung für bessere Organisation
- **Klarere Entity-Struktur**: Verbesserte Übersichtlichkeit in Home Assistant


## 🛡️ Fehlerbehandlung

- **Detailliertes Logging**: Umfassende Protokollierung für Fehleranalyse, Info / Warning und Debug Meldungen sind etabliert.
- **Validierung**: Automatische Validierung von Konfigurationen und Werten.

## 📈 Monitoring & Statistiken

- **Historische Daten**: Alle Sensoren landen in den Home Assistant historischen Daten, es gibt eine Anleitung für die Übernahme historischer Daten, wenn z.B. von einer anderen Lösung zu dieser Integration gewechselt wird.
- **Firmware-Anpassungen**: Automatische Anpassung der Sensoren basierend auf Firmware-Version

## 🔐 Sicherheit & Zuverlässigkeit

- **Konfigurationsvalidierung**: Verhindert fehlerhafte Konfigurationen
- **Verbindungsüberwachung**: Automatische Überwachung der Modbus-Verbindung

---

**Weitere Informationen zu einzelnen Features finden Sie in der entsprechenden Dokumentation:**
- [Installation](installation.md)
- [Initiale Konfiguration](initiale-konfiguration.md)
- [Heizkurve](heizkurve.md)
- [Raumthermometer](raumthermometer.md)
- [WarmWasser-Steuerung](warmwasser-solltemperatur.md)
- [Stromverbrauchsberechnung](stromverbrauchsberechnung.md)

