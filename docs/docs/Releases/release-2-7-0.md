---
title: "Release 2.7.0"
---

# Release 2.7.0

*Zuletzt geändert am 12.07.2026*

> **Aktueller Release** · Branch `V2.7.0`

---

## Zusammenfassung

Release 2.7.0 enthält einen Bugfix für Nutzer mit deutschen Umlauten im Gerätenamen sowie eine neue Möglichkeit, den Register-Order-Default für 32-Bit-Modbus-Sensoren pro Firmware-Version zu hinterlegen. Der Default für die beiden neuesten Firmware-Versionen (`V1.1.0-3K`, `V0.0.10-3K`) wurde dabei auf `"low_first"` korrigiert. Keine Breaking Changes.

---

## Fehlerbehebungen

### Umlaute im Gerätenamen lassen Energie-Sensor-Lookup fehlschlagen ([#93](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/93))

**Betroffen:** Nutzer, die im Options-Flow der Integration einen Gerätenamen mit Umlauten (z. B. `Wärmepumpe`) konfiguriert haben **und** keinen externen Energie-Sensor eingetragen haben (Fallback auf den integrierten Sensor).

### Falscher Default für 32-Bit-Register-Reihenfolge bei neuester Firmware

**Betroffen:** Nutzer mit Firmware `V1.1.0-3K` oder `V0.0.10-3K` ohne expliziten `int32_register_order`-Override in `lambda_wp_config.yaml`.

**Ursache:** Der neue firmware-abhängige Default (siehe unten) stand beim Einführen zunächst für alle Firmware-Versionen auf `"high_first"` — auch für die beiden neuesten, die tatsächlich `"low_first"` verwenden. int32-Sensoren (z. B. Energie-Akkumulation) konnten dadurch falsche Werte liefern.

**Fix:** `FIRMWARE_CONFIG` in `const_base.py` trägt für `V1.1.0-3K` und `V0.0.10-3K` nun `"reg_order": "low_first"`. Ein manueller YAML-Override bleibt unverändert vorrangig.

**Symptom:** Im Debug-Log erscheinen wiederholt Zeilen wie:

```
[Energy] HP1 electrical: Sensor sensor.wärmepumpe_hp1_compressor_power_consumption_accumulated nicht verfügbar (state=None)
```

**Ursache:** Home Assistants Entity Registry transliteriert Umlaute beim ersten Anlegen einer Entity automatisch zu ASCII (`ä` → `a`). Die tatsächliche Entity heißt daher `sensor.warmepumpe_hp1_…`, der interne Lookup konstruierte bislang jedoch `sensor.wärmepumpe_hp1_…` — die Namen stimmten nie überein.

**Fix:** Neue Hilfsfunktion `slugify_name_prefix_for_lookup()` in `utils.py`, die für rein lesende Lookups dieselbe Transliteration anwendet wie Home Assistants Entity Registry. Alle `unique_id`-relevanten Pfade sind unverändert — keine Auswirkung auf bestehende Entities, Verlauf oder Zählerstand.

**Betroffene Dateien:** `custom_components/lambda_heat_pumps/utils.py`, `custom_components/lambda_heat_pumps/coordinator.py`

---

## Neue Funktionen

### Firmware-abhängiger Default für die Register-Reihenfolge (`int32_register_order`)

**Betroffen:** `custom_components/lambda_heat_pumps/const_base.py` · `custom_components/lambda_heat_pumps/modbus_utils.py` · `custom_components/lambda_heat_pumps/__init__.py`

Bisher war der Default für die 32-Bit-Register-Reihenfolge (`"high_first"`) hartkodiert — unabhängig von der konfigurierten Firmware-Version. Da der korrekte Wert pro Firmware-Version unterschiedlich sein kann, trägt nun jeder Eintrag in der Firmware-Konfiguration seinen zugehörigen Register-Order-Default.

**Neue Struktur `FIRMWARE_CONFIG` in `const_base.py`:**

```python
FIRMWARE_CONFIG: dict[str, dict] = {
    "V1.1.0-3K":  {"version": 9, "reg_order": "low_first"},
    "V0.0.10-3K": {"version": 8, "reg_order": "low_first"},
    # ...
}
# Rückwärtskompatibilität — alle bestehenden Aufrufer unverändert:
FIRMWARE_VERSION: dict[str, int] = {k: v["version"] for k, v in FIRMWARE_CONFIG.items()}
```

**Prioritätskette (von niedrig nach hoch):**

1. `"high_first"` — absoluter Fallback
2. `FIRMWARE_CONFIG[fw_version]["reg_order"]` — FW-abhängiger Default *(neu)*
3. `modbus.int32_byte_order` in `lambda_wp_config.yaml` — Legacy-Override
4. `modbus.int32_register_order` in `lambda_wp_config.yaml` — Expliziter Override

Der YAML-Override in `lambda_wp_config.yaml` bleibt vollständig erhalten und hat weiterhin Vorrang vor dem FW-Default.

**Für Entwickler / Maintainer:** Wenn eine neue Firmware-Version einen anderen Register-Order verwendet, genügt es, den entsprechenden Eintrag in `FIRMWARE_CONFIG` mit dem richtigen `"reg_order"`-Wert anzulegen — `FIRMWARE_VERSION` wird automatisch davon abgeleitet.

---

## Betroffene Dateien

| Datei | Änderung |
|---|---|
| `custom_components/lambda_heat_pumps/utils.py` | Neue Funktion `slugify_name_prefix_for_lookup()`; Import `ha_slugify` |
| `custom_components/lambda_heat_pumps/coordinator.py` | 2 Lookup-Stellen nutzen `slugify_name_prefix_for_lookup` statt `normalize_name_prefix` |
| `custom_components/lambda_heat_pumps/const_base.py` | `FIRMWARE_CONFIG` als neue Primärstruktur; `FIRMWARE_VERSION` als abgeleitetes Compat-Dict; `reg_order` für `V1.1.0-3K`/`V0.0.10-3K` auf `"low_first"` korrigiert |
| `custom_components/lambda_heat_pumps/modbus_utils.py` | `get_int32_register_order(hass, entry)` — FW-abhängiger Default vor YAML-Fallback |
| `custom_components/lambda_heat_pumps/__init__.py` | Call-Site übergibt `entry` an `get_int32_register_order` |
