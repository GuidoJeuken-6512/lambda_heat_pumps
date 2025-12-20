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
- Weitere Informationen: Siehe README.md Abschnitt "PV-Überschuss-Steuerung"

**Konfiguration:**
1. Aktivieren Sie "PV-Überschuss"
2. Klicken Sie auf **Weiter**
3. Wählen Sie einen PV-Leistungssensor aus (z.B. Template-Sensor für PV-Überschuss)
4. Klicken Sie auf **Absenden**

**PV-Überschuss-Modi:**
- **Standard**: Automatischer Modus
- **Optionen**: Verschiedene Modi je nach Konfiguration

## Optionen-Workflow

### Schritt 1: Grundoptionen anpassen

1. **Temperaturgrenzen anpassen:**
   - Passen Sie die Warmwasser- und Heizkreis-Temperaturgrenzen an
   - Stellen Sie sicher, dass Minimum < Maximum

2. **Firmware-Version aktualisieren:**
   - Aktualisieren Sie die Firmware-Version, falls sich diese geändert hat

3. **Erweiterte Funktionen aktivieren:**
   - Aktivieren Sie Raumthermostat-Steuerung, falls gewünscht
   - Aktivieren Sie PV-Überschuss-Steuerung, falls gewünscht

### Schritt 2: Erweiterte Konfiguration

Wenn Sie erweiterte Funktionen aktiviert haben:

1. **Raumthermostat konfigurieren:**
   - Wählen Sie für jeden Heizkreis einen Raumtemperatur-Sensor aus
   - Die Integration führt Sie durch den Konfigurationsprozess

2. **PV-Überschuss konfigurieren:**
   - Wählen Sie einen PV-Leistungssensor aus
   - Die Integration führt Sie durch den Konfigurationsprozess

### Schritt 3: Konfiguration speichern

1. **Überprüfen Sie die Einstellungen:**
   - Überprüfen Sie alle angepassten Werte
   - Stellen Sie sicher, dass alle Validierungen bestanden wurden

2. **Konfiguration speichern:**
   - Klicken Sie auf **Absenden** oder **Speichern**
   - Die Integration übernimmt die neuen Einstellungen

3. **Home Assistant neu starten (falls erforderlich):**
   - In einigen Fällen ist ein Neustart erforderlich
   - Folgen Sie den Anweisungen auf dem Bildschirm

## Validierungen

Die Integration validiert automatisch die eingegebenen Werte:

### Temperatur-Validierung

- **Minimum < Maximum**: Die Minimum-Temperatur muss kleiner als die Maximum-Temperatur sein
- **Bereichsprüfung**: Alle Werte müssen innerhalb der erlaubten Bereiche liegen
- **Fehlermeldungen**: Bei Fehlern werden entsprechende Meldungen angezeigt

### Sensor-Validierung

- **Sensor-Existenz**: Überprüft, ob die ausgewählten Sensoren existieren
- **Sensor-Verfügbarkeit**: Überprüft, ob die Sensoren verfügbar sind
- **Fehlermeldungen**: Bei Fehlern werden entsprechende Meldungen angezeigt

## Beispiel-Konfigurationen

### Beispiel 1: Standard-Konfiguration

```yaml
# Warmwasser-Temperaturgrenzen
hot_water_min_temp: 25
hot_water_max_temp: 65

# Heizkreis-Temperaturgrenzen
heating_circuit_min_temp: 10
heating_circuit_max_temp: 40
heating_circuit_temp_step: 0.1

# Firmware-Version
firmware_version: "1.0.0"

# Erweiterte Funktionen
room_thermostat_control: false
pv_surplus: false
```

### Beispiel 2: Mit Raumthermostat

```yaml
# Grundoptionen
hot_water_min_temp: 25
hot_water_max_temp: 65
heating_circuit_min_temp: 10
heating_circuit_max_temp: 40
heating_circuit_temp_step: 0.1
firmware_version: "1.0.0"

# Raumthermostat aktiviert
room_thermostat_control: true
room_temperature_entity_hc1: sensor.wohnzimmer_temperatur
room_temperature_entity_hc2: sensor.schlafzimmer_temperatur

# PV-Überschuss deaktiviert
pv_surplus: false
```

### Beispiel 3: Mit PV-Überschuss

```yaml
# Grundoptionen
hot_water_min_temp: 25
hot_water_max_temp: 65
heating_circuit_min_temp: 10
heating_circuit_max_temp: 40
heating_circuit_temp_step: 0.1
firmware_version: "1.0.0"

# Raumthermostat deaktiviert
room_thermostat_control: false

# PV-Überschuss aktiviert
pv_surplus: true
pv_power_sensor_entity: sensor.pv_ueberschuss
pv_surplus_mode: "auto"
```

## Häufige Probleme

### "Minimum-Temperatur höher als Maximum-Temperatur"
- **Ursache**: Minimum-Temperatur ist größer oder gleich Maximum-Temperatur
- **Lösung**: Stellen Sie sicher, dass Minimum < Maximum

### "Sensor nicht gefunden"
- **Ursache**: Der ausgewählte Sensor existiert nicht oder ist nicht verfügbar
- **Lösung**: 
  - Überprüfen Sie, ob der Sensor in Home Assistant existiert
  - Wählen Sie einen anderen Sensor aus

### "Optionen werden nicht gespeichert"
- **Ursache**: Validierungsfehler oder Home Assistant-Neustart erforderlich
- **Lösung**: 
  - Überprüfen Sie die Validierungsfehler
  - Starten Sie Home Assistant neu, falls erforderlich

### "Firmware-Version ändert nichts"
- **Ursache**: Home Assistant wurde nicht neu gestartet
- **Lösung**: Starten Sie Home Assistant vollständig neu, damit die neuen Sensoren erkannt werden

## Nächste Schritte

Nach der Anpassung der Optionen können Sie:

- [Raumthermostat](raumthermostat.md) konfigurieren (falls aktiviert)
- [Warmwasser Solltemperatur Steuerung](warmwasser-solltemperatur.md) verwenden
- [Stromverbrauchsberechnung](stromverbrauchsberechnung.md) einrichten
- [Historische Daten übernehmen](historische-daten.md) bei Wärmepumpenwechsel

