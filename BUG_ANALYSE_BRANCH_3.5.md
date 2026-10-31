# Analyse der offenen Bug-Issues gegen Branch `3.5`

## Schließ-Kommentare zum Release V3.6.1 (gepostet 31.10.2026)

Release `V3.6.1` am 31.10.2026 veröffentlicht. Die Issues unten wurden mit diesen Kommentaren geschlossen. **Ausnahme: #137 ist auf GitHub noch offen** (Stand 31.10.2026, 19:40); der Kommentar ist dort noch nicht gepostet.

**Behoben in 3.x**

- **#82** (Falsche Firmware-Version übernommen)
  > Fixed in 3.6.1 (change in 3.6.0): when upgrading from 2.x, a firmware version you changed later in the options dialog now takes precedence over the one originally set up, and an unknown firmware name raises a repair instead of silently falling back to the oldest version. You can always correct the firmware under ⋮ → Reconfigure. Closing — thanks for reporting!

- **#85** (Entity mit falscher Domain)
  > Fixed since 3.5: entity IDs are now suggested with the platform's own domain, so the "wrong domain" warning is gone. Existing entries are already registered as `climate.*` by Home Assistant, so nothing needs to be renamed. Available in 3.6.1 via HACS. Closing — thanks!

- **#90** (Warmwasser thermisch = elektrisch, extreme Werte)
  > The root cause was a 32-bit register order that didn't match the controller. 3.6.1 handles this: the upgrade keeps your firmware's order (or the one set explicitly in `lambda_wp_config.yaml`), and if the counters only make sense the other way round, a repair "Check the 32-bit register order" tells you which setting to choose — no energy is booked from misread counters until then. Old statistics can be cleaned up as described in the FAQ. Closing — please reopen if you still see wrong values after updating.

- **#104** (Akkumulierte Energiezähler falsch / negativ)
  > Fixed in 3.6.1: misread energy counters (below zero or above 1 GWh, but plausible with swapped words) are now detected and raise the repair "Check the 32-bit register order" with the setting to choose. Until then the counters keep their last plausible value and no energy is booked, so the statistics stay clean. The FAQ now explains how to repair statistics recorded with the wrong order. Closing — thanks for the detailed data that made this possible!

- **#119** (Log-Flut durch Sonderwerte)
  > Since the 3.x rewrite, sentinel values are no longer logged at all — they simply show as `unknown`. The remaining warnings (e.g. a module not answering) are logged once, not on every poll. Available in 3.6.1 via HACS; 2.x won't get further changes. Closing — thanks for the suggestion!

- **#120** (PV-Überschuss: Screenshots fehlen)
  > The PV-surplus page has been reworked: screenshots are back, the Lambda settings (E-meter type, measuring point, Manual vs. Automatic) are explained, and since 3.6.0 the integration sends 0 W when the source sensor has no value, so the E-Manager no longer drops into error 6. Docs: https://guidojeuken-6512.github.io/lambda_heat_pumps/Anwender/pv_ueberschuss_steuerung/ — closing, thanks to everyone who contributed!

- **#121** (`async_get_device` deprecated)
  > Fixed since 3.5.4 (`async_get_device_by_identifier()` is used instead). With 3.6.1 this is now available via HACS; the warning only remains on 2.8.x. Closing — thanks!

**Kein Fehler der Integration**

- **#94** (Verlauf nach Update auf 2.6.0 weg)
  > We couldn't reproduce this with the rewritten 3.x integration, which keeps entity IDs and history across updates. 3.6.1 is now available via HACS. Closing — please reopen with details if it happens again.

- **#95** (Stützpunkte der Heizkurve statisch)
  > The support point entities aren't Modbus registers: the Lambda doesn't expose its panel values, so they are the integration's own settings for the heating-curve calculation in Home Assistant and need to be copied from the panel once (see https://guidojeuken-6512.github.io/lambda_heat_pumps/Anwender/heizkreis-steuerung/). That's intended. The odd values -300 and -3276.8 were controller sentinels and show as `unknown` since 3.5. Closing — thanks!

- **#132** (Room Temperature / Set Flow Temperature `unknown`)
  > This isn't a bug in the integration: these values are only filled while room thermostat control is active and a sensor is configured (see the "Raumthermometer" docs page). Since 3.6.0 such request registers are disabled by default on new installations. Closing — feel free to reopen if you have questions!

- **#137** (E-Manager-Sollleistung ≠ 0)
  > This is the Lambda's own behaviour, not the integration's: the integration only writes the surplus value you provide. The setpoint is calculated by the Lambda, and it only uses the surplus in "Automatic" mode. If the reported value includes the heat pump's own consumption, choose the matching measuring point. The PV-surplus page now explains this: https://guidojeuken-6512.github.io/lambda_heat_pumps/Anwender/pv_ueberschuss_steuerung/ — closing, please reopen if it persists with the documented settings.

- **Umsetzung:** Branch `3.6` (Version 3.6.0), siehe [Umsetzungsplan 3.5.x](#umsetzungsplan-35x-stand-29102026).
- **Stand:** 29.10.2026 (Erstanalyse 12.10.2026; HA-2026.10-Prüfung 19.10.2026; Tester-Rückmeldungen bis 21.10.2026; Issue-Aktivität 22.–29.10.2026 eingearbeitet, siehe [Nachtrag 29.10.2026](#nachtrag-29102026-issue-aktivität-seit-dem-22102026); Bewertung „betrifft 3.5.x“ und [Umsetzungsplan 3.5.x](#umsetzungsplan-35x-stand-29102026))
- **Nachtrag 31.10.2026:** `V3.6.1` ist veröffentlicht, `main` steht auf 3.6.1. Mit dem Release geschlossen: #82, #85, #90, #94, #95, #104, #119, #120, #121 (dazu #132, #122 als Duplikat von #85). #137 ist noch offen.
- **`main` (2.x) wird nicht mehr geändert** (Entscheidung 22.10.2026). Alle Fixes nur noch in `3.5`; `main` bekommt sie mit dem Merge.
- **Register ohne Werte nach Firmware:** eigene Auswertung in [`REGISTER_OHNE_WERTE.md`](REGISTER_OHNE_WERTE.md) (44 Issues, Tabelle Firmware → Register, F26–F29).
- **Geprüfter Code:** `origin/3.5` @ `be4728b` (Integration v3.5.7, noch ohne Tag); Erstanalyse gegen `55439d4` (v3.5.6)
- **Grundlage:** alle 24 offenen GitHub-Issues. Geprüft wurden die 9 mit Label `bug` und die 6 ohne Label, die einen Fehler beschreiben. Die 9 `enhancement`-Issues sind nur am Ende aufgelistet. **Stand 29.10.2026:** 28 offene Issues (11 `bug`, 7 ohne Label, 10 `enhancement`). Neu: #142, #143, #144. Geschlossen seit 22.10.: #100, #133, #136, #140 (Enhancement, „nicht geplant“), #141 (Duplikat von #121).
- **Code-Stand unverändert:** Seit `0938372` (22.10.2026) gibt es in `3.5` keine Code-Commits. Alle Aussagen zum Code gelten weiter für 3.5.7.
- **Tester-Hinweis (20.10.2026):** Die Testberichte von @Sturmi77 (#105, #120, #122/#85, #128, #133, #134, #136) stammen von einer Pumpe mit **Firmware V1.0.4-3K** (Display: Wärmepumpenmodul SW V1.0.4-3K, Build 29.06.2026). In der Integration war **V1.1.0-3K** eingestellt. Für 3.5.7 ist das gleichwertig: Beide haben Stufe ≥ 3 und `low_first`, die Integration legt dieselben Entitäten an (Firmware-Grenzen gibt es nur bei Stufe 1–2, 1–7 und ≥ 3, `sensor.py:177/307/308`). Unterschied ist nur die Modellanzeige am Gerät.
- **Hinweis:** Die Analyse selbst hat keinen Code geändert. Nachträglich umgesetzt (17.10.2026): F1, F2, F6 und das Zurücksetzen der Registerreihenfolge bei einem Firmwarewechsel (3.5.7), Doku-Korrekturen zu #128/#134. Details im Abschnitt [Änderungen am 17.10.2026](#änderungen-am-17102026). Zeilenangaben beziehen sich auf `custom_components/lambda_heat_pumps/` im Branch `3.5`.

Der Branch `3.5` ist ein Rewrite (PR #115: `modbus-connection`/`tmodbus` statt `pymodbus`, neue Entity-/Register-Modelle). Viele Issues, die gegen 2.x gemeldet wurden, betreffen Code, den es so nicht mehr gibt. Sie wurden deshalb gegen die neue Implementierung neu bewertet.

> **Release-Stand (geprüft):** Branch `3.5` ist **noch nicht veröffentlicht**. Letzter Tag bzw. Release ist `V2.8.6`, `main` steht auf 2.8.6, und es gibt keinen Tag auf einem 3.5-Commit. Für die Migrationsbefunde heißt das:
> - Es gibt **keine Endanwender-Installationen von 3.5** aus einem Release. **Ausnahme:** Tester, die 3.5.x direkt aus dem Branch installieren (z. B. der Melder von #133/#134/#128). Für sie gilt: Bereits migrierte Einträge werden von späteren Fixes im Migrationsschritt 9 nicht mehr erfasst und müssen von Hand korrigiert werden. Eine *zusätzliche* Migration (neue `ENTRY_VERSION`) oder Repair-Logik für „bereits auf 3.5 migrierte Einträge“ ist **nicht nötig**. Die eigenen Testinstallationen lassen sich von Hand korrigieren (Option neu setzen bzw. Eintrag neu anlegen).
> - Die Migration **2.x → 3.5** (`async_migrate_entry`, `ENTRY_VERSION = 9`) läuft dagegen beim ersten Start für **jeden** 2.8.x-Anwender. Fehler darin treffen alle Upgrader. Die Befunde zu #104/#90, #82 und #122/#85 bleiben deshalb relevant, werden aber **direkt im bestehenden Migrationsschritt 9** behoben, ohne neue Version.
> - **Nachtrag 29.10.2026:** Inzwischen nutzen mehrere Tester 3.5.x. Weiterhin keine neue `ENTRY_VERSION`, aber was auch Tester betrifft (F5, F16), wird bei jedem Start geprüft statt in Schritt 9 migriert; die F1-Altlast deckt F30 ab. Details im [Umsetzungsplan 3.5.x](#umsetzungsplan-35x-stand-29102026).

---

## Übersicht

| Issue | 3.5.x | Titel (gekürzt) | Status in 3.5 | Priorität |
|---|---|---|---|---|
| [#133](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/133) | ☑️ behoben in 3.5.7 (HW-Test offen) | Migration schreibt `high_first` über den Firmware-Default | ✅ **behoben** (F1 + F2, 17.10.2026), **geschlossen 27.10.**; HW-Test durch andere 2.8.x-Anwender offen | – |
| [#104](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/104) | ☑️ geschlossen (V3.6.1) | Akkumulierte Energiezähler falsch / negativ | ✅ **geschlossen 31.10.** mit V3.6.1: F1 + F2, Repair „Registerreihenfolge prüfen“ (F30), FAQ Statistik (F31) | – |
| [#90](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/90) | ☑️ geschlossen (V3.6.1) | Warmwasser thermisch = elektrisch, extreme Werte | ✅ **geschlossen 31.10.** mit V3.6.1 (gleiche Ursache wie #104, F30) | – |
| [#82](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/82) | ☑️ geschlossen (V3.6.1) | Falsche Firmware-Version übernommen | ✅ **geschlossen 31.10.** mit V3.6.1 (F4: Options vor Data, Repair bei unbekanntem Namen) | – |
| [#100](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/100) | 🔷 **ja** (F26–F28) | Neue Steuerung FW 1.3.8 / 1.3.10 | **geschlossen 27.10.**, Befunde offen; V1.0.4-3K ✅ in 3.5.7; V1.0.2-3K (F26), neu gemeldet **V1.0.7-3K** (24.10., Frage unbeantwortet) → F26 erweitert; F27/F28 offen | mittel |
| [#144](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/144) | ☑️ beantwortet (30.10.2026) | Neue Steuerung SW V1.4.1 (WP-FW **V1.0.8-3K**), 2.8.6 | ✅ **beantwortet 30.10.**: Doku-Seite "Heizkreis Steuerung" erstellt; erklärt, dass alle Werte außer Vorlauf Offset von Hand vom Lambda-Display übernommen werden; F26 (Firmware-Updates) ist separate Aufgabe | niedrig |
| [#143](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/143) | 🔷 **ja** (gemeldet auf 3.5.6; F27, F12) | Viele Entitäten (v. a. Puffer) ohne Messwert, 3.5.6 | 🟡 **neu 28.10.**: EU13, V1.0.4-3K (Option V1.1.0-3K); passt zu `REGISTER_OHNE_WERTE.md` (3005–3009 = „keine Anforderung“); Screenshot auswerten, Rückfragen | niedrig–mittel |
| [#142](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/142) | ❔ prüfen (gleiche Logik in 3.5; F32) | Raumtemperatur wird nicht nach 5004/5104 geschrieben, 2.8.6 | 🟡 **neu 28.10.**: Register lesen 62536 = −3000 (nichts geschrieben); Code schreibt nur mit Option „Raumthermostat-Steuerung“; Log fehlt | niedrig–mittel |
| [#122](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/122) | ☑️ geschlossen (Duplikat) | Entity-ID mit falscher Domain (`sensor.*_heating_circuit`) | ✅ **geschlossen** (Duplikat von #85) | mittel (Frist HA 2027.5) |
| [#85](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/85) | ☑️ geschlossen (V3.6.1) | Entity-ID mit falscher Domain (`sensor.*_boil1_hot_water`) | ✅ **behoben** ab 3.5, **geschlossen 31.10.** mit V3.6.1; F5 entfällt (HA führt die Einträge bereits als `climate.*`, siehe Umsetzungsplan Schritt 2) | – |
| [#105](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/105) | 🔷 **ja** (Retest „Automatik“; F15, F10) | E-Manager-Register springt auf 0 | 🟢 auf 3.5.6 **nicht reproduzierbar** (Retest 18.10., Modus „Manuell“); Modus „Automatik“ ungetestet | niedrig |
| [#101](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/101) | 🔷 **ja** (F9) | Solarthermiemodul wird nicht erkannt | 🟡 unklar, Logs fehlen; Schwachstelle in der Modulerkennung | niedrig |
| [#94](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/94) | – nein | Verlauf nach Update auf 2.6.0 weg | ✅ **geschlossen 31.10.** (in 3.x nicht reproduzierbar) | – |
| [#95](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/95) | – nein | Heizkurven-Stützpunkte zeigen statische Werte | ✅ **geschlossen 31.10.** (kein Code-Bug, so gewollt; Sentinel-Werte seit 3.5 `unknown`) | – |
| [#132](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/132) | ☑️ geschlossen | Room Temperature / Set Flow Temperature `unknown` | ✅ **geschlossen 31.10.** (kein Code-Bug, nur UX/Konfiguration — Raumthermostat muß aktiviert sein, Sensor muß konfiguriert sein) | niedrig |
| [#120](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/120) | ☑️ geschlossen (V3.6.1) | Screenshots PV-Überschuss fehlen (toter Link) | ✅ **geschlossen 31.10.**: Doku-Seite überarbeitet (F14, F24), 0 W bei fehlendem Quellwert (F15) | – |
| [#119](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/119) | – nein (behoben seit 3.5.0, Rewrite) | Sonderwerte fluten das Log (2.8.x) | ✅ **geschlossen 31.10.**: Sonderwerte werden still `unknown`, restliche Warnungen nur einmal; Entitäten → F27/F28 | – |
| [#134](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/134) | 🔷 **ja** (Doku F25) | Upgrade-Hinweise 2.8.6 → 3.5.6 (Setpoint-Entity, Statistik-Reparaturen) | ✅ **Changelog ergänzt/korrigiert** (17.10.2026), Issue geschlossen; Rückfrage zu V1.0.4-3K vs. V1.1.0-3K offen (F25) | – |
| [#128](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/128) | 🔷 Enhancement (F17) | Heizkurve: Abweichung zum Pumpen-Sollwert (Enhancement) | 🟡 Doku korrigiert (beide Branches), Abweichungssensor offen (F17); Tester bestätigt Nutzen mit Live-Daten | niedrig |
| [#136](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/136) | – nein (nicht geplant) | Setzen der Betriebsart (Heizkreis) wird zurückgesetzt | ⛔ **wird nicht umgesetzt** (22.10.2026), **geschlossen 22.10.** als „nicht geplant“ (F23) | – |
| [#137](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/137) | – nein (Verhalten der Lambda; Doku F24) | E-Manager-Sollleistung ≠ 0 ohne PV-Überschuss (2.8.6) | 🟢 Verhalten der Lambda, Doku F24 erledigt; Schließ-Kommentar entworfen, **auf GitHub noch offen** (31.10.) | niedrig |
| [#121](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/121) | ☑️ geschlossen | `device_registry.async_get_device` deprecated | ✅ **geschlossen 31.10.** (behoben in 3.5.4, mit V3.6.1 über HACS; Duplikat #141) | – |
| [#112](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/112) | – nein (behoben in 3.5.5) | Register 5007 doppelt adressiert | ✅ **behoben** in 3.5.5 | – |

Spalte 3.5.x: 🔷 betrifft 3.5.x, Arbeit offen · ☑️ betraf 3.5.x, behoben · ❔ noch unklar · ◽ nur optionale UX · – betrifft 3.5.x nicht (nur 2.x oder kein Code-Fehler). Reihenfolge der Umsetzung: [Umsetzungsplan 3.5.x](#umsetzungsplan-35x-stand-29102026).

Legende Status: 🔴 Fehler im 3.5-Code nachgewiesen · 🟠 Teilaspekte offen · 🟡 unklar bzw. Restarbeit · 🟢 kein Code-Fehler in 3.5 · ✅ behoben (Issue kann geschlossen werden)

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
> - **Rückmeldung des Melders (20.10.2026):** Er kann 3.5.7 **nicht verifizieren**: Sein Eintrag wurde am 03.10. migriert und hat `low_first` von Hand gesetzt, eine zweite Installation gibt es nicht. Er bestätigt die Zahlen aus 3.5.6 (Zähler rund eine Minute bei 1.140.719.617 / 1.989.148.679 Wh; nach `low_first` exakt wieder 82.942 / 489.104 Wh, die eigenen Gesamtzähler der Integration waren nicht betroffen). Verifikation braucht einen 2.8.x-Eintrag (Version 8) ohne gespeicherte Reihenfolge, `low_first`-Firmware, leere/fehlende YAML → Update auf 3.5.7 → Options ohne `int32_register_order`, Zähler unverändert, `recorder/validate_statistics` ohne neue Befunde. Er bittet, beim Schließen den Hinweis zum Nachstellen von Hand zu behalten, und bietet Tests auf seinem migrierten Eintrag an (Options-Default, Firmwarewechsel über *Neu konfigurieren*).
> - Wer 3.5 vor diesem Fix schon installiert hat, hat `high_first` fest in den Options stehen. Das korrigiert sich nicht von selbst: im Options-Dialog einmal die richtige Reihenfolge wählen.
> - **#133 geschlossen (27.10.2026).** Der HW-Test mit einem frischen 2.8.x-Eintrag steht weiter aus.

> **Neuer Befund (22.–23.10.2026, @Eisbaer2, 2.8.6): V0.0.10-3K mit `high_first`.**
> - Display zeigt **V0.0.10-3K** (seit Langem, kein Update). In der Integration war **V1.1.0-3K** eingestellt; der Melder sagt, er habe das nicht selbst geändert. Fehler seit ca. 13.10.2026: `compressor_thermal_energy_output_accumulated` = −2147023552 (`0x80070540`), Strom z. B. 1146028282 (`0x444F00FA`).
> - Mit getauschten 16-Bit-Wörtern ergeben sich plausible Zähler: Wärme 88.113.159 Wh, Strom 16.401.487 → 16.401.491 → 16.401.496 Wh (+4/+5 Wh je Abfrage), JAZ ≈ 5,4. Die von Gemini vorgeschlagene float32-Deutung ist falsch (falsche Hex-Umrechnung, +16 kWh in 30 s; die Lambda kennt nur INT16/INT32). Antwort im Issue am 23.10.
> - Umstellen auf V0.0.10-3K half nicht, weil V0.0.10-3K und V1.1.0-3K beide `low_first` haben. **Mit `int32_register_order: "high_first"` in `lambda_wp_config.yaml` stimmen die Werte (bestätigt 23.10.).**
> - **Folge:** Zusammen mit #90 (V0.0.9-3K liefert `low_first`-Daten) ist das der zweite Fall, in dem die Firmware-Nummer nicht zur Wortreihenfolge passt. In 3.5 trifft das jeden, dessen Anlage von `FIRMWARE_CONFIG` abweicht: Nach dem Upgrade gilt der Firmware-Default, falls die YAML keinen expliziten Wert hat. → **F30** (Plausibilitätsprüfung bzw. Erkennung der Wortreihenfolge), F11 wird damit wichtiger.
> - **Offen:** Warum stand V1.1.0-3K in den Options? Möglich ist ein früherer Options-Dialog mit Vorauswahl der neuesten Firmware in 2.x. Nicht geklärt; für 3.5 irrelevant, weil 3.5 den Namen direkt speichert (siehe #82).
> - **Offen (Doku):** Der Melder fragt, wie er 10 Tage falsche Statistik reparieren kann. Das ist Punkt 6 unten (FAQ zur Statistikbereinigung), weiter offen.

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
>
> **Nachtrag 29.10.2026:** Der umgekehrte Fall ist jetzt belegt: eine Anlage mit V0.0.10-3K (Tabelle `low_first`) liefert `high_first` (#104, @Eisbaer2, bestätigt). Die Reihenfolge hängt also nicht verlässlich an der Firmware-Nummer. Siehe F30.

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

## 🟠 #100: Neue Steuerung (SW 1.3.8 / 1.3.10, FW V1.0.2-3K / V1.0.4-3K)

Ein Sammel-Thread mit mehreren Befunden von @madmaxx425. Einiges ist umgesetzt, Stand in 3.5:

| Befund | Status in 3.5 |
|---|---|
| 1: Energie-Delta wird gekappt statt verworfen | ✅ behoben (`_energy_delta` verwirft) |
| 2: Sentinel-Werte 0x8000 / -3000 / 0xFFFF | ✅ für `gauge`/`enum` behoben (`lambda_modbus/model.py`: `SENTINELS`, opt-in `NO_REQUEST`) |
| 3: Register 1024–1060 auf der neuen Steuerung nicht belegt | 🟠 teilweise: Gauges zeigen `unknown`, die **`integer`-Felder `config_parameter_24/33/50/60` zeigen weiterhin 32768** (`heat_pump.py`, `sensor.py:223/232/238/248`); sie haben weder Sentinel noch Firmware-Range. **21.10.: an zweiter Anlage bestätigt**, 1024–1033 und 1051–1060 gesichert ohne Wert ab V1.0.x → F27 (Ausschluss per Firmware), F28 (Sentinel für `integer`) |
| 4a: `ambient_temperature` | 🔴 **Regression**, siehe unten |
| 4b: `volume_flow_heat_sink` Einheit/Skalierung | ✅ **geklärt 21.10.: `l/h`, Skala 1 ist richtig.** Rohwert 1047 bei 6,1 kW und 5,1 K Spreizung ergibt per Wärmebilanz ~1.030 l/h; der Vorschlag `l/min`/0.01 (= 628 l/h) passt nicht. Keine Änderung (F7 entfällt) |
| Firmware „V1.0.4-3K“ in die Auswahl aufnehmen (zugesagt am 04.08.) | ✅ **FIXED** 17.10.2026: in `FIRMWARE_CONFIG` mit Ordinal 9 und `low_first` (Rohdump von @madmaxx425); `V1.1.0-3K` rückt auf 10 |
| Firmware „V1.0.2-3K“ (neu 21.10., @BMeyendriesch) | 🟠 offen → **F26**: fehlt in `FIRMWARE_CONFIG`; `low_first` durch Zähler belegt (1020–1023 = `17563 0 32623 1` → 17,6 / 98,2 kWh) |

**Stand 29.10.2026:** Issue am 27.10. geschlossen (Antwort: bei plausiblen Energiewerten nichts ändern, sonst FAQ; nach Steuerungstausch Einstellungen prüfen). Danach noch:
- @web2date (24.10.): neue Steuerung seit 12.10., WP-Software **V1.0.7-3K**, Frage „welche Version wählen?“ ist **unbeantwortet**. Antwort aus dem Code: in 3.5.7 V1.0.4-3K oder V1.1.0-3K wählen (gleiche Entitäten, beide `low_first`); in 2.8.6 V1.1.0-3K.
- @AndiBo62 (23.10.) hat die neue Steuerung bekommen, Befunde in #144 (WP-FW **V1.0.8-3K**).
- @doerr-sebastian (27.10.) fragt nach dem Grund für den Steuerungstausch; keine Auswirkung auf die Integration.
- Bekannte Firmware-Namen der neuen Steuerung damit: V1.0.2, V1.0.4, V1.0.7, V1.0.8 (jeweils -3K). In `FIRMWARE_CONFIG` steht nur V1.0.4-3K. → F26 erweitert.

**Neuer Datenpunkt (21.10.2026, @BMeyendriesch):** EU15L, in Betrieb seit 20.10.2026, SW V1.3.10 (29.06.2026), **WP-Firmware V1.0.2-3K**, Integration 2.8.6 mit Option V1.1.0-3K. Vollständiger FC03-Dump im Heizbetrieb mit laufendem Kompressor:
- 1024–1043 und 1051–1063: alle 32768. Das Display zeigt Heißgas, Kondensation, Sauggas, Verdampfung, Unterkühlung, Expansionsventil und EqM **mit Werten**; die Steuerung gibt sie nur nicht über Modbus aus. Anfrage beim Lambda-Support läuft.
- 1008 (EQ-Austritt) und 1015–1018: 32768; 0002: −3000; 5003–5005: −3000; 3005–3009 und 5006: −1; 1050: 0.
- Gültig: 1000–1007, 1009–1014 (COP 5,90), 1019–1023, 0003/0004, 5007 = 39,6 °C.
- In 2.8.6 ist 5007 doppelt angelegt (#112): `hc1_flow_line_temperature_setpoint` bekommt den Wert, `hc1_target_temp_flow_line` bleibt `unknown`. In 3.5.5 behoben; beim Upgrade gilt der Hinweis aus #134.
- Vollständige Auswertung aller Dumps: [`REGISTER_OHNE_WERTE.md`](REGISTER_OHNE_WERTE.md).

**Regression von #108 (geschlossen):** In `main`/2.8.x wurde `ambient_temperature` auf Wunsch von #108 auf `firmware_versions: ["1-9"]` erweitert, weil Register 2 auch auf V1.1.0-3K gültige Werte liefert und ungültige Werte über `sentinel_values` abgefangen werden. In 3.5 steht wieder `firmware_versions=("1-7",)` (`sensor.py:177`). Auf **V0.0.10-3K und V1.1.0-3K wird die Entity also gar nicht mehr angelegt**, obwohl `general.py` den 0xFFFF-Sentinel für dieses Feld bereits abfängt.

**Lösungsansatz:**
1. ~~`sensor.py:177`: Die Firmware-Range entfernen (oder `("1-9",)` setzen). Die Sentinel-Filterung in `Ambient.temperature` reicht aus. Dazu einen Regressionstest für #108 schreiben.~~ **Zurückgestellt (22.10.2026):** Register 0002 ist laut Lambda-Protokoll ein Schreibregister für einen extern eingespeisten Außenwert. Auf V1.0.4-3K liefert es ohne Einspeisung −3000 (#100) **oder den Rohwert −300** (#107, = −30,0 °C, kein Sonderwert). Der einzige gültige Wert in #108 kam von einer externen Einspeisung, die Firmware-Angabe dort wurde zurückgezogen. Ohne Firmware-Range würde 3.5 auf solchen Anlagen −30,0 °C anzeigen. Siehe F3.
2. ✅ **Erledigt (3.5.7).** ~~`"V1.0.4-3K"` in `FIRMWARE_CONFIG` aufnehmen.~~ Ordinal und `reg_order` vorher mit den Testern aus #100 klären (@b-bremer, @7xy, @madmaxx425). Laut Thread sind die Register identisch mit Protokoll 1.0, die Reihenfolge ist vermutlich `low_first`. Achtung: Ordinals sind Vergleichswerte für `firmware_version`. Eine neue Version zwischen den bestehenden erfordert entweder eine Neunummerierung (und eine Prüfung aller `firmware_version`/`firmware_versions`-Angaben) oder ein Ordinal ≥ 10.
3. `config_parameter_*` (die `integer`-Felder im Bereich 1024–1060): entweder `nan=SENTINELS` am Feld setzen oder sie per `firmware_versions` auf die alten Steuerungen begrenzen. Die Alternative: Default-mäßig deaktivieren (`entity_registry_enabled_default=False`), weil sie undokumentiert sind. → Jetzt **F27** (Ausschluss ab V1.0.x für 1024–1033 und 1051–1060) und **F28** (Sentinel für `integer`-Felder).
4. ✅ **Geklärt 21.10.2026, keine Änderung:** `l/h`, Skala 1 stimmt (Wärmebilanz, siehe oben). ~~`volume_flow_heat_sink`: Mit Lambda-Protokoll 1.0 und einem Rohwert-Dump verifizieren.~~ Ist die Korrektur bestätigt, `gauge(6, 0.01, unit="l/min")` verwenden und die Sensoreinheit anpassen. **Achtung:** Schon der Wechsel 2.x → 3.5 erzeugt für diesen Sensor die Reparaturen „Einheit geändert“ (`l/h` → `L/h`) und „Mittelwert-Typ geändert“ (`total` → `measurement`, nur durch Löschen der Statistik behebbar, siehe #134). Ein weiterer Einheitenwechsel sollte deshalb **im selben Release** kommen, damit Anwender die Statistik nur einmal löschen müssen.
5. In der Doku (initiale Konfiguration) klarstellen, welche Versionsanzeige gemeint ist (Statuszeile der WP-Seite, nicht SW-Version). Laut Thread ist die Doku mit GIF bereits online, also nur prüfen.

---

## 🟡 #122 und #85: Entity-ID mit falscher Domain (`sensor.*` statt `climate.*`)

**Meldung:** HA warnt „sets an entity ID with wrong domain: `sensor.eu13l_hc1_heating_circuit`“ bzw. `sensor.eu13l_boil1_hot_water`. Ab HA 2027.5 funktioniert das nicht mehr.

**Prüfung in 3.5:**
- Im Code behoben: `entity.py:84-86` schlägt die Entity-ID aus `_entity_domain` vor, und `climate.py:105` setzt `_entity_domain = "climate"`. `number.py` und `sensor.py` setzen ebenfalls ihre eigene Domain. Neue Installationen erzeugen also `climate.<prefix>_hc1_heating_circuit` bzw. `climate.<prefix>_boil1_hot_water`.
- **Offen (Upgrade-Pfad 2.x → 3.5):** Geprüft in `main`: 2.x setzt in `climate.py` `self.entity_id = names["entity_id"]` aus `generate_sensor_names()`. Die Climate-Entities wurden also tatsächlich mit `sensor.*`-ID registriert. Installationen, die von 2.x upgraden, behalten diese ID in der Entity-Registry, denn die Registry-ID hat Vorrang vor dem Vorschlag. Ob HA bei solchen Registry-Einträgen ab 2027.5 ebenfalls warnt bzw. sie ablehnt, sollte mit einem Test gegen eine aktuelle HA-Version geprüft werden. Sicher ist: Die IDs bleiben inkonsistent.

**Lösungsansatz:**
1. ~~Im bestehenden Migrationsschritt 9~~ **Geändert 29.10.2026:** bei jedem Start in `async_setup_entry`, damit auch Tester mit schon migriertem Eintrag erfasst werden (siehe Umsetzungsplan, Schritt 2). Die Entity-Registry durchgehen: `er.async_entries_for_config_entry(registry, entry.entry_id)`. Jeden Eintrag mit `entry.domain == "climate"`, dessen `entity_id` nicht mit `climate.` beginnt, über `registry.async_update_entity(entity_id, new_entity_id=f"climate.{object_id}")` umbenennen. Vorher auf Kollisionen prüfen (`registry.async_get(new_id)`).
2. Den Anwender im Changelog darauf hinweisen, dass Automationen/Dashboards mit `sensor.*_heating_circuit` bzw. `sensor.*_hot_water` angepasst werden müssen.
3. Test: Ein Registry-Eintrag `sensor.x_boil1_hot_water` auf Plattform `climate` wird nach dem Setup zu `climate.x_boil1_hot_water`.
4. #85 als Duplikat von #122 schließen (oder umgekehrt).

**Datenpunkt (20.10.2026, @Sturmi77):** Upgrade 2.8.6 → 3.5.6, ein HP/Boiler/HC, Raumthermostat aus. Die Warmwasser-Entität war schon unter 2.8.6 `climate.*` (von Hand umbenannt) und blieb es; kein `sensor.*_boil1_hot_water` und kein `*_hc1_heating_circuit` in der Registry (die Heizkreis-Klima-Entität gibt es in 3.5 nur mit Raumthermostat). Das Problem ist also nicht bei jedem 2.x-Upgrade vorhanden, sondern nur bei Registry-Einträgen, die 2.x tatsächlich mit `sensor.*` angelegt hat. Seine Vermutung (alte `sensor.*`-Einträge löschen und neu laden) ist ungetestet; F5 bleibt der saubere Weg.

---

## 🟢 #105: E-Manager-Register (PV-Überschuss) springt zwischendurch auf 0

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

**Retest 3.5.6 (@Sturmi77, 18.10.2026, Kommentar 20.10.):** EU10L, `pos`, E-Manager „Modbus Client“ / „E-Überschuss“ / **Manuell**, Quelle ist ein Template-Sensor (0 W bei veralteter Quelle). Gesendeten Wert und `emgr_actual_power` 12:00–17:30 in 10-s-Schritten verglichen:
- **Keine falschen Nullen:** 17 Nullen an der Pumpe, jede davon stand innerhalb der vorherigen 40 s schon in der Quelle (9 s Schreiben + 30 s Rücklesen).
- **Werte kommen 1:1 an:** 78 Fünf-Minuten-Slots > 50 W, Mittel 1.360 W gesendet / 1.358 W gelesen, Spitze 5.664 / 5.648 W, keine Abweichung > 150 W.
- **Kein Fehler**, außer einmal 31 s Fehler 6 während eines HA-Neustarts (dabei wird nichts geschrieben, vgl. F15).
- **Nicht abgedeckt:** Modus „Automatik“ (Psoll, Register 104, und die 15-min-Startverzögerung). Der Tester will das nachreichen.

→ Für 3.5 nicht reproduzierbar. Schließen, sobald der Automatik-Test vorliegt oder die ursprünglichen Melder nichts mehr berichten.

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

## 🟡 #120: Screenshots zur PV-Überschuss-Konfiguration fehlen

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
- Bild 2 zeigt die Energie-Management-Seite der Lambda mit Betriebsart „Automatik“, aber nicht die nötigen E-Manager-Einstellungen. Ein Tester (Kommentar im Issue, EU10L, Firmware V1.0.4-3K, 3.5.6) betreibt es mit E-Meter-Typ „Modbus Client“, Messpunkt „E-Überschuss“, Betriebsart „manuell“; er bietet diesen Text als Ersatz an.
- **Nachtrag 18.10.2026 (Tester, sonniger Tag):** Der Wert kommt an (`emgr_actual_power` bis 5.648 W, kein Fehler). **Im Modus „Manuell“ nutzt die Pumpe ihn aber nicht:** `emgr_actual_power_consumption` und `emgr_power_consumption_setpoint` (Psoll, Register 104) bleiben 0; ein WW-Zyklus bei 3,3 kW Überschuss lief mit den üblichen ~0,9 kW, ein Heizlauf auf Mindestleistung mit normalem Kurvensollwert. Das openHAB-Binding dokumentiert die Leistungsaufnahme als nur in „Automatik“ gültig, und Bild 2 zeigt Psoll ebenfalls in „Automatik“. → Die Doku-Zeile „Betriebsart: z. B. Manuell oder Automatik“ (`pv_ueberschuss_steuerung.md`) ist irreführend, siehe **F24**. Laut Handbuch kann die Pumpe in „Automatik“ zusätzlich die Temperaturen anheben („PV Betrieb – Temperaturerhöhung“ für Heizkreis, Puffer, Warmwasser); ein Forenbericht (simon42) nennt Anhebungen sogar bei auf 0 gestellten Parametern. Automatik-Test des Testers steht aus.
- Code-Beobachtung desselben Testers: siehe F15 (kein Weiterschreiben bei ausgefallener Quelle → E-Manager-Fehler 6).

**Lösungsansatz:**
1. ✅ **F14 in `3.5` erledigt (17.10.2026):** alle 21 Pfade in 14 Dateien auf `../assets/`, dazu 10 tote Anker korrigiert. Build ohne Hinweise, Prüfer: 0 Probleme; Merge-Probe `3.5` → `main`: 0 Probleme. In `main` (live) ist die PV-Seite weiterhin kaputt, bis dort dieselbe Zeile geändert wird oder 3.5 gemergt ist. ~~Alle betroffenen Pfade auf `../assets/` setzen, **in beiden Branches identisch** (in `main` nur die PV-Seite, in `3.5` alle 16 Seiten). Dann bleibt der Merge konfliktfrei und das Ergebnis korrekt. Nachweis: Build + Pfadprüfung → 0 kaputte Bilder.~~
2. ✅ PV-Seite in `3.5` neu geschrieben (Einstellungen nach Vorschlag des Testers, Bild 1 durch Platzhalter ersetzt); vom Tester als passend bestätigt (18.10.). Screenshot aus 3.5 muss noch der Maintainer liefern.
3. F24: Betriebsart in der Doku präzisieren (Psoll nur in „Automatik“, mögliche Temperaturanhebung).
4. Danach Issue schließen.

---

## ✅ #134: Upgrade-Hinweise 2.8.6 → 3.5.6

**Meldung:** (1) `hc1_flow_line_temperature_setpoint` verschwindet auf Firmware 3+ und verwaist. (2) Nach dem Upgrade 11 Statistik-Reparaturen, keine davon über die Oberfläche behebbar.

**Prüfung:**
- (1) Gewollt, Fix für #112 (3.5.5): `flow_line_temperature_setpoint` nur noch für Firmware-Stufe 1–2 (`sensor.py:307`), ab Stufe 3 (V0.0.5-3K) ersetzt durch `target_temp_flow_line`. Keine Registry-Migration (andere `unique_id`, andere Bedeutung).
- (2) Die Volumenstrom-Sensoren waren in 2.8.6 `state_class: total` mit `l/h`/`l/min`, in 3.5 `measurement` mit `L/h`/`L/min`. Pro Sensor erscheinen „Einheit geändert“ **und** „Mittelwert-Typ geändert“. Laut HA-Frontend (`fix_issue.mean_type_changed`) lässt sich der Mittelwert-Typ **nur durch Löschen der Statistik** beheben; bis dahin keine neue Langzeitstatistik. Die Option „Einheit … aktualisieren, ohne Konvertierung“ allein reicht nicht. Der Changelog vom 15.10. hatte das falsch („Historie bleibt erhalten“).

**Erledigt (17.10.2026):**
- Changelog (beide Dateien, EN/DE): Upgrade-Hinweis zu `hcX_flow_line_temperature_setpoint` → `hcX_target_temp_flow_line` inkl. Vorgehen zum Erhalt der Statistik (verwaiste Entity löschen, neue auf alte entity_id umbenennen).
- Changelog: Statistik-Reparaturen mit HA-Wortlaut der Optionen; Empfehlung auf „Alle alten Statistikdaten für diese Entität löschen“ korrigiert; Einleitung „es geht nichts verloren“ eingeschränkt.

**Stand 20.10.2026:** Beantwortet und geschlossen; der Melder bestätigt den Reparaturdialog („exactly as described“).

**Nachtrag des Melders (20.10.2026):** Seine Pumpe läuft mit **V1.0.4-3K**, in der Integration war V1.1.0-3K gewählt. Seine Aussagen zur Entitätenmenge beziehen sich auf die Option V1.1.0-3K. **Frage:** Legt 3.5.7 für V1.0.4-3K dieselben Entitäten an? Falls nicht, wünscht er einen Satz in den Upgrade-Notes für alle, die versehentlich V1.1.0-3K gewählt haben.
- **Antwort aus dem Code:** Ja, identisch. V1.0.4-3K (Stufe 9) und V1.1.0-3K (Stufe 10) liegen auf derselben Seite aller Firmware-Grenzen (`"1-2"`, `"1-7"`, `≥ 3`), beide sind `low_first`. Ein Wechsel über *Neu konfigurieren* ändert nur die Modellanzeige am Gerät; eine gesetzte Registerreihenfolge wird dabei entfernt, die Firmware-Reihenfolge ist aber dieselbe. → **F25:** Im Issue antworten; optional ein Satz in Changelog/`firmware-wechsel.md`.

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

**Live-Daten des Melders (17.10.2026, Firmware V1.0.4-3K, 3.5.6):**
- `hc1_target_temp_flow_line` trägt im Zustand HEATING den echten Sollwert der Kurve (33,2 °C bei 13,7 °C berechneter Außentemperatur = Display = interpolierte Kurve; am 17.10. 29,0 °C vs. interpoliert 29,05 °C bei Kurve 55 / 37,5 / 22 °C). Der Template-Helfer „Sollwert − `heating_curve_flow_line_temperature_calc`“ bleibt innerhalb der Display-Rundung. → Die offene Frage zu F17 („enthält `target_temp_flow_line` den Offset 5X50?“) ist damit für Offset 0 beantwortet; mit Offset ≠ 0 weiter ungeprüft.
- Display-Änderungen an der Kurve werden nie zurückgelesen; sein Alarm (Abweichung > ~1 K über 2 h) hat genau das erkannt. Der Abweichungssensor (F17) ist damit auch ohne Kurvenschätzung nützlich.
- Für eine spätere Kurvenschätzung: Paare (Außentemperatur, Sollwert) eignen sich, der gemessene Vorlauf nicht (bei Dauerlauf bis 2,5 K unter Soll, im Takten 0–0,9 K; Abschaltung ca. +1,0 bis +1,7 K über Soll).
- **Weiter gewünscht:** die Grenze **7–65 °C** von 5X05 dokumentieren und die Kurvenwerte darauf begrenzen. Da 3.5 5X05 nie schreibt, ist das nur eine Bereichs- und Doku-Frage (Punkt 2 oben: Bereich der Stützpunkte, heute 15–75 °C, auf 7–65 °C setzen).

---

## ⛔ #136 (und #125): Setzen der Heizkreis-Betriebsart wird zurückgesetzt

> **Entscheidung 22.10.2026: wird nicht umgesetzt (F23).** Gründe:
> 1. Kein Eingriff in die Regelung der Lambda, erst recht nicht gegen ihren Wärmefahrplan. Dauerhaftes Neuschreiben alle paar Minuten würde die eigene Einstellung der Lambda laufend übersteuern, ohne dass es am Display sichtbar ist.
> 2. Das Register gibt nicht zurück, was gesetzt wurde (nach dem Timeout „keine Anforderung“, Rücklesen firmwareabhängig, #31). Eine Entität würde etwas anderes zeigen als die Lambda tut; erwartbar sind viele neue Issues.
> 3. Nicht resilient: Die Integration kann nicht prüfen, ob die Anforderung angekommen ist und noch gilt. Bei Neustart, Verbindungsabbruch oder Update fällt die Lambda still zurück. Ob ein Wechsel bei laufendem Verdichter zulässig ist, ist nicht dokumentiert.
>
> Wer es trotzdem will: `lambda_heat_pumps.write_modbus_register` in einer eigenen Automation, auf eigene Verantwortung. Issue mit „not planned“ schließen.

**Meldung (@AndiBo62, 19.10.2026):** Das Setzen der Betriebsart funktioniert, wird aber zurückgesetzt; das Dropdown an der Steuerung zieht nicht mit. Er gleicht das per Automation aus.

**Messung (@Sturmi77, 20.10.2026, Firmware V1.0.4-3K, 3.5.6, Register 5006 über `write_modbus_register`/`read_modbus_register`, Pumpe jeweils in Taktpause):**
1. Vor jedem Schreiben liest 5006 `65535` (keine Anfrage), Modus-Sensor `unknown`.
2. Schreiben von **2** (wie Display): zurückgelesen 2, Sensor `AUTOMATIK`; nach **~5 min** wieder 65535.
3. Schreiben von **6** (Sommer): binnen ~10 s `hc1` `CH-SUMMER`, `hp1` `SUMMER`, Soll-Vorlauf 0,0 °C; nach ~5 min von selbst zurück (`HEATING`, 28,7 °C).
4. **6 alle 3 min neu schreiben** (5×): Sommer hält 15 min ohne Rückfall; danach 2 → sofort `HEATING`, Kompressor startet.
- Nichts wird in der Steuerung gespeichert, keine Fehler. In #125 wurde der Rückfall nach ~15 min berichtet, hier ~5 min (evtl. firmwareabhängig). Rücklesen ist hier möglich, in #31 immer −1 (firmwareabhängig).
- Passt zum Lambda-Protokolltext aus #113: Anfrageregister 00–49 müssen erneuert werden (Timeout 5 min).

**Prüfung in 3.5:** `lambda_modbus/heating_circuit.py:27` modelliert `operating_mode` (5X06) bereits als `enum(..., writable=True, force_fc16=True, nan=SENTINELS + (NO_REQUEST,))`. Eine Entität zum Setzen gibt es nicht (Plattformen: climate, number, sensor); nur der Lesesensor.

**Ehemaliger Lösungsansatz (F23, verworfen):**
1. `select`-Entität pro Heizkreis mit den Modi plus „keine Anfrage“. Bei gewähltem Modus alle 3 min (sicher unter 5 min) neu schreiben; bei „keine Anfrage“ `0xFFFF` schreiben und das Wiederholen beenden.
2. Angezeigter Zustand aus dem zuletzt geschriebenen Wert, nicht aus dem Register (Rücklesen firmwareabhängig). Auswahl über Neustarts mit `RestoreEntity` halten.
3. Doku: Das ist eine **zeitlich begrenzte Anforderung**, keine Einstellung; das Display-Dropdown ändert sich nicht.
4. Vorsicht: Modus nicht bei laufendem Kompressor wechseln, solange Lambda das nicht freigibt (Hinweis des Testers, Forum). Ggf. Schreiben nur in `STBY`/Taktpause zulassen oder deutlich warnen.
5. Tests: Wiederholtes Schreiben im Takt, „keine Anfrage“ stoppt, Restore nach Neustart.

---

## 🟡 #137: E-Manager-Sollleistung zeigt Wert ohne PV-Überschuss

**Meldung (@drink1909, 19.10.2026, Integration 2.8.6, Steuerung 1.3.8):** Kaskade aus WP-Zähler und Hauszähler; die Einspeisung am Hauszähler wird als Überschuss gemeldet. Mit Überschuss funktioniert die Temperaturanhebung. **Ohne Überschuss** (Wert 0) zeigt „E-Manager Sollleistung“ während eines Laufs (z. B. WW unter Hysterese) einen Wert **~200 W unter der tatsächlichen Leistungsaufnahme** (1.460 W Aufnahme → 1.260 W Soll). Die Pumpe glaubt an Überschuss und hebt die Temperatur mit Netzstrom an.

**Prüfung:**
- „E-Manager Sollleistung“ ist Register **104** (`power_consumption_setpoint`, `lambda_modbus/general.py:31`), in 3.5 wie in 2.x nur gelesen. Die Lambda berechnet den Wert selbst. Die Integration schreibt nur Register 102 (`actual_power`).
- Ein Wert knapp unter der Aufnahme passt zu einer Regelung, die Psoll aus „gemeldete Leistung + eigene Aufnahme“ bildet: Meldet der Messpunkt **Bezug/Einspeisung inkl. WP-Verbrauch** (z. B. „E-Eintrag“ oder ein vorzeichenbehafteter Netzwert statt reinem Überschuss), rechnet die Pumpe ihren eigenen Verbrauch heraus. Bei einer Zählerkaskade, in der der gemeldete Wert den WP-Verbrauch **nicht** enthält, wäre der E-Manager-Messpunkt dann falsch gewählt. Das ist eine Vermutung.
- Weitere mögliche Ursache in 2.8.6: Modus `entry` (2.x) oder ein negativer Quellwert, der in `neg` anders kodiert wird.

**Lösungsansatz:**
1. Rückfragen: Messpunkt und Betriebsart am E-Manager, PV-Modus der Integration (`pos`/`neg`/`entry`), Verlauf von `emgr_actual_power` (Register 102) im fraglichen Zeitraum (steht dort wirklich 0?).
2. Wenn 102 = 0 und Psoll trotzdem > 0: Verhalten der Lambda, an Lambda verweisen; in der Doku festhalten, welcher Messpunkt zu welchem Zählerwert passt.
3. Kein Code-Fix in Sicht; ggf. mit F24 (Doku Betriebsart) zusammen dokumentieren.

---

## 🟡 #144: Neue Steuerung SW V1.4.1 (WP-Firmware V1.0.8-3K)

**Meldung (@AndiBo62, 28.10.2026, Integration 2.8.6, HA 2026.10.4):** EU08L nach Steuerungstausch. Der Puffer wurde erst nach einer Weile erkannt. (1) `sensor.eu08l_ambient_temperature` ist `unknown`, `ambient_temperature_1h` und `ambient_temperature_calculated` haben Werte. (2) `emgr_operating_state` zeigt nur Error (E-Manager: Modbus Client, E-Eintrag, wie vorher).

**Verlauf:** (2) hat Lambda am 28.10. behoben, kein Fehler mehr. Am 29.10. nach einem weiteren Update zeigt das Display **V1.0.8-3K**. Der Melder fragt, ob `hp1_energy_source_inlet_temperature` die Außentemperatur ersetzen kann.

**Prüfung:**
- (1) Register 0002 ist ein Schreibregister für einen extern eingespeisten Außenwert und liefert auf der neuen Steuerung ohne Einspeisung keinen Wert (−3000, siehe `REGISTER_OHNE_WERTE.md`, F3). `unknown` ist also richtig. `ambient_temperature_1h`/`_calculated` kommen aus den Registern 0003/0004 und haben auf der neuen Steuerung Werte. In 3.5 wird `ambient_temperature` ab V0.0.10 gar nicht angelegt (`firmware_versions=("1-7",)`).
- Ersatz: `ambient_temperature_calculated` (0004) ist die Außentemperatur, mit der die Lambda rechnet, und passt besser als `energy_source_inlet_temperature`. Der Quelleneintritt (1007) ist bei einer Luft-WP die Lufttemperatur am Verdampfer; sie liegt nahe an der Außentemperatur, wird aber im Betrieb und beim Abtauen von der Pumpe beeinflusst.
- Firmware **V1.0.8-3K** fehlt in der Auswahl (2.8.6 und 3.5.7). → F26.
- Die späte Puffererkennung passt zur Schwachstelle in der Modulerkennung (F9, Timeout = „Modul fehlt“); in 2.8.6 aber anderer Code.

**Lösungsansatz:**
1. Antworten: 0002 hat ohne Einspeisung keinen Wert, `ambient_temperature_calculated` nutzen; Firmware: in 2.8.6 V1.1.0-3K wählen.
2. V1.0.8-3K mit F26 aufnehmen.
3. Danach schließen.

---

## 🟡 #143: Viele Entitäten (vor allem Puffer) ohne Messwert

**Meldung (@andy5macht, 28.10.2026, Integration 3.5.6, HA 2026.10.4):** EU13 mit **V1.0.4-3K**, in der Integration V1.1.0-3K. Viele Sensoren ohne Wert, vor allem beim Puffer (Screenshot). Registerreihenfolge auf `low_first` gestellt, „sonst fehlen noch mehr Werte“.

**Prüfung:**
- Die Firmware-Wahl ist für 3.5.7 gleichwertig (siehe Tester-Hinweis oben).
- Laut `REGISTER_OHNE_WERTE.md` liefern auf V1.0.4 die Puffer-Register 3000–3003 und 3050 Werte. **3005–3009** sind Anforderungsregister und lesen ohne aktive Modbus-Anforderung −1. Die Integration zeigt sie richtig als `unknown`. Dazu kommen die 21 Register 1024–1033/1051–1060 ohne Wert (F27).
- Die Bemerkung zu `low_first` passt zu #133: 3.5.6 hat bei der Migration `high_first` gesetzt. Die Reihenfolge betrifft aber nur die 32-Bit-Zähler (1020–1023). Dass ohne `low_first` „noch mehr“ fehlt, ist so nicht erklärbar. Vielleicht wurden falsche Zählerwerte verworfen bzw. die Statistik-Sensoren blieben stehen. Rückfrage nötig.
- Der Screenshot ist noch nicht ausgewertet (Bild, nicht maschinenlesbar).

**Lösungsansatz:**
1. Screenshot gegen `REGISTER_OHNE_WERTE.md` abgleichen: Was ist Anforderungs-/Schreibregister (erwartet `unknown`), was sollte einen Wert haben?
2. Rückfragen: Update auf 3.5.7, Diagnose-Download, für fehlende Puffer-Entitäten ein Lesetest über `read_modbus_register` (3000–3009).
3. Mit F27 (Entitäten ohne Wert nicht anlegen) und F12 (Anforderungsregister standardmäßig deaktivieren bzw. als Diagnose) würde die Liste deutlich kürzer. 3005–3009 als Kandidaten für F12 vormerken.

---

## 🟡 #142: Raumtemperatur wird nicht übernommen

**Meldung (@medicus07, 28.10.2026, Integration „2.6.8“ – vermutlich 2.8.6, EU15L, V0.0.10-3K):** PV-Überschuss über Modbus läuft. Für beide Heizkreise je ein HA-Raumtemperatursensor eingetragen (21,1 °C), HA neu gestartet. `read_modbus_register` liefert für 5004 und 5104 dauerhaft **62536**.

**Prüfung:**
- 62536 = `0xF448` = −3000, der Sonderwert für „nichts vorgegeben“. Es wird also tatsächlich nichts geschrieben (oder die Lambda verwirft es).
- 2.8.6 (`main`, `services.py:405–465`) und 3.5 (`services.py:84`, `async_write_room_temperatures`) schreiben nur, wenn **`room_thermostat_control`** in den Options aktiv ist **und** für den Heizkreis eine Entity eingetragen ist und einen Zahlenwert hat. Wahrscheinlichste Ursache: Entities eingetragen, Option „Raumthermostat-Steuerung“ aber nicht aktiv. Aus den Screenshots ist das ohne Bildauswertung nicht ablesbar.
- 2.8.6 loggt jeden Schreibvorgang auf `INFO` („[Scheduled] Writing room temperature to register 5004 …“) und Fehler auf `ERROR`. Ein Log würde sofort zeigen, ob geschrieben wird.
- Möglich ist auch, dass die Lambda den Wert nur annimmt, wenn am Heizkreis die Raumtemperatur auf Modbus/extern eingestellt ist. Das ist nicht dokumentiert.
- Nebenbefund 2.8.6: `num_hc` kommt aus `entry.data` mit Default 1. Fehlt der Schlüssel, wird nur HC1 geschrieben. Hier sind aber beide Kreise betroffen, also nicht die Ursache.

**Lösungsansatz:**
1. Rückfragen: Ist „Raumthermostat-Steuerung“ in den Optionen aktiv? Log mit `INFO` für `custom_components.lambda_heat_pumps`; Einstellung des Raumfühlers am Heizkreis der Lambda.
2. Falls die Option fehlt: In der Doku (`raumthermometer.md`) deutlicher machen, dass beide Schritte nötig sind. Optional im Options-Flow warnen, wenn Entities ohne aktive Option eingetragen sind (S).
3. Gleiche Logik in 3.5, also kein eigener 3.5-Fix, solange die Ursache nicht im Code liegt.

---

## ✅ #121: `device_registry.async_get_device` deprecated

**Prüfung:** Im Branch `3.5` gibt es keinen Aufruf von `async_get_device(` mehr. `coordinator.py:247` nutzt `async_get_device_by_identifier(controller, entry.entry_id)` (Changelog 3.5.4).

**Lösungsansatz:** Mit Hinweis auf 3.5.4 schließen.

---

## ✅ #112: Modbus-Register 5007 doppelt adressiert

**Prüfung:** `sensor.py:307-308`: `flow_line_temperature_setpoint` ist auf `firmware_versions=("1-2",)` begrenzt, `target_temp_flow_line` gilt ab `firmware_version=3`. Pro Firmware wird also nur eine der beiden Entities angelegt (`serves()` in `firmware.py`). Der nicht-deterministische „primary sensor“ aus 2.x (`list(set)[0]`) existiert im neuen Registermodell nicht mehr (Changelog 3.5.5).

**Lösungsansatz:** Mit Hinweis auf 3.5.5 schließen. Optional einen Hinweis für Anwender ergänzen, die die verwaiste Entity aus 2.x noch in der Registry haben: manuell löschen.

---

## Nachtrag 29.10.2026: Issue-Aktivität seit dem 22.10.2026

| Issue | Was ist passiert | Folge für die Analyse |
|---|---|---|
| #104 | @Eisbaer2 (2.8.6, Display V0.0.10-3K, Option war V1.1.0-3K): Zähler falsch seit ca. 13.10.; Gemini-Deutung „float32“ widerlegt; **`high_first` per YAML löst es** (23.10.). Frage nach Reparatur von 10 Tagen Statistik offen | F30 neu, F31 neu, Hinweis bei #90 |
| #100 | Am 27.10. geschlossen. Neu: WP-Software V1.0.7-3K (@web2date, Frage offen), Steuerungstausch bei @AndiBo62 | F26 erweitert |
| #133 | Am 27.10. geschlossen | Übersicht |
| #136 | Am 22.10. als „nicht geplant“ geschlossen (Begründung DE/EN im Issue) | Übersicht |
| #140 | Enhancement (Modi normal/eco/Frostschutz lesen), 27.10. „nicht geplant“: nicht über Modbus lesbar, Verweis auf PV-Überschuss-Steuerung | Liste der Enhancements |
| #141 | Duplikat von #121 (2.x `utils.py:246`), 27.10. geschlossen | Übersicht #121 |
| #142 | Neu: Raumtemperatur wird nicht nach 5004/5104 geschrieben (2.8.6) | eigener Abschnitt, F32 |
| #143 | Neu: viele Entitäten ohne Wert, v. a. Puffer (3.5.6, V1.0.4-3K) | eigener Abschnitt |
| #144 | Neu: neue Steuerung, V1.0.8-3K; E-Manager durch Lambda behoben, `ambient_temperature` `unknown` | eigener Abschnitt, F26 |

Keine neuen Kommentare seit dem 22.10. in #82, #85, #90, #94, #95, #101, #105, #112, #120, #121, #122, #128, #132, #137.

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
| V0.0.10-3K: Firmware-Tabelle (`low_first`) widerspricht einer Anlage mit `high_first` (bestätigt) | `const.py:FIRMWARE_CONFIG` | #104, F30 |
| Bildpfade `../../assets/` statt `../assets/` (21 Bilder in `3.5`, 2 in `main`) | `docs/docs/Anwender/*.md`, `docs/docs/Vorlagen/*.md` | F14, ✅ in `3.5` behoben |
| 10 tote Anker in der Entwickler-Doku (Slugs mit Umlauten, umbenannte Überschriften); in `main` schon mit `2ade7ce` behoben | `docs/docs/Entwickler/*.md`, `Releases/release-2-3.md` | ✅ in `3.5` behoben |
| Doku in `3.5` wurde nie gebaut, Fehler fielen nicht auf | – | ✅ neuer Workflow `docs-check.yml` + `script/check_docs.py` |
| PV-Überschuss: kein Weiterschreiben, wenn der Quellsensor `unknown`/`unavailable` ist → E-Manager-Fehler 6 nach einigen Minuten (auch in 2.8.6 so) | `services.py:105ff` | F15, siehe #120 |
| 2.x-Modus `pv_surplus_mode: entry` wird nicht migriert; 3.5 kennt nur `pos`/`neg`. Schreiben funktioniert (wie `pos`), im Options-Dialog ist `entry` aber kein gültiger Auswahlwert (Verhalten der Oberfläche ungeprüft) | `config_flow.py:321` (Options-Dialog) | F16 |
| `integer()` filtert keine Sonderwerte (nur `gauge()`/`enum()` setzen `nan`). `config_parameter_*` und `request_type` zeigen 32768, `emgr_actual_power` −32768 W (#91, V0.0.8-3K, E-Manager nicht auf Modbus) | `lambda_modbus/model.py`, `heat_pump.py`, `general.py` | F28 |
| Doku/Changelog 3.5.2: „0xFFFF erscheint als −300 °C“ ist falsch (0xFFFF = −0,1 °C; −300 °C ist −3000 und war schon gefiltert). Gleicher Fehler im Kommentar `general.py:15`; `Entwickler/sensoren-uebersicht.md:41` nennt für 0002 `0x8000`, gemessen wurden −3000 und −300 | `CHANGELOG*.md`, `FAQ/falsche-keine-sensorwerte.md`, `general.py`, `Entwickler/sensoren-uebersicht.md` | F29 |
| Merge `3.5` → `main` hat einen Konflikt in `hacs.json` (`homeassistant`: 2024.3.3 vs. 2026.9.0); richtig ist der Wert aus `3.5` | `hacs.json` | Merge-Vorbereitung |
| Doku-Workflow hat keinen `workflow_dispatch`, lässt sich also nicht manuell starten | `.github/workflows/docsz.yml` | optional |
| **Externer Energiezähler: Rückfall auf das Lambda-Register.** Liefert ein in `energy_consumption_sensors` eingetragener Zähler `unknown`/`unavailable`, nimmt `_track_energy` (`if reading is None: reading = register`) das Lambda-Register, obwohl `_meter_reading` laut Kommentar genau das vermeiden soll. Kommt der Zähler zurück, wird die Differenz zwischen beiden Zählern als Verbrauch gebucht, sofern sie unter 100 kWh liegt. | `coordinator.py:458-460` | F18, ✅ behoben 18.10.2026 (`_energy_source`, `_forget_energy_sources`) |
| #135 (geschlossen): Melder schreibt nach der Antwort, bei ihm erscheine im Heizkreis-Status keine Zirkulation; unbeantwortet | Issue #135 | Rückmeldung offen |
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
| F3 | ⏸ **zurückgestellt** (22.10.2026) – `ambient_temperature`: Firmware-Range 1-7 entfernen. Register 0002 liefert auf V1.0.4 ohne Einspeisung auch −300 (= −30,0 °C, #107); nur mit zusätzlichem Sonderwert −300 vertretbar | #100/#108 | **S** (1 Zeile, `sensor.py:177`) | 🟢 **niedrig** (Wert nur bei externer Einspeisung sinnvoll) | Unit **M** + HW **S** |
| F4 | Migration: Firmware aus Options vor Data, Warnung bei unbekanntem Namen | #82 | **S** (~5 Zeilen, `__init__.py:134`) | 🟠 **mittel** | Unit **S** |
| F5 | Climate-Entity-IDs `sensor.*` → `climate.*` in der Registry umbenennen, **als Prüfung bei jedem Start** statt im Migrationsschritt 9 (erreicht auch Tester; Entscheidung 29.10.) | #122/#85 | **M** (~30–40 Zeilen + Klärung des HA-Verhaltens) | 🟠 **mittel** (ab HA 2027.5 hoch) | Unit **M** + HW **M** |
| F6 | ✅ **FIXED** – `V1.0.4-3K` in `FIRMWARE_CONFIG` aufnehmen | #100 | **S** im Code, **L** in der Klärung (Ordinal, `reg_order`) | 🟠 **mittel** | Unit **S** + HW durch Tester |
| F7 | ✅ **entfällt** (21.10.2026) – `volume_flow_heat_sink`: `l/h`, Skala 1 per Wärmebilanz bestätigt (#100, V1.0.2-3K) | #100 | – | – | – |
| F8 | → aufgegangen in **F27/F28** – `config_parameter_*`: 32768 ausblenden bzw. Default aus | #100 | **S** (4 Felder) | 🟢 **niedrig** | Unit **S** |
| F9 | Modulerkennung: Retry bei Timeout | #101/#90 | **S–M** (~15 Zeilen) | 🟢 **niedrig** (selten, Reload hilft) | Unit **M** |
| F10 | PV-Überschuss: Debug-Log und optionales Rücklesen | #105 | **S** | 🟠 **mittel** (falls der Bug noch existiert; unbestätigt) | HW **M** (Beobachtung über Stunden) |
| F11 | Plausibilitätswarnung für 32-Bit-Zähler | #90/#104 | **S–M** | 🟢 **niedrig** (Absicherung, F1/F2 sind der Fix) | Unit **S** |
| F12 | #132: Eingaberegister standardmäßig deaktivieren bzw. als Diagnose führen | #132 | **S** | 🟢 **niedrig** (UX) | Unit **S** |
| F13 | ✅ **erledigt** (17.10.2026, beide Branches) – #95: Doku zur Heizkurve/Raumthermometer | #95/#128 | **S** | 🟢 **niedrig** | manuell |
| F14 | ✅ **FIXED in `3.5`** (17.10.2026; `main` wird nicht mehr geändert, PV-Seite kommt mit dem Merge) – Bildpfade `../../assets/` → `../assets/` | #120 | **S** (16 Dateien, mechanisch) | 🟠 **mittel** (vor dem Merge zwingend, sonst 21 kaputte Bilder live) | Build + Pfadprüfung (Skript vorhanden) |
| F15 | PV-Überschuss: 0 W senden (+ Log-Warnung), wenn die Quelle `unknown`/`unavailable` ist | #120/#105 | **S** | 🟠 **mittel** (verhindert E-Manager-Fehler 6) | Unit **S** |
| F16 | `pv_surplus_mode: entry` aus 2.x: im Options-Dialog als `pos` vorbelegen (statt Migration, erreicht auch Tester; Entscheidung 29.10.) | – | **S** (1 Zeile, `config_flow.py:321`) | 🟢 **niedrig** | Unit **S** |
| F17 | Abweichungssensor Pumpen-Sollwert − berechnete Kurve | #128 | **S–M** | 🟢 **niedrig** (Enhancement) | Unit **S** + HW **S** |
| F18 | ✅ **FIXED** 18.10.2026 – Externer Zähler: Rückfall aufs Register erlaubt, aber jeder Quellenwechsel und jeder Ausfall beginnt wie beim Start (erste Differenz verworfen) | – | **S** (2 Zeilen, `coordinator.py:458`) | 🟠 **mittel** (falsche kWh bei jedem Ausfall des Zählers) | Unit **S** |
| F19 | ✅ **FIXED** 18.10.2026 – Hilfetext zur Firmware im Einrichtungsdialog korrigieren (auch unter Neu konfigurieren) | – | **S** (Übersetzungen) | 🟢 **niedrig** | – |
| F20 | Testumgebung auf HA 2026.10 anheben + deprecated `async_get_device` im Test ersetzen | HA 2026.10 | **S** (1 Pin + 2 Testzeilen) | 🟠 **mittel** (Tests laufen sonst gegen eine HA-Version unter dem Minimum) | Testlauf |
| F21 | Climate-Properties → `native_…`, Mindestversion 2026.11.0 – **erst nach Erscheinen von 2026.11** | HA 2026.11 | **S** (~5 Zeilen + `hacs.json`) | 🟢 **niedrig** (nur Log-Warnungen bis 2027.11) | Unit **S** |
| F22 | hassfest (`ha.yml`) auf `3.5` laufen lassen | HA 2026.10 | – | 🟢 **niedrig** | CI |
| F23 | ⛔ **wird nicht umgesetzt** (22.10.2026) – `select`-Entität Heizkreis-Betriebsart (5X06) mit Neuschreiben alle 3 min. Gründe: kein Eingriff in die Regelung/Wärmefahrplan, Register gibt den gesetzten Wert nicht zurück, Ankunft nicht prüfbar | #136/#125 | – | – | – |
| F24 | Doku PV-Überschuss: Psoll nur in „Automatik“, mögliche Temperaturanhebung; Messpunkt passend zum Zählerwert | #120/#137 | **S** | 🟢 **niedrig** | manuell (Automatik-Test des Testers abwarten) |
| F25 | Antwort #134: V1.0.4-3K und V1.1.0-3K legen dieselben Entitäten an; optional Satz in Changelog/`firmware-wechsel.md` | #134 | **S** | 🟢 **niedrig** | – |
| F26 | Firmware der neuen Steuerung in `FIRMWARE_CONFIG`: `V1.0.2-3K` (#100), **neu `V1.0.7-3K` (#100, 24.10.) und `V1.0.8-3K` (#144, 29.10.)**, alle `low_first` angenommen (belegt nur für V1.0.2/V1.0.4). Ordinals neu ordnen (z. B. V1.0.2 → 9, V1.0.4 → 10, V1.0.7 → 11, V1.0.8 → 12, V1.1.0 → 13); kein Sensor prüft auf ≥ 9, Einträge speichern den Namen. Alternativ ein Sammeleintrag „V1.0.x-3K (neue Steuerung)“, damit nicht jedes Lambda-Update eine neue Version braucht | #100/#144 | **S** (`const.py` + `test_firmware.py`) | 🟢 **niedrig** (heute: V1.0.4-3K oder V1.1.0-3K wählen, gleiche Entitäten) | Unit **S** |
| F27 | Sensoren auf 1024–1033 und 1051–1060 (21 Stück) ab V1.0.x nicht mehr anlegen (`firmware_versions=("1-8",)`); **offen:** V1.1.0-3K mit ausschließen? Danach prüfen, ob die Register auch nicht mehr gelesen werden (11 Einzelabfragen der Leistungsgrenzen) | #100/#119/#88 | **S** (+ **S–M** für das Lesen) | 🟠 **mittel** (21 dauerhaft „unbekannte“ bzw. 32768-Entitäten, Log-Last) | Unit **S**; Changelog-Hinweis (Entitäten „nicht mehr bereitgestellt“) |
| F28 | Sonderwert 0x8000 auch für `integer`-Felder filtern (`config_parameter_*`, `request_type`, `emgr_actual_power`) | #91/#100 | **S** | 🟠 **mittel** (−32768 W bzw. 32768 als Messwert, z. B. im Energie-Dashboard) | Unit **S** |
| F29 | Doku/Changelog/Kommentar korrigieren: 0xFFFF = −0,1 °C, nicht −300 °C; 0002-Aussage in der Entwickler-Doku | – | **S** | 🟢 **niedrig** | – |
| F30 | **Wortreihenfolge der 32-Bit-Zähler nicht allein aus der Firmware ableiten** (neu 29.10.). Belegt: V0.0.10-3K mit `high_first` (#104), V0.0.9-3K mit `low_first`-Daten (#90). Variante a: F11 umsetzen, also bei unplausiblen Zählern (≤ 0, > 10⁹ Wh oder Wechsel fast nur im oberen Wort) ein Repair-Issue „Registerreihenfolge prüfen“ mit der anderen Reihenfolge als Vorschlag. Variante b: beim Setup beide Deutungen von 1020–1023 vergleichen und die plausiblere übernehmen (Zähler steigen nur im unteren Wort). Bis dahin: FAQ-Hinweis, dass die Tabelle nur ein Default ist | #104/#90 | a: **S–M**, b: **M** | 🟠 **mittel** (beschädigt das Energie-Dashboard, betrifft unbekannt viele Anlagen) | Unit **S–M**; Simulator (umschaltbare Wortreihenfolge) |
| F31 | FAQ: Statistik nach falscher Registerreihenfolge bereinigen (Ausreißer per SQL bzw. „Statistik anpassen“, Lücke verteilen). Bisher Punkt 6 bei #104, jetzt konkret angefragt (#104, 23.10.) | #104/#133 | **S** | 🟢 **niedrig** | – |
| F32 | Raumthermostat: Doku klarstellen (Option „Raumthermostat-Steuerung“ **und** Entity nötig); optional Hinweis im Options-Flow, wenn Entities ohne aktive Option eingetragen sind | #142 | **S** | 🟢 **niedrig** (erst nach Rückmeldung des Melders) | Unit **S** |

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
- ⏸ **Zurückgestellt 22.10.2026:** Neue Belege (#100, #107, #108) zeigen, dass Register 0002 auf V1.0.x nur bei externer Einspeisung einen Wert hat und sonst −3000 oder −300 (= −30,0 °C) liefert. Die Bewertung unten ist damit überholt; Details in `REGISTER_OHNE_WERTE.md`.
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
- ✅ **Entfällt (21.10.2026):** Rohwert-Dump von V1.0.2-3K bestätigt `l/h`, Skala 1 (Wärmebilanz).
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
| **B: vor dem Release empfohlen** | F5, F27, F28, F30 (F7 entfällt) | ~0,5–1 Tag (+ Klärung HA-Verhalten) | ~0,5 Tag | Upgrade-Test (mit Paket A kombinierbar) + Rohwert-Dumps von Testern |
| **C: abhängig von Externen** | F6 | ~1 h | ~1 h | Tester aus #100 (Termin unklar) |
| **D: nach dem Release möglich** | F9–F12, F15, F17, F21 (sobald HA 2026.11 erschienen ist), F24, F25, F26, F29, F31, F32 | ~0,5 Tag gesamt | ~0,5 Tag | F10: Langzeitbeobachtung |

**Kernaussage:** Die kritischsten Fixes (F1–F4) sind im Code klein. Ihr Risiko liegt im Release-Zeitpunkt: Sie wirken alle beim ersten Start nach dem Upgrade und sind danach nur mit einer zusätzlichen Migration bzw. manueller Statistikbereinigung zu korrigieren. Den größten Testaufwand machen nicht die Fixes selbst, sondern das Umschreiben der drei Tests, die das aktuelle (Fehl-)Verhalten festschreiben, und der eine echte Upgrade-Test, der F1, F3, F4 und F5 gemeinsam abdeckt.

## Umsetzungsplan 3.5.x (Stand 29.10.2026)

> **Umsetzung in Branch `3.6` (29.10.2026, Version 3.6.0):** Schritte 1–5 und der Code-Teil von Schritt 8 sind umgesetzt, 184 Tests bestehen (Python 3.14, HA 2026.10.2), der Doku-Build ist ohne Hinweise. Offen bleiben Schritt 6 (Hardware-Test), Schritt 7 (Release und Merge) sowie F21 (wartet auf HA 2026.11) und F17 (Enhancement #128).
>
> | Commit | Schritt | Fixes | Ergebnis |
> |---|---|---|---|
> | `5d8655b` | 1 | F20, F22 | Testumgebung HA 2026.10 (`0.13.373`), deprecated `async_get_device` im Test ersetzt; hassfest/HACS und Doku-Check auch auf `3.*` |
> | `cb523ed` | 2 | F4, F16; **F5 entfällt** | Migration: Firmware aus Options vor Data, unbekannter Name → Warnung + Repair (entfernt durch *Neu konfigurieren*). Options-Dialog: PV-Modus `entry` → `pos`. **F5:** HA registriert Entitäten immer unter der Plattform-Domain und nimmt aus einer vorgeschlagenen ID nur den Objektteil; die 2.x-Einträge heißen also schon `climate.*`, nur die Warnung kam vom falschen Vorschlag. Ein Umbenennen über die Domain lehnt HA ab („New entity ID should be same domain“). Test sichert das ab |
> | `21b13ab` | 3 | F30 (inkl. F11), F31 | Zähler < 0 oder > 1 GWh, getauscht plausibel → Repair „32-Bit-Registerreihenfolge prüfen“ mit Vorschlag; beide Zähler der WP halten ihren letzten Wert, COP (berechnet) unbekannt, keine Energie gebucht (vorher 65,5 kWh pro Wh unter dem Sprungfilter). Alle Werte aus #104/#133/#90 per Test geprüft. FAQ Statistikbereinigung |
> | `82cf97e` | 4 | F26, F27, F28, F12 | V1.0.2/V1.0.7/V1.0.8-3K (Ordinals 9–12, V1.1.0 → 13); 20 Sensoren 1024–1033/1051–1060 nicht auf V1.0.x (**V1.1.0-3K behält sie**, kein Dump); 0x8000 als „kein Wert“ bei E-Manager-Leistungen, Inverter, Volumenstrom, `request_type`; Anforderungs-/Schreibregister standardmäßig aus |
> | `20d6256` | 5 | F24, F25, F29, F32 | Changelog 3.6.0, Version 3.6.0; PV-Doku (Psoll nur „Automatik“, Messpunkt), Firmware-Seite, 0xFFFF = −0,1 °C, Raumthermometer (Option **und** Sensor) |
> | `b869411` | 8 | F15, F9, F10 | PV 0 W bei ausgefallener Quelle (einmal gewarnt); Retry bei Timeout in der Modulerkennung, Module auf Info geloggt; Debug-Log des PV-Rohwerts |
>
> **Abweichungen vom Plan:** F5 entfällt (siehe oben). F27 schließt V1.1.0-3K bewusst nicht aus. F27a (die Leistungsgrenzen auf V1.0.x auch nicht mehr lesen) ist nicht umgesetzt: Die Integration liest die elf Register weiter einmal pro Stunde, legt aber keine Entitäten mehr an. F28 lässt die Config-Parameter unverändert (32768 kann dort ein echter Wert sein; auf V1.0.x fallen sie durch F27 weg).

**Betrifft 3.5.x (Arbeit offen):** #104, #90, #82, #100, #144, #143, #122/#85, #105, #101, #120, #134 und das Enhancement #128. Unklar: #142. **Betrifft 3.5.x nicht:** #94, #95, #112, #121, #136, #137 (#132 nur optionale UX). Dazu kommen Befunde ohne eigenes Issue: F15, F16, F20, F21, F22, F29.

**Prinzip:** Erst die Testgrundlage, dann alles, was beim ersten Start nach dem Upgrade einmalig wirkt (Migration, Zähler). Danach alles, was die Menge der Entitäten ändert, gesammelt in einem Release. Dann der Hardware-Test als Freigabe. Was jederzeit nachgeschoben werden kann, kommt nach dem Release.

**Tester mit 3.5 (Entscheidung 29.10.2026): keine neue `ENTRY_VERSION`.** Einige Tester haben 3.5.x im Einsatz; ihr Eintrag ist schon auf Version 9, der Migrationsschritt 9 läuft für sie nie wieder. Deshalb gilt:
- In Schritt 9 kommt nur, was ausschließlich den Wechsel von 2.x betrifft (F4).
- Alles, was auch Tester betrifft, wird **beim Start bei jedem Setup** geprüft: einmalig wirksam, danach ohne Wirkung, wenn alles stimmt (F5, F16). Das erreicht 2.x-Umsteiger und Tester gleichermaßen.
- Die Altlast aus F1 (`high_first` fest in den Options bei Testern, die mit 3.5.6 oder älter migriert haben) lässt sich nicht automatisch korrigieren, weil ein von Hand gesetztes `high_first` richtig sein kann (#104). Das deckt F30 ab: Unplausible Zähler erzeugen bei jedem, auch bei Testern, ein Repair-Issue.
- Eine neue `ENTRY_VERSION` hätte für Tester einen Nachteil: Nach einem Rückschritt auf eine ältere 3.5.x lädt der Eintrag nicht mehr, weil HA einen Eintrag mit höherer Version ablehnt.

| Schritt | Inhalt | Fixes | Issues | Warum an dieser Stelle | Aufwand |
|---|---|---|---|---|---|
| **1. Testgrundlage** | Testumgebung auf HA 2026.10 (Pin + 2 Testzeilen), hassfest auf `3.5` | F20, F22 | – | Alle folgenden Tests sollen gegen eine HA-Version laufen, die 3.5 auch verlangt (heute 2026.8.1 < Minimum 2026.9.0). | S |
| **2. Upgrade-Pfad korrigieren** | **a) Migrationsschritt 9:** Firmware aus Options vor Data, Warnung bei unbekanntem Namen (F4). **b) Prüfung beim Start** (`async_setup_entry`, jedes Setup): Registry-Einträge der Plattform `climate` mit `sensor.*`-ID auf `climate.*` umbenennen, Kollisionen überspringen und loggen (F5; vorher HA-Verhalten klären). **c) Options-Dialog:** unbekannter PV-Modus (z. B. `entry` aus 2.x) wird als `pos` vorbelegt (F16, `config_flow.py:321`); das Schreiben behandelt ihn heute schon wie `pos` (`services.py:120`) | F4, F5, F16 | #82, #122, #85 | a) betrifft nur 2.x-Umsteiger und muss vor dem Release stehen, sonst bräuchte es eine neue `ENTRY_VERSION`. b) und c) erreichen auch Tester, deren Eintrag schon migriert ist. Tests: a) `test_config_flow.py` (Version 8), b) `test_init.py` mit vorbereitetem Registry-Eintrag (umbenannt, Kollision, zweiter Start ändert nichts), c) `test_options_flow.py` | M |
| **3. Zähler absichern** | Unplausible 32-Bit-Zähler erkennen und ein Repair-Issue „Registerreihenfolge prüfen“ mit der anderen Reihenfolge als Vorschlag anlegen (Variante a, enthält F11); FAQ zur Statistikbereinigung | F30, F31 | #104, #90 | #104 (23.10.) zeigt, dass F1 allein nicht schützt, wenn eine Anlage von der Firmware-Tabelle abweicht. Der Schaden (Energie-Dashboard) entsteht direkt nach dem Upgrade. | S–M |
| **4. Firmware-Tabelle und Entitäten** | Neue Firmware-Namen (V1.0.2/V1.0.7/V1.0.8-3K) und Ordinals → Register ohne Werte ab V1.0.x nicht mehr anlegen → Sonderwert 0x8000 für `integer` → Anforderungsregister standardmäßig deaktivieren | F26 → F27 → F28 → F12 | #100, #144, #143, (#132) | F27 nutzt Firmware-Bereiche und hängt deshalb an den Ordinals aus F26. Alle vier ändern, welche Entitäten erscheinen. Ein gemeinsamer Changelog-Hinweis im ohnehin großen Versionssprung ist besser als mehrere kleine Brüche. | M |
| **5. Doku vor dem Release** | Betriebsart E-Manager (Psoll nur in „Automatik“), V1.0.4 vs. V1.1.0, 0xFFFF = −0,1 °C, Raumthermostat braucht Option **und** Entity, Changelog für Schritt 2–4; Hinweis für Tester: wer mit 3.5.6 oder älter migriert hat, prüft die Registerreihenfolge einmal im Options-Dialog | F24, F25, F29, F32 | #120, #134, #142, #137 | Nur Doku, kein Risiko. Schritt 2–4 brauchen ohnehin Changelog-Text. | S |
| **6. Freigabe: Upgrade-Test an echter Anlage** | 2.8.6 → 3.5 auf einer `low_first`-Anlage ohne YAML-Wert, möglichst zusätzlich eine Anlage mit abweichender Reihenfolge (z. B. der Melder aus #104). Prüfen: Options ohne `int32_register_order`, Zähler unverändert, Climate-IDs umbenannt, `recorder/validate_statistics` ohne neue Befunde, F30-Repair erscheint nur bei abweichender Anlage. **Zusätzlich ein schon migrierter Tester-Eintrag** (z. B. @Sturmi77): Update starten, Climate-IDs umbenannt, Options-Dialog zeigt einen gültigen PV-Modus, bei falscher Reihenfolge erscheint das F30-Repair | – | #133, #104 | Ein Test deckt F1, F4, F5, F16 und F30 gemeinsam ab, der Tester-Eintrag die Prüfungen beim Start. Der Simulator aus `modbus_tools` (umschaltbare Wortreihenfolge) eignet sich als Vorstufe. | 0,5 Tag |
| **7. Release 3.5 + Merge nach `main`** | Erstes öffentliches 3.5-Release; Merge `3.5` → `main` (Konflikt `hacs.json` zugunsten `3.5`); 2.x-FAQ-Seite zu `async_get_device` danach löschen | – | #121, #112, #134 schließen | `main` bekommt erst hier die Fixes. | S |
| **8. Nach dem Release** | PV-Überschuss 0 W bei ausgefallener Quelle (kann vorgezogen werden); Retry bei der Modulerkennung; Debug-Log PV; Climate `native_…` + Mindestversion 2026.11 (sobald HA 2026.11 erschienen ist, Anfang November); Abweichungssensor Heizkurve | F15, F9, F10, F21, F17 | #105, #101, #144 (späte Puffererkennung), #128 | Keine einmalige Wirkung beim Upgrade, kein Datenrisiko; lässt sich in Patch-Releases nachschieben. F21 ist an den HA-Termin gebunden, nicht an 3.5. | je S–M |

**Zurückgestellt bzw. nicht geplant:** F3 (`ambient_temperature` ab V0.0.10; Register 0002 hat ohne Einspeisung keinen Wert, siehe #144), F23 (#136).

**Issue-Antworten parallel, unabhängig von den Schritten:** #100 (@web2date: V1.0.7-3K → V1.0.4-3K/V1.1.0-3K wählen), #104 (Statistik-Frage, F31), #144 (0002 / `ambient_temperature_calculated`), #142 und #143 (Rückfragen), #105 (Automatik-Test), #90 (Firmware/Rohwert), #94/#95/#132 schließen.

**Kritischer Pfad:** Schritt 1 → 2 → 3 → 4 → 6 → 7. Schritt 5 läuft neben 2–4 her. Grob 3–4 Arbeitstage plus Hardware-Test; die größte Unbekannte ist F5 (HA-Verhalten bei Registry-Einträgen mit falscher Domain).

---

## Empfohlene Reihenfolge

> Stand 22.10.2026, **ersetzt durch den [Umsetzungsplan 3.5.x](#umsetzungsplan-35x-stand-29102026)** oben. Bleibt zur Nachvollziehbarkeit stehen.

Da 3.5 noch nicht veröffentlicht ist, sollten alle Migrationskorrekturen (F1, F4, F5) **vor dem Release** in den bestehenden Migrationsschritt 9 einfließen. *(Überholt 29.10.: F5 wird eine Prüfung beim Start, siehe Umsetzungsplan.)* Danach bräuchte jede Korrektur eine eigene neue Migration. Die Pakete beziehen sich auf die Bewertung oben.

1. **Paket A, vor dem Release zwingend:** ~~F1 + F2 (#104/#90, Registerreihenfolge in Migration und Options-Flow)~~ ✅ erledigt (#133), ~~F3~~ ⏸ zurückgestellt, F4 (#82, Firmware-Priorität), F14 (Bildpfade, vor dem Merge nach `main`), F16 (`entry` → `pos` in Schritt 9), F20 (Testumgebung HA 2026.10), F22 (hassfest auf `3.5`). Abschließend ein echter Upgrade-Test 2.8.6 → 3.5 auf einer `low_first`-Anlage.
2. **Paket B, vor dem Release empfohlen:** F5 (#122/#85, Climate-IDs; vorher das HA-Verhalten klären), F27 + F28 (Register ohne Werte, siehe `REGISTER_OHNE_WERTE.md`), F30 (Wortreihenfolge prüfen statt nur aus der Firmware ableiten; nach #104 vom 23.10. kann F1 allein Anlagen wie die von @Eisbaer2 nicht schützen). Beides ändert Entitäten und kommt am besten mit dem ohnehin großen Versionssprung 3.5. ~~F7~~ entfällt.
3. **Paket C, abhängig von Testern:** ~~F6 (`V1.0.4-3K`)~~ ✅ erledigt.
4. **Paket D, nach dem Release:** F21 (Climate `native_…`, sobald HA 2026.11 erschienen ist), F24 (Doku Betriebsart E-Manager), F25 (#134 Antwort), F26 (V1.0.2/V1.0.7/V1.0.8-3K), F29 (Doku 0xFFFF), F31 (FAQ Statistik), F32 (Doku Raumthermostat), F9–F12, F15 (PV 0 W bei ausgefallener Quelle; kann auch vorgezogen werden), F17 (#128 Abweichungssensor).
5. **Issues pflegen:** #121 und #112 schließen, #132 schließen (in #134 bestätigt), #94/#95 nach Rückmeldung schließen, #105 nach Retest schließen, ~~#133 schließen~~ ✅ 27.10., ~~#134~~ ✅, ~~#136~~ ✅ 22.10., ~~#100~~ ✅ 27.10., #120 nach F14 schließen, in #90 nach Firmware-Version/Rohwert fragen. **Neu (29.10.):** in #100 @web2date antworten (V1.0.7-3K → V1.0.4-3K/V1.1.0-3K wählen); #104 Rückfrage zur Statistik beantworten (F31), danach schließen; #144 antworten (0002/`ambient_temperature_calculated`, Firmware) und schließen; #143 und #142 Rückfragen stellen (siehe Abschnitte).
6. **Merge `3.5` → `main` vorbereiten:** `main` wird bis dahin nicht mehr geändert; F14 ist in `3.5` erledigt; Konflikt in `hacs.json` zugunsten von `3.5` lösen.

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

#128 Heizkurve: Abweichung zum realen Vorlaufsoll (inzwischen analysiert, siehe oben) · #138 Heatpump Flow Card von @Sturmi77 (Bitte um README-Link und Vorwarnung bei Umbenennungen von Entitäten/Zuständen, betrifft z. B. F5) · #119 Weniger Logging bei Sentinel-Werten · #140 Modi normal/eco/Frostschutz lesen (geschlossen 27.10., „nicht geplant“) · #113 Schreibbarer Kühl-Vorlaufsollwert · #83 Energiestatistik Wärmeverteilung · #79 Status-Entity PV-Überschuss-Modus · #77 Spreizung HP1 · #60 Abtauzähler 6h/12h · #59 Soll-Vorlauf bei PV-Überschuss erhöhen · #45 Wechselnde Strompreise · #37 State-Werte in Influx/Grafana
