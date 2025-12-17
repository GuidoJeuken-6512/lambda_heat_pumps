---
title: "Aktionen (read / write Modbus register)"
---

# Aktionen (read / write Modbus register)

Die Lambda Heat Pumps Integration bietet Services zum direkten Lesen und Schreiben von Modbus-Registern. Diese Funktionen sind nützlich für erweiterte Konfigurationen, Fehlerbehebung oder spezielle Anwendungsfälle.

## Verfügbare Services

### read_modbus_register

Liest einen Wert aus einem Modbus-Register.

**Service**: `lambda_heat_pumps.read_modbus_register`

**Parameter:**
- `register_address` (erforderlich): Die Adresse des zu lesenden Registers (Integer)

**Rückgabewert:**
- `value`: Der gelesene Wert (Integer)

**Beispiel:**
```yaml
service: lambda_heat_pumps.read_modbus_register
data:
  register_address: 1003
```

**Verwendung in Automatisierungen:**
```yaml
automation:
  - alias: "Modbus Register lesen"
    trigger:
      - platform: time
        at: "12:00:00"
    action:
      - service: lambda_heat_pumps.read_modbus_register
        data:
          register_address: 1003
      - service: system_log.write
        data:
          message: "Register 1003 Wert: {{ states('sensor.last_modbus_read') }}"
```

### write_modbus_register

Schreibt einen Wert in ein Modbus-Register.

**Service**: `lambda_heat_pumps.write_modbus_register`

**Parameter:**
- `register_address` (erforderlich): Die Adresse des zu schreibenden Registers (Integer)
- `value` (erforderlich): Der zu schreibende Wert (Integer, Bereich: -32768 bis 65535)

**Beispiel:**
```yaml
service: lambda_heat_pumps.write_modbus_register
data:
  register_address: 1003
  value: 50
```

**Verwendung in Automatisierungen:**
```yaml
automation:
  - alias: "Modbus Register schreiben"
    trigger:
      - platform: state
        entity_id: input_number.target_temp
    action:
      - service: lambda_heat_pumps.write_modbus_register
        data:
          register_address: 1003
          value: "{{ states('input_number.target_temp') | int }}"
```

## Verwendung über Developer Tools

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
   - `register_address`: Geben Sie die Register-Adresse ein (z.B. `1003`)
   - `value`: Geben Sie den zu schreibenden Wert ein (z.B. `50`)

4. **Service aufrufen:**
   - Klicken Sie auf **Service aufrufen**
   - Der Wert wird an die Lambda geschrieben

## Wichtige Register-Adressen

### Wärmepumpe (HP1)

- **Register 1002**: HP1 State
- **Register 1003**: HP1 Operating State
- **Register 1004**: HP1 Flow Temperature
- **Register 1005**: HP1 Return Temperature

### Heizkreis (HC1)

- **Register 5000**: HC1 Target Room Temperature
- **Register 5001**: HC1 Room Device Temperature
- **Register 5004**: HC1 Target Flow Temperature (wird von Raumthermostat geschrieben)

### Kessel (Boil1)

- **Register 2000**: Boil1 Target Temperature
- **Register 2001**: Boil1 Actual Temperature

### PV-Überschuss

- **Register 102**: E-Manager Actual Power (wird von PV-Surplus geschrieben)

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
    action:
      - service: lambda_heat_pumps.read_modbus_register
        data:
          register_address: 1003
      - service: notify.mobile_app
        data:
          message: "Register 1003 wurde gelesen"
```

### Beispiel 2: Temperatur manuell setzen

Setzen Sie eine Temperatur direkt über Modbus:

```yaml
script:
  set_target_temp:
    sequence:
      - service: lambda_heat_pumps.write_modbus_register
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
    action:
      - service: lambda_heat_pumps.read_modbus_register
        data:
          register_address: 1003
      - service: system_log.write
        data:
          message: "Register 1003: {{ states('sensor.last_modbus_read') }}"
```

## Einschränkungen

### 16-Bit-Register

Die Services unterstützen derzeit nur **16-Bit-Register** (einzelne Register):

- **Wertebereich**: -32768 bis 65535
- **32-Bit-Register**: Werden derzeit nicht unterstützt (siehe [Hinweis](#hinweis-32-bit-register))

### Hinweis: 32-Bit-Register

Die Services `read_modbus_register` und `write_modbus_register` können derzeit **nicht** mit 32-Bit-Registern umgehen. Dies führt zu Fehlern beim Lesen/Schreiben von 32-Bit-Registern.

**Betroffene Register:**
- `compressor_power_consumption_accumulated` (Register 20, INT32)
- `compressor_thermal_energy_output_accumulated` (Register 22, INT32)
- Weitere 32-Bit-Register

**Workaround**: Verwenden Sie die entsprechenden Sensoren der Integration, die 32-Bit-Register korrekt lesen können.

## Fehlerbehebung

### "Service nicht gefunden"
- **Ursache**: Integration nicht korrekt installiert oder nicht konfiguriert
- **Lösung**: 
  - Überprüfen Sie, ob die Integration korrekt installiert ist
  - Überprüfen Sie, ob die Integration konfiguriert ist
  - Starten Sie Home Assistant neu

### "Register-Fehler"
- **Ursache**: Register-Adresse existiert nicht oder ist nicht zugänglich
- **Lösung**: 
  - Überprüfen Sie die Register-Adresse
  - Überprüfen Sie die Modbus-Verbindung
  - Überprüfen Sie die Logs auf Fehlermeldungen

### "Wert außerhalb des Bereichs"
- **Ursache**: Wert liegt außerhalb des erlaubten Bereichs (-32768 bis 65535)
- **Lösung**: Verwenden Sie einen Wert innerhalb des erlaubten Bereichs

### "32-Bit-Register-Fehler"
- **Ursache**: Versuch, ein 32-Bit-Register zu lesen/schreiben
- **Lösung**: 
  - Verwenden Sie die entsprechenden Sensoren der Integration
  - 32-Bit-Register werden derzeit nicht von den Services unterstützt

## Sicherheitshinweise

⚠️ **WICHTIG**: Das direkte Schreiben von Modbus-Registern kann die Funktion Ihrer Lambda-Wärmepumpe beeinträchtigen. 

- **Vorsicht**: Schreiben Sie nur Register, die Sie verstehen
- **Backup**: Erstellen Sie ein Backup Ihrer Konfiguration vor Änderungen
- **Dokumentation**: Konsultieren Sie die Modbus-Dokumentation Ihrer Lambda-Wärmepumpe
- **Testen**: Testen Sie Änderungen in einer sicheren Umgebung

## Nächste Schritte

Nach der Verwendung der Modbus-Aktionen können Sie:

- [Stromverbrauchsberechnung](stromverbrauchsberechnung.md) einrichten
- [Optionen des config_flow](optionen-config-flow.md) anpassen
- [Historische Daten übernehmen](historische-daten.md) bei Wärmepumpenwechsel

