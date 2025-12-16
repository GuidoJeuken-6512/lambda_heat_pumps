# Übersicht aller Home Assistant Entitäten (Modbus Lambda Heat Pumps)

**Annahme:** Jeweils 1 Gerät pro Typ: 1 HP, 1 Boiler, 1 Buffer, 1 Solar, 1 Heating Circuit

**Legende:** R = Read-only (nur lesbar), RW = Read/Write (lesbar und schreibbar)

## Inhaltsverzeichnis

1. [Heat Pump (HP1)](#heat-pump-hp1)
   - [Sensors](#sensors)
   - [Cycling Sensors (Flanken-basiert)](#cycling-sensors-flanken-basiert)
   - [Energy Consumption Sensors (Energieverbrauchs-Sensoren nach Betriebsart)](#energy-consumption-sensors-energieverbrauchs-sensoren-nach-betriebsart)
   - [Template-Sensoren (Berechnete Sensoren)](#template-sensoren-berechnete-sensoren)
2. [Boiler (BOIL1)](#boiler-boil1)
   - [Sensors](#sensors-1)
3. [Buffer (BUFF1)](#buffer-buff1)
   - [Sensors](#sensors-2)
4. [Solar (SOL1)](#solar-sol1)
   - [Sensors](#sensors-3)
5. [Heating Circuit (HC1)](#heating-circuit-hc1)
   - [Sensors](#sensors-4)
6. [General Sensors (Main Controller)](#general-sensors-main-controller)
   - [Ambient Sensors](#ambient-sensors)
   - [E-Manager Sensors](#e-manager-sensors)
   - [Dummy Sensors](#dummy-sensors)
7. [Climate Entities](#climate-entities)
   - [Hot Water Climate (Boiler)](#hot-water-climate-boiler)
   - [Heating Circuit Climate](#heating-circuit-climate)
8. [Base Addresses](#base-addresses)
9. [Firmware-Versionen](#firmware-versionen)
10. [Wichtige Hinweise](#wichtige-hinweise)
11. [Übersicht aller RW-Sensoren](#übersicht-aller-rw-sensoren)

## Heat Pump (HP1)

### Sensors
| Name                                    | Register | minFW | Einheit | R/W | Beschreibung |
|-----------------------------------------|----------|-------|---------|-----|--------------|
| Error State                             | 0        | 1     | -       | R   | Fehlerstatus der Wärmepumpe |
| Error Number                            | 1        | 1     | -       | R   | Fehlernummer |
| State                                   | 2        | 1     | -       | R   | Zustand der Wärmepumpe |
| Operating State                         | 3        | 1     | -       | R   | Betriebszustand |
| Flow Line Temperature                   | 4        | 1     | °C      | R   | Vorlauftemperatur |
| Return Line Temperature                 | 5        | 1     | °C      | R   | Rücklauftemperatur |
| Volume Flow Heat Sink                   | 6        | 1     | l/h     | R   | Volumenstrom Wärmesenke |
| Energy Source Inlet Temperature         | 7        | 1     | °C      | R   | Temperatur Energiequelle Einlass |
| Energy Source Outlet Temperature        | 8        | 1     | °C      | R   | Temperatur Energiequelle Auslass |
| Volume Flow Energy Source               | 9        | 1     | l/min   | R   | Volumenstrom Energiequelle |
| Compressor Unit Rating                  | 10       | 1     | kW      | R   | Kompressor-Einheitenleistung |
| Actual Heating Capacity                 | 11       | 1     | kW      | R   | Tatsächliche Heizleistung |
| Inverter Power Consumption              | 12       | 1     | W       | R   | Inverter-Leistungsaufnahme |
| COP                                     | 13       | 1     | -       | R   | Leistungszahl |
| Request-Type                            | 15       | 1     | -       | R   | Anforderungstyp |
| Requested Flow Line Temperature         | 16       | 1     | °C      | R   | Gewünschte Vorlauftemperatur |
| Requested Return Line Temperature       | 17       | 1     | °C      | R   | Gewünschte Rücklauftemperatur |
| Requested Flow to Return Temp Diff      | 18       | 1     | K       | R   | Gewünschte Vorlauf-Rücklauf-Temp.-Diff. |
| Relais State 2nd Heating Stage          | 19       | 1     | -       | R   | Relais-Zustand 2. Heizstufe |
| Compressor Power Consumption Accum.     | 20       | 1     | kWh     | R   | Kompressor-Leistungsaufnahme kumuliert |
| Compressor Thermal Energy Output Accum. | 22       | 1     | kWh     | R   | Kompressor-Wärmeenergie-Ausgabe kumuliert |
| Unknown Parameter (R1024)               | 24       | 1     | -       | R   | Unbekannter Parameter |
| VdA Rating                              | 25       | 1     | kW      | R   | VdA-Leistung |
| Hot Gas Temperature                     | 26       | 1     | °C      | R   | Heißgas-Temperatur |
| Subcooling Temperature                  | 27       | 1     | °C      | R   | Unterkühlungs-Temperatur |
| Suction Gas Temperature                 | 28       | 1     | °C      | R   | Sauggas-Temperatur |
| Condensation Temperature                | 29       | 1     | °C      | R   | Kondensations-Temperatur |
| Evaporation Temperature                 | 30       | 1     | °C      | R   | Verdampfungs-Temperatur |
| EqM Rating                              | 31       | 1     | kW      | R   | EqM-Leistung |
| Expansion Valve Opening Angle           | 32       | 1     | °       | R   | Expansionsventil-Öffnungswinkel |
| Unknown Parameter (R1050)               | 50       | 1     | -       | R   | Unbekannter Parameter |
| DHW Output Power at 15°C                | 51       | 1     | kW      | R   | WW-Ausgangsleistung bei 15°C |
| Heating Min Output Power at 15°C        | 52       | 1     | kW      | R   | Heizung Min-Ausgangsleistung bei 15°C |
| Heating Max Output Power at 15°C        | 53       | 1     | kW      | R   | Heizung Max-Ausgangsleistung bei 15°C |
| Heating Min Output Power at 0°C         | 54       | 1     | kW      | R   | Heizung Min-Ausgangsleistung bei 0°C |
| Heating Max Output Power at 0°C         | 55       | 1     | kW      | R   | Heizung Max-Ausgangsleistung bei 0°C |
| Heating Min Output Power at -15°C       | 56       | 1     | kW      | R   | Heizung Min-Ausgangsleistung bei -15°C |
| Heating Max Output Power at -15°C       | 57       | 1     | kW      | R   | Heizung Max-Ausgangsleistung bei -15°C |
| Cooling Min Output Power                | 58       | 1     | kW      | R   | Kühlung Min-Ausgangsleistung |
| Cooling Max Output Power                | 59       | 1     | kW      | R   | Kühlung Max-Ausgangsleistung |
| Unknown Parameter (R1060)               | 60       | 1     | -       | R   | Unbekannter Parameter |

### Cycling Sensors (Flanken-basiert)
| Name                          | Register | minFW | Einheit | R/W | Beschreibung |
|-------------------------------|----------|-------|---------|-----|--------------|
| Heating Cycling Total         | -        | 1     | cycles  | R   | Gesamtzahl Heizzyklen (kumulativ) |
| Hot Water Cycling Total       | -        | 1     | cycles  | R   | Gesamtzahl Warmwasserzyklen (kumulativ) |
| Cooling Cycling Total         | -        | 1     | cycles  | R   | Gesamtzahl Kühlzyklen (kumulativ) |
| Defrost Cycling Total         | -        | 1     | cycles  | R   | Gesamtzahl Abtauzyklen (kumulativ) |
| Heating Cycling Yesterday     | -        | 1     | cycles  | R   | Heizzyklen von gestern (gespeichert) |
| Hot Water Cycling Yesterday   | -        | 1     | cycles  | R   | Warmwasserzyklen von gestern (gespeichert) |
| Cooling Cycling Yesterday     | -        | 1     | cycles  | R   | Kühlzyklen von gestern (gespeichert) |
| Defrost Cycling Yesterday     | -        | 1     | cycles  | R   | Abtauzyklen von gestern (gespeichert) |
| Heating Cycling Daily         | -        | 1     | cycles  | R   | Tägliche Heizzyklen (wird täglich um 00:00 zurückgesetzt) |
| Hot Water Cycling Daily       | -        | 1     | cycles  | R   | Tägliche Warmwasserzyklen (wird täglich um 00:00 zurückgesetzt) |
| Cooling Cycling Daily         | -        | 1     | cycles  | R   | Tägliche Kühlzyklen (wird täglich um 00:00 zurückgesetzt) |
| Defrost Cycling Daily         | -        | 1     | cycles  | R   | Tägliche Abtauzyklen (wird täglich um 00:00 zurückgesetzt) |
| Heating Cycling 2H            | -        | 1     | cycles  | R   | 2-Stunden Heizzyklen (wird alle 2h zurückgesetzt: 0,2,4,6,8,10,12,14,16,18,20,22 Uhr) |
| Hot Water Cycling 2H          | -        | 1     | cycles  | R   | 2-Stunden Warmwasserzyklen (wird alle 2h zurückgesetzt: 0,2,4,6,8,10,12,14,16,18,20,22 Uhr) |
| Cooling Cycling 2H            | -        | 1     | cycles  | R   | 2-Stunden Kühlzyklen (wird alle 2h zurückgesetzt: 0,2,4,6,8,10,12,14,16,18,20,22 Uhr) |
| Defrost Cycling 2H            | -        | 1     | cycles  | R   | 2-Stunden Abtauzyklen (wird alle 2h zurückgesetzt: 0,2,4,6,8,10,12,14,16,18,20,22 Uhr) |
| Heating Cycling 4H            | -        | 1     | cycles  | R   | 4-Stunden Heizzyklen (wird alle 4h zurückgesetzt: 0,4,8,12,16,20 Uhr) |
| Hot Water Cycling 4H          | -        | 1     | cycles  | R   | 4-Stunden Warmwasserzyklen (wird alle 4h zurückgesetzt: 0,4,8,12,16,20 Uhr) |
| Cooling Cycling 4H            | -        | 1     | cycles  | R   | 4-Stunden Kühlzyklen (wird alle 4h zurückgesetzt: 0,4,8,12,16,20 Uhr) |
| Defrost Cycling 4H            | -        | 1     | cycles  | R   | 4-Stunden Abtauzyklen (wird alle 4h zurückgesetzt: 0,4,8,12,16,20 Uhr) |

**Hinweise zu Cycling-Sensoren:**
- **Flanken-basierte Zählung:** Alle Cycling-Sensoren werden durch Flankenerkennung im `operating_state` erhöht
- **Direkte Inkrementierung:** Keine Template-Berechnungen mehr - direkte Werte in den Sensoren
- **Automatische Resets:** Daily (00:00), 2H (alle 2h), 4H (alle 4h) werden automatisch zurückgesetzt
- **Yesterday-Werte:** Werden vor dem Daily-Reset (um 00:00) vom aktuellen Daily-Wert übernommen
- **Historische Daten:** Alle Werte werden in der Home Assistant Datenbank gespeichert
- **State Classes:** TOTAL (kumulativ), MEASUREMENT (periodisch zurückgesetzt)

### Energy Consumption Sensors (Energieverbrauchs-Sensoren nach Betriebsart)
| Name                          | Register | minFW | Einheit | R/W | Beschreibung |
|-------------------------------|----------|-------|---------|-----|--------------|
| Heating Energy Total          | -        | 1     | kWh     | R   | Gesamter Energieverbrauch für Heizen (kumulativ) |
| Heating Energy Daily          | -        | 1     | kWh     | R   | Täglicher Energieverbrauch für Heizen (wird täglich um 00:00 zurückgesetzt) |
| Heating Energy Monthly        | -        | 1     | kWh     | R   | Monatlicher Energieverbrauch für Heizen (wird monatlich am 1. zurückgesetzt) |
| Heating Energy Yearly         | -        | 1     | kWh     | R   | Jährlicher Energieverbrauch für Heizen (wird jährlich am 1. Januar zurückgesetzt) |
| Hot Water Energy Total        | -        | 1     | kWh     | R   | Gesamter Energieverbrauch für Warmwasser (kumulativ) |
| Hot Water Energy Daily        | -        | 1     | kWh     | R   | Täglicher Energieverbrauch für Warmwasser (wird täglich um 00:00 zurückgesetzt) |
| Hot Water Energy Monthly      | -        | 1     | kWh     | R   | Monatlicher Energieverbrauch für Warmwasser (wird monatlich am 1. zurückgesetzt) |
| Hot Water Energy Yearly       | -        | 1     | kWh     | R   | Jährlicher Energieverbrauch für Warmwasser (wird jährlich am 1. Januar zurückgesetzt) |
| Cooling Energy Total          | -        | 1     | kWh     | R   | Gesamter Energieverbrauch für Kühlen (kumulativ) |
| Cooling Energy Daily          | -        | 1     | kWh     | R   | Täglicher Energieverbrauch für Kühlen (wird täglich um 00:00 zurückgesetzt) |
| Cooling Energy Monthly        | -        | 1     | kWh     | R   | Monatlicher Energieverbrauch für Kühlen (wird monatlich am 1. zurückgesetzt) |
| Cooling Energy Yearly         | -        | 1     | kWh     | R   | Jährlicher Energieverbrauch für Kühlen (wird jährlich am 1. Januar zurückgesetzt) |
| Defrost Energy Total          | -        | 1     | kWh     | R   | Gesamter Energieverbrauch für Abtauen (kumulativ) |
| Defrost Energy Daily          | -        | 1     | kWh     | R   | Täglicher Energieverbrauch für Abtauen (wird täglich um 00:00 zurückgesetzt) |
| Defrost Energy Monthly        | -        | 1     | kWh     | R   | Monatlicher Energieverbrauch für Abtauen (wird monatlich am 1. zurückgesetzt) |
| Defrost Energy Yearly         | -        | 1     | kWh     | R   | Jährlicher Energieverbrauch für Abtauen (wird jährlich am 1. Januar zurückgesetzt) |
| Standby Energy Total          | -        | 1     | kWh     | R   | Gesamter Energieverbrauch für Standby (kumulativ) |
| Standby Energy Daily          | -        | 1     | kWh     | R   | Täglicher Energieverbrauch für Standby (wird täglich um 00:00 zurückgesetzt) |
| Standby Energy Monthly        | -        | 1     | kWh     | R   | Monatlicher Energieverbrauch für Standby (wird monatlich am 1. zurückgesetzt) |
| Standby Energy Yearly         | -        | 1     | kWh     | R   | Jährlicher Energieverbrauch für Standby (wird jährlich am 1. Januar zurückgesetzt) |

**Hinweise zu Energy Consumption Sensors:**
- **Flanken-basierte Energiezuordnung:** Energie wird basierend auf Betriebsart-Änderungen zugeordnet
- **Automatische Berechnung:** Energieverbrauch wird aus dem Kompressor-Stromverbrauch berechnet
- **Automatische Resets:** Daily (00:00), Monthly (1. des Monats), Yearly (1. Januar) werden automatisch zurückgesetzt
- **Offset-Unterstützung:** Total-Sensoren unterstützen Offsets für Wärmepumpen-Austausch
- **State Classes:** TOTAL_INCREASING (kumulativ), TOTAL (periodisch zurückgesetzt)
- **Einheitenkonvertierung:** Unterstützt automatische Konvertierung von Wh, kWh, MWh zu kWh
- **Quellesensor:** Standardmäßig wird `compressor_power_consumption_accumulated` (Register 20) verwendet
- **Quellesensor-Konfiguration:** Der Quellesensor kann in der `lambda_wp_config.yaml` durch einen eigenen Sensor ersetzt werden (siehe Konfigurationsbeispiel unten)

**Konfigurationsbeispiel für eigenen Quellesensor:**
```yaml
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.eu08l_hp1_compressor_power_consumption_accumulated"  # Standard
  hp2:
    sensor_entity_id: "sensor.my_custom_energy_meter"  # Eigener Sensor

energy_consumption_offsets:
  hp1:
    heating_energy_total: 0
    hot_water_energy_total: 0
    cooling_energy_total: 0
    defrost_energy_total: 0
    stby_energy_total: 0
  hp2:
    heating_energy_total: 150.5
    hot_water_energy_total: 45.2
    cooling_energy_total: 12.8
    defrost_energy_total: 3.1
    stby_energy_total: 5.0
```

### Template-Sensoren (Berechnete Sensoren)
| Name                                    | minFW | Einheit | R/W | Beschreibung |
|-----------------------------------------|-------|---------|-----|--------------|
| COP Calculated                          | 1     | -       | R   | Berechneter COP-Wert aus kumulativen Werten |

**Beispiel Entity-ID:** `sensor.eu08l_hp1_cop_calculated`

**Berechnung COP Calculated:**
```
COP = Thermische Energie Ausgabe (kumuliert) / Elektrische Leistungsaufnahme (kumuliert)
```

**Quell-Sensoren:**
- `compressor_thermal_energy_output_accumulated` (Register 22, Wh)
- `compressor_power_consumption_accumulated` (Register 20, Wh)

**Template-Logik:**
```jinja2
{% set thermal = states('sensor.{full_entity_prefix}_compressor_thermal_energy_output_accumulated') | float(0) %}
{% set power = states('sensor.{full_entity_prefix}_compressor_power_consumption_accumulated') | float(1) %}
{{ (thermal / power) | round(2) if power > 0 else 0 }}
```

**Hinweise zu Template-Sensoren:**
- **Automatische Berechnung:** Werden bei jeder Coordinator-Aktualisierung neu berechnet
- **Jinja2-Templates:** Verwenden Home Assistant Template-Syntax
- **Sicherheitsprüfung:** Verhindert Division durch Null (COP = 0 wenn power = 0)
- **Präzision:** 2 Dezimalstellen für COP-Werte
- **State Class:** `measurement` (Momentanwert)

## Boiler (BOIL1)

### Sensors
| Name                          | Register | minFW | Einheit | R/W | Beschreibung |
|-------------------------------|----------|-------|---------|-----|--------------|
| Error Number                  | 0        | 1     | -       | R   | Fehlernummer |
| Operating State               | 1        | 1     | -       | R   | Betriebszustand |
| Actual High Temperature       | 2        | 1     | °C      | R   | Tatsächliche hohe Temperatur |
| Actual Low Temperature        | 3        | 1     | °C      | R   | Tatsächliche niedrige Temperatur |
| Actual Circulation Temperature| 4        | 1     | °C      | R   | Tatsächliche Zirkulationstemperatur |
| Actual Circulation Pump State | 5        | 1     | -       | R   | Tatsächlicher Zirkulationspumpen-Zustand |
| Target High Temperature       | 50       | 1     | °C      | RW  | Ziel hohe Temperatur |
| Maximum Temperature           | 50       | 1     | °C      | R   | Maximale Temperatur |
| Dummy Boiler FW2              | 99       | 2     | -       | R   | Dummy für Firmware 2 |

## Buffer (BUFF1)

### Sensors
| Name                                 | Register | minFW | Einheit | R/W | Beschreibung |
|--------------------------------------|----------|-------|---------|-----|--------------|
| Error Number                         | 0        | 1     | -       | R   | Fehlernummer |
| Operating State                      | 1        | 1     | -       | R   | Betriebszustand |
| Actual High Temperature              | 2        | 1     | °C      | R   | Tatsächliche hohe Temperatur |
| Actual Low Temperature               | 3        | 1     | °C      | R   | Tatsächliche niedrige Temperatur |
| Buffer High Temperature Setpoint     | 4        | 1     | °C      | RW  | Buffer hohe Temperatur Sollwert |
| Request Type                         | 5        | 1     | -       | R   | Anforderungstyp |
| Flow Line Temperature Setpoint       | 6        | 1     | °C      | R   | Vorlauftemperatur Sollwert |
| Return Line Temperature Setpoint     | 7        | 1     | °C      | R   | Rücklauftemperatur Sollwert |
| Heat Sink Temperature Diff Setpoint  | 8        | 1     | K       | R   | Wärmesenke Temperaturdifferenz Sollwert |
| Requested Heating Capacity           | 9        | 1     | kW      | R   | Gewünschte Heizleistung |
| Maximum Temperature                  | 50       | 1     | °C      | R   | Maximale Temperatur |

## Solar (SOL1)

### Sensors
| Name                | Register | minFW | Einheit | R/W | Beschreibung |
|---------------------|----------|-------|---------|-----|--------------|
| Error Number        | 0        | 1     | -       | R   | Fehlernummer |
| Operating State     | 1        | 1     | -       | R   | Betriebszustand |
| Collector Temperature| 2        | 1     | °C      | R   | Kollektor-Temperatur |
| Storage Temperature | 3        | 1     | °C      | R   | Speicher-Temperatur |
| Power Current       | 4        | 1     | kW      | R   | Aktuelle Leistung |
| Energy Total        | 5        | 1     | kWh     | R   | Gesamtenergie |

## Heating Circuit (HC1)

### Sensors
| Name                          | Register | minFW | Einheit | R/W | Beschreibung |
|-------------------------------|----------|-------|---------|-----|--------------|
| Error Number                  | 0        | 1     | -       | R   | Fehlernummer |
| Operating State               | 1        | 1     | -       | R   | Betriebszustand |
| Flow Line Temperature         | 2        | 1     | °C      | R   | Vorlauftemperatur |
| Return Line Temperature       | 3        | 1     | °C      | R   | Rücklauftemperatur |
| Room Device Temperature       | 4        | 1     | °C      | R   | Raumgerät-Temperatur |
| Set Flow Line Temperature     | 5        | 1     | °C      | R   | Einstellung Vorlauftemperatur |
| Operating Mode                | 6        | 1     | -       | R   | Betriebsmodus |
| Target Flow Line Temperature  | 7        | 3     | °C      | R   | Ziel Vorlauftemperatur |
| Set Flow Line Offset Temp     | 50       | 1     | °C      | R   | Einstellung Vorlauf-Offset-Temperatur |
| Target Room Temperature       | 51       | 1     | °C      | RW  | Ziel-Raumtemperatur |
| Set Cooling Mode Room Temp    | 52       | 1     | °C      | R   | Einstellung Kühlmodus-Raumtemperatur |

## General Sensors (Main Controller)

### Ambient Sensors
| Name                           | Register | minFW | Einheit | R/W | Beschreibung |
|--------------------------------|----------|-------|---------|-----|--------------|
| Ambient Error Number           | 0        | 1     | -       | R   | Umgebungsfehlernummer |
| Ambient Operating State        | 1        | 1     | -       | R   | Umgebungsbetriebszustand |
| Ambient Temperature            | 2        | 1     | °C      | R   | Umgebungstemperatur |
| Ambient Temperature 1h         | 3        | 1     | °C      | R   | Umgebungstemperatur 1h |
| Ambient Temperature Calculated | 4        | 1     | °C      | R   | Berechnete Umgebungstemperatur |

### E-Manager Sensors
| Name                           | Register | minFW | Einheit | R/W | Beschreibung |
|--------------------------------|----------|-------|---------|-----|--------------|
| E-Manager Error Number         | 100      | 1     | -       | R   | E-Manager Fehlernummer |
| E-Manager Operating State      | 101      | 1     | -       | R   | E-Manager Betriebszustand |
| E-Manager Actual Power         | 102      | 1     | W       | R   | E-Manager tatsächliche Leistung |
| E-Manager Power Consumption    | 103      | 1     | W       | R   | E-Manager Leistungsaufnahme |
| E-Manager Power Consumption Setpoint | 104 | 1     | W       | R   | E-Manager Leistungsaufnahme Sollwert |

### Dummy Sensors
| Name                           | Register | minFW | Einheit | R/W | Beschreibung |
|--------------------------------|----------|-------|---------|-----|--------------|
| Dummy General FW2              | 999      | 2     | -       | R   | Dummy für Firmware 2 |

## Climate Entities

### Hot Water Climate (Boiler)
| Name                | Register | minFW | Einheit | R/W | Beschreibung |
|---------------------|----------|-------|---------|-----|--------------|
| Hot Water          | 2        | 1     | °C      | R   | Warmwasser-Temperatur |
| Hot Water Setpoint | 50       | 1     | °C      | RW  | Warmwasser-Temperatur Sollwert |

### Heating Circuit Climate
| Name                | Register | minFW | Einheit | R/W | Beschreibung |
|---------------------|----------|-------|---------|-----|--------------|
| Room Temperature    | 4        | 1     | °C      | R   | Raumtemperatur |
| Target Room Temp    | 51       | 1     | °C      | RW  | Ziel-Raumtemperatur |

## Base Addresses

Alle Geräte verwenden folgende Basis-Adressen:
- **Heat Pumps:** 1000 (HP1 = 1000, HP2 = 2000, HP3 = 3000)
- **Boilers:** 2000 (BOIL1 = 2000, BOIL2 = 2100, etc.)
- **Buffers:** 3000 (BUFF1 = 3000, BUFF2 = 3100, etc.)
- **Solar:** 4000 (SOL1 = 4000, SOL2 = 4100)
- **Heating Circuits:** 5000 (HC1 = 5000, HC2 = 5100, etc.)

## Firmware-Versionen

| Firmware | Version | Beschreibung |
|----------|---------|--------------|
| V0.0.9-3K | 7 | Aktuelle Firmware |
| V0.0.8-3K | 6 | Vorgängerversion – weiterhin häufig im Einsatz |
| V0.0.7-3K | 5 | Vorgängerversion |
| V0.0.6-3K | 4 | Ältere Version |
| V0.0.5-3K | 3 | Ältere Version |
| V0.0.4-3K | 2 | Ältere Version |
| V0.0.3-3K | 1 | Älteste unterstützte Version |

## Wichtige Hinweise

1. **Register-Adressen** sind relative Adressen innerhalb jedes Gerätebereichs
2. **minFW** gibt die minimale Firmware-Version an, ab der der Sensor verfügbar ist
3. **Einheiten** werden automatisch von der Integration gesetzt
4. **R/W** zeigt an, ob ein Sensor nur lesbar (R) oder lesbar/schreibbar (RW) ist
5. **Cycling-Sensoren** basieren auf Flankenerkennung und direkter Inkrementierung (keine Template-Berechnungen mehr)
6. **Energy Consumption Sensors** erfassen den Energieverbrauch nach Betriebsart (Heizen, Warmwasser, Kühlen, Abtauen, Standby) mit flanken-basierter Energiezuordnung
7. **Template-Sensoren** sind berechnete Sensoren mit Jinja2-Templates (z.B. COP Calculated)
8. **Climate-Entities** werden automatisch für Boiler und Heating Circuits erstellt
9. **Alle Sensoren** werden dynamisch basierend auf der Konfiguration erstellt

## Übersicht aller RW-Sensoren

| Gerät | Name | Register | minFW | Einheit | Beschreibung |
|-------|------|----------|-------|---------|--------------|
| **Boiler (BOIL1)** | Target High Temperature | 50 | 1 | °C | Ziel hohe Temperatur |
| **Buffer (BUFF1)** | Buffer High Temperature Setpoint | 4 | 1 | °C | Buffer hohe Temperatur Sollwert |
| **Heating Circuit (HC1)** | Target Room Temperature | 51 | 1 | °C | Ziel-Raumtemperatur |
| **Climate - Hot Water** | Hot Water Setpoint | 50 | 1 | °C | Warmwasser-Temperatur Sollwert |
| **Climate - Heating Circuit** | Target Room Temp | 51 | 1 | °C | Ziel-Raumtemperatur |

**Hinweise zu RW-Sensoren:**
- **RW-Sensoren** können sowohl gelesen als auch geschrieben werden
- **Sollwerte** können über Home Assistant oder Automatisierungen gesetzt werden
- **Temperatur-Sollwerte** werden direkt an die Geräte übertragen
- **Alle RW-Sensoren** sind temperaturbezogen und steuern das Heiz-/Kühlsystem

---
**Hinweis:** Diese Dokumentation basiert auf der aktuellen `const.py` und wird automatisch aktualisiert, wenn neue Sensoren hinzugefügt werden.



