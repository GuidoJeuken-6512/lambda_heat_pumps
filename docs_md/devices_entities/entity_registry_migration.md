# Entity Registry Migration und Updates in Integrationen

## Inhaltsverzeichnis

- [Übersicht](#übersicht)
- [Wichtige Grundsätze](#wichtige-grundsätze)
  - [Historische Daten schützen](#historische-daten-schützen)
  - [Registry-Integrität wahren](#registry-integrität-wahren)
- [Verfügbare Migrationsfunktionen](#verfügbare-migrationsfunktionen)
  - [async_update_entity() - Allgemeine Entitätsaktualisierung](#1-async_update_entity---allgemeine-entitätsaktualisierung)
  - [async_update_entity_platform() - Plattform-Migration](#2-async_update_entity_platform---plattform-migration)
  - [async_update_entity_options() - Entitätsoptionen aktualisieren](#3-async_update_entity_options---entitätsoptionen-aktualisieren)
  - [async_migrate_entries() - Batch-Migration](#4-async_migrate_entries---batch-migration)
  - [async_remove() - Entität sicher entfernen](#5-async_remove---entität-sicher-entfernen)
  - [async_clear_* Funktionen - Batch-Bereinigung](#6-async_clear--funktionen---batch-bereinigung)
  - [async_purge_expired_orphaned_entities() - Bereinigung verwaister Entitäten](#7-async_purge_expired_orphaned_entities---bereinigung-verwaister-entitäten)
- [Entitätserstellung und Migration in Integrationen](#entitätserstellung-und-migration-in-integrationen)
  - [Automatische Entitätserstellung](#1-automatische-entitätserstellung)
  - [Entitätsmigration bei Updates](#2-entitätsmigration-bei-updates)
  - [Manuelle Entitätsverwaltung](#3-manuelle-entitätsverwaltung)
  - [Entitätsverknüpfungen](#4-entitätsverknüpfungen)
- [Praktische Migrationsszenarien](#praktische-migrationsszenarien)
  - [Szenario 1: Integration von v1.0 auf v2.0 aktualisieren](#szenario-1-integration-von-v10-auf-v20-aktualisieren)
  - [Szenario 2: Entitäten zwischen Bereichen neu zuordnen](#szenario-2-entitäten-zwischen-bereichen-neu-zuordnen)
  - [Szenario 3: Entitätsnamen standardisieren](#szenario-3-entitätsnamen-standardisieren)
  - [Szenario 4: Integration komplett neu strukturieren](#szenario-4-integration-komplett-neu-strukturieren)
  - [Szenario 5: Entitäten zwischen Geräten neu zuordnen](#szenario-5-entitäten-zwischen-geräten-neu-zuordnen)
  - [Szenario 6: Labels und Kategorien massenweise aktualisieren](#szenario-6-labels-und-kategorien-massenweise-aktualisieren)
- [Sicherheitsaspekte und Best Practices](#sicherheitsaspekte-und-best-practices)
  - [Backup vor Migrationen](#1-backup-vor-migrationen)
  - [Validierung vor Anwendung](#2-validierung-vor-anwendung)
  - [Rollback-Funktionalität](#3-rollback-funktionalität)
  - [Wiederherstellung aus deleted_entities](#4-wiederherstellung-aus-deleted_entities)
  - [Analyse der deleted_entities](#5-analyse-der-deleted_entities)
- [Erweiterte Entitätssuche und -filterung](#erweiterte-entitätssuche-und--filterung)
  - [Entitäten nach verschiedenen Kriterien finden](#1-entitäten-nach-verschiedenen-kriterien-finden)
  - [Intelligente Entitätsfilterung](#2-intelligente-entitätsfilterung)
- [Monitoring und Debugging](#monitoring-und-debugging)
  - [Migration-Logs](#1-migration-logs)
  - [Entitätsstatus überprüfen](#2-entitätsstatus-überprüfen)
- [Fazit](#fazit)
- [Weitere Ressourcen](#weitere-ressourcen)

---

## Übersicht

Diese Dokumentation beschreibt die verschiedenen Möglichkeiten, Entitäten in Home Assistant Integrationen zu migrieren, zu aktualisieren und zu verwalten. Besonderer Fokus liegt auf der Erhaltung historischer Daten und der korrekten Durchführung von Major Updates.

## Wichtige Grundsätze

### **Historische Daten schützen**
- **Entity ID niemals ändern**: Die `entity_id` ist der Primärschlüssel für alle historischen Daten
- **unique_id Migration**: Verwenden Sie `previous_unique_id` für Änderungen der unique_id
- **Schrittweise Updates**: Führen Sie komplexe Migrationen in mehreren Schritten durch

### **Registry-Integrität wahren**
- **Validierung**: Überprüfen Sie alle Änderungen vor der Anwendung
- **Rollback-Möglichkeit**: Behalten Sie Backup-Daten für den Notfall
- **Event-basierte Updates**: Nutzen Sie die Home Assistant Event-Systeme

## Verfügbare Migrationsfunktionen

### 1. **async_update_entity() - Allgemeine Entitätsaktualisierung**

Die Hauptfunktion für alle Arten von Entitätsaktualisierungen.

```python
from homeassistant.helpers.entity_registry import async_get

async def update_entity_basic(hass):
    """Grundlegende Entitätsaktualisierung."""
    registry = async_get(hass)
    
    # Einzelne Felder aktualisieren
    registry.async_update_entity(
        entity_id="sensor.example",
        name="Neuer Name",
        icon="mdi:new-icon",
        entity_category="diagnostic"
    )
```

**Verfügbare Parameter:**
- `name`: Benutzerfreundlicher Name
- `icon`: Icon der Entität
- `entity_category`: Kategorie (primary, secondary, config, diagnostic)
- `device_class`: Geräteklasse
- `unit_of_measurement`: Maßeinheit
- `supported_features`: Unterstützte Features
- `capabilities`: Verfügbare Funktionen
- `area_id`: Bereichszuordnung
- `labels`: Benutzerdefinierte Labels

### 2. **async_update_entity_platform() - Plattform-Migration**

**WICHTIG**: Nur für Entitäten verwenden, die noch nicht geladen wurden!

```python
async def migrate_entity_platform(hass, old_entity_id, new_platform):
    """Entität zwischen Integrationen migrieren."""
    registry = async_get(hass)
    
    # Prüfen, ob Entität bereits geladen ist
    state = hass.states.get(old_entity_id)
    if state is not None and state.state != "unavailable":
        raise ValueError("Entität ist bereits geladen und kann nicht migriert werden")
    
    # Plattform ändern
    registry.async_update_entity_platform(
        entity_id=old_entity_id,
        new_platform=new_platform,
        new_config_entry_id="new_config_entry_id",
        new_unique_id="new_unique_id"
    )
```

**Einschränkungen:**
- Entität darf nicht bereits geladen sein
- `new_config_entry_id` ist erforderlich, wenn die alte Entität bereits verknüpft war
- Nur für echte Integration-Migrationen verwenden

### 3. **async_update_entity_options() - Entitätsoptionen aktualisieren**

Aktualisiert domänenspezifische Optionen einer Entität.

```python
async def update_entity_options(hass, entity_id, domain, options):
    """Entitätsoptionen aktualisieren."""
    registry = async_get(hass)
    
    # Neue Optionen setzen
    registry.async_update_entity_options(
        entity_id=entity_id,
        domain=domain,
        options={
            "custom_option": "value",
            "another_option": 42
        }
    )
    
    # Optionen entfernen
    registry.async_update_entity_options(
        entity_id=entity_id,
        domain=domain,
        options=None  # Entfernt alle Optionen für diese Domain
    )
```

### 4. **async_migrate_entries() - Batch-Migration**

Führt Migrationen für alle Entitäten einer Konfiguration durch.

### 5. **async_remove() - Entität sicher entfernen**

Entfernt eine Entität aus der Registry, behält aber alle historischen Daten in der Datenbank.

```python
async def remove_entity_safely(hass, entity_id):
    """Entität sicher entfernen ohne Datenverlust."""
    registry = async_get(hass)
    
    # Entität wird in deleted_entities gespeichert
    registry.async_remove(entity_id)
    
    # Historische Daten bleiben in der Datenbank erhalten
    # Nur der Registry-Eintrag wird entfernt
```

**Wichtige Eigenschaften:**
- **Kein Datenverlust**: Historische Daten bleiben in der Datenbank
- **Deleted Entities**: Entität wird in `deleted_entities` gespeichert
- **Orphaned Timestamp**: Zeitstempel wird gesetzt für spätere Bereinigung
- **Event-basiert**: `EVENT_ENTITY_REGISTRY_UPDATED` wird ausgelöst

### 6. **async_clear_* Funktionen - Batch-Bereinigung**

Entfernt spezifische Verknüpfungen von mehreren Entitäten gleichzeitig.

#### **async_clear_config_entry()**
```python
async def clear_integration_entities(hass, config_entry_id):
    """Alle Entitäten einer Integration entfernen."""
    registry = async_get(hass)
    
    # Entfernt alle Entitäten der Integration
    # Historische Daten bleiben erhalten
    registry.async_clear_config_entry(config_entry_id)
```

#### **async_clear_area_id()**
```python
async def clear_area_entities(hass, area_id):
    """Alle Entitäten eines Bereichs neu zuordnen."""
    registry = async_get(hass)
    
    # Entfernt area_id von allen Entitäten
    # Entitäten bleiben bestehen, nur Bereichszuordnung wird gelöscht
    registry.async_clear_area_id(area_id)
```

#### **async_clear_label_id()**
```python
async def clear_label_from_entities(hass, label_id):
    """Label von allen Entitäten entfernen."""
    registry = async_get(hass)
    
    # Entfernt Label von allen betroffenen Entitäten
    # Entitäten bleiben bestehen, nur Label wird gelöscht
    registry.async_clear_label_id(label_id)
```

#### **async_clear_category_id()**
```python
async def clear_category_from_entities(hass, scope, category_id):
    """Kategorie von allen Entitäten entfernen."""
    registry = async_get(hass)
    
    # Entfernt Kategorie aus dem angegebenen Scope
    # Entitäten bleiben bestehen, nur Kategorie wird gelöscht
    registry.async_clear_category_id(scope, category_id)
```

### 7. **async_purge_expired_orphaned_entities() - Bereinigung verwaister Entitäten**

Bereinigt veraltete gelöschte Entitäten nach dem Ablauf der Aufbewahrungsfrist.

```python
async def cleanup_old_entities(hass):
    """Veraltete gelöschte Entitäten bereinigen."""
    registry = async_get(hass)
    
    # Entfernt Entitäten, die länger als ORPHANED_ENTITY_KEEP_SECONDS gelöscht sind
    # Standard: 30 Tage Aufbewahrung
    registry.async_purge_expired_orphaned_entities()
```

```python
async def migrate_all_entities(hass, config_entry_id):
    """Alle Entitäten einer Konfiguration migrieren."""
    from homeassistant.helpers.entity_registry import async_migrate_entries
    
    async def migration_callback(entry):
        """Migration für einzelne Entität."""
        updates = {}
        
        # unique_id aktualisieren
        if entry.unique_id.startswith("old_prefix_"):
            updates["new_unique_id"] = entry.unique_id.replace("old_prefix_", "new_prefix_")
            updates["previous_unique_id"] = entry.unique_id
        
        # Plattform aktualisieren
        if entry.platform == "old_platform":
            updates["platform"] = "new_platform"
        
        # Weitere Updates...
        if entry.name and "old_name" in entry.name:
            updates["name"] = entry.name.replace("old_name", "new_name")
        
        return updates if updates else None
    
    # Migration durchführen
    await async_migrate_entries(hass, config_entry_id, migration_callback)
```

## Praktische Migrationsszenarien

### **Szenario 1: Integration von v1.0 auf v2.0 aktualisieren**

```python
async def migrate_v1_to_v2(hass, config_entry_id):
    """Migration von Integration v1.0 auf v2.0."""
    registry = async_get(hass)
    
    async def v2_migration(entry):
        updates = {}
        
        # unique_id Format ändern (z.B. von "sensor_001" zu "sensor_v2_001")
        if not entry.unique_id.startswith("v2_"):
            updates["new_unique_id"] = f"v2_{entry.unique_id}"
            updates["previous_unique_id"] = entry.unique_id
        
        # Neue Attribute hinzufügen
        if not hasattr(entry, "capabilities") or entry.capabilities is None:
            updates["capabilities"] = {
                "min": 0,
                "max": 100,
                "step": 1
            }
        
        # Plattform aktualisieren
        if entry.platform == "old_integration":
            updates["platform"] = "new_integration"
        
        return updates if updates else None
    
    await async_migrate_entries(hass, config_entry_id, v2_migration)
```

### **Szenario 2: Entitäten zwischen Bereichen neu zuordnen**

```python
async def reorganize_entities_by_area(hass):
    """Entitäten nach neuen Bereichen neu organisieren."""
    registry = async_get(hass)
    
    # Mapping von alten zu neuen Bereichen
    area_mapping = {
        "old_living_room": "living_room",
        "old_kitchen": "kitchen",
        "old_bedroom": "master_bedroom"
    }
    
    for entry in registry.entities.values():
        if entry.area_id in area_mapping:
            registry.async_update_entity(
                entity_id=entry.entity_id,
                area_id=area_mapping[entry.area_id]
            )
```

### **Szenario 3: Entitätsnamen standardisieren**

```python
async def standardize_entity_names(hass, config_entry_id):
    """Entitätsnamen nach neuen Standards formatieren."""
    
    async def name_standardization(entry):
        if not entry.name:
            return None
        
        new_name = entry.name
        
        # Deutsche Umlaute korrigieren
        new_name = new_name.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
        
        # Einheiten standardisieren
        new_name = new_name.replace("Grad", "°C").replace("Prozent", "%")
        
        # Nur aktualisieren, wenn sich etwas geändert hat
        if new_name != entry.name:
            return {"name": new_name}
        
        return None
    
    await async_migrate_entries(hass, config_entry_id, name_standardization)
```

### **Szenario 4: Integration komplett neu strukturieren**

```python
async def restructure_integration(hass, old_config_entry_id, new_config_entry_id):
    """Integration komplett neu strukturieren mit Datenverlustschutz."""
    
    # 1. Backup erstellen
    backup_file = await backup_entity_registry(hass)
    
    try:
        # 2. Alle Entitäten der alten Integration sammeln
        registry = async_get(hass)
        old_entities = list(registry.entities.get_entries_for_config_entry_id(old_config_entry_id))
        
        # 3. Neue Entitäten mit gleichen entity_ids erstellen
        for old_entity in old_entities:
            # Neue Entität mit gleicher entity_id erstellen
            # Dadurch bleiben alle historischen Daten erhalten
            registry.async_update_entity(
                entity_id=old_entity.entity_id,
                platform="new_platform",
                config_entry_id=new_config_entry_id,
                new_unique_id=f"new_{old_entity.unique_id}",
                previous_unique_id=old_entity.unique_id
            )
        
        # 4. Alte Konfiguration entfernen
        registry.async_clear_config_entry(old_config_entry_id)
        
        _LOGGER.info(f"Integration erfolgreich von {old_config_entry_id} zu {new_config_entry_id} migriert")
        
    except Exception as e:
        # 5. Rollback bei Fehlern
        _LOGGER.error(f"Migration fehlgeschlagen: {str(e)}")
        await rollback_migration(hass, backup_file)
        raise
```

### **Szenario 5: Entitäten zwischen Geräten neu zuordnen**

```python
async def reassign_entities_to_devices(hass, device_mapping):
    """Entitäten zwischen Geräten neu zuordnen."""
    registry = async_get(hass)
    
    for old_device_id, new_device_id in device_mapping.items():
        # Alle Entitäten des alten Geräts finden
        entities = async_entries_for_device(registry, old_device_id)
        
        for entity in entities:
            # Entität dem neuen Gerät zuordnen
            registry.async_update_entity(
                entity_id=entity.entity_id,
                device_id=new_device_id
            )
            
            _LOGGER.info(f"Entität {entity.entity_id} von Gerät {old_device_id} zu {new_device_id} zugeordnet")
```

### **Szenario 6: Labels und Kategorien massenweise aktualisieren**

```python
async def bulk_update_labels_and_categories(hass, config_entry_id):
    """Labels und Kategorien für alle Entitäten einer Integration aktualisieren."""
    
    async def label_category_update(entry):
        updates = {}
        
        # Neue Labels hinzufügen
        new_labels = entry.labels.copy()
        new_labels.add("migrated_v2")
        new_labels.add("automated")
        updates["labels"] = new_labels
        
        # Neue Kategorien setzen
        new_categories = entry.categories.copy()
        new_categories["energy"] = "power_consumption"
        new_categories["comfort"] = "temperature_control"
        updates["categories"] = new_categories
        
        return updates
    
    await async_migrate_entries(hass, config_entry_id, label_category_update)
```

## Sicherheitsaspekte und Best Practices

### **1. Backup vor Migrationen**
```python
async def backup_entity_registry(hass):
    """Entity Registry vor Migration sichern."""
    registry = async_get(hass)
    
    backup_data = {
        "timestamp": datetime.now().isoformat(),
        "entities": []
    }
    
    for entry in registry.entities.values():
        backup_data["entities"].append({
            "entity_id": entry.entity_id,
            "unique_id": entry.unique_id,
            "name": entry.name,
            "platform": entry.platform,
            "config_entry_id": entry.config_entry_id,
            "device_id": entry.device_id,
            "area_id": entry.area_id
        })
    
    # Backup in Datei speichern
    backup_file = f"/config/entity_registry_backup_{int(time.time())}.json"
    with open(backup_file, 'w') as f:
        json.dump(backup_data, f, indent=2)
    
    return backup_file
```

### **2. Validierung vor Anwendung**
```python
async def validate_migration(hass, config_entry_id, migration_callback):
    """Migration vor der Anwendung validieren."""
    registry = async_get(hass)
    validation_errors = []
    
    for entry in registry.entities.get_entries_for_config_entry_id(config_entry_id):
        try:
            updates = migration_callback(entry)
            if updates:
                # Prüfen, ob die Änderungen gültig sind
                if "new_unique_id" in updates:
                    # Prüfen, ob neue unique_id bereits existiert
                    existing = registry.entities.get_entry_by_unique_id(
                        config_entry_id, updates["new_unique_id"]
                    )
                    if existing and existing.entity_id != entry.entity_id:
                        validation_errors.append(
                            f"unique_id {updates['new_unique_id']} existiert bereits"
                        )
        except Exception as e:
            validation_errors.append(f"Fehler bei {entry.entity_id}: {str(e)}")
    
    if validation_errors:
        raise ValueError(f"Validierungsfehler: {validation_errors}")
    
    return True
```

### **3. Rollback-Funktionalität**
```python
async def rollback_migration(hass, backup_file):
    """Migration bei Problemen rückgängig machen."""
    with open(backup_file, 'r') as f:
        backup_data = json.load(f)
    
    registry = async_get(hass)
    
    for entity_data in backup_data["entities"]:
        entity_id = entity_data["entity_id"]
        if entity_id in registry.entities:
            registry.async_update_entity(
                entity_id=entity_id,
                unique_id=entity_data["unique_id"],
                name=entity_data["name"],
                platform=entity_data["platform"],
                config_entry_id=entity_data["config_entry_id"],
                device_id=entity_data["device_id"],
                area_id=entity_data["area_id"]
            )
```

### **4. Wiederherstellung aus deleted_entities**
```python
async def restore_deleted_entity(hass, entity_id, platform, unique_id):
    """Gelöschte Entität aus deleted_entities wiederherstellen."""
    registry = async_get(hass)
    
    # Gelöschte Entität finden
    for key, deleted_entity in registry.deleted_entities.items():
        if deleted_entity.entity_id == entity_id:
            # Entität wiederherstellen
            registry.async_update_entity(
                entity_id=entity_id,
                platform=platform,
                unique_id=unique_id,
                config_entry_id=deleted_entity.config_entry_id,
                device_id=deleted_entity.device_id,
                area_id=deleted_entity.area_id,
                name=deleted_entity.name,
                icon=deleted_entity.icon,
                entity_category=deleted_entity.entity_category,
                device_class=deleted_entity.device_class,
                supported_features=deleted_entity.supported_features,
                unit_of_measurement=deleted_entity.unit_of_measurement,
                capabilities=deleted_entity.capabilities,
                options=deleted_entity.options,
                labels=deleted_entity.labels,
                categories=deleted_entity.categories
            )
            
            # Aus deleted_entities entfernen
            registry.deleted_entities.pop(key)
            registry.async_schedule_save()
            
            _LOGGER.info(f"Entität {entity_id} erfolgreich wiederhergestellt")
            return True
    
    _LOGGER.warning(f"Entität {entity_id} nicht in deleted_entities gefunden")
    return False
```

### **5. Analyse der deleted_entities**
```python
async def analyze_deleted_entities(hass):
    """Analyse aller gelöschten Entitäten."""
    registry = async_get(hass)
    
    analysis = {
        "total_deleted": len(registry.deleted_entities),
        "by_platform": {},
        "by_config_entry": {},
        "orphaned_entities": [],
        "recently_deleted": []
    }
    
    now = time.time()
    orphaned_threshold = 24 * 60 * 60  # 24 Stunden
    
    for key, deleted_entity in registry.deleted_entities.items():
        # Nach Plattform gruppieren
        platform = deleted_entity.platform
        analysis["by_platform"][platform] = analysis["by_platform"].get(platform, 0) + 1
        
        # Nach Konfigurationseintrag gruppieren
        config_entry = deleted_entity.config_entry_id
        if config_entry:
            analysis["by_config_entry"][config_entry] = analysis["by_config_entry"].get(config_entry, 0) + 1
        else:
            analysis["orphaned_entities"].append({
                "entity_id": deleted_entity.entity_id,
                "platform": deleted_entity.platform,
                "deleted_at": deleted_entity.orphaned_timestamp
            })
        
        # Kürzlich gelöschte Entitäten
        if deleted_entity.orphaned_timestamp and (now - deleted_entity.orphaned_timestamp) < orphaned_threshold:
            analysis["recently_deleted"].append({
                "entity_id": deleted_entity.entity_id,
                "platform": deleted_entity.platform,
                "deleted_at": deleted_entity.orphaned_timestamp
            })
    
    return analysis
```

## Erweiterte Entitätssuche und -filterung

### **1. Entitäten nach verschiedenen Kriterien finden**

```python
from homeassistant.helpers.entity_registry import (
    async_get, async_entries_for_device, async_entries_for_area,
    async_entries_for_label, async_entries_for_category, async_entries_for_config_entry
)

async def find_entities_by_criteria(hass):
    """Entitäten nach verschiedenen Kriterien finden."""
    registry = async_get(hass)
    
    # Alle Entitäten einer Integration
    integration_entities = async_entries_for_config_entry(registry, "config_entry_id")
    
    # Alle Entitäten eines Geräts
    device_entities = async_entries_for_device(registry, "device_id")
    
    # Alle Entitäten eines Bereichs
    area_entities = async_entries_for_area(registry, "area_id")
    
    # Alle Entitäten mit einem bestimmten Label
    labeled_entities = async_entries_for_label(registry, "label_id")
    
    # Alle Entitäten einer bestimmten Kategorie
    category_entities = async_entries_for_category(registry, "scope", "category_id")
    
    return {
        "integration": len(integration_entities),
        "device": len(device_entities),
        "area": len(area_entities),
        "label": len(labeled_entities),
        "category": len(category_entities)
    }
```

### **2. Intelligente Entitätsfilterung**

```python
async def filter_entities_intelligently(hass, config_entry_id):
    """Intelligente Filterung von Entitäten für Migrationen."""
    registry = async_get(hass)
    
    # Alle Entitäten der Integration
    all_entities = async_entries_for_config_entry(registry, config_entry_id)
    
    # Nach verschiedenen Kriterien filtern
    entities_to_migrate = []
    entities_to_skip = []
    
    for entity in all_entities:
        # Entitäten mit bestimmten Eigenschaften migrieren
        if (entity.entity_category == "diagnostic" or 
            entity.platform == "old_platform" or
            entity.unique_id.startswith("deprecated_")):
            
            entities_to_migrate.append(entity)
        else:
            entities_to_skip.append(entity)
    
    return {
        "to_migrate": entities_to_migrate,
        "to_skip": entities_to_skip,
        "total": len(all_entities)
    }
```

## Monitoring und Debugging

### **1. Migration-Logs**
```python
import logging

_LOGGER = logging.getLogger(__name__)

async def log_migration_progress(hass, config_entry_id, migration_callback):
    """Migration mit detailliertem Logging durchführen."""
    registry = async_get(hass)
    total_entities = len(list(registry.entities.get_entries_for_config_entry_id(config_entry_id)))
    processed = 0
    errors = 0
    
    _LOGGER.info(f"Starte Migration für {total_entities} Entitäten")
    
    async def logged_migration(entry):
        nonlocal processed, errors
        
        try:
            updates = migration_callback(entry)
            if updates:
                _LOGGER.info(f"Migriere {entry.entity_id}: {updates}")
            processed += 1
            return updates
        except Exception as e:
            errors += 1
            _LOGGER.error(f"Fehler bei {entry.entity_id}: {str(e)}")
            return None
    
    await async_migrate_entries(hass, config_entry_id, logged_migration)
    
    _LOGGER.info(f"Migration abgeschlossen: {processed} verarbeitet, {errors} Fehler")
```

### **2. Entitätsstatus überprüfen**
```python
async def verify_migration_success(hass, config_entry_id):
    """Überprüfen, ob Migration erfolgreich war."""
    registry = async_get(hass)
    
    verification_results = {
        "total_entities": 0,
        "migrated_entities": 0,
        "errors": []
    }
    
    for entry in registry.entities.get_entries_for_config_entry_id(config_entry_id):
        verification_results["total_entities"] += 1
        
        # Prüfen, ob Migration erfolgreich war
        if entry.platform == "new_platform":
            verification_results["migrated_entities"] += 1
        else:
            verification_results["errors"].append(
                f"{entry.entity_id}: Plattform nicht aktualisiert"
            )
    
    return verification_results
```

## Fazit

Die Entity Registry bietet umfangreiche Möglichkeiten für die Migration und Aktualisierung von Entitäten. Wichtig ist dabei:

1. **Historische Daten schützen**: entity_id niemals ändern
2. **Schrittweise vorgehen**: Komplexe Migrationen in mehreren Schritten
3. **Validierung**: Alle Änderungen vor der Anwendung prüfen
4. **Backup**: Sichern Sie sich vor Migrationen ab
5. **Monitoring**: Überwachen Sie den Migrationsprozess

Durch die korrekte Verwendung dieser Funktionen können Integrationen sicher aktualisiert werden, ohne dass historische Daten verloren gehen.

## Weitere Ressourcen

### **Offizielle Home Assistant Dokumentation**

- [Home Assistant Entity Registry API](https://developers.home-assistant.io/docs/entity_registry_index/) - Offizielle API-Dokumentation
- [Home Assistant Migration Guide](https://developers.home-assistant.io/docs/migration/) - Allgemeiner Migrationsleitfaden
- [Home Assistant Event System](https://developers.home-assistant.io/docs/core/event/) - Event-System Dokumentation
- [Home Assistant Configuration Entries](https://developers.home-assistant.io/docs/config_entries_index/) - Konfigurationseinträge
- [Home Assistant Core Source Code](https://github.com/home-assistant/core) - Quellcode der Entity Registry

### **Spezifische Entity Registry Funktionen**

- [Entity Registry Helper Functions](https://github.com/home-assistant/core/blob/dev/homeassistant/helpers/entity_registry.py) - Alle verfügbaren Hilfsfunktionen
- [Entity Registry Events](https://github.com/home-assistant/core/blob/dev/homeassistant/helpers/entity_registry.py#L1320) - Event-basierte Updates
- [Entity Registry Storage](https://github.com/home-assistant/core/blob/dev/homeassistant/helpers/entity_registry.py#L460) - Speicher- und Migrationslogik

### **Praktische Beispiele und Tutorials**

- [Home Assistant Community Forum](https://community.home-assistant.io/) - Community-Diskussionen und Lösungen
- [Home Assistant Discord](https://discord.gg/c5DvZ4e) - Live-Hilfe und Diskussionen
- [Home Assistant GitHub Discussions](https://github.com/home-assistant/core/discussions) - Entwickler-Diskussionen

### **Integration-spezifische Migrationen**

- [Zigbee2MQTT Migration Guide](https://github.com/Koenkk/Z-Stack-firmware/tree/master/coordinator/Z-Stack_3.x.0/bin) - Beispiel für Zigbee-Integrationen
- [Z-Wave JS Migration](https://github.com/home-assistant/core/tree/dev/homeassistant/components/zwave_js) - Z-Wave Migrationsbeispiele
- [MQTT Integration Migration](https://github.com/home-assistant/core/tree/dev/homeassistant/components/mqtt) - MQTT-spezifische Migrationen

### **Best Practices und Patterns**

- [Home Assistant Architecture](https://developers.home-assistant.io/docs/architecture_index/) - Architektur-Übersicht
- [Home Assistant Testing](https://developers.home-assistant.io/docs/development_testing/) - Testen von Migrationen
- [Home Assistant Code Standards](https://developers.home-assistant.io/docs/development_coding_standards/) - Coding Standards

### **Community-Beiträge und Blog-Posts**

- [Home Assistant Blog](https://www.home-assistant.io/blog/) - Offizielle Blog-Posts
- [Community Blog](https://community.home-assistant.io/c/blog) - Community-Blog-Beiträge
- [Reddit r/homeassistant](https://www.reddit.com/r/homeassistant/) - Reddit Community

### **Video-Tutorials und Präsentationen**

- [Home Assistant YouTube Channel](https://www.youtube.com/c/HomeAssistant) - Offizielle Videos
- [Community YouTube Channels](https://community.home-assistant.io/c/videos) - Community-Videos
- [Home Assistant Conference Talks](https://conference.home-assistant.io/) - Konferenz-Vorträge

### **Entwickler-Tools und Debugging**

- [Home Assistant Dev Tools](https://www.home-assistant.io/docs/tools/dev-tools/) - Entwickler-Tools
- [Home Assistant Logs](https://www.home-assistant.io/docs/configuration/logging/) - Logging und Debugging
- [Home Assistant Profiler](https://www.home-assistant.io/docs/tools/profiler/) - Performance-Profiling

### **Migration-spezifische Ressourcen**

- [Entity Registry Migration Examples](https://github.com/home-assistant/core/tree/dev/tests/helpers/test_entity_registry.py) - Test-Beispiele für Migrationen
- [Configuration Entry Migration](https://github.com/home-assistant/core/tree/dev/homeassistant/config_entries) - Konfigurationseintrag-Migrationen
- [Device Registry Migration](https://github.com/home-assistant/core/tree/dev/homeassistant/helpers/device_registry.py) - Geräte-Registry Migrationen
