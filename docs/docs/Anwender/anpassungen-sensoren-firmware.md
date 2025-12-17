---
title: "Anpassungen der Sensoren abhängig von der Firmware"
---

# Anpassungen der Sensoren abhängig von der Firmware

Die Lambda Heat Pumps Integration erstellt automatisch Sensoren basierend auf der erkannten Hardware und der konfigurierten Firmware-Version. Die Firmware-Version bestimmt, welche Sensoren verfügbar sind und welche Register gelesen werden können.

## Firmware-Version und Sensor-Verfügbarkeit

### Firmware-Version finden

Um die Firmware-Version Ihrer Lambda-Wärmepumpe zu finden:

1. Klicken Sie auf der Lambda-Bedienoberfläche auf die Wärmepumpe
2. Klicken Sie auf die "i" Taste auf der linken Seite
3. Klicken Sie auf die Taste auf der rechten Seite, die wie ein Computerchip aussieht (letzte Taste)
4. Die Firmware-Version wird dort angezeigt

### Firmware-Version bei der Konfiguration

Bei der Initialkonfiguration müssen Sie die Firmware-Version auswählen:

- **Wichtig**: Die Firmware-Version bestimmt, welche Sensoren erstellt werden
- **Falsche Firmware-Version**: Kann zu fehlenden oder falschen Sensoren führen
- **Korrektur**: Wenn Sie die falsche Firmware-Version ausgewählt haben, müssen Sie die Integration entfernen und erneut hinzufügen

## Sensor-Filterung basierend auf Firmware

Die Integration filtert Sensoren automatisch basierend auf der Firmware-Version:

- **Unterstützte Sensoren**: Nur Sensoren, die für Ihre Firmware-Version verfügbar sind, werden erstellt
- **Nicht unterstützte Sensoren**: Sensoren, die für Ihre Firmware-Version nicht verfügbar sind, werden nicht erstellt
- **Automatische Filterung**: Die Filterung erfolgt automatisch beim Start der Integration

## Manuelle Anpassungen

### Deaktivierte Register

Sie können bestimmte Register deaktivieren, wenn sie Probleme verursachen oder nicht benötigt werden:

**Konfiguration in `lambda_wp_config.yaml`:**

```yaml
disabled_registers:
  - 2004  # Beispiel: boil1_actual_circulation_temp
  - 100000  # Beispiel: Weitere deaktivierte Register
```

**Zweck:**
- Verhindert das Lesen von problematischen Registern
- Reduziert Modbus-Traffic
- Behebt Probleme mit nicht unterstützten Registern

### Sensor-Name-Überschreibungen

Sie können Standard-Sensornamen überschreiben:

**Konfiguration in `lambda_wp_config.yaml`:**

```yaml
sensors_names_override:
  - id: hp1_flow_temp
    override_name: "Wohnzimmer Temperatur"
  - id: hp1_return_temp
    override_name: "Rücklauf Temperatur"
```

**Zweck:**
- Anpassung der Sensornamen für bessere Lesbarkeit
- Lokalisierung der Sensornamen
- Anpassung an persönliche Präferenzen

## Register-Reihenfolge-Konfiguration

Für 32-Bit-Werte aus mehreren 16-Bit-Registern kann die Register-Reihenfolge konfiguriert werden:

**Konfiguration in `lambda_wp_config.yaml`:**

```yaml
modbus:
  # Register-Reihenfolge für 32-Bit-Register (int32-Sensoren)
  # "high_first" = Höherwertiges Register zuerst (Standard)
  # "low_first" = Niedrigwertiges Register zuerst
  int32_register_order: "high_first"  # oder "low_first"
```

**Wann ist das wichtig?**
- **"high_first"**: Standard für die meisten Lambda-Modelle (höherwertiges Register zuerst)
- **"low_first"**: Erforderlich für bestimmte Lambda-Modelle oder Firmware-Versionen (niedrigwertiges Register zuerst)
- **Rückwärtskompatibilität**: Alte Config mit `int32_byte_order` oder alten Werten (`big`/`little`) wird automatisch erkannt und migriert

**Fehlerbehebung:**
- Falls Sie falsche Werte in den Sensoren sehen, versuchen Sie die andere Register-Reihenfolge-Einstellung

## Firmware-Update

Wenn Sie die Firmware Ihrer Lambda-Wärmepumpe aktualisieren:

1. **Überprüfen Sie die neue Firmware-Version:**
   - Finden Sie die neue Firmware-Version auf der Lambda-Bedienoberfläche

2. **Aktualisieren Sie die Konfiguration:**
   - Gehen Sie zu **Einstellungen** → **Geräte & Dienste**
   - Klicken Sie auf Ihre Lambda-Integration
   - Klicken Sie auf **Konfigurieren**
   - Aktualisieren Sie die Firmware-Version

3. **Home Assistant neu starten:**
   - Starten Sie Home Assistant neu, damit die neuen Sensoren erkannt werden

4. **Überprüfen Sie die Sensoren:**
   - Überprüfen Sie, ob alle erwarteten Sensoren vorhanden sind
   - Überprüfen Sie, ob die Sensoren korrekte Werte anzeigen

## Häufige Probleme

### "Sensor fehlt nach Firmware-Update"
- **Ursache**: Firmware-Version wurde nicht aktualisiert
- **Lösung**: Aktualisieren Sie die Firmware-Version in den Integration-Optionen

### "Falsche Werte in Sensoren"
- **Ursache**: Falsche Register-Reihenfolge für 32-Bit-Werte
- **Lösung**: Ändern Sie `int32_register_order` in `lambda_wp_config.yaml` von `"high_first"` zu `"low_first"` oder umgekehrt

### "Register-Fehler im Log"
- **Ursache**: Register wird von der Firmware nicht unterstützt
- **Lösung**: Fügen Sie das Register zur `disabled_registers` Liste in `lambda_wp_config.yaml` hinzu

## Nächste Schritte

Nach der Anpassung der Sensoren können Sie:

- [Warmwasser Solltemperatur Steuerung](warmwasser-solltemperatur.md) einrichten
- [Raumthermostat](raumthermostat.md) konfigurieren
- [Stromverbrauchsberechnung](stromverbrauchsberechnung.md) einrichten

