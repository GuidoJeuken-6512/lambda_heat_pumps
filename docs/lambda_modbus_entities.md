# Übersicht aller Home Assistant Entitäten (Modbus Lambda Heat Pumps)

**Annahme:** Jeweils 1 Gerät pro Typ: 1 HP, 1 Boiler, 1 Buffer, 1 Solar, 1 Heating Circuit

**Legende:** R = Read-only (nur lesbar), RW = Read/Write (lesbar und schreibbar)

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

### Calculated Sensors (Template-basiert)
| Name                          | Typ | Einheit | R/W | Beschreibung |
|-------------------------------|-----|---------|-----|--------------|
| Heating Cycling Total         | TOTAL | cycles | R   | Gesamtzahl Heizzyklen |
| Hot Water Cycling Total       | TOTAL | cycles | R   | Gesamtzahl Warmwasserzyklen |
| Cooling Cycling Total         | TOTAL | cycles | R   | Gesamtzahl Kühlzyklen |
| Defrost Cycling Total         | TOTAL | cycles | R   | Gesamtzahl Abtauzyklen |
| Heating Cycling Yesterday     | TOTAL | cycles | R   | Heizzyklen von gestern |
| Hot Water Cycling Yesterday   | TOTAL | cycles | R   | Warmwasserzyklen von gestern |
| Cooling Cycling Yesterday     | TOTAL | cycles | R   | Kühlzyklen von gestern |
| Defrost Cycling Yesterday     | TOTAL | cycles | R   | Abtauzyklen von gestern |
| Heating Cycling Daily         | DAILY | cycles | R   | Tägliche Heizzyklen |
| Hot Water Cycling Daily       | DAILY | cycles | R   | Tägliche Warmwasserzyklen |
| Cooling Cycling Daily         | DAILY | cycles | R   | Tägliche Kühlzyklen |
| Defrost Cycling Daily         | DAILY | cycles | R   | Tägliche Abtauzyklen |

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
| V0.0.8-3K | 6 | Aktuelle Firmware - am häufigsten |
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
5. **Berechnete Sensoren** basieren auf Template-Logik und anderen Sensor-Werten
6. **Climate-Entities** werden automatisch für Boiler und Heating Circuits erstellt
7. **Alle Sensoren** werden dynamisch basierend auf der Konfiguration erstellt

---
**Hinweis:** Diese Dokumentation basiert auf der aktuellen `const.py` und wird automatisch aktualisiert, wenn neue Sensoren hinzugefügt werden.



