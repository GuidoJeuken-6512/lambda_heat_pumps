# Lambda Heat Pumps Integration - Ablaufdiagramm

Dieses Dokument zeigt den kompletten Ablauf der Lambda Heat Pumps Integration von der Initialisierung bis zum kontinuierlichen Betrieb.

## Hauptablauf

```mermaid
flowchart TD
    A[Home Assistant Start] --> B[async_setup]
    B --> C[Debug Logging Setup]
    C --> D[Config Entry Setup]
    
    D --> E[async_setup_entry]
    E --> F[Check if already loaded]
    F -->|Already loaded| G[Skip Setup]
    F -->|Not loaded| H[ensure_lambda_config]
    
    H --> I[Module Auto-Detection]
    I --> J[Create Coordinator]
    J --> K[Initialize Modbus Client]
    K --> L[Auto-detect Module Counts]
    L --> M[Update Config Entry]
    
    M --> N[Generate Base Addresses]
    N --> O[Create Main Coordinator]
    O --> P[Initialize Coordinator]
    P --> Q[First Data Refresh with Retry]
    
    Q --> R[Data Available?]
    R -->|No| S[Error - Setup Failed]
    R -->|Yes| T[Store Coordinator in hass.data]
    
    T --> U[Setup Platforms]
    U --> V[Setup Services]
    V --> V1[Check Existing Services]
    V1 -->|Services exist| V2[Stop Old Services]
    V1 -->|No services| V3[Setup New Services]
    V2 --> V3
    V3 --> V4[Setup Service Timers]
    V4 --> V5[Register Service Callbacks]
    V5 --> W[Setup Cycling Automations]
    W --> X[Add Update Listener]
    X --> Y[Setup Complete]
    
    %% Data Update Cycle
    Y --> Z[Coordinator Update Cycle]
    Z --> AA[Read Modbus Registers]
    AA --> BB[Process Raw Data]
    BB --> CC[Calculate Derived Values]
    CC --> CC1[Track Energy Consumption]
    CC1 --> CC2[Update Cycling Counters]
    CC2 --> CC3[Apply Energy Offsets]
    CC3 --> DD[Update Entity States]
    DD --> EE[Trigger Entity Updates]
    EE --> Z
    
    %% Service Update Cycle (parallel to data cycle)
    Y --> ZZ[Service Timer Cycle]
    ZZ --> AAA[Check Service Options]
    AAA --> BBB[Room Thermostat Control?]
    BBB -->|Yes| CCC[Write Room Temperature]
    BBB -->|No| DDD[Skip Room Temperature]
    CCC --> EEE[PV Surplus Control?]
    DDD --> EEE
    EEE -->|Yes| FFF[Write PV Surplus]
    EEE -->|No| GGG[Skip PV Surplus]
    FFF --> HHH[Wait 30 seconds]
    GGG --> HHH
    HHH --> ZZ
    
    %% Platform Setup Details
    U --> U1[Sensor Platform]
    U --> U2[Climate Platform]
    U1 --> U3[Create HP Sensors]
    U1 --> U4[Create Boiler Sensors]
    U1 --> U5[Create Buffer Sensors]
    U1 --> U6[Create Solar Sensors]
    U1 --> U7[Create HC Sensors]
    U1 --> U8[Create Calculated Sensors]
    U1 --> U9[Create Energy Consumption Sensors]
    U9 --> U9A[Heating Energy Total/Daily]
    U9 --> U9B[Hot Water Energy Total/Daily]
    U9 --> U9C[2H/4H Energy Sensors]
    U9 --> U9D[Monthly/Yearly Energy Sensors]
    
    %% Error Handling
    Q --> Q1[Max Retries Reached?]
    Q1 -->|Yes| S
    Q1 -->|No| Q2[Wait and Retry]
    Q2 --> Q
    
    %% Unload Process
    FF[async_unload_entry] --> GG[Cleanup Cycling Automations]
    GG --> HH[Unload Platforms]
    HH --> II[Shutdown Coordinator]
    II --> JJ[Remove from hass.data]
    JJ --> KK[Check if last entry]
    KK -->|Last entry| LL[Unload Services]
    KK -->|Not last| MM1[Skip Service Unload]
    LL --> LL1[Stop Service Timers]
    LL1 --> LL2[Clear Service Callbacks]
    LL2 --> LL3[Remove from hass.data]
    LL3 --> LL4[Unload Complete]
    MM1 --> LL4
    
    %% Reload Process
    MM[async_reload_entry] --> NN[Check Entry Valid]
    NN --> OO[Unload Current Entry]
    OO --> PP[Wait for Cleanup]
    PP --> QQ[Setup Entry Again]
    QQ --> Y
    
    %% Migration Process
    RR[async_migrate_entry] --> SS[Perform Structured Migration]
    SS --> TT[Migration Success?]
    TT -->|Yes| UU[Update Entry Version]
    TT -->|No| VV[Migration Failed]
    
    style A fill:#e1f5fe
    style Y fill:#c8e6c9
    style S fill:#ffcdd2
    style LL fill:#c8e6c9
    style VV fill:#ffcdd2
```

## Wichtige Funktionen in der Reihenfolge

### 1. **Initialisierung** (`async_setup`)
- **Zweck**: Grundlegende Integration einrichten
- **Funktionen**: 
  - Debug-Logging aktivieren
  - Integration in Home Assistant registrieren

### 2. **Config Entry Setup** (`async_setup_entry`)
- **Zweck**: Hauptkonfiguration der Integration
- **Funktionen**:
  - Prüfung ob bereits geladen
  - Lambda-Konfigurationsdatei sicherstellen (`lambda_wp_config.yaml`)
  - Modul-Auto-Detection mit Retry-Logik (3 Versuche)
  - Base-Adressen für verschiedene Gerätetypen generieren

### 3. **Coordinator Initialisierung**
- **Zweck**: Zentrale Datenverwaltung und Modbus-Kommunikation
- **Funktionen**:
  - Modbus-Client erstellen
  - Erste Datenabfrage mit Retry-Mechanismus (3 Versuche)
  - Update-Intervall konfigurieren (Standard: 30 Sekunden)
  - Daten in `hass.data` speichern

### 4. **Platform Setup**
- **Sensor Platform**: 
  - HP (Heat Pump) Sensoren
  - Boiler Sensoren
  - Buffer Sensoren
  - Solar Sensoren
  - HC (Heating Circuit) Sensoren
  - Berechnete Sensoren
  - **Energieverbrauch-Sensoren**:
    - Heating Energy (Total/Daily)
    - Hot Water Energy (Total/Daily)
    - 2H/4H Energy Sensoren
    - Monthly/Yearly Energy Sensoren
- **Climate Platform**: 
  - Klimasteuerung für Wärmepumpen

### 5. **Services & Automations**
- **Services**: 
  - **Timer-basierte Services**: Automatische Modbus-Writes alle 30 Sekunden
  - **Room Thermostat Control**: Schreiben von Raumtemperaturen in Modbus-Register
  - **PV Surplus Control**: Schreiben von PV-Überschuss-Daten in Modbus-Register
  - **Service-Management**: Automatisches Stoppen alter Services bei Reload
  - **Manuelle Services**: Direkte Steuerung der Wärmepumpen
- **Cycling Automations**: Automatisches Tracking von Heizzyklen

### 6. **Datenupdate-Zyklus** (kontinuierlich)
- **Zweck**: Regelmäßige Datenaktualisierung
- **Funktionen**:
  - Modbus-Register lesen
  - Rohdaten verarbeiten und validieren
  - Abgeleitete Werte berechnen (Energieverbrauch, Zyklen, etc.)
  - **Energieverbrauch tracken**:
    - Power Consumption aus Modbus-Registern lesen
    - Energie-Deltas berechnen (Heating/Hot Water)
    - Sensoren für verschiedene Zeiträume aktualisieren
    - Offsets für Reset-Zyklen anwenden
  - Entity-States aktualisieren
  - Home Assistant über Änderungen benachrichtigen

### 6.1. **Service-Update-Zyklus** (parallel zum Datenupdate)
- **Zweck**: Automatische Steuerung der Wärmepumpen
- **Funktionen**:
  - **Timer-basierte Ausführung**: Alle 30 Sekunden
  - **Room Thermostat Control**: 
    - Prüfung der Option in Config-Entry
    - Lesen der konfigurierten Raumtemperatur-Sensoren
    - Schreiben in Modbus-Register (Standard: 5004)
  - **PV Surplus Control**:
    - Prüfung der Option in Config-Entry
    - Lesen der konfigurierten PV-Power-Sensoren
    - Schreiben in Modbus-Register (Standard: 102)
    - Unterstützung für verschiedene Modi (INT16/UINT16)
  - **Fehlerbehandlung**: Graceful Degradation bei Modbus-Fehlern

### 7. **Migration** (`async_migrate_entry`)
- **Zweck**: Aktualisierung zwischen Integration-Versionen
- **Funktionen**:
  - Strukturierte Migration durchführen
  - Konfigurationseinträge aktualisieren
  - Kompatibilität sicherstellen

### 8. **Unload/Reload**
- **Unload** (`async_unload_entry`):
  - Cycling-Automationen aufräumen
  - Platforms entladen
  - Coordinator herunterfahren
  - **Service-Management**:
    - Prüfung ob letzter Eintrag
    - Stoppen aller Service-Timer
    - Löschen der Service-Callbacks
    - Entfernen aus hass.data
- **Reload** (`async_reload_entry`):
  - Eintrag validieren
  - Aktuellen Eintrag entladen
  - **Service-Cleanup**: Automatisches Stoppen alter Services
  - Neu einrichten

## Technische Details

### Modbus-Kommunikation
- **Protokoll**: Modbus TCP
- **Port**: Standard 502
- **Slave ID**: Standard 1
- **Update-Intervall**: 30 Sekunden (konfigurierbar)

### Fehlerbehandlung
- **Retry-Mechanismus**: 3 Versuche für kritische Operationen
- **Graceful Degradation**: Integration funktioniert auch bei teilweisen Fehlern
- **Logging**: Umfassendes Logging für Debugging

### Datenstruktur
- **Coordinator**: Zentrale Datenverwaltung
- **Entity Registry**: Home Assistant Entity-Management
- **Persistent Storage**: Zyklus- und Energiedaten werden gespeichert

## Konfigurationsdateien

- `lambda_wp_config.yaml`: Hauptkonfiguration der Wärmepumpen
- `cycle_energy_persist.json`: Persistente Speicherung von Zyklus- und Energiedaten
- `manifest.json`: Integration-Metadaten und Abhängigkeiten

## Service-Konfiguration

### Room Thermostat Control
- **Option**: `room_thermostat_control` in Config-Entry
- **Sensoren**: Konfigurierbare Raumtemperatur-Sensoren pro Heizkreis
- **Register**: Standard 5004 (konfigurierbar)
- **Format**: Temperatur in 0.1°C (z.B. 223 = 22.3°C)

### PV Surplus Control
- **Option**: `pv_surplus` in Config-Entry
- **Sensor**: Konfigurierbarer PV-Power-Sensor
- **Register**: Standard 102 (konfigurierbar)
- **Modi**:
  - **INT16**: Positive und negative Werte (2's Complement)
  - **UINT16**: Nur positive Werte
- **Einheit**: Watt (automatische Konvertierung von kW)

### Service-Management
- **Timer-Intervall**: 30 Sekunden (konfigurierbar)
- **Automatisches Cleanup**: Services werden beim Reload automatisch gestoppt
- **Fehlerbehandlung**: Graceful Degradation bei Modbus-Fehlern
- **Logging**: Umfassendes Info-Level Logging für Debugging

## Energieverbrauch-Sensoren Details

Die Integration erstellt automatisch verschiedene Energieverbrauch-Sensoren für jede Wärmepumpe:

### Sensor-Typen
- **Heating Energy**: Verbrauch für Heizbetrieb
- **Hot Water Energy**: Verbrauch für Warmwasserbereitung

### Zeiträume
- **Total**: Gesamtverbrauch (kumulativ)
- **Daily**: Täglicher Verbrauch (resettet täglich)
- **2H/4H**: 2- und 4-Stunden-Zyklen
- **Monthly**: Monatlicher Verbrauch (resettet monatlich)
- **Yearly**: Jährlicher Verbrauch (resettet jährlich)

### Funktionsweise
1. **Datenquelle**: Power Consumption Register aus Modbus
2. **Berechnung**: Energie-Deltas basierend auf Betriebsmodus (Heating/Hot Water)
3. **Tracking**: Kontinuierliche Verfolgung der Verbrauchswerte
4. **Reset**: Automatische Zurücksetzung basierend auf Zeiträumen
5. **Offsets**: Anwendung von Offsets für korrekte Reset-Zyklen

## Abhängigkeiten

- **pymodbus**: >= 3.6.0 (Modbus-Kommunikation)
- **Home Assistant**: Integration in das HA-Framework
- **asyncio**: Asynchrone Programmierung
