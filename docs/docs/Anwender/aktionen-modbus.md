---
title: "Aktionen (read / write Modbus register)"
---

# Aktionen (read / write Modbus register)

Die Lambda Heat Pumps Integration bietet Actions zum direkten Lesen und Schreiben von Modbus-Registern. Diese Funktionen sind nützlich für Automatisierungen, erweiterte Konfigurationen, Fehlerbehebung oder spezielle Anwendungsfälle.

## Verfügbare Actionen

### read_modbus_register

Liest einen Wert aus einem Modbus-Register.

**Action**: `lambda_heat_pumps.read_modbus_register`

**Parameter:**
- `register_address` (erforderlich): Die Adresse des zu lesenden Registers (Integer)

**Rückgabewert:**
- `value`: Der gelesene Wert (Integer)

**Beispiel:**
```yaml
actions:
  - action: lambda_heat_pumps.read_modbus_register
    metadata: {}
    data:
      register_address: 1003
mode: single
```

**Verwendung in Automatisierungen:**
```yaml
automation:
  - alias: "Modbus Register lesen"
    trigger:
      - platform: time
        at: "12:00:00"
    actions:
      - action: lambda_heat_pumps.read_modbus_register
        metadata: {}
        data:
          register_address: 1003
      - action: system_log.write
        metadata: {}
        data:
          message: "Register 1003 Wert: {{ states('sensor.last_modbus_read') }}"
    mode: single
```

### write_modbus_register

Schreibt einen Wert in ein Modbus-Register.

**Action**: `lambda_heat_pumps.write_modbus_register`

**Parameter:**
- `register_address` (erforderlich): Die Adresse des zu schreibenden Registers (Integer)
- `value` (erforderlich): Der zu schreibende Wert (Integer, Bereich: -32768 bis 32767)

**Beispiel:**
```yaml
actions:
  - action: lambda_heat_pumps.write_modbus_register
    metadata: {}
    data:
      register_address: 1003
      value: 50
mode: single
```

**Verwendung in Automatisierungen:**
```yaml
automation:
  - alias: "Modbus Register schreiben"
    trigger:
      - platform: state
        entity_id: input_number.target_temp
    actions:
      - action: lambda_heat_pumps.write_modbus_register
        metadata: {}
        data:
          register_address: 1003
          value: "{{ states('input_number.target_temp') | int }}"
    mode: single
```

## Verwendung über Developer Tools

<img src="../../assets/dev_tools_actions_de.png" alt="DevTools Actions" style="width: 60%; height: auto; border-radius: 8px;">

### Register lesen

1. **Öffnen Sie Home Assistant:**
   - Gehen Sie zu **Entwicklertools** → **Services**

2. **Service auswählen:**
   - Wählen Sie `lambda_heat_pumps.read_modbus_register` aus

3. **Parameter eingeben:**
   - `register_address`: Geben Sie die Register-Adresse ein (z.B. `1003`)

4. **Service aufrufen:**
   - Klicken Sie auf **Service aufrufen**
   - Der gelesene Wert wird in den Logs angezeigt

### Register schreiben

1. **Öffnen Sie Home Assistant:**
   - Gehen Sie zu **Entwicklertools** → **Services**

2. **Service auswählen:**
   - Wählen Sie `lambda_heat_pumps.write_modbus_register` aus

3. **Parameter eingeben:**
   - `register_address`: Geben Sie die Register-Adresse ein (z.B. `2050`)
   - `value`: Geben Sie den zu schreibenden Wert ein (z.B. `500`)
   In diesem Beispiel würden sie die SollTemperatur des Boiler1 auf 50°C setzten.

4. **Service aufrufen:**
   - Klicken Sie auf **Service aufrufen**
   - Der Wert wird an die Lambda geschrieben

## Wichtige Register-Adressen
**Hinweis:** Die Temperatursensoren haben eine Skalierung von "0,1", für 1°C muss also der Wert "10" an die Aktion übergeben werden 
### Wärmepumpe (HP1)

- **Register 1002**: HP1 State (lesbar)
- **Register 1003**: HP1 Operating State (lesbar)
- **Register 1004**: HP1 Flow Temperature (lesbar)
- **Register 1005**: HP1 Return Temperature (lesbar)

### Heizkreis (HC1)

- **Register 5000**: HC1 Error Number (lesbar)
- **Register 5001**: HC1 Operating State (lesbar)
- **Register 5004**: HC1 Room Device Temperature (lesbar / schreibbar)
- **Register 5007**: HC1 Target Flow Temperature (lesbar, wird von Raumthermostat geschrieben)
- **Register 5051**: HC1 Target Room Temperature (lesbar / schreibbar)

### Kessel (Boil1)

- **Register 2000**: Boil1 Error Number (lesbar)
- **Register 2001**: Boil1 Operating State (lesbar)
- **Register 2002**: Boil1 Actual High Temperature (lesbar)
- **Register 2050**: Boil1 Target High Temperature (lesbar / schreibbar)

### PV-Überschuss

- **Register 102**: E-Manager Actual Power (lesbar / schreibbar, wird von PV-Surplus geschrieben)

**Hinweis**: Diese Adressen sind Beispiele. Die tatsächlichen Register-Adressen können je nach Firmware-Version und Konfiguration variieren. Konsultieren Sie die Modbus-Dokumentation Ihrer Lambda-Wärmepumpe für genaue Adressen.

## Beispiel-Anwendungsfälle

### Beispiel 1: Register-Wert überwachen

Überwachen Sie einen Register-Wert und senden Sie eine Benachrichtigung bei Änderungen:

```yaml
automation:
  - alias: "Register-Wert überwachen"
    trigger:
      - platform: time_pattern
        minutes: /5  # Alle 5 Minuten
    actions:
      - action: lambda_heat_pumps.read_modbus_register
        metadata: {}
        data:
          register_address: 1003
      - action: notify.mobile_app
        metadata: {}
        data:
          message: "Register 1003 wurde gelesen"
    mode: single
```

### Beispiel 2: Temperatur manuell setzen

Setzen Sie eine Temperatur direkt über Modbus:

```yaml
script:
  set_target_temp:
    sequence:
      - action: lambda_heat_pumps.write_modbus_register
        metadata: {}
        data:
          register_address: 5004
          value: "{{ target_temp | int }}"
```

### Beispiel 3: Register-Werte protokollieren

Protokollieren Sie Register-Werte regelmäßig:

```yaml
automation:
  - alias: "Register-Werte protokollieren"
    trigger:
      - platform: time_pattern
        hours: /1  # Jede Stunde
    actions:
      - action: lambda_heat_pumps.read_modbus_register
        metadata: {}
        data:
          register_address: 1003
      - action: system_log.write
        metadata: {}
        data:
          message: "Register 1003: {{ states('sensor.last_modbus_read') }}"
    mode: single
```

## Einschränkungen

### 16-Bit-Register

Die Actions unterstützen derzeit nur **16-Bit-Register** (einzelne Register):

- **Wertebereich**: -32768 bis 32767
- **32-Bit-Register**: Werden derzeit nicht unterstützt (siehe [Hinweis](#hinweis-32-bit-register))

### Hinweis: 32-Bit-Register

Die Actions `read_modbus_register` und `write_modbus_register` können derzeit **nicht** mit 32-Bit-Registern umgehen. Dies führt zu Fehlern beim Lesen/Schreiben von 32-Bit-Registern.

**Betroffene Register:**
- `compressor_power_consumption_accumulated` (Register 20, INT32)
- `compressor_thermal_energy_output_accumulated` (Register 22, INT32)
- Weitere 32-Bit-Register

**Workaround**: Verwenden Sie die entsprechenden Sensoren der Integration, die 32-Bit-Register korrekt lesen können.


⚠️ **WICHTIG**: Das direkte Schreiben von Modbus-Registern kann die Funktion Ihrer Lambda-Wärmepumpe beeinträchtigen. 

- **Vorsicht**: Schreiben Sie nur Register, die Sie verstehen
- **Backup**: Erstellen Sie ein Backup Ihrer Konfiguration vor Änderungen
- **Dokumentation**: Konsultieren Sie die Modbus-Dokumentation Ihrer Lambda-Wärmepumpe
- **Testen**: Testen Sie Änderungen in einer sicheren Umgebung
