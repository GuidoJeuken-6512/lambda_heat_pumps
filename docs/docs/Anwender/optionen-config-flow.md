---
title: "Optionen des config_flow"
---

# Optionen des config_flow

Nach der Initialkonfiguration können Sie erweiterte Einstellungen in den Integration-Optionen anpassen. Diese Optionen ermöglichen es, das Verhalten der Integration zu optimieren und erweiterte Funktionen zu aktivieren.

## Zugriff auf die Optionen

1. **Öffnen Sie Home Assistant:**
   - Gehen Sie zu **Einstellungen** → **Geräte & Dienste**
   - Suchen Sie nach Ihrer Lambda-Integration
   - Klicken Sie auf die Integration

2. **Optionen öffnen:**
   - Klicken Sie auf **Konfigurieren** (oder das Zahnrad-Symbol)
   - Die Options-Seite wird geöffnet

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
  - **Standard**: 10°C
  - **Bereich**: 10°C bis 40°C
  - **Schrittweite**: 1°C
  - **Einheit**: °C

- **Maximum-Temperatur**: 
  - **Standard**: 40°C
  - **Bereich**: 10°C bis 40°C
  - **Schrittweite**: 1°C
  - **Einheit**: °C

- **Temperatur-Schrittweite**: 
  - **Standard**: 0.1°C
  - **Bereich**: 0.1°C bis 2.0°C
  - **Schrittweite**: 0.1°C
  - **Einheit**: °C

**Hinweis**: Diese Grenzen gelten für alle Heizkreise und beeinflussen die verfügbaren Werte für Heizkreis-Temperatur-Number-Entities.

### Firmware-Version

**Beschreibung**: Aktualisieren Sie die Firmware-Version Ihrer Lambda-Wärmepumpe.

- **Standard**: Die bei der Initialkonfiguration ausgewählte Firmware-Version
- **Wichtig**: Die Firmware-Version bestimmt, welche Sensoren verfügbar sind

**So finden Sie die Firmware-Version:**
1. Klicken Sie auf der Lambda-Bedienoberfläche auf die Wärmepumpe
2. Klicken Sie auf die "i" Taste auf der linken Seite
3. Klicken Sie auf die Taste auf der rechten Seite, die wie ein Computerchip aussieht (letzte Taste)
4. Die Firmware-Version wird dort angezeigt

**Hinweis**: Nach Änderung der Firmware-Version müssen Sie Home Assistant neu starten, damit die neuen Sensoren erkannt werden.

### Raumthermostat-Steuerung

**Beschreibung**: Aktivieren Sie die Raumthermostat-Steuerung für präzise Temperaturkontrolle.

- **Standard**: Deaktiviert
- **Optionen**: Aktiviert / Deaktiviert

**Nach Aktivierung:**
- Sie müssen für jeden Heizkreis einen Raumtemperatur-Sensor auswählen
- Die Integration berechnet automatisch Anpassungen der Vorlauftemperatur
- Weitere Informationen: [Raumthermostat](raumthermostat.md)

**Konfiguration:**
1. Aktivieren Sie "Raumthermostat-Steuerung"
2. Klicken Sie auf **Weiter**
3. Wählen Sie für jeden Heizkreis einen Raumtemperatur-Sensor aus
4. Klicken Sie auf **Absenden**

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
- **Optionen**: Verschiedene Modi je nach Konfiguration


Nach der Anpassung der Optionen können Sie:

- [Raumthermostat](raumthermostat.md) konfigurieren (falls aktiviert)
- [PV Überschuss Steuerung](pv_ueberschuss_steuerung.md) verwenden (falls aktiviert)
- [Warmwasser Solltemperatur Steuerung](warmwasser-solltemperatur.md) verwenden
- [Stromverbrauchsberechnung](stromverbrauchsberechnung.md) einrichten
- [Historische Daten übernehmen](historische-daten.md) bei Wärmepumpenwechsel

