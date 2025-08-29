# Lambda Heat Pumps: Cycling Sensoren (Total, Daily, Yesterday, 2H, 4H)

## Übersicht
Die Cycling-Sensoren sind eine **vereinfachte und robuste Lösung** zur Verfolgung von Betriebsmodus-Wechseln der Lambda Wärmepumpen. Sie umfassen:

- **Total-Sensoren**: Gesamtanzahl aller Cycling-Ereignisse seit Installation
- **Daily-Sensoren**: Tägliche Cycling-Werte (werden täglich um Mitternacht auf 0 gesetzt)
- **Yesterday-Sensoren**: Speichern die gestern erreichten Daily-Werte
- **2H-Sensoren**: 2-Stunden Cycling-Werte (werden alle 2 Stunden auf 0 gesetzt)
- **4H-Sensoren**: 4-Stunden Cycling-Werte (werden alle 4 Stunden auf 0 gesetzt)

**Neue vereinfachte Architektur:**
- Alle Sensoren werden **gleichzeitig** bei jeder Flankenerkennung erhöht


Die Flankenerkennung erfolgt zentral im Coordinator für maximale Robustheit und Performance.

## Architektur

### 1. Sensor-Typen

#### Total Cycling Sensoren (echte Entities)
- **Zweck**: Zählen die Gesamtanzahl der Cycling-Ereignisse seit Installation
- **Typ**: Echte Python-Entities (`LambdaCyclingSensor`)
- **Persistenz**: Werte werden direkt in den Entities gespeichert
- **Update**: Bei jeder Flankenerkennung durch `increment_cycling_counter`
- **Beispiele**: 
  - `sensor.eu08l_hp1_heating_cycling_total`
  - `sensor.eu08l_hp1_hot_water_cycling_total`
  - `sensor.eu08l_hp1_cooling_cycling_total`
  - `sensor.eu08l_hp1_defrost_cycling_total`

#### Yesterday Cycling Sensoren (echte Entities)
- **Zweck**: Speichern die gestern erreichten Daily-Cycling-Werte
- **Typ**: Echte Python-Entities (`LambdaYesterdaySensor`)
- **Update**: Täglich um Mitternacht auf Daily-Wert gesetzt (vor Daily-Reset)
- **Beispiele**:
  - `sensor.eu08l_hp1_heating_cycling_yesterday`
  - `sensor.eu08l_hp1_hot_water_cycling_yesterday`
  - `sensor.eu08l_hp1_cooling_cycling_yesterday`
  - `sensor.eu08l_hp1_defrost_cycling_yesterday`

#### Daily Cycling Sensoren (echte Entities)
- **Zweck**: Zählen die täglichen Cycling-Werte seit Mitternacht
- **Typ**: Echte Python-Entities (`LambdaCyclingSensor`)
- **Update**: Bei jeder Flankenerkennung erhöht, täglich um Mitternacht auf 0 gesetzt
- **Beispiele**:
  - `sensor.eu08l_hp1_heating_cycling_daily`
  - `sensor.eu08l_hp1_hot_water_cycling_daily`
  - `sensor.eu08l_hp1_cooling_cycling_daily`
  - `sensor.eu08l_hp1_defrost_cycling_daily`

#### 2H Cycling Sensoren (echte Entities)
- **Zweck**: Zählen die 2-Stunden Cycling-Werte
- **Typ**: Echte Python-Entities (`LambdaCyclingSensor`)
- **Update**: Bei jeder Flankenerkennung erhöht, alle 2 Stunden auf 0 gesetzt
- **Reset-Zeiten**: 00:00, 02:00, 04:00, 06:00, 08:00, 10:00, 12:00, 14:00, 16:00, 18:00, 20:00, 22:00
- **Beispiele**:
  - `sensor.eu08l_hp1_heating_cycling_2h`
  - `sensor.eu08l_hp1_hot_water_cycling_2h`
  - `sensor.eu08l_hp1_cooling_cycling_2h`
  - `sensor.eu08l_hp1_defrost_cycling_2h`

#### 4H Cycling Sensoren (echte Entities)
- **Zweck**: Zählen die 4-Stunden Cycling-Werte
- **Typ**: Echte Python-Entities (`LambdaCyclingSensor`)
- **Update**: Bei jeder Flankenerkennung erhöht, alle 4 Stunden auf 0 gesetzt
- **Reset-Zeiten**: 00:00, 04:00, 08:00, 12:00, 16:00, 20:00
- **Beispiele**:
  - `sensor.eu08l_hp1_heating_cycling_4h`
  - `sensor.eu08l_hp1_hot_water_cycling_4h`
  - `sensor.eu08l_hp1_cooling_cycling_4h`
  - `sensor.eu08l_hp1_defrost_cycling_4h`

### 2. Flankenerkennung

#### Zentrale Flankenerkennung im Coordinator
Die Flankenerkennung erfolgt zentral im `LambdaDataUpdateCoordinator` für maximale Robustheit:

```python
# In coordinator.py
def _detect_cycling_flank(self, hp_index: int, old_state: int, new_state: int) -> None:
    """Detect cycling flank and increment all relevant counters."""
    if old_state != new_state and old_state is not None:
        # Alle Sensor-Typen gleichzeitig erhöhen
        await increment_cycling_counter(
            self.hass, mode, hp_index, name_prefix, use_legacy_modbus_names, cycling_offsets
        )
```

#### Timing-Schutz
- **Startup-Schutz**: Erste 30 Sekunden nach Start werden ignoriert
- **Robuste Flankenerkennung**: Nur bei echten Statuswechseln
- **Fehlerbehandlung**: Graceful handling bei fehlenden Werten

### 3. Automatisierungen

#### Reset-basierte Logik
Die neue Architektur verwendet **Reset-basierte Logik** statt Update-basierte Logik:

```python
# In automations.py
@callback
def reset_daily_sensors(now: datetime) -> None:
    """Reset daily sensors at midnight and update yesterday sensors."""
    # 1. Erst Yesterday-Sensoren auf aktuelle Daily-Werte setzen
    _update_yesterday_sensors(hass, entry_id)
    
    # 2. Dann Daily-Sensoren auf 0 zurücksetzen
    async_dispatcher_send(hass, SIGNAL_RESET_DAILY, entry_id)
```

#### Zeit-basierte Resets
- **Daily-Reset**: Täglich um Mitternacht (00:00:00)
- **2H-Reset**: Alle 2 Stunden um :00 Uhr (00:00, 02:00, 04:00, etc.)
- **4H-Reset**: Alle 4 Stunden um :00 Uhr (00:00, 04:00, 08:00, etc.)

### 4. Funktionsweise der neuen Architektur

#### 4.1. Flankenerkennung und Inkrementierung
1. **Flankenerkennung**: Coordinator erkennt Statuswechsel
2. **Gleichzeitige Inkrementierung**: Alle Sensor-Typen werden gleichzeitig erhöht
3. **Persistenz**: Werte werden in den Entities gespeichert

#### 4.2. Reset-Zyklen
1. **Daily-Reset um Mitternacht**:
   - Yesterday-Sensoren werden auf aktuelle Daily-Werte gesetzt
   - Daily-Sensoren werden auf 0 zurückgesetzt

2. **2H-Reset alle 2 Stunden**:
   - 2H-Sensoren werden auf 0 zurückgesetzt

3. **4H-Reset alle 4 Stunden**:
   - 4H-Sensoren werden auf 0 zurückgesetzt

#### 4.3. Vorteile der neuen Architektur
- **Einfachheit**: Keine komplexen Template-Berechnungen
- **Robustheit**: Alle Sensoren sind echte Entities
- **Performance**: Keine kontinuierlichen Berechnungen
- **Wartbarkeit**: Klare Trennung der Verantwortlichkeiten
- **Skalierbarkeit**: Einfache Erweiterung um neue Zeiträume

### 5. Automatische Erstellung

#### 5.1. Basierend auf HP-Konfiguration
Alle Cycling-Sensoren werden automatisch basierend auf der HP-Konfiguration erstellt:

```python
# Aus der Config
num_hps = entry.data.get("num_hps", 1)  # z.B. 2 HPs

# Automatische Erstellung für jede HP
for hp_idx in range(1, num_hps + 1):  # 1, 2
    for mode, template_id in cycling_modes:  # heating, hot_water, cooling, defrost
        # Erstellt Total-, Yesterday-, Daily-, 2H- und 4H-Sensoren
```

#### 5.2. Konsistente Namensgebung
Alle Sensoren verwenden die zentrale `generate_sensor_names` Funktion:

```python
# Für alle Sensor-Typen
names = generate_sensor_names(
    device_prefix,        # "hp1"
    template["name"],     # "Heating Cycling Total"
    template_id,          # "heating_cycling_total"
    name_prefix,          # "eu08l"
    use_legacy_modbus_names  # False
)
```

#### 5.3. Beispiel-Output (2 HPs)
**Total-Sensoren (4 Modi × 2 HPs = 8 Sensoren):**
- `sensor.eu08l_hp1_heating_cycling_total`
- `sensor.eu08l_hp1_hot_water_cycling_total`
- `sensor.eu08l_hp1_cooling_cycling_total`
- `sensor.eu08l_hp1_defrost_cycling_total`
- `sensor.eu08l_hp2_heating_cycling_total`
- `sensor.eu08l_hp2_hot_water_cycling_total`
- `sensor.eu08l_hp2_cooling_cycling_total`
- `sensor.eu08l_hp2_defrost_cycling_total`

**Yesterday-Sensoren (4 Modi × 2 HPs = 8 Sensoren):**
- `sensor.eu08l_hp1_heating_cycling_yesterday`
- `sensor.eu08l_hp1_hot_water_cycling_yesterday`
- `sensor.eu08l_hp1_cooling_cycling_yesterday`
- `sensor.eu08l_hp1_defrost_cycling_yesterday`
- `sensor.eu08l_hp2_heating_cycling_yesterday`
- `sensor.eu08l_hp2_hot_water_cycling_yesterday`
- `sensor.eu08l_hp2_cooling_cycling_yesterday`
- `sensor.eu08l_hp2_defrost_cycling_yesterday`

**Daily-Sensoren (4 Modi × 2 HPs = 8 Sensoren):**
- `sensor.eu08l_hp1_heating_cycling_daily`
- `sensor.eu08l_hp1_hot_water_cycling_daily`
- `sensor.eu08l_hp1_cooling_cycling_daily`
- `sensor.eu08l_hp1_defrost_cycling_daily`
- `sensor.eu08l_hp2_heating_cycling_daily`
- `sensor.eu08l_hp2_hot_water_cycling_daily`
- `sensor.eu08l_hp2_cooling_cycling_daily`
- `sensor.eu08l_hp2_defrost_cycling_daily`

**2H-Sensoren (4 Modi × 2 HPs = 8 Sensoren):**
- `sensor.eu08l_hp1_heating_cycling_2h`
- `sensor.eu08l_hp1_hot_water_cycling_2h`
- `sensor.eu08l_hp1_cooling_cycling_2h`
- `sensor.eu08l_hp1_defrost_cycling_2h`
- `sensor.eu08l_hp2_heating_cycling_2h`
- `sensor.eu08l_hp2_hot_water_cycling_2h`
- `sensor.eu08l_hp2_cooling_cycling_2h`
- `sensor.eu08l_hp2_defrost_cycling_2h`

**4H-Sensoren (4 Modi × 2 HPs = 8 Sensoren):**
- `sensor.eu08l_hp1_heating_cycling_4h`
- `sensor.eu08l_hp1_hot_water_cycling_4h`
- `sensor.eu08l_hp1_cooling_cycling_4h`
- `sensor.eu08l_hp1_defrost_cycling_4h`
- `sensor.eu08l_hp2_heating_cycling_4h`
- `sensor.eu08l_hp2_hot_water_cycling_4h`
- `sensor.eu08l_hp2_cooling_cycling_4h`
- `sensor.eu08l_hp2_defrost_cycling_4h`

**Für 2 HPs werden insgesamt 40 Sensoren erstellt (5 Typen × 4 Modi × 2 HPs)**

### 6. Vorteile der Gesamtlösung

#### 6.1. Robustheit
- **Zentrale Flankenerkennung**: Alle Logik im Coordinator
- **Echte Entities**: Alle Sensoren sind echte Python-Entities
- **Reset-basierte Logik**: Einfache und verständliche Reset-Mechanismen
- **Fehlerbehandlung**: Graceful handling bei fehlenden Werten
- **Timing-Schutz**: Robuste Behandlung von Startup-Sequenzen

#### 6.2. Performance
- **Effiziente Flankenerkennung**: Nur bei echten Statuswechseln
- **Keine Template-Berechnungen**: Alle Sensoren sind echte Entities
- **Minimaler Ressourcenverbrauch**: Keine kontinuierlichen Polling-Operationen
- **Gleichzeitige Updates**: Alle Sensoren werden in einem Vorgang aktualisiert

#### 6.3. Wartbarkeit
- **Zentrale Definition**: Alle Sensoren in `const.py` definiert
- **Konsistente Namensgebung**: Verwendet `generate_sensor_names`
- **Klare Trennung**: Flankenerkennung, Reset-Logik und Entity-Management sind getrennt
- **Einfache Erweiterung**: Neue Zeiträume können einfach hinzugefügt werden

#### 6.4. Erweiterbarkeit
- **Neue Modi**: Einfache Erweiterung um neue Betriebsmodi
- **Neue Zeiträume**: Einfache Erweiterung um neue Reset-Zeiträume
- **Neue HPs**: Automatische Skalierung basierend auf Konfiguration
- **Neue Features**: Einfache Integration neuer Funktionen

## Fazit

Die neue Cycling-Sensor-Architektur bietet eine **deutlich vereinfachte, robuste und performante Lösung** für die Verfolgung von Betriebsmodus-Wechseln. Die Kombination aus:

- **Zentraler Flankenerkennung** im Coordinator mit Timing-Schutz
- **Echten Entities** für alle Sensor-Typen
- **Reset-basierter Logik** statt komplexer Template-Berechnungen
- **Gleichzeitiger Inkrementierung** aller Sensor-Typen
- **Automatischer Erstellung** basierend auf HP-Konfiguration
- **Konsistenter Namensgebung** mit `generate_sensor_names`
- **Robuster Fehlerbehandlung** für Startup-Sequenzen
