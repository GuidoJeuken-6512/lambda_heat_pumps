# Inhaltsverzeichnis

- [Hinweis zur Migration von flacher zu hierarchischer Struktur](#hinweis-zur-migration-von-flacher-zu-hierarchischer-struktur)
- [Übersicht](#übersicht)
- [Beispielstruktur: Lambda Wärmepumpe "Eu08L"](#beispielstruktur-lambda-wärmepumpe-eu08l)
- [Verknüpfung: Integration → Device → Subdevice → Entity](#verknüpfung-integration--device--subdevice--entity)
- [Beispielhafte Registrierung im Code](#beispielhafte-registrierung-im-code)
- [Hinweise für Integrationsentwickler](#hinweise-für-integrationsentwickler)
- [Vorteile der Struktur](#vorteile-der-struktur)
- [Weitere Ressourcen](#weitere-ressourcen)
# Hinweis zur Migration von flacher zu hierarchischer Struktur

Eine Migration von einer flachen Struktur (ein Device, alle Sensoren darunter) zu einer hierarchischen Struktur (Hauptgerät + Subgeräte, wie im Beispiel unten) ist möglich, **ohne historische Daten oder Namen zu verlieren**, solange die `entity_id` der einzelnen Entitäten unverändert bleibt.

- Die Zuordnung zu Devices/Subdevices (`device_id`, `via_device`) kann geändert werden, ohne dass die `entity_id` geändert werden muss.
- Historische Daten (History, Logbuch, Statistiken) sind immer an die `entity_id` gebunden.
- Die Gerätehierarchie beeinflusst nur die Gruppierung und Anzeige im Frontend, nicht die Zuordnung der historischen Werte.

**Wichtig:** Nur wenn die `entity_id` geändert wird, gehen die alten Daten verloren.
# Geräte und Subgeräte in Home Assistant Integrationen  
**Beispiel: Lambda Wärmepumpe "Eu08L"**

## Übersicht

In Home Assistant werden Geräte (Devices) und Entitäten (Entities) über die Device Registry verwaltet. Ein Gerät repräsentiert eine physische oder virtuelle Hardware-Komponente (z.B. eine Wärmepumpe). Subgeräte sind Komponenten oder Module, die Teil eines Hauptgeräts sind, aber als eigene Geräte oder Entitäten erscheinen können.

## Beispielstruktur: Lambda Wärmepumpe "Eu08L"


- **Hauptgerät:**  
  - **Name:** Eu08L  
  - **device_id:** `eu08l_main`
  - **Entität:**  
    - `sensor.eu08l_status`  
      - Automatisch vergebener Name: **Eu08l Status**

- **Subgeräte:**  
  - **HP1:**  
    - **device_id:** `eu08l_hp1`
    - **Entität:**  
      - `sensor.eu08l_hp1_status`  
        - Automatisch vergebener Name: **Eu08l Hp1 Status**
  - **HP2:**  
    - **device_id:** `eu08l_hp2`
    - **Entität:**  
      - `sensor.eu08l_hp2_status`  
        - Automatisch vergebener Name: **Eu08l Hp2 Status**
  - **Boiler1:**  
    - **device_id:** `eu08l_boiler1`
    - **Entität:**  
      - `sensor.eu08l_boiler1_status`  
        - Automatisch vergebener Name: **Eu08l Boiler1 Status**
  - **Boiler2:**  
    - **device_id:** `eu08l_boiler2`
    - **Entität:**  
      - `sensor.eu08l_boiler2_status`  
        - Automatisch vergebener Name: **Eu08l Boiler2 Status**

## Verknüpfung: Integration → Device → Subdevice → Entity

1. **Integration:**  
   Stellt die Verbindung zur Lambda Wärmepumpe her.
2. **Device:**  
   Das Hauptgerät "Eu08L" wird als Device registriert.
3. **Subdevices:**  
   HP1, HP2, Boiler1, Boiler2 werden als eigene Devices (Subgeräte) registriert.
4. **Entities:**  
   Jeder Device/Subdevice ist mindestens ein Status-Sensor (Entity) zugeordnet.

## Beispielhafte Registrierung im Code

```python
# filepath: custom_components/lambda_heat_pumps/__init__.py
from homeassistant.helpers import device_registry as dr, entity_registry as er

# Device Registry und Entity Registry abrufen
device_registry = dr.async_get(hass)
entity_registry = er.async_get(hass)

# Hauptgerät registrieren
main_device = device_registry.async_get_or_create(
    config_entry_id=entry.entry_id,
    identifiers={("lambda_heat_pumps", "eu08l_main")},
    manufacturer="Lambda",
    model="Eu08L",
    name="Eu08L"
)

# Subgeräte registrieren
hp1_device = device_registry.async_get_or_create(
    config_entry_id=entry.entry_id,
    identifiers={("lambda_heat_pumps", "eu08l_hp1")},
    manufacturer="Lambda",
    model="HP1",
    name="Eu08L HP1",
    via_device_id=main_device.id  # Korrekte Verknüpfung zum Hauptgerät
)

# Analog für HP2, Boiler1, Boiler2...
hp2_device = device_registry.async_get_or_create(
    config_entry_id=entry.entry_id,
    identifiers={("lambda_heat_pumps", "eu08l_hp2")},
    manufacturer="Lambda",
    model="HP2",
    name="Eu08L HP2",
    via_device_id=main_device.id
)

# Entities mit Bezug auf Devices/Subdevices registrieren
# WICHTIG: device_id wird über die Entity Registry gesetzt, nicht im Konstruktor
async_add_entities([
    StatusSensor(name="Eu08L Status", entity_id="sensor.eu08l_status"),
    StatusSensor(name="HP1 Status", entity_id="sensor.eu08l_hp1_status"),
    # ... weitere Sensoren für HP2, Boiler1, Boiler2
])

# Nach der Registrierung die device_id über die Entity Registry setzen
for entity in hass.data[DOMAIN]["entities"]:
    if entity.entity_id == "sensor.eu08l_status":
        entity_registry.async_update_entity(
            entity_id=entity.entity_id,
            device_id=main_device.id
        )
    elif entity.entity_id == "sensor.eu08l_hp1_status":
        entity_registry.async_update_entity(
            entity_id=entity.entity_id,
            device_id=hp1_device.id
        )
    # ... weitere Entitäten
```

## Hinweise für Integrationsentwickler

- **Subdevices** sollten als eigene Devices registriert werden, wenn sie eigenständig steuerbar oder logisch abgrenzbar sind.
- Die Verknüpfung zwischen Subdevice und Hauptgerät erfolgt über das Attribut `via_device_id` (nicht `via_device`).
- Jede Entität (`sensor`, `switch`, etc.) muss mit einer `device_id` verknüpft werden, damit sie im Geräte-Dashboard erscheint.
- Die Device Registry sorgt für eine klare Zuordnung und Gruppierung in der Home Assistant UI.

## Migration von flacher zu hierarchischer Struktur

### **Schritt-für-Schritt Migration:**

1. **Backup erstellen**
   ```python
   # Entity Registry Backup
   entity_backup = {}
   for entity in entity_registry.entities.values():
       if entity.config_entry_id == config_entry_id:
           entity_backup[entity.entity_id] = {
               "device_id": entity.device_id,
               "name": entity.name,
               "unique_id": entity.unique_id
           }
   ```

2. **Neue Device-Struktur erstellen**
   ```python
   # Hauptgerät und Subgeräte registrieren
   main_device = device_registry.async_get_or_create(...)
   sub_device = device_registry.async_get_or_create(
       config_entry_id=entry.entry_id,
       identifiers={("lambda_heat_pumps", "sub_device")},
       via_device_id=main_device.id
   )
   ```

3. **Entitäten neu zuordnen**
   ```python
   # device_id der Entitäten aktualisieren
   for entity_id, backup_data in entity_backup.items():
       if "sub_device" in backup_data["name"]:
           entity_registry.async_update_entity(
               entity_id=entity_id,
               device_id=sub_device.id
           )
   ```

### **Wichtige Migrationsregeln:**

- **entity_id niemals ändern** - Alle historischen Daten bleiben erhalten
- **device_id kann geändert werden** - Entitäten werden neu gruppiert
- **via_device_id für Hierarchie** - Verknüpfung zwischen Haupt- und Subgeräten
- **Schrittweise Migration** - Erst testen, dann produktiv einsetzen

## Vorteile der Struktur

- Übersichtliche Darstellung im Frontend: Hauptgerät und Subgeräte werden logisch gruppiert.
- Automatische Zuordnung zu Räumen und Integrationen.
- Bessere Wartbarkeit und Erweiterbarkeit der Integration.

## Weitere Ressourcen

- [Home Assistant Device Registry](https://developers.home-assistant.io/docs/device_registry_index/)
- [Home Assistant Entity Registry](https://developers.home-assistant.io/docs/entity_registry_index/)
