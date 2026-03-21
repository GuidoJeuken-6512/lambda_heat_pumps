---
title: "Release 2.4.0"
---

# Release 2.4.0

*Zuletzt geändert am 21.03.2026*

> **Aktueller Release** · Branch `V2.4.0`

---

## Zusammenfassung

Release 2.4.0 behebt einen kritischen Bug in der Offset-Logik für Cycling-Sensoren, der dazu führte, dass konfigurierte Offsets aus der `lambda_wp_config.yaml` bei jedem Zyklus-Ereignis erneut addiert wurden statt einmalig beim Start. Zusätzlich wurden die Dokumentation, das Konfigurations-Template und die Test-Suite vollständig aktualisiert.

---

## Bugfixes

### Kritisch: Cycling-Offset wurde bei jedem Zyklus-Ereignis erneut addiert

**Betroffen:** `custom_components/lambda_heat_pumps/utils.py` · `increment_cycling_counter()`

**Symptom:** Konfigurierte `cycling_offsets` aus der `lambda_wp_config.yaml` wurden nicht einmalig angewendet, sondern bei jedem erkannten Betriebsmodus-Wechsel (z. B. Wärmepumpe wechselt in Heizbetrieb) erneut auf den Gesamtzähler addiert. Bei einem konfigurierten Offset von 1500 und 10 Zyklen ergab sich:

```
Erwartet:  100 (Basiswert) + 1500 (Offset) + 10 (Zyklen) =  1610
Tatsächlich: 100 + 1500 × 11                             = 16610
```

**Ursache:** `increment_cycling_counter()` las den vollen YAML-Offset-Wert und addierte ihn bei jedem Aufruf, ohne zu prüfen, ob er bereits im Sensorwert enthalten war. Parallel dazu wendete `_apply_cycling_offset()` in `sensor.py` den Offset korrekt einmalig beim HA-Start an — die beiden Mechanismen konkurrierten.

**Fix:** Der Offset-Block wurde vollständig aus `increment_cycling_counter()` entfernt. Der Parameter `cycling_offsets` wurde aus der Funktionssignatur gestrichen. Die alleinige Verantwortung für Offsets liegt jetzt bei `_apply_cycling_offset()` in `sensor.py`, die korrekt differenzbasiert arbeitet (`_applied_offset`-Tracking).

```python
# Vorher (fehlerhaft):
final_value = int(new_value + offset)   # offset = voller YAML-Wert, jedes Mal!

# Nachher (korrekt):
final_value = new_value                 # nur +1, kein Offset hier
```

**Wie `_apply_cycling_offset()` korrekt funktioniert (unverändert):**

```
HA-Start:
  Gespeicherter Wert:      100
  _applied_offset:           0  (aus Attribut, letzte Session)
  YAML-Offset:            1500
  Differenz:              1500  → wird addiert
  Ergebnis:               1600  ✓
  _applied_offset = 1500  (für nächsten Neustart gespeichert)

Nächster HA-Start:
  Gespeicherter Wert:     1600
  _applied_offset:        1500  (wiederhergestellt)
  YAML-Offset:            1500
  Differenz:                 0  → nichts addiert  ✓

Zyklus-Ereignis (nach Fix):
  increment_cycling_counter() addiert nur +1
  Ergebnis: 1600 + 1 = 1601  ✓
```

---

## Neue Funktionen

### Negative Offsets werden explizit unterstützt und dokumentiert

Sowohl `cycling_offsets` als auch `energy_consumption_offsets` akzeptieren negative Werte. Ein negativer Offset subtrahiert den angegebenen Betrag vom Gesamtzähler — nützlich, um einen zu hohen Ausgangswert zu korrigieren.

```yaml
cycling_offsets:
  hp1:
    heating_cycling_total: -200   # Subtrahiert 200 von der Gesamtzahl
```

Die Validierung beim Laden prüft nur, ob der Wert numerisch ist — kein `>= 0`-Check.

### Thermische Energie-Offsets dokumentiert

`energy_consumption_offsets` unterstützt neben elektrischen Offsets (`{mode}_energy_total`) auch thermische Offsets (`{mode}_thermal_energy_total`). Dies war bisher undokumentiert:

```yaml
energy_consumption_offsets:
  hp1:
    heating_energy_total: 5000.0             # elektrisch
    heating_thermal_energy_total: 6500.0     # thermisch (optional)
    hot_water_thermal_energy_total: 2600.0   # thermisch (optional)
```

---

## Konfigurationstemplate (`const_base.py`)

Das `LAMBDA_WP_CONFIG_TEMPLATE` wurde erweitert:

- `compressor_start_cycling_total` wurde zum Cycling-Offset-Beispiel hinzugefügt (fehlte bisher trotz Unterstützung)
- Thermische Energie-Offsets (`{mode}_thermal_energy_total`) wurden als kommentierte Beispiele ergänzt
- Hinweis auf negative Offsets wurde eingefügt
- Kommentare auf Englisch vereinheitlicht

---

## Dokumentation

### Benutzer-Dokumentation

| Datei | Änderung |
|---|---|
| `Anwender/lambda-wp-config.md` | Warnbanner „fehlerhaft" entfernt; negative Offsets dokumentiert; thermische Offsets im Beispiel ergänzt |
| `Anwender/historische-daten.md` | Warnbanner „fehlerhaft" entfernt; Funktionsweise-Beschreibung korrigiert (Punkt 2 beschrieb fälschlicherweise das buggy Verhalten); thermische Offsets ergänzt |

> Die Hinweise `⚠️ die Funktion der Offsets ist fehlerhaft, bitte im Moment nicht einsetzen!` wurden entfernt. Cycling-Offsets können ab Version 2.4.0 ohne Einschränkung eingesetzt werden.

### Entwickler-Dokumentation

| Datei | Änderung |
|---|---|
| `Entwickler/cycling-sensoren.md` | Flankenerkennung-Codebeispiel aktualisiert (kein `cycling_offsets`-Parameter mehr); Increment-Logik-Beispiel auf korrekten Stand gebracht; Abschnitt 8 (Cycling-Offsets) vollständig überarbeitet; Log-Meldung korrigiert |
| `Entwickler/modbus-wp-config.md` | `cycling_offsets`-Abschnitt: Codebeispiel zeigt jetzt `_apply_cycling_offset()` statt altem Bugcode; thermische Offsets ergänzt; negative Offsets dokumentiert; vollständiges Beispiel erweitert |

---

## Tests

Neue Testdatei `tests/test_offset_features.py` mit **23 Tests**:

| Testgruppe | Abgedeckte Szenarien |
|---|---|
| `TestCyclingOffsetOnStartup` | Positiver Offset einmalig addiert; negativer Offset subtrahiert; Offset 0 → keine Änderung; kein Config-Eintrag → keine Änderung |
| `TestCyclingOffsetDifferentialTracking` | Gleicher Offset nicht erneut angewendet; erhöhter Offset addiert nur Delta; verringerter Offset subtrahiert nur Delta |
| `TestCyclingOffsetPersistence` | `applied_offset` in State-Attributen vorhanden; nach HA-Neustart wiederhergestellt |
| `TestIncrementCyclingCounterNoOffset` | Inkrementiert exakt um +1 ohne Offset; `cycling_offsets`-Parameter nicht mehr in Signatur (Regressionsschutz) |
| `TestEnergyOffsetApplication` | Elektrischer Offset beim Start angewendet; negativer Offset subtrahiert; gleicher Offset nicht doppelt angewendet |
| `TestEnergyOffsetIncrementDifferential` | Erster Aufruf aktualisiert `_applied_offset`; zweiter Aufruf mit gleichem Offset addiert nichts extra |
| `TestOffsetConfigValidation` | Negative Werte bestehen Validierung; nicht-numerische Werte werden auf 0 gesetzt; thermische Schlüssel sind gültig |
| `TestConfigTemplate` | Template enthält `cycling_offsets`, `thermal_energy_total`, `compressor_start_cycling_total` |

---

## Migration / Breaking Changes

**Keine Breaking Changes für Endanwender.**

Für Entwickler: Der Parameter `cycling_offsets` wurde aus `increment_cycling_counter()` entfernt. Eigene Aufrufe dieser Funktion müssen angepasst werden:

```python
# Alt (2.3.x):
await increment_cycling_counter(
    hass, mode=mode, hp_index=1, name_prefix="eu08l",
    cycling_offsets=self._cycling_offsets,   # ← entfernen
)

# Neu (2.4.0):
await increment_cycling_counter(
    hass, mode=mode, hp_index=1, name_prefix="eu08l",
)
```

---

## Betroffene Dateien

| Datei | Art |
|---|---|
| `custom_components/lambda_heat_pumps/utils.py` | Bugfix: Offset-Block aus `increment_cycling_counter()` entfernt |
| `custom_components/lambda_heat_pumps/coordinator.py` | Anpassung: `cycling_offsets`-Parameter aus beiden Aufrufen entfernt |
| `custom_components/lambda_heat_pumps/const_base.py` | Erweiterung: `LAMBDA_WP_CONFIG_TEMPLATE` |
| `tests/test_offset_features.py` | Neu: 23 Offset-Tests |
| `docs/docs/Anwender/lambda-wp-config.md` | Dokumentation aktualisiert |
| `docs/docs/Anwender/historische-daten.md` | Dokumentation aktualisiert |
| `docs/docs/Entwickler/cycling-sensoren.md` | Dokumentation aktualisiert |
| `docs/docs/Entwickler/modbus-wp-config.md` | Dokumentation aktualisiert |
