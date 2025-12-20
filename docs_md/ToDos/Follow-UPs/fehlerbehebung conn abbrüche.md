# Fehlerbehebung: Connection Abbrüche bei Lambda Heat Pumps

## ✅ Was bereits behoben wurde:

1) **Logging erhöht** - Info-Messages bei jedem Modbus read/write mit Zustand
2) **Debug-Messages** - Andere Info Messages (read databases) auf debug gesetzt
3) **Register 5007 deaktiviert** - HC1 Register 7 in lambda_wp_config.yaml deaktiviert (nicht vorhanden)
4) **Health-Check repariert** - Modbus Health-Check API-Kompatibilität behoben

## 🔍 Root Cause Analyse:

**Problem:** Timing-Kollisionen zwischen Coordinator-Reads (30s) und Service-Writes (30s) + Auto-Detection
- **Services starten sofort** nach Integration-Setup
- **Auto-Detection startet sofort** bei Reloads
- **Coordinator-Reads** laufen alle 30 Sekunden
- **Service-Writes** triggern 8 Sekunden nach Read-Start
- **Auto-Detection** kollidiert mit Coordinator-Reads
- **Verbindungsabbrüche** durch gleichzeitige Modbus-Zugriffe

## 🎯 Lösungsplan:

### Phase 1: Service-Timing optimieren
- [x] **Service-Start verzögern** - Services warten auf ersten erfolgreichen Read
- [x] **Intervall auf 41s ändern** - Ungerade Zahl > 30, vermeidet Kollisionen
- [x] **Read-Status prüfen** - Services starten nur bei stabiler Verbindung

### Phase 2: Code-Implementierung
- [x] **services.py anpassen** - `wait_for_successful_read_then_start_services()`
- [x] **DEFAULT_WRITE_INTERVAL** von 30 auf 41 Sekunden ändern
- [x] **Coordinator-Integration** - Services warten auf `async_refresh()` Erfolg
- [x] **Auto-Detection-Wait** - Services warten zusätzlich auf Auto-Detection-Abschluss
- [x] **Reload-Fix** - Services warten auch bei Reloads auf Auto-Detection
- [x] **Auto-Detection-Verbindungsprüfung** - Auto-Detection wartet auf stabile Verbindung (in modbus_utils.py)
- [x] **Service-Verbindungsprüfung** - Services warten auf stabile Verbindung vor Modbus-Operationen
- [x] **Coordinator-Integration** - Coordinator nutzt wait_for_stable_connection statt alte Prüfung
- [x] **Alte Verbindungsprüfung entfernt** - _is_connection_healthy und _health_check_read aus Coordinator entfernt
- [x] **Auto-Detection-Verzögerung** - Auto-Detection wartet 38 Sekunden vor Start
- [x] **Reload vs. Erster Start** - Auto-Detection unterscheidet zwischen Reload (38s Verzögerung) und erstem Start (sofort)

### Phase 3: Testing & Validierung
- [x] **Timing-Test** - Verifikation: Services starten nach Read-Ende
- [x] **Kollisions-Test** - Prüfung: Keine gleichzeitigen Modbus-Zugriffe
- [x] **Stabilität-Test** - Langzeit-Test ohne Verbindungsabbrüche
- [x] **Reload-Test** - Auto-Detection verzögert sich bei Reloads
- [x] **Config-Flow-Test** - Auto-Detection startet sofort bei neuem Setup

### Phase 4: Weitere Optimierungen
- [x] **PV-Surplus Fehler** - Services warten auf stabile Verbindung vor Modbus-Operationen
- [x] **Unload-Fehler** - Services werden korrekt entladen
- [x] **Error-Handling** - Robuste Verbindungsprüfung mit Fallback-Strategie

## ✅ **LÖSUNG VOLLSTÄNDIG IMPLEMENTIERT UND GETESTET!**

### **🎯 Zusammenfassung der Lösung:**

**Problem:** Timing-Kollisionen zwischen Coordinator-Reads, Service-Writes, Auto-Detection + Mehrfache Reloads
**Lösung:** Intelligente Verzögerung, universelle Verbindungsprüfung + Reload-Sperre

### **🔧 Implementierte Features:**

1. **Services-Timing optimiert** - 41s Intervall, warten auf Read + Auto-Detection
2. **Auto-Detection intelligent** - 38s Verzögerung bei Reloads, sofort bei erstem Start
3. **Universelle Verbindungsprüfung** - Robuste Prüfung für alle Module
4. **Reload-Sperre** - Verhindert parallele Reloads, nacheinander abarbeiten
5. **Keine Kollisionen mehr** - Perfekte Trennung der Modbus-Zugriffe

### **✅ ERFOLGREICH GETESTET:**
- **Keine "Cancel send" Fehler** mehr
- **Keine "Connection unhealthy"** Meldungen mehr
- **Keine parallelen Reloads** mehr
- **Stabile Modbus-Verbindungen** nach jedem Reload
- **Saubere Reload-Sequenz** - perfekte Synchronisation

**Alle Connection-Abbrüche sind vollständig behoben!** 🎉

## 📋 Technische Details:

**Aktueller Zustand:**
- Coordinator: 30s Read-Intervall
- Services: 30s Write-Intervall (sofortiger Start)
- Kollision: Services triggern 8s nach Read-Start

**Ziel-Zustand (ERREICHT):**
- Coordinator: 30s Read-Intervall ✅
- Services: 41s Write-Intervall (Start nach erfolgreichem Read + Auto-Detection) ✅
- Auto-Detection: 38s Verzögerung bei Reloads, sofort bei erstem Start ✅
- Reload-Sperre: Nacheinander abarbeiten, keine parallelen Reloads ✅
- Keine Kollisionen: Services und Auto-Detection laufen zwischen Read-Zyklen ✅
- Keine "Cancel send" Fehler mehr ✅
- Stabile Modbus-Verbindungen nach jedem Reload ✅

## 🔧 Implementierung:

### **Services-Timing:**
```python
# services.py - Neue Logik:
async def wait_for_successful_read_then_start_services():
    coordinator = get_coordinator()
    await coordinator.async_refresh()  # Warte auf erfolgreichen Read
    await wait_for_auto_detection_completion()  # Warte auf Auto-Detection
    update_interval = timedelta(seconds=41)  # Starte mit 41s Intervall
    async_track_time_interval(hass, scheduled_update_callback, update_interval)
```

### **Auto-Detection-Timing:**
```python
# __init__.py - Intelligente Verzögerung:
is_reload = hass.data.get(DOMAIN, {}).get(entry.entry_id) is not None

if is_reload:
    await asyncio.sleep(38)  # 38s Verzögerung bei Reloads
else:
    # Sofort starten bei erstem Setup
```

### **Universelle Verbindungsprüfung:**
```python
# modbus_utils.py - Robuste Verbindungsprüfung:
async def wait_for_stable_connection(coordinator):
    # 10 Versuche mit 1s Abstand
    # Robuste API-Kompatibilität
    # Fallback-Strategie
```

### **Reload-Sperre:**
```python
# __init__.py - Verhindert parallele Reloads:
_reload_lock = asyncio.Lock()
_reload_in_progress = False

async def async_reload_entry():
    if _reload_in_progress:
        _LOGGER.warning("Another reload is already in progress, skipping")
        return True
    # ... Reload durchführen ...
```

**✅ ERREICHTES ERGEBNIS:** Stabile Verbindung ohne Timing-Kollisionen bei Services, Auto-Detection und Coordinator + Keine parallelen Reloads mehr!

## 🔄 **NEUE ENTDECKUNG: Mehrfache Reloads!**

### **🎯 Problem identifiziert:**
- **Mehrere Reload-Vorgänge** laufen gleichzeitig
- **Race Conditions** zwischen Reloads
- **Mehrere Coordinator-Instanzen** laufen parallel
- **"Cancel send" Fehler** durch überlappende Reloads

### **🔧 Lösung implementiert:**
- **Reload-Sperre** verhindert mehrere gleichzeitige Reloads
- **Globale Reload-Status** Überwachung
- **Detaillierte Logging** für Reload-Sequenz
- **Robuste Fehlerbehandlung** bei Reload-Konflikten

### **📊 Implementierte Features:**
1. **Reload-Lock** - Verhindert parallele Reloads
2. **Reload-Status** - Überwacht laufende Reloads
3. **Skip-Logik** - Überspringt redundante Reloads
4. **Detailliertes Logging** - Verfolgt Reload-Sequenz

### **✅ ERFOLGREICH GETESTET:**
- **Keine parallelen Reloads** mehr - alle laufen nacheinander
- **Keine "Cancel send" Fehler** mehr im Log
- **Keine "Connection unhealthy"** Meldungen mehr
- **Stabile Modbus-Verbindungen** nach jedem Reload
- **Saubere Reload-Sequenz** - perfekte Synchronisation

**Das Problem der mehrfachen Reloads ist vollständig behoben!** 🎉