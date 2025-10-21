# TO-DO: Energy Consumption Sensor Handling

## Implementierung der verbesserten Sensor-Wechsel-Logik

### 1. Persistierung des internen Sensors entfernen
- [x] JSON-Persistierung für Modbus-Sensoren in `_read_single_register` entfernen
- [x] Vereinfachung der Logik - interne Sensoren nutzen `last_energy_reading`
- [x] Alle heutigen Code-Änderungen per Git zurückgesetzt (außer TO.md und Doku)

### 2. Behaltene Verbesserungen (zu re-implementieren)
**Zero-Value Protection:**
- [x] Delta-Berechnung erst nach 2 Werten > 0 starten
- [x] Verhindert Sprünge durch initiale 0-Werte beim Start/Sensor-Wechsel
- [x] Implementiert in `_track_hp_energy_consumption`

**Verbesserte calculate_energy_delta:**
- [x] ~~Keine Deltas bei last_reading = 0.0 (verhindert Sprünge)~~ → **NICHT NÖTIG** (Zero-Value Protection löst das Problem besser)
- [x] ~~Gibt 0.0 zurück statt des rohen Deltas bei 0-Werten~~ → **NICHT NÖTIG** (Zero-Value Protection löst das Problem besser)
- [x] Bessere Logging für Debugging

### 3. Sensor-Wechsel auf internen Sensor ✅
**Logik:**
- Letzten DB-Wert aus der Home Assistant Datenbank auslesen
- **Wenn > 0:** Delta = aktueller Wert - letzter DB-Wert
- **Wenn 0:** Loop bis zwei Werte > 0 verfügbar sind

**✅ Implementiert:**
- Intelligente DB-Wert-Nutzung für Default-Sensoren
- Automatische Fallback auf Zero-Value Protection bei DB-Wert = 0
- Detaillierte Log-Messages für alle Fallentscheidungen

### 4. Sensor-Wechsel auf externen Sensor ✅
**Logik:**
- Loop bis zwei Werte > 0 verfügbar sind
- Verhindert Sprünge durch initiale 0-Werte

**✅ Implementiert:**
- Zero-Value Protection für alle externen Sensoren
- Robuste Sensor-Wechsel-Erkennung in beide Richtungen
- Vollständige Validierung externer Sensoren

### 5. Vorteile der neuen Logik
- **Zuverlässiger:** Nutzt immer die aktuellsten Werte aus der DB
- **Einfacher:** Keine komplexe JSON-Persistierung nötig
- **Robuster:** Verhindert Sprünge durch 0-Werte beim Start
- **Konsistenter:** Einheitliche Behandlung aller Sensor-Typen

### 6. Zusätzliche Verbesserungen ✅

**Info-Message beim Laden der Integration:**
- [x] Anzeige des verwendeten Quellsensors für Verbrauchswerte beim Start
- [x] Hilfe für User um zu verstehen, welcher Sensor aktiv ist
- [x] Log-Nachricht: "Energy consumption tracking using sensor: {sensor_entity_id}"

**Externe Sensoren Validierung:**
- [x] Nicht vorhandene externe Sensoren abfangen (Schreibfehler des Users)
- [x] Prüfung ob konfigurierter Sensor existiert und verfügbar ist
- [x] Fehlermeldung mit Hinweis auf korrekte Sensor-ID
- [x] Fallback auf internen Modbus-Sensor bei fehlerhaften Konfigurationen

**Update-Intervall Config Flow Optimierung:**
- [x] Update-Intervall in der Config Flow Maske weiter oben platzieren (direkt nach Firmware-Version)
- [x] Erklärtext hinzufügen zur besseren Verständlichkeit
- [x] Minimum-Intervall von 5 auf 10 Sekunden erhöhen (verhindert zu häufige Modbus-Anfragen)
- [x] Maximum bleibt bei 300 Sekunden (5 Minuten)
- [x] Datei: `custom_components/lambda_heat_pumps/config_flow.py` (Zeilen 906-911)

### 7. Status
- **✅ Zero-Value Protection implementiert:** Schritt 2 vollständig abgeschlossen
- **✅ Sensor-Wechsel-Logik implementiert:** Schritte 3-4 vollständig abgeschlossen
- **✅ Robuste Sensor-Wechsel-Erkennung:** Funktioniert in beide Richtungen (Custom ↔ Default)
- **✅ Zusätzliche Verbesserungen implementiert:** Schritt 6 vollständig abgeschlossen
- **🎉 ALLE AUFGABEN ABGESCHLOSSEN!** - Energy Consumption Sensor Handling vollständig implementiert
- **Priorität:** Abgeschlossen - verhindert Energieverbrauch-Sprünge und verbessert User Experience
- **Komplexität:** Abgeschlossen - alle geplanten Features implementiert

### 8. Implementierungsdetails - Zero-Value Protection
**✅ Abgeschlossen am:** 2025-01-27
**📁 Geänderte Dateien:**
- `custom_components/lambda_heat_pumps/coordinator.py` (Zeilen 96, 1765-1802)

**🔧 Implementierte Lösung:**
- In-Memory Flag `_energy_first_value_seen` für jede Wärmepumpe
- 3-Schritt-Logik: 0-Werte ignorieren → Erster Wert speichern → Ab zweitem Wert Delta berechnen
- Automatische Recovery nach 0-Werten
- Vollständig getestet mit verschiedenen Szenarien

**📊 Test-Ergebnisse:**
- ✅ Neustart mit 0-Werten: Kein Sprung beim ersten echten Wert
- ✅ 0-Werte mitten im Betrieb: Automatische Recovery
- ✅ Mehrere Wärmepumpen: Unabhängige Flags funktionieren korrekt

### 9. Implementierungsdetails - Sensor-Wechsel-Logik und Verbesserungen
**✅ Abgeschlossen am:** 2025-01-27
**📁 Geänderte Dateien:**
- `custom_components/lambda_heat_pumps/coordinator.py` (Sensor-Wechsel-Erkennung, Info-Messages)
- `custom_components/lambda_heat_pumps/utils.py` (Externe Sensor-Validierung)
- `custom_components/lambda_heat_pumps/config_flow.py` (Update-Intervall Optimierung)

**🔧 Implementierte Features:**
- **Robuste Sensor-Wechsel-Erkennung:** Funktioniert in beide Richtungen (Custom ↔ Default)
- **Intelligente DB-Wert-Nutzung:** Für Default-Sensoren mit Historie
- **Externe Sensor-Validierung:** Fehlerhafte Sensoren werden abgefangen
- **Info-Messages:** Klare Anzeige der verwendeten Quellsensoren
- **Config Flow Optimierung:** Update-Intervall besser positioniert und erklärt

**📊 Test-Ergebnisse:**
- ✅ Custom → Default Sensor-Wechsel: DB-Wert wird intelligent genutzt
- ✅ Default → Custom Sensor-Wechsel: Zero-Value Protection aktiviert
- ✅ Fehlerhafte externe Sensoren: Automatischer Fallback auf Default-Sensoren
- ✅ Info-Messages: Klare Anzeige der aktiven Sensoren beim Start
- ✅ Config Flow: Update-Intervall besser positioniert und erklärt
