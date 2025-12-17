---
title: "Raumthermostat"
---

# Raumthermostat

Die Lambda Heat Pumps Integration unterstützt die Integration externer Raumthermostat-Sensoren für eine präzise Temperatursteuerung. Diese Funktion ermöglicht es, die Heizkurven-Vorlauftemperatur basierend auf der tatsächlichen Raumtemperatur anzupassen.

## Übersicht

Die Raumthermostat-Funktion verwendet externe Sensoren (z.B. von Home Assistant) als Eingabe für die Lambda-Wärmepumpe. Die Integration berechnet automatisch eine Anpassung der Vorlauftemperatur basierend auf der Differenz zwischen Soll- und Ist-Temperatur.

### Funktionsweise

1. **Externe Sensoren**: Verwenden Sie beliebige Temperatursensoren aus Home Assistant
2. **Automatische Berechnung**: Die Integration berechnet die Anpassung der Vorlauftemperatur
3. **Modbus-Schreiben**: Die berechnete Temperatur wird an die Lambda geschrieben
4. **Regelmäßige Updates**: Die Temperatur wird regelmäßig aktualisiert (standardmäßig alle 9 Sekunden)

## Aktivierung

### Schritt 1: Raumthermostat in den Optionen aktivieren

1. **Öffnen Sie Home Assistant:**
   - Gehen Sie zu **Einstellungen** → **Geräte & Dienste**
   - Suchen Sie nach Ihrer Lambda-Integration
   - Klicken Sie auf **Konfigurieren**

2. **Raumthermostat aktivieren:**
   - Aktivieren Sie die Option **Raumthermostat-Steuerung**
   - Klicken Sie auf **Weiter**

### Schritt 2: Sensoren auswählen

Für jeden Heizkreis müssen Sie einen Raumtemperatur-Sensor auswählen:

1. **Raumtemperatur-Sensor auswählen:**
   - Wählen Sie einen Sensor aus, der die aktuelle Raumtemperatur misst
   - **Beispiel**: `sensor.wohnzimmer_temperatur` oder `sensor.living_room_temperature`

2. **Für jeden Heizkreis:**
   - Wiederholen Sie den Vorgang für jeden konfigurierten Heizkreis (HC1, HC2, etc.)

3. **Konfiguration speichern:**
   - Klicken Sie auf **Absenden**

## Verfügbare Number-Entities

Nach der Aktivierung werden für jeden Heizkreis folgende Number-Entities erstellt:

### Raumthermostat-Offset

- **Entity-ID**: `number.*_hc1_room_thermostat_offset`
- **Bereich**: -10.0 bis +10.0
- **Schrittweite**: 0.1
- **Standardwert**: 0.0
- **Beschreibung**: Offset für die Raumtemperatur-Berechnung

### Raumthermostat-Faktor

- **Entity-ID**: `number.*_hc1_room_thermostat_factor`
- **Bereich**: 0.1 bis 5.0
- **Schrittweite**: 0.1
- **Standardwert**: 1.0
- **Beschreibung**: Faktor für die Raumtemperatur-Berechnung

## Berechnung der Vorlauftemperatur

Die Integration berechnet die Vorlauftemperatur in mehreren Schritten:

### 1. Grundwert aus Heizkurve

Zuerst wird der Grundwert aus der Heizkurve berechnet:

```
T_base = Interpolation zwischen Heizkurven-Stützpunkten
```

### 2. Flow-Line-Offset

Der Flow-Line-Offset wird hinzugefügt:

```
T_flow = T_base + Flow_Line_Offset
```

### 3. Raumthermostat-Anpassung

Wenn der Raumthermostat aktiviert ist, wird eine Anpassung berechnet:

```
Δ_RT = (T_soll - T_ist - Offset) * Faktor
T_final = T_flow + Δ_RT
```

**Beispiel:**
- Raum-Soll: 23.5°C
- Raum-Ist: 22.6°C
- Offset: 0.0
- Faktor: 1.0
- **Δ_RT** = (23.5 - 22.6 - 0.0) * 1.0 = 0.9°C
- **T_final** = T_flow + 0.9°C

## Konfiguration der Parameter

### Offset anpassen

Der Offset ermöglicht eine Feinabstimmung der Raumtemperatur-Berechnung:

- **Positiver Offset**: Erhöht die berechnete Anpassung
- **Negativer Offset**: Verringert die berechnete Anpassung
- **Standard**: 0.0 (keine Anpassung)

**Beispiel:**
- Wenn die Raumtemperatur konstant 0.5°C zu niedrig gemessen wird, können Sie einen Offset von -0.5 setzen

### Faktor anpassen

Der Faktor bestimmt, wie stark die Raumtemperatur-Differenz die Vorlauftemperatur beeinflusst:

- **Faktor 1.0**: Standard-Anpassung (1:1)
- **Faktor > 1.0**: Stärkere Anpassung (z.B. 2.0 = doppelte Anpassung)
- **Faktor < 1.0**: Schwächere Anpassung (z.B. 0.5 = halbe Anpassung)

**Beispiel:**
- Wenn die Raumtemperatur 1°C zu niedrig ist und der Faktor 2.0 ist, wird die Vorlauftemperatur um 2.0°C erhöht

## Beispiel-Konfiguration

### Automatisierung für automatische Temperaturanpassung

```yaml
automation:
  - alias: "Raumthermostat Offset anpassen"
    trigger:
      - platform: state
        entity_id: sensor.wohnzimmer_temperatur
    condition:
      - condition: numeric_state
        entity_id: sensor.wohnzimmer_temperatur
        below: 20
    action:
      - service: number.set_value
        target:
          entity_id: number.eu08l_hc1_room_thermostat_offset
        data:
          value: -0.5
```

## Häufige Probleme

### "Raumthermostat funktioniert nicht"
- **Ursache**: Raumthermostat nicht in den Optionen aktiviert
- **Lösung**: Aktivieren Sie die Raumthermostat-Steuerung in den Integration-Optionen

### "Sensor nicht gefunden"
- **Ursache**: Der ausgewählte Sensor existiert nicht oder ist nicht verfügbar
- **Lösung**: 
  - Überprüfen Sie, ob der Sensor in Home Assistant existiert
  - Wählen Sie einen anderen Sensor aus

### "Temperatur wird nicht aktualisiert"
- **Ursache**: Modbus-Verbindungsproblem oder Sensor nicht verfügbar
- **Lösung**: 
  - Überprüfen Sie die Modbus-Verbindung
  - Überprüfen Sie, ob der Sensor Werte liefert
  - Überprüfen Sie die Logs auf Fehlermeldungen

### "Vorlauftemperatur ändert sich zu stark"
- **Ursache**: Faktor zu hoch eingestellt
- **Lösung**: Reduzieren Sie den Raumthermostat-Faktor (z.B. von 2.0 auf 1.0)

### "Vorlauftemperatur ändert sich zu wenig"
- **Ursache**: Faktor zu niedrig eingestellt
- **Lösung**: Erhöhen Sie den Raumthermostat-Faktor (z.B. von 0.5 auf 1.0)

## Nächste Schritte

Nach der Einrichtung des Raumthermostats können Sie:

- [Stromverbrauchsberechnung](stromverbrauchsberechnung.md) einrichten
- [Historische Daten übernehmen](historische-daten.md) bei Wärmepumpenwechsel
- [Optionen des config_flow](optionen-config-flow.md) anpassen

