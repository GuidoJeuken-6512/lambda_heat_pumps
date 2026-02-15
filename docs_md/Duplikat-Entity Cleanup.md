# Plan: Duplikat-Entity Cleanup – Vollständige Überholung

## TL;DR
Die `async_remove_duplicate_entity_suffixes`-Funktion in `custom_components/lambda_heat_pumps/migration.py` (Zeile 435) hat mehrere Probleme: 
1. Async-Operationen werden möglicherweise nicht korrekt erwartet
2. Ineffiziente zwei-Loop-Struktur bei großen Registries
3. Redundante Fehlerbehandlung
4. Schwache Validierung von Duplikaten

Der Plan verfolgt eine **komplette Neuimplementierung** mit stärkerer Duplikatverfolgung, optimierter Performance und robusterem Error-Handling – plus Integration-Tests zur Verifizierung.

---

## Schritt 1: Async-Verhalten klären

**Ziel:** Entscheiden, ob `await` notwendig ist für `async_remove()` und `states.async_remove()`

**Aufgaben:**
- [ ] Recherchiere Home Assistant `async_remove()`-Methode: ist sie blockierend oder nicht?
- [ ] Prüfe [__init__.py] Zeile 258 zur Aufrufstelle – ob Fehlerbehandlung vorhanden ist
- [ ] Teste mit lokalem Home Assistant: Laufen die Removes synchron oder asynchron?
- [ ] Entscheide: Brauchen wir `await` oder kann der Current-Code funktionieren?

**Output:** 
- Dokumentation im Code
- Entscheidung für Implementierung (mit Begründung)
- Ggf. Änderung der async-Signatur

---

## Schritt 2: Neue Helper-Funktionen

**Ziel:** Schreibe drei robuste Helper-Funktionen mit besserer Trennung und Type-Safety

### 2.1 `_extract_duplicate_suffix(entity_id: str) -> str | None`

**Funktion:** Extrahiert das Suffix (`_2`, `_3` etc.) statt nur zu prüfen

**Eigenschaften:**
- Returns `None` wenn kein Duplikat erkannt
- Returns den Suffix-String wenn vorhanden (z.B. `"_2"`)
- Ermöglicht Meta-Information über die Duplikat-Nummer

**Beispiele:**
```python
_extract_duplicate_suffix("sensor.xyz_2")      # "_2"
_extract_duplicate_suffix("climate.abc_3")     # "_3"
_extract_duplicate_suffix("number.test_10")    # "_10"
_extract_duplicate_suffix("sensor.xyz")        # None
```

### 2.2 `_entity_belongs_to_our_domain(registry_entry: RegistryEntry) -> bool`

**Funktion:** Verbesserte Version von `_is_our_platform()`

**Verbesserungen vs. Original:**
- Type-Hints: `registry_entry: RegistryEntry` statt `Any`
- Explizite Domain-Checks (nicht nur Platform)
- Logging bei Unsicherheitsfällen (Debug-Level)
- Behandlung mehrerer Platform-Formate robust

**Checks:**
- Platform-String: `startswith(DOMAIN + ".)"` oder `== DOMAIN`
- Platform-Tuple: `platform[0] == DOMAIN`
- Domain-Attribut fallback
- Null-Handling mit Defaults

### 2.3 `_get_all_our_integration_entries(entity_registry) -> List[RegistryEntry]`

**Funktion:** Alle Registry-Entries unserer Integration effizienter abrufen

**Logik:**
```python
def _get_all_our_integration_entries(entity_registry) -> List[RegistryEntry]:
    """
    Sammelt alle Entries unserer Integration aus der Registry.
    
    Versucht verschiedene Zugriffsmuster (neu → alt):
    1. entity_registry.entities.values() mit Filter
    2. Fallback: manuelles Durchsuchen mit getattr()
    
    Returns: Liste von RegistryEntry-Objekten
    """
```

**Fehlertoleranz:**
- `hasattr()` Checks für verschiedene HA-Versionen
- Graceful-Degradation bei fehlender API

---

## Schritt 3: Hauptfunktion Neuschreiben

**Ziel:** Ersetze `async_remove_duplicate_entity_suffixes()` mit neuer, eleganterer Implementierung

### Neue Struktur (vereinigt beide Loops)

```
1. Alle Registry-Entries unserer Integration sammeln (eine Liste)
2. Filtern nach Lösch-Kriterien:
   - Hat Duplikat-Suffix? → Entry zum Löschen markieren
   - config_entry_id ist die aktuelle entry_id ODER ist null/gelöscht? → Markieren
3. Duplikate sammeln mit Metadata (entity_id, suffix, grund, config_entry_id)
4. Batch-Löschen mit robusten Exception-Handling pro Entity
5. Statistiken zusammenstellen + detailliertes Logging
```

### Verbesserungen vs. Original

| Bereich | Original | Neu |
|---------|----------|-----|
| **Duplikat-Erkennung** | Nur Suffix-Check | Suffix-Extraktion + Metadata |
| **Loop-Struktur** | 2 getrennte Loops | 1 gefilterte Loop |
| **Async-Handling** | Unklar | Explizit mit/ohne `await` |
| **Error-Handling** | Generisches `Exception` | Spezifische Exceptions (NotFound, PermissionDenied, etc.) |
| **Logging** | Info/Warning | Info/Debug/Warning mit Kontext |
| **Rückgabe** | `int` (removed count) | Dict: `{"removed": int, "failed": int, "skipped": int}` |

### Neue Signatur

```python
async def async_remove_duplicate_entity_suffixes(
    hass: HomeAssistant, 
    entry_id: str
) -> Dict[str, int]:
    """
    Entfernt Entities mit Duplikat-Suffixen (_2, _3, …).
    
    Args:
        hass: Home Assistant Instanz
        entry_id: Config-Entry-ID
    
    Returns:
        Dict mit Statistiken:
        {
            "removed": int,      # Erfolgreich gelöschte Entities
            "failed": int,       # Fehlerhafte Löschvorgänge
            "skipped": int,      # Übersprungene (nicht gehörend, etc.)
        }
    """
```

### Pseudo-Code der Implementierung

```python
async def async_remove_duplicate_entity_suffixes(hass, entry_id) -> dict:
    stats = {"removed": 0, "failed": 0, "skipped": 0}
    
    try:
        entity_registry = async_get_entity_registry(hass)
        current_entry_ids = {e.entry_id for e in hass.config_entries.async_entries(DOMAIN)}
        
        # Kandidaten sammeln
        candidates = []
        for entry in _get_all_our_integration_entries(entity_registry):
            suffix = _extract_duplicate_suffix(entry.entity_id)
            if not suffix:
                stats["skipped"] += 1  # Kein Duplikat-Suffix
                continue
            
            if not _entity_belongs_to_our_domain(entry):
                stats["skipped"] += 1  # Nicht unsere Integration
                continue
            
            # Sollte gelöscht werden?
            if entry.config_entry_id == entry_id or entry.config_entry_id not in current_entry_ids:
                candidates.append({
                    "entity_id": entry.entity_id,
                    "unique_id": entry.unique_id,
                    "config_entry_id": entry.config_entry_id,
                    "suffix": suffix,
                    "reason": "aktueller_eintrag" if entry.config_entry_id == entry_id else "verwaister_eintrag"
                })
        
        # Duplikate löschen
        for candidate in candidates:
            try:
                await _safe_remove_entity(hass, entity_registry, candidate)
                stats["removed"] += 1
                _LOGGER.info(f"Cleanup: Entity gelöscht: {candidate['entity_id']} (Grund: {candidate['reason']})")
            except Exception as e:
                stats["failed"] += 1
                _LOGGER.warning(f"Cleanup: Entity {candidate['entity_id']} konnte nicht gelöscht werden: {e}")
        
        # Zusammenfassung
        _log_cleanup_summary(stats, entry_id)
        
    except Exception as e:
        _LOGGER.error(f"Cleanup Duplikat-Entities für Entry {entry_id} fehlgeschlagen: {e}")
    
    return stats
```

---

## Schritt 4: Robustheit & Edge Cases

**Ziel:** Behandle folgende Fälle explizit und sicher

### 4.1 Async-Operationen

- [ ] Teste: Ist `async_remove()` blockierend oder nicht?
- [ ] Implementiere mit/ohne `await` je nach Befund
- [ ] Fallback: Wenn `await`-Fehler auftritt, nutze `ensure_future()` + Callback

### 4.2 Registry-Mutation während Loop

- [ ] Snapshot vor Loop erstellen statt während des Loops zu mutieren
- [ ] Puffer alle Lösch-Kandidaten, DANN löschen

### 4.3 Exception-Spezifisierung

Fange nicht einfach `Exception`, sondern:
- `RegistryEntryNotFound`: Entity existiert bereits nicht mehr
- `PermissionDenied`: Keine Berechtigung
- `ValueError`: Ungültige entity_id Format
- Fallback: Générique `Exception` mit Logging

### 4.4 Validierung vor Deletion

- [ ] Prüfe entity_id Format vor `async_remove()`
- [ ] Validiere dass entity_id zu unserer Integration gehört (nochmal)
- [ ] Prüfe ob config_entry_id logisch konsistent ist

### 4.5 Null/None Werte

- [ ] Alle Zugriffe mit Type-Safe defaults
- [ ] `entity_id is None` → überspringe mit Warnung
- [ ] `config_entry_id is None` → markiere als verwaist

---

## Schritt 5: Validierung & Testing (Manuell)

**Ziel:** Verifiziere korrekte Funktion durch manuelle Tests

### Validierungs-Checkliste

- [ ] **Setup mit Duplikaten:** Starte Integration mit existierenden Duplikat-Entities (z.B. `sensor.lambda_wp_xyz_2`) → Cleanup sollte sie entfernen
- [ ] **Reload ohne neue Duplikate:** Reload die Integration → keine neuen Duplikat-Suffixe entstehen
- [ ] **Falsche Entities nicht gelöscht:** Entities ohne Suffix bleiben (z.B. `sensor.lambda_wp_xyz`)
- [ ] **Korrekte Logs:** Logs geben klare Auskunft über gelöschte/übersprungene Entities
- [ ] **Performance:** Setup-Zeit ist akzeptabel (auch mit 100+ Entities)
- [ ] **Verwaiste Duplikate:** Wenn alte Config-Entry-ID gelöscht wurde, werden ihre Duplikate trotzdem entfernt

### Performance-Benchmark

- [ ] Messe Setup-Zeit mit Registry-Snapshots vor/nach
- [ ] Log die Dauer der Cleanup-Operation
- [ ] Verifiziere dass Cleanup nicht mehr als 500ms dauert

---

## Schritt 6: Dokumentation aktualisieren

**Ziel:** Code-Dokumentation und externe Doku synchronisieren

### 6.1 migration.py

- [ ] Kommentare für Helper-Funktionen aktualisieren
- [ ] Pseudo-Code-Kommentare für Hauptlogik hinzufügen
- [ ] Inline-Erklärung: Warum `await` / warum nicht

### 6.2 entity-duplikat-cleanup.md

- [ ] Code-Referenzen auf neue Funktionen aktualisieren
- [ ] Neue Ablauf-Beschreibung mit 1-Loop-Struktur erklären
- [ ] Log-Beispiele zeigen (vorher/nachher)
- [ ] Return-Value Änderung dokumentieren (int → dict)

### 6.3 Migrations-Architektur

- [ ] Falls separate Migrations-Doku existiert: Duplikat-Cleanup dort erwähnen
- [ ] Wichtigkeit von `entry_id` Eindeutigkeit erklären

---

## Entscheidungen & Begründung

### Warum Async-Klärung zuerst?
Ohne korrekte Async-Handhabung kann keine zuverlässige Lösung entstehen. Das ist die Grundvoraussetzung.

### Warum vollständige Neurealisierung statt Patch?
- Die zwei-Loop-Struktur ist semantisch suboptimal
- Ab Grund auf neu macht Code wartbarer und performant
- Einfacher, alle Edge-Cases auf einmal zu behandeln

### Warum keine automatisierten Tests?
- Fokus auf Robustheit & Logging statt Test-Coverage
- Manuelle Validierung reicht für diesen Use-Case
- Integration-Tests würden Mock-Home-Assistant erfordern (komplex)

### Warum Helper-Funktionen mit Type-Hints?
- Macht Fehlermöglichkeiten offensichtlich
- IDE-Autocompletion hilft bei Fehlersuche
- Lesbarkeit und Wartbarkeit verbessern sich

### Warum Dict-Return statt Int-Return?
- Gibt mehr Kontext über Cleanup-Ergebnis
- Ermöglicht besseres Logging und Debugging
- Statistiken können später in Dashboard angezeigt werden (optional)

---

## Priorität & Abhängigkeiten

```
Phase 1 (Voraussetzung):
  └─ Schritt 1: Async-Verhalten klären
     └─ Entscheidung: Mit/ohne `await`

Phase 2 (Implementierung):
  ├─ Schritt 2: Helper-Funktionen schreiben
  ├─ Schritt 3: Hauptfunktion neuschreiben (benötigt Schritt 2)
  └─ Schritt 4: Edge-Cases behandeln (benötigt Schritt 3)

Phase 3 (Verifizierung & Doku):
  ├─ Schritt 5: Manuelle Validierung
  └─ Schritt 6: Dokumentation aktualisieren
```

---

## Erfolgskriterien

- ✅ Alle Duplikat-Entities werden erkannt und gelöscht
- ✅ Nicht-Duplikat-Entities bleiben unberührt
- ✅ Setup-Performance bleibt < 1 Sekunde (auch mit vielen Entities)
- ✅ Fehlerhafte Löschvorgänge werden geloggt und stoppen nicht den gesamten Cleanup
- ✅ Code ist lesbar und wartbar (Type-Hints, Kommentare, klare Struktur)
- ✅ Dokumentation ist aktuell und präzise
