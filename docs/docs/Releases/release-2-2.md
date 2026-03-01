# Release 2.2

Dokumentation basierend auf dem [GitHub Release Release2.2](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/releases/tag/Release2.2).

---

## Stichpunkte (Übersicht)

- [Flow Line Offset Number Entity (neu)](#flow-line-offset)
- [Heating Curve Validation (Fix)](#heating-curve-validation)
- [Eco Mode in Heizkurve (Issue #51)](#eco-mode-heizkurve)
- [Hot Water Temperature Limits (Issue #50)](#hot-water-limits)

---

## Neue Funktionen

<a id="flow-line-offset"></a>
### Flow Line Offset Number Entity

- **Bidirektionale Modbus-synchronisierte Number-Entity** zur Einstellung des Vorlauf-Offsets (Flow Line Offset) pro Heizkreis.
- Wird **automatisch für jeden Heizkreis** (HC1, HC2, …) angelegt.
- **Bereich:** -10,0°C bis +10,0°C, Schrittweite 0,1°C.
- Liest den aktuellen Wert aus dem Modbus-Register und schreibt Änderungen direkt zurück.
- Erscheint in der Gerätekonfiguration neben den Heizkurven-Stützpunkten.
- **Modbus-Register:** Register 50 (relativ zur Heizkreis-Basisadresse).

---

## Behobene Punkte

<a id="heating-curve-validation"></a>
### Heating Curve Validation

- **Validierungslogik:** Beide Bedingungen werden nun **unabhängig** geprüft (`elif` durch `if` ersetzt).
- **Ergebnis:** Alle Validierungsfehler werden gemeldet, wenn mehrere Heizkurven-Werte falsch konfiguriert sind (z. B. alle drei Temperaturpunkte in falscher Reihenfolge).
- **Issue #48:** Behebung des Falls, in dem alle drei Heizkurven-Punkte **identische Werte** hatten; dies wird nun korrekt als Fehler erkannt.

<a id="eco-mode-heizkurve"></a>
### Eco Mode in Heizkurve (Issue #51)

- **Neue Number-Entity** `eco_temp_reduction` pro Heizkreis.
- **Bereich:** -10,0°C bis 0,0°C (Standard: -1,0°C).
- **Funktion:** Reduziert die berechnete Vorlauftemperatur automatisch, wenn der Heizkreis im **ECO-Modus** ist (`operating_state = 1`).
- Integration in die Heizkurven-Berechnung zusammen mit Vorlauf-Offset und Raumthermostat-Anpassung.

<a id="hot-water-limits"></a>
### Hot Water Temperature Limits (Issue #50)

- **Warmwasser-Temperaturgrenzen** an den Lambda-Standard angepasst: **Minimum 25°C, Maximum 65°C**.

---

## Referenz

- [GitHub Release Release2.2](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/releases/tag/Release2.2)
