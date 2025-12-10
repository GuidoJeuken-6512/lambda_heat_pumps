# Compressor Start Cycling Sensor - Plan (ARCHIVED)

**Status**: ✅ **VOLLSTÄNDIG UMGESETZT**  
**Umsetzungsdatum**: 2025-01-XX  
**Release**: 2.0.0

## Übersicht

Dieser Plan wurde vollständig umgesetzt. Der `compressor_start` Cycling-Sensor wurde erfolgreich implementiert und ist Teil von Release 2.0.0.

## Original Plan (aus Cursor Plan-Modus)

**Plan-Name**: "Neuer Cycling-Sensor für START COMPRESSOR"

### Ziel

Neuer dedizierter Sensor `compressor_start` der nur bei echtem Compressor-Start (HP_STATE Wert 5 = "START COMPRESSOR") hochzählt.

## Umsetzung

### ✅ Implementierte Features

1. **Sensor-Templates in `const.py`**:
   - ✅ `compressor_start_cycling_total` - Gesamtanzahl aller Compressor-Starts
   - ✅ `compressor_start_cycling_daily` - Tägliche Compressor-Starts (resettet um Mitternacht)
   - ✅ `compressor_start_cycling_2h` - 2-Stunden Compressor-Starts (resettet alle 2 Stunden)
   - ✅ `compressor_start_cycling_4h` - 4-Stunden Compressor-Starts (resettet alle 4 Stunden)
   - ✅ `compressor_start_cycling_monthly` - Monatliche Compressor-Starts (resettet am 1. des Monats)
   - ⚠️ **Hinweis**: Kein Yesterday-Sensor (wie im Plan ursprünglich vorgesehen), aber monthly wurde zusätzlich implementiert

2. **Flankenerkennung in `coordinator.py`**:
   - ✅ Separate Flankenerkennung für HP_STATE Register (1002) implementiert
   - ✅ Erkennung: HP_STATE wechselt zu Wert 5 ("START COMPRESSOR")
   - ✅ Verwendet `_last_state` Dictionary für State-Tracking
   - ⚠️ **Hinweis**: Verwendet HP_STATE Register 1002 (nicht HP_OPERATING_STATE Register 1003) und Wert 5 (nicht State 2)

3. **Sensor-Erstellung in `sensor.py`**:
   - ✅ `LambdaCyclingSensor` Instanzen für compressor_start (total, daily, 2h, 4h, monthly)
   - ✅ Automatische Erstellung basierend auf HP-Konfiguration
   - ✅ Integration in bestehende Cycling-Sensor-Architektur

4. **Persistierung**:
   - ✅ Nutzt bestehende Persistierung über `RestoreEntity`
   - ✅ Offsets in `lambda_wp_config.yaml` unterstützt: `compressor_start_cycling_total`

5. **Übersetzungen**:
   - ✅ Deutsche und englische Übersetzungen hinzugefügt
   - ✅ Alle Sensor-Namen übersetzt

## Unterschiede zum Original-Plan

### Abweichungen (alle positiv):

1. **Register-Quelle**: 
   - **Plan**: HP_OPERATING_STATE Register 1003, State 2
   - **Umsetzung**: HP_STATE Register 1002, Wert 5 ✅ (korrekter Register)

2. **Sensor-Name**:
   - **Plan**: `compressor_cycle_start`
   - **Umsetzung**: `compressor_start` ✅ (konsistenter mit anderen Cycling-Sensoren)

3. **Zeiträume**:
   - **Plan**: total, daily, yesterday, 2h, 4h
   - **Umsetzung**: total, daily, 2h, 4h, monthly ✅ (monthly zusätzlich, yesterday weggelassen)

4. **Flankenerkennung**:
   - **Plan**: Erweiterung von `_detect_cycling_flank()`
   - **Umsetzung**: Separate Flankenerkennung für HP_STATE ✅ (sauberere Trennung)

## Geänderte Dateien

- ✅ `custom_components/lambda_heat_pumps/const.py` - Sensor-Templates hinzugefügt
- ✅ `custom_components/lambda_heat_pumps/coordinator.py` - HP_STATE Flankenerkennung implementiert
- ✅ `custom_components/lambda_heat_pumps/sensor.py` - Sensor-Erstellung
- ✅ `custom_components/lambda_heat_pumps/utils.py` - `increment_cycling_counter` erweitert
- ✅ `custom_components/lambda_heat_pumps/translations/de.json` - Deutsche Übersetzungen
- ✅ `custom_components/lambda_heat_pumps/translations/en.json` - Englische Übersetzungen
- ✅ `docs/CYCLING_SENSORS.md` - Dokumentation aktualisiert

## Tests

- ✅ Unit Tests für neue Cycling-Sensoren
- ✅ Tests für Flankenerkennung
- ✅ Tests für Persistierung

## Dokumentation

- ✅ Vollständig dokumentiert in `docs/CYCLING_SENSORS.md`
- ✅ Im CHANGELOG.md für Release 2.0.0 dokumentiert
- ✅ Im RELEASE_2.0.0_PLAN.md als Feature 4 dokumentiert

## Status

**🎉 PLAN VOLLSTÄNDIG UMGESETZT UND GETESTET**

Alle geplanten Features wurden implementiert, teilweise sogar erweitert (monthly Sensor). Der Sensor ist produktionsreif und Teil von Release 2.0.0.

---

**Archiviert am**: 2025-01-XX  
**Grund**: Plan vollständig umgesetzt, alle Features implementiert und getestet







