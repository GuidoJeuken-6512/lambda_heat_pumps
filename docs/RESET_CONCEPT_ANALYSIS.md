# Reset-Konzept Analyse für Lambda Heat Pumps Integration

## Übersicht der aktuellen Reset-Architektur

### 1. **Warum drei Einträge pro Sensor-Typ?**

**Aktuell:** Jeder Sensor-Typ (heating, hot_water, cooling, defrost) hat **drei Varianten**:
- `_daily` - Reset täglich um Mitternacht
- `_2h` - Reset alle 2 Stunden  
- `_4h` - Reset alle 4 Stunden

**Grund:** Verschiedene Zeiträume für statistische Auswertungen:
- **Daily**: Tagesstatistiken (z.B. "Wie oft hat die WP heute geheizt?")
- **2H**: Kurzfristige Trends (z.B. "Wie aktiv war die WP in den letzten 2h?")
- **4H**: Mittelfristige Trends (z.B. "Wie war das Verhalten über 4h?")

### 2. **Ist das Konstrukt generisch?**

**JA** - Das System ist bereits generisch aufgebaut:

#### **A) Template-basierte Konfiguration:**
```python
# In const.py - Jeder Sensor hat Reset-Attribute:
"heating_cycling_daily": {
    "operating_state": "heating",
    "period": "daily",
    "reset_interval": "daily",
    "reset_signal": "lambda_heat_pumps_reset_daily",
    # ...
}
```

#### **B) Dynamische Signal-Erstellung:**
```python
# In utils.py
def create_reset_signal(sensor_type: str, period: str) -> str:
    """Erstellt standardisiertes Reset-Signal"""
    return f"lambda_heat_pumps_reset_{period}"
```

#### **C) Zentrale Registry:**
```python
# In utils.py
class SensorResetRegistry:
    def register(self, sensor_type: str, entry_id: str, period: str, callback)
    def send_reset(self, sensor_type: str, period: str, entry_id: str = None)
```

### 3. **Kann man einen 10:00 Uhr Reset-Sensor hinzufügen?**

**JA** - Das System ist erweiterbar:

#### **Schritt 1: Neues Signal definieren**
```python
# In automations.py
SIGNAL_RESET_10H = "lambda_heat_pumps_reset_10h"
```

#### **Schritt 2: Automation erstellen**
```python
# In automations.py
@callback
async def reset_10h_sensors(hass: HomeAssistant, entry_id: str):
    """10:00 Uhr Reset der 10H-Sensoren"""
    async_dispatcher_send(hass, SIGNAL_RESET_10H, entry_id)

# Zeit-basierte Automation
async def setup_time_based_automations(hass: HomeAssistant, entry_id: str):
    # ... bestehende Automations ...
    
    # 10:00 Uhr Reset
    hass.helpers.event.async_track_time_change(
        reset_10h_sensors, hour=10, minute=0, second=0
    )
```

#### **Schritt 3: Sensor-Template erweitern**
```python
# In const.py
"heating_cycling_10h": {
    "operating_state": "heating",
    "period": "10h",
    "reset_interval": "10h",
    "reset_signal": "lambda_heat_pumps_reset_10h",
    "description": "10-Stunden Cycling-Zähler für Heizen, werden täglich um 10:00 Uhr auf 0 gesetzt.",
}
```

#### **Schritt 4: Sensor-Implementierung erweitern**
```python
# In sensor.py - LambdaCyclingSensor
async def async_added_to_hass(self):
    # ... bestehende Handler ...
    
    if self._sensor_id.endswith("_10h"):
        self._unsub_10h_dispatcher = async_dispatcher_connect(
            self.hass, SIGNAL_RESET_10H, self._handle_10h_reset
        )

@callback
def _handle_10h_reset(self, entry_id: str):
    """Handle 10h reset signal."""
    if entry_id == self._entry.entry_id and self._sensor_id.endswith("_10h"):
        self._cycling_value = 0
        self.async_write_ha_state()
        _LOGGER.info(f"10H sensor {self.entity_id} reset to 0")
```

### 4. **Können "alle" Sensoren die Reset Timer nutzen?**

**JA** - Das System ist universell einsetzbar:

#### **A) Bereits implementiert:**
- ✅ **Cycling Sensoren** (heating, hot_water, cooling, defrost)
- ✅ **Energy Consumption Sensoren** (daily, 2h, 4h)

#### **B) Erweiterbar für:**
- ✅ **Beliebige Template-Sensoren** (LambdaTemplateSensor)
- ✅ **Custom Sensoren** (durch Registry-Registrierung)
- ✅ **Externe Sensoren** (durch Signal-Abonnement)

#### **C) Universelle Registrierung:**
```python
# Jeder Sensor kann sich registrieren:
register_sensor_reset_handler(
    hass=hass,
    sensor_type="custom",
    entry_id=entry_id,
    period="daily",
    callback=my_reset_callback
)
```

### 5. **Sind die Funktionen zentralisiert/generalisiert?**

**JA** - Das System ist vollständig zentralisiert:

#### **A) Zentrale Komponenten:**
- **`SensorResetRegistry`** - Zentrale Verwaltung aller Reset-Handler
- **`create_reset_signal()`** - Standardisierte Signal-Erstellung
- **`send_reset_signal()`** - Zentrale Signal-Verteilung
- **`automations.py`** - Zentrale Zeit-basierte Automations

#### **B) Generische Funktionen:**
- **Template-basierte Konfiguration** - Alle Reset-Parameter in `const.py`
- **Dynamische Signal-Erstellung** - Keine hardcodierten Signale
- **Universelle Registry** - Jeder Sensor-Typ kann registriert werden
- **Flexible Zeit-Intervalle** - Beliebig erweiterbar

#### **C) Einheitliche API:**
```python
# Für alle Sensor-Typen gleich:
register_sensor_reset_handler(hass, sensor_type, entry_id, period, callback)
send_reset_signal(sensor_type, period, entry_id)
```

## Fazit

Das Reset-System ist **vollständig generisch und erweiterbar**:

1. ✅ **Template-basiert** - Alle Konfiguration in `const.py`
2. ✅ **Zentralisiert** - Einheitliche Registry und Signal-Verteilung
3. ✅ **Erweiterbar** - Neue Zeit-Intervalle einfach hinzufügbar
4. ✅ **Universell** - Alle Sensor-Typen können Reset nutzen
5. ✅ **Wartbar** - Keine Code-Duplikation, einheitliche API

**Ein 10:00 Uhr Reset-Sensor kann problemlos hinzugefügt werden, ohne das bestehende System zu beeinträchtigen.**

