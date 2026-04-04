---
title: "Offsets – Historische Daten übernehmen"
---

# Offsets – Historische Daten übernehmen

*Zuletzt geändert am 28.03.2026*

Offsets ermöglichen es, historische Zähler- und Verbrauchswerte nahtlos fortzuführen – etwa nach dem Austausch einer Wärmepumpe, nach einem Zählerreset oder zur Korrektur eines falschen Ausgangswertes. Die Integration unterstützt zwei unabhängige Offset-Typen:

| Typ | Sensoren | Einheit | YAML-Schlüssel |
|-----|----------|---------|----------------|
| **Cycling-Offsets** | Betriebszyklenzähler | Zyklen (Integer) | `cycling_offsets` |
| **Energie-Offsets** | Energieverbrauchs-Totals | kWh (Float) | `energy_consumption_offsets` |

Beide Typen werden in der Datei `/config/lambda_wp_config.yaml` konfiguriert (→ [Konfigurationsübersicht](lambda-wp-config.md)).

---

## Wie funktionieren Offsets?

### Differenz-Tracking – kein Doppelzählen

Offsets werden **nicht blind addiert**, sondern es wird immer nur die **Differenz** zum bereits angewendeten Offset berechnet. Das System speichert jeden angewendeten Offset als Attribut `applied_offset` im HA-State.

**Beispiel: Cycling-Offset = 1500**

| Ereignis | Sensorwert | `applied_offset` | Differenz |
|----------|----------:|------------------:|----------:|
| Erststart, Offset = 1500 | 0 → **1500** | 0 → 1500 | +1500 |
| HA-Neustart, Offset unverändert | 1500 (restored) | 1500 (restored) | 0 – kein Effekt |
| Offset auf 1600 geändert | 1500 → **1600** | 1500 → 1600 | +100 |

So ist es **sicher, Home Assistant beliebig oft neu zu starten** – der Offset wird nie doppelt angewendet.

### Wann werden Offsets angewendet?

Offsets werden **einmalig beim HA-Start** angewendet, sobald der Sensor initialisiert wird. Im laufenden Betrieb werden nur tatsächliche Zählinkremente addiert – der Offset hat keinen Einfluss mehr.

### Negative Offsets – Korrektur eines zu hohen Wertes

**Positive und negative Werte sind ausdrücklich erlaubt.** Ein negativer Offset subtrahiert den angegebenen Betrag vom Gesamtzähler und ermöglicht so die Korrektur eines falschen Ausgangswertes:

```yaml
cycling_offsets:
  hp1:
    heating_cycling_total: -200   # Subtrahiert 200 von der Gesamtzahl
```

```yaml
energy_consumption_offsets:
  hp1:
    heating_energy_total: -150.5  # Subtrahiert 150,5 kWh vom Total
```

---

## 1. Cycling-Offsets

### Welche Sensoren?

Cycling-Offsets wirken ausschließlich auf **Total-Sensoren** (`*_cycling_total`). Daily-, Monthly- und Yearly-Sensoren erhalten keine Offsets.

| YAML-Schlüssel | Beschreibung |
|----------------|-------------|
| `heating_cycling_total` | Gesamtzahl Heizzyklen |
| `hot_water_cycling_total` | Gesamtzahl Warmwasserzyklen |
| `cooling_cycling_total` | Gesamtzahl Kühlzyklen |
| `defrost_cycling_total` | Gesamtzahl Abtauzyklen |
| `compressor_start_cycling_total` | Gesamtzahl Kompressorstarts |

### Konfiguration

```yaml
cycling_offsets:
  hp1:
    heating_cycling_total: 1500             # HP1 hatte bereits 1500 Heizzyklen
    hot_water_cycling_total: 800            # HP1 hatte bereits 800 Warmwasserzyklen
    cooling_cycling_total: 200              # HP1 hatte bereits 200 Kühlzyklen
    defrost_cycling_total: 50               # HP1 hatte bereits 50 Abtauzyklen
    compressor_start_cycling_total: 5000    # HP1 hatte bereits 5000 Kompressorstarts
  hp2:
    heating_cycling_total: 0
    hot_water_cycling_total: 0
    cooling_cycling_total: 0
    defrost_cycling_total: 0
    compressor_start_cycling_total: 0
```

### Typische Szenarien

#### Szenario A: Wärmepumpen-Austausch

Alte Pumpe hatte 2500 Heizzyklen. Neue Pumpe startet bei 0, der Zähler in HA soll trotzdem weiterlaufen:

```yaml
cycling_offsets:
  hp1:
    heating_cycling_total: 2500
    hot_water_cycling_total: 1200
    cooling_cycling_total: 300
    defrost_cycling_total: 80
    compressor_start_cycling_total: 12000
```

#### Szenario B: Manueller Zähler-Reset

Der Modbus-Zähler der Wärmepumpe wurde zurückgesetzt, der HA-Gesamtzähler soll nicht zurückspringen:

```yaml
cycling_offsets:
  hp1:
    heating_cycling_total: 5000   # Wert vor dem Reset
```

#### Szenario C: Falscher Ausgangswert korrigieren

Ein fehlerhafter Offset hat den Zähler um 500 zu hoch gesetzt:

```yaml
cycling_offsets:
  hp1:
    heating_cycling_total: -500   # Subtrahiert 500 vom Gesamtzähler
```

---

## 2. Energie-Offsets

### Welche Sensoren?

Energie-Offsets wirken ausschließlich auf **Total-Sensoren** (`*_energy_total`). Es gibt zwei Untertypen:

**Elektrische Offsets** (`{mode}_energy_total`):

| YAML-Schlüssel | Beschreibung |
|----------------|-------------|
| `heating_energy_total` | Elektrischer Gesamtverbrauch Heizen |
| `hot_water_energy_total` | Elektrischer Gesamtverbrauch Warmwasser |
| `cooling_energy_total` | Elektrischer Gesamtverbrauch Kühlen |
| `defrost_energy_total` | Elektrischer Gesamtverbrauch Abtauen |

**Thermische Offsets** (`{mode}_thermal_energy_total`, optional):

| YAML-Schlüssel | Beschreibung |
|----------------|-------------|
| `heating_thermal_energy_total` | Thermischer Gesamtoutput Heizen |
| `hot_water_thermal_energy_total` | Thermischer Gesamtoutput Warmwasser |
| `cooling_thermal_energy_total` | Thermischer Gesamtoutput Kühlen |
| `defrost_thermal_energy_total` | Thermischer Gesamtoutput Abtauen |

### Konfiguration

**⚠️ Alle Werte müssen in kWh angegeben werden! Dezimaltrennzeichen: Punkt (`.`)**

```yaml
energy_consumption_offsets:
  hp1:
    # Elektrische Offsets (Stromverbrauch):
    heating_energy_total: 5000.0              # kWh, HP1 hatte bereits 5000 kWh Heizen
    hot_water_energy_total: 2000.0            # kWh, HP1 hatte bereits 2000 kWh Warmwasser
    cooling_energy_total: 500.0               # kWh
    defrost_energy_total: 150.0               # kWh
    # Thermische Offsets (Wärmeabgabe, optional):
    heating_thermal_energy_total: 18000.0     # kWh thermischer Output Heizen
    hot_water_thermal_energy_total: 7200.0    # kWh thermischer Output Warmwasser
    cooling_thermal_energy_total: 1500.0      # kWh
    defrost_thermal_energy_total: 480.0       # kWh
  hp2:
    heating_energy_total: 150.5
    hot_water_energy_total: 45.25
    cooling_energy_total: 12.8
    defrost_energy_total: 3.1
```

### Wh vs. kWh

Die Quellsensoren (→ [Energieverbrauchsberechnung](Energieverbrauchsberechnung.md)) können Wh oder kWh liefern – die Konvertierung erfolgt automatisch. **Offset-Werte** müssen jedoch immer in **kWh** angegeben werden.

| Quellsensor | Offset |
|-------------|--------|
| Wh → automatische Konvertierung | Immer kWh |

### Typische Szenarien

#### Szenario A: Wärmepumpen-Austausch

```yaml
energy_consumption_offsets:
  hp1:
    heating_energy_total: 5000.0
    hot_water_energy_total: 2000.0
    cooling_energy_total: 500.0
    defrost_energy_total: 150.0
    heating_thermal_energy_total: 18000.0
    hot_water_thermal_energy_total: 7200.0
```

#### Szenario B: Zähler-Reset kompensieren

```yaml
energy_consumption_offsets:
  hp1:
    heating_energy_total: 10000.5   # Gesamtwert vor dem Reset
    hot_water_energy_total: 3500.25
```

#### Szenario C: Korrektur eines zu hohen Wertes

```yaml
energy_consumption_offsets:
  hp1:
    heating_energy_total: -250.0   # Subtrahiert 250 kWh vom Total
```

---

## Schritt-für-Schritt: Offsets einrichten

### Schritt 1: Werte ermitteln

Notieren Sie die letzten bekannten Zählerstände der alten oder zurückgesetzten Wärmepumpe:
- Cycling-Zähler: z. B. aus dem HA-Verlauf oder aus der Wärmepumpen-Steuerung
- Energie-Totals: aus dem letzten bekannten HA-Sensorwert (in kWh)

### Schritt 2: lambda_wp_config.yaml bearbeiten

Öffnen Sie `/config/lambda_wp_config.yaml` (→ [Konfigurationsanleitung](lambda-wp-config.md)) und fügen Sie die Offset-Abschnitte hinzu:

```yaml
cycling_offsets:
  hp1:
    heating_cycling_total: 2500
    # weitere Schlüssel ...

energy_consumption_offsets:
  hp1:
    heating_energy_total: 5000.0
    # weitere Schlüssel ...
```

### Schritt 3: Home Assistant neu starten

Nach dem Speichern muss Home Assistant vollständig neu gestartet werden. Die Offsets werden beim nächsten Start automatisch auf die Total-Sensoren angewendet.

### Schritt 4: Überprüfen

Prüfen Sie, ob die Sensor-Werte korrekt sind:
- Die Total-Sensoren sollten den Basiswert + Offset zeigen
- Das Attribut `applied_offset` am Sensor zeigt den aktuell angewendeten Offset

---

## Häufige Probleme

### Offset wird nicht angewendet

- YAML-Syntax prüfen (Einrückung mit Leerzeichen, kein Tab)
- Sicherstellen, dass HA vollständig neu gestartet wurde
- HA-Logs auf Fehlermeldungen prüfen

### Energie-Offset in falscher Einheit

- Alle Energie-Offsets müssen in **kWh** angegeben werden
- Umrechnung: Wh ÷ 1000 = kWh

### Offset wurde doppelt angewendet

- Das sollte durch das Differenz-Tracking nicht passieren
- Wenn doch: Den Wert des Attributs `applied_offset` des betroffenen Sensors prüfen
- Im Log nachsehen, ob der Offset korrekt protokolliert wurde

---

## Verwandte Seiten

- [lambda_wp_config.yaml Konfiguration](lambda-wp-config.md) – vollständige Konfigurationsdatei
- [Energieverbrauchsberechnung](Energieverbrauchsberechnung.md) – Quellsensoren für Energiedaten
- [Historische Daten löschen](historische_daten_loeschen.md) – Zähler und Verlauf zurücksetzen
