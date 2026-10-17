---
title: "Anpassungen der Sensoren abhängig von der Firmware"
---

# Anpassungen der Sensoren abhängig von der Firmware

*Zuletzt geändert am 17.10.2026*

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
- **Korrektur**: Öffnen Sie **Einstellungen** → **Geräte & Dienste** → Ihre Lambda-Integration → Menü (⋮) → **Neu konfigurieren** und wählen Sie dort die richtige Firmware. Die Firmware lässt sich **nicht** über die normalen Integrations-**Optionen** ändern, nur über „Neu konfigurieren" – das lädt die Integration danach automatisch neu. Details: [Firmware-Version ändern](firmware-wechsel.md).

## Sensor-Filterung basierend auf Firmware

Die Integration filtert Sensoren automatisch basierend auf der Firmware-Version:

- **Unterstützte Sensoren**: Nur Sensoren, die für Ihre Firmware-Version verfügbar sind, werden erstellt
- **Nicht unterstützte Sensoren**: Sensoren, die für Ihre Firmware-Version nicht verfügbar sind, werden nicht erstellt
- **Automatische Filterung**: Die Filterung erfolgt automatisch beim Start der Integration

Unabhängig davon probt die Integration bei jedem Start zusätzlich, welche Register der **konkrete** Controller tatsächlich beantwortet. Ein Sensor entsteht also nur, wenn beide Prüfungen ihn zulassen: die gewählte Firmware kennt das Register, **und** der Controller antwortet tatsächlich darauf.

## Manuelle Anpassungen

Für Register, die Ihre Lambda zwar meldet, aber die Sie nicht brauchen oder die falsche Werte liefern (z. B. eine nicht vorhandene Zirkulationspumpe), gibt es seit Version 3.5 keinen eigenen YAML-Mechanismus mehr (`disabled_registers`/`sensors_names_override` sind entfallen). Nutzen Sie stattdessen die Bordmittel von Home Assistant:

- **Sensor nicht anzeigen**: Entität in der Entity-Registry **deaktivieren** (Entität öffnen → Zahnrad → Deaktivieren). Details: [Entitäten löschen](entitaeten_loeschen.md). Die Integration liest die Lambda seit 3.5 blockweise; das Register wird also weiterhin abgefragt, nur die Entität erscheint nicht mehr.
- **Sensor anders benennen**: Entität in Home Assistant **umbenennen** (Entität öffnen → Zahnrad → Name ändern). `unique_id` und Historie bleiben dabei erhalten.

## Register-Reihenfolge-Konfiguration

Für 32-Bit-Werte aus mehreren 16-Bit-Registern (die beiden Energiezähler jeder Wärmepumpe, der Solar-Ertragszähler) kann die Register-Reihenfolge konfiguriert werden – seit 3.5 als **Integrations-Option**, nicht mehr in `lambda_wp_config.yaml`:

1. Gehen Sie zu **Einstellungen** → **Geräte & Dienste** → Ihre Lambda-Integration → **Konfigurieren**
2. Stellen Sie **Register-Reihenfolge** auf `high_first` oder `low_first`

**Wann ist das wichtig?**
- Jede Firmware hat einen dokumentierten Standardwert, den die Integration automatisch vorschlägt (z. B. `high_first` bis einschließlich V0.0.9-3K, `low_first` ab V0.0.10-3K) – Sie müssen die Option also nur ändern, wenn Ihr konkretes Gerät davon abweicht.
- **Rückwärtskompatibilität**: War in einer älteren `lambda_wp_config.yaml` bereits `int32_register_order` (oder das noch ältere `int32_byte_order`/`big`/`little`) gesetzt, übernimmt die Integration diesen Wert beim ersten Start nach dem Update einmalig automatisch in die neue Option. Ohne Eintrag gilt die Reihenfolge der Firmware.
- **Firmwarewechsel**: Eine hier gewählte Reihenfolge wird zurückgesetzt, wenn Sie die Firmware über „Neu konfigurieren" ändern (ab 3.5.7).

**Fehlerbehebung:**
- Falls Sie falsche Werte in den Sensoren sehen, versuchen Sie die andere Register-Reihenfolge-Einstellung

## Firmware-Update

Wenn die Firmware Ihrer Lambda aktualisiert oder die Steuerung getauscht wurde, ändern Sie die Firmware-Version über **⋮ → Neu konfigurieren**. Ausführliche Anleitung, inklusive der Folgen für Sensoren und Register-Reihenfolge: [Firmware-Version ändern](firmware-wechsel.md).

## Häufige Probleme

### "Sensor fehlt nach Firmware-Update"
- **Ursache**: Firmware-Version wurde nicht aktualisiert
- **Lösung**: Aktualisieren Sie die Firmware-Version über „Neu konfigurieren" (siehe oben)

### "Falsche Werte in Sensoren"
- **Ursache**: Falsche Register-Reihenfolge für 32-Bit-Werte
- **Lösung**: Zuerst die Firmware-Version prüfen ([Firmware-Version ändern](firmware-wechsel.md)), dann ggf. die Option **Register-Reihenfolge** in den Integrations-Optionen von `high_first` zu `low_first` oder umgekehrt ändern. Siehe auch [Falsche / keine Sensorwerte](../FAQ/falsche-keine-sensorwerte.md).

### "Failed to fetch … im Log"
- **Ursache**: Ein Modul der Lambda hat auf die Abfrage nicht geantwortet. Die Meldung erscheint einmal, nicht bei jeder Abfrage; die Sensoren dieses Moduls sind so lange „nicht verfügbar“.
- **Lösung**: Verbindung prüfen. Bedient die Lambda ein Modul dauerhaft nicht mehr, lädt sich die Integration automatisch neu und erkennt die Module neu. Das Deaktivieren einer Entität ändert an der Abfrage nichts.

## Nächste Schritte

Nach der Anpassung der Sensoren können Sie:

- [Warmwasser Solltemperatur Steuerung](warmwasser-solltemperatur.md) einrichten
- [Raumthermometer](raumthermometer.md) konfigurieren
- [Energie- und Wärmeverbrauchsberechnung](Energieverbrauchsberechnung.md) einrichten
