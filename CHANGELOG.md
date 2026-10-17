# Changelog

**Deutsche Version siehe unten / [German version see below](#deutsche-version)**

> 📜 Full version history: [CHANGELOG_ALL_CHANGES.md](CHANGELOG_ALL_CHANGES.md) · Vollständige Versionshistorie: [CHANGELOG_ALL_CHANGES.md](CHANGELOG_ALL_CHANGES.md)

<!-- lang:en -->
## English Version

> **📚 Documentation**: A German documentation is currently being built at [https://guidojeuken-6512.github.io/lambda_heat_pumps](https://guidojeuken-6512.github.io/lambda_heat_pumps)

> **⚠️ Upgrading from 2.x to 3.5.x — Home Assistant will show "Repairs" about statistics (harmless):**
> After the first start, Settings → Repairs lists about 14 warnings for `eu08l_…` sensors (names depend on your device name). They concern *long-term statistics recorded by 2.x*, not live data — nothing is lost and all sensors keep working.
> - **"Unit changed" / "Mean type changed"** (`hp1_volume_flow_heat_sink`, `hp1_volume_flow_energy_source`): 2.x stored the units as `l/h` and `l/min`, 3.5 uses Home Assistant's standard `L/h` and `L/min`, which HA cannot convert automatically. → Open the repair and choose **"Update the unit of the old values"** (history is kept; the values are identical, only the unit label changes). Deleting the statistics instead also works but discards the history. **Old long-term data is not deleted by the update** — it stays untouched; but until you pick one of the two options, Home Assistant records no new long-term statistics for these two sensors (live values and the history graph are unaffected).
> - **"State class removed"** (error numbers `*_error_number`, `hp1_request_type`, `hp1_config_parameter_24/33/50/60`): these are codes, not measurements, so 3.5 no longer records statistics for them (in 2.x they were wrongly recorded as `total`). → Safe to ignore, or delete their statistics under Developer Tools → Statistics ([how](https://guidojeuken-6512.github.io/lambda_heat_pumps/Anwender/historische_daten_loeschen/)).
> - Repairs about *unknown entity references* in dashboards/templates mean a 2.x entity was renamed or removed in 3.5 — adjust the card/template.
> - Back up before upgrading.

### [Unreleased]

Fixed the 2.x→3.5 migration pinning the 32-bit register order to `high_first`: without an explicit value in the old `lambda_wp_config.yaml` (missing, empty or commented-out key — the usual case), the migration stored `high_first` instead of leaving the setting unset, so the firmware default no longer applied. On firmware `V0.0.10-3K` and `V1.1.0-3K` (low word first) the accumulated energy counters jumped to absurd values (e.g. 1.14 billion Wh) and polluted the long-term statistics. The setting is now only carried over when the old file sets it explicitly; otherwise the firmware's own order applies, as in 2.8.x. The options dialog now also pre-selects the firmware's order instead of `high_first`, so saving it unchanged no longer pins the wrong value. **Already upgraded to 3.5 before this fix?** Check *Settings → Integrations → Lambda → Configure → 32-bit register order* and set `low_first` for V0.0.10-3K/V1.1.0-3K. See [CHANGELOG_ALL_CHANGES.md](CHANGELOG_ALL_CHANGES.md) for details. [Issue #133](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/133)

### [3.5.6] - 2026-09-15

Fixed a data-loss bug found via a live v2.8.x→3.5.x upgrade on real hardware: every lifetime total counter (`heating_energy_total`, `heating_thermal_energy_total`, `hot_water_energy_total`, `stby_energy_total`, and their cycling-count equivalents) reset to zero (or the configured offset alone) instead of continuing from its accumulated value, because the old version's entities go `unavailable` while it unloads for the upgrade, and the new `RestoreSensor`-based restore only ever tried the entity's own last state — with no fallback once that state was `"unavailable"`. `_restored_value()` now falls back to Home Assistant's own long-term statistics, which still hold the real last value from before the gap; a configured offset is treated as already included in a value recovered this way, instead of being added a second time on top. A second bug in the same change — the `_cycling_yesterday` sensors crashing on restore because their own caller wasn't updated for the new return shape — was caught by the same live test and fixed alongside it. Verified against real hardware: every lifetime and cycling total (incl. five different configured offsets) survived the actual upgrade with its exact prior value, and the previously-crashing `_cycling_yesterday` sensors came back healthy after redeploying the fix.

### [3.5.5] - 2026-09-12

Fixed a register conflict reported against firmware 3+: heating-circuit register 7 is repurposed on firmware 3 from the writable setpoint request to the read-only value the controller actually acts on, but the old writable sensor (`flow_line_temperature_setpoint`) had no upper firmware bound, so it kept being created alongside the new read-only one (`target_temp_flow_line`) — both reading and writing the same address. `flow_line_temperature_setpoint` is now restricted to firmware 1-2, the range it still means what its name says. See [CHANGELOG_ALL_CHANGES.md](CHANGELOG_ALL_CHANGES.md) for details. [Issue #112](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/112)

### [3.5.4] - 2026-09-09

Fixed another Home Assistant deprecation warning, found by auditing the real system log of two live installations after a Home Assistant 2026.9.1 upgrade: `device_registry.async_get_device()`, used to resolve a sub-device's parent for `via_device_id`, is deprecated and scheduled for removal in Home Assistant 2027.8.0. Replaced with `async_get_device_by_identifier()`. Verified against real hardware — the full test suite, a live remove/recreate of the config entry, and an end-to-end run of the actual config flow all pass unchanged. See [CHANGELOG_ALL_CHANGES.md](CHANGELOG_ALL_CHANGES.md) for details.

### [3.5.3] - 2026-09-06

Fixed a functional regression from the 3.5.0 rewrite found via live testing: every Modbus write used FC06 (Write Single Register), which Lambda's own protocol documentation says is not implemented at all — every write (room-thermostat control, PV-surplus export, hot-water/heating-circuit/cooling-circuit setpoints, the generic register-write service) failed with "Illegal Function". Every writable register now writes via FC16 (Write Multiple Registers), matching the pre-3.5 code and Lambda's documented protocol. See [CHANGELOG_ALL_CHANGES.md](CHANGELOG_ALL_CHANGES.md) for details.

### [3.5.2] - 2026-09-06

Follow-up to the 3.5.0 rewrite adoption: fixed three gaps found by auditing every 2.7.x/2.8.x bugfix from the pre-rewrite `main` branch against the rewritten codebase — a `via_device` deprecation warning on sub-devices, a `0xFFFF` sentinel ("no request"/"no external sensor") read as a real value (e.g. exactly -300.0 °C for the outside temperature), and Modbus reads/writes not actually being serialized against each other (the class of issue behind #105). See [CHANGELOG_ALL_CHANGES.md](CHANGELOG_ALL_CHANGES.md) for details and the new regression tests.

### [3.5.0] - 2026-09-06

Adopted a ground-up rewrite of the integration (PR #115): the Modbus layer moves from `pymodbus` to [`modbus-connection`](https://github.com/home-assistant-libs/modbus-connection)/`tmodbus`, heat pumps and other modules are addressed by index and object reference instead of reconstructed entity-id strings (removing the bug class behind Issues #93/#107), and counters persist via plain Home Assistant `RestoreSensor`s. Minimum Home Assistant version is now 2026.9.0. See [CHANGELOG_ALL_CHANGES.md](CHANGELOG_ALL_CHANGES.md) for the full breakdown.

<!-- /lang:en -->
## Deutsche Version {#deutsche-version}

<!-- lang:de -->

> **📚 Dokumentation**: Eine deutsche Dokumentation wird derzeit unter [https://guidojeuken-6512.github.io/lambda_heat_pumps](https://guidojeuken-6512.github.io/lambda_heat_pumps) aufgebaut

> **⚠️ Update von 2.x auf 3.5.x — Home Assistant zeigt „Reparaturen“ zu Statistiken an (harmlos):**
> Nach dem ersten Start listet Einstellungen → Reparaturen rund 14 Warnungen zu `eu08l_…`-Sensoren (Namen je nach Gerätename). Sie betreffen die *von 2.x aufgezeichnete Langzeitstatistik*, nicht die Live-Daten — es geht nichts verloren und alle Sensoren funktionieren weiter.
> - **„Maßeinheit geändert“ / „Mittelwert-Typ geändert“** (`hp1_volume_flow_heat_sink`, `hp1_volume_flow_energy_source`): 2.x speicherte die Einheiten als `l/h` und `l/min`, 3.5 nutzt die HA-Standardeinheiten `L/h` und `L/min`, die HA nicht automatisch umrechnen kann. → Reparatur öffnen und **„Maßeinheit der alten Werte aktualisieren“** wählen (Historie bleibt erhalten; die Werte sind identisch, nur das Einheiten-Label ändert sich). Alternativ die Statistik löschen — dann geht die Historie verloren. **Die alten Langzeitdaten werden durch das Update nicht gelöscht**, sie bleiben unverändert erhalten; solange du aber keine der beiden Optionen wählst, zeichnet Home Assistant für diese beiden Sensoren keine neue Langzeitstatistik auf (Live-Werte und Verlaufsgrafik sind nicht betroffen).
> - **„Statusklasse entfernt“** (Fehlernummern `*_error_number`, `hp1_request_type`, `hp1_config_parameter_24/33/50/60`): Das sind Codes, keine Messwerte, deshalb zeichnet 3.5 dafür keine Statistik mehr auf (in 2.x wurden sie fälschlich als `total` aufgezeichnet). → Kann ignoriert werden, oder die Statistik unter Entwicklerwerkzeuge → Statistiken löschen ([Anleitung](https://guidojeuken-6512.github.io/lambda_heat_pumps/Anwender/historische_daten_loeschen/)).
> - Reparaturen zu *unbekannten Entitätsreferenzen* in Dashboards/Templates bedeuten, dass eine 2.x-Entität in 3.5 umbenannt oder entfernt wurde — Karte/Template anpassen.
> - Vor dem Update ein Backup erstellen.

### [Unveröffentlicht]

Die Migration von 2.x auf 3.5 hat die 32-Bit-Registerreihenfolge fest auf `high_first` gesetzt: Stand in der alten `lambda_wp_config.yaml` kein ausdrücklicher Wert (Datei fehlt, ist leer oder der Eintrag ist auskommentiert — der Normalfall), speicherte die Migration `high_first`, statt die Einstellung leer zu lassen. Der Firmware-Default griff dadurch nicht mehr. Bei Firmware `V0.0.10-3K` und `V1.1.0-3K` (niederwertiges Wort zuerst) sprangen die akkumulierten Energiezähler auf unsinnige Werte (z. B. 1,14 Mrd. Wh) und verfälschten die Langzeitstatistik. Die Einstellung wird jetzt nur noch übernommen, wenn die alte Datei sie ausdrücklich setzt; sonst gilt die Reihenfolge der Firmware, wie in 2.8.x. Auch der Options-Dialog schlägt jetzt die Reihenfolge der Firmware vor statt `high_first`, sodass unverändertes Speichern keinen falschen Wert mehr festschreibt. **Schon vor diesem Fix auf 3.5 aktualisiert?** Unter *Einstellungen → Integrationen → Lambda → Konfigurieren → 32-Bit-Registerreihenfolge* prüfen und bei V0.0.10-3K/V1.1.0-3K `low_first` wählen. Details siehe [CHANGELOG_ALL_CHANGES.md](CHANGELOG_ALL_CHANGES.md). [Issue #133](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/133)

### [3.5.6] - 2026-09-15

Einen Datenverlust-Bug behoben, gefunden bei einem echten v2.8.x→3.5.x-Upgrade auf realer Hardware: Jeder Lifetime-Gesamtzähler (`heating_energy_total`, `heating_thermal_energy_total`, `hot_water_energy_total`, `stby_energy_total` sowie die entsprechenden Zyklus-Zähler) fiel beim Upgrade auf null (bzw. nur den konfigurierten Offset) zurück, statt beim akkumulierten Wert weiterzuzählen — weil die Entities der alten Version beim Entladen für den Versionssprung kurz `unavailable` werden, und die neue, auf `RestoreSensor` basierende Wiederherstellung nur den letzten eigenen State versucht hat, ohne Fallback, wenn dieser `"unavailable"` war. `_restored_value()` greift jetzt zusätzlich auf Home Assistants eigene Langzeitstatistik zurück, die den echten letzten Wert trotz der Lücke noch hält; ein konfigurierter Offset wird dabei als bereits enthalten behandelt, statt ein zweites Mal draufaddiert zu werden. Ein zweiter Bug in derselben Änderung — die `_cycling_yesterday`-Sensoren stürzten beim Wiederherstellen ab, weil ihr eigener Aufrufer nicht auf das neue Rückgabeformat umgestellt war — wurde durch denselben Live-Test gefunden und gleich mitbehoben. Gegen echte Hardware verifiziert: Alle Lifetime- und Zyklus-Zähler (inkl. fünf verschiedener konfigurierter Offsets) haben den echten Upgrade mit exakt ihrem vorherigen Wert überstanden, und die zuvor abstürzenden `_cycling_yesterday`-Sensoren liefen nach dem Redeploy des Fixes wieder sauber.

### [3.5.5] - 2026-09-12

Einen gemeldeten Register-Konflikt ab Firmware 3 behoben: Heizkreis-Register 7 wird ab Firmware 3 umgewidmet — vom schreibbaren angeforderten Sollwert zum read-only Wert, den der Regler tatsächlich verwendet — aber der alte schreibbare Sensor (`flow_line_temperature_setpoint`) hatte keine obere Firmware-Grenze und wurde weiterhin parallel zum neuen read-only Sensor (`target_temp_flow_line`) angelegt — beide lesen und schreiben dieselbe Adresse. `flow_line_temperature_setpoint` ist jetzt auf Firmware 1-2 begrenzt, den Bereich, in dem der Name noch stimmt. Details siehe [CHANGELOG_ALL_CHANGES.md](CHANGELOG_ALL_CHANGES.md). [Issue #112](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/112)

### [3.5.4] - 2026-09-09

Eine weitere Home-Assistant-Deprecation-Warnung behoben, gefunden bei der Auswertung der echten System-Logs zweier laufender Installationen nach einem Update auf Home Assistant 2026.9.1: `device_registry.async_get_device()`, genutzt um das übergeordnete Gerät eines Untergeräts für `via_device_id` zu finden, ist deprecated und wird in Home Assistant 2027.8.0 entfernt. Ersetzt durch `async_get_device_by_identifier()`. Gegen echte Hardware verifiziert — die volle Testsuite, ein Live-Entfernen/Neuanlegen des Config-Entry sowie ein kompletter Durchlauf des echten Config-Flows laufen unverändert durch. Details siehe [CHANGELOG_ALL_CHANGES.md](CHANGELOG_ALL_CHANGES.md).

### [3.5.3] - 2026-09-06

Eine Funktionsregression aus dem 3.5.0-Rewrite behoben, gefunden beim Live-Test: Jeder Modbus-Schreibvorgang nutzte FC06 (Write Single Register), das laut Lambdas eigener Protokolldokumentation gar nicht implementiert ist — jeder Schreibvorgang (Raumthermostat-Steuerung, PV-Überschuss-Export, Warmwasser-/Heizkreis-/Kühlkreis-Sollwerte, der generische Register-Schreib-Service) scheiterte mit "Illegal Function". Jedes schreibbare Register nutzt jetzt FC16 (Write Multiple Registers), wie schon der Vor-3.5-Code und wie von Lambda dokumentiert. Details siehe [CHANGELOG_ALL_CHANGES.md](CHANGELOG_ALL_CHANGES.md).

### [3.5.2] - 2026-09-06

Nachzieharbeiten zur 3.5.0-Rewrite-Übernahme: drei Lücken behoben, gefunden bei der Prüfung aller 2.7.x/2.8.x-Bugfixes des Vor-Rewrite-Branches `main` gegen den neu geschriebenen Code — eine `via_device`-Deprecation-Warnung bei Sub-Geräten, ein als echter Wert gelesener `0xFFFF`-Sonderwert ("keine Anforderung"/"kein externer Sensor", z. B. exakt -300,0 °C bei der Außentemperatur) sowie nicht tatsächlich serialisierte Modbus-Lese-/Schreibvorgänge (dieselbe Fehlerklasse wie Issue #105). Details und die neuen Regressionstests siehe [CHANGELOG_ALL_CHANGES.md](CHANGELOG_ALL_CHANGES.md).

### [3.5.0] - 2026-09-06

Übernahme eines von Grund auf neu geschriebenen Codes für die Integration (PR #115): Die Modbus-Schicht wechselt von `pymodbus` zu [`modbus-connection`](https://github.com/home-assistant-libs/modbus-connection)/`tmodbus`, Wärmepumpen und andere Module werden über Index und Objektreferenz statt rekonstruierter entity_id-Strings adressiert (behebt die Fehlerklasse hinter den Issues #93/#107), und Zähler persistieren über normale Home-Assistant-`RestoreSensor`s. Mindest-Home-Assistant-Version ist jetzt 2026.9.0. Vollständige Aufschlüsselung siehe [CHANGELOG_ALL_CHANGES.md](CHANGELOG_ALL_CHANGES.md).

<!-- /lang:de -->
