# Analyse der offenen Bug-Issues gegen Branch `3.5`

- **Stand:** 12.10.2026
- **Geprüfter Code:** `origin/3.5` @ `55439d4` (Integration v3.5.6)
- **Grundlage:** alle 24 offenen GitHub-Issues. Geprüft wurden die 9 mit Label `bug` und die 6 ohne Label, die einen Fehler beschreiben. Die 9 `enhancement`-Issues sind nur am Ende aufgelistet.
- **Hinweis:** Es wurde **kein Code geändert**. Zeilenangaben beziehen sich auf `custom_components/lambda_heat_pumps/` im Branch `3.5`.

Der Branch `3.5` ist ein Rewrite (PR #115: `modbus-connection`/`tmodbus` statt `pymodbus`, neue Entity-/Register-Modelle). Viele Issues, die gegen 2.x gemeldet wurden, betreffen Code, den es so nicht mehr gibt. Sie wurden deshalb gegen die neue Implementierung neu bewertet.

---

## Übersicht

| Issue | Titel (gekürzt) | Status in 3.5 | Priorität |
|---|---|---|---|
| [#104](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/104) | Akkumulierte Energiezähler falsch / negativ | 🔴 **teilweise offen** (Regression bei der Registerreihenfolge) | hoch |
| [#90](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/90) | Warmwasser thermisch = elektrisch, extreme Werte | 🔴 **teilweise offen** (gleiche Ursache wie #104) | hoch |
| [#82](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/82) | Falsche Firmware-Version übernommen | 🟠 **teilweise offen** (Migration bevorzugt veralteten Wert) | mittel |
| [#100](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/100) | Neue Steuerung FW 1.3.8 / 1.3.10 | 🟠 **teilweise offen** (mehrere Restpunkte + Regression #108) | mittel |
| [#122](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/122) | Entity-ID mit falscher Domain (`sensor.*_heating_circuit`) | 🟡 Code behoben, **Registry-Altlasten offen** | mittel (Frist HA 2027.5) |
| [#85](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/85) | Entity-ID mit falscher Domain (`sensor.*_boil1_hot_water`) | 🟡 wie #122 (Duplikat) | mittel (Frist HA 2027.5) |
| [#105](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/105) | E-Manager-Register springt auf 0 | 🟡 vermutlich behoben (3.5.2/3.5.3), **nicht bestätigt** | mittel |
| [#101](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/101) | Solarthermiemodul wird nicht erkannt | 🟡 unklar, Logs fehlen; Schwachstelle in der Modulerkennung | niedrig |
| [#94](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/94) | Verlauf nach Update auf 2.6.0 weg | 🟢 in 3.5 nicht reproduzierbar | niedrig |
| [#95](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/95) | Heizkurven-Stützpunkte zeigen statische Werte | 🟢 kein Code-Bug (so gewollt) + Sentinel-Werte behoben | niedrig |
| [#132](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/132) | Room Temperature / Set Flow Temperature `unknown` | 🟢 kein Code-Bug (so gewollt), nur UX | niedrig |
| [#120](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/120) | Screenshots PV-Überschuss fehlen (toter Link) | 🟡 Bilder liegen im Repo, Live-Seite prüfen | niedrig |
| [#121](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/121) | `device_registry.async_get_device` deprecated | ✅ **behoben** in 3.5.4 | – |
| [#112](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/112) | Register 5007 doppelt adressiert | ✅ **behoben** in 3.5.5 | – |

Legende: 🔴 Fehler im 3.5-Code nachgewiesen · 🟠 Teilaspekte offen · 🟡 unklar bzw. Restarbeit · 🟢 kein Code-Fehler in 3.5 · ✅ behoben (Issue kann geschlossen werden)

---

## 🔴 #104: Akkumulierte Energiezähler falsch / negativ

**Meldung:** `compressor_power_consumption_accumulated` / `..._thermal_energy_output_accumulated` liefern Werte wie -1.341.390.833 Wh. Ursache in 2.x war die 32-Bit-Registerreihenfolge, die Lambda ab V0.0.10 geändert hat. In 2.8.0 wird deshalb `reg_order` aus `FIRMWARE_CONFIG` als Default genommen.

**Prüfung in 3.5:**
- Grundsätzlich richtig umgesetzt: `const.py:22ff`. `FIRMWARE_CONFIG` enthält `reg_order`. `coordinator.py` (ca. Z. 160) nimmt `entry.options[int32_register_order]` und, **wenn das fehlt**, `default_register_order(firmware)`. Die beiden 32-Bit-Zähler werden jeweils am Stück gelesen (`ranges.py`, `(20,21)`, `(22,23)`).
- **Fehler 1: Die Migration überschreibt den Firmware-Default.** `__init__.py:141` ruft `options.setdefault(CONF_INT32_REGISTER_ORDER, await _async_read_register_order(hass))` auf. `_async_read_register_order()` (`__init__.py:151-179`) liefert `DEFAULT_INT32_REGISTER_ORDER` = `high_first`, wenn die YAML-Datei fehlt oder der Schlüssel auskommentiert ist. Das ist der Normalfall, denn in 2.8.x wurde Anwendern ausdrücklich geraten, den Eintrag wieder auszukommentieren. Damit steht nach dem Upgrade 2.8→3.5 **explizit `high_first`** in den Options. Der Firmware-Fallback im Coordinator greift nie mehr. Bei Firmware **V0.0.10-3K und V1.1.0-3K** (`low_first`) kommen dadurch wieder genau die Werte aus #104/#90.
- **Fehler 2: Der Options-Flow schreibt den falschen Default.** `config_flow.py:281` setzt als Default `options.get(CONF_INT32_REGISTER_ORDER, DEFAULT_INT32_REGISTER_ORDER)`. Bei einem neuen Eintrag ohne gespeicherte Option zeigt das Formular also `high_first`. Speichert der Anwender die Optionen (z. B. nur um PV-Überschuss zu aktivieren), wird `high_first` dauerhaft gespeichert, auch bei `low_first`-Firmware.

**Lösungsansatz:**
1. In `async_migrate_entry` die Registerreihenfolge **nur** setzen, wenn die alte YAML einen expliziten Wert enthält. `_async_read_register_order()` gibt dann `None` statt `DEFAULT_…` zurück, und `options.setdefault` wird nur bei einem Wert ungleich `None` ausgeführt. Ohne expliziten Wert bleibt der Firmware-Default aus dem Coordinator wirksam.
2. Im Options-Flow den Default aus der Firmware ableiten: `options.get(CONF_INT32_REGISTER_ORDER) or default_register_order(entry.data[CONF_FIRMWARE_VERSION]) or DEFAULT_INT32_REGISTER_ORDER`.
3. Besser noch: einen Wert `"auto"` (= Firmware-Default) einführen und als Default anbieten. Dann bleibt ein Firmwarewechsel über `reconfigure` konsistent.
4. **Reparatur bestehender 3.5-Installationen:** In einer Migration (ENTRY_VERSION 10) `int32_register_order` aus den Options entfernen, wenn er `high_first` ist, die Firmware aber `low_first` erwartet **und** die YAML keinen expliziten Wert hatte. Alternativ ein Repair-Issue (`homeassistant.helpers.issue_registry`) anlegen, wenn ein 32-Bit-Zähler negativ ist oder unplausibel springt.
5. Tests: Migration ohne YAML bei `V0.0.10-3K` → keine `int32_register_order` in den Options. Options-Flow bei `V1.1.0-3K` → Default `low_first`.
6. Doku/FAQ: Nach einer Korrektur der Reihenfolge springen die `TOTAL_INCREASING`-Sensoren. Beschreiben, wie man die Statistik bereinigt (`recorder.purge_entities`, Statistik-Korrektur).

---

## 🔴 #90: Warmwasser thermisch und elektrisch identisch / extrem hohe Werte

**Meldung (2.5.0, FW 0.0.9):** Warmwasser-Energie thermisch und elektrisch sind (fast) gleich und liegen bei ca. 21.400 kWh bzw. 89.000 kWh. Die akkumulierten Register zeigen negative bzw. unplausible Werte.

**Prüfung in 3.5:**
- Die Energiezuordnung wurde neu geschrieben (`coordinator.py`, `_track_energy` und `_energy_delta`). Elektrisch und thermisch kommen aus **getrennten** Registern und fließen in getrennte Töpfe (`totals.electrical` / `totals.thermal`). Die Verwechslung aus 2.x gibt es nicht mehr.
- `_energy_delta` verwirft negative Deltas und Sprünge > `MAX_ENERGY_DELTA_KWH` (100 kWh pro Poll). Statt zu kappen, wird verworfen (Befund 1 aus #100). Riesige Werte wie 21.400 kWh können so nicht mehr entstehen.
- **Die eigentliche Ursache ist aber die falsche 32-Bit-Registerreihenfolge, und die kann durch die Regression aus #104 wieder auftreten.** Mit falscher Reihenfolge ändern sich die Rohwerte fast nur im (vertauschten) Low-Word. Die Deltas sind dann meist > 100 kWh oder negativ, die Zähler bleiben praktisch stehen. Ein Delta < 100 kWh wird aber falsch gezählt.

**Lösungsansatz:**
1. Den Fix aus #104 umsetzen. Damit ist #90 im Kern erledigt.
2. Zusätzlich eine Plausibilitätswarnung einbauen: Ist ein 32-Bit-Zähler ≤ 0 oder liegt er über z. B. 10⁹ Wh, einmalig ein Warning bzw. Repair-Issue auslösen mit dem Hinweis „Registerreihenfolge prüfen“, statt still 0 zu buchen.
3. Den Reporter nach Umstellung auf 3.5.x um Rückmeldung bitten, danach das Issue schließen. Die bestehenden falschen Langzeitstatistiken muss der Anwender selbst bereinigen (Offset in den Optionen oder Statistik löschen, wie im Issue-Kommentar beschrieben).

---

## 🟠 #82: Falsche Firmware-Version wird übernommen

**Meldung (2.4.0):** Gewählt wird „V0.0.10-3K“, eingerichtet wird „V0.0.9-3K“.

**Prüfung in 3.5:**
- Der Config-Flow speichert jetzt direkt den **Namen** (`config_flow.py:100`, `SelectSelector` mit `FIRMWARE_VERSIONS`). `firmware.py: firmware_level()` löst ihn über `FIRMWARE_CONFIG[name]` auf. Ein Index-Versatz ist dabei nicht mehr möglich, **die Neueinrichtung ist also korrekt**.
- **Offen: Die Migration von 2.x übernimmt einen veralteten Wert.** In 2.x hatte `entry.options["firmware_version"]` Vorrang vor `entry.data` (`utils.get_firmware_version`: erst Options, dann Data). Hat ein Anwender die Firmware in 2.x über den Options-Flow geändert, steht der neue Wert in den Options und der alte, ursprüngliche in `data`. 3.5 macht es umgekehrt (`__init__.py:134`): `data.get(FW) or options.pop(FW)`. Der **alte** Wert aus `data` gewinnt, der aktuelle aus den Options wird ignoriert und bleibt sogar als Leiche in den Options stehen. Genau das ergibt den Effekt „falsche (ältere) Version eingerichtet“. Indirekt bekommt der Anwender dann auch die falsche Registerreihenfolge und die falschen Firmware-Gates für Sensoren.
- Ein unbekannter Firmware-Name fällt still auf `FIRMWARE_VERSIONS[-1]` zurück (`V0.0.3-3K`, die älteste). Das betrifft z. B. Einträge mit Namen, die es nur in einem Testbranch gab.

**Lösungsansatz:**
1. In `async_migrate_entry` die 2.x-Priorität übernehmen: `firmware = options.pop(CONF_FIRMWARE_VERSION, None) or data.get(CONF_FIRMWARE_VERSION)`. Den Options-Schlüssel dabei immer entfernen.
2. Bei einem unbekannten Namen nicht still auf die älteste Version zurückfallen. Stattdessen ein Warning loggen und ein Repair-Issue mit Verweis auf „Neu konfigurieren“ erzeugen.
3. Test: Eintrag mit `data.firmware_version="V0.0.9-3K"` und `options.firmware_version="V0.0.10-3K"` → nach der Migration `V0.0.10-3K`.

---

## 🟠 #100: Neue Steuerung (SW 1.3.8 / 1.3.10, FW V1.0.4-3K)

Ein Sammel-Thread mit mehreren Befunden von @madmaxx425. Einiges ist umgesetzt, Stand in 3.5:

| Befund | Status in 3.5 |
|---|---|
| 1: Energie-Delta wird gekappt statt verworfen | ✅ behoben (`_energy_delta` verwirft) |
| 2: Sentinel-Werte 0x8000 / -3000 / 0xFFFF | ✅ für `gauge`/`enum` behoben (`lambda_modbus/model.py`: `SENTINELS`, opt-in `NO_REQUEST`) |
| 3: Register 1024–1060 auf der neuen Steuerung nicht belegt | 🟠 teilweise: Gauges zeigen `unknown`, die **`integer`-Felder `config_parameter_24/33/50/60` zeigen weiterhin 32768** (`heat_pump.py`, `sensor.py:223/232/238/248`); sie haben weder Sentinel noch Firmware-Range |
| 4a: `ambient_temperature` | 🔴 **Regression**, siehe unten |
| 4b: `volume_flow_heat_sink` Einheit/Skalierung | 🟠 offen: weiterhin `integer(6, unit="l/h")`, Skala 1 (`heat_pump.py:26`, `sensor.py:195`); der Vorschlag `l/min`, Skala 0.01, wurde nie umgesetzt (auch nicht in `main`) |
| Firmware „V1.0.4-3K“ in die Auswahl aufnehmen (zugesagt am 04.08.) | 🔴 offen: fehlt in `FIRMWARE_CONFIG` (`const.py:21ff`), weder in `3.5` noch in `main` |

**Regression von #108 (geschlossen):** In `main`/2.8.x wurde `ambient_temperature` auf Wunsch von #108 auf `firmware_versions: ["1-9"]` erweitert, weil Register 2 auch auf V1.1.0-3K gültige Werte liefert und ungültige Werte über `sentinel_values` abgefangen werden. In 3.5 steht wieder `firmware_versions=("1-7",)` (`sensor.py:177`). Auf **V0.0.10-3K und V1.1.0-3K wird die Entity also gar nicht mehr angelegt**, obwohl `general.py` den 0xFFFF-Sentinel für dieses Feld bereits abfängt.

**Lösungsansatz:**
1. `sensor.py:177`: Die Firmware-Range entfernen (oder `("1-9",)` setzen). Die Sentinel-Filterung in `Ambient.temperature` reicht aus. Dazu einen Regressionstest für #108 schreiben.
2. `"V1.0.4-3K"` in `FIRMWARE_CONFIG` aufnehmen. Ordinal und `reg_order` vorher mit den Testern aus #100 klären (@b-bremer, @7xy, @madmaxx425). Laut Thread sind die Register identisch mit Protokoll 1.0, die Reihenfolge ist vermutlich `low_first`. Achtung: Ordinals sind Vergleichswerte für `firmware_version`. Eine neue Version zwischen den bestehenden erfordert entweder eine Neunummerierung (und eine Prüfung aller `firmware_version`/`firmware_versions`-Angaben) oder ein Ordinal ≥ 10.
3. `config_parameter_*` (die `integer`-Felder im Bereich 1024–1060): entweder `nan=SENTINELS` am Feld setzen oder sie per `firmware_versions` auf die alten Steuerungen begrenzen. Die Alternative: Default-mäßig deaktivieren (`entity_registry_enabled_default=False`), weil sie undokumentiert sind.
4. `volume_flow_heat_sink`: Mit Lambda-Protokoll 1.0 und einem Rohwert-Dump verifizieren. Ist die Korrektur bestätigt, `gauge(6, 0.01, unit="l/min")` verwenden und die Sensoreinheit anpassen. **Achtung:** Ein Einheitenwechsel betrifft die Langzeitstatistik, HA meldet dann ein Statistik-Problem. Das im Changelog erwähnen.
5. In der Doku (initiale Konfiguration) klarstellen, welche Versionsanzeige gemeint ist (Statuszeile der WP-Seite, nicht SW-Version). Laut Thread ist die Doku mit GIF bereits online, also nur prüfen.

---

## 🟡 #122 und #85: Entity-ID mit falscher Domain (`sensor.*` statt `climate.*`)

**Meldung:** HA warnt „sets an entity ID with wrong domain: `sensor.eu13l_hc1_heating_circuit`“ bzw. `sensor.eu13l_boil1_hot_water`. Ab HA 2027.5 funktioniert das nicht mehr.

**Prüfung in 3.5:**
- Im Code behoben: `entity.py:84-86` schlägt die Entity-ID aus `_entity_domain` vor, und `climate.py:105` setzt `_entity_domain = "climate"`. `number.py` und `sensor.py` setzen ebenfalls ihre eigene Domain. Neue Installationen erzeugen also `climate.<prefix>_hc1_heating_circuit` bzw. `climate.<prefix>_boil1_hot_water`.
- **Offen:** Bestehende Installationen, die unter 2.x die Climate-Entities mit `sensor.*`-ID registriert haben, behalten diese ID in der Entity-Registry, denn die Registry-ID hat Vorrang vor dem Vorschlag. Ob HA bei solchen Registry-Einträgen ab 2027.5 ebenfalls warnt bzw. sie ablehnt, sollte mit einem Test gegen eine aktuelle HA-Version geprüft werden. Sicher ist: Die IDs bleiben inkonsistent.

**Lösungsansatz:**
1. In `async_setup_entry` (oder in einer neuen Migration) die Entity-Registry durchgehen: `er.async_entries_for_config_entry(registry, entry.entry_id)`. Jeden Eintrag mit `entry.domain == "climate"`, dessen `entity_id` nicht mit `climate.` beginnt, über `registry.async_update_entity(entity_id, new_entity_id=f"climate.{object_id}")` umbenennen. Vorher auf Kollisionen prüfen (`registry.async_get(new_id)`).
2. Den Anwender im Changelog darauf hinweisen, dass Automationen/Dashboards mit `sensor.*_heating_circuit` bzw. `sensor.*_hot_water` angepasst werden müssen.
3. Test: Ein Registry-Eintrag `sensor.x_boil1_hot_water` auf Plattform `climate` wird nach dem Setup zu `climate.x_boil1_hot_water`.
4. #85 als Duplikat von #122 schließen (oder umgekehrt).

---

## 🟡 #105: E-Manager-Register (PV-Überschuss) springt zwischendurch auf 0

**Meldung:** Zwischen zwei Werten zeigt die Lambda kurz 0 an, dadurch wird die 15-Minuten-Startverzögerung nie erreicht. Zuletzt noch in 2.8.3 beobachtet.

**Prüfung in 3.5:**
- Der Schreibpfad ist neu (`services.py:105-133`, `async_write_pv_surplus`). Ist der Quellsensor `unknown`/`unavailable`, wird **nicht** geschrieben (`_number()` → `None` → `return`). Es wird also keine 0 aktiv gesendet.
- Die Modbus-Serialisierung (die Ursache in 2.x) ist in 3.5.2 über `DEFAULT_MODBUS_MESSAGE_SPACING = 0.05` gelöst (`const.py:49`, `__init__.py:63`). Das aktiviert den internen Pacer-Lock von `modbus-connection`.
- 3.5.3: FC16 statt FC06. Vorher scheiterte **jeder** Schreibvorgang mit „Illegal Function“.
- Weitere Quellen für eine 0, die weiterhin möglich sind:
  - Modus `pos`: Negative Werte werden auf 0 geklemmt (`services.py:125`). Liefert der Quellsensor bei Einspeisung negative Werte (Netzzähler), schickt die Integration korrekt 0. Das ist ein Konfigurationsthema (Template-Sensor oder Modus `neg`).
  - Die Lambda selbst setzt den Wert nach einem Timeout zurück, wenn zu lange nichts geschrieben wird. Bei einem Intervall von 9 s ist das unwahrscheinlich.
- „Psoll = 0“ (Register 104) berechnet die Lambda selbst, die Integration liest das Register nur.

**Lösungsansatz:**
1. Die Reporter (@medicus07, @thofes) bitten, mit 3.5.6 erneut zu testen.
2. Für die Diagnose ein Debug-Log des geschriebenen Rohwerts einbauen (`_LOGGER.debug("PV surplus %s W -> raw %s", power, raw)`), optional mit Rücklesen von Register 102 direkt nach dem Schreiben (nur im Debug-Modus).
3. Optional: Klemmen auf 0 im Modus `pos` als Debug-Hinweis loggen, damit eine Fehlkonfiguration sichtbar wird.
4. Wird nichts mehr gemeldet, das Issue mit Verweis auf 3.5.2/3.5.3 schließen.

---

## 🟡 #101: Solarthermiemodul wird nicht erkannt

**Meldung:** Ein Solarmodul (Speicher- und Kollektortemperatur) ist an der Steuerung angeschlossen und in der Lambda-App sichtbar, aber nicht in HA. Der Reporter hat keine Logs nachgeliefert.

**Prüfung in 3.5:**
- Erkennung über `module_auto_detect.py`: Für `sol` wird Register `4000 + 100·(n-1)` gelesen. Die Sensoren (`SOL_SENSORS`, `lambda_modbus/solar.py`) sind vorhanden.
- **Schwachstelle:** `module_auto_detect.py:64` wertet auch einen `ModbusTimeoutError` als „Modul nicht vorhanden“. Antwortet die Steuerung beim Setup einmal zu langsam, fehlt das Modul bis zum nächsten Reload. Das passt auch zur Beobachtung in #90 („erst 5 Module, nach Reload 6“).
- Möglich ist auch, dass Lambda den Solarkreis bei manchen Konfigurationen nicht als Modbus-Modul „Solar“ (4xxx) exponiert, sondern nur intern verwaltet. Das lässt sich nur mit einem Register-Dump klären.

**Lösungsansatz:**
1. Den Reporter erneut um ein Debug-Log oder den Diagnose-Download (`diagnostics.py`) bitten, zusätzlich um einen Lesetest von Register 4000 über den Service `read_modbus_register`.
2. Robustere Erkennung: Bei einem Timeout den Probe 1–2× mit kurzer Pause wiederholen, bevor das Modul als „nicht vorhanden“ gilt. `IllegalDataAddressError` bleibt das eindeutige „nicht vorhanden“.
3. Die erkannten Modulzahlen beim Setup auf `INFO` loggen (aktuell nur `DEBUG`), damit Anwender ohne Debug-Modus sehen, was erkannt wurde.

---

## 🟢 #94: Verlauf aller Entities nach Update auf 2.6.0 nicht mehr verfügbar

**Meldung:** Nach dem Update auf 2.6.0 fehlt die Historie vor dem 25.06., Energie-Entities aktualisieren nicht mehr.

**Prüfung in 3.5:**
- Betrifft eine alte Version. In 3.5 wird die Unique-ID-Form ausdrücklich beibehalten (`entity.py:62-70`, inkl. Legacy-Präfix), damit die Historie erhalten bleibt. Die Migration setzt `use_legacy_modbus_names` für Alt-Einträge auf `True`.
- 3.5.6 behebt außerdem den Verlust der Lifetime-Zähler beim Upgrade 2.8→3.5 (Fallback auf die Langzeitstatistik).
- Das Symptom „Energie-Entities aktualisieren nicht“ passt zur falschen Registerreihenfolge (siehe #104).

**Lösungsansatz:**
1. Kein Code-Fix in 3.5 nötig. Den Reporter fragen, ob das Problem mit 3.5.6 noch besteht. Verlorene Historie aus 2.6.0 lässt sich nicht wiederherstellen.
2. Danach das Issue schließen. Für den Upgrade-Pfad 2.x→3.5 empfiehlt sich ein Test „Unique-IDs vor/nach Migration identisch“ (falls noch nicht vorhanden).

---

## 🟢 #95: Heizkurven-Stützpunkte zeigen falsche, statische Werte

**Meldung:** `number.*_heating_curve_{cold,mid,warm}_outside_temp` zeigen 48,3 / 39,0 / 32,1 °C statt der Werte am Panel. Außerdem `set_flow_line_temperature` = -300 und `requested_flow_line_temperature` = -3276,8.

**Prüfung in 3.5:**
- Die Heizkurven-Stützpunkte sind **keine Register**. Sie sind integrationseigene Einstellungen (`const.py:184`, `CURVE_POINTS`), die Defaults sind 48,3 / 39,0 / 32,0. Die Lambda stellt die Panel-Werte nicht über Modbus bereit. Das Verhalten ist also so gewollt (wie im Issue-Kommentar erklärt).
- -300,0 (`0xF448`, -3000) und -3276,8 (`0x8000`) werden jetzt über `SENTINELS` (`lambda_modbus/model.py`) als `unknown` angezeigt und nicht mehr als Messwert. **Behoben.**

**Lösungsansatz:**
1. Kein Code-Bug. UX-Verbesserung: In der Entity-Beschreibung bzw. Übersetzung deutlich machen, dass die Werte manuell vom Panel übernommen werden müssen. Optional beim ersten Setup ein Hinweis (Persistent Notification), dass die Heizkurve konfiguriert werden muss.
2. Das Thema überschneidet sich mit Enhancement #128 (Abweichung zum realen Vorlaufsollwert, Kurvenschätzung).
3. Issue schließen.

---

## 🟢 #132: „Room Temperature“ / „Set Flow Temperature“ = `unknown`

**Meldung:** Beide Sensoren zeigen `unknown`. Der Kommentar von @j00pa bezog sich auf #112 (in 3.5.5 behoben).

**Prüfung in 3.5:**
- `room_device_temperature` (HC-Register 4) und `set_flow_line_temperature` (HC-Register 5), siehe `sensor.py:302-303`, sind **Eingaberegister für externe Vorgaben**. Sie haben nur einen Wert, wenn jemand sie per Modbus beschreibt: Raumtemperatur bei aktivierter Raumthermostat-Steuerung, Vorlaufsoll bei einem entsprechenden Heizkreis-Betriebsmodus. Ohne Vorgabe antwortet die Lambda mit einem Sentinel. Seit 3.5.2 wird das korrekt als `unknown` statt -300 °C dargestellt.
- Der BLU H&T-Sensor wirkt nur, wenn er in den Optionen als Raumtemperatur-Entity für den Heizkreis eingetragen **und** die Raumthermostat-Steuerung aktiviert ist (`services.py:84-102`).
- Der Rundungshinweis (`28.400000000000002`) ist kosmetisch. `suggested_display_precision=1` sorgt in der UI bereits für eine korrekte Anzeige.

**Lösungsansatz:**
1. Kein Code-Bug. Dem Reporter antworten und den Zusammenhang erklären.
2. UX: Beide Entities standardmäßig deaktivieren (`entity_registry_enabled_default=False`) oder als `EntityCategory.DIAGNOSTIC` kennzeichnen, und sie aktivieren, wenn die Raumthermostat-Steuerung eingeschaltet wird.
3. FAQ-Eintrag „Warum ist Sensor X `unknown`?“ (Sentinel-Werte).

---

## 🟡 #120: Screenshots zur PV-Überschuss-Konfiguration fehlen

**Prüfung:** `docs/docs/Anwender/pv_ueberschuss_steuerung.md:24/28` verweist auf `../../assets/pv_surplus_de_{1,2}.png`. Beide Dateien liegen in `docs/docs/assets/`, und der Pfad folgt demselben Muster wie auf den anderen Seiten (z. B. `debug-logs-erzeugen`). Im Repo ist der Link also gültig. Die Live-Seite konnte aus dieser Umgebung nicht abgerufen werden (kein Netzwerkzugriff auf github.io).

**Lösungsansatz:**
1. Die Live-Seite `…/Anwender/pv_ueberschuss_steuerung/` prüfen. Fehlen die Bilder dort, den Docs-Build (`.github/workflows/docsz.yml`) bzw. das Deployment untersuchen, z. B. ob die Assets aus dem richtigen Branch kommen. Möglicherweise wurde nach dem Hinzufügen der Bilder kein neuer Build angestoßen.
2. Prüfen, ob es eine englische Variante der Seite oder einen README-Abschnitt gibt, auf den sich der Reporter bezieht. Das README hat im Abschnitt „PV Surplus Control“ keine Bilder.
3. Robuster wäre die Markdown-Syntax `![…](../assets/pv_surplus_de_1.png)` statt rohem `<img src="../../…">`. Der Docs-Generator löst Markdown-Bildpfade relativ zur Quelldatei auf, rohe HTML-Pfade nicht.

---

## ✅ #121: `device_registry.async_get_device` deprecated

**Prüfung:** Im Branch `3.5` gibt es keinen Aufruf von `async_get_device(` mehr. `coordinator.py:247` nutzt `async_get_device_by_identifier(controller, entry.entry_id)` (Changelog 3.5.4).

**Lösungsansatz:** Mit Hinweis auf 3.5.4 schließen.

---

## ✅ #112: Modbus-Register 5007 doppelt adressiert

**Prüfung:** `sensor.py:307-308`: `flow_line_temperature_setpoint` ist auf `firmware_versions=("1-2",)` begrenzt, `target_temp_flow_line` gilt ab `firmware_version=3`. Pro Firmware wird also nur eine der beiden Entities angelegt (`serves()` in `firmware.py`). Der nicht-deterministische „primary sensor“ aus 2.x (`list(set)[0]`) existiert im neuen Registermodell nicht mehr (Changelog 3.5.5).

**Lösungsansatz:** Mit Hinweis auf 3.5.5 schließen. Optional einen Hinweis für Anwender ergänzen, die die verwaiste Entity aus 2.x noch in der Registry haben: manuell löschen.

---

## Zusätzliche Befunde (ohne eigenes offenes Issue)

| Befund | Ort | Bezug |
|---|---|---|
| `ambient_temperature` wieder auf FW 1-7 begrenzt (Regression des geschlossenen #108) | `sensor.py:177` | siehe #100 |
| Firmware-Priorität in der Migration vertauscht (`data` vor `options`) | `__init__.py:134` | siehe #82 |
| Migration schreibt `high_first` fest, statt den Firmware-Default zu lassen | `__init__.py:141`, `151-179` | siehe #104/#90 |
| Options-Flow-Default für die Registerreihenfolge ignoriert die Firmware | `config_flow.py:281` | siehe #104/#90 |
| Timeout bei der Modulerkennung wird als „Modul fehlt“ gewertet | `module_auto_detect.py:64` | siehe #101/#90 |

## Empfohlene Reihenfolge

1. **#104/#90**: Registerreihenfolge in Migration und Options-Flow korrigieren und bestehende Einträge reparieren. Das hat den größten Effekt: falsche Energiewerte und kaputte Langzeitstatistik.
2. **#100/#108**: Regression bei `ambient_temperature` beheben und `V1.0.4-3K` aufnehmen.
3. **#82**: Firmware-Priorität in der Migration korrigieren.
4. **#122/#85**: Registry-Migration für Climate-Entity-IDs (Frist HA 2027.5).
5. **#101**: Retry bei Timeout in der Modulerkennung.
6. Die Issues #121 und #112 schließen, #94/#95/#132 nach Rückmeldung schließen, #105 nach Retest schließen, #120 an der Live-Seite prüfen.

---

## Nicht betrachtet (Label `enhancement`)

#128 Heizkurve: Abweichung zum realen Vorlaufsoll · #119 Weniger Logging bei Sentinel-Werten · #113 Schreibbarer Kühl-Vorlaufsollwert · #83 Energiestatistik Wärmeverteilung · #79 Status-Entity PV-Überschuss-Modus · #77 Spreizung HP1 · #60 Abtauzähler 6h/12h · #59 Soll-Vorlauf bei PV-Überschuss erhöhen · #45 Wechselnde Strompreise · #37 State-Werte in Influx/Grafana
