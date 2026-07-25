---
title: "Register-Reihenfolge für int32-Sensoren (Issue #22)"
---

# Register-Reihenfolge für int32-Sensoren

*Zuletzt geändert am 12.07.2026*

Technische Dokumentation zur konfigurierbaren Register-Reihenfolge (Register/Word Order) bei 32-Bit-Modbus-Werten. Basis: [Issue #22](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/22); erweitert in V2.7.0 um firmware-abhängigen Default.

## Problemstellung

### Symptome

- **Falsche Werte** bei int32-Entitäten (z. B. Energie-Akkumulation Wh/kWh).
- Lambda-Software zeigt korrekte Werte, Home Assistant zeigt abweichende oder unrealistische Werte.
- Betroffen sind nur **32-Bit-Sensoren**, die aus zwei 16-Bit-Modbus-Registern zusammengesetzt werden.

### Ursache

Es geht um die **Reihenfolge der Register (Register/Word Order)**, nicht um Byte-Endianness innerhalb eines einzelnen 16-Bit-Registers. Modbus nutzt innerhalb eines Registers typisch Big-Endian; die **Reihenfolge mehrerer Register** ist nicht normiert und kann je nach Gerät/Firmware unterschiedlich sein.

Die Integration bildet zwei 16-Bit-Register zu einem 32-Bit-Wert:

- **high_first (Standard):** `value = (Register[0] << 16) | Register[1]` (Register[0] = MSW, Register[1] = LSW)
- **low_first:** `value = (Register[1] << 16) | Register[0]` (Register[0] = LSW, Register[1] = MSW)

Verschiedene Lambda-Geräte/Firmware-Varianten erwarten unterschiedliche Reihenfolgen.

---

## Konfiguration

### Prioritätskette (niedrig → hoch)

| Priorität | Quelle | Beschreibung |
|---|---|---|
| 1 | Absoluter Fallback | `"high_first"` — greift nur, wenn FW-Version unbekannt |
| 2 | `FIRMWARE_CONFIG` | FW-abhängiger Default aus `const_base.py` *(ab V2.7.0)* |
| 3 | YAML Legacy | `modbus.int32_byte_order` in `lambda_wp_config.yaml` (deprecated, wird migriert) |
| 4 | YAML Explizit | `modbus.int32_register_order` in `lambda_wp_config.yaml` — **höchste Priorität** |

Der YAML-Override in `lambda_wp_config.yaml` gewinnt immer — er überschreibt den FW-abhängigen Default.

### YAML-Override (lambda_wp_config.yaml)

```yaml
modbus:
  # "high_first" = Höherwertiges Register zuerst (Standard)
  # "low_first" = Niedrigwertiges Register zuerst
  int32_register_order: "high_first"   # oder "low_first"
```

Weitere Beispiele und Kontext: [modbus_wp_config.yaml – Modbus-Parameter](modbus-wp-config.md).

### Firmware-abhängiger Default (FIRMWARE_CONFIG, ab V2.7.0)

Jeder FW-Eintrag in `const_base.py` trägt einen `reg_order`-Wert:

```python
FIRMWARE_CONFIG: dict = {
    "V1.1.0-3K":  {"version": 9, "reg_order": "low_first"},
    "V0.0.10-3K": {"version": 8, "reg_order": "low_first"},
    "V0.0.9-3K":  {"version": 7, "reg_order": "high_first"},
    # ...
}
# Rückwärtskompatibilität — alle bestehenden Aufrufer unverändert:
FIRMWARE_VERSION: dict = {k: v["version"] for k, v in FIRMWARE_CONFIG.items()}
```

Wenn eine Firmware-Version einen anderen Register-Order verwendet, genügt es, den entsprechenden Eintrag in `FIRMWARE_CONFIG` mit dem richtigen `"reg_order"`-Wert zu setzen. `FIRMWARE_VERSION` wird automatisch abgeleitet — alle bestehenden Aufrufer bleiben unverändert.

**Hinweis:** Die beiden neuesten Firmware-Versionen (`V1.1.0-3K`, `V0.0.10-3K`) verwenden tatsächlich `"low_first"` — abweichend vom absoluten Fallback `"high_first"`, der für ältere Versionen zutrifft.

---

## Implementierung im Code

### 1. Konfiguration laden: `get_int32_register_order` (modbus_utils.py)

- **Datei:** `custom_components/lambda_heat_pumps/modbus_utils.py`
- **Funktion:** `async def get_int32_register_order(hass, entry=None) -> str`
- Liest `lambda_wp_config.yaml` und gibt `"high_first"` oder `"low_first"` zurück.
- **Priorität** (ab V2.7.0): absoluter Fallback → FW-Default aus `FIRMWARE_CONFIG` → YAML-Legacy → YAML-Explizit.
- **Rückwärtskompatibilität:**
  - Fehlt `int32_register_order`, wird `int32_byte_order` ausgewertet (mit Log-Hinweis zur Migration).
  - Werte `"big"` → `"high_first"`, `"little"` → `"low_first"` (mit Log-Hinweis).
  - Ungültige Werte → Fallback `"high_first"`.
  - Ausnahme beim Laden → Fallback `"high_first"`.
  - `entry=None` → FW-Default wird aus `DEFAULT_FIRMWARE` abgeleitet (identisches Verhalten wie vor V2.7.0).

### 2. Register kombinieren: `combine_int32_registers` (modbus_utils.py)

- **Datei:** `custom_components/lambda_heat_pumps/modbus_utils.py`
- **Funktion:** `def combine_int32_registers(registers: list, register_order: str = "high_first") -> int`
- Erwartet mindestens 2 Register; wirft `ValueError`, wenn nicht.
- **Rückwärtskompatibilität:** `"big"` wird wie `"high_first"`, `"little"` wie `"low_first"` behandelt.
- **Logik:**
  - `register_order == "low_first"`: `(registers[1] << 16) | registers[0]`
  - sonst (high_first): `(registers[0] << 16) | registers[1]`

### 3. Einbindung beim Start (__init__.py)

- **Datei:** `custom_components/lambda_heat_pumps/__init__.py`
- **Zeitpunkt:** Vor dem ersten `async_refresh()` des Coordinators.
- Coordinator erhält die globale Register-Reihenfolge:
  - `coordinator._int32_register_order = await get_int32_register_order(hass, entry)` *(entry ab V2.7.0)*
- Default im Coordinator: `"high_first"` (siehe `coordinator.py`).

### 4. Verwendung im Coordinator (coordinator.py)

- **Globale Reihenfolge:** `self._int32_register_order` (wird in __init__.py gesetzt).
- **Batch-Read:** Für jeden int32-Sensor wird die Reihenfolge ermittelt als:
  - `sensor_info.get("register_order") or sensor_info.get("byte_order") or self._int32_register_order`
  - Anschließend: `combine_int32_registers([value, next_value], register_order)`.
- **Single-Read (int32):** Es wird `combine_int32_registers(result.registers, self._int32_register_order)` verwendet.
- Betroffen sind u. a. Batch-Lesevorgänge, Boiler-, Buffer-, Solar-, Heizkreis- und Energieverbrauchs-Int32-Sensoren.

### 5. Firmware-Konfiguration (const_base.py) *(ab V2.7.0)*

- **Datei:** `custom_components/lambda_heat_pumps/const_base.py`
- **`FIRMWARE_CONFIG`:** Primärstruktur mit `version` (int) und `reg_order` (`"high_first"` / `"low_first"`) je FW-Version-String.
- **`FIRMWARE_VERSION`:** Abgeleitetes Compat-Dict `{fw_str: int}` — alle bestehenden Aufrufer unverändert.
- **Pflege:** Neuen FW-Eintrag in `FIRMWARE_CONFIG` mit korrektem `reg_order` anlegen; `FIRMWARE_VERSION` wird automatisch aktualisiert.

### 6. Config-Template (const.py)

- **LAMBDA_WP_CONFIG_TEMPLATE** enthält einen kommentierten Abschnitt zu `modbus.int32_register_order` mit `"high_first"` / `"low_first"` und kurzer Erklärung (Register/Word Order, nicht Byte-Endianness).

### 7. Migration (migration.py)

- **Funktion:** `migrate_to_register_order_terminology`
- **Migration:** `modbus.int32_byte_order` → `modbus.int32_register_order` (Wert wird übernommen, Key umbenannt).
- **Version:** `REGISTER_ORDER_TERMINOLOGY` (const_migration.py).

---

## Betroffene Sensoren

Alle Sensoren mit **data_type: "int32"** in den Templates, z. B.:

- Energie-Akkumulation (z. B. `compressor_power_consumption_accumulated`, `compressor_thermal_energy_output_accumulated`)
- Weitere int32-Sensoren für Boiler, Puffer, Solar, Heizkreise

Die genaue Liste ergibt sich aus `const.py` (HP_SENSOR_TEMPLATES, CALCULATED_SENSOR_TEMPLATES usw.) über das Attribut `data_type: "int32"`.

---

## Sensor-spezifische Overrides (Templates)

Im Coordinator wird pro int32-Sensor optional eine eigene Reihenfolge unterstützt:

- **register_order** oder **byte_order** im Sensor-Template überschreibt die globale `_int32_register_order`, falls gesetzt.
- Beispiel (konzeptionell): `sensor_info.get("register_order") or sensor_info.get("byte_order") or self._int32_register_order`

Damit können einzelne Sensoren bei Bedarf anders konfiguriert werden als die globale Einstellung.

---

## Fehlerbehebung für Anwender

1. **Falsche int32-Werte** → In `lambda_wp_config.yaml` unter `modbus` wechseln:
   - von `int32_register_order: "high_first"` auf `"low_first"` oder umgekehrt.
2. Integration neu laden oder Home Assistant neu starten.
3. Werte mit Lambda-Software abgleichen.

Anwender-FAQ: [Falsche / keine Sensorwerte](../FAQ/falsche-keine-sensorwerte.md).

---

## Referenzen

- [Issue #22 (GitHub)](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/22)
- [Release 2.7.0](../Releases/release-2-7-0.md) — Firmware-abhängiger Register-Order-Default
- [modbus_wp_config.yaml – Modbus-Parameter](modbus-wp-config.md)
- [FAQ – Falsche / keine Sensorwerte](../FAQ/falsche-keine-sensorwerte.md)
