---
title: "FAQ – Falsche / keine Sensorwerte"
---

# Falsche oder keine Sensorwerte

Hier finden Sie die häufigsten Ursachen und Lösungen, wenn Sensoren **falsche Werte** anzeigen oder **gar keine Werte** liefern.

---

## 1. Falsche Werte bei Energie- bzw. int32-Sensoren

### Problematik

- **Symptome:** Energie-Sensoren (Wh/kWh) oder andere 32-Bit-Sensoren zeigen **völlig falsche**, oft unrealistisch hohe oder niedrige Werte.
- **Lambda-Software** zeigt dagegen korrekte Werte.
- Betroffen sind vor allem **int32-Entitäten** (z. B. Akkumulations-Sensoren), die aus zwei 16-Bit-Modbus-Registern zusammengesetzt werden.

**Ursache:** Die **Reihenfolge der Register** (Register/Word Order) bei der Interpretation von 32-Bit-Werten ist je nach Gerät/Firmware unterschiedlich. Es geht nicht um Byte-Endianness innerhalb eines Registers, sondern darum, ob das höherwertige oder das niedrigere 16-Bit-Register zuerst gelesen wird. 

Leider kann nicht automatisch ermittelt werden, welche Register Reihenfolge die Lambda verwendet.

### Lösung

In der **lambda_wp_config.yaml** die Register-Reihenfolge für 32-Bit-Werte anpassen:

```yaml
modbus:
  # "high_first" = Höherwertiges Register zuerst (Standard)
  # "low_first" = Niedrigwertiges Register zuerst
  int32_register_order: "high_first"   # oder "low_first"
```

**Vorgehen:**

1. Zeigen Ihre Sensoren **falsche** Werte → probieren Sie die andere Einstellung:
   - bisher `high_first` → auf `low_first` wechseln  
   - bisher `low_first` → auf `high_first` wechseln  
2. Nach Änderung die Integration neu laden oder Home Assistant neu starten.
3. Werte prüfen; bei korrekter Einstellung sollten die Anzeigen mit der Lambda-Software übereinstimmen.

Weitere Hinweise und Firmware-Anpassungen: [Anpassungen der Sensoren abhängig von der Firmware](../Anwender/anpassungen-sensoren-firmware.md). Die technische Beschreibung (Register-Reihenfolge, Implementierung) ist in der Projekt-Dokumentation unter `docs_md/issue22_endianness_fix.md` (Issue #22) zu finden.

---

## 2. Sensoren liefern keine Werte (unavailable / fehlen)

### Problematik

- Einzelne Sensoren bleiben **unavailable** oder erscheinen gar nicht.
- Im Log treten **Modbus-Fehler** oder Timeouts für bestimmte Register auf.
- Typisch bei **anderen Firmware-Versionen** oder Geräten, die nicht alle Register unterstützen.
    - Die Konfiguration der Zirkulationspumpe ist so ein Beispiel, es ist nicht automatisiert auswertbar, wie die Lambda konfiguriert wurde.

### Lösung

Nicht unterstützte oder fehlerhafte Register in der **lambda_wp_config.yaml** deaktivieren:

```yaml
disabled_registers:
  - 2004   # Beispiel: boil1_actual_circulation_temp (nicht verfügbar)
  - 2005   # Weitere Register, die Fehler verursachen
```

**Vorgehen:**

1. Im Home-Assistant-Log die **Register-Adresse** des fehlschlagenden Zugriffs ermitteln.
2. Diese Adresse (als Zahl) unter `disabled_registers` in der **lambda_wp_config.yaml** eintragen.
3. Konfiguration speichern und Integration neu laden (oder Home Assistant neu starten).

Damit wird das Register nicht mehr gelesen; der zugehörige Sensor bleibt ohne Wert oder wird nicht angeboten, dafür verschwinden die Fehler und andere Sensoren arbeiten normal.

Der betreffende Sensor kann dann aus dem Dashboard in Home Assistant gelöscht werden.

Ausführliche Anleitung zur Konfiguration: [lambda_wp_config.yaml – disabled_registers](../Anwender/lambda-wp-config.md) bzw. [Anpassungen der Sensoren abhängig von der Firmware](../Anwender/anpassungen-sensoren-firmware.md).
