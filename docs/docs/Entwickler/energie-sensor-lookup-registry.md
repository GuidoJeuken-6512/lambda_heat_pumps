---
title: "Energie-Sensor-Lookup über die Entity Registry"
---

# Energie-Sensor-Lookup über die Entity Registry

*Zuletzt geändert am 08.08.2026*

Diese Seite beschreibt, warum das Rekonstruieren einer `entity_id` aus dem Gerätenamen strukturell unzuverlässig ist, wie das die betriebsart-abhängigen Energiewerte lahmgelegt hat und warum der Lookup jetzt über die stabile `unique_id` in der Entity Registry läuft.

> **Update v2.8.3**: Der ursprüngliche v2.8.2-Fix (unten als "Die Lösung" beschrieben) deckte nur den Energie-Lookup in `coordinator.py` ab. In v2.8.3 kam heraus, dass derselbe Bug an drei weiteren Stellen steckte – dem *Schreib*-Pfad der Energie-/Zyklus-Zähler (`increment_energy_consumption_counter()`/`increment_cycling_counter()`), den COP-Sensoren (`LambdaCOPSensor`) und den Template-Sensoren (`template_sensor.py`, Heizkurve/ECO-Absenkung) – sowie die eigentliche Ursache, der Separator-Bug in `slugify_name_prefix_for_lookup()` selbst. Alle vier Stellen sind jetzt behoben; Details siehe die Abschnitte "Die Lösung" und "Verwandte Stellen (v2.8.3)" unten.

---

## Das Problem: zwei Normalisierungen für einen Namen

Die Integration leitet aus dem vom Nutzer vergebenen Gerätenamen (Config-Feld `name`) einen `name_prefix` ab. Dafür existieren in `utils.py` **zwei** Funktionen mit unterschiedlichem Verhalten:

| Funktion | Implementierung | Verwendung |
|---|---|---|
| `normalize_name_prefix()` | `.lower().replace(" ", "")` – entfernt **nur** Leerzeichen, lässt `_`/`-`/`.` unangetastet | Bildung der `unique_id` |
| `slugify_name_prefix_for_lookup()` | seit v2.8.3: `normalize_name_prefix(unidecode.unidecode(raw))` – transliteriert nur Umlaute/Unicode, überlässt die Trennzeichen-Regel `normalize_name_prefix()` | `entity_id`-Bildung und Lookups |

Bis einschließlich v2.8.2 rief `slugify_name_prefix_for_lookup()` stattdessen `ha_slugify(raw, separator="")` auf – Home Assistants `slugify()` kollabiert dabei *jedes* Trennzeichen (Leerzeichen, `_`, `-`, `.`, Klammern) einheitlich, unabhängig vom gewählten `separator`. Das lieferte nur bei reinem ASCII plus Leerzeichen dasselbe Ergebnis wie `normalize_name_prefix()` – bei Unterstrich, Bindestrich oder Punkt im Namen liefen beide Funktionen auseinander (das eigentliche #107-Symptom). Seit v2.8.3 sind beide Funktionen bis auf die Umlaut-Transliteration deckungsgleich:

| Gerätename | `normalize_name_prefix()` | `slugify_name_prefix_for_lookup()` (≤ v2.8.2) | `slugify_name_prefix_for_lookup()` (≥ v2.8.3) | |
|---|---|---|---|---|
| `EU08L` | `eu08l` | `eu08l` | `eu08l` | identisch |
| `Lambda EU10L` | `lambdaeu10l` | `lambdaeu10l` | `lambdaeu10l` | identisch |
| `Lambda_EU10L` | `lambda_eu10l` | `lambdaeu10l` | `lambda_eu10l` | **jetzt identisch** |
| `Lambda-EU10L` | `lambda-eu10l` | `lambdaeu10l` | `lambda-eu10l` | **jetzt identisch** |
| `Wärmepumpe Süd` | `wärmepumpesüd` (ungültige `entity_id`) | `warmepumpesud` | `warmepumpesud` | Umlaute bleiben bewusst transliteriert |
| `EU08L (Keller)` | `eu08l(keller)` | `eu08lkeller` | `eu08l(keller)` | **jetzt identisch** – Klammern bleiben eine bekannte, kleinere Restlücke (kein gültiges `entity_id`-Zeichen, siehe HA `_OBJECT_ID`-Regex, aber nicht Teil des #107-Melderfalls) |

---

## Auswirkung: Energiewerte blieben stehen

`_track_hp_energy_type_consumption()` in `coordinator.py` braucht den Wert des eigenen akkumulierten Modbus-Energiesensors, um das Verbrauchs-Delta dem aktuellen Betriebsmodus (heating, hot_water, cooling, defrost) zuzuordnen. Die zugehörige `entity_id` wurde dafür aus dem Gerätenamen **rekonstruiert**:

```python
# vorher
name_prefix = slugify_name_prefix_for_lookup(self.entry.data.get("name", "")) or "eu08l"
sensor_entity_id = default_sensor_id_template.format(name_prefix=name_prefix, hp_idx=hp_idx)
current_energy_state = self.hass.states.get(sensor_entity_id)
```

Bei einem Gerätenamen wie `Lambda_EU10L` ergab das `sensor.lambdaeu10l_hp1_…`, während die tatsächlich registrierte Entity `sensor.lambda_eu10l_hp1_…` hieß – mit Unterstrich.

Die Folge war besonders unauffällig: `hass.states.get()` lieferte `None`, die Funktion protokollierte das nur auf **DEBUG**-Level und brach ab – **bevor** `_energy_last_operating_state` oder `_last_energy_reading` je gesetzt wurden. Es gab keinen Fehler, keine Warnung, keinen unavailable-Sensor. Nur: alle betriebsart-abhängigen Verbrauchswerte blieben unverändert stehen.

Die Basissensoren (`hp1_compressor_power_consumption_accumulated`, `hp1_compressor_thermal_energy_output_accumulated`) waren nicht betroffen – sie werden direkt aus dem Modbus-Register gelesen und brauchen keinen `entity_id`-Lookup. Genau das machte die Diagnose schwierig: Die Rohwerte stiegen sichtbar korrekt, nur die abgeleiteten Werte standen still.

### Warum welche Installation betroffen war

Entscheidend ist, **wann** die Entities angelegt wurden – denn die `entity_id`-Bildung in `generate_sensor_names()` wurde erst mit v2.8.0 auf `slugify` umgestellt, davor nutzte sie `normalize`:

| Entities angelegt | reale `entity_id` | Lookup ab v2.7.0 | |
|---|---|---|---|
| ≤ v2.7.0 | `normalize`-Form (mit Sonderzeichen) | `slugify`-Form | **kaputt** |
| ≥ v2.8.0 | `slugify`-Form | `slugify`-Form | funktioniert |

Beim Update behält Home Assistant die bestehende `entity_id` (die Zuordnung läuft über die `unique_id`), der neu berechnete Vorschlag wird verworfen. Bestandsinstallationen behielten also ihre alte Form – und liefen damit ins Leere.

### Herkunft der Regression

Der fehlerhafte Lookup entstand in **v2.7.0** (Commit `9a8187d`) – ausgerechnet als Fix für [#93](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/93): Dort brach der Lookup bei **Umlauten** im Gerätenamen, weil Home Assistant beim Anlegen einer Entity intern transliteriert (`ä` → `a`), die Integration das aber nicht nachbildete. Die Umstellung auf `slugify_name_prefix_for_lookup()` löste das korrekt – entfernte als Nebeneffekt aber auch Unterstriche, Bindestriche und Punkte, die zuvor unkritisch waren. Ein Fix hat also einen zweiten, breiteren Fehler eingeführt.

---

## Die Lösung: Nachschlagen statt Raten

Die `entity_id` wird nicht mehr konstruiert, sondern über die **`unique_id`** in der Entity Registry aufgelöst:

```python
# nachher – coordinator._resolve_internal_energy_sensor_entity_id()
names = generate_sensor_names(
    f"hp{hp_idx}", sensor_id, sensor_id,
    normalize_name_prefix(self.entry.data.get("name", "")) or "eu08l",
    self._use_legacy_names,
)
registry = self._entity_registry or async_get_entity_registry(self.hass)
resolved = registry.async_get_entity_id("sensor", DOMAIN, names["unique_id"])
```

Der Ansatz funktioniert, weil die `unique_id` **stabil** ist:

- Sie wird seit jeher mit `normalize_name_prefix()` gebildet; diese Bildung wurde nie geändert (siehe auch [unique_id – Kopplung an name_prefix](unique-id-name-prefix-kopplung.md)).
- Home Assistant nutzt sie selbst als unveränderlichen Schlüssel, um Entities über Neustarts und Updates hinweg wiederzuerkennen.

Damit deckt der Lookup alle Fälle ab:

| Situation | Ergebnis |
|---|---|
| Sonderzeichen im Namen, Altinstallation | korrekt aufgelöst |
| Sonderzeichen im Namen, Neuinstallation | korrekt aufgelöst |
| Umlaute im Namen (vgl. #93) | korrekt aufgelöst |
| Vom Nutzer manuell umbenannte Entity | korrekt aufgelöst |

Der letzte Fall ist der eigentliche Gewinn: Eine namensbasierte Konstruktion – gleich welcher Variante – scheitert grundsätzlich, sobald jemand die Entity in der Oberfläche umbenennt. Nur der Registry-Lookup folgt der Umbenennung.

### Fallback

Steht die Entity (noch) nicht in der Registry – etwa im ersten Zyklus nach dem Start – greift die bisherige namensbasierte Konstruktion. Das Verhalten entspricht dort exakt dem vorherigen Stand, und da der Lookup bei **jedem** Poll-Zyklus neu erfolgt, heilt sich ein Fehlgriff im nächsten Zyklus selbst. Ein Registry-Fehler wird abgefangen und darf den Poll-Zyklus nicht abbrechen.

### Zuordnung Sensor-Typ → sensor_id

Die für die `unique_id` benötigten Template-Schlüssel liegen als Modul-Konstante in `coordinator.py`:

```python
INTERNAL_ENERGY_SENSOR_IDS = {
    "electrical": "compressor_power_consumption_accumulated",
    "thermal": "compressor_thermal_energy_output_accumulated",
}
```

Wichtig ist, die `unique_id` über dieselbe zentrale Funktion `generate_sensor_names()` zu bilden, die auch `sensor.py` beim Anlegen der Entity verwendet – nicht über eine eigene Formel. Sonst laufen beide Seiten erneut auseinander. Genau das sichert der Test `test_unique_id_matches_sensor_py_generation` ab.

Zu unterscheiden von diesem *Lese*-Helfer ist `_default_internal_energy_entity_id()` (ebenfalls `coordinator.py`, seit v2.8.3): Er liefert bewusst **ohne** Registry-Auflösung dieselbe namensbasierte `entity_id` wie früher. Grund: Diese sechs Stellen speisen die Sensor-Wechsel-Erkennung, deren Ergebnis mit einem *persistierten* Wert verglichen und wieder zurückgeschrieben wird. Eine Registry-Auflösung würde auf Bestandsanlagen mit abweichender `entity_id` (z. B. eine zweite Wärmepumpe, deren Entities unter einer älteren Version angelegt wurden) beim ersten Start nach dem Update einen Sensor-Wechsel melden und die Energie-Basislinie zurücksetzen – nicht risikofrei. Merksatz: **Lesen → Registry-Lookup, Vergleich mit Persistiertem → Namensform beibehalten.**

---

## Verwandte Stellen (v2.8.3)

Derselbe Bug – `entity_id` aus dem Namen statt aus der `unique_id` – steckte in drei weiteren Stellen, alle in v2.8.3 behoben:

| Stelle | Symptom | Fix |
|---|---|---|
| `utils.py` – `increment_energy_consumption_counter()` / `increment_cycling_counter()` | Betriebsart-abhängige Zähler (`hot_water_energy_*`, `*_cycling_*` usw.) blieben bei jeder Sonderzeichen-Installation stehen – der eigentliche #107-Fall, den der ursprüngliche Fix (nur Lesepfad in `coordinator.py`) nicht abdeckte. | Nutzen jetzt denselben Helper `resolve_entity_id_by_unique_id()`. |
| `sensor.py` – `LambdaCOPSensor` | Alle COP-Sensoren einer zweiten Wärmepumpe/eines zweiten Heizkreises blieben dauerhaft `unbekannt`. | Quell-`entity_id`s werden einmalig in `async_setup_entry()` über `resolve_entity_id_by_unique_id()` aufgelöst statt über rohen `generate_sensor_names()`-Text. |
| `template_sensor.py` – Heizkurven-Sensor (genau die Stelle, die hier zuvor als "nicht abgedeckt" geführt wurde) | Berechneter COP (`*_cop_calc`) blieb bei `0.0`; Heizkurve rechnete still mit den eingebauten Default-Stützpunkten statt den konfigurierten; ECO-Absenkung griff nie. | Zwei neue Helfer in `utils.py`: `resolve_sensor_entity_id()` (bündelt "Namen erzeugen → Domain anpassen → über `unique_id` auflösen", inkl. des `_number`-Suffix aus `number.py`) und `resolve_template_entity_ids()` (löst Entity-Referenzen in einem fertig formatierten Template-String generisch auf, ohne die Template-Definitionen selbst anzufassen). |

Weiterhin offen, bewusst nicht angefasst:

| Stelle | Thema |
|---|---|
| `coordinator.py` – `_on_entity_registry_changed()` | Filtert Registry-Change-Events per Präfix-Vergleich. Ein Umbau auf `config_entry_id` wäre robuster, muss aber `remove`-Events berücksichtigen, bei denen der Registry-Eintrag bereits entfernt ist. |
| `coordinator.py` – `_update_entity_address_mapping()` | Rät pro Sensor mehrere `entity_id`-Varianten, statt `async_entries_for_config_entry()` zu nutzen. Größerer Blast-Radius als die oben behobenen Stellen (u. a. Override-Namen-Sensoren mit abweichender `unique_id`-Formel) – eigenes Ticket. |

---

## Diagnose im Log

Bei aktiviertem DEBUG-Logging für `custom_components.lambda_heat_pumps.coordinator`:

```
[Energy] HP1 electrical: Verwende Modbus-Sensor sensor.lambda_eu10l_hp1_compressor_power_consumption_accumulated
```

Diese Zeile zeigt die **tatsächlich verwendete** Entity-ID. Erscheint stattdessen wiederholt

```
[Energy] HP1 electrical: Sensor sensor.… nicht verfügbar (state=None)
```

liegt der Sensor unter einer anderen ID vor – dann prüfen, ob die Entity existiert und ob ihre `unique_id` zum Gerätenamen passt.

---

## Verwandte Seiten

- [unique_id – Kopplung an name_prefix](unique-id-name-prefix-kopplung.md) – warum die `unique_id` langfristig von `entry_id` statt `name_prefix` abgeleitet werden sollte
- [Energieverbrauchsberechnung](energieverbrauchssensoren.md) – Aufbau der betriebsart-abhängigen Verbrauchssensoren
