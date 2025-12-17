---
title: "Initiale Konfiguration"
---

# Initiale Konfiguration

Nach der Installation der Lambda Heat Pumps Integration über HACS müssen Sie die Integration in Home Assistant einrichten. Dieser Abschnitt führt Sie durch den Konfigurationsprozess.

## Konfiguration über die Benutzeroberfläche

### Schritt 1: Integration hinzufügen

1. **Öffnen Sie Home Assistant:**
   - Gehen Sie zu **Einstellungen** → **Geräte & Dienste**
   - Klicken Sie auf **Integration hinzufügen** (unten rechts)

2. **Integration suchen:**
   - Geben Sie "Lambda Heat Pumps" in das Suchfeld ein
   - Wählen Sie die Integration aus der Liste aus

### Schritt 2: Grundkonfiguration

Bei der Einrichtung müssen Sie folgende **Pflichtfelder** angeben:

#### Name
- **Beschreibung**: Ein Name für Ihre Lambda-Wärmepumpe (z. B. "EU08L", "Meine Wärmepumpe")
- **Beispiel**: `EU08L`
- **Hinweis**: Dieser Name wird als Präfix für alle erstellten Entitäten verwendet

#### Host
- **Beschreibung**: IP-Adresse oder Hostname Ihres Lambda-Controllers
- **Beispiel**: `192.168.1.100` oder `lambda-wp.local`
- **Hinweis**: Stellen Sie sicher, dass Home Assistant Zugriff auf diese IP-Adresse hat

#### Port
- **Beschreibung**: Modbus-TCP-Port
- **Standardwert**: `502`
- **Hinweis**: In den meisten Fällen ist Port 502 korrekt

#### Slave ID
- **Beschreibung**: Modbus-Slave-ID
- **Standardwert**: `1`
- **Hinweis**: Die Standard-Slave-ID ist 1, ändern Sie diesen Wert nur, wenn Ihre Lambda eine andere Slave-ID verwendet

#### Firmware-Version
- **Beschreibung**: Firmware-Version Ihres Lambda-Controllers
- **Wichtig**: Die Firmware-Version bestimmt, welche Sensoren verfügbar sind
- **So finden Sie die Firmware-Version:**
  1. Klicken Sie auf der Lambda-Bedienoberfläche auf die Wärmepumpe
  2. Klicken Sie auf die "i" Taste auf der linken Seite
  3. Klicken Sie auf die Taste auf der rechten Seite, die wie ein Computerchip aussieht (letzte Taste)
  4. Die Firmware-Version wird dort angezeigt

### Schritt 3: Automatische Konfiguration

Nach der Eingabe der Grunddaten führt die Integration eine **automatische Modulerkennung** durch:

- **Auto-Detection**: Erkennt automatisch verfügbare Module (Wärmepumpen, Kessel, Puffer, Solar, Heizkreise)
- **Dynamische Entity-Erstellung**: Erstellt Sensoren und Entities basierend auf erkanntem Hardware
- **Intelligente Standardeinstellungen**: Wendet optimale Einstellungen für Ihre spezifische Lambda-Konfiguration an
- **Konfigurationsvalidierung**: Verhindert doppelte Konfigurationen und validiert bestehende Verbindungen

**Hinweis**: Die automatische Erkennung kann einige Sekunden dauern. Bitte haben Sie Geduld.

### Schritt 4: Konfiguration abschließen

Nach erfolgreicher Erkennung:

1. **Überprüfen Sie die erkannten Module:**
   - Die Integration zeigt Ihnen die erkannten Module an
   - Überprüfen Sie, ob alle Module korrekt erkannt wurden

2. **Konfiguration speichern:**
   - Klicken Sie auf **Absenden** oder **Speichern**
   - Die Integration wird nun eingerichtet

3. **Home Assistant neu starten (falls erforderlich):**
   - In einigen Fällen ist ein Neustart erforderlich
   - Folgen Sie den Anweisungen auf dem Bildschirm

## Nach der Initialkonfiguration

Nach erfolgreicher Konfiguration:

1. **Überprüfen Sie die erstellten Entitäten:**
   - Gehen Sie zu **Einstellungen** → **Geräte & Dienste**
   - Suchen Sie nach Ihrer Lambda-Integration
   - Klicken Sie auf die Integration, um alle erstellten Entitäten zu sehen

2. **Konfigurieren Sie erweiterte Optionen:**
   - Klicken Sie auf **Konfigurieren** bei Ihrer Lambda-Integration
   - Hier können Sie weitere Einstellungen anpassen (siehe [Optionen des config_flow](optionen-config-flow.md))

3. **Erstellen Sie Dashboards:**
   - Verwenden Sie die erstellten Sensoren in Ihren Home Assistant Dashboards
   - Alle Sensoren sind sofort in Automatisierungen und Szenen verfügbar

## Häufige Probleme

### "Verbindung fehlgeschlagen"
- **Ursache**: Home Assistant kann nicht auf die Lambda-IP-Adresse zugreifen
- **Lösung**: 
  - Überprüfen Sie die IP-Adresse
  - Stellen Sie sicher, dass Home Assistant und die Lambda im gleichen Netzwerk sind
  - Überprüfen Sie die Firewall-Einstellungen

### "Falsche Sensoren erkannt"
- **Ursache**: Falsche Firmware-Version ausgewählt
- **Lösung**: 
  - Überprüfen Sie die Firmware-Version auf der Lambda-Bedienoberfläche
  - Entfernen Sie die Integration und fügen Sie sie erneut mit der korrekten Firmware-Version hinzu

### "Doppelte Konfiguration"
- **Ursache**: Eine Konfiguration mit derselben IP/Port/Slave-ID existiert bereits
- **Lösung**: 
  - Entfernen Sie die bestehende Konfiguration oder verwenden Sie eine andere IP-Adresse/Port/Slave-ID

## Nächste Schritte

Nach der erfolgreichen Initialkonfiguration können Sie:

- [Anpassungen der Sensoren abhängig von der Firmware](anpassungen-sensoren-firmware.md) vornehmen
- [Warmwasser Solltemperatur Steuerung](warmwasser-solltemperatur.md) einrichten
- [Raumthermostat](raumthermostat.md) konfigurieren
- [Stromverbrauchsberechnung](stromverbrauchsberechnung.md) einrichten
- [Historische Daten übernehmen](historische-daten.md) bei Wärmepumpenwechsel

