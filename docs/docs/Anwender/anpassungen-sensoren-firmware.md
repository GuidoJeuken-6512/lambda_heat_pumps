---
title: "Anpassungen der Sensoren abhängig von der Firmware"
---

# Anpassungen der Sensoren abhängig von der Firmware

*Zuletzt geändert am 06.09.2026*

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
- **Korrektur**: Öffnen Sie **Einstellungen** → **Geräte & Dienste** → Ihre Lambda-Integration → Menü (⋮) → **Neu konfigurieren** und wählen Sie dort die richtige Firmware. Die Firmware lässt sich **nicht** über die normalen Integrations-**Optionen** ändern, nur über „Neu konfigurieren" – das lädt die Integration danach automatisch neu.

## Sensor-Filterung basierend auf Firmware

Die Integration filtert Sensoren automatisch basierend auf der Firmware-Version:

- **Unterstützte Sensoren**: Nur Sensoren, die für Ihre Firmware-Version verfügbar sind, werden erstellt
- **Nicht unterstützte Sensoren**: Sensoren, die für Ihre Firmware-Version nicht verfügbar sind, werden nicht erstellt
- **Automatische Filterung**: Die Filterung erfolgt automatisch beim Start der Integration

Unabhängig davon probt die Integration bei jedem Start zusätzlich, welche Register der **konkrete** Controller tatsächlich beantwortet. Ein Sensor entsteht also nur, wenn beide Prüfungen ihn zulassen: die gewählte Firmware kennt das Register, **und** der Controller antwortet tatsächlich darauf.

## Manuelle Anpassungen

Für Register, die Ihre Lambda zwar meldet, aber die Sie nicht brauchen oder die falsche Werte liefern (z. B. eine nicht vorhandene Zirkulationspumpe), gibt es seit Version 3.5 keinen eigenen YAML-Mechanismus mehr (`disabled_registers`/`sensors_names_override` sind entfallen). Nutzen Sie stattdessen die Bordmittel von Home Assistant:

- **Sensor nicht anzeigen/lesen**: Entität in der Entity-Registry **deaktivieren** (Entität öffnen → Zahnrad → Deaktivieren). Details: [Entitäten löschen](entitaeten_loeschen.md).
- **Sensor anders benennen**: Entität in Home Assistant **umbenennen** (Entität öffnen → Zahnrad → Name ändern). `unique_id` und Historie bleiben dabei erhalten.

## Register-Reihenfolge-Konfiguration

Für 32-Bit-Werte aus mehreren 16-Bit-Registern (die beiden Energiezähler jeder Wärmepumpe, der Solar-Ertragszähler) kann die Register-Reihenfolge konfiguriert werden – seit 3.5 als **Integrations-Option**, nicht mehr in `lambda_wp_config.yaml`:

1. Gehen Sie zu **Einstellungen** → **Geräte & Dienste** → Ihre Lambda-Integration → **Konfigurieren**
2. Stellen Sie **Register-Reihenfolge** auf `high_first` oder `low_first`

**Wann ist das wichtig?**
- Jede Firmware hat einen dokumentierten Standardwert, den die Integration automatisch vorschlägt (z. B. `high_first` bis einschließlich V0.0.9-3K, `low_first` ab V0.0.10-3K) – Sie müssen die Option also nur ändern, wenn Ihr konkretes Gerät davon abweicht.
- **Rückwärtskompatibilität**: War in einer älteren `lambda_wp_config.yaml` bereits `int32_register_order` (oder das noch ältere `int32_byte_order`/`big`/`little`) gesetzt, übernimmt die Integration diesen Wert beim ersten Start nach dem Update einmalig automatisch in die neue Option.

**Fehlerbehebung:**
- Falls Sie falsche Werte in den Sensoren sehen, versuchen Sie die andere Register-Reihenfolge-Einstellung

## Firmware-Update

Wenn Sie die Firmware Ihrer Lambda-Wärmepumpe aktualisieren:

1. **Überprüfen Sie die neue Firmware-Version:**
   - Finden Sie die neue Firmware-Version auf der Lambda-Bedienoberfläche

2. **Aktualisieren Sie die Konfiguration:**
   - Gehen Sie zu **Einstellungen** → **Geräte & Dienste**
   - Klicken Sie auf Ihre Lambda-Integration
   - Öffnen Sie das Menü (⋮) und wählen Sie **Neu konfigurieren** (nicht „Konfigurieren"/Optionen)
   - Aktualisieren Sie die Firmware-Version

3. **Neuladen abwarten:**
   - „Neu konfigurieren" lädt die Integration danach automatisch neu; ein manueller Neustart von Home Assistant ist nicht nötig

4. **Überprüfen Sie die Sensoren:**
   - Überprüfen Sie, ob alle erwarteten Sensoren vorhanden sind
   - Überprüfen Sie, ob die Sensoren korrekte Werte anzeigen

## Häufige Probleme

### "Sensor fehlt nach Firmware-Update"
- **Ursache**: Firmware-Version wurde nicht aktualisiert
- **Lösung**: Aktualisieren Sie die Firmware-Version über „Neu konfigurieren" (siehe oben)

### "Falsche Werte in Sensoren"
- **Ursache**: Falsche Register-Reihenfolge für 32-Bit-Werte
- **Lösung**: Ändern Sie die Option **Register-Reihenfolge** in den Integrations-Optionen von `high_first` zu `low_first` oder umgekehrt

### "Register-Fehler im Log"
- **Ursache**: Register wird von der Firmware nicht unterstützt
- **Lösung**: Deaktivieren Sie die betroffene Entität in Home Assistant (siehe oben) – das unterdrückt die Fehlermeldung, da das Register dann nicht mehr gelesen wird

## Nächste Schritte

Nach der Anpassung der Sensoren können Sie:

- [Warmwasser Solltemperatur Steuerung](warmwasser-solltemperatur.md) einrichten
- [Raumthermometer](raumthermometer.md) konfigurieren
- [Energie- und Wärmeverbrauchsberechnung](Energieverbrauchsberechnung.md) einrichten
