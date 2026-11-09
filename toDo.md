# ToDo

*Stand 09.11.2026, Branch `feature/lambda-cockpit` (3.7.0)*

## Offen aus dem Lambda Cockpit

- [x] **`sensor.eu08l_hp1_compressor_start_cycling_daily` ist nicht mehr vorhanden** — behoben 09.11.2026: Schalter wirkt nur noch beim Umlegen (`_period_toggle_changed`, Store `lambda_heat_pumps.period_sensors`). (gemeldet 04.11.2026).
  - **Befund (Test-Container):** Die Entität existiert noch, ist aber von der Integration deaktiviert (`disabled_by: integration`, geändert am 04.11. 18:39:21 = Speichern der Optionen). Insgesamt 48 Perioden-Sensoren sind so deaktiviert.
  - **Ursache (seit 3.6.1, nicht durch das Cockpit):** Der Options-Dialog speichert beim ersten Absenden immer auch `period_sensors_enabled` (Standard: aus). Ab dann gleicht `_reconcile_period_sensor_enablement()` (`sensor.py`) bei jedem Laden alle Perioden-Sensoren an den Schalter an und deaktiviert auch solche, die der Nutzer vorher **einzeln aktiviert** hatte. Nur vom Nutzer *deaktivierte* bleiben verschont. Wer die Optionen aus einem anderen Grund speichert (hier: Dashboard-Schalter), verliert also seine einzeln eingeschalteten Tages-/Monatszähler.
  - **Vorschlag:** Nur angleichen, wenn sich der Schalter tatsächlich geändert hat (zuletzt angewendeten Wert pro Eintrag in einem `Store` merken). Ohne gemerkten Wert und mit Schalter „aus“ nichts deaktivieren. Test dazu; Hinweis im Changelog für Nutzer von 3.6.1.
  - **Sofort-Abhilfe für Betroffene:** Entität unter Einstellungen → Entitäten wieder aktivieren, oder den Schalter „Perioden-Energiesensoren aktivieren“ einschalten.

- [x] ~~**Wärmefahrplan-Sensor firmwareabhängig machen.**~~ Bleibt so (Entscheidung 09.11.2026). `schedule_outside_temperature_calc` nur für Firmware anlegen, deren Soll-Vorlauf (5007) die Rückrechnung zulässt. Im Standby meldet die Lambda 0 °C (derzeit abgefangen: Sensor „unbekannt“).
- [ ] **Sporadischer „Konfigurationsfehler“ beim Laden des Cockpits.** „Custom element doesn't exist: lambda-cockpit-card“, obwohl die JS-Datei mit HTTP 200 geladen wird; keine Konsolenfehler. Gehäuft kurz nach einem HA-Neustart, Neuladen der Seite hilft. Reproduzierbar mit dem Playwright-Skript gegen den Test-Container.
  - **Firefox (immer, behoben 09.11.2026, nicht committet):** HA lädt die Karten vor dem eigenen Code und ersetzt in Firefox danach `window.customElements` durch ein Polyfill für „scoped custom element registries“, das die vorher definierten Elemente nicht kennt. Beide Karten melden sich jetzt erneut in der aktuellen Registry an, bis `home-assistant` definiert ist (`lccDefine` / `lecDefine`). Mit Playwright in Firefox und Chrome geprüft.
  - **Chrome/Edge (sporadisch):** beobachten, ob der Fehler mit dieser Änderung auch dort verschwindet.
- [ ] **Screenshot des Cockpits für die Doku** (`docs/docs/Anwender/lambda-cockpit.md`).
- [x] **Options-Screenshot erneuern** (erledigt 09.11.2026): `docs/docs/assets/options_cockpit_de.png` zeigt noch den alten Hilfetext („Ausschalten entfernt das Dashboard nicht“).
- [ ] **Live-Entfernen bestätigen:** Option im laufenden Betrieb ausschalten → Dashboard verschwindet ohne Neustart (bisher nur über Neustart nachgestellt).
- [x] **Release-Seite 3.7 und Changelog** geschrieben 09.11.2026 (`docs/docs/Releases/release-3-7.md`, `CHANGELOG.md`, `CHANGELOG_ALL_CHANGES.md`). Beim Release Datum eintragen.
- [ ] **Doku-Build prüfen:** Bilder innerhalb nummerierter Listen (`lambda-cockpit.md`) im Doku-Check der CI.
- [ ] **Standardwerte der Einstellwerte** (Hysteresen, Spreizung, Heizgrenze, max. Temperaturen) mit den Werkseinstellungen der Lambda abgleichen; derzeit Schätzwerte.

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
