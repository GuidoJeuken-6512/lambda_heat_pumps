# ToDo

*Stand 04.11.2026, Branch `feature/lambda-cockpit` (3.7.0)*

## Offen aus dem Lambda Cockpit

- [ ] **Wärmefahrplan-Sensor firmwareabhängig machen.** `schedule_outside_temperature_calc` nur für Firmware anlegen, deren Soll-Vorlauf (5007) die Rückrechnung zulässt. Im Standby meldet die Lambda 0 °C (derzeit abgefangen: Sensor „unbekannt“).
- [ ] **Sporadischer „Konfigurationsfehler“ beim Laden des Cockpits.** „Custom element doesn't exist: lambda-cockpit-card“, obwohl die JS-Datei mit HTTP 200 geladen wird; keine Konsolenfehler. Gehäuft kurz nach einem HA-Neustart, Neuladen der Seite hilft. Ursache unklar (Ladereihenfolge von `add_extra_js_url`?). Reproduzierbar mit dem Playwright-Skript gegen den Test-Container.
- [ ] **Screenshot des Cockpits für die Doku** (`docs/docs/Anwender/lambda-cockpit.md`).
- [ ] **Options-Screenshot erneuern:** `docs/docs/assets/options_cockpit_de.png` zeigt noch den alten Hilfetext („Ausschalten entfernt das Dashboard nicht“).
- [ ] **Live-Entfernen bestätigen:** Option im laufenden Betrieb ausschalten → Dashboard verschwindet ohne Neustart (bisher nur über Neustart nachgestellt).
- [ ] **Release-Seite 3.7 und Changelog** schreiben.
- [ ] **Doku-Build prüfen:** Bilder innerhalb nummerierter Listen (`lambda-cockpit.md`) im Doku-Check der CI.
- [ ] **Standardwerte der Einstellwerte** (Hysteresen, Spreizung, Heizgrenze, max. Temperaturen) mit den Werkseinstellungen der Lambda abgleichen; derzeit Schätzwerte.

## Warten auf Lambda-Firmware (nicht sichtbar, nicht dokumentiert)

- [ ] **PV-Erhöhungen 2051 / 3051 / 5053** (Modbus-Doku V006): `PV_OFFSET_FIRMWARE_VERSIONS` in `const.py` setzen **und** die Lesebereiche in `lambda_modbus/ranges.py` erweitern (Boiler/Puffer 50–51, Heizkreis 50–53).
- [ ] **„Warmwasser sofort“ (2006)** und **„Zirkulation starten“ (2005 schreiben)**: Register, Entitäten, Knöpfe im Cockpit.
- [ ] **Raum-Soll nach Abtauungen anheben:** Logik ist im Coordinator vorhanden, Option im Options-Dialog ausgeblendet. Beim Einblenden: Abtauungen des Tages über einen Neustart retten (derzeit Neuzählung).

## Später / Verbesserungen

- [ ] **Mehrere Wärmepumpen / Heizkreise** im Cockpit (derzeit nur HP1, BOIL1, BUFF1, HC1; andere nur per Karten-YAML).
- [ ] **Mehrere Lambda-Anlagen:** Es gibt nur ein Dashboard `lambda-cockpit`; die zuletzt eingerichtete Anlage gewinnt.
- [ ] **Umbenennungen nach dem Erzeugen** nachführen: Karte löst Entitäten zur Laufzeit über die unique_id auf (Websocket `config/entity_registry/list_for_display`) statt über die beim Erzeugen eingetragenen IDs.
- [ ] **Interne HA-Schnittstellen beobachten:** `hass.data[LOVELACE_DATA]`, `LovelaceStorage` und der Zugriff auf die Dashboard-Sammlung über den Websocket-Befehl `lovelace/dashboards/delete` (`dashboard.py`). Bei jedem HA-Update kurz testen.
- [ ] **Entitäten-Karte:** Erklärtexte (`LEC_INFO`) für weitere Entitäten ergänzen.

## Sonstiges

- [ ] **Test-Container `homeassistant-test`** läuft mit dem Branch und eingeschaltetem Cockpit. Sicherung der Integration 3.6.1 und der `.storage`-Dateien: `C:\Users\Guido\AppData\Local\Temp\claude\bd4e34e3e3afd108\4c63a84f-7db4-481e-b1c8-d6eec93d75aa\scratchpad\ha_test_backup`.
- [ ] **`BUG_ANALYSE_BRANCH_3.5.md`:** aufgeräumte Fassung liegt uncommittet im Arbeitsverzeichnis.
- [ ] **`tests/playwright/node_modules`** ist unvollständig (Pakete ohne `package.json`).
