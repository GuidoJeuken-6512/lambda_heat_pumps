---
title: "Entity-Duplikate (_2, _3) – Cleanup"
---

# Entity-Duplikate (_2, _3) – Cleanup

Diese Seite beschreibt, wie die Integration doppelt angelegte Entities (z. B. `sensor.xyz_2`, `climate.xyz_3`) erkennt und bereinigt – ohne die Namenslogik oder bestehende Entity-IDs zu ändern (kein Verlust historischer Daten).

## Hintergrund

### Wann entstehen Duplikate mit _2, _3?

Home Assistant vergibt das Suffix `_2`, `_3`, … wenn eine neue Entity mit derselben vorgeschlagenen `entity_id` registriert wird wie eine bereits existierende. Typische Ursachen in dieser Integration:

1. **Verwaiste Einträge in der Entity Registry**  
   Die Integration wurde entfernt und mit demselben Namen wieder hinzugefügt. Alte Entities können in der Registry verbleiben; beim erneuten Setup können dann Duplikat-Suffixe entstehen.

2. **Updates / Reloads**  
   Nach einem Update oder Reload können unter bestimmten Bedingungen Duplikate in der Registry stehen.

### Eindeutigkeit des Namens

Im Config Flow ist der **Name** pro Eintrag eindeutig: `name_already_exists` und `connection_already_exists` verhindern doppelte Einträge. Der **name_prefix** (Name, kleingeschrieben, ohne Leerzeichen) fließt in `generate_sensor_names` ein und damit in `entity_id` und `unique_id`. Eine zusätzliche Einbeziehung von `entry_id` in die unique_id ist **nicht** vorgesehen, um keinen Verlust historischer Daten zu riskieren.

## Cleanup-Logik

### Wann wird bereinigt?

Der Cleanup läuft bei **jedem** Aufruf von `async_setup_entry` der Integration – also:

- beim ersten Anlegen der Integration,
- beim **Reload** der Integration,
- bei jedem **Restart** von Home Assistant.

Damit werden auch beim Update entstandene Duplikate beim nächsten Reload oder Neustart automatisch bereinigt.

### Wo wird bereinigt?

- **Ort:** `__init__.py` – direkt nach dem Setzen von `hass.data[DOMAIN][entry.entry_id]` und **vor** `async_forward_entry_setups`. So sind Duplikate bereits entfernt, bevor die Plattformen (Sensor, Climate, Number) ihre Entities anmelden.
- **Implementierung:** `migration.py` – Funktion `async_remove_duplicate_entity_suffixes(hass, entry_id)`.

### Ablauf

1. Entity Registry laden.
2. Alle Einträge für die aktuelle `config_entry_id` holen (`get_entries_for_config_entry_id`).
3. Für jede Entity prüfen, ob die `entity_id` mit dem Muster `_\d+` endet (z. B. `_2`, `_3`, `_10`).
4. Diese Duplikat-Entities mit `entity_registry.async_remove(entity_id)` entfernen.
5. Es werden **nur** Entities dieses Config-Eintrags entfernt; andere Einträge bleiben unberührt.

### Code-Referenz

```python
# migration.py
_ENTITY_ID_DUPLICATE_SUFFIX_RE = re.compile(r"_\d+$")

async def async_remove_duplicate_entity_suffixes(
    hass: HomeAssistant, entry_id: str
) -> int:
    """Entfernt Entities dieser Integration, deren entity_id mit _2, _3, … endet."""
    # ... siehe migration.py
```

Aufruf in `__init__.py`:

```python
# Duplikat-Entities (_2, _3, …) aus der Registry entfernen (bei jedem Setup/Reload/Restart)
await async_remove_duplicate_entity_suffixes(hass, entry.entry_id)
```

## Vorgabe: Kein Verlust historischer Daten

**unique_id** und **entity_id** (Namensschema) werden **nicht** geändert. Maßnahmen beschränken sich auf das Entfernen von Duplikat-Entities aus der Registry. Die „Haupt“-Entity (ohne Suffix) bleibt unverändert; ihre Historie/Statistiken bleiben erhalten.

## Logging

- Bei jeder entfernten Entity: `Cleanup: Duplikat-Entity entfernt (Suffix _2/_3/…): <entity_id>`
- Am Ende, falls mindestens eine entfernt wurde: `Cleanup: N Duplikat-Entity/Entities für Entry <entry_id> entfernt.`
- Fehler beim Entfernen einer einzelnen Entity werden als Warning geloggt; ein Fehler der gesamten Cleanup-Funktion führt nicht zum Abbruch des Setups.
