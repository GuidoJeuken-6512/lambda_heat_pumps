---
title: "Release 2.8.3"
---

# Release 2.8.3

*Zuletzt geändert am 08.08.2026*

> **Aktueller Release** · Branch `V2.8.3`

---

## Zusammenfassung

Release 2.8.3 behebt [Issue #107](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/107) tatsächlich vollständig — der als 2.8.2 veröffentlichte Fix (**zurückgezogen**, siehe unten) deckte nur einen von vier betroffenen Stellen sowie nicht die eigentliche Ursache ab. Enthält im Kern eine wiederkehrende Bugklasse: Entity-Referenzen wurden aus dem Gerätenamen **rekonstruiert** statt über die stabile `unique_id` in der Entity Registry **aufgelöst**. Bei Sonderzeichen im Gerätenamen (Unterstrich, Bindestrich, Punkt), bei einer zweiten Wärmepumpe/einem zweiten Heizkreis mit abweichender `entity_id` oder bei einer vom Nutzer manuell umbenannten Entity driftete die Rekonstruktion von der real registrierten `entity_id` ab — mit unterschiedlichen, teils sehr unauffälligen Symptomen (Zähler frieren still ein, COP-Sensoren bleiben `unbekannt`, Heizkurve rechnet mit falschen Stützpunkten). Zusätzlich enthält dieses Release eine rückblickende Durchsicht aller Änderungen seit V2.6.0 mit dem Ziel, eigenen Code durch Home-Assistant-Bordmittel zu ersetzen und Duplikate zu entfernen — ohne Verhaltensänderung. Keine Breaking Changes; keine `entity_id`/`unique_id` einer Bestandsentity ändert sich.

**Vollständig live gegen einen realen Migrationspfad getestet:** V2.6.0 → V2.8.0 (Fehler reproduziert) → V2.8.3 (Fehler behoben, 0 Regressionen), zusätzlich ein gezieltes Szenario mit künstlich divergierenden `entity_id`s (Nutzer-Umbenennung simuliert).

---

## Fehlerbehebungen ([#107](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/107))

### Befund 1 — Der 2.8.2-Fix deckte nur die Lese-, nicht die Schreib-Seite ab

**Betroffen:** Betriebsart-abhängige Verbrauchswerte und Zyklus-Zähler aller Bestandsinstallationen mit Sonderzeichen im Gerätenamen.

**Symptom:** `hot_water_energy_daily/total`, `stby_energy_*`, `cooling_energy_*`, `defrost_energy_*` sowie alle `*_cycling_total/daily/2h/4h`-Sensoren blieben stehen, obwohl der 2.8.2-Fix bereits veröffentlicht war.

**Ursache:** `increment_energy_consumption_counter()` und `increment_cycling_counter()` (`utils.py`) suchten ihre Ziel-Sensoren weiterhin, indem sie eine `entity_id` aus dem Gerätenamen rekonstruierten und textuell gegen die Entity Registry abglichen — der 2.8.2-Fix hatte nur den Lesepfad in `coordinator.py` korrigiert.

**Fix:** Beide Funktionen lösen ihre Ziel-Entity jetzt über die `unique_id` auf, mit dem gemeinsamen Helper `resolve_entity_id_by_unique_id()` (neu in `utils.py`). Die bisherige textbasierte Konstruktion bleibt als selbstheilender Fallback für den ersten Zyklus nach Neuanlage einer Entity.

**Betroffene Dateien:** `custom_components/lambda_heat_pumps/utils.py`

### Befund 2 — Die eigentliche Ursache: Separator-Bug in `slugify_name_prefix_for_lookup()`

**Betroffen:** Jede Installation mit Unterstrich, Bindestrich oder Punkt im Gerätenamen.

**Symptom:** `slugify_name_prefix_for_lookup()` rief `slugify(name, separator="")` auf. Home Assistants `slugify()` kollabiert *jedes* Trennzeichen (Leerzeichen, `_`, `-`, `.`, Klammern) einheitlich zum gewählten Separator — unabhängig vom Wert. `normalize_name_prefix()` (bildet die `unique_id`) tut das nicht: Sie entfernt nur Leerzeichen und lässt `_` unangetastet. Ein einfacher Wechsel auf `separator="_"` hätte Unterstriche repariert, aber Namen mit Leerzeichen neu gebrochen (`"Lambda WP"` → `"lambda_wp"` statt `"lambdawp"`).

**Fix:** Die Funktion trennt jetzt zwei Anliegen, die vorher unzulässig vermischt waren: zuerst Unicode-Transliteration (Umlaute etc., über dieselbe `unidecode`-Bibliothek, auf die `homeassistant.util.slugify()` intern ohnehin aufbaut), danach die bestehende, unveränderte Trennzeichen-Regel aus `normalize_name_prefix()`. `entity_id` und `unique_id` stimmen bei Unterstrichen wieder überein, ohne den in 2.7.0 behobenen Leerzeichen-Fall erneut zu brechen.

**Bekannte, bewusst offene Restlücke:** Ein literaler Bindestrich/Punkt/Klammer im Gerätenamen wird in der `entity_id` weiterhin unverändert durchgereicht statt zu `_` kollabiert — kein gültiges HA-`entity_id`-Zeichen, aber konsistent mit der `unique_id`-Behandlung und nicht Teil des in #107 gemeldeten Falls.

**Betroffene Dateien:** `custom_components/lambda_heat_pumps/utils.py`

### Befund 3 — Energie-/Zyklus-Zähler blieben für eine zweite Wärmepumpe stehen (In-Memory-Cache)

**Betroffen:** Installationen mit mehr als einer Wärmepumpe, bei denen die real registrierten `entity_id`s der zweiten (dritten, …) Wärmepumpe von der aktuell berechneten Form abweichen (z. B. durch Auto-Erkennung unter einer älteren Version oder manuelle Umbenennung).

**Symptom:** Auch nach Befund 1 blieben `hp2`-Zähler stehen, während `hp1` normal lief.

**Ursache:** `sensor.py` speichert jede erzeugte Entity in `energy_entities`/`cycling_entities` (`hass.data`), geschlüsselt über das eigene `entity_id`-Attribut — ausgelesen **bevor** `async_add_entities()` die Entity tatsächlich bei Home Assistant registriert hat. Die Increment-Funktionen lösen die reale `entity_id` zwar korrekt über die Registry auf, suchten die Entity-**Instanz** im Cache aber über genau diesen aufgelösten Wert — ein Fehltreffer, da der Cache unter dem abweichenden, vor der Registrierung gültigen Wert geschlüsselt war.

**Fix:** Beide Caches sind jetzt über die `unique_id` geschlüsselt (baubedingt stabil), konsequent auch angewendet auf die weiteren Konsumenten: der tägliche „Yesterday"-Sensor-Rollover (`automations.py`) und die Energie-State-Persistenz für Neustarts (`coordinator.py`).

**Betroffene Dateien:** `custom_components/lambda_heat_pumps/sensor.py`, `custom_components/lambda_heat_pumps/automations.py`, `custom_components/lambda_heat_pumps/coordinator.py`

### Befund 4 — COP-Sensoren einer zweiten Wärmepumpe dauerhaft `unbekannt`

**Betroffen:** Wie Befund 3.

**Symptom:** Alle `*_cop_daily/monthly/yearly/total/hourly`-Sensoren der zweiten Wärmepumpe zeigten dauerhaft `unbekannt`.

**Ursache:** `LambdaCOPSensor` liest seine thermischen/elektrischen Quell-Sensoren über `self._thermal_energy_entity_id`/`self._electrical_energy_entity_id`, einmalig bei der Erzeugung aus rohem `generate_sensor_names()`-Text gesetzt — nie gegen die Entity Registry korrigiert. `hass.states.get()` ging ins Leere, das `async_track_state_change_event()`-Abonnement feuerte nie.

**Fix:** Beide Quell-`entity_id`s werden über `resolve_entity_id_by_unique_id()` aufgelöst, einmalig in `async_setup_entry()` vor der Erzeugung jedes `LambdaCOPSensor`.

**Betroffene Dateien:** `custom_components/lambda_heat_pumps/sensor.py`

### Befund 5 — Template-Sensoren: vierte und letzte Stelle derselben Bugklasse

**Betroffen:** Wie Befund 3/4 — zusätzlich die berechnete COP (`*_cop_calc`) und die Heizkurve.

**Symptom:** Zwei für Nutzer sichtbare Folgen: der **berechnete COP** (`*_cop_calc`) stand dauerhaft auf `0.0`, weil das erzeugte Template `sensor.<name>_hp2_compressor_*_accumulated` referenzierte, während die registrierte Entity `sensor.<name-ohne-unterstrich>_hp2_…` heißt; und die **Heizkurve** (`*_heating_curve_flow_line_temperature_calc`) fiel still auf die eingebauten Default-Stützpunkte zurück, während die **ECO-Absenkung** überhaupt nie griff.

**Fix:** Zwei neue gemeinsame Helfer in `utils.py`:

- `resolve_sensor_entity_id()` bündelt „Namen erzeugen → Domain anpassen → über `unique_id` auflösen" (inklusive des `_number`-Suffix, das `number.py` an seine `unique_id` anhängt).
- `resolve_template_entity_ids()` löst die in einem fertig formatierten Template-String referenzierten Entities generisch auf, ohne die Template-Definitionen selbst anzufassen.

Findet die Registry keinen Treffer, bleibt die bisherige namensbasierte Form erhalten — selbstheilend beim nächsten Start.

**Betroffene Dateien:** `custom_components/lambda_heat_pumps/utils.py`, `custom_components/lambda_heat_pumps/template_sensor.py`

### Nebenbefund — `Template not found`-Warnung bei jedem Setup

**Betroffen:** Setup-/Reload-Log für `cooling`/`defrost`/`hot_water`/`stby`.

**Symptom:** `Template not found for <mode>_energy_hourly` wurde als `WARNING` geloggt, obwohl kein Fehler vorliegt — `hourly` ist nur für `heating` als Template definiert, der Guard überspringt die anderen vier Modi korrekt.

**Fix:** Auf `DEBUG` heruntergestuft.

**Betroffene Dateien:** `custom_components/lambda_heat_pumps/sensor.py`

---

## Internes Refactoring (keine Funktionsänderung)

Rückblickende Durchsicht aller Änderungen seit V2.6.0 mit dem Ziel, Home Assistants eigene Bordmittel zu nutzen und Duplikate zu entfernen — **keine** `entity_id`/`unique_id` ändert sich.

| Änderung | Datei |
|---|---|
| `get_int32_register_order()` nutzt `utils.get_firmware_version()` statt eigener Fallback-Kaskade; toter Import entfernt | `modbus_utils.py` |
| Sechs identische Konstruktionen der internen Energie-Sensor-`entity_id` → ein Helper `_default_internal_energy_entity_id()` | `coordinator.py` |
| Fünf identische Blöcke zur Cycling-Entity-Cache-Befüllung → eine Schleife | `sensor.py` |
| `LambdaCyclingSensor._handle_reset()`: fünf identische `if`/`elif`-Zweige → eine Bedingung (`CYCLING_RESET_INTERVALS`) | `sensor.py` |
| Siebenfaches `[65535]`-Literal → benannte Konstante `SENTINEL_NO_REQUEST` | `const_sensor.py` |

**Bewusst *nicht* geändert** (geprüft, Ersetzung hätte Bugs reproduziert oder war bereits optimal): der geteilte `asyncio.Lock` in `modbus_utils.py`, `MAX_ENERGY_DELTA_WH`, `FIRMWARE_CONFIG` — bereits mit den richtigen Bordmitteln umgesetzt. `slugify_name_prefix_for_lookup()` darf **nicht** durch `homeassistant.util.slugify()` ersetzt werden (live verifiziert, würde die #107-Regression reproduzieren). Die sechs Stellen der Sensor-Wechsel-Erkennung in `coordinator.py` behalten bewusst ihre namensbasierte Form (Vergleich mit persistiertem Wert — Registry-Auflösung würde auf Bestandsanlagen einen Sensor-Wechsel melden und die Energie-Basislinie zurücksetzen).

---

## Betroffene Dateien

| Datei | Änderung |
|---|---|
| `custom_components/lambda_heat_pumps/utils.py` | `resolve_entity_id_by_unique_id()`, `resolve_sensor_entity_id()`, `resolve_template_entity_ids()` neu; `slugify_name_prefix_for_lookup()` Separator-Fix; `increment_energy_consumption_counter()`/`increment_cycling_counter()` nutzen Registry-Lookup |
| `custom_components/lambda_heat_pumps/coordinator.py` | Energie-State-Persistenz auf `unique_id`-Keying umgestellt; `_default_internal_energy_entity_id()` neu |
| `custom_components/lambda_heat_pumps/sensor.py` | `energy_entities`/`cycling_entities`-Cache auf `unique_id`-Keying umgestellt; COP-Quell-`entity_id`s über Registry aufgelöst; Cache-Loop und `_handle_reset()` entduplizert; Log-Downgrade |
| `custom_components/lambda_heat_pumps/template_sensor.py` | Heizkurven-Sensor löst Quell-Entities (Außentemperatur, Stützpunkte, `operating_state`, `eco_temp_reduction`) über die Registry auf |
| `custom_components/lambda_heat_pumps/automations.py` | „Yesterday"-Sensor-Rollover auf `unique_id`-Keying umgestellt |
| `custom_components/lambda_heat_pumps/modbus_utils.py` | `get_int32_register_order()` entduplizert |
| `custom_components/lambda_heat_pumps/const_sensor.py` | `SENTINEL_NO_REQUEST`-Konstante neu |

---

## Verifikation

- **Unit-Tests:** 541 → 559 grün (18 neue Tests), 1 skipped.
- **Kompletter Migrationstest** in einer Docker-Testinstanz (2 Wärmepumpen, Gerätename `Lambda_EU10L`): V2.6.0 installiert und Config neu angelegt (Baseline: Zähler laufen) → Update auf V2.8.0 (Fehler reproduziert: Basissensor stieg, alle abgeleiteten Zähler eingefroren, 26 von 30 COP-Sensoren `unbekannt`, 8 `Template not found`-Warnungen) → Update auf V2.8.3 (alle Zähler laufen wieder, 0 von 30 COP-Sensoren `unbekannt`, 0 `Template not found`-Warnungen, 0 ERROR-Zeilen, alle 330 `entity_id`/`unique_id` unverändert).
- **Zusätzliches Divergenz-Szenario:** 5 Entities gezielt umbenannt (nur `entity_id`, `unique_id` unverändert — simuliert eine Nutzer-Umbenennung bzw. eine unter älterer Version angelegte zweite Wärmepumpe). Berechneter COP sprang von `0.0` auf den korrekten Wert; Heizkurve reagierte auf einen geänderten Stützpunkt aus der umbenannten Entity (Log-Beleg: `mid=number.lambdaeu10l_hc2_heating_curve_mid_outside_temp` wurde korrekt aufgelöst).

Details zur Registry-Lookup-Architektur: [Energie-Sensor-Lookup über die Entity Registry](../Entwickler/energie-sensor-lookup-registry.md).

---

## [2.8.2] - 2026-08-05 (zurückgezogen)

Wurde aus den Releases zurückgezogen — der Fix deckte Issue #107 nur unvollständig ab (siehe Befund 1 oben). Enthielt zusätzlich die `ambient_temperature`-Firmware-Bereichs-Korrektur ([#108](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/108)), die in 2.8.3 unverändert enthalten ist. Details: [CHANGELOG.md](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/blob/main/CHANGELOG.md).
