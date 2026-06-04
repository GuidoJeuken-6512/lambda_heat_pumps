# Plan: Flexible Firmware-Versionssteuerung mit Range-Notation

## Context

Die bestehende Logik aktiviert Sensoren nach dem Prinzip „Sensor wurde in FW-Version X eingeführt":
- Jeder Sensor hat `firmware_version: X` (Minimum-Version)
- `get_compatible_sensors()` filtert: `sensor.firmware_version <= current_fw_version`

Das Konzept versagt bei nicht-zusammenhängenden Versionsbereichen (Sensor entfernt und später wieder eingeführt).

## Lösung: firmware_versions mit Range/Exception-Notation

### Syntax

Vereinheitlichte Syntax — drei Elementtypen:

| Element | Bedeutung |
|---------|-----------|
| `"X-Y"` | Versionen X bis Y (Bereich, inklusiv) |
| `"-X"` | Version X ausschließen |
| `X` (int) | Einzelne Version hinzufügen |

`+X` entfällt — Ergänzungen werden entweder als Bereich `"X-X"` oder direkt als Integer `X` geschrieben.

**Hauptbeispiel:** Sensor aktiv in V1–V5 und V7–V8, nicht in V6:
```python
"firmware_versions": ["1-5", "7-8"]
```

**Mit Ausnahme:** Sensor aktiv in V1–V8, außer V4:
```python
"firmware_versions": ["1-8", "-4"]
```

**Einzelne Versionen:**
```python
"firmware_versions": [1, 3, 6]
```

### Sensorstruktur (const_sensor.py)

```python
# Bisherig — bleibt unverändert (ab FW 1 aktiv, kein Breaking Change)
"sensor_a": {
    "firmware_version": 1,
    ...
}

# Neu — aktiv in 1-5 und 7-8
"sensor_b": {
    "firmware_versions": ["1-5", "7-8"],
    ...
}

# Nur bis Version 3 aktiv (danach entfernt)
"sensor_c": {
    "firmware_versions": ["1-3"],
    ...
}
```

---

## Implementierung in `utils.py`

### Neue Hilfsfunktion `_parse_firmware_versions()`

```python
def _parse_firmware_versions(spec: list) -> set[int]:
    """Parse firmware_versions spec into a set of active version integers.

    Supported elements:
      "X-Y"  → range X..Y inclusive
      "-X"   → exclude version X
      X      → include version X (int)
    """
    included = set()
    excluded = set()
    for item in spec:
        if isinstance(item, int):
            included.add(item)
        elif isinstance(item, str):
            if item.startswith("-"):
                excluded.add(int(item[1:]))
            elif "-" in item:
                lo, hi = item.split("-", 1)
                included.update(range(int(lo), int(hi) + 1))
            else:
                included.add(int(item))
    return included - excluded
```

### Erweiterte `get_compatible_sensors()`

```python
def get_compatible_sensors(sensor_templates: dict, fw_version: int) -> dict:
    result = {}
    for k, v in sensor_templates.items():
        if "firmware_versions" in v:
            active_versions = _parse_firmware_versions(v["firmware_versions"])
            if fw_version in active_versions:
                result[k] = v
        elif isinstance(v.get("firmware_version"), (int, float)):
            if v["firmware_version"] <= fw_version:
                result[k] = v
        else:
            result[k] = v
    return result
```

**Priorität:** `firmware_versions` > `firmware_version` (Minimum) > kein Feld (immer aktiv)

---

## Geänderte Dateien

| Datei | Änderung |
|-------|----------|
| `utils.py` | Neue `_parse_firmware_versions()`; `get_compatible_sensors()` erweitert |
| `const_sensor.py` | Optional: Sensoren mit nicht-trivialem Versionsverhalten erhalten `firmware_versions` |
| `sensor.py` | Keine Änderung |
| `coordinator.py` | Keine Änderung |
| `migration.py` | Keine Änderung |

---

## Rückwärtskompatibilität

- Alle bestehenden Sensoren mit `firmware_version: X` bleiben **vollständig unverändert**
- `firmware_versions` ist optional — kein Breaking Change
- `const_sensor.py` muss nur angefasst werden, wenn ein Sensor feinere Steuerung braucht

---

## Unit Tests (`tests/test_utils.py`)

- `_parse_firmware_versions(["1-5", "7-8"])` → `{1, 2, 3, 4, 5, 7, 8}`
- `_parse_firmware_versions(["1-8", "-4"])` → `{1, 2, 3, 5, 6, 7, 8}`
- `_parse_firmware_versions([1, 3, 6])` → `{1, 3, 6}`
- `_parse_firmware_versions(["1-3"])` → `{1, 2, 3}`
- `get_compatible_sensors()` mit altem `firmware_version`-Feld → bisheriges Verhalten unverändert
- `get_compatible_sensors()` mit neuem `firmware_versions`-Feld → korrekte Filterung

---

## Dokumentation

- Docstring in `_parse_firmware_versions()` beschreibt alle Elementtypen mit Beispielen
- `CHANGELOG.md` / Release Notes: Neues optionales Feld `firmware_versions` in Sensor-Templates
- `README` oder Entwickler-Doku: Abschnitt „Sensor Firmware Compatibility" mit Syntax-Tabelle und Beispielen

---

## Verifikation (manuell)

1. Sensor mit `firmware_versions: ["1-3"]` in `const_sensor.py` setzen
2. FW `V0.0.5-3K` (= 3) wählen → Sensor aktiv in HA
3. FW auf `V0.0.6-3K` (= 4) ändern → Sensor verschwindet aus HA
4. Sensor mit `firmware_versions: ["1-5", "7-8"]` → in FW 6 nicht sichtbar, in FW 7 wieder da
5. Bestehende Sensoren mit `firmware_version: 1` in allen FW-Versionen aktiv
