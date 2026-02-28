# Release 2.3

> ⚠️ **Vor dem Update**: Erstelle ein Backup deiner Home Assistant Konfiguration (Verzeichnis `config/`) sowie der `lambda_wp_config.yaml`. Dieses Release enthält einen Breaking Change, der Entity-IDs verändern kann.

---

## Breaking Changes

### Name-Prefix-Normalisierung (`fcd9a83`)

Die Hilfsfunktion `normalize_name_prefix` konvertiert den konfigurierten `name_prefix` jetzt automatisch zu **Kleinbuchstaben** und entfernt Leerzeichen. Das betrifft alle Entity-IDs und `unique_id`s.

**Wer ist betroffen:** Wer einen `name_prefix` mit Großbuchstaben oder Leerzeichen konfiguriert hatte (z. B. `"EU08L"` oder `"Lambda WP"`), bekommt geänderte Entity-IDs. Bestehende Automationen, Dashboards und Template-Sensoren, die auf die alten Entity-IDs referenzieren, müssen angepasst werden.

---

## Neue Sensoren

### Vorlauftemperatur-Sollwert (`bf47d5a`)

Neuer Sensor `hp_flow_line_temperature_setpoint` für den berechneten Vorlauf-Sollwert der Wärmepumpe. Mit deutschen und englischen Übersetzungen, Aufnahme in das Modbus-Register-Dashboard.

### COP-Sensoren: Arbeitszahlen Heizen / Kühlen / Warmwasser (`1479540`, `4650ec5`, `1a4ac91`)

Neue Sensoren für die Arbeitszahl (Coefficient of Performance):

- **Perioden:** stündlich, täglich, monatlich, gesamt
- **Modi:** Heizen, Kühlen, Warmwasser
- Berechnung aus thermischem Energieertrag und elektrischem Verbrauch
- Vollständige Übersetzungen (DE/EN)

### Thermische Energieverbrauchs-Sensoren (`9dda198`)

Tracking der abgegebenen Wärmeenergie (thermischer Output) pro Wärmepumpe:

- Täglich / Monatlich / Gesamt / Gestern
- Optional aus eigenem externen Quellsensor konfigurierbar (z. B. Wärmemengenzähler)
- Ergänzt die bereits vorhandenen elektrischen Verbrauchssensoren

### Kompressorstarts Gestern (`55f979b`, `477b743`)

Neuer Sensor `compressor_start_cycling_yesterday` zur Auswertung von Kompressorstarts des Vortags. Vollständige Übersetzungen (DE/EN).

---

## Neue Konfigurationsoptionen

### Konfigurierbarer Quellsensor für thermische Energie (`d5c8d4e`, `9dda198`)

In der `lambda_wp_config.yaml` kann pro Wärmepumpe optional ein **eigener Quellsensor für die thermische Energie** angegeben werden:

```yaml
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.mein_stromzaehler"       # elektrisch (Pflicht)
    thermal_sensor_entity_id: "sensor.mein_waermezaehler"  # thermisch (optional)
```

Ohne Angabe wird der Lambda-interne Modbus-Sensor (`compressor_thermal_energy_output_accumulated`) verwendet.

**Weitere Informationen:** [lambda_wp_config.yaml – Energieverbrauchs-Sensoren](../Anwender/lambda-wp-config.md#4-energieverbrauchs-sensoren)

---

## Verbesserungen

### ResetManager: Zentralisierte Reset-Logik (`f6af7ff`)

Alle Reset-Automationen (täglich, 2h, 4h, monatlich, jährlich) wurden in eine dedizierte `ResetManager`-Klasse ausgelagert. Sensoren abonnieren nur noch die für sie relevanten Reset-Signale. Das verhindert unnötige Resets und vereinfacht die interne Logik.

### Energie-Persistenz: Werte bleiben nach HA-Neustart erhalten (`28862bd`)

Der Coordinator speichert den Zustand der Energieverbrauchssensoren persistent. Nach einem HA-Neustart oder Integration-Reload werden die Werte aus dem internen Speicher wiederhergestellt, statt auf 0 zurückzufallen.

### Energie-Konsistenzprüfung (`8186f6e`)

Tages-, Monats- und Jahreswerte werden beim Restore und bei Resets auf Konsistenz geprüft: Ein Vortages-/Vormonatswert kann den aktuellen Gesamtwert nie übersteigen. Das verhindert negative Differenzen und fehlerhafte Statistiken in HA.

### Reset-Sequenz: Yesterday vor Daily (`1a4ac91`)

Die Reset-Reihenfolge wurde korrigiert: `yesterday`-Sensoren werden jetzt **vor** dem täglichen Reset des laufenden Zählers aktualisiert. So stimmt der `_yesterday`-Wert immer mit dem tatsächlichen Vortagesverbrauch überein.

### Energieberechnung korrigiert (`d5c8d4e`)

Die Berechnung der täglichen, monatlichen und jährlichen Energiedifferenzen liest Ausgangswerte jetzt direkt aus den registrierten HA-Entities statt aus internen Hilfsvariablen. Dadurch werden Inkonsistenzen nach Reloads vermieden.

---

## Interne Refactorings

### `const.py` aufgeteilt in drei Dateien

Die 2.600-Zeilen-Datei `const.py` wurde in drei eigenständige Module aufgeteilt:

| Datei | Inhalt |
|---|---|
| `const_base.py` | Grundkonstanten, Retry-Parameter, Zustandstabellen |
| `const_sensor.py` | Alle Sensor-Templates (Modbus-Sensoren) |
| `const_calculated_sensors.py` | Templates für berechnete Sensoren (Energie, COP, Zyklen) |

`const.py` importiert jetzt nur noch aus diesen drei Dateien und re-exportiert alles – keine Änderung an der öffentlichen API.

### `cycling_sensor.py` entfernt

Die Datei war bereits leer und wurde aus dem Repository entfernt.

### Per-Entry-Reload-Locks (K-02)

Der globale `_reload_lock` und das globale `_reload_in_progress`-Flag wurden durch **pro-Entry-Locks** (`_entry_reload_locks`, `_entry_reload_flags`) ersetzt. Dadurch blockiert ein laufender Reload von Entry A nicht mehr den Reload von Entry B.

### Template-Setup-Task gespeichert (K-01)

Der Hintergrund-Task für das Setup von Template-Sensoren (`hass.async_create_task(setup_templates())`) wird jetzt in `coordinator_data["template_setup_task"]` gespeichert, damit er beim Unload sauber abgebrochen werden kann.

### Flankenerkennung `compressor_start_cycling`: RESTART-BLOCK statt START COMPRESSOR

Der Zähler `compressor_start_cycling` reagiert jetzt auf den Übergang in HP-State `2` (**RESTART-BLOCK**) statt in State `5` (START COMPRESSOR).

RESTART-BLOCK ist der Sperrzeit-Zustand nach einem abgeschlossenen Kompressorlauf (Mindestpause zwischen zwei Starts). Damit wird ein **abgeschlossener Zyklus** gezählt, nicht ein gestarteter – robuster und semantisch korrekter.

```
… → 5: START COMPRESSOR → (Betrieb) → 20: STOPPING → 2: RESTART-BLOCK ← Zähler hier
```

### Entity-Cleaner überspringt `config_parameter_`-Sensoren

Der Duplikat-Cleanup (`async_remove_duplicate_entity_suffixes` in `migration.py`) erkannte Sensoren wie `sensor.eu08l_hp1_config_parameter_24` fälschlicherweise als HA-Duplikate (Regex `_\d+$` matched das Suffix `_24`). Sensoren mit `config_parameter_` im Namen werden jetzt in beiden Sammel-Phasen übersprungen.

### Logging: f-Strings durch `%s`-Format ersetzt (M-02)

Über 130 `_LOGGER.xxx(f"…")` Aufrufe in `coordinator.py`, `sensor.py` und `utils.py` wurden auf die HA-konforme `%s`-Schreibweise umgestellt. Das ermöglicht lazy evaluation (String wird nur formatiert, wenn der Log-Level aktiv ist).

### Redundante `_unique_id`-Attribute entfernt (M-03)

In `LambdaCyclingSensor`, `LambdaEnergyConsumptionSensor` und `LambdaThermalEnergySensor` wurden die redundant doppelt gesetzten Attribute `self._unique_id` und die überschreibende `unique_id`-Property entfernt. `self._attr_unique_id` (HA-Standard) ist jetzt die einzige Quelle.

---

## Fixes

### Modbus int16-Vorzeichenkonvertierung (`e11ad7d`)

Korrektur der Konvertierung von vorzeichenbehafteten 16-Bit-Registerwerten (Two's Complement). Neue Hilfsfunktion `clamp_to_int16` verhindert Überlauf bei der Umwandlung.

### Raumthermostat-Offset + Modbus-Konvertierung (`208e358`)

Der konfigurierbare Offset-Bereich für den Raumthermostat wurde korrigiert. Gleichzeitig wurde die Modbus-Konvertierung für vorzeichenbehaftete Werte angepasst.

### `maximum_boiler_temperature` aus Sensor-Templates entfernt (`2f5031a`)

Der Sensor `maximum_boiler_temperature` liest dasselbe Modbus-Register wie `target_high_temperature` und wurde aus den Templates entfernt, um Duplikate zu vermeiden.

---

## Dashboard-Vorlagen

### Lambda Heizkurven-Card (`0872146`)

Lovelace-Custom-Card zur Darstellung der Heizkurve:

- X-Achse: Außentemperatur (−22 °C bis +22 °C), Y-Achse: Vorlauftemperatur
- Linie durch drei Stützpunkte, aktueller Betriebspunkt als roter Punkt
- Reines JavaScript-Modul, keine externen Bibliotheken
- **Dokumentation:** [Vorlagen → Lambda_heizkurve_card](../Vorlagen/Lambda_heizkurve_card.md)

### Lambda Energy Dashboard (`8186f6e`, `2f88eb4`)

YAML-Vorlage für ein vollständiges Energie-Dashboard:

- Tabs: Aktuell, Tagesverbrauch, Monatsverbrauch, Jahresverbrauch
- Neuer Tab **„Lambda Taktungen"** mit täglichen, monatlichen und Gesamt-Zählern für Heizen, Warmwasser, Kühlen, Abtauen und Kompressorstarts
- **Dokumentation:** [Vorlagen → Lambda_energy_dashboard](../Vorlagen/Lambda_energy_dashboard.md)
