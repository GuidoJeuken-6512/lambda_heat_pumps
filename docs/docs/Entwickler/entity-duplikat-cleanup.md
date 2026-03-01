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

1. **Sammelphase:** Entity Registry laden und alle Kandidaten ermitteln (ohne die Registry während der Iteration zu verändern):
   - Einträge für die aktuelle `config_entry_id` (`get_entries_for_config_entry_id(entry_id)`), deren `entity_id` mit `_\d+` endet (z. B. `_2`, `_3`) → Grund „aktueller Eintrag“.
   - Verwaiste Duplikate: alle Entities unserer Platform mit Duplikat-Suffix, deren `config_entry_id` nicht mehr zu einer bestehenden Config-Entry gehört → Grund „verwaist“.
2. **Löschphase:** Für jeden gesammelten Kandidaten nacheinander `entity_registry.async_remove(entity_id)` und `hass.states.async_remove(entity_id)` aufrufen. Es werden nur die in der Sammelphase ermittelten Duplikat-Entities entfernt; die „Haupt“-Entity (ohne Suffix) und andere Einträge bleiben unberührt.

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

- Bei jeder entfernten Entity: `Cleanup: Duplikat entfernt: <entity_id> (reason: aktueller_eintrag|verwaist)`.
- Am Ende: `Cleanup abgeschlossen: N Duplikat(e) entfernt, M Fehler für Entry <entry_id>` (falls mindestens ein Entfernen oder ein Fehler); sonst bei keinem Fund: `Cleanup: Keine Duplikat-Entities (_2, _3, …) für Entry <entry_id> gefunden.`
- Fehler beim Entfernen einer einzelnen Entity werden als Warning geloggt (`Entity … konnte nicht entfernt werden (reason: …)`); ein Fehler der gesamten Cleanup-Funktion führt nicht zum Abbruch des Setups.

## Prüfliste: Log und Entity Registry

### Im Log prüfen (nach Reload/Neustart der Integration)

1. **Start des Cleanups:** Es erscheint `Cleanup: Prüfe auf Duplikat-Entities (_2, _3, …) für Entry <entry_id> …`.
2. **Pro entfernte Entity:** `Cleanup: Duplikat entfernt: <entity_id> (reason: aktueller_eintrag|verwaist)`.
3. **Am Ende:** Entweder `Cleanup abgeschlossen: N Duplikat(e) entfernt, M Fehler …` oder `Cleanup: Keine Duplikat-Entities … gefunden.`
4. Bei Fehlern: `Cleanup: Entity … konnte nicht entfernt werden (reason: …)`.

### Entity Registry prüfen

- **Einstellungen → Geräte & Dienste → Entitäten** (oder Developer Tools → States): Nach `_2`, `_3` usw. in der Entity-ID suchen (z. B. Filter „lambda“ oder „eu08l“).
- Erwartung: Nach einem erfolgreichen Cleanup und Reload sollten **keine** Entities mehr existieren, deren Entity-ID mit `_2`, `_3`, … endet (z. B. `sensor.eu08l_hp1_compressor_start_cycling_2h_3`).

### Wenn Duplikate trotz Log-Meldung „Duplikat entfernt“ noch sichtbar sind

- **Reload der Integration** auslösen (Einstellungen → Integrationen → Lambda Heat Pumps → Drei Punkte → Neu laden); die Registry wird beim Setup aktualisiert, die UI kann mit Verzögerung aktualisieren.
- **Browser-Cache / UI:** Seite hart aktualisieren (Strg+F5) oder App neu öffnen.
- **Mehrere Config-Einträge:** Der Cleanup läuft pro Config-Entry. Bei mehreren Lambda-Integrationen (z. B. zwei Wärmepumpen mit zwei Einträgen) wird für jeden Eintrag einmal bereinigt; verwaiste Duplikate ohne gültigen `config_entry_id` werden im zweiten Durchlauf („verwaist“) erfasst.
