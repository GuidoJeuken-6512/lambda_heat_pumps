---
title: "Migrationssystem"
---

# Migrationssystem

*Zuletzt geändert am 06.09.2026*

**Stand:** Release 3.5.2 (Rewrite auf [`modbus-connection`](https://github.com/home-assistant-libs/modbus-connection)/`tmodbus`, Branch `3.5`; Hintergrund zum Rewrite: [Issue #99](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/99))

Das versionierte Migrationssystem aus der Vor-Rewrite-Integration
(`MigrationVersion`-Enum, `migration.py`, `const_migration.py`,
Registry-Backups, Config-Datei-Textmigration) existiert seit 3.5 nicht mehr.
An seine Stelle tritt eine einzelne, deutlich kleinere Funktion.

## `async_migrate_entry` (`__init__.py`)

Ein einfacher Integer-Zähler, `ENTRY_VERSION` (`const.py`, aktuell `9`),
ersetzt das alte Enum. Eine Entry, deren `entry.version` kleiner ist, wird
beim nächsten Setup **einmalig** aktualisiert:

```python
async def async_migrate_entry(hass: HomeAssistant, entry: LambdaConfigEntry) -> bool:
    if entry.version >= ENTRY_VERSION:
        return True

    data = dict(entry.data)
    options = dict(entry.options)

    for key in ("num_hps", "num_boil", "num_buff", "num_sol", "num_hc"):
        data.pop(key, None)

    data[CONF_PORT] = int(data[CONF_PORT])
    data[CONF_SLAVE_ID] = int(data[CONF_SLAVE_ID])
    data.setdefault(CONF_USE_LEGACY_MODBUS_NAMES, True)

    firmware = data.get(CONF_FIRMWARE_VERSION) or options.pop(CONF_FIRMWARE_VERSION, None)
    data[CONF_FIRMWARE_VERSION] = firmware if firmware in FIRMWARE_VERSIONS else FIRMWARE_VERSIONS[-1]

    options.setdefault(CONF_INT32_REGISTER_ORDER, await _async_read_register_order(hass))

    hass.config_entries.async_update_entry(entry, data=data, options=options, version=ENTRY_VERSION)
    return True
```

| Schritt | Zweck |
|---|---|
| Modulzahlen (`num_hps`, …) aus `entry.data` entfernen | Werden ab 3.5 bei **jedem** Setup neu geprobt statt gespeichert (siehe [Ablaufdiagramm](Ablaufdiagramm.md#2-setup-ablauf)) |
| `port`/`slave_id` zu `int` erzwingen | Der Nummern-Selector im Config-Flow lieferte früher `float` |
| `use_legacy_modbus_names` defaulten auf `True` | Jede Entry vor 3.5 nutzte Entity-Namen mit `name_prefix` — siehe [unique_id und name_prefix](unique-id-name-prefix-kopplung.md) |
| `firmware_version` nach `entry.data` verschieben | Lag vorher uneinheitlich mal in `data`, mal in `options` |
| `int32_register_order` in die Optionen übernehmen | Einmaliger Fallback: liest die alte `lambda_wp_config.yaml` (`_async_read_register_order`), falls die Option noch nicht gesetzt ist — siehe [Register-Reihenfolge](register-reihenfolge-int32.md) |

Es gibt keine Rollback-Logik, kein Backup-System und keinen
Fehlerschwellenwert mehr — die Migration ist eine reine Werte-Umformung ohne
I/O außer dem einmaligen, fehlertoleranten Lesen der alten YAML-Datei
(`_async_read_register_order`; ein Lesefehler fällt einfach auf den
Firmware-Standard zurück, statt die Migration abzubrechen).

## Was aus der Config-Datei-Migration wurde

`lambda_wp_config.yaml` wird nicht mehr automatisch umgeschrieben oder um
fehlende Abschnitte ergänzt. Sie hat nur noch drei mögliche Abschnitte
(`cycling_offsets`, `energy_consumption_offsets`,
`energy_consumption_sensors`, siehe [modbus_wp_config.yaml](modbus-wp-config.md))
und wird beim ersten Start komplett auskommentiert aus einem festen Template
angelegt (`config_file.py::TEMPLATE`). Ein fehlerhafter Abschnitt wird beim
Einlesen übersprungen und gemeldet (`_salvage`), statt automatisch repariert
zu werden — es gibt nichts mehr zu migrieren, weil das Dateiformat sich seit
3.5.0 nicht mehr geändert hat.

## Entity-Duplikate

Die frühere `async_remove_duplicate_entity_suffixes()`-Bereinigung
(`migration.py`) ist ebenfalls entfallen — nicht weil die Migration sie nicht
mehr ausführt, sondern weil die Ursache dafür behoben wurde. Details:
[Entity-Duplikate (_2, _3) – Cleanup](entity-duplikat-cleanup.md).
