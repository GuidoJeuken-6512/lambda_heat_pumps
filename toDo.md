# ToDo

*Stand 14.11.2026, `main` (3.7.0; Änderungen für 3.7.1 noch nicht released)*

## Offen aus dem Lambda Cockpit

- [x] **`sensor.eu08l_hp1_compressor_start_cycling_daily` ist nicht mehr vorhanden** — behoben 09.11.2026: Schalter wirkt nur noch beim Umlegen (`_period_toggle_changed`, Store `lambda_heat_pumps.period_sensors`). (gemeldet 04.11.2026).
  - **Befund (Test-Container):** Die Entität existiert noch, ist aber von der Integration deaktiviert (`disabled_by: integration`, geändert am 04.11. 18:39:21 = Speichern der Optionen). Insgesamt 48 Perioden-Sensoren sind so deaktiviert.
  - **Ursache (seit 3.6.1, nicht durch das Cockpit):** Der Options-Dialog speichert beim ersten Absenden immer auch `period_sensors_enabled` (Standard: aus). Ab dann gleicht `_reconcile_period_sensor_enablement()` (`sensor.py`) bei jedem Laden alle Perioden-Sensoren an den Schalter an und deaktiviert auch solche, die der Nutzer vorher **einzeln aktiviert** hatte. Nur vom Nutzer *deaktivierte* bleiben verschont. Wer die Optionen aus einem anderen Grund speichert (hier: Dashboard-Schalter), verliert also seine einzeln eingeschalteten Tages-/Monatszähler.
  - **Vorschlag:** Nur angleichen, wenn sich der Schalter tatsächlich geändert hat (zuletzt angewendeten Wert pro Eintrag in einem `Store` merken). Ohne gemerkten Wert und mit Schalter „aus“ nichts deaktivieren. Test dazu; Hinweis im Changelog für Nutzer von 3.6.1.
  - **Sofort-Abhilfe für Betroffene:** Entität unter Einstellungen → Entitäten wieder aktivieren, oder den Schalter „Perioden-Energiesensoren aktivieren“ einschalten.

- [x] ~~**Wärmefahrplan-Sensor firmwareabhängig machen.**~~ Bleibt so (Entscheidung 09.11.2026). `schedule_outside_temperature_calc` nur für Firmware anlegen, deren Soll-Vorlauf (5007) die Rückrechnung zulässt. Im Standby meldet die Lambda 0 °C (derzeit abgefangen: Sensor „unbekannt“).
- [ ] **Sporadischer „Konfigurationsfehler“ beim Laden des Cockpits.** „Custom element doesn't exist: lambda-cockpit-card“, obwohl die JS-Datei mit HTTP 200 geladen wird; keine Konsolenfehler. Gehäuft kurz nach einem HA-Neustart, Neuladen der Seite hilft. Reproduzierbar mit dem Playwright-Skript gegen den Test-Container.
  - **Firefox (immer, behoben in 3.7.0):** HA lädt die Karten vor dem eigenen Code und ersetzt in Firefox danach `window.customElements` durch ein Polyfill für „scoped custom element registries“, das die vorher definierten Elemente nicht kennt. Beide Karten melden sich jetzt erneut in der aktuellen Registry an, bis `home-assistant` definiert ist (`lccDefine` / `lecDefine`). Mit Playwright in Firefox und Chrome geprüft.
  - **Chrome/Edge (sporadisch):** beobachten, ob der Fehler mit dieser Änderung auch dort verschwindet.
- [x] **Hilfeseite je Kachel** (14.11.2026, 3.7.1, nicht released): `docs/docs/Anwender/lambda-cockpit-kacheln.md`, „?“ an jeder Kachel öffnet den Abschnitt in neuem Tab. Bei neuen Kacheln Abschnitt und Anker mitpflegen (`LCC_HELP_URL`, `_help()`).
- [ ] **Screenshot des Cockpits für die Doku** (`docs/docs/Anwender/lambda-cockpit.md`).
- [x] **Options-Screenshot erneuern** (erledigt 09.11.2026): `docs/docs/assets/options_cockpit_de.png` zeigt noch den alten Hilfetext („Ausschalten entfernt das Dashboard nicht“).
- [ ] **Live-Entfernen bestätigen:** Option im laufenden Betrieb ausschalten → Dashboard verschwindet ohne Neustart (bisher nur über Neustart nachgestellt).
- [x] **Release-Seite 3.7 und Changelog** geschrieben 09.11.2026 (`docs/docs/Releases/release-3-7.md`, `CHANGELOG.md`, `CHANGELOG_ALL_CHANGES.md`). Beim Release Datum eintragen.
- [x] **Doku-Build prüfen:** Bilder innerhalb nummerierter Listen (`lambda-cockpit.md`) im Doku-Check der CI. Erledigt: 0 Probleme (13.11.2026).
- [ ] **Standardwerte der Einstellwerte** (Hysteresen, Spreizung, Heizgrenze, max. Temperaturen) mit den Werkseinstellungen der Lambda abgleichen; derzeit Schätzwerte.
- [x] **Dashboard ließ sich nicht entfernen** (gemeldet 13.11.2026): Ein verwaister Eintrag einer gelöschten Konfiguration im Store `lambda_heat_pumps.dashboard` hielt das Dashboard fest. Behoben (3.7.1, nicht released), Test dazu.
- [x] **Simulator `C:\Cursor\modbus_tools`:** Register 5005–5007 und 5105–5107 (Soll-Vorlauf der Heizkreise) ergänzt; ohne sie zeigten Puffer und Heizkreis oben links „–“. Simulator neu starten, damit er sie lädt.
- [ ] **Release 3.7.1** (Climate-Fix, #160, #167, Hinweise aus #163, Heizkreis-Karte zu #157, Vorlauf-Werte zu #156/#128) — gebaut wird erst auf Anweisung. Changelog-Einträge stehen als „unveröffentlicht“.
- [x] **Climate-Fix live geprüft** (13.11.2026): auf HA 2026.9.1 (Port 8124) und 2026.11.1 (Port 8125, schlanke Konfiguration `C:\Cursor\ha_test_2611`): Werte da, keine Veraltet-Warnung im Log. Nach dem Release zusätzlich im Log von .131 kontrollieren.
- [x] **#167 Kompressorstarts heute** (14.11.2026, 3.7.1, nicht released): Kachel unter „Umschaltungen“, AT-Werte in der Kopfzeile; bestehende Dashboards zeigen sie ohne Neuschreiben.
- [ ] **#166 beantworten:** Prototyp einer Karte im Stil des Lambda-Displays. Empfehlung: eigene HACS-Karte, in der Doku verlinkt. Details in der Bugliste.
- [ ] **#165 auf GitHub schließen:** lokal als „nicht geplant“ notiert, auf GitHub noch offen.
- [ ] **Playwright-Skript `ha_session.cjs`** (Scratchpad) nutzt noch Port 8123. Auf Port 8124 umstellen, bevor Browser-Tests laufen.
- [ ] **Schlanke Test-Konfiguration `C:\Cursor\ha_test_2611`** (ohne Datenbank, nur nötige Dateien) mit Container `ha-2611` (HA 2026.11.1, Port 8125). Ist nicht im Repo; bei Bedarf neu anlegen.
- [ ] **Heizkreis ohne eigenen Rücklauffühler** (gemeldet 09.11.2026, Prod-Anlage): `hc1_return_line_temperature` (Register 5003) ist dauerhaft „unbekannt“; Kachel Heizkreis zeigt links ein leeres Feld „–“, Schaltpunkte Heizkreis zeigen „RL –“ und „noch – K“. Ein Klick auf die Kachel öffnet `hc1_flow_line_temperature` (ganze Kachel verknüpft, nicht das Feld).
  - [x] **Leeres Feld ausblenden**, wenn der Heizkreis-Rücklauf keinen Wert hat (3.7.1, nicht released; auch der Heizkreis-Schaltpunkt entfällt).
  - **Ersatz für die Schaltpunkte:** ohne Heizkreis-Rücklauf `hp1_return_line_temperature` verwenden. Vorher bei Lambda klären, ob die Regelung in diesem Fall wirklich nach dem WP-Rücklauf schaltet.

## Später / Verbesserungen

- [x] **Mehrere Heizkreise** umgesetzt (3.7.1, nicht released): Kachel Heizbetrieb je Heizkreis auf der Hauptseite, Reiter je Heizkreis mit Karte „Lambda Heizkreis“, Reparaturmeldung für bestehende Cockpits; bei einem Heizkreis bleibt alles wie bisher. Offen bleibt: **mehrere Wärmepumpen** im Cockpit (derzeit nur HP1, BOIL1, BUFF1, HC1). Für Heizkreis 2/3 gibt es jetzt eine Schritt-für-Schritt-Anleitung in der Doku (Kopie der Karte, `_hc1_` → `_hc2_`); eine Auswahl in der Karte selbst bleibt offen. **Entschieden (13.11.2026):** eigene Heizkreis-Karte plus Reparaturmeldung, die sie nach Bestätigung ins erzeugte Dashboard einfügt. Details, Risiken und Synergien (VL-Werte und Abweichung in der Heizkurve, fehlender Rücklauffühler, Raumfühler je Heizkreis, Bild Heizkörper/Fußbodenheizung) in der Bugliste bei #157.
- [ ] **Mehrere Lambda-Anlagen:** Es gibt nur ein Dashboard `lambda-cockpit`; die zuletzt eingerichtete Anlage gewinnt.
- [ ] **Umbenennungen nach dem Erzeugen** nachführen: Karte löst Entitäten zur Laufzeit über die unique_id auf (Websocket `config/entity_registry/list_for_display`) statt über die beim Erzeugen eingetragenen IDs.
- [ ] **Interne HA-Schnittstellen beobachten:** `hass.data[LOVELACE_DATA]`, `LovelaceStorage` und der Zugriff auf die Dashboard-Sammlung über den Websocket-Befehl `lovelace/dashboards/delete` (`dashboard.py`). Bei jedem HA-Update kurz testen.
- [ ] **Entitäten-Karte:** Erklärtexte (`LEC_INFO`) für weitere Entitäten ergänzen.

## Sonstiges

- [x] **Test-Container `homeassistant-test`** läuft jetzt auf Port 8124 mit dem Config-Ordner `lambda_heat_pumps2_8_6` (HA 2026.9.1). Der Container `homeassistant` (Port 8123) nutzt das Repo als Config, uncommittete Änderungen sind dort sofort aktiv.
- [x] **`BUG_ANALYSE_BRANCH_3.5.md`:** aufgeräumte Fassung ist committet.
- [ ] **`tests/playwright/node_modules`** ist unvollständig (Pakete ohne `package.json`).
