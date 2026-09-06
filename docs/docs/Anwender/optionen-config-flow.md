---
title: "Optionen des config_flow"
---

# Optionen des config_flow

*Zuletzt geändert am 06.09.2026*

<div style="display: flex; gap: 20px; align-items: flex-start; margin: 20px 0; flex-wrap: wrap;">
  <div style="flex: 0 0 50%; min-width: 300px;">
    <img src="../../assets/config_flow_options_de.png" alt="Config Flow Optionen" style="width: 100%; height: auto; border-radius: 8px;">
  </div>
  <div style="flex: 1; min-width: 300px;">
    <p>Nach der Initialkonfiguration können Sie erweiterte Einstellungen in den Integration-Optionen anpassen. Diese Optionen ermöglichen es, das Verhalten der Integration zu optimieren und erweiterte Funktionen zu aktivieren.</p>

    <h2>Zugriff auf die Optionen</h2>

    <ol>
      <li><strong>Öffnen Sie Home Assistant:</strong>
        <ul>
          <li>Gehen Sie zu <strong>Einstellungen</strong> → <strong>Geräte & Dienste</strong></li>
          <li>Suchen Sie nach Ihrer Lambda-Integration</li>
          <li>Klicken Sie auf die Integration</li>
        </ul>
      </li>
      <li><strong>Optionen öffnen:</strong>
        <ul>
          <li>Klicken Sie auf <strong>Konfigurieren</strong> (oder das Zahnrad-Symbol)</li>
          <li>Die Options-Seite wird geöffnet</li>
        </ul>
      </li>
    </ol>
  </div>
</div>

## Verfügbare Optionen

### Warmwasser-Temperaturgrenzen

**Beschreibung**: Legen Sie die minimalen und maximalen Temperaturgrenzen für Warmwasser fest.

- **Minimum-Temperatur**: 
  - **Standard**: 25°C
  - **Bereich**: 25°C bis 65°C
  - **Schrittweite**: 1°C
  - **Einheit**: °C

- **Maximum-Temperatur**: 
  - **Standard**: 65°C
  - **Bereich**: 25°C bis 65°C
  - **Schrittweite**: 1°C
  - **Einheit**: °C

**Hinweis**: Diese Grenzen gelten für alle Kessel (Boiler) und beeinflussen die verfügbaren Werte für die Warmwasser-Solltemperatur-Number-Entities.

### Heizkreis-Temperaturgrenzen

**Beschreibung**: Legen Sie die minimalen und maximalen Temperaturgrenzen für Heizkreise fest.

- **Minimum-Temperatur**: 
  - **Standard**: 15°C
  - **Bereich**: 10°C bis 40°C
  - **Schrittweite**: 1°C
  - **Einheit**: °C

- **Maximum-Temperatur**: 
  - **Standard**: 35°C
  - **Bereich**: 10°C bis 40°C
  - **Schrittweite**: 1°C
  - **Einheit**: °C

- **Temperatur-Schrittweite**: 
  - **Standard**: 0.5°C
  - **Bereich**: 0.1°C bis 2.0°C
  - **Schrittweite**: 0.1°C
  - **Einheit**: °C

**Hinweis**: Diese Grenzen gelten für alle Heizkreise und beeinflussen die verfügbaren Werte für Heizkreis-Temperatur-Number-Entities.

### Firmware-Version gehört NICHT zu diesen Optionen

Anders als bis Version 3.4 lässt sich die Firmware-Version **nicht** über diese Options-Seite ändern. Sie wird nur beim Ersteinrichten sowie über **„Neu konfigurieren"** (Menü ⋮ bei der Integration, nicht das Zahnrad-Symbol) gesetzt. Details: [Anpassungen der Sensoren abhängig von der Firmware](anpassungen-sensoren-firmware.md).

### Register-Reihenfolge

**Beschreibung**: Reihenfolge der beiden 16-Bit-Register bei 32-Bit-Werten (Energiezähler, Solar-Ertrag).

- **Optionen**: `high_first` (höherwertiges Register zuerst) / `low_first` (niedrigwertiges Register zuerst)
- **Standard**: richtet sich nach der gewählten Firmware-Version und wird automatisch vorbelegt
- **Wann ändern?**: Wenn 32-Bit-Sensoren (z. B. Energieverbrauch) unrealistische Werte zeigen, probieren Sie die jeweils andere Einstellung.

### Abfrage-Intervall

**Beschreibung**: Wie oft die Integration Daten von der Lambda über Modbus abruft.

- **Standard**: 30 Sekunden
- **Bereich**: 10 bis 300 Sekunden
- **Hinweis**: Lambda erfordert ein Timeout von mindestens 60 Sekunden. Ein Wert von 30 Sekunden ist daher der empfohlene Standard.

### Raumthermostat-Steuerung

**Beschreibung**: Aktivieren Sie die Raumthermostat-Steuerung für präzise Temperaturkontrolle.

- **Standard**: Deaktiviert
- **Optionen**: Aktiviert / Deaktiviert

**Nach Aktivierung:**
- Sie müssen für jeden Heizkreis einen Raumtemperatur-Sensor auswählen
- Die Integration berechnet automatisch Anpassungen der Vorlauftemperatur
- Weitere Informationen: [Raumthermostat](raumthermometer.md)

**Konfiguration:**
1. Aktivieren Sie "Raumthermostat-Steuerung"
2. Klicken Sie auf **Weiter**
3. Wählen Sie für jeden Heizkreis einen Raumtemperatur-Sensor aus
4. Klicken Sie auf **Absenden**

### Kühlmodus-Steuerung

**Beschreibung**: Blendet zusätzlich zur Heizkreis-Thermostat-Entität eine eigene **Kühlkreis**-Climate-Entität pro Heizkreis ein, die den Kühl-Sollwert (`set_cooling_mode_room_temperature`) schreibt.

- **Standard**: Deaktiviert
- **Optionen**: Aktiviert / Deaktiviert
- **Hinweis**: Unabhängig von der Raumthermostat-Steuerung aktivierbar; beide zusammen fragen im selben Schritt nach den Raumtemperatur-Sensoren, weil der Kühlbetrieb denselben Ist-Wert braucht wie die Heizkreis-Regelung.

### PV-Überschuss-Steuerung

**Beschreibung**: Aktivieren Sie die PV-Überschuss-Steuerung für optimale Nutzung von Solarstrom.

- **Standard**: Deaktiviert
- **Optionen**: Aktiviert / Deaktiviert

**Nach Aktivierung:**
- Sie müssen einen PV-Leistungssensor auswählen
- Die Integration schreibt die PV-Leistung regelmäßig an die Lambda (standardmäßig alle 9 Sekunden)
- Weitere Informationen: [PV Überschuss Steuerung](pv_ueberschuss_steuerung.md)

**Konfiguration:**
1. Aktivieren Sie "PV-Überschuss"
2. Klicken Sie auf **Weiter**
3. Wählen Sie einen PV-Leistungssensor aus (z.B. Template-Sensor für PV-Überschuss)
4. Klicken Sie auf **Absenden**

**PV-Überschuss-Modi:**

| Schlüssel | Beschreibung |
|-----------|-------------|
| `pos` (Standard) | Pos. E-Überschuss – nur positive Werte, UINT16 (0–65535) |
| `neg` | Neg. E-Überschuss – positive und negative Werte, INT16 (−32768–32767) |

Der Modus bestimmt, wie der Leistungswert des PV-Sensors an das Lambda-Register 102 (E-Manager Actual Power) übertragen wird.

Nach der Anpassung der Optionen können Sie:

- [Raumthermostat](raumthermometer.md) konfigurieren (falls aktiviert)
- [PV Überschuss Steuerung](pv_ueberschuss_steuerung.md) verwenden (falls aktiviert)
- [Warmwasser Solltemperatur Steuerung](warmwasser-solltemperatur.md) verwenden
- [Energie- und Wärmeverbrauchsberechnung](Energieverbrauchsberechnung.md) einrichten
- [Historische Daten übernehmen](historische-daten.md) bei Wärmepumpenwechsel

