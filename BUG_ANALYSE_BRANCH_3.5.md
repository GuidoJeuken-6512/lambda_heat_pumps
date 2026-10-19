# Analyse der offenen Bug-Issues gegen Branch `3.5`

- **Stand:** 19.10.2026 (Erstanalyse 12.10.2026; HA-2026.10-Prüfung 19.10.2026)
- **Geprüfter Code:** `origin/3.5` @ `be4728b` (Integration v3.5.7, noch ohne Tag); Erstanalyse gegen `55439d4` (v3.5.6)
- **Grundlage:** alle 24 offenen GitHub-Issues. Geprüft wurden die 9 mit Label `bug` und die 6 ohne Label, die einen Fehler beschreiben. Die 9 `enhancement`-Issues sind nur am Ende aufgelistet.
- **Hinweis:** Die Analyse selbst hat keinen Code geändert. Nachträglich umgesetzt (17.10.2026): F1, F2, F6 und das Zurücksetzen der Registerreihenfolge bei einem Firmwarewechsel (3.5.7), Doku-Korrekturen zu #128/#134. Details im Abschnitt [Änderungen am 17.10.2026](#änderungen-am-17102026). Zeilenangaben beziehen sich auf `custom_components/lambda_heat_pumps/` im Branch `3.5`.

Der Branch `3.5` ist ein Rewrite (PR #115: `modbus-connection`/`tmodbus` statt `pymodbus`, neue Entity-/Register-Modelle). Viele Issues, die gegen 2.x gemeldet wurden, betreffen Code, den es so nicht mehr gibt. Sie wurden deshalb gegen die neue Implementierung neu bewertet.

> **Release-Stand (geprüft):** Branch `3.5` ist **noch nicht veröffentlicht**. Letzter Tag bzw. Release ist `V2.8.6`, `main` steht auf 2.8.6, und es gibt keinen Tag auf einem 3.5-Commit. Für die Migrationsbefunde heißt das:
> - Es gibt **keine Endanwender-Installationen von 3.5** aus einem Release. **Ausnahme:** Tester, die 3.5.x direkt aus dem Branch installieren (z. B. der Melder von #133/#134/#128). Für sie gilt: Bereits migrierte Einträge werden von späteren Fixes im Migrationsschritt 9 nicht mehr erfasst und müssen von Hand korrigiert werden. Eine *zusätzliche* Migration (neue `ENTRY_VERSION`) oder Repair-Logik für „bereits auf 3.5 migrierte Einträge“ ist **nicht nötig**. Die eigenen Testinstallationen lassen sich von Hand korrigieren (Option neu setzen bzw. Eintrag neu anlegen).
> - Die Migration **2.x → 3.5** (`async_migrate_entry`, `ENTRY_VERSION = 9`) läuft dagegen beim ersten Start für **jeden** 2.8.x-Anwender. Fehler darin treffen alle Upgrader. Die Befunde zu #104/#90, #82 und #122/#85 bleiben deshalb relevant, werden aber **direkt im bestehenden Migrationsschritt 9** behoben, ohne neue Version.

---

## Übersicht

| Issue | Titel (gekürzt) | Status in 3.5 | Priorität |
|---|---|---|---|
| [#133](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/133) | Migration schreibt `high_first` über den Firmware-Default | ✅ **behoben** (F1 + F2, 17.10.2026), HW-Test durch den Melder ausstehend | – |
| [#104](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/104) | Akkumulierte Energiezähler falsch / negativ | ✅ **Regression behoben** (F1 + F2, siehe #133), HW-Test ausstehend | – |
| [#90](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/90) | Warmwasser thermisch = elektrisch, extreme Werte | ✅ **Regression behoben** (gleiche Ursache wie #104), HW-Test ausstehend | – |
| [#82](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/82) | Falsche Firmware-Version übernommen | 🟠 **teilweise offen** (Migration bevorzugt veralteten Wert); Index-Fehler im Code nicht nachweisbar | mittel |
| [#100](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/100) | Neue Steuerung FW 1.3.8 / 1.3.10 | 🟠 **teilweise offen** (Restpunkte + Regression #108); V1.0.4-3K ✅ in 3.5.7 | mittel |
| [#122](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/122) | Entity-ID mit falscher Domain (`sensor.*_heating_circuit`) | 🟡 Code behoben, **Registry-Altlasten offen** | mittel (Frist HA 2027.5) |
| [#85](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/85) | Entity-ID mit falscher Domain (`sensor.*_boil1_hot_water`) | 🟡 wie #122 (Duplikat) | mittel (Frist HA 2027.5) |
| [#105](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/105) | E-Manager-Register springt auf 0 | 🟡 vermutlich behoben (3.5.2/3.5.3), **nicht bestätigt** | mittel |
| [#101](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/101) | Solarthermiemodul wird nicht erkannt | 🟡 unklar, Logs fehlen; Schwachstelle in der Modulerkennung | niedrig |
| [#94](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/94) | Verlauf nach Update auf 2.6.0 weg | 🟢 in 3.5 nicht reproduzierbar | niedrig |
| [#95](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/95) | Heizkurven-Stützpunkte zeigen statische Werte | 🟢 kein Code-Bug (so gewollt) + Sentinel-Werte behoben | niedrig |
| [#132](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/132) | Room Temperature / Set Flow Temperature `unknown` | 🟢 kein Code-Bug, nur UX; `target_temp_flow_line` in #134 auf V1.1.0-3K als korrekt bestätigt | niedrig |
| [#120](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/120) | Screenshots PV-Überschuss fehlen (toter Link) | 🔴 **Ursache gefunden:** falscher Bildpfad; in `3.5` sogar 21 Bilder betroffen (siehe F14) | mittel (vor Merge 3.5 → main) |
| [#134](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/134) | Upgrade-Hinweise 2.8.6 → 3.5.6 (Setpoint-Entity, Statistik-Reparaturen) | ✅ **Changelog ergänzt/korrigiert** (17.10.2026), kein Code-Bug | – |
| [#128](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/128) | Heizkurve: Abweichung zum Pumpen-Sollwert (Enhancement) | 🟡 Doku korrigiert (beide Branches), Abweichungssensor offen (F17) | niedrig |
| [#121](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/121) | `device_registry.async_get_device` deprecated | ✅ **behoben** in 3.5.4 | – |
| [#112](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/112) | Register 5007 doppelt adressiert | ✅ **behoben** in 3.5.5 | – |

Legende: 🔴 Fehler im 3.5-Code nachgewiesen · 🟠 Teilaspekte offen · 🟡 unklar bzw. Restarbeit · 🟢 kein Code-Fehler in 3.5 · ✅ behoben (Issue kann geschlossen werden)

---

## ✅ #104 / #133: Akkumulierte Energiezähler falsch / negativ

**Meldung:** `compressor_power_consumption_accumulated` / `..._thermal_energy_output_accumulated` liefern Werte wie -1.341.390.833 Wh. Ursache in 2.x war die 32-Bit-Registerreihenfolge, die Lambda ab V0.0.10 geändert hat. In 2.8.0 wird deshalb `reg_order` aus `FIRMWARE_CONFIG` als Default genommen.

**Prüfung in 3.5:**
- Grundsätzlich richtig umgesetzt: `const.py:22ff`. `FIRMWARE_CONFIG` enthält `reg_order`. `coordinator.py` (ca. Z. 160) nimmt `entry.options[int32_register_order]` und, **wenn das fehlt**, `default_register_order(firmware)`. Die beiden 32-Bit-Zähler werden jeweils am Stück gelesen (`ranges.py`, `(20,21)`, `(22,23)`).
- **Fehler 1: Die Migration überschreibt den Firmware-Default.** `__init__.py:141` ruft `options.setdefault(CONF_INT32_REGISTER_ORDER, await _async_read_register_order(hass))` auf. `_async_read_register_order()` (`__init__.py:151-179`) liefert `DEFAULT_INT32_REGISTER_ORDER` = `high_first`, wenn die YAML-Datei fehlt oder der Schlüssel auskommentiert ist. Das ist der Normalfall, denn in 2.8.x wurde Anwendern ausdrücklich geraten, den Eintrag wieder auszukommentieren. Damit steht nach dem Upgrade 2.8→3.5 **explizit `high_first`** in den Options. Der Firmware-Fallback im Coordinator greift nie mehr. Bei Firmware **V0.0.10-3K und V1.1.0-3K** (`low_first`) kommen dadurch wieder genau die Werte aus #104/#90.
- **Fehler 2: Der Options-Flow schreibt den falschen Default.** `config_flow.py:281` setzt als Default `options.get(CONF_INT32_REGISTER_ORDER, DEFAULT_INT32_REGISTER_ORDER)`. Bei einem neuen Eintrag ohne gespeicherte Option zeigt das Formular also `high_first`. Speichert der Anwender die Optionen (z. B. nur um PV-Überschuss zu aktivieren), wird `high_first` dauerhaft gespeichert, auch bei `low_first`-Firmware.

> **✅ FIXED (17.10.2026, Fehler 1 und 2):** Bestätigt durch [#133](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/133) (echtes Upgrade 2.8.6 → 3.5.6 auf V1.1.0-3K, Zähler rund eine Minute bei 1,14 Mrd. Wh, Langzeitstatistik beschädigt).
> - `__init__.py`: `_async_read_register_order()` gibt `None` zurück, wenn die YAML fehlt, unlesbar ist oder keinen Wert setzt. Die Migration setzt `int32_register_order` nur bei einem expliziten Wert. Sonst gilt die Reihenfolge der Firmware, wie in 2.8.x.
> - `config_flow.py`: Der Options-Flow bietet als Default `options[...]` → `default_register_order(firmware)` → `high_first` an. Unverändertes Speichern ändert also nichts mehr.
> - Tests: `test_config_flow.py` (ohne Datei, auskommentierter Schlüssel bei V1.1.0-3K inkl. Zählerwert, unlesbare Datei, expliziter `high_first` bleibt erhalten) und `test_options_flow.py` (Default je Firmware, gesetzter Wert bleibt). Die neuen Tests schlagen ohne den Fix fehl.
> - Umgesetzt wurden Punkt 1, 2 und 5. Punkt 3 (Wert „auto“) ist durch eine einfachere Lösung ersetzt (siehe unten). Punkt 6 (Doku zur Statistikbereinigung) ist weiter offen.
> - **Nachtrag (17.10.2026):** *Neu konfigurieren* entfernt `int32_register_order` bei einem Firmwarewechsel aus den Options; danach gilt die Reihenfolge der neuen Firmware. Damit bleibt ein Firmwarewechsel auch ohne „auto“ konsistent. Eine abweichende Reihenfolge lässt sich danach wieder unter *Konfigurieren* setzen.
> - Wer 3.5 vor diesem Fix schon installiert hat, hat `high_first` fest in den Options stehen. Das korrigiert sich nicht von selbst: im Options-Dialog einmal die richtige Reihenfolge wählen.

**Lösungsansatz:**
1. In `async_migrate_entry` die Registerreihenfolge **nur** setzen, wenn die alte YAML einen expliziten Wert enthält. `_async_read_register_order()` gibt dann `None` statt `DEFAULT_…` zurück, und `options.setdefault` wird nur bei einem Wert ungleich `None` ausgeführt. Ohne expliziten Wert bleibt der Firmware-Default aus dem Coordinator wirksam.
2. Im Options-Flow den Default aus der Firmware ableiten: `options.get(CONF_INT32_REGISTER_ORDER) or default_register_order(entry.data[CONF_FIRMWARE_VERSION]) or DEFAULT_INT32_REGISTER_ORDER`.
3. ~~Besser noch: einen Wert `"auto"` (= Firmware-Default) einführen und als Default anbieten. Dann bleibt ein Firmwarewechsel über `reconfigure` konsistent.~~ Ersetzt: `reconfigure` setzt die Option bei einem Firmwarewechsel zurück (umgesetzt 17.10.2026).
4. ~~Reparatur bestehender 3.5-Installationen über eine neue Migration (ENTRY_VERSION 10)~~ – **entfällt**, weil 3.5 unveröffentlicht ist. Der Fix in Punkt 1 kommt direkt in den bestehenden Migrationsschritt 9. Eigene Testinstallationen: die Option im Options-Dialog einmal korrekt setzen.
5. Tests: Migration ohne YAML bei `V0.0.10-3K` → keine `int32_register_order` in den Options. Options-Flow bei `V1.1.0-3K` → Default `low_first`.
6. Doku/FAQ: Nach einer Korrektur der Reihenfolge springen die `TOTAL_INCREASING`-Sensoren. Beschreiben, wie man die Statistik bereinigt (`recorder.purge_entities`, Statistik-Korrektur).

---

## ✅ #90: Warmwasser thermisch und elektrisch identisch / extrem hohe Werte

**Meldung (2.5.0, FW 0.0.9):** Warmwasser-Energie thermisch und elektrisch sind (fast) gleich und liegen bei ca. 21.400 kWh bzw. 89.000 kWh. Die akkumulierten Register zeigen negative bzw. unplausible Werte.

**Prüfung in 3.5:**
- Die Energiezuordnung wurde neu geschrieben (`coordinator.py`, `_track_energy` und `_energy_delta`). Elektrisch und thermisch kommen aus **getrennten** Registern und fließen in getrennte Töpfe (`totals.electrical` / `totals.thermal`). Die Verwechslung aus 2.x gibt es nicht mehr.
- `_energy_delta` verwirft negative Deltas und Sprünge > `MAX_ENERGY_DELTA_KWH` (100 kWh pro Poll). Statt zu kappen, wird verworfen (Befund 1 aus #100). Riesige Werte wie 21.400 kWh können so nicht mehr entstehen.
- **Die eigentliche Ursache ist aber die falsche 32-Bit-Registerreihenfolge, und die kann durch die Regression aus #104 wieder auftreten.** Mit falscher Reihenfolge ändern sich die Rohwerte fast nur im (vertauschten) Low-Word. Die Deltas sind dann meist > 100 kWh oder negativ, die Zähler bleiben praktisch stehen. Ein Delta < 100 kWh wird aber falsch gezählt.

**Lösungsansatz:**
1. Den Fix aus #104 umsetzen. Damit ist #90 im Kern erledigt.
2. Zusätzlich eine Plausibilitätswarnung einbauen: Ist ein 32-Bit-Zähler ≤ 0 oder liegt er über z. B. 10⁹ Wh, einmalig ein Warning (optional ein Repair-Issue) auslösen mit dem Hinweis „Registerreihenfolge prüfen“, statt still 0 zu buchen.
3. Den Reporter nach Umstellung auf 3.5.x um Rückmeldung bitten, danach das Issue schließen. Die bestehenden falschen Langzeitstatistiken muss der Anwender selbst bereinigen (Offset in den Optionen oder Statistik löschen, wie im Issue-Kommentar beschrieben).

> **Nachtrag 17.10.2026 – Widerspruch zur Firmware-Tabelle:** Der Melder nennt Firmware „0.0.9-3K“. Seine gemeldeten Werte lassen sich aber exakt als `low_first`-Daten erklären, die als `high_first` gelesen wurden (256.729 Wh → −354.877.437; 1.399.530 Wh → 1.525.284.885). In `FIRMWARE_CONFIG` steht V0.0.9-3K auf `high_first`, und die eigene Testinstallation `.115` (V0.0.9-3K, Live-Test 3.5.6) spricht dafür. Mögliche Erklärungen: falsch abgelesene Version (die Steuerung zeigt mehrere), Version aus HA statt vom Display, oder die Reihenfolge hängt an der Steuerungsgeneration statt an der Firmware-Nummer. **Nicht geändert.** Klärung: im Issue nach der Version in der Statuszeile der WP-Seite und einem Rohwert von Register 1020/1021 fragen.

---

## 🟠 #82: Falsche Firmware-Version wird übernommen

**Meldung (2.4.0):** Gewählt wird „V0.0.10-3K“, eingerichtet wird „V0.0.9-3K“.

**Prüfung in 3.5:**
- Der Config-Flow speichert jetzt direkt den **Namen** (`config_flow.py:100`, `SelectSelector` mit `FIRMWARE_VERSIONS`). `firmware.py: firmware_level()` löst ihn über `FIRMWARE_CONFIG[name]` auf. Ein Index-Versatz ist dabei nicht mehr möglich, **die Neueinrichtung ist also korrekt**.
- **Offen: Die Migration von 2.x übernimmt einen veralteten Wert.** In 2.x hatte `entry.options["firmware_version"]` Vorrang vor `entry.data` (`utils.get_firmware_version`: erst Options, dann Data). Hat ein Anwender die Firmware in 2.x über den Options-Flow geändert, steht der neue Wert in den Options und der alte, ursprüngliche in `data`. 3.5 macht es umgekehrt (`__init__.py:134`): `data.get(FW) or options.pop(FW)`. Der **alte** Wert aus `data` gewinnt, der aktuelle aus den Options wird ignoriert und bleibt sogar als Leiche in den Options stehen. Genau das ergibt den Effekt „falsche (ältere) Version eingerichtet“. Indirekt bekommt der Anwender dann auch die falsche Registerreihenfolge und die falschen Firmware-Gates für Sensoren.
- **Nachtrag 17.10.2026:** Im Code von 2.4.0 (`434e20c`) ist kein Index-Versatz zu finden; Config-Flow und `get_firmware_version()` arbeiten mit dem Namen. Auffällig war dort nur, dass `V1.1.0-3K` und `V0.0.10-3K` beide das Ordinal 8 hatten. Die gemeldete Ursache von #82 bleibt damit unklar; für 3.5 ist nur der Migrationspunkt unten relevant.
- Ein unbekannter Firmware-Name fällt still auf `FIRMWARE_VERSIONS[-1]` zurück (`V0.0.3-3K`, die älteste). Das betrifft z. B. Einträge mit Namen, die es nur in einem Testbranch gab.

**Lösungsansatz:**
1. Im bestehenden Migrationsschritt (`async_migrate_entry`, Version 9, **keine neue Version nötig**, da 3.5 unveröffentlicht ist) die 2.x-Priorität übernehmen: `firmware = options.pop(CONF_FIRMWARE_VERSION, None) or data.get(CONF_FIRMWARE_VERSION)`. Den Options-Schlüssel dabei immer entfernen.
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
| Firmware „V1.0.4-3K“ in die Auswahl aufnehmen (zugesagt am 04.08.) | ✅ **FIXED** 17.10.2026: in `FIRMWARE_CONFIG` mit Ordinal 9 und `low_first` (Rohdump von @madmaxx425); `V1.1.0-3K` rückt auf 10 |

**Regression von #108 (geschlossen):** In `main`/2.8.x wurde `ambient_temperature` auf Wunsch von #108 auf `firmware_versions: ["1-9"]` erweitert, weil Register 2 auch auf V1.1.0-3K gültige Werte liefert und ungültige Werte über `sentinel_values` abgefangen werden. In 3.5 steht wieder `firmware_versions=("1-7",)` (`sensor.py:177`). Auf **V0.0.10-3K und V1.1.0-3K wird die Entity also gar nicht mehr angelegt**, obwohl `general.py` den 0xFFFF-Sentinel für dieses Feld bereits abfängt.

**Lösungsansatz:**
1. `sensor.py:177`: Die Firmware-Range entfernen (oder `("1-9",)` setzen). Die Sentinel-Filterung in `Ambient.temperature` reicht aus. Dazu einen Regressionstest für #108 schreiben.
2. ✅ **Erledigt (3.5.7).** ~~`"V1.0.4-3K"` in `FIRMWARE_CONFIG` aufnehmen.~~ Ordinal und `reg_order` vorher mit den Testern aus #100 klären (@b-bremer, @7xy, @madmaxx425). Laut Thread sind die Register identisch mit Protokoll 1.0, die Reihenfolge ist vermutlich `low_first`. Achtung: Ordinals sind Vergleichswerte für `firmware_version`. Eine neue Version zwischen den bestehenden erfordert entweder eine Neunummerierung (und eine Prüfung aller `firmware_version`/`firmware_versions`-Angaben) oder ein Ordinal ≥ 10.
3. `config_parameter_*` (die `integer`-Felder im Bereich 1024–1060): entweder `nan=SENTINELS` am Feld setzen oder sie per `firmware_versions` auf die alten Steuerungen begrenzen. Die Alternative: Default-mäßig deaktivieren (`entity_registry_enabled_default=False`), weil sie undokumentiert sind.
4. `volume_flow_heat_sink`: Mit Lambda-Protokoll 1.0 und einem Rohwert-Dump verifizieren. Ist die Korrektur bestätigt, `gauge(6, 0.01, unit="l/min")` verwenden und die Sensoreinheit anpassen. **Achtung:** Schon der Wechsel 2.x → 3.5 erzeugt für diesen Sensor die Reparaturen „Einheit geändert“ (`l/h` → `L/h`) und „Mittelwert-Typ geändert“ (`total` → `measurement`, nur durch Löschen der Statistik behebbar, siehe #134). Ein weiterer Einheitenwechsel sollte deshalb **im selben Release** kommen, damit Anwender die Statistik nur einmal löschen müssen.
5. In der Doku (initiale Konfiguration) klarstellen, welche Versionsanzeige gemeint ist (Statuszeile der WP-Seite, nicht SW-Version). Laut Thread ist die Doku mit GIF bereits online, also nur prüfen.

---

## 🟡 #122 und #85: Entity-ID mit falscher Domain (`sensor.*` statt `climate.*`)

**Meldung:** HA warnt „sets an entity ID with wrong domain: `sensor.eu13l_hc1_heating_circuit`“ bzw. `sensor.eu13l_boil1_hot_water`. Ab HA 2027.5 funktioniert das nicht mehr.

**Prüfung in 3.5:**
- Im Code behoben: `entity.py:84-86` schlägt die Entity-ID aus `_entity_domain` vor, und `climate.py:105` setzt `_entity_domain = "climate"`. `number.py` und `sensor.py` setzen ebenfalls ihre eigene Domain. Neue Installationen erzeugen also `climate.<prefix>_hc1_heating_circuit` bzw. `climate.<prefix>_boil1_hot_water`.
- **Offen (Upgrade-Pfad 2.x → 3.5):** Geprüft in `main`: 2.x setzt in `climate.py` `self.entity_id = names["entity_id"]` aus `generate_sensor_names()`. Die Climate-Entities wurden also tatsächlich mit `sensor.*`-ID registriert. Installationen, die von 2.x upgraden, behalten diese ID in der Entity-Registry, denn die Registry-ID hat Vorrang vor dem Vorschlag. Ob HA bei solchen Registry-Einträgen ab 2027.5 ebenfalls warnt bzw. sie ablehnt, sollte mit einem Test gegen eine aktuelle HA-Version geprüft werden. Sicher ist: Die IDs bleiben inkonsistent.

**Lösungsansatz:**
1. Im bestehenden Migrationsschritt 9 (`async_migrate_entry`; als unveröffentlichte Version ist **keine neue `ENTRY_VERSION` nötig**) die Entity-Registry durchgehen: `er.async_entries_for_config_entry(registry, entry.entry_id)`. Jeden Eintrag mit `entry.domain == "climate"`, dessen `entity_id` nicht mit `climate.` beginnt, über `registry.async_update_entity(entity_id, new_entity_id=f"climate.{object_id}")` umbenennen. Vorher auf Kollisionen prüfen (`registry.async_get(new_id)`).
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
4. **Nachtrag 17.10.2026:** In #134 bestätigt der Melder auf V1.1.0-3K mit 3.5.6, dass `hc1_target_temp_flow_line` im Heizbetrieb echte Werte liefert (33,2 °C, identisch mit Display und Kurve). Der Teil „Set Flow Temperature `unknown`“ ist damit für Firmware 3+ erledigt; das Issue kann geschlossen werden.

---

## 🔴 #120: Screenshots zur PV-Überschuss-Konfiguration fehlen

> **Analyse 17.10.2026 – frühere Annahme „Link im Repo gültig“ war falsch.** Beide Branches wurden mit `zensical build` gebaut und alle `<img>`-Pfade der fertigen Seiten nachgerechnet.

**Ursache:**
- Die Bilder `pv_surplus_de_{1,2}.png` liegen seit März in `docs/docs/assets/` (beide Branches).
- `pv_ueberschuss_steuerung.md:24/28` verweist auf `../../assets/…`. Zensical löst relative Pfade auch in rohem `<img>`-HTML **relativ zur Quelldatei** auf (`docs/docs/Anwender/`) und setzt beim Bauen eine Ebene davor. Aus `../../assets/` wird `../../../assets/`, und das zeigt aus der Seite heraus. Richtig ist `../assets/…` (so funktioniert z. B. `heizkurve.md` in `main`).
- Historie `main`: `09c8d81` (04.08.) hat alle Pfade auf `../assets/` korrigiert, `a4fe6fb` (04.08.) hat die PV-Seite wieder auf `../../assets/` zurückgesetzt.

**Umfang:**

| Stand | Kaputte Bilder in der gebauten Doku |
|---|---|
| `main` (live) | 2 (nur PV-Seite) |
| `3.5` | **21 auf 16 Seiten** (u. a. Heizkurve, Optionen, Entitäten löschen, Debug-Logs, Historische Daten löschen, alle Dashboard-Vorlagen) |
| Test-Merge `3.5` → `main` | **21**, die `3.5`-Fassung gewinnt (`3.5` ist vor `09c8d81` abgezweigt; `26b4e71` hat die Pfade dort sogar ausdrücklich auf `../../` gesetzt) |

**Weitere Befunde zur Seite:**
- Bild 1 zeigt den Options-Dialog aus 2.x mit drei Messpunkten (E-Eintrag / Pos. / Neg.). In 3.5 gibt es nur `pos`/`neg` („Kodierung des PV-Überschusses“). Das Bild passt nicht mehr zu 3.5.
- Bild 2 zeigt die Energie-Management-Seite der Lambda mit Betriebsart „Automatik“, aber nicht die nötigen E-Manager-Einstellungen. Ein Tester (Kommentar im Issue, EU10L, V1.1.0-3K, 3.5.6) betreibt es mit E-Meter-Typ „Modbus Client“, Messpunkt „E-Überschuss“, Betriebsart „manuell“; er bietet diesen Text als Ersatz an. Ob „Automatik“ oder „manuell“ richtig ist, muss der Maintainer entscheiden.
- Code-Beobachtung desselben Testers: siehe F15 (kein Weiterschreiben bei ausgefallener Quelle → E-Manager-Fehler 6).

**Lösungsansatz:**
1. ✅ **F14 in `3.5` erledigt (17.10.2026):** alle 21 Pfade in 14 Dateien auf `../assets/`, dazu 10 tote Anker korrigiert. Build ohne Hinweise, Prüfer: 0 Probleme; Merge-Probe `3.5` → `main`: 0 Probleme. In `main` (live) ist die PV-Seite weiterhin kaputt, bis dort dieselbe Zeile geändert wird oder 3.5 gemergt ist. ~~Alle betroffenen Pfade auf `../assets/` setzen, **in beiden Branches identisch** (in `main` nur die PV-Seite, in `3.5` alle 16 Seiten). Dann bleibt der Merge konfliktfrei und das Ergebnis korrekt. Nachweis: Build + Pfadprüfung → 0 kaputte Bilder.~~
2. PV-Seite um eine Schritt-für-Schritt-Anleitung nach dem Vorschlag des Testers ergänzen; Bild 1 durch einen Screenshot aus 3.5 ersetzen (muss der Maintainer liefern).
3. Danach Issue schließen.

---

## ✅ #134: Upgrade-Hinweise 2.8.6 → 3.5.6

**Meldung:** (1) `hc1_flow_line_temperature_setpoint` verschwindet auf Firmware 3+ und verwaist. (2) Nach dem Upgrade 11 Statistik-Reparaturen, keine davon über die Oberfläche behebbar.

**Prüfung:**
- (1) Gewollt, Fix für #112 (3.5.5): `flow_line_temperature_setpoint` nur noch für Firmware-Stufe 1–2 (`sensor.py:307`), ab Stufe 3 (V0.0.5-3K) ersetzt durch `target_temp_flow_line`. Keine Registry-Migration (andere `unique_id`, andere Bedeutung).
- (2) Die Volumenstrom-Sensoren waren in 2.8.6 `state_class: total` mit `l/h`/`l/min`, in 3.5 `measurement` mit `L/h`/`L/min`. Pro Sensor erscheinen „Einheit geändert“ **und** „Mittelwert-Typ geändert“. Laut HA-Frontend (`fix_issue.mean_type_changed`) lässt sich der Mittelwert-Typ **nur durch Löschen der Statistik** beheben; bis dahin keine neue Langzeitstatistik. Die Option „Einheit … aktualisieren, ohne Konvertierung“ allein reicht nicht. Der Changelog vom 15.10. hatte das falsch („Historie bleibt erhalten“).

**Erledigt (17.10.2026):**
- Changelog (beide Dateien, EN/DE): Upgrade-Hinweis zu `hcX_flow_line_temperature_setpoint` → `hcX_target_temp_flow_line` inkl. Vorgehen zum Erhalt der Statistik (verwaiste Entity löschen, neue auf alte entity_id umbenennen).
- Changelog: Statistik-Reparaturen mit HA-Wortlaut der Optionen; Empfehlung auf „Alle alten Statistikdaten für diese Entität löschen“ korrigiert; Einleitung „es geht nichts verloren“ eingeschränkt.

**Offen:** Antwort im Issue (Entwurf liegt vor). Danach schließen.

---

## 🟡 #128 (Enhancement): Heizkurve – Abweichung zum realen Vorlauf-Sollwert

**Prüfung in 3.5:**
- Stützpunkte und Eco-Absenkung sind HA-Handwerte (`number.py`, `RestoreNumber`, Bereich 15–75 °C, `const.py:188ff`). Nur `heating_curve_flow_line_temperature_calc` (`sensor.py:991ff`) nutzt sie (plus Offset 5X50, Eco-Absenkung, HA-Raumkorrektur).
- **Nichts schreibt in 5X05.** An die Pumpe gehen nur: Raumtemperatur eines HA-Sensors → 5X04 (alle 9 s), Raum-Soll aus Climate → 5X51, Vorlauf-Offset → 5X50. Die Pumpe regelt immer mit ihrer eigenen Kurve. Gleiches Verhalten in 2.8.6 (`main`, `services.py`: nur 5004).
- Der echte Sollwert: `target_temp_flow_line` (ab Stufe 3) bzw. `flow_line_temperature_setpoint` (Stufe 1–2). Der Melder nutzt bereits einen Template-Helfer „Sollwert minus berechnete Kurve“ und hat damit eine veraltete HA-Kurve nach einer Display-Änderung erkannt.

**Erledigt (17.10.2026):** Doku korrigiert, **identisch in `3.5` und `main`** (Merge-Probe konfliktfrei): `raumthermometer.md` behauptete „die berechnete Temperatur wird an die Lambda geschrieben“ – richtig ist, nur die Raumtemperatur geht nach 5X04. `heizkurve.md` hat einen Infokasten: Handwerte, Defaults 48,3/39,0/32,0 °C sind nicht die der Pumpe, nach Display-Änderung nachziehen, echter Sollwert in `hcX_target_temp_flow_line`. Datum beider Seiten auf 17.10.2026.

**Offen:**
1. **F17 Abweichungssensor** (S–M): Sollwert der Pumpe minus Kurve, nur im Zustand HEATING, sonst `unknown`. Vorher klären: Enthält `target_temp_flow_line` den Offset 5X50? Soll die HA-Raumkorrektur aus dem Vergleich heraus (die Pumpe hat eine eigene Raumaufschaltung)?
2. Bereich der Stützpunkte an realistische Grenzen anpassen (S). Ein Schutz für Modbus ist nicht nötig, da 5X05 nie geschrieben wird.
3. Kurvenschätzung (L) und Offset 5X50 als Stellgröße (L): als eigene Issues vormerken.

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
| Registerreihenfolge überlebte einen Firmwarewechsel unter „Neu konfigurieren“ | `config_flow.py`, `async_step_reconfigure` | ✅ behoben in 3.5.7 |
| V0.0.9-3K: Firmware-Tabelle (`high_first`) widerspricht den Werten aus #90 (`low_first`) | `const.py:FIRMWARE_CONFIG` | siehe #90, offen |
| Bildpfade `../../assets/` statt `../assets/` (21 Bilder in `3.5`, 2 in `main`) | `docs/docs/Anwender/*.md`, `docs/docs/Vorlagen/*.md` | F14, ✅ in `3.5` behoben |
| 10 tote Anker in der Entwickler-Doku (Slugs mit Umlauten, umbenannte Überschriften); in `main` schon mit `2ade7ce` behoben | `docs/docs/Entwickler/*.md`, `Releases/release-2-3.md` | ✅ in `3.5` behoben |
| Doku in `3.5` wurde nie gebaut, Fehler fielen nicht auf | – | ✅ neuer Workflow `docs-check.yml` + `script/check_docs.py` |
| PV-Überschuss: kein Weiterschreiben, wenn der Quellsensor `unknown`/`unavailable` ist → E-Manager-Fehler 6 nach einigen Minuten (auch in 2.8.6 so) | `services.py:105ff` | F15, siehe #120 |
| 2.x-Modus `pv_surplus_mode: entry` wird nicht migriert; 3.5 kennt nur `pos`/`neg`. Schreiben funktioniert (wie `pos`), im Options-Dialog ist `entry` aber kein gültiger Auswahlwert (Verhalten der Oberfläche ungeprüft) | `__init__.py`, `async_migrate_entry` | F16 |
| Merge `3.5` → `main` hat einen Konflikt in `hacs.json` (`homeassistant`: 2024.3.3 vs. 2026.9.0); richtig ist der Wert aus `3.5` | `hacs.json` | Merge-Vorbereitung |
| Doku-Workflow hat keinen `workflow_dispatch`, lässt sich also nicht manuell starten | `.github/workflows/docsz.yml` | optional |
| **Externer Energiezähler: Rückfall auf das Lambda-Register.** Liefert ein in `energy_consumption_sensors` eingetragener Zähler `unknown`/`unavailable`, nimmt `_track_energy` (`if reading is None: reading = register`) das Lambda-Register, obwohl `_meter_reading` laut Kommentar genau das vermeiden soll. Kommt der Zähler zurück, wird die Differenz zwischen beiden Zählern als Verbrauch gebucht, sofern sie unter 100 kWh liegt. | `coordinator.py:458-460` | F18, ✅ behoben 18.10.2026 (`_energy_source`, `_forget_energy_sources`) |
| **Hilfetext zur Firmware im Einrichtungsdialog falsch:** „Wird als Firmware des Geräts angezeigt und ändert nichts am Auslesen.“ Die Firmware bestimmt Sensoren und Register-Reihenfolge. | `strings.json`, `translations/*.json` (`config.step.user.data_description.firmware_version`) | F19, ✅ behoben 18.10.2026 |

## Kompatibilität mit Home Assistant 2026.10 / 2026.11 (geprüft 19.10.2026)

Geprüft gegen `homeassistant==2026.10.2` mit `modbus-connection[tmodbus]==4.12.4` (die Version, die HA 2026.10 selbst mitbringt), Python 3.14, Branch `3.5`.

**Ergebnis:** Die Integration läuft unter 2026.10 ohne Funktionsverlust und ohne eine einzige Deprecation-Meldung aus `custom_components/lambda_heat_pumps`. 157 von 158 Tests bestehen; der eine Fehlschlag liegt im Testcode (F20).

| Thema (HA-Changelog / Dev-Blog) | Betroffen? |
|---|---|
| `device_registry.async_get_device` deprecated, wirft in Testcode einen Fehler | Integration nein (nutzt `async_get_device_by_identifier`, `coordinator.py:249`); **Test ja** → F20 |
| `DeviceEntry.config_entries` wird durchgesetzt, `via_device` → `via_device_id` | nein, bereits umgestellt |
| `modbus.get_hub` deprecated | nein, nicht genutzt |
| Probatio ersetzt `voluptuous` (seit 2026.9) | nein; Config-Flow-, Service- und `lambda_wp_config.yaml`-Schemas laufen unter 2026.10.2 fehlerfrei. **War aber bisher ungetestet**, weil die Testumgebung auf HA 2026.8.1 steht → F20 |
| Config-Entry-Exceptions in `async_migrate_entry`, zentrale Abort-Gründe | optional, keine Änderung nötig |
| `RestoreStateData.last_states` entfällt (2026.11) | nein, nur `async_get_last_sensor_data`/`async_get_last_number_data`/`async_get_last_state` |
| Climate: `current_temperature`, `target_temperature`, `temperature_unit` → `native_…` (2026.11, alte Namen bis 2027.11 mit Warnung) | **ja** (`climate.py:109`, `:158`, `:163`) → F21 |
| hassfest prüft die `requirements` von Custom-Integrationen | `ha.yml` läuft nur auf `main` (Push/Schedule) und bei PRs; 3.5 wurde noch nicht geprüft → F22 |

**F20 – Testumgebung auf HA 2026.10 anheben.** `requirements_test.txt` pinnt `pytest-homeassistant-custom-component==0.13.355` (= HA 2026.8.1), die Integration verlangt aber mindestens 2026.9.0 (`hacs.json`). Auf eine Version mit HA 2026.10 anheben (z. B. `0.13.373`, getestet). Gleichzeitig `tests/test_init.py:308` und `:312` von `devices.async_get_device(identifiers=…)` auf `devices.async_get_device_by_identifier(…, entry.entry_id)` umstellen, sonst schlägt `test_modules_are_their_own_devices` fehl.

**F21 – Climate-Properties auf `native_…` umstellen (erst mit 2026.11).** Bewusst **abwarten**: HA 2026.9 und 2026.10 kennen die neuen Namen noch nicht (in 2026.10.2 geprüft). Eine Umstellung jetzt würde dort Ist-/Solltemperatur und Einheit der Klima-Entitäten verlieren. Ab 2026.11 schreiben die alten Namen nur Warnungen ins Log, entfernt werden sie in 2027.11. Umsetzung, sobald 2026.11 erschienen ist:
- `climate.py:109` `_attr_temperature_unit` → `_attr_native_temperature_unit`
- `climate.py:158` `current_temperature` → `native_current_temperature`
- `climate.py:163` `target_temperature` → `native_target_temperature`
- `async_set_temperature` und eigene Lesezugriffe auf die alten Namen prüfen
- im selben Commit `hacs.json` `homeassistant` auf `2026.11.0` anheben, Testumgebung (F20) auf HA 2026.11 nachziehen
- `min_temp`, `max_temp`, `target_temperature_step` bleiben unverändert

**F22 – hassfest auf `3.5` laufen lassen.** Seit 2026.10 prüft hassfest auch die `requirements` von Custom-Integrationen (`modbus-connection[tmodbus]>=4.8.1`). Der Lauf passiert automatisch mit dem Merge-PR `3.5` → `main`; alternativ vorher `ha.yml` per `workflow_dispatch` auf `3.5` starten.

## Bewertung der Fixes: Komplexität, Kritikalität, Testaufwand

**Skalen:**
- **Komplexität:** S = wenige Zeilen, lokal · M = mehrere Stellen oder neue Logik · L = Design- oder Abstimmungsbedarf
- **Kritikalität:** Auswirkung × Wahrscheinlichkeit, jeweils bezogen auf den Upgrade 2.8.x → 3.5. 🔴 hoch: viele Anwender, Datenschaden oder Funktionsverlust · 🟠 mittel · 🟢 niedrig
- **Testaufwand:** *Unit* = pytest mit dem vorhandenen simulierten `Controller` (`tests/conftest.py`) · *HW* = Verifikation an echter Anlage bzw. echtem Upgrade

**Neu (17.10.2026):** Der Lambda-Simulator aus [modbus_tools](https://github.com/GuidoJeuken-6512/modbus_tools) (`GuiServer/server_threaded.py`, ohne GUI startbar, Wortreihenfolge der 32-Bit-Register umschaltbar) erlaubt End-to-End-Tests über echtes Modbus-TCP. Mit der Fixture `socket_enabled` läuft die echte Integration in der HA-Testumgebung dagegen. Für F1/F2/F6 und das Zurücksetzen bei Firmwarewechsel bestanden alle 6 Szenarien; mit dem Code vor dem Fix reproduzierte der Simulator #133 exakt (1.111.490.575 Wh statt 1.000.000). Hinweis zum Simulator: Mit einer begrenzten Log-Queue ohne Leser blockiert `setup_modbus_server()` beim Start. Der Test liegt noch nicht im Repo.

Der Testaufwand ist realistisch abschätzbar, weil die Infrastruktur steht. Für Migrationen gibt es `tests/test_config_flow.py` (Einträge mit `version=8`), für die Registry und Firmware-Gates `tests/test_init.py`, für Optionen `tests/test_options_flow.py`, für Timeouts `fail_read(...)` in `conftest.py`.

| # | Fix | Issue | Komplexität | Kritikalität | Testaufwand |
|---|---|---|---|---|---|
| F1 | ✅ **FIXED** – Migration: Registerreihenfolge nur übernehmen, wenn die YAML sie explizit setzt | #104/#90/#133 | **S** (~10 Zeilen, `__init__.py:141-179`) | 🔴 **hoch** | Unit **M** + HW **M** |
| F2 | ✅ **FIXED** (einfache Variante + Zurücksetzen bei Firmwarewechsel) – Options-Flow: Default der Registerreihenfolge aus der Firmware | #104/#133 | **S** (~3 Zeilen, `config_flow.py:281`); Variante „auto“: **M** | 🔴 **hoch** | Unit **S**; mit „auto“ **M** |
| F3 | `ambient_temperature`: Firmware-Range 1-7 entfernen | #100/#108 | **S** (1 Zeile, `sensor.py:177`) | 🟠 **mittel–hoch** | Unit **M** (Test schreibt Bug fest) + HW **S** |
| F4 | Migration: Firmware aus Options vor Data, Warnung bei unbekanntem Namen | #82 | **S** (~5 Zeilen, `__init__.py:134`) | 🟠 **mittel** | Unit **S** |
| F5 | Climate-Entity-IDs `sensor.*` → `climate.*` in der Registry umbenennen | #122/#85 | **M** (~30–40 Zeilen + Klärung des HA-Verhaltens) | 🟠 **mittel** (ab HA 2027.5 hoch) | Unit **M** + HW **M** |
| F6 | ✅ **FIXED** – `V1.0.4-3K` in `FIRMWARE_CONFIG` aufnehmen | #100 | **S** im Code, **L** in der Klärung (Ordinal, `reg_order`) | 🟠 **mittel** | Unit **S** + HW durch Tester |
| F7 | `volume_flow_heat_sink`: Einheit/Skala prüfen und korrigieren | #100 | **S** im Code, **M** in der Verifikation | 🟢–🟠 **niedrig–mittel** | Unit **S** + HW **M** (Rohwert-Dump) |
| F8 | `config_parameter_*`: 32768 ausblenden bzw. Default aus | #100 | **S** (4 Felder) | 🟢 **niedrig** | Unit **S** |
| F9 | Modulerkennung: Retry bei Timeout | #101/#90 | **S–M** (~15 Zeilen) | 🟢 **niedrig** (selten, Reload hilft) | Unit **M** |
| F10 | PV-Überschuss: Debug-Log und optionales Rücklesen | #105 | **S** | 🟠 **mittel** (falls der Bug noch existiert; unbestätigt) | HW **M** (Beobachtung über Stunden) |
| F11 | Plausibilitätswarnung für 32-Bit-Zähler | #90/#104 | **S–M** | 🟢 **niedrig** (Absicherung, F1/F2 sind der Fix) | Unit **S** |
| F12 | #132: Eingaberegister standardmäßig deaktivieren bzw. als Diagnose führen | #132 | **S** | 🟢 **niedrig** (UX) | Unit **S** |
| F13 | ✅ **erledigt** (17.10.2026, beide Branches) – #95: Doku zur Heizkurve/Raumthermometer | #95/#128 | **S** | 🟢 **niedrig** | manuell |
| F14 | ✅ **FIXED in `3.5`** (17.10.2026; `main`: nur PV-Seite offen) – Bildpfade `../../assets/` → `../assets/` | #120 | **S** (16 Dateien, mechanisch) | 🟠 **mittel** (vor dem Merge zwingend, sonst 21 kaputte Bilder live) | Build + Pfadprüfung (Skript vorhanden) |
| F15 | PV-Überschuss: 0 W senden (+ Log-Warnung), wenn die Quelle `unknown`/`unavailable` ist | #120/#105 | **S** | 🟠 **mittel** (verhindert E-Manager-Fehler 6) | Unit **S** |
| F16 | Migration: `pv_surplus_mode: entry` → `pos` | – | **S** (1 Zeile in Schritt 9) | 🟢 **niedrig** | Unit **S** |
| F17 | Abweichungssensor Pumpen-Sollwert − berechnete Kurve | #128 | **S–M** | 🟢 **niedrig** (Enhancement) | Unit **S** + HW **S** |
| F18 | ✅ **FIXED** 18.10.2026 – Externer Zähler: Rückfall aufs Register erlaubt, aber jeder Quellenwechsel und jeder Ausfall beginnt wie beim Start (erste Differenz verworfen) | – | **S** (2 Zeilen, `coordinator.py:458`) | 🟠 **mittel** (falsche kWh bei jedem Ausfall des Zählers) | Unit **S** |
| F19 | ✅ **FIXED** 18.10.2026 – Hilfetext zur Firmware im Einrichtungsdialog korrigieren (auch unter Neu konfigurieren) | – | **S** (Übersetzungen) | 🟢 **niedrig** | – |
| F20 | Testumgebung auf HA 2026.10 anheben + deprecated `async_get_device` im Test ersetzen | HA 2026.10 | **S** (1 Pin + 2 Testzeilen) | 🟠 **mittel** (Tests laufen sonst gegen eine HA-Version unter dem Minimum) | Testlauf |
| F21 | Climate-Properties → `native_…`, Mindestversion 2026.11.0 – **erst nach Erscheinen von 2026.11** | HA 2026.11 | **S** (~5 Zeilen + `hacs.json`) | 🟢 **niedrig** (nur Log-Warnungen bis 2027.11) | Unit **S** |
| F22 | hassfest (`ha.yml`) auf `3.5` laufen lassen | HA 2026.10 | – | 🟢 **niedrig** | CI |

### Begründungen im Detail

**F1 – Registerreihenfolge in der Migration (🔴 hoch, S, Test M)** – ✅ **FIXED** 17.10.2026 (#133), HW-Test steht noch aus
- *Wer ist betroffen:* Jeder 2.8.x-Anwender mit Firmware V0.0.10-3K oder V1.1.0-3K, der **keinen** expliziten Wert in `lambda_wp_config.yaml` hat. Genau diesen Anwendern wurde in #104 geraten, die Zeile wieder auszukommentieren. Auch alle Neuinstallationen ab 2.8.0 mit neuer Steuerung gehören dazu. Das ist vermutlich der Großteil der aktiven Nutzer.
- *Folge:* Unmittelbar nach dem Upgrade liefern die akkumulierten Zähler wieder Unsinn. `TOTAL_INCREASING`-Sensoren springen, die **Langzeitstatistik im Energie-Dashboard wird beschädigt**. Das ist irreversibel, nur manuell zu bereinigen, und es tritt genau beim Release auf.
- *Code:* Klein. `_async_read_register_order()` gibt `None` zurück, wenn kein expliziter Wert existiert, und `setdefault` läuft nur bei einem Wert ungleich `None`. Der Firmware-Fallback im Coordinator existiert bereits und ist getestet (`test_the_register_order_defaults_to_what_the_firmware_uses`).
- *Tests:*
  - `test_an_older_entry_without_the_config_file` und `test_an_unreadable_old_config_file_falls_back_to_the_default_order` **schreiben das Fehlverhalten fest** (`== DEFAULT_INT32_REGISTER_ORDER` in den Options). Beide müssen umgeschrieben werden: Erwartet wird „kein Options-Eintrag“, die effektive Reihenfolge folgt der Firmware.
  - Neu: Die Tests mit V0.0.10-3K **und** V0.0.8-3K parametrisieren (beide `reg_order`-Werte), jeweils mit explizitem YAML-Wert, ohne Datei, mit auskommentiertem Wert und mit unlesbarer Datei.
  - HW: einen echten Upgrade 2.8.6 → 3.5 auf einer `low_first`-Anlage durchführen und Zählerwerte und Statistik vor und nach dem Upgrade vergleichen.

**F2 – Default im Options-Flow (🔴 hoch, S, Test S)** – ✅ **FIXED** 17.10.2026 (#133), einfache Variante; statt „auto“ setzt *Neu konfigurieren* die Option bei einem Firmwarewechsel zurück
- *Wer ist betroffen:* Jeder Anwender mit `low_first`-Firmware ohne gespeicherte Option, der den Options-Dialog speichert, egal aus welchem Grund. Das trifft Neuinstallationen und, nach F1, auch alle Upgrader. Ohne F2 macht der Options-Dialog F1 also wieder kaputt. **F1 und F2 gehören zusammen.**
- *Code:* Die einfache Variante ist ein Default aus `default_register_order(firmware)`. Sie speichert den Wert beim Speichern aber fest. Ein späterer Firmwarewechsel über *Neu konfigurieren* zieht die Reihenfolge dann nicht mehr nach. Die Variante „auto“ (eigener Wert, Übersetzungen in `strings.json`/`translations/*.json`, Auswertung im Coordinator) ist sauberer, aber M. **Empfehlung:** vor dem Release die einfache Variante, „auto“ später als Verbesserung.
- *Tests:* In `tests/test_options_flow.py` den Default für V1.1.0-3K (`low_first`) und V0.0.8-3K (`high_first`) prüfen, außerdem, dass ein gespeicherter Wert erhalten bleibt.

**F3 – `ambient_temperature` (🟠 mittel–hoch, S, Test M)**
- *Wer ist betroffen:* Alle Anwender mit V0.0.10-3K oder V1.1.0-3K. In 2.8.x existiert die Entity (Fix #108), nach dem Upgrade auf 3.5 verschwindet sie: „nicht mehr bereitgestellt“. Automationen und Dashboards mit der Außentemperatur brechen. Das ist eine sichtbare Regression bei einem zentralen Sensor.
- *Code:* 1 Zeile. Die Sentinel-Filterung (`general.py`, `nan=SENTINELS + (NO_REQUEST,)`) fängt ungültige Werte bereits ab.
- *Tests:* `test_a_register_its_firmware_withdrew_is_not_modelled` (`tests/test_init.py:176`) nutzt **genau `ambient_temperature`** als Beispiel für den Firmware-Range-Mechanismus und prüft, dass die Entity bei V1.1.0 **fehlt**. Der Test muss auf ein anderes Register umgestellt werden (oder auf ein Test-Template), damit der Mechanismus weiter abgedeckt bleibt. Neu kommt ein Regressionstest für #108 hinzu: V1.1.0 mit gültigem Wert → Entity vorhanden, Wert korrekt; 0xFFFF → `unknown`. HW: kurzer Blick auf eine V1.1.0-Anlage.
- *Hinweis:* Die Range 1-7 wurde im Rewrite bewusst gesetzt, siehe Test und Kommentar „newer controllers … report nothing through it (0x8000)“. Das widerspricht dem Hardware-Befund aus #108. Vor dem Fix kurz mit dem Autor des Rewrites abstimmen.

**F4 – Firmware-Priorität in der Migration (🟠 mittel, S, Test S)**
- *Wer ist betroffen:* Nur 2.x-Anwender, die die Firmware nachträglich über den Options-Dialog geändert haben, sodass `options` und `data` voneinander abweichen. Das kommt seltener vor, ist aber typisch nach einem Steuerungstausch (#100) oder einem Firmware-Update.
- *Folge:* Falsche Firmware-Gates (Sensoren fehlen oder sind zu viel), dazu über F1 eventuell die falsche Registerreihenfolge. Die Folgen sind dieselben wie bei #104, nur seltener.
- *Tests:* Ein neuer Migrationstest, in dem `data` und `options` unterschiedliche Firmware haben und die Options gewinnen müssen. `test_an_older_entry_is_brought_forward` (nur Options) bleibt gültig.

**F5 – Registry-Umbenennung der Climate-IDs (🟠 mittel, M, Test M)**
- *Wer ist betroffen:* Alle 2.x-Anwender mit Warmwasser-Climate (praktisch alle) bzw. mit Heizkreis-Climate. Heute gibt es nur eine Log-Warnung, ab **HA 2027.5** droht ein Funktionsverlust.
- *Komplexität:* Der Code selbst (`er.async_entries_for_config_entry`, `async_update_entity(new_entity_id=…)`) ist überschaubar. Aufwand machen:
  1. Zuerst klären, wie HA solche Registry-Einträge heute behandelt und ab 2027.5 behandeln wird. Möglicherweise korrigiert HA sie selbst, dann entfällt F5.
  2. Kollisionen behandeln (Ziel-ID belegt).
  3. **Breaking Change für Anwender:** Automationen, Skripte und Dashboards mit `sensor.*_hot_water` bzw. `sensor.*_heating_circuit` müssen angepasst werden. Das gehört in die Release Notes. Da 3.5 ohnehin ein großer Versionssprung ist, passt der Zeitpunkt gut.
- *Tests:* Unit mit vorbereitetem Registry-Eintrag (Plattform `climate`, ID `sensor.…`) für drei Fälle: umbenannt, Kollision, bereits korrekt (Idempotenz). HW: echter Upgrade einer 2.8.6-Installation, danach prüfen, ob die Warnung weg ist und die Historie an der neuen ID hängt.

**F6 – Firmware `V1.0.4-3K` (🟠 mittel, Code S, Klärung L)** – ✅ **FIXED** 17.10.2026: Ordinal 9 zwischen V0.0.10 (8) und V1.1.0 (jetzt 10), `low_first` laut Rohdump in #100. Kein Sensor prüft auf 8–10, Einträge speichern den Namen.
- Der Code ist ein Eintrag in `FIRMWARE_CONFIG`. Die eigentliche Arbeit ist die Klärung: Ist V1.0.4-3K funktional neuer als V1.1.0-3K oder ein paralleler Zweig (Steuerungs-SW vs. WP-Firmware, siehe #100)? Davon hängt das Ordinal ab. Ein Einschub zwischen bestehende Ordinals würde **alle** `firmware_version`/`firmware_versions`-Angaben verschieben und **bestehende Einträge** (die den Namen speichern, nicht das Ordinal) still umgaten. Ordinal ≥ 10 ist risikoarm.
- *Tests:* `tests/test_firmware.py` (Ordinal, `reg_order`) erweitern. Die Verifikation an echter Hardware muss durch die Tester aus #100 erfolgen. Das ist die Abhängigkeit mit der größten Unsicherheit beim Zeitplan.

**F7 – `volume_flow_heat_sink` (🟢–🟠, Code S, Verifikation M)**
- Der Code ist trivial, aber ein Einheitenwechsel (l/h → l/min) löst bei bestehenden Statistiken einen HA-Statistik-Konflikt aus. Der Anwender muss die Statistik bereinigen. Vor dem 3.5-Release ist dafür der richtige Zeitpunkt, danach wäre es ein eigener Breaking Change.
- *Voraussetzung:* ein Rohwert-Dump plus Displaywert von mindestens zwei Anlagen (alte und neue Steuerung). Ändert die neue Steuerung die Bedeutung, braucht es zusätzlich ein Firmware-Gating (zwei Felder an Adresse 6, analog zu #112).

**F8 bis F13 (🟢 niedrig):** Kleine, lokale Änderungen ohne Datenrisiko.
- **F9 (Retry bei Timeout):** Laut Kommentar in `module_auto_detect.py` antworten manche Controller auf ein **fehlendes** Modul mit Schweigen. Jeder Retry verlängert dann das Setup pro fehlendem Modultyp um Timeout × Retries. Retries deshalb begrenzen (1×) und testen, dass das Setup bei schweigenden Controllern nicht spürbar langsamer wird. Dafür eignet sich `fail_read(..., ModbusTimeoutError)` in `conftest.py`: einmal Timeout, dann Antwort → Modul erkannt.
- **F8:** Achtung, `model.py` sagt ausdrücklich, dass bei Config-Parametern jede Zahl gültig sein kann. Daher lieber `entity_registry_enabled_default=False` als `nan=SENTINELS`.
- **F12:** `entity_registry_enabled_default` wirkt nur auf **neu** angelegte Entities. Upgrader behalten den bisherigen Zustand, es besteht also kein Risiko.

### Gesamtaufwand (grobe Schätzung)

| Paket | Fixes | Implementierung | Unit-Tests | HW-Verifikation |
|---|---|---|---|---|
| **A: vor dem Release zwingend** | ~~F1, F2~~ ✅, F3, F4, F14, F16, F20, F22 | ~0,5 Tag | ~1 Tag (inkl. Umschreiben von 3 bestehenden Tests) | 1 echter Upgrade 2.8.6 → 3.5 auf einer `low_first`-Anlage (~0,5 Tag) |
| **B: vor dem Release empfohlen** | F5, F7 | ~0,5–1 Tag (+ Klärung HA-Verhalten) | ~0,5 Tag | Upgrade-Test (mit Paket A kombinierbar) + Rohwert-Dumps von Testern |
| **C: abhängig von Externen** | F6 | ~1 h | ~1 h | Tester aus #100 (Termin unklar) |
| **D: nach dem Release möglich** | F8–F12, F15, F17, F21 (sobald HA 2026.11 erschienen ist) | ~0,5 Tag gesamt | ~0,5 Tag | F10: Langzeitbeobachtung |

**Kernaussage:** Die kritischsten Fixes (F1–F4) sind im Code klein. Ihr Risiko liegt im Release-Zeitpunkt: Sie wirken alle beim ersten Start nach dem Upgrade und sind danach nur mit einer zusätzlichen Migration bzw. manueller Statistikbereinigung zu korrigieren. Den größten Testaufwand machen nicht die Fixes selbst, sondern das Umschreiben der drei Tests, die das aktuelle (Fehl-)Verhalten festschreiben, und der eine echte Upgrade-Test, der F1, F3, F4 und F5 gemeinsam abdeckt.

## Empfohlene Reihenfolge

Da 3.5 noch nicht veröffentlicht ist, sollten alle Migrationskorrekturen (F1, F4, F5) **vor dem Release** in den bestehenden Migrationsschritt 9 einfließen. Danach bräuchte jede Korrektur eine eigene neue Migration. Die Pakete beziehen sich auf die Bewertung oben.

1. **Paket A, vor dem Release zwingend:** ~~F1 + F2 (#104/#90, Registerreihenfolge in Migration und Options-Flow)~~ ✅ erledigt (#133), F3 (#100/#108, `ambient_temperature`), F4 (#82, Firmware-Priorität), F14 (Bildpfade, vor dem Merge nach `main`), F16 (`entry` → `pos` in Schritt 9), F20 (Testumgebung HA 2026.10), F22 (hassfest auf `3.5`). Abschließend ein echter Upgrade-Test 2.8.6 → 3.5 auf einer `low_first`-Anlage.
2. **Paket B, vor dem Release empfohlen:** F5 (#122/#85, Climate-IDs; vorher das HA-Verhalten klären), F7 (`volume_flow_heat_sink`, nur nach Hardware-Verifikation). Beides sind Breaking Changes, die am besten mit dem ohnehin großen Versionssprung 3.5 kommen.
3. **Paket C, abhängig von Testern:** ~~F6 (`V1.0.4-3K`)~~ ✅ erledigt.
4. **Paket D, nach dem Release:** F21 (Climate `native_…`, sobald HA 2026.11 erschienen ist), F8–F12, F15 (PV 0 W bei ausgefallener Quelle; kann auch vorgezogen werden), F17 (#128 Abweichungssensor).
5. **Issues pflegen:** #121 und #112 schließen, #132 schließen (in #134 bestätigt), #94/#95 nach Rückmeldung schließen, #105 nach Retest schließen, #133 nach HW-Test des Melders schließen, #134 nach Antwort schließen, #120 nach F14 schließen, in #90 nach Firmware-Version/Rohwert fragen.
6. **Merge `3.5` → `main` vorbereiten:** F14 vorher erledigen; Konflikt in `hacs.json` zugunsten von `3.5` lösen.

---

## Änderungen am 17.10.2026

| Commit | Branch | Inhalt |
|---|---|---|
| `0ee31a8` | `3.5` | Fix #133: Migration pinnt die Registerreihenfolge nicht mehr; Options-Flow bietet den Firmware-Wert an (F1, F2) |
| `5f90f89`, `7a04c4e` | `3.5` | Changelog-Einträge, Version 3.5.7 (`manifest.json`) |
| `9d6c7f8` | `3.5` | V1.0.4-3K (`low_first`, Ordinal 9; V1.1.0-3K → 10) (F6); *Neu konfigurieren* entfernt die Registerreihenfolge bei Firmwarewechsel |
| `0ca36d5` | `3.5` | Changelog: Upgrade-Hinweis `hcX_flow_line_temperature_setpoint` (#134) |
| `fab707d` | `3.5` | Changelog: Statistik-Reparaturen der Volumenstrom-Sensoren korrigiert (#134) |
| `0bafd8b` / `641b702` | `3.5` / `main` | Doku Raumthermometer/Heizkurve korrigiert (#128), identisch in beiden Branches |
| `be4728b` / `5ad6cd0` | `3.5` / `main` | Änderungsdatum der beiden Doku-Seiten |
| `f3b16ba` | `3.5` | Bug-Analyse auf Stand 17.10.2026 |
| `cd549dc` | `3.5` | F14 Bildpfade, 10 tote Anker, Doku-Prüfer (`script/check_docs.py`, `.github/workflows/docs-check.yml`) |
| `3505b69` | `3.5` | Neue Seite „Firmware-Version ändern“, FAQ „Falsche / keine Sensorwerte“ überarbeitet |
| (dieser Commit) | `3.5` | Gesamte Doku auf 3.5 durchgesehen, Release-Seite 3.5, Platzhalter für veraltete Screenshots |


Unit-Tests: 156/156 bestanden (Python 3.14, `pytest-homeassistant-custom-component==0.13.355`).

---

## Nicht betrachtet (Label `enhancement`)

#128 Heizkurve: Abweichung zum realen Vorlaufsoll (inzwischen analysiert, siehe oben) · #119 Weniger Logging bei Sentinel-Werten · #113 Schreibbarer Kühl-Vorlaufsollwert · #83 Energiestatistik Wärmeverteilung · #79 Status-Entity PV-Überschuss-Modus · #77 Spreizung HP1 · #60 Abtauzähler 6h/12h · #59 Soll-Vorlauf bei PV-Überschuss erhöhen · #45 Wechselnde Strompreise · #37 State-Werte in Influx/Grafana
