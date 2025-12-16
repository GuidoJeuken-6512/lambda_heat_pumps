# Änderungsprotokoll

#### New Features seit dem letzten Release
- **Geräte-Hierarchie**: Aufteilung in Haupt- und Sub-Geräte für bessere Organisation und klarere Entity-Struktur
- **Mehrsprachige Unterstützung**: Umfassende Übersetzungen in Deutsch und Englisch für alle Entity-Namen
- **Heizkurven-Berechnung**: Intelligente Heizkurven-Berechnung mit drei Stützpunkten (Kalt, Mittel, Warm) und automatischer Vorlauftemperatur-Berechnung
- **Kompressor-Start Cycling Sensor**: Neuer Cycling-Sensor zur Verfolgung von Kompressor-Start-Ereignissen mit total, daily, 2h, 4h und monthly Varianten
- **Vorlauf-Offset Number Entity**: Bidirektionale Modbus-synchronisierte Number-Entity zur einfachen Anpassung der Vorlauf-Offset-Temperatur (-10°C bis +10°C)

### [2.0.1] - 2025-01-XX

#### Neue Funktionen
- **Vorlauf-Offset Number Entity**: Hinzugefügte bidirektionale Modbus-synchronisierte Number-Entity zur Anpassung der Vorlauf-Offset-Temperatur
  - Wird automatisch für jeden Heizkreis (HC1, HC2, etc.) erstellt
  - Bereich: -10.0°C bis +10.0°C mit 0.1°C Schrittweite
  - Liest aktuellen Wert aus Modbus-Register und schreibt Änderungen direkt zurück
  - Erscheint in der Geräte-Konfiguration neben den Heizkurven-Stützpunkten
  - Modbus-Register: Register 50 (relativ zur Base-Adresse des Heizkreises)

#### Behoben
- **Heizkurven-Validierung**: Validierungslogik korrigiert, um beide Bedingungen unabhängig zu prüfen
  - `elif` zu `if` geändert, um sicherzustellen, dass beide Validierungsprüfungen durchgeführt werden
  - Meldet jetzt alle Validierungsprobleme, wenn mehrere Heizkurven-Werte falsch konfiguriert sind
  - Zuvor wurde nur das erste Problem gemeldet, wenn alle drei Temperaturpunkte in falscher Reihenfolge waren
- **Warmwasser-Temperaturgrenzen**: Minimum/Maximum-Werte für Warmwasser auf Lambda-Standard (25/65°C) angepasst


#### Geändert
- **Git-Konfiguration**: `automations.yaml` aus gitignore entfernt, um zu verhindern, dass sie in git getrackt wird

### [2.0.0] - 2025-01-XX

#### Neue Funktionen
- **Geräte-Hierarchie**: Implementierte Aufteilung in Haupt- und Sub-Geräte für bessere Organisation und klarere Entity-Struktur
- **Mehrsprachige Unterstützung**: Hinzugefügte umfassende Übersetzungen in Deutsch und Englisch für alle Entity-Namen, gewährleistet ordnungsgemäße Lokalisierungsunterstützung
- **Heizkurven-Berechnung**: Implementierte intelligente Heizkurven-Berechnung mit drei Stützpunkten (Kalt, Mittel, Warm) und automatischer Vorlauftemperatur-Berechnung basierend auf Außentemperatur
  - **Kalter Punkt**: Definiert die Heizkurve bei niedrigen Außentemperaturen
  - **Mittlerer Punkt**: Definiert die Heizkurve bei mittleren Außentemperaturen
  - **Warmer Punkt**: Definiert die Heizkurve bei hohen Außentemperaturen
  - **Neuer Sensor**: `heating_curve_flow_line_temperature_calc` berechnet automatisch die optimale Vorlauftemperatur basierend auf aktueller Außentemperatur und den konfigurierten Stützpunkten
- **Kompressor-Start Cycling Sensor**: Hinzugefügter neuer Cycling-Sensor zur Verfolgung von Kompressor-Start-Ereignissen
  - **Total-Sensor**: `compressor_start_cycling_total` - Verfolgt Gesamtanzahl der Kompressor-Starts seit Installation
  - **Daily-Sensor**: `compressor_start_cycling_daily` - Verfolgt tägliche Kompressor-Starts (Reset um Mitternacht)
  - **2H-Sensor**: `compressor_start_cycling_2h` - Verfolgt 2-Stunden Kompressor-Starts (Reset alle 2 Stunden)
  - **4H-Sensor**: `compressor_start_cycling_4h` - Verfolgt 4-Stunden Kompressor-Starts (Reset alle 4 Stunden)
  - **Monthly-Sensor**: `compressor_start_cycling_monthly` - Verfolgt monatliche Kompressor-Starts (Reset am 1. des Monats)
  - **Flankenerkennung**: Verwendet HP_STATE Register (1002) statt HP_OPERATING_STATE, erkennt "START COMPRESSOR" Status (Wert 5)

#### Verbesserungen
- Verbesserte Entity-Namensgebung mit ordnungsgemäßen Geräte- und Sub-Geräte-Präfixen
- Verbesserte Übersetzungs-Ladung und -Anwendung für alle Entity-Typen
- Bessere Integration mit Home Assistants Übersetzungssystem
- **Write-Interval-Optimierung**: Reduziertes Write-Interval von 41 Sekunden auf 9 Sekunden für schnellere Reaktionszeiten
- **Externe Verbrauchssensor-Validierung**: Verbesserte Validierung externer Verbrauchssensoren mit Entity Registry Fallback-Prüfung, ermöglicht Sensoren auch dann zu akzeptieren, wenn sie beim Start noch nicht im State verfügbar sind. Runtime Retry-Mechanismus behandelt temporäre Nicht-Verfügbarkeit elegant.

### [1.4.3] - 2025-11-04
#### Fehlerbehebungen
- **ISSUE 39**  Modebus batch Reads erkennen Fehler falsch: Schnelleres Umsschalten zu individual reads, damit korrekte Sensoren wieder zur Verfügung stehen
- **ISSUE 22** Zusätzliches logging eingefügt, um Fehler zu identifizieren
- **Einheit des Sensors volume_flow_heat_sink korregiert** zu l/h

### [1.4.2] - 2025-10-24

#### Fehlerbehebungen
- **Test-Reparaturen**: Behoben fehlgeschlagene Tests durch Ersetzen von Mock-Objekten mit ordnungsgemäßen Test-Implementierungen
- **Verbesserte Test-Zuverlässigkeit**: Reduzierte false-positive Test-Fehler und verbesserte Test-Stabilität
- **Integration-Reload-Fehler**: Behoben Fehler beim Neuladen der Integration
- **Konfigurations-Fix**: Behoben `default_config` in `load_lambda_config()` um alle erforderlichen Keys einzubinden (`energy_consumption_sensors`, `energy_consumption_offsets`, `modbus`)

#### Geändert
- **Register-Order-Werte**: Konfigurationswerte von `"big"`/`"little"` auf `"high_first"`/`"low_first"` geändert für bessere Klarheit
  - Alte Werte (`big`/`little`) werden weiterhin mit automatischer Konvertierung unterstützt
  - Neuer Standard ist `"high_first"` (ersetzt `"big"`)
  - Verbesserte Dokumentation und Kommentare zur Klärung von Register-Reihenfolge vs. Byte-Endianness

#### Verbesserungen
- **Test-Optimierung**: 57 Tests erfolgreich repariert und optimiert
- **Gitignore-Korrektur**: Korrigiert .gitignore für ordnungsgemäße Einbindung aller docs-Unterverzeichnisse
- **Service-Dokumentation**: Erstellt umfassende Dokumentation für zukünftige Service-Optimierungen
- **Service-Scheduler-Optimierung**: Implementierte intelligente Service-Scheduler, die nur aktiviert werden, wenn PV-Surplus oder Raumthermostat-Steuerungsoptionen aktiviert sind, wodurch der Ressourcenverbrauch erheblich reduziert wird, wenn Services nicht benötigt werden

---
