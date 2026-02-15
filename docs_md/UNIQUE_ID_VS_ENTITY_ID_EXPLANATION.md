# Unterschied zwischen unique_id und entity_id in Home Assistant

## Kurze Erklärung

| Aspekt | unique_id | entity_id |
|--------|-----------|-----------|
| **Zweck** | Identifiziert eine Entity über Integration-Neuladen/Restarts hinweg | Benutzer-sichtbare, eindeutige Bezeichnung im System |
| **Bereich** | Pro Integrationsinstanz eindeutig | Global eindeutig im gesamten Home Assistant |
| **Änderbar** | Nein (führt zu Registry-Konflikt) | Ja, aber nur manuell (user-facing) |
| **Speicher-Ort** | Entity Registry (intern) | State Machine + Entity Registry |
| **Beispiel** | `eu08l_hp1_heating_energy_daily` | `sensor.eu08l_hp1_heating_energy_daily` |
| **Sichtbar für User?** | Nein (intern) | Ja (in Automatisierungen, etc.) |

---

## Vertiefung: Wie sie zusammenhängen

### Home Assistant Entity Registry

Home Assistant verwaltet alle Sensoren, Switches, etc. in einer **Entity Registry**:

```
Entity Registry:
├─ unique_id: "eu08l_hp1_heating_energy_daily"          ← Internal ID
├─ entity_id: "sensor.eu08l_hp1_heating_energy_daily"   ← User-facing ID
├─ domain: "sensor"
├─ platform: "lambda_heat_pumps"
├─ config_entry_id: "a1b2c3d4e5f6..."                  ← Welche Integration?
└─ ... weitere Metadaten
```

### unique_id – Das interne Gedächtnis

**Zweck:** Home Assistant damit sagen "Diese Entity wurde bereits erstellt, nicht neu erstellen"

**Verwendung:**
```python
# In sensor.py:
class LambdaEnergyConsumptionSensor(SensorEntity):
    def __init__(self, ...):
        self._attr_unique_id = f"{name_prefix}_hp1_heating_energy_daily"
        # Home Assistant speichert das in der Registry
```

**Was passiert bei Neustart:**
```
Neustart 1:
├─ Sensor wird erstellt mit unique_id = "eu08l_hp1_heating_energy_daily"
└─ Home Assistant speichert das, entity_id wird vergeben

Neustart 2:
├─ Sensor wird wieder erstellt mit GLEICHER unique_id
├─ Home Assistant sieht: "Ah, diese Entity kenne ich schon!"
└─ Verwendet den alten entity_id wieder → Keine Duplikate
```

### entity_id – Der Benutzername

**Zweck:** Für Benutzer und Automatisierungen lesbar

**Verwendung in Automatisierungen:**
```yaml
automation:
  - alias: "Heizung zu teuer"
    trigger:
      entity_id: sensor.eu08l_hp1_heating_energy_daily  # ← entity_id!
      above: 20
    action: ...
```

**Generierung aus unique_id:**
```python
# Home Assistant macht sowas ähnliches:
entity_id = f"sensor.{unique_id}"  # Vereinfacht gesagt

# oder mit Domain:
entity_id = f"{domain}.{sanitized_unique_id}"
```

---

## Aktuelles Problem in der Integration

### Wie werden sie JETZT generiert?

**In sensor.py & utils.py:**

```python
# name_prefix kommt aus Config-Flow
name_prefix = entry.data.get("name", "")  # z.B. "eu08l" oder "EU08L"

# Es wird NICHT konsistent normalisiert:
if name_prefix:
    name_prefix_lc = name_prefix.lower()  # "EU08L" → "eu08l"
else:
    name_prefix_lc = ""  # Problem: wird nicht normalisiert!

# unique_id:
unique_id = f"{name_prefix_lc}_hp1_{sensor_id}"
# Beispiel: "eu08l_hp1_heating_energy_daily"

# entity_id:
entity_id = f"sensor.{name_prefix_lc}_hp1_{sensor_id}"
# Beispiel: "sensor.eu08l_hp1_heating_energy_daily"
```

### Das Duplikat-Problem entsteht hier:

```
Szenario:
└─ User gibt im Config-Flow Namen "EU08L" ein (Großbuchstaben)

Neustart 1:
├─ name_prefix = "EU08L"
├─ unique_id = "EU08L_hp1_heating_energy_daily"  (nicht normalisiert!)
├─ entity_id = "sensor.EU08L_hp1_heating_energy_daily"
└─ Speichert beide in Registry

Neustart 2 (oder User ändert Namen auf "eu08l"):
├─ name_prefix = "eu08l"
├─ unique_id = "eu08l_hp1_heating_energy_daily"  ← ANDERS als Neustart 1!
├─ entity_id = "sensor.eu08l_hp1_heating_energy_daily"
└─ Home Assistant sieht:
   ├─ Neue unique_id → "Das ist eine neue Entity!"
   ├─ Aber entity_id existiert schon in der Registry
   └─ KONFLIKT! → Erstellt "sensor.eu08l_hp1_heating_energy_daily_2"
```

---

## Die Lösung: Normalisierung (V2)

### AKTUELL (Fehleranfällig):

```
unique_id = "{nicht_normalisiertes_name_prefix}_hp1_sensor_id"
          = "EU08L_hp1_heating_energy_daily"  ← Groß/Klein unterschiedlich!
          = "eu08l_hp1_heating_energy_daily"  ← Andere Eingabe
          → UNTERSCHIEDLICH → Duplikat!

entity_id = f"sensor.{unique_id}"
```

### NEU (Mit Normalisierung):

```python
# Normalisierung IMMER machen:
def normalize_name_prefix(raw_name_prefix: str) -> str:
    if not raw_name_prefix:
        return "device"
    return raw_name_prefix.lower().replace(" ", "_").replace("-", "_")[:30]

# Dann:
name_prefix = normalize_name_prefix(entry.data.get("name", ""))
# "EU08L" → "eu08l"
# "eu08l" → "eu08l"
# "Eu 08 L" → "eu_08_l"

unique_id = f"{name_prefix}_hp1_heating_energy_daily"
           = "eu08l_hp1_heating_energy_daily"  ← IMMER gleich!

entity_id = f"sensor.{unique_id}"
          = "sensor.eu08l_hp1_heating_energy_daily"  ← Konsistent
```

---

## Langfristige Lösung: entry_id-basiert (V3)

### WARUM das noch besser ist:

**Aktuell (name_prefix-basiert):**
```
unique_id = "eu08l_hp1_heating_energy_daily"

Problem: Was wenn der Benutzer MEHRMALS "eu08l" als Name verwendet?
├─ Integration 1 mit Name "eu08l" → unique_id = "eu08l_hp1_..."
├─ Integration 2 mit Name "eu08l" → unique_id = "eu08l_hp1_..."  ← KONFLIKT!
└─ Home Assistant kann nicht unterscheiden, welche ist welche
```

**Neu (entry_id-basiert):**
```
unique_id = "{entry_id}_hp1_heating_energy_daily"
          = "a1b2c3d4e5f6_hp1_heating_energy_daily"  ← Entry 1
          = "z9y8x7w6v5u4_hp1_heating_energy_daily"  ← Entry 2
          ← GARANTIERT unterschiedlich, selbst wenn Name gleich ist!

Warum entry_id?
├─ entry_id = UUID der Config-Entry
├─ Würde vom Benutzer oder System generiert
├─ Ändert sich NIEMALS während der Integration
└─ Ist GLOBAL eindeutig über alle Integrationen
```

### Vergleich:

```
Szenario: Zwei Lambda Heat Pump Integrationen mit gleichen Namen

┌─ Integration 1 (Name: "eu08l")
├─ Config Entry ID: "a1b2c3d4e5f6..."
├─ AKTUELL mit name_prefix-Basis:
│  └─ unique_id = "eu08l_hp1_heating_energy_daily"
└─ NEU mit entry_id-Basis:
   └─ unique_id = "a1b2c3d4e5f6_hp1_heating_energy_daily"

┌─ Integration 2 (Name: "eu08l", anders Setup!)
├─ Config Entry ID: "z9y8x7w6v5u4..."
├─ AKTUELL mit name_prefix-Basis:
│  └─ unique_id = "eu08l_hp1_heating_energy_daily"  ← KONFLIKT mit Integration 1!
└─ NEU mit entry_id-Basis:
   └─ unique_id = "z9y8x7w6v5u4_hp1_heating_energy_daily"  ← Eindeutig!
```

---

## Grafik: unique_id vs entity_id

```
Home Assistant System
│
├─── Entity Registry (Speichert Mapping)
│    │
│    ├─ unique_id (internal): "eu08l_hp1_heating_energy_daily"
│    │  └─ ✅ Damit weiß HA: "Diese Entity schon gesehen"
│    │
│    ├─ entity_id (user-facing): "sensor.eu08l_hp1_heating_energy_daily"
│    │  └─ ✅ Damit können User diese Entity referenzieren
│    │
│    └─ config_entry_id: "a1b2c3d4e5f6..."
│       └─ ✅ Damit weiß HA, zu welcher Integration gehört
│
├─── State Machine (speichert Wert)
│    │
│    └─ entity_id: "sensor.eu08l_hp1_heating_energy_daily"
│       └─ state: "123.45"  (der aktuelle Sensorwert)
│
└─── Automatisierungen
     │
     └─ Benutzer schreibt:
        automation.daily_summary:
          trigger:
            entity_id: sensor.eu08l_hp1_heating_energy_daily  ← entity_id!
          condition:
            numeric_state:
              entity_id: sensor.eu08l_hp1_heating_energy_daily  ← entity_id!
              above: 20
          action: ...
```

---

## Praktische Auswirkungen

### Wenn unique_id sich ändert (Aktueller Bug):

```
Effekt 1: Registry-Struktur
├─ Alte unique_id in Registry bleibt registriert
├─ Neue unique_id sieht HA als "neue Entity"
└─ Aber entity_id schon registriert!
   └─ → "_2" Suffix Duplikat entsteht

Effekt 2: Daten-Verlust
├─ Historische Daten (stored in influxdb oder SQLite)
├─ Sind mit der alten entity_id verknüpft
├─ Neue unique_id → neue entity_id (_2) → keine alten Daten
└─ → Energy-Geschichte ist unterbrochen!

Effekt 3: Automation Bricht
├─ Automation referenziert "sensor.eu08l_hp1_heating_energy_daily"
├─ Aber jetzt gibt es auch "sensor.eu08l_hp1_heating_energy_daily_2"
├─ Automation läuft gegen falsches Entity oder beide!
└─ → Verwirrung & unerwartetes Verhalten
```

### Mit korrekter Normalisierung (V2):

```
unique_id ändert sich NICHT mehr
├─ entity_id bleibt gleich
├─ Historische Daten bleiben erhalten
├─ Automation funktioniert weiterhin
└─ ✅ Keine Duplikate!
```

### Mit entry_id-basiert (V3):

```
unique_id ist GARANTIERT eindeutig
├─ Auch wenn Benutzer mehrere Integrationen mit gleichem Namen anlegt
├─ Keine Konflikte auch in komplexen Setups
└─ ✅ Zukunftssicher & skalierbar!
```

---

## Zusammenfassung für die Migration

### Problem-Ablauf:

```
1. User gibt Name "EU08L" ein
   ↓
2. unique_id = "EU08L_..." (nicht normalisiert)
   ↓
3. User/System ändert zu "eu08l" oder Neustart
   ↓
4. unique_id = "eu08l_..." (ANDERS!)
   ↓
5. Home Assistant sieht neue unique_id + alte entity_id
   ↓
6. Konflikt → Duplikat "_2" entsteht!
```

### Lösung V2 (Normalisierung):

```
Verhindet, dass unique_id unterschiedlich wird:
├─ Alle Eingaben → einheitliche Form
└─ ✅ Keine Duplikate
```

### Lösung V3 (entry_id-basiert):

```
Verwendet globale eindeutige Identifizierer:
├─ entry_id ist UUID, ändert sich nie
├─ Auch bei mehreren setups wie "eu08l" eindeutig
└─ ✅ Zukunftssicher & skalierbar
```

---

## Beispiel aus der Realität

**Setup eines Benutzers:**

```
Integration 1: Lambda Heat Pump
├─ Name eingegeben: "Wärmepumpe Oben"
├─ Config Entry ID: "abc123..."
├─ Sensoren:
│  └─ sensor.warmepumpe_oben_hp1_heating_energy_daily
│
└─ unique_id: "warmepumpe_oben_hp1_heating_energy_daily"

Integration 2: Zweite Wärmepumpe (gleicher Name!)
├─ Name eingegeben: "Wärmepumpe Oben"  ← GLEICH wie Integration 1
├─ Config Entry ID: "def456..."
├─ Sensoren:
│  └─ PROBLEM mit aktueller Lösung!
│
└─ unique_id: "warmepumpe_oben_hp1_heating_energy_daily"  ← KONFLIKT!
   └─ Home Assistant: "Warte, diese unique_id gibt es ja schon!"
   └─ Erstellt Duplikat: "sensor.warmepumpe_oben_hp1_heating_energy_daily_2"
```

**Mit entry_id-Lösung:**

```
Integration 1:
├─ unique_id: "abc123_hp1_heating_energy_daily"

Integration 2:
├─ unique_id: "def456_hp1_heating_energy_daily"  ← ANDERS (entry_id unterschiedlich)
└─ ✅ Kein Konflikt!
```

---

**Fazit:**
- **unique_id** = Internes Gedächtnis von Home Assistant ("Kenne ich diese Entity?")
- **entity_id** = Benutzer-sichtbare Adresse ("Wo ist diese Entity im System?")
- **Das Problem:** unique_id hängt von `name_prefix` ab, der nicht konsistent ist
- **Die Lösung:** Entweder normalisieren (V2) oder entry_id verwenden (V3)