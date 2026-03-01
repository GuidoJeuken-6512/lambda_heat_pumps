---
title: "unique_id – Kopplung an name_prefix: Problem und Lösung"
---

# unique_id – Kopplung an name_prefix: Problem und Lösung

Diese Seite beschreibt, warum die Ableitung der `unique_id` aus dem vom Nutzer konfigurierbaren `name_prefix` ein strukturelles Problem darstellt, welche Auswirkungen das hat und wie eine verlustfreie Migration zur stabilen `entry_id`-basierten Lösung aussieht.

---
 
## Das Problem

### Aktuelle Implementierung

In `utils.py` wird die `unique_id` einer Entität im Legacy-Modus so gebildet:

```python
# utils.py – generate_sensor_names() – Legacy-Modus
unique_id = f"{name_prefix_lc}_{device_prefix}_{sensor_id}"
# Beispiel: "eu08l_hp1_cop_calc"
```

Der `name_prefix` stammt direkt aus dem `name`-Feld der Config-Entry, das der Nutzer beim Einrichten der Integration selbst eingibt (z. B. `"EU08L"`) und jederzeit über den Config Flow ändern kann.

### Warum das ein Problem ist

Die `unique_id` ist das **unveränderliche Erkennungsmerkmal** einer Entität in Home Assistant. Die Entity Registry verknüpft damit:

- benutzerdefinierte Namen, Icons und Bereichszuweisungen
- Referenzen aus Automationen und Skripten
- Dashboard-Karten
- Statistik- und Historiendaten (über die `entity_id`)

**Grundregel:** Die `unique_id` darf sich niemals ändern – sonst behandelt HA die Entität als neu und die alte als verwaist.

Weil `name_prefix` aus einer Nutzereingabe abgeleitet wird, kann er sich ändern. Damit ändert sich die `unique_id` – mit weitreichenden Folgen.

---

## Auswirkungen bei Namensänderung

**Szenario:** Nutzer benennt die Integration von `"EU08L"` zu `"Meine Wärmepumpe"` um.

| | Vorher | Nachher |
|---|---|---|
| `name_prefix` | `eu08l` | `meinewärmepumpe` |
| `unique_id` | `eu08l_hp1_cop_calc` | `meinewärmepumpe_hp1_cop_calc` |

Da HA anhand der `unique_id` Kontinuität erkennt, behandelt es die umbenannten Entitäten als **völlig neue Objekte**:

1. **Neue Entitäten werden angelegt** – mit den neuen `unique_id`-Werten, als wären sie nie dagewesen
2. **Alte Entitäten bleiben als Geister** – in der Entity Registry, ohne zugehörigen Code
3. **Konflikte bei `entity_id`** – HA hängt `_2`, `_3` usw. an (z. B. `sensor.hp1_cop_calc_2`)
4. **Automationen und Skripte brechen** – alle Referenzen auf alte `entity_id`-Werte sind ungültig
5. **Dashboard-Karten zeigen „Entität nicht gefunden"**
6. **Benutzerdefinierte Namen, Icons und Bereichszuweisungen gehen verloren**
7. **Statistiken/Historie** bleiben an der alten (nun verwaisten) Entität hängen

Das Tückische: Der Nutzer ändert nur einen **Anzeigenamen** und erwartet keinerlei technische Auswirkung.

Die aktuelle Notlösung in `migration.py` (`migrate_to_legacy_names()`) versucht, verwaiste Entitäten zu löschen und Duplikate zu bereinigen – das ist aber ein reaktives Band-Aid, das den Datenverlust nicht verhindert, sondern nur die Registry aufräumt.

---

## Die Lösung: entry_id statt name_prefix

### Warum entry_id?

Die `entry_id` ist eine vom System automatisch generierte UUID, die beim Anlegen einer Config-Entry einmalig vergeben wird und sich **niemals ändert** – unabhängig davon, was der Nutzer umbenennt oder rekonfiguriert.

```python
# config_entry.entry_id
# Beispiel: "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"
```

### Code-Vergleich

```python
# BISHER (instabil – ändert sich mit dem Nutzernamen):
unique_id = f"{name_prefix_lc}_{device_prefix}_{sensor_id}"
# Beispiel: "eu08l_hp1_cop_calc"

# KÜNFTIG (stabil – entry_id ist unveränderliche UUID):
unique_id = f"{entry_id}_{device_prefix}_{sensor_id}"
# Beispiel: "a1b2c3d4e5f6_hp1_cop_calc"
```

Die `entry_id` ist in `generate_sensor_names()` als zusätzlicher Parameter zu ergänzen. Der `name_prefix` bleibt weiterhin für `entity_id` und den Anzeigenamen (`name`) relevant – nur die `unique_id` wird davon entkoppelt.

---

## Migrationsstrategie ohne Datenverlust

### Das zentrale Werkzeug: `async_update_entity()`

Home Assistant bietet eine API, die eine `unique_id` **in-place umbenennt**. Die Entität bleibt als dasselbe Objekt erhalten – nur ihr interner Schlüssel ändert sich:

```python
entity_registry.async_update_entity(
    entity_id,          # bestehende entity_id (bleibt gleich)
    unique_id=new_uid   # neuer unique_id-Wert
)
```

Dies ist der fundamentale Unterschied zur aktuellen Strategie (`async_remove` → Neuanlegen), die alle verknüpften Daten unwiederbringlich verliert.

### Was bei der Migration erhalten bleibt

| Datenschicht | Mechanismus | Ergebnis |
|---|---|---|
| Entity Registry (Namen, Icons, Bereiche) | Registry-Eintrag bleibt, nur `unique_id` überschrieben | **Erhalten** |
| Statistiken / Historiendaten | Recorder ist an `entity_id` gebunden, nicht `unique_id` | **Erhalten** |
| Automationen und Skripte | Referenzieren `entity_id`, nicht `unique_id` | **Erhalten** |
| Dashboard-Karten | Referenzieren `entity_id`, nicht `unique_id` | **Erhalten** |
| Benutzerdefinierte Einstellungen | Im Registry-Eintrag gespeichert, der bleibt | **Erhalten** |

Solange `entity_id` unverändert bleibt, bemerkt der Nutzer die Migration nicht.

### Migrationsfunktion – Pseudocode

```python
async def migrate_v9_unique_id_to_entry_id(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> bool:
    """
    Migriert unique_ids von name_prefix-basiert auf entry_id-basiert.
    Verwendet async_update_entity() – kein Datenverlust.
    """
    entry_id = config_entry.entry_id
    name_prefix = normalize_name_prefix(config_entry.data.get("name", ""))

    entity_registry = async_get_entity_registry(hass)
    registry_entries = entity_registry.entities.get_entries_for_config_entry_id(entry_id)

    migrated = 0
    for reg_entry in registry_entries:
        old_uid = reg_entry.unique_id

        # Fall 1: Legacy-Modus – unique_id beginnt mit name_prefix
        if name_prefix and old_uid.startswith(name_prefix + "_"):
            suffix = old_uid[len(name_prefix) + 1:]  # z. B. "hp1_cop_calc"
            new_uid = f"{entry_id}_{suffix}"

        # Fall 2: Standard-Modus – kein name_prefix-Präfix, entry_id voranstellen
        elif not old_uid.startswith(entry_id):
            new_uid = f"{entry_id}_{old_uid}"

        else:
            continue  # Bereits migriert

        entity_registry.async_update_entity(
            reg_entry.entity_id,
            unique_id=new_uid
        )
        _LOGGER.info("unique_id migriert: %s → %s", old_uid, new_uid)
        migrated += 1

    _LOGGER.info("Migration v9 abgeschlossen: %d unique_id(s) aktualisiert", migrated)
    return True
```

---

## Einordnung in die bestehende Migrationsinfrastruktur

Die Integration verfügt über ein versioniertes Migrationssystem (`MigrationVersion` in `const_migration.py`, Dispatcher in `migration.py`). Die neue Migrations-Stufe fügt sich nahtlos ein:

```python
# const_migration.py
class MigrationVersion(IntEnum):
    ...
    REGISTER_ORDER_TERMINOLOGY = 8        # aktuell
    UNIQUE_ID_DECOUPLED_FROM_NAME = 9     # neu
```

Die Migrationsfunktion wird im `perform_structured_migration()`-Dispatcher als neuer Eintrag für Version 9 registriert. Vor der Migration wird – wie bei allen bisherigen Stufen – ein Registry-Backup via `create_registry_backup()` erstellt.

### Voraussetzungen für die Implementierung

1. `generate_sensor_names()` in `utils.py` erhält `entry_id` als zusätzlichen Parameter
2. Alle Aufrufstellen (`sensor.py`, `climate.py`, `number.py`, `migration.py`) werden angepasst
3. Die neue Migrationsfunktion wird in `migration.py` implementiert und im Dispatcher eingehängt
4. `const_migration.py` bekommt den neuen Enum-Wert

---

## Status

| Aspekt | Status |
|---|---|
| Problem analysiert | Ja |
| Lösung definiert | Ja |
| Implementierung | Offen |
| Ziel-Release | nicht festgelegt |

Verwandte Analyse: [integration_analysis.md](../../analysis/integration_analysis.md) (H-02)
