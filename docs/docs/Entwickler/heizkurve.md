---
title: "Heizkurve"
---

# Heizkurve

Die Lambda Heat Pumps Integration unterstützt die Konfiguration von Heizkurven für jeden Heizkreis. Die Heizkurve bestimmt die Vorlauftemperatur basierend auf der Außentemperatur und ermöglicht eine energieeffiziente und komfortable Heizungssteuerung.

## Übersicht

Die Heizkurven-Funktion verwendet drei Stützpunkte, um die Vorlauftemperatur in Abhängigkeit von der Außentemperatur zu berechnen. Die Integration interpoliert linear zwischen diesen Stützpunkten und berücksichtigt zusätzliche Einflussfaktoren wie Flow-Line-Offset, Raumthermostat-Anpassung und ECO-Modus.

![Heizkurven-Konfiguration](../assets/Integration_Heizkurve_de.png)

## Funktionsweise

Die Heizkurven-Berechnung erfolgt in mehreren Schritten:

1. **Lineare Interpolation**: Basierend auf der aktuellen Außentemperatur wird zwischen den drei Stützpunkten interpoliert
2. **Flow-Line-Offset**: Ein manueller Offset kann hinzugefügt werden
3. **Raumthermostat-Anpassung**: Bei aktiviertem Raumthermostat wird die Vorlauftemperatur basierend auf der Raumtemperatur angepasst
4. **ECO-Modus**: Im ECO-Modus wird eine Temperaturreduktion angewendet

## Heizkurven-Stützpunkte

Für jeden Heizkreis stehen drei Number-Entities zur Verfügung, die die Heizkurven-Stützpunkte definieren:

### Kaltpunkt (-22°C)

- **Entity-ID**: `number.*_hc1_heating_curve_cold_outside_temp`
- **Bereich**: 15.0 bis 75.0 °C
- **Schrittweite**: 0.1 °C
- **Standardwert**: 48.3 °C
- **Beschreibung**: Vorlauftemperatur bei einer Außentemperatur von -22°C

### Mittelpunkt (0°C)

- **Entity-ID**: `number.*_hc1_heating_curve_mid_outside_temp`
- **Bereich**: 15.0 bis 75.0 °C
- **Schrittweite**: 0.1 °C
- **Standardwert**: 39.0 °C
- **Beschreibung**: Vorlauftemperatur bei einer Außentemperatur von 0°C

### Warmpunkt (+22°C)

- **Entity-ID**: `number.*_hc1_heating_curve_warm_outside_temp`
- **Bereich**: 15.0 bis 75.0 °C
- **Schrittweite**: 0.1 °C
- **Standardwert**: 32.0 °C
- **Beschreibung**: Vorlauftemperatur bei einer Außentemperatur von +22°C

**Hinweis**: Die Entity-IDs variieren je nach Konfiguration (Legacy-Modus oder Standard-Modus) und Name-Präfix.

## Berechnung der Vorlauftemperatur

Die Integration berechnet die Vorlauftemperatur automatisch basierend auf folgenden Faktoren:

### 1. Grundwert aus Heizkurve

Zuerst wird der Grundwert durch lineare Interpolation zwischen den Stützpunkten berechnet:

- **Außentemperatur ≥ +22°C**: Verwendet den Warmpunkt-Wert
- **Außentemperatur zwischen 0°C und +22°C**: Interpoliert zwischen Mittelpunkt und Warmpunkt
- **Außentemperatur zwischen -22°C und 0°C**: Interpoliert zwischen Kaltpunkt und Mittelpunkt
- **Außentemperatur ≤ -22°C**: Verwendet den Kaltpunkt-Wert

**Beispiel**: Bei einer Außentemperatur von 10.7°C und den Standardwerten:
- Mittelpunkt (0°C): 39.0°C
- Warmpunkt (+22°C): 32.0°C
- **Interpolierter Wert**: ≈ 35.6°C

### 2. Flow-Line-Offset

Ein manueller Offset kann über die Number-Entity `number.*_hc1_flow_line_offset_temperature` hinzugefügt werden:

- **Bereich**: -10.0 bis +10.0 °C
- **Standardwert**: 0.0 °C
- **Verwendung**: Für manuelle Anpassungen der Vorlauftemperatur

Weitere Informationen: [Vorlauf Offset](lambda-wp-config.md#6-modbus-konfiguration)

### 3. Raumthermostat-Anpassung

Wenn die Raumthermostat-Steuerung aktiviert ist, wird die Vorlauftemperatur basierend auf der Differenz zwischen Soll- und Ist-Raumtemperatur angepasst:

```
Anpassung = (Soll-Temperatur - Ist-Temperatur - Offset) × Faktor
```

Weitere Informationen: [Raumthermostat](raumthermostat.md)

### 4. ECO-Modus

Wenn der Heizkreis im ECO-Modus (operating_state = 1) ist, wird eine Temperaturreduktion angewendet:

- **Entity-ID**: `number.*_hc1_eco_temp_reduction`
- **Bereich**: -10.0 bis 0.0 °C
- **Standardwert**: -1.0 °C
- **Beschreibung**: Temperaturreduktion im ECO-Modus

Die ECO-Temperaturreduktion wird zur berechneten Vorlauftemperatur addiert (negativer Wert = Reduktion).

## Konfiguration

### Heizkurven-Stützpunkte anpassen

1. **Öffnen Sie Home Assistant:**
   - Gehen Sie zu **Einstellungen** → **Geräte & Dienste**
   - Suchen Sie nach Ihrer Lambda-Integration
   - Klicken Sie auf das Gerät für den gewünschten Heizkreis

2. **Heizkurven-Stützpunkte finden:**
   - Suchen Sie nach den Number-Entities:
     - `Heizkurve-22°C` (Kaltpunkt)
     - `Heizkurve+-0°C` (Mittelpunkt)
     - `Heizkurve+22°C` (Warmpunkt)

3. **Werte anpassen:**
   - Klicken Sie auf die jeweilige Number-Entity
   - Passen Sie den Wert an Ihre Anforderungen an
   - Die Änderung wird sofort übernommen

### Empfohlene Einstellungen

Die optimalen Heizkurven-Werte hängen von verschiedenen Faktoren ab:

- **Gebäudeart**: Altbau benötigt höhere Temperaturen als Neubau
- **Heizsystem**: Fußbodenheizung benötigt niedrigere Temperaturen als Radiatoren
- **Dämmung**: Gut gedämmte Gebäude benötigen niedrigere Temperaturen
- **Komfort**: Höhere Werte = wärmer, aber mehr Energieverbrauch

**Beispiel-Konfiguration für ein gut gedämmtes Haus mit Fußbodenheizung:**
- Kaltpunkt (-22°C): 35.0°C
- Mittelpunkt (0°C): 28.0°C
- Warmpunkt (+22°C): 22.0°C

**Beispiel-Konfiguration für ein Altbau mit Radiatoren:**
- Kaltpunkt (-22°C): 55.0°C
- Mittelpunkt (0°C): 45.0°C
- Warmpunkt (+22°C): 35.0°C

## Berechneter Sensor

Die Integration erstellt automatisch einen Sensor, der die berechnete Vorlauftemperatur anzeigt:

- **Entity-ID**: `sensor.*_hc1_heating_curve_flow_line_temperature_calc`
- **Name**: "Heizkurve Vorlauf ber."
- **Einheit**: °C
- **Aktualisierung**: Automatisch bei Änderungen der Außentemperatur oder Heizkurven-Stützpunkte

Dieser Sensor zeigt die final berechnete Vorlauftemperatur nach allen Anpassungen (Heizkurve, Flow-Line-Offset, Raumthermostat, ECO-Modus).

## Feineinstellung

### Flow-Line-Offset verwenden

Der Flow-Line-Offset eignet sich für:
- **Temporäre Anpassungen**: Kurzfristige Erhöhung oder Reduzierung der Vorlauftemperatur
- **Feineinstellung**: Kleine Korrekturen ohne Änderung der Heizkurven-Stützpunkte
- **Saisonale Anpassungen**: Anpassung für Übergangszeiten

**Beispiel**: Wenn die Heizung etwas zu kalt ist, können Sie einen Flow-Line-Offset von +2.0°C setzen, ohne die gesamte Heizkurve zu ändern.

### ECO-Modus nutzen

Der ECO-Modus reduziert die Vorlauftemperatur, um Energie zu sparen:

- **Aktivierung**: Automatisch, wenn der Heizkreis im ECO-Betriebszustand ist
- **Konfiguration**: Über die Number-Entity `eco_temp_reduction`
- **Empfehlung**: -1.0°C bis -3.0°C für moderate Energieeinsparung

**Hinweis**: Eine zu starke Reduktion kann den Komfort beeinträchtigen.

## Überwachung und Logging

Die Integration protokolliert die Heizkurven-Berechnung im Home Assistant Log:

```
Heizkurven-Wert sensor.eu08l_hc1_heating_curve_flow_line_temperature_calc: 
ambient=10.70°C, y_cold=48.30°C, y_mid=39.00°C, y_warm=32.00°C, 
interpolated=35.60°C, flow_offset=0.00°C, rt_enabled=True, 
delta=0.90°C, offset=0.00, factor=1.00, adjustment=0.90°C, 
eco_reduction=0.00°C (op_state=0) -> 36.50°C
```

Die Log-Meldung zeigt:
- **ambient**: Aktuelle Außentemperatur
- **y_cold, y_mid, y_warm**: Heizkurven-Stützpunkte
- **interpolated**: Ergebnis der linearen Interpolation
- **flow_offset**: Flow-Line-Offset
- **adjustment**: Raumthermostat-Anpassung
- **eco_reduction**: ECO-Temperaturreduktion
- **op_state**: Betriebszustand des Heizkreises
- **-> result**: Finale berechnete Vorlauftemperatur

## Tipps und Best Practices

### Heizkurve optimieren

1. **Start mit Standardwerten**: Beginnen Sie mit den Standardwerten und passen Sie schrittweise an
2. **Beobachten Sie den Verbrauch**: Überwachen Sie den Energieverbrauch bei verschiedenen Einstellungen
3. **Komfort prüfen**: Stellen Sie sicher, dass die Raumtemperatur den gewünschten Wert erreicht
4. **Saisonal anpassen**: Passen Sie die Heizkurve für Winter und Übergangszeiten an

### Fehlerbehebung

**Problem**: Vorlauftemperatur ist zu niedrig
- **Lösung**: Erhöhen Sie die Heizkurven-Stützpunkte oder verwenden Sie einen positiven Flow-Line-Offset

**Problem**: Vorlauftemperatur ist zu hoch
- **Lösung**: Reduzieren Sie die Heizkurven-Stützpunkte oder verwenden Sie einen negativen Flow-Line-Offset

**Problem**: Heizkurve reagiert nicht auf Außentemperatur
- **Lösung**: Überprüfen Sie, ob der Außentemperatur-Sensor korrekt funktioniert

## Weitere Informationen

- [Raumthermostat](raumthermostat.md) - Integration externer Raumthermostat-Sensoren
- [lambda_wp_config.yaml Konfiguration](lambda-wp-config.md) - Erweiterte Konfigurationsoptionen
- [Technische Berechnungsdetails](../../docs_md/HEATING_CURVE_CALCULATION.md) - Detaillierte Beschreibung der Berechnungslogik

