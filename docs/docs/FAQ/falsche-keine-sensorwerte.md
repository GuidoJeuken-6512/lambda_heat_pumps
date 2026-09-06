---
title: "FAQ – Falsche / keine Sensorwerte"
---

# Falsche oder keine Sensorwerte

*Zuletzt geändert am 06.09.2026*

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

Seit Version 3.5 stellen Sie die Register-Reihenfolge für 32-Bit-Werte als **Integrations-Option** ein, nicht mehr in der `lambda_wp_config.yaml`:

1. **Einstellungen** → **Geräte & Dienste** → Ihre Lambda-Integration → **Konfigurieren**
2. Option **Register-Reihenfolge** auf `high_first` oder `low_first` stellen

**Vorgehen:**

1. Zeigen Ihre Sensoren **falsche** Werte → probieren Sie die andere Einstellung:
   - bisher `high_first` → auf `low_first` wechseln  
   - bisher `low_first` → auf `high_first` wechseln  
2. Die Änderung lädt die Integration automatisch neu.
3. Werte prüfen; bei korrekter Einstellung sollten die Anzeigen mit der Lambda-Software übereinstimmen.

Weitere Hinweise und Firmware-Anpassungen: [Anpassungen der Sensoren abhängig von der Firmware](../Anwender/anpassungen-sensoren-firmware.md).

---

## 2. Sensoren liefern keine Werte (unavailable / fehlen)

### Problematik

- Einzelne Sensoren bleiben **unavailable** oder erscheinen gar nicht.
- Im Log treten **Modbus-Fehler** oder Timeouts für bestimmte Register auf.
- Typisch bei **anderen Firmware-Versionen** oder Geräten, die nicht alle Register unterstützen.
    - Die Konfiguration der Zirkulationspumpe ist so ein Beispiel, es ist nicht automatisiert auswertbar, wie die Lambda konfiguriert wurde.

### Lösung

Seit Version 3.5 gibt es kein `disabled_registers` in der `lambda_wp_config.yaml` mehr – deaktivieren Sie stattdessen die betroffene **Entität** direkt in Home Assistant:

**Vorgehen:**

1. Den betroffenen Sensor in Home Assistant öffnen (Einstellungen → Geräte & Dienste → Entitäten, oder direkt über die Detailseite).
2. Auf das **Zahnrad** klicken und die Entität **deaktivieren**.
3. Optional: Bei zusätzlichen Log-Fehlern die Firmware-Version in den Integrations-Optionen prüfen – ein Register, das Ihre Firmware laut Konfiguration nicht haben sollte, wird ohnehin nicht gelesen (siehe [Anpassungen der Sensoren abhängig von der Firmware](../Anwender/anpassungen-sensoren-firmware.md)).

Eine deaktivierte Entität wird nicht mehr abgefragt, dadurch verschwinden die zugehörigen Fehler im Log.

Ausführliche Anleitung: [Entitäten löschen](../Anwender/entitaeten_loeschen.md).

---

## 3. Außentemperatur oder Puffer-Anforderung zeigt -300 °C / eine unrealistische Anforderung

### Problematik

- Die Außentemperatur (`ambient_temperature`) zeigt exakt **-300 °C**, oder eine
  Puffer-Anforderung (z. B. Vorlauf-/Rücklauf-Sollwert) zeigt einen
  unrealistischen, konstanten Wert.
- Betroffen sind Installationen ohne extern eingespeisten Außenfühler bzw.
  ohne aktive Anforderung an einen Puffer.

**Ursache:** Die Lambda-Steuerung meldet auf diesen Registern `0xFFFF` (−1),
wenn kein externer Sensor eingespeist ist bzw. keine Anforderung besteht.
Skaliert sieht das wie ein echter Messwert aus (−300,0 °C), ist aber keiner.
Bis einschließlich Version 3.5.1 wurde dieser Sonderwert bei diesen Registern
nicht herausgefiltert.

### Lösung

Ab Version 3.5.2 wird `0xFFFF` bei den betroffenen Registern (Außentemperatur
sowie den Puffer-/Heizkreis-Anforderungsregistern) als „nicht verfügbar“
(`unknown`) statt als Messwert angezeigt. Ein Update der Integration behebt
dies ohne weitere Konfiguration.
