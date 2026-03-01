# Plan: Status-Sensoren – History & Grafana-Visualisierung

**Status:** Entwurf
**Betrifft:** Alle `txt_mapping: True`-Sensoren (operating_state, state, error_state, operating_mode, …)

---

## 1. Problem-Analyse

### 1.1 Warum fehlt die History in HA?

Das Screenshot zeigt History-Daten erst ab ~21. Feb. für `hp1_operating_state`. Das Problem tritt auch auf älteren Systemen ohne die Name-Prefix-Änderung von Release 2.3 auf — die Entity-ID-Änderung ist daher **nicht** die Ursache.

**Ursache: Kein `state_class`, kein `device_class: enum`**

Alle Status-Sensoren haben in `sensor.py` explizit:
```python
self._attr_device_class = None
self._attr_state_class = None
```
HA-Verhalten bei Sensoren ohne `state_class` und ohne `device_class`:
- ✅ Kurzzeit-History (Zustandsänderungen): wird aufgezeichnet
- ❌ Long-Term-Statistics: **nicht** verfügbar
- ❌ HA-Statistik-Karten (Energie-Dashboard etc.): nicht nutzbar
- ⚠️ InfluxDB-Export: String-Werte werden als Tags exportiert, nicht als Felder

### 1.2 Warum fehlt die Grafana-Visualisierung?

Grafana visualisiert typischerweise **numerische** Zeitreihen. Status-Sensoren liefern Strings wie `"CH"`, `"DHW"`, `"STBY"`.

| Grafana-Quelle | Problem |
|---|---|
| InfluxDB (häufigste HA-Brücke) | String-States werden als Tag gespeichert, nicht als Field → keine Zeitreihe |
| HA-SQLite direkt | String-Werte im `states`-Table, numerische Queries scheitern |
| PostgreSQL | Gleiche Struktur wie SQLite |

Ohne numerischen Wert kann kein Time-Series-Panel in Grafana einen Betriebsstatus-Verlauf darstellen.

### 1.3 Betroffene Sensoren

Alle Sensoren mit `"txt_mapping": True` in `const_sensor.py`:

| Sensor-Key | Modbus-Register | Mapping-Dict | Zustände |
|---|---|---|---|
| `error_state` (HP) | HP+0 | `HP_ERROR_STATE` | 5 |
| `state` (HP) | HP+2 | `HP_STATE` | 14 |
| `operating_state` (HP) | HP+3 | `HP_OPERATING_STATE` | 19 |
| `relais_state_2nd_heating_stage` (HP) | HP+19 | `HP_RELAIS_STATE_2ND_HEATING_STAGE` | 2 |
| `operating_state` (BOIL) | BOIL+1 | `BOIL_OPERATING_STATE` | 13 |
| `operating_state` (BUFF) | BUFF+1 | `BUFF_OPERATING_STATE` | 10 |
| `operating_state` (SOL) | SOL+1 | `SOL_OPERATING_STATE` | 4 |
| `operating_state` (HC) | HC+1 | `HC_OPERATING_STATE` | 21 |
| `operating_mode` (HC) | HC+6 | `HC_OPERATING_MODE` | 8 |

---

## 2. Lösung

### Phase 1 – `device_class: enum` + `options` setzen (HA-konform)

**Ziel:** Korrekte HA-Repräsentation, History-Aufzeichnung als Enum-Entity.

**Änderungen in `const_sensor.py`:** Jedem `txt_mapping: True`-Eintrag `"device_class": "enum"` und `"options": [...]` hinzufügen.

Beispiel für `operating_state` (HP):
```python
"operating_state": {
    "relative_address": 3,
    "name": "Operating State",
    "unit": None,
    "scale": 1,
    "precision": 0,
    "data_type": "uint16",
    "device_type": "Hp",
    "writeable": False,
    "txt_mapping": True,
    "device_class": "enum",
    "options": [
        "STBY", "CH", "DHW", "CC", "CIRCULATE", "DEFROST",
        "OFF", "FROST", "STBY-FROST", "Not used", "SUMMER",
        "HOLIDAY", "ERROR", "WARNING", "INFO-MESSAGE",
        "TIME-BLOCK", "RELEASE-BLOCK", "MINTEMP-BLOCK", "FIRMWARE-DOWNLOAD"
    ],
    "options": {"register": True},
}
```

**Änderungen in `sensor.py`:** In der `LambdaSensor`-Klasse `device_class` und `options` aus dem Template übernehmen, wenn `txt_mapping=True`:
```python
if self._is_state_sensor:
    self._attr_device_class = sensor_info.get("device_class", None)
    self._attr_options = sensor_info.get("options_list", None)  # umbenannt wg. Konflikt
    self._attr_state_class = None   # bleibt None – Enum-Sensoren haben kein state_class
    self._attr_native_unit_of_measurement = None
```

**Auswirkung:**
- ✅ HA zeigt den Sensor als Enum-Entity mit definierten Zuständen
- ✅ History-Aufzeichnung verbessert (korrekte Entity-Klasse)
- ✅ Validierung: HA warnt wenn der Sensor einen nicht-deklarierten Zustand ausgibt
- ❌ Long-Term-Statistics: weiterhin nicht verfügbar (Enum-Sensoren unterstützen kein `state_class`)
- ❌ Grafana: weiterhin keine numerischen Zeitreihen

---

### Phase 2 – Rohen Zahlenwert als Sensor-Attribut exposen

**Ziel:** Numerischen Register-Wert zusätzlich verfügbar machen, ohne neue Entities zu erstellen.

**Änderungen in `sensor.py`:** Für alle `txt_mapping=True`-Sensoren den rohen Integer-Wert als `extra_state_attributes` setzen:
```python
@property
def extra_state_attributes(self):
    attrs = super().extra_state_attributes or {}
    if self._is_state_sensor and self._raw_numeric_value is not None:
        attrs["raw_value"] = self._raw_numeric_value
    return attrs
```

`self._raw_numeric_value` wird in `native_value` gespeichert, bevor das Mapping angewendet wird.

**Auswirkung:**
- ✅ Roher Zahlenwert im HA-Attribut `raw_value` → Template-Sensoren möglich
- ✅ InfluxDB exportiert Attribute als Fields → Grafana kann `raw_value` plotten
- ⚠️ Erfordert InfluxDB-Konfiguration mit `include_attributes: true`

---

### Phase 3 – Numerische Companion-Sensoren (optional, für Grafana-Direktanbindung)

**Ziel:** Pro Status-Sensor einen dedizierten numerischen Sensor erstellen, der den rohen Register-Wert enthält.

**Ansatz:** Neuen Eintrag in `const_calculated_sensors.py` pro `txt_mapping`-Sensor:
```python
"hp_operating_state_numeric": {
    "name": "HP Operating State (numeric)",
    "source_sensor": "operating_state",   # txt_mapping-Sensor
    "state_class": "measurement",
    "unit": None,
    "device_class": None,
    "formula": "raw_value",               # nimmt raw_value-Attribut
}
```

Oder direkt: den Modbus-Wert ein zweites Mal als reiner Zahl-Sensor lesen (gleiche Register-Adresse, kein `txt_mapping`).

**Namensschema:** `{original_sensor_id}_numeric`
Beispiel: `sensor.eu08l_hp1_operating_state_numeric` → Wert `1` für CH

**Auswirkung:**
- ✅ Numerische Zeitreihe direkt in HA und Grafana
- ✅ `state_class: measurement` → Long-Term-Statistics verfügbar
- ⚠️ Verdoppelt die Anzahl der Status-Sensoren

---

## 3. Empfehlung: Umsetzungsreihenfolge

| Phase | Aufwand | Vorteil | Empfehlung |
|---|---|---|---|
| 1 – `device_class: enum` + `options` | Niedrig | HA-konform, bessere Entity-Darstellung | **Sofort umsetzen** |
| 2 – `raw_value` als Attribut | Niedrig | Grafana via InfluxDB-Attribut | **Sofort umsetzen** |
| 3 – Numerische Companion-Sensoren | Mittel | Direkter Grafana-Support ohne InfluxDB-Umweg | **Optional, auf Anfrage** |

Phase 1 + 2 zusammen lösen das Grafana-Problem für alle Nutzer mit InfluxDB-Brücke und verbessern die HA-Darstellung ohne Breaking Change.

---

## 4. Historische Lücke

Die fehlende History ist ein **grundlegendes, versionsunabhängiges Problem** — betroffen sind auch Systeme ohne die Name-Prefix-Änderung von Release 2.3. Die Ursache liegt ausschließlich in der fehlenden `device_class`-Deklaration der Status-Sensoren (siehe 1.1).

HA zeichnet Zustandsänderungen zwar auf, zeigt sie aber im History-Panel nur lückenhaft an, wenn die Entity-Klasse unklar ist. Die Lösung aus Phase 1 (Setzen von `device_class: enum`) stellt sicher, dass HA diese Sensoren ab dem nächsten Update korrekt klassifiziert und vollständig in der History anzeigt.

Daten, die vor dem Update aufgezeichnet wurden, bleiben in `home-assistant_v2.db` erhalten und sind nach dem Update weiterhin sichtbar.

---

## 5. Betroffene Dateien

| Datei | Änderung |
|---|---|
| `const_sensor.py` | `device_class: "enum"` + `options_list` zu allen `txt_mapping`-Einträgen |
| `sensor.py` | `LambdaSensor`: `device_class`/`options` aus Template übernehmen, `raw_value` als Attribut |
| `const_calculated_sensors.py` | (Phase 3) Numerische Companion-Sensor-Templates |
| `tests/test_init_simple.py` | Tests für neues Attribut `raw_value` + `device_class` |
