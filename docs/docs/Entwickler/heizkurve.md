---
title: "Heizkurve"
---

# Heizkurve

Die Lambda Heat Pumps Integration unterstützt die Konfiguration von Heizkurven für jeden Heizkreis. Die Heizkurve bestimmt die Vorlauftemperatur basierend auf der Außentemperatur und ermöglicht eine energieeffiziente und komfortable Heizungssteuerung.

## Übersicht

Die Heizkurven-Funktion verwendet drei Stützpunkte, um die Vorlauftemperatur in Abhängigkeit von der Außentemperatur zu berechnen. Die Integration interpoliert linear zwischen diesen Stützpunkten und berücksichtigt zusätzliche Einflussfaktoren wie Flow-Line-Offset, Raumthermomenter-Anpassung und ECO-Modus.

![Heizkurven-Konfiguration](../assets/Integration_Heizkurve_de.png)

## Funktionsweise

Die Heizkurven-Berechnung erfolgt in mehreren Schritten:

1. **Lineare Interpolation**: Basierend auf der aktuellen Außentemperatur wird zwischen den drei Stützpunkten interpoliert
2. **Flow-Line-Offset**: Ein manueller Offset kann hinzugefügt werden
3. **Raumthermomenter-Anpassung**: Bei aktiviertem Raumthermomenter wird die Vorlauftemperatur basierend auf der Raumtemperatur angepasst
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


### 3. Raumthermomenter-Anpassung

Wenn die Raumthermomenter-Steuerung aktiviert ist, wird die Vorlauftemperatur basierend auf der Differenz zwischen Soll- und Ist-Raumtemperatur angepasst:

```
Anpassung = (Soll-Temperatur - Ist-Temperatur - Offset) × Faktor
```

Weitere Informationen: [Raumthermomenter](https://guidojeuken-6512.github.io/lambda_heat_pumps/Anwender/raumthermometer/)

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


## Berechneter Sensor

Die Integration erstellt automatisch einen Sensor, der die berechnete Vorlauftemperatur anzeigt:

- **Entity-ID**: `sensor.*_hc1_heating_curve_flow_line_temperature_calc`
- **Name**: "Heizkurve Vorlauf ber."
- **Einheit**: °C
- **Aktualisierung**: Automatisch bei Änderungen der Außentemperatur oder Heizkurven-Stützpunkte

Dieser Sensor zeigt die final berechnete Vorlauftemperatur nach allen Anpassungen (Heizkurve, Flow-Line-Offset, Raumthermomenter, ECO-Modus).

### Aus welchen Werten wird die Entity berechnet?

Die Entity `sensor.*_hc1_heating_curve_flow_line_temperature_calc` wird in der Klasse **LambdaHeatingCurveCalcSensor** (`template_sensor.py`) berechnet. Verwendet werden:

| Schritt | Quelle | Beschreibung |
|--------|--------|--------------|
| **1. Außentemperatur** | `sensor.*_ambient_temperature_calculated` | Aktuelle Außentemperatur (X für die Heizkurve). |
| **2. Stützpunkte (Y)** | `number.*_hc1_heating_curve_cold_outside_temp` | Vorlauf bei -22 °C (Kaltpunkt). |
| | `number.*_hc1_heating_curve_mid_outside_temp` | Vorlauf bei 0 °C (Mittelpunkt). |
| | `number.*_hc1_heating_curve_warm_outside_temp` | Vorlauf bei +22 °C (Warmpunkt). |
| **3. Stützpunkte (X)** | fest | Kalt = -22 °C, Mitte = 0 °C, Warm = +22 °C. |
| **4. Grundwert** | berechnet | Lineare Interpolation zwischen den Stützpunkten: *y = y_a + (x − x_a) × (y_b − y_a) / (x_b − x_a)*. Bei Außentemperatur ≥ +22 °C wird der Warmpunkt-Wert verwendet, bei ≤ -22 °C der Kaltpunkt-Wert. |
| **5. Flow-Line-Offset** | Coordinator-Daten `hc{idx}_set_flow_line_offset_temperature` | Wird zum interpolierten Wert addiert (z. B. aus Number-Entity `number.*_hc1_flow_line_offset_temperature` / Modbus). |
| **6. Raumthermostat** (wenn aktiviert) | `number.*_hc1_room_thermostat_offset`, `number.*_hc1_room_thermostat_factor` | Offset und Faktor für die Raumtemperatur-Anpassung. |
| | Coordinator `hc{idx}_room_device_temperature`, `hc{idx}_target_room_temperature` | Ist- und Soll-Raumtemperatur. **Anpassung** = (Soll − Ist − Offset) × Faktor, wird zum Zwischenergebnis addiert. |
| **7. ECO-Modus** (wenn operating_state = 1) | Coordinator `hc{idx}_operating_state` | Wert 1 = ECO aktiv. |
| | `number.*_hc1_eco_temp_reduction` | Temperaturreduktion (z. B. -1 °C), wird addiert. |
| **8. Endergebnis** | — | Auf die konfigurierte Nachkommastelle gerundet (z. B. 1 Dezimalstelle). |

*Hinweis:* `*` steht für deinen Geräte-/Namenspräfix (z. B. `eu08l`), `hc1` für Heizkreis 1 (bei mehreren Heizkreisen `hc2` usw.).

## Template-Sensor ohne Lambda-Integration (Standalone)

Wenn Sie Home Assistant nutzen, aber **nicht** diese Lambda-Integration (z. B. andere Wärmepumpe oder manuelle Heizungssteuerung), können Sie die gleiche Heizkurven-Berechnung mit einem **Template-Sensor** nachbilden. Der Sensor berechnet die Vorlauftemperatur aus der Außentemperatur und drei Stützpunkten (lineare Interpolation wie oben).

### Voraussetzungen

- Ein **Sensor für die Außentemperatur** (z. B. `sensor.outside_temperature` oder `sensor.weather_temperature`).
- Drei Werte für die Heizkurven-Stützpunkte:
  - **Kaltpunkt (-22 °C):** Vorlauftemperatur bei -22 °C Außentemperatur (z. B. 50 °C).
  - **Mittelpunkt (0 °C):** Vorlauftemperatur bei 0 °C (z. B. 41 °C).
  - **Warmpunkt (+22 °C):** Vorlauftemperatur bei +22 °C (z. B. 35 °C).

Diese Werte können fest im Template stehen oder aus **Input-Number**-Helfern kommen (dann sind sie im UI änderbar).

### Variante A: Feste Stützpunkte im Template

In **Einstellungen** → **Geräte & Dienste** → **Helfer** → **Template-Sensor** einen neuen Sensor anlegen, oder in `configuration.yaml` unter `template:` einbinden:

```yaml
# configuration.yaml (Ausschnitt)
template:
  - sensor:
      - name: "Heizkurve Vorlauf berechnet"
        unique_id: heating_curve_flow_standalone
        unit_of_measurement: "°C"
        state: >
          {% set t = states('sensor.outside_temperature') | float(10) %}
          {% set y_cold = 50.0 %}
          {% set y_mid = 41.0 %}
          {% set y_warm = 35.0 %}
          {% set x_cold = -22 %}
          {% set x_mid = 0 %}
          {% set x_warm = 22 %}
          {% if t >= x_warm %}
            {{ y_warm | round(1) }}
          {% elif t > x_mid %}
            {{ (y_mid + (t - x_mid) * (y_warm - y_mid) / (x_warm - x_mid)) | round(1) }}
          {% elif t > x_cold %}
            {{ (y_cold + (t - x_cold) * (y_mid - y_cold) / (x_mid - x_cold)) | round(1) }}
          {% else %}
            {{ y_cold | round(1) }}
          {% endif %}
```

- **`sensor.outside_temperature`** durch Ihre Außentemperatur-Entity ersetzen.
- **`y_cold`, `y_mid`, `y_warm`** (50, 41, 35) nach Bedarf anpassen.

### Variante B: Stützpunkte aus Input-Number-Helfern

Zuerst drei **Helfer** → **Zahl** anlegen (z. B. `input_number.heating_curve_cold`, `input_number.heating_curve_mid`, `input_number.heating_curve_warm`) mit Min/Max z. B. 15–75 °C und gewünschten Standardwerten. Dann den Template-Sensor so definieren, dass er diese Entities liest:

```yaml
template:
  - sensor:
      - name: "Heizkurve Vorlauf berechnet"
        unique_id: heating_curve_flow_standalone
        unit_of_measurement: "°C"
        state: >
          {% set t = states('sensor.outside_temperature') | float(10) %}
          {% set y_cold = states('input_number.heating_curve_cold') | float(50) %}
          {% set y_mid = states('input_number.heating_curve_mid') | float(41) %}
          {% set y_warm = states('input_number.heating_curve_warm') | float(35) %}
          {% set x_cold = -22 %}
          {% set x_mid = 0 %}
          {% set x_warm = 22 %}
          {% if t >= x_warm %}
            {{ y_warm | round(1) }}
          {% elif t > x_mid %}
            {{ (y_mid + (t - x_mid) * (y_warm - y_mid) / (x_warm - x_mid)) | round(1) }}
          {% elif t > x_cold %}
            {{ (y_cold + (t - x_cold) * (y_mid - y_cold) / (x_mid - x_cold)) | round(1) }}
          {% else %}
            {{ y_cold | round(1) }}
          {% endif %}
```

- **`sensor.outside_temperature`** durch Ihre Außentemperatur-Entity ersetzen.
- **`input_number.heating_curve_*`** durch Ihre Helfer-IDs ersetzen; die `float(50)` usw. sind Fallbacks, wenn die Entity noch keinen Wert hat.

### Formel (Kurz)

- **Außentemperatur ≥ +22 °C:** Ausgabe = Warmpunkt.
- **Zwischen 0 °C und +22 °C:** Lineare Interpolation zwischen Mittelpunkt und Warmpunkt:  
  *Vorlauf = y_mid + (t − 0) × (y_warm − y_mid) / 22*
- **Zwischen -22 °C und 0 °C:** Lineare Interpolation zwischen Kaltpunkt und Mittelpunkt:  
  *Vorlauf = y_cold + (t − (−22)) × (y_mid − y_cold) / 22*
- **Außentemperatur ≤ -22 °C:** Ausgabe = Kaltpunkt.

Optional können Sie einen **Flow-Line-Offset** (z. B. aus einem weiteren `input_number`) addieren, indem Sie im Template zum Endergebnis `+ states('input_number.flow_offset') | float(0)` hinzufügen.

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
- **adjustment**: Raumthermomenter-Anpassung
- **eco_reduction**: ECO-Temperaturreduktion
- **op_state**: Betriebszustand des Heizkreises
- **-> result**: Finale berechnete Vorlauftemperatur


## Weitere Informationen

- [Raumthermomenter](raumthermostat.md) - Integration externer Raumthermomenter-Sensoren
- [Technische Berechnungsdetails](../../docs_md/HEATING_CURVE_CALCULATION.md) - Detaillierte Beschreibung der Berechnungslogik

