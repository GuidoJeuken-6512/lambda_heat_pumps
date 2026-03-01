# Release 2.0.0

Dokumentation basierend auf dem [GitHub Release V2.0.0](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/releases/tag/V2.0.0).

---

## Stichpunkte (Übersicht)

- [Device Hierarchy](#device-hierarchy)
- [Mehrsprachige Unterstützung](#mehrsprachige-unterstuetzung)
- [Heizkurven-Berechnung](#heizkurven-berechnung)
- [Compressor Start Cycling Sensor](#compressor-start-cycling-sensor)
- [Verbesserungen & Bugfixes](#verbesserungen-und-bugfixes)

---

## Neue Funktionen

<a id="device-hierarchy"></a>
### Device Hierarchy

- **Trennung in Hauptgeräte und Sub-Geräte** für bessere Struktur und klarere Entity-Organisation in Home Assistant.

<a id="mehrsprachige-unterstuetzung"></a>
### Mehrsprachige Unterstützung

- **Übersetzungen** in Deutsch und Englisch für alle Entity-Namen.

<a id="heizkurven-berechnung"></a>
### Heizkurven-Berechnung

- **Heizkurven-Berechnung** mit drei Stützpunkten (kalt, mittel, warm) und automatischer Vorlauftemperatur-Berechnung.
- Dokumentation: `HEATING_CURVE_CALCULATION.md`.

<a id="compressor-start-cycling-sensor"></a>
### Compressor Start Cycling Sensor

- **Neuer Cycling-Sensor** für Kompressor-Starts mit Varianten: total, daily, 2h, 4h und monthly.

---

## Verbesserungen und Bugfixes

<a id="verbesserungen-und-bugfixes"></a>

- **External Energy Sensor:** Erweiterte Validierung mit Entity-Registry-Fallback.
- **Write Interval:** Schreibintervall von 41 Sekunden auf 9 Sekunden reduziert für schnellere Reaktion.
- **Performance:** Verbesserte Startzeit und Update-Zyklen.
- **State Normalization:** Getrennte Normalisierungsmethoden für Betriebszustände und allgemeine Zustände.
- **Tests:** Tests für Offset-Verarbeitung (Cycling und Energieverbrauch).
- **Bugfixes:** VERSION-Import in Tests, Entity-ID-Formatierung, verbessertes Error-Handling bei Sensor-Validierung.
- **Dokumentation:** Cycling-Sensoren-Doku aktualisiert, diverse Doku-Dateien überarbeitet.

---

## Technische Änderungen (Auszug)

- **coordinator.py:** Sensor-Validierung und State-Normalisierung.
- **sensor.py:** Neue Cycling-Sensoren, Offset-Verarbeitung.
- **number.py:** Number-Platform-Unterstützung.
- **utils.py:** Energie-Sensor-Validierung.

---

## Deployment

- **Breaking Changes:** Keine.
- **Migration:** Automatische Migration von älteren Versionen.
- **Konfiguration:** Optionale neue Optionen für Heizkurve und Offsets.

---

## Referenz

- [GitHub Release V2.0.0](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/releases/tag/V2.0.0)
