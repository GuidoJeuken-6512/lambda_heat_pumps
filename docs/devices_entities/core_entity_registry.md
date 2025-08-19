# Home Assistant Core Entity Registry

## Inhaltsverzeichnis

- [Übersicht](#übersicht)
- [Was ist die Entity Registry?](#was-ist-die-entity-registry)
- [Wo befindet sich die Entity Registry?](#wo-befindet-sich-die-entity-registry)
- [Struktur der Entity Registry](#struktur-der-entity-registry)
  - [entity_id (String)](#1-entity_id-string)
  - [name (String)](#2-name-string)
    - [Name-Anzeige in der GUI](#name-anzeige-in-der-gui)
  - [platform (String)](#3-platform-string)
  - [config_entry_id (String)](#4-config_entry_id-string)
  - [device_id (String)](#5-device_id-string)
  - [area_id (String)](#6-area_id-string)
  - [capabilities (Object)](#7-capabilities-object)
  - [supported_features (Integer)](#8-supported_features-integer)
  - [disabled_by (String)](#9-disabled_by-string)
  - [entity_category (String)](#10-entity_category-string)
  - [has_entity_name (Boolean)](#11-has_entity_name-boolean)
  - [original_name (String)](#12-original_name-string)
  - [unique_id (String)](#13-unique_id-string)
  - [previous_unique_id (String)](#14-previous_unique_id-string)
- [Beispiel einer Entity Registry Eintrag](#beispiel-einer-entity-registry-eintrag)
- [Wichtigkeit der Entity Registry](#wichtigkeit-der-entity-registry)
  - [Persistenz](#1-persistenz)
  - [Verknüpfungen](#2-verknüpfungen)
  - [Benutzerfreundlichkeit](#3-benutzerfreundlichkeit)
  - [Automatisierung](#4-automatisierung)
- [Entitätserstellung und Migration in Integrationen](#entitätserstellung-und-migration-in-integrationen)
  - [Automatische Entitätserstellung](#1-automatische-entitätserstellung)
  - [Entitätsmigration bei Updates](#2-entitätsmigration-bei-updates)
  - [Manuelle Entitätsverwaltung](#3-manuelle-entitätsverwaltung)
  - [Entitätsverknüpfungen](#4-entitätsverknüpfungen)
- [Best Practices](#best-practices)
  - [Namensgebung](#1-namensgebung)
  - [Organisation](#2-organisation)
  - [Wartung](#3-wartung)
- [Fehlerbehebung](#fehlerbehebung)
  - [Häufige Probleme](#häufige-probleme)
- [Abhängigkeit zu historischen Daten](#abhängigkeit-zu-historischen-daten)
  - [Verbindung zur Datenbank](#verbindung-zur-datenbank)
    - [Datenbankstruktur](#1-datenbankstruktur)
    - [Matching-Mechanismus](#2-matching-mechanismus)
    - [Datenfluss](#3-datenfluss)
  - [Wichtige Abhängigkeiten](#4-wichtige-abhängigkeiten)
    - [Recorder-Integration](#recorder-integration)
    - [History-Integration](#history-integration)
    - [Statistics-Integration](#statistics-integration)
  - [Matching-Probleme und Lösungen](#5-matching-probleme-und-lösungen)
    - [Problem: Entität verschwunden aus History](#problem-entität-verschwunden-aus-history)
    - [Problem: Historische Daten nicht verfügbar](#problem-historische-daten-nicht-verfügbar)
    - [Problem: Falsche Datenzuordnung](#problem-falsche-datenzuordnung)
  - [Datenbankoptimierung](#6-datenbankoptimierung)
    - [Indizes für bessere Performance](#indizes-für-bessere-performance)
    - [Partitionierung für große Datenmengen](#partitionierung-für-große-datenmengen)
  - [Monitoring und Wartung](#7-monitoring-und-wartung)
    - [Überprüfung der Datenintegrität](#überprüfung-der-datenintegrität)
    - [Bereinigung verwaister Daten](#bereinigung-verwaister-daten)
- [Fazit](#fazit)
- [Weitere Ressourcen](#weitere-ressourcen)

---

## Übersicht

Die `core.entity_registry` ist eine zentrale Komponente in Home Assistant, die alle verfügbaren Entitäten (Entities) verwaltet und deren Metadaten speichert. Sie fungiert als zentrales Verzeichnis für alle Sensoren, Schalter, Lampen und andere Geräte in Ihrem Smart Home.

## Was ist die Entity Registry?

Die Entity Registry ist eine persistente Datenbank, die Informationen über alle Entitäten in Ihrem Home Assistant System speichert. Sie wird automatisch verwaltet und aktualisiert, wenn neue Geräte hinzugefügt oder bestehende konfiguriert werden.

## Wo befindet sich die Entity Registry?

Die Entity Registry wird in der Datei `.storage/core.entity_registry` gespeichert, die sich im Konfigurationsverzeichnis von Home Assistant befindet.

## Struktur der Entity Registry

Jede Entität in der Registry hat folgende Hauptattribute:

### 1. **entity_id** (String)
- **Beschreibung**: Eindeutige ID der Entität im Format `domain.unique_name`
- **Beispiele**: `sensor.temperature_living_room`, `light.kitchen_ceiling`
- **Wichtigkeit**: Wird für alle Referenzen in Automatisierungen, Skripten und Dashboards verwendet
- **Format**: `{domain}.{name}`

### 2. **name** (String)
- **Beschreibung**: Benutzerfreundlicher Name der Entität
- **Beispiele**: "Wohnzimmer Temperatur", "Küche Deckenleuchte"
- **Wichtigkeit**: Wird in der Benutzeroberfläche angezeigt
- **Hinweis**: Kann vom Benutzer geändert werden

#### **Name-Anzeige in der GUI**

**Wenn `name` leer ist (`null` oder leerer String):**
- Home Assistant generiert automatisch einen Namen aus der `entity_id`
- Format: `domain.unique_name` wird zu `Domain Unique Name` konvertiert
- Beispiel: `sensor.lambda_hp1_temperature` → "Sensor Lambda Hp1 Temperature"
- Automatische Groß-/Kleinschreibung und Leerzeichen-Formatierung

**Wenn `name` gefüllt ist:**
- Der benutzerdefinierte Name wird direkt angezeigt
- Überschreibt alle automatisch generierten Namen
- Wird in allen UI-Bereichen verwendet (Dashboards, Automatisierungen, etc.)
- Bleibt auch nach Neustarts und Updates erhalten

**Fallback-Mechanismus:**
1. **Priorität 1**: Benutzerdefinierter `name` aus der Registry
2. **Priorität 2**: Automatisch generierter Name aus der `entity_id`
3. **Priorität 3**: Integration-spezifischer Standardname (falls verfügbar)

**Beispiele für die Namensgenerierung:**
```
entity_id: sensor.living_room_temperature
name: null → "Sensor Living Room Temperature"

entity_id: light.kitchen_ceiling
name: "Küche Deckenleuchte" → "Küche Deckenleuchte"

entity_id: climate.hvac_system
name: "" → "Climate Hvac System"
```

### 3. **platform** (String)
- **Beschreibung**: Integration/Plattform, die die Entität bereitstellt
- **Beispiele**: `mqtt`, `modbus`, `zha`, `deconz`
- **Wichtigkeit**: Zeigt an, über welchen Weg die Entität kommuniziert

### 4. **config_entry_id** (String)
- **Beschreibung**: Verknüpfung zur Konfigurationseintrag-ID
- **Wichtigkeit**: Verknüpft die Entität mit der entsprechenden Integration
- **Hinweis**: Wird für die Verwaltung von Integrationen benötigt

### 5. **device_id** (String)
- **Beschreibung**: Verknüpfung zur Geräte-ID in der Device Registry
- **Wichtigkeit**: Gruppiert Entitäten, die zum selben physischen Gerät gehören
- **Beispiel**: Ein Temperatursensor und ein Feuchtigkeitssensor am selben Gerät

### 6. **area_id** (String)
- **Beschreibung**: Verknüpfung zur Bereichs-ID (z.B. Wohnzimmer, Küche)
- **Wichtigkeit**: Ermöglicht die Gruppierung von Entitäten nach Räumen
- **Verwendung**: Für Dashboards und Automatisierungen

### 7. **capabilities** (Object)
- **Beschreibung**: Verfügbare Funktionen der Entität
- **Beispiele**: `min`, `max`, `step` für numerische Werte
- **Wichtigkeit**: Definiert, welche Aktionen möglich sind

### 8. **supported_features** (Integer)
- **Beschreibung**: Bitmaske der unterstützten Features
- **Beispiele**: Für Lampen: Dimmen, Farbänderung, etc.
- **Wichtigkeit**: Bestimmt verfügbare Steuerungsoptionen

### 9. **disabled_by** (String)
- **Beschreibung**: Grund, warum die Entität deaktiviert ist
- **Werte**: `user`, `integration`, `config_entry`, `none`
- **Wichtigkeit**: Zeigt an, ob und warum eine Entität nicht verfügbar ist

### 10. **entity_category** (String)
- **Beschreibung**: Kategorie der Entität
- **Werte**: `config`, `diagnostic`, `primary`, `secondary`
- **Wichtigkeit**: Bestimmt, wie die Entität in der UI angezeigt wird

### 11. **has_entity_name** (Boolean)
- **Beschreibung**: Ob die Entität einen eigenen Namen hat
- **Wichtigkeit**: Beeinflusst die Namensgebung in der UI

### 12. **original_name** (String)
- **Beschreibung**: Ursprünglicher Name der Entität
- **Wichtigkeit**: Wird für Wiederherstellungen verwendet

### 13. **unique_id** (String)
- **Beschreibung**: Eindeutige ID der Entität (normalerweise vom Gerät)
- **Wichtigkeit**: Verhindert Duplikate bei Neustarts
- **Format**: Oft MAC-Adresse oder Seriennummer

### 14. **previous_unique_id** (String)
- **Beschreibung**: Vorherige unique_id der Entität vor einer Änderung
- **Wichtigkeit**: Ermöglicht die Verfolgung von Entitätsänderungen und Migrationen
- **Verwendung**: 
  - Bei Integration-Updates, die die unique_id ändern
  - Bei manuellen Änderungen der unique_id
  - Für die Rückverfolgung von Entitätshistorie
- **Beispiel**: Wenn eine Integration von Version 1.0 auf 2.0 aktualisiert wird und sich die unique_id ändert
- **Hinweis**: Wird nur gesetzt, wenn sich die unique_id ändert, sonst ist es `null`

## Beispiel einer Entity Registry Eintrag

```json
{
  "entity_id": "sensor.lambda_hp1_temperature",
  "name": "Lambda WP1 Temperatur",
  "platform": "lambda_heat_pumps",
  "config_entry_id": "abc123def456",
  "device_id": "device123",
  "area_id": "basement",
  "capabilities": {
    "min": -50,
    "max": 100,
    "step": 0.1
  },
  "supported_features": 0,
  "disabled_by": null,
  "entity_category": "primary",
  "has_entity_name": true,
  "original_name": "Lambda WP1 Temperatur",
  "unique_id": "lambda_hp1_temp_001",
  "previous_unique_id": null
}
```

## Wichtigkeit der Entity Registry

### 1. **Persistenz**
- Entitäten bleiben auch nach Neustarts erhalten
- Konfigurationen werden gespeichert
- Benutzerdefinierte Namen bleiben bestehen

### 2. **Verknüpfungen**
- Verbindet Entitäten mit Geräten
- Gruppiert Entitäten nach Bereichen
- Verknüpft mit Integrationen

### 3. **Benutzerfreundlichkeit**
- Benutzerdefinierte Namen
- Gruppierung nach Räumen
- Einfache Verwaltung

### 4. **Automatisierung**
- Stabile Referenzen für Automatisierungen
- Einfache Auswahl in Skripten
- Konsistente Namensgebung

## Entitätserstellung und Migration in Integrationen

### 1. **Automatische Entitätserstellung**
- **Discovery-Prozess**: Integrationen erkennen automatisch neue Geräte
- **Registry-Eintrag**: Neue Entität wird automatisch in der Entity Registry registriert
- **Standardwerte**: Integration setzt Standardnamen und -attribute
- **unique_id**: Wird automatisch aus Gerätedaten generiert (MAC, Seriennummer, etc.)

### 2. **Entitätsmigration bei Updates**
- **Version-Updates**: Integration kann Entitäten neu strukturieren
- **unique_id-Änderungen**: `previous_unique_id` wird gesetzt
- **Attribut-Updates**: Neue Felder werden hinzugefügt, veraltete entfernt
- **Rückwärtskompatibilität**: Bestehende Konfigurationen bleiben funktionsfähig

### 3. **Manuelle Entitätsverwaltung**
- **UI-Bearbeitung**: Entitäten können über die Home Assistant UI angepasst werden
- **Name-Änderungen**: Benutzerfreundliche Namen ohne Verlust der entity_id
- **Bereichszuordnung**: Entitäten können Räumen zugeordnet werden
- **Deaktivierung**: Unerwünschte Entitäten können deaktiviert werden

### 4. **Entitätsverknüpfungen**
- **Device Registry**: Entitäten werden mit physischen Geräten verknüpft
- **Area Registry**: Gruppierung nach Räumen für bessere Organisation
- **Integration Registry**: Verknüpfung mit der entsprechenden Integration
- **Konfigurationseinträge**: Verbindung zu spezifischen Integrationseinstellungen

## Best Practices

### 1. **Namensgebung**
- Verwenden Sie aussagekräftige Namen
- Nutzen Sie deutsche Bezeichnungen
- Halten Sie Namen kurz aber verständlich

### 2. **Organisation**
- Gruppieren Sie Entitäten nach Räumen
- Verwenden Sie konsistente Namenskonventionen
- Deaktivieren Sie ungenutzte Entitäten

### 3. **Wartung**
- Überprüfen Sie regelmäßig die Registry
- Entfernen Sie verwaiste Entitäten
- Aktualisieren Sie veraltete Konfigurationen

## Fehlerbehebung

### Häufige Probleme

1. **Entität verschwunden**
   - Prüfen Sie, ob das Gerät noch verbunden ist
   - Überprüfen Sie die Integration
   - Schauen Sie in die Logs

2. **Doppelte Entitäten**
   - Prüfen Sie die `unique_id`
   - Entfernen Sie Duplikate manuell
   - Aktualisieren Sie die Integration

3. **Falsche Verknüpfungen**
   - Überprüfen Sie `device_id` und `area_id`
   - Korrigieren Sie manuell in der UI
   - Nutzen Sie die Home Assistant UI für Änderungen

## Fazit

Die Entity Registry ist das Herzstück der Home Assistant Entitätsverwaltung. Sie sorgt für Stabilität, Benutzerfreundlichkeit und eine saubere Organisation Ihres Smart Home Systems. Durch das Verständnis der verschiedenen Attribute und deren Bedeutung können Sie Ihr System optimal konfigurieren und warten.

## Abhängigkeit zu historischen Daten

### Verbindung zur Datenbank

Die Entity Registry ist eng mit der Home Assistant Datenbank verknüpft, die historische Daten aller Entitäten speichert. Diese Verbindung ist entscheidend für die Funktionalität des Systems.

#### 1. **Datenbankstruktur**
- **Tabelle**: `states` - Speichert alle Zustandsänderungen
- **Verknüpfung**: Über `entity_id` wird die Verbindung hergestellt
- **Zeitstempel**: Jeder Zustand wird mit UTC-Zeitstempel gespeichert
- **Metadaten**: Zusätzliche Informationen wie Einheiten und Attribute

#### 2. **Matching-Mechanismus**

Das Matching zwischen Entity Registry und historischen Daten erfolgt über mehrere Schlüssel:

```sql
-- Beispiel der Datenbankabfrage
SELECT * FROM states 
WHERE entity_id = 'sensor.lambda_hp1_temperature' 
ORDER BY last_updated DESC;
```

**Primärer Schlüssel**: `entity_id`
- Muss exakt mit dem `entity_id` in der Entity Registry übereinstimmen
- Änderungen an der Registry wirken sich sofort auf historische Daten aus

**Sekundäre Schlüssel**:
- `unique_id` - Für die Identifikation bei Neustarts
- `device_id` - Für gerätebasierte Abfragen
- `area_id` - Für bereichsbasierte Abfragen

#### 3. **Datenfluss**

```
Integration → Entity Registry → Datenbank
     ↓              ↓           ↓
  Neue Entität → Registriert → Zustände gespeichert
     ↓              ↓           ↓
  Update → Registry aktualisiert → Neue Daten hinzugefügt
     ↓              ↓           ↓
  Löschung → Registry bereinigt → Historische Daten bleiben
```

### 4. **Wichtige Abhängigkeiten**

#### **Recorder-Integration**
- Speichert alle Zustandsänderungen in der Datenbank
- Verwendet die Entity Registry für die Zuordnung
- Kann nur Entitäten aufzeichnen, die in der Registry registriert sind

#### **History-Integration**
- Zeigt historische Daten in der UI an
- Filtert basierend auf Entity Registry Einträgen
- Berücksichtigt `disabled_by` Status

#### **Statistics-Integration**
- Berechnet Durchschnittswerte und Trends
- Benötigt kontinuierliche Daten aus der Datenbank
- Abhängig von der Stabilität der Entity Registry

### 5. **Matching-Probleme und Lösungen**

#### **Problem: Entität verschwunden aus History**
- **Ursache**: Entität in Registry deaktiviert (`disabled_by: user`)
- **Lösung**: Entität über die UI wieder aktivieren oder `disabled_by: null` setzen
- **Häufige Ursachen**: Integration wurde entfernt, Gerät offline, manuelle Deaktivierung

#### **Problem: Historische Daten nicht verfügbar**
- **Ursache**: Recorder-Integration filtert Entitäten aus
- **Lösung**: Überprüfen Sie die Recorder-Konfiguration auf Include/Exclude-Regeln
- **Häufige Ursachen**: Entität wird von Recorder ignoriert, Datenbank-Fehler

#### **Problem: Falsche Datenzuordnung**
- **Ursache**: `unique_id` ist nicht eindeutig oder hat sich geändert
- **Lösung**: Überprüfen Sie die `unique_id` in der Entity Registry
- **Häufige Ursachen**: Integration-Updates, doppelte Geräte, fehlerhafte Konfiguration

### 6. **Datenbankoptimierung**

#### **Indizes für bessere Performance**
```sql
-- Entity Registry abhängige Indizes
CREATE INDEX IF NOT EXISTS states_entity_id_idx ON states(entity_id);
CREATE INDEX IF NOT EXISTS states_last_updated_idx ON states(last_updated);
CREATE INDEX IF NOT EXISTS states_entity_id_last_updated_idx ON states(entity_id, last_updated);
```

#### **Partitionierung für große Datenmengen**
- **Auto-Purge**: Automatische Bereinigung alter Daten
- **Auto-Repack**: Datenbank-Optimierung für bessere Performance
- **Commit-Interval**: Häufigkeit der Datenbank-Commits
- **Max-Retry-Delay**: Maximale Wartezeit bei Verbindungsproblemen

### 7. **Monitoring und Wartung**

#### **Überprüfung der Datenintegrität**
- **Automatisierte Überwachung**: Regelmäßige Prüfung der Registry-Integrität
- **Zeitbasierte Trigger**: Überwachung zu definierten Zeiten
- **Logging**: Protokollierung von Status-Checks und Problemen
- **Benachrichtigungen**: Warnungen bei Registry-Problemen

#### **Bereinigung verwaister Daten**
```sql
-- Finde Entitäten ohne Registry-Eintrag
SELECT DISTINCT entity_id FROM states 
WHERE entity_id NOT IN (
  SELECT entity_id FROM entity_registry
);
```

## Weitere Ressourcen

- [Home Assistant Entity Registry Dokumentation](https://www.home-assistant.io/docs/configuration/entity_registry/)
- [Home Assistant Device Registry](https://www.home-assistant.io/docs/configuration/device_registry/)
- [Home Assistant Area Registry](https://www.home-assistant.io/docs/configuration/area_registry/)
- [Home Assistant Integration Dokumentation](https://www.home-assistant.io/integrations/)
- [Home Assistant Recorder Dokumentation](https://www.home-assistant.io/docs/configuration/recorder/)
- [Home Assistant History Dokumentation](https://www.home-assistant.io/docs/configuration/history/)
- [Home Assistant Statistics Dokumentation](https://www.home-assistant.io/docs/configuration/statistics/)
