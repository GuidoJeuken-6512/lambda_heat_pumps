---
title: "Historische Daten übernehmen"
---

# Historische Daten übernehmen

Wenn Sie eine Wärmepumpe austauschen oder die Zählerstände zurücksetzen, können Sie historische Daten in die Integration übernehmen. Dies ermöglicht es, die Kontinuität der Daten zu erhalten und historische Trends beizubehalten.

Wenn Sie diese Integration neu installieren und vorher andere Lösungen im Einsatz hatten, die andere Entitäten zur Verfügung gestellt haben, so können Sie die historischen Daten der "alten" Sensoren auf die "neuen" umschreiben. Wie das funktioniert ist hier beschrieben: [Historische Werte neu zuordnen](https://homeassistant.com.de/homeassistant/homeassistant-historische-werte-neu-zuordnen/){:target="_blank" rel="noopener noreferrer"}

## Übersicht

Die Integration unterstützt Offsets für:

- **Cycling-Sensoren**: Zählerstände für Betriebszyklen (Heizen, Warmwasser, Kühlen, Abtauen)
- **Energieverbrauchs-Sensoren**: Energieverbrauchswerte (Heizen, Warmwasser, Kühlen, Abtauen)

## Cycling-Offsets

Cycling-Offsets ermöglichen es, einen Basiswert zu Total-Cycling-Sensoren hinzuzufügen. Dies ist nützlich beim:

- **Wärmepumpen-Austausch**: Zählerstand der vorherigen Pumpe hinzufügen
- **Zähler-Reset**: Manuelle Resets kompensieren
- **Migrations-Szenarien**: Historische Daten erhalten

### Konfiguration

Die Cycling-Offsets werden in `lambda_wp_config.yaml` konfiguriert:

```yaml
cycling_offsets:
  hp1:
    heating_cycling_total: 1500    # HP1 hatte bereits 1500 Heizzyklen
    hot_water_cycling_total: 800   # HP1 hatte bereits 800 Warmwasserzyklen
    cooling_cycling_total: 200     # HP1 hatte bereits 200 Kühlzyklen
    defrost_cycling_total: 50      # HP1 hatte bereits 50 Abtauzyklen
    compressor_start_cycling_total: 5000  # HP1 hatte bereits 5000 Kompressor-Starts
  hp2:
    heating_cycling_total: 0       # HP2 startet frisch
    hot_water_cycling_total: 0     # HP2 startet frisch
    cooling_cycling_total: 0       # HP2 startet frisch
    defrost_cycling_total: 0       # HP2 startet frisch
    compressor_start_cycling_total: 0     # HP2 startet frisch
```

### Funktionsweise

1. **Beim Start**: Offsets werden auf Total-Sensoren angewendet, wenn sie initialisiert werden
2. **Während des Betriebs**: Offsets werden zu jeder Inkrementierung hinzugefügt
3. **Nur Total-Sensoren**: Offsets gelten nur für `*_cycling_total` Sensoren
4. **Automatische Anwendung**: Offsets werden automatisch geladen und angewendet
5. **Offset-Tracking**: System verfolgt angewendete Offsets, um Doppelanwendung zu verhindern

### Beispiel-Szenarien

#### Szenario 1: Wärmepumpen-Austausch

Alte Pumpe hatte 2500 Heizzyklen, neue Pumpe startet bei 0:

```yaml
cycling_offsets:
  hp1:
    heating_cycling_total: 2500
    hot_water_cycling_total: 1200
    cooling_cycling_total: 300
    defrost_cycling_total: 80
```

#### Szenario 2: Zähler-Reset

Manueller Reset der Zähler, aber Historie erhalten:

```yaml
cycling_offsets:
  hp1:
    heating_cycling_total: 5000  # Vorheriger Gesamtwert vor Reset
    hot_water_cycling_total: 2000
    cooling_cycling_total: 500
    defrost_cycling_total: 150
```

## Energieverbrauchs-Offsets

Energieverbrauchs-Offsets ermöglichen es, historische Energieverbrauchswerte zu übernehmen. Dies ist nützlich beim:

- **Wärmepumpen-Austausch**: Energieverbrauch der vorherigen Pumpe hinzufügen
- **Zähler-Reset**: Manuelle Resets kompensieren
- **Migrations-Szenarien**: Historische Energieverbrauchsdaten erhalten

### Konfiguration

**⚠️ WICHTIG: Alle Werte müssen in kWh angegeben werden!**

Die Energieverbrauchs-Offsets werden in `lambda_wp_config.yaml` konfiguriert:

```yaml
energy_consumption_offsets:
  hp1:
    heating_energy_total: 0.0       # kWh Offset für HP1 Heizung Total
    hot_water_energy_total: 0.0     # kWh Offset für HP1 Warmwasser Total
    cooling_energy_total: 0.0      # kWh Offset für HP1 Kühlung Total
    defrost_energy_total: 0.0       # kWh Offset für HP1 Abtau Total
  hp2:
    heating_energy_total: 150.5     # Beispiel: HP2 verbrauchte bereits 150.5 kWh Heizung
    hot_water_energy_total: 45.25   # Beispiel: HP2 verbrauchte bereits 45.25 kWh Warmwasser
    cooling_energy_total: 12.8      # Beispiel: HP2 verbrauchte bereits 12.8 kWh Kühlung
    defrost_energy_total: 3.1        # Beispiel: HP2 verbrauchte bereits 3.1 kWh Abtau
```

### Funktionsweise

1. **Nur Total-Sensoren**: Offsets werden nur auf `*_energy_total` Sensoren angewendet
2. **Automatische Anwendung**: Offsets werden beim Start automatisch geladen und angewendet
3. **Einheiten**: Alle Werte müssen in kWh (Kilowattstunden) angegeben werden
4. **Dezimalnotation**: Verwenden Sie Punkt (.) als Dezimaltrennzeichen in YAML

### Beispiel-Szenarien

#### Szenario 1: Wärmepumpen-Austausch

Alte Pumpe verbrauchte 5000 kWh Heizung, neue Pumpe startet bei 0:

```yaml
energy_consumption_offsets:
  hp1:
    heating_energy_total: 5000.0
    hot_water_energy_total: 2000.0
    cooling_energy_total: 500.0
    defrost_energy_total: 150.0
```

#### Szenario 2: Zähler-Reset

Manueller Reset der Zähler, aber Historie erhalten:

```yaml
energy_consumption_offsets:
  hp1:
    heating_energy_total: 10000.5  # Vorheriger Gesamtwert vor Reset
    hot_water_energy_total: 3500.25
    cooling_energy_total: 800.0
    defrost_energy_total: 250.5
```

## Anwendung der Offsets

### Schritt 1: Historische Werte ermitteln

Bevor Sie die Offsets konfigurieren, müssen Sie die historischen Werte ermitteln:

1. **Cycling-Werte**: Notieren Sie die letzten Zählerstände der alten Wärmepumpe
2. **Energieverbrauchswerte**: Notieren Sie die letzten Energieverbrauchswerte der alten Wärmepumpe

### Schritt 2: lambda_wp_config.yaml bearbeiten

1. **Datei öffnen:**
   - Die Datei befindet sich in `/config/lambda_heat_pumps/lambda_wp_config.yaml`
   - Falls die Datei nicht existiert, wird sie beim ersten Start automatisch erstellt

2. **Offsets hinzufügen:**
   - Fügen Sie die `cycling_offsets` und/oder `energy_consumption_offsets` Sektionen hinzu
   - Verwenden Sie die Beispiele oben als Vorlage

3. **Datei speichern:**
   - Speichern Sie die Datei

### Schritt 3: Home Assistant neu starten

1. **Home Assistant neu starten:**
   - Starten Sie Home Assistant vollständig neu
   - Die Offsets werden beim Start automatisch angewendet

2. **Überprüfen Sie die Sensoren:**
   - Überprüfen Sie, ob die Total-Sensoren die korrekten Werte anzeigen
   - Die Offsets sollten bereits in den Sensor-Werten enthalten sein

## Offset-Anpassung

Sie können Offsets jederzeit anpassen:

1. **lambda_wp_config.yaml bearbeiten:**
   - Ändern Sie die Offset-Werte
   - Speichern Sie die Datei

2. **Home Assistant neu starten:**
   - Starten Sie Home Assistant neu
   - Die neuen Offsets werden automatisch angewendet

**Hinweis**: Das System verhindert Doppelanwendung von Offsets durch intelligentes Tracking. Wenn Sie einen Offset erhöhen, wird nur die Differenz hinzugefügt.

## Häufige Probleme

### "Offsets werden nicht angewendet"
- **Ursache**: Datei nicht korrekt gespeichert oder YAML-Syntax-Fehler
- **Lösung**: 
  - Überprüfen Sie die YAML-Syntax
  - Verwenden Sie einen YAML-Validator
  - Überprüfen Sie die Logs auf Fehlermeldungen

### "Falsche Werte nach Offset-Anwendung"
- **Ursache**: Falsche Einheiten (z.B. Wh statt kWh für Energie)
- **Lösung**: 
  - Stellen Sie sicher, dass Energie-Offsets in kWh angegeben sind
  - Konvertieren Sie Wh zu kWh (÷ 1000)

### "Offsets werden doppelt angewendet"
- **Ursache**: Mehrfaches Neustarten ohne Änderung
- **Lösung**: 
  - Das System verhindert Doppelanwendung automatisch
  - Überprüfen Sie die Logs, um zu sehen, ob Offsets korrekt angewendet wurden

## Nächste Schritte

Nach der Übernahme historischer Daten können Sie:

- [Stromverbrauchsberechnung](stromverbrauchsberechnung.md) einrichten
- [Optionen des config_flow](optionen-config-flow.md) anpassen
- [Aktionen (read/write Modbus register)](aktionen-modbus.md) verwenden

