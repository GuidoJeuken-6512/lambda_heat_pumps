# Analyse der offenen Bug-Issues gegen Branch `3.5`

- **Stand:** 15.11.2026 (Abgleich mit GitHub; Version 3.7.1)
- **Geschlossene Issues (V3.6.1):** #82, #85, #90, #94, #95, #104, #119, #120, #121, #122 (Duplikat #85), #132, #133, #134, #136, #140, #141 (Duplikat #121), #144. 
- **Geschlossen nach V3.6.1:** #138 (Doku Hydraulic Card), #142 (gelöst), #149 (tmodbus-Anforderung, 3.6.2)
- **Geschlossen:** #153 (behoben in 3.7.0), #105 und #161 (GitHub geschlossen), #160, #157 und #167 (behoben in 3.7.1, GitHub geschlossen 14.11.2026), #166 (beantwortet: keine zweite Karte, Verlinkung angeboten; geschlossen 14.11.2026), #165 (nicht geplant), #137 (Verhalten der Lambda), #168 und #170 (behoben in 3.7.2, unveröffentlicht) – alle mit Kommentar geschlossen 15.11.2026
- **Offen, noch in Arbeit:** #152, #151, #143, #101, #128 und die Cockpit-Issues (siehe Abschnitt unten)
- **Technische Schulden (Enhancement):** #128, #101, #105 (Tests/Regressionen ausstehend)
- **Register ohne Werte nach Firmware:** eigene Auswertung in [`REGISTER_OHNE_WERTE.md`](REGISTER_OHNE_WERTE.md) (44 Issues, Tabelle Firmware → Register, F26–F29).

---

## Offene Issues

| Issue | Titel | Status | Priorität |
|---|---|---|---|
| [#137](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/137) | E-Manager-Sollleistung ≠ 0 ohne PV-Überschuss | Verhalten der Lambda; **GitHub geschlossen** 15.11.2026 mit Kommentar | – |
| [#153](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/153) | Außentemperatur „unbekannt“ bei 0 °C | **FIXED** in 3.7.0 (GitHub geschlossen) | – |
| [#152](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/152) | `ambient_temperature` fehlt nach 3.6.1 | Firmware-Sperre `"1-7"`; Rückfrage Firmware und Werte vor dem Update | niedrig–mittel |
| [#151](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/151) | PV-Modus endet nicht, Psoll springt auf 0 (2.6.0) | Lambda-Verhalten wie #137; 0-Sprünge vermutlich evcc parallel | niedrig |
| [#143](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/143) | Viele Entitäten ohne Messwert (Puffer) | Feedback zu Screenshot (EU13, V1.0.4-3K) | niedrig–mittel |
| [#101](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/101) | Solarthermiemodul wird nicht erkannt | Logs fehlen; Timeout-Logik prüfen (F9) | niedrig |
| [#105](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/105) | E-Manager-Register springt auf 0 | **Geschlossen** (GitHub), Ursache zweiter Modbus-Client (evcc) | – |
| [#128](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/128) | Heizkurve: Abweichung zum Sollwert (Enhancement) | Abweichung Soll − berechnet im Cockpit sichtbar (3.7.1); Abweichungs-Sensor (F17) offen | niedrig |

---

## Details

### #153: Außentemperatur „unbekannt“ bei 0 °C

**Status:** Bug der Integration, behoben in 3.7.0 (Fix auf main als 3.6.3, nicht einzeln veröffentlicht).

Seit 3.5.2 (Commit c2b07d1) filterte `Ambient.temperature` (Register 2) zusätzlich 0xFFFF als „kein externer Fühler“. Bei Faktor 0,1 ist 0xFFFF aber −0,1 °C, ein echter Messwert. Um den Gefrierpunkt sprang der Sensor deshalb bei jedem Abruf mit −0,1 °C auf „unbekannt“. Die CSV des Melders bestätigt das: 32 × unbekannt, 24 × −0,2, 8 × 0,0, kein einziges Mal −0,1. Ein fehlender Fühler meldet −3000 (0xF448, `NO_SENSOR`) und wird weiter gefiltert.

**Fix:** `NO_REQUEST` bei `Ambient.temperature` entfernt (`lambda_modbus/general.py`); Test `test_a_no_request_or_no_sensor_register_reads_unknown` erwartet jetzt −0,1 °C. Die Puffer-Anforderungsregister und die Heizkreis-Betriebsart behalten den Filter (dort bedeutet −1 wirklich „keine Anforderung“).

**Nächste Schritte:** Im Issue antworten (Fix in 3.7.0), danach schließen.

---

### #152: `ambient_temperature` fehlt nach 3.6.1

**Status:** Rückfrage nötig.

Die Entität wird seit 3.6.1 nur für Firmware bis V0.0.9-3K (`firmware_versions=("1-7",)`, `sensor.py`) angelegt, weil neuere Steuerungen Register 2 nur mit 0x8000 beantworten. HA zeigt sie deshalb als „nicht mehr bereitgestellt“. Nicht in Release-Seite oder Firmware-Doku erwähnt (Doku-Lücke).

**Nächste Schritte:** Firmware am Display und in der Integration erfragen, und ob der Sensor vor dem Update echte Werte zeigte. Falls ja: Sperre zu streng → anpassen. Sonst: Ersatz `ambient_temperature_calculated` / `ambient_temperature_1h` nennen, verwaiste Entität löschen.

---

### #151: PV-Modus endet nicht, Psoll springt auf 0

**Status:** Vermutlich kein Bug der Integration (Melder nutzt 2.6.0).

Psoll bleibt stehen und der PV-Modus endet nicht: Logik der Lambda (wie #137). Die kurzen 0-Werte passen zum Hinweis eines anderen Nutzers (#105, #151), dass sie ohne evcc verschwinden.

**Nächste Schritte:** Update auf 3.6.1 empfehlen; Register 102 nur von einer Quelle schreiben lassen (evcc **oder** Integration); E-Manager-Einstellungen prüfen.

---

### #137: E-Manager-Sollleistung ≠ 0 ohne PV-Überschuss

**Status:** Verhalten der Lambda, nicht der Integration. Auf GitHub mit Kommentar geschlossen (15.11.2026).

Die PV-Überschuss-Dokumentation erklärt jetzt, dass die Sollleistung (`emgr_power_consumption_setpoint`) nur im Betriebsmodus "Automatik" berechnet wird. Im Modus "Manuell" ist die Sollleistung immer 0. Der Wert kommt direkt von der Lambda (Register 1087), und die Integration schreibt nur den Überschusswert.

---

### #143: Viele Entitäten ohne Messwert (Puffer)

**Status:** Feedback zu Screenshot ausstehend (EU13, V1.0.4-3K)

Register 3005–3009 (Puffer-Temperatur) und weitere zeigen auf einer EU13 mit Firmware V1.0.4-3K keine Werte (erscheinen als "unbekannt" in Home Assistant). Das passt zur Auswertung in [`REGISTER_OHNE_WERTE.md`](REGISTER_OHNE_WERTE.md), die zeigt, dass diese Register mit dieser Firmware und Steuerungsgeneration nicht vorhanden sind.

Der Melder hat einen Screenshot gepostet, aber die Bildbeschreibung ist unklar. **Nächste Schritte:** Rückfrage, ob es um alle 3005–3009 geht oder nur einige, und ob die Entitäten mit der richtigen Firmware danach vorhanden sind.

---

### #101: Solarthermiemodul wird nicht erkannt

**Status:** Logs fehlen; Schwachstelle in der Modulerkennung bekannt

Bei der Modulerkennung kann ein Timeout bei der Antwort des Solar-Wärmemodul-Registers (1010) als "Modul fehlt" fehlinterpretiert werden (`module_auto_detect.py:64`). Das ist eher selten, und ein Reload der Integration hilft meist. Ein Retry bei Timeout würde helfen (F9).

**Nächste Schritte:** Im Issue nach neueren Logs fragen (mit Zeilenzeiten), oder mit einem Reload testen, ob das Modul dann erkannt wird.

---

### #105: E-Manager-Register springt auf 0

**Status:** Ursache wahrscheinlich gefunden: zweiter Modbus-Client (evcc)

Der Melder berichtete, dass das E-Manager-Register (`emgr_actual_power`, Register 102) zwischendurch auf 0 springt. Im Retest 18.10. mit Modus "Manuell" war das nicht zu beobachten. Im Modus "Automatik" (bei aktiviertem PV-Überschuss) könnte das Verhalten anders sein.

**Update 11/2026:** Ein Nutzer (alphabravocharly72) berichtet, dass die 0-Werte verschwinden, sobald evcc nicht mehr mit der Lambda verbunden ist. Zwei Schreiber auf Register 102 überschreiben sich gegenseitig.

**Nächste Schritte:** Beim Melder nachfragen, ob evcc oder ein anderer Modbus-Client parallel läuft; mit #151 verknüpfen. Doku-Hinweis „nur ein Schreiber für Register 102“ erwägen.

---

### #128: Heizkurve – Abweichung zum Sollwert

**Status:** Doku korrigiert; Abweichungs-Sensor offen (F17)

Die Heizkurven-Abweichung zwischen berechneter und realer Vorlauftemperatur ist bekannt und dokumentiert. Die Integration stellt einen berechneten Sollwert zur Verfügung, die echte Abweichung hängt von der Pumpe, der Regelung und der Hysterese ab.

Ein Abweichungs-Sensor (Soll − Ist) würde helfen, Regelprobleme zu erkennen (F17), ist aber eine Enhancement. Ein Tester hat bestätigt, dass das Konzept sinnvoll ist.

**Nächste Schritte:** Wenn Zeit vorhanden, einen Sensor-Template schreiben und in die Doku aufnehmen.

---

## Lambda Cockpit: offene Issues (Stand 15.11.2026)

Neues Dashboard aus 3.7.0. Die Meldungen stammen vom 10. bis 15.11.2026.

| Issue | Titel | Einordnung | Priorität |
|---|---|---|---|
| [#160](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/160) | Entitäten-Suche: Eingabe schließt nach jedem Buchstaben | **FIXED** in 3.7.1, Suchfeld bleibt erhalten; GitHub geschlossen 14.11.2026 | mittel |
| [#162](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/162) | Raumtemperatur an Lambda immer ausgegraut | **Offen**; Raumfühler wird ab 3.7.1 je Heizkreis zugeordnet (kann helfen). Entitätsliste und Optionen vom Melder anfordern | mittel |
| [#157](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/157) | Nur ein Heizkreis sichtbar (3 vorhanden); PV-Symbol schwer zu sehen | **FIXED** in 3.7.1: bei mehreren Heizkreisen Kachel Heizbetrieb je Heizkreis auf der Hauptseite, Reiter je Heizkreis mit Karte „Lambda Heizkreis“; Reparaturmeldung für bestehende Cockpits. PV-Symbol bleibt so (eigenes Issue, falls gewünscht); GitHub geschlossen 14.11.2026 | mittel |
| [#156](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/156) | Keine Heizkurvendaten im Dashboard; Wunsch: VL berechnet, Vorlauf-Offset, VL Soll und VL Ist in der Heizkurve | **Teils FIXED** in 3.7.1: Vorlauf-Werte als Zeile unter der Heizkurve. **Bleibt offen:** Werte in die Grafik der Heizkurve (geplant 3.7.2); fehlende Daten nach dem Start (Ursache unklar) | niedrig–mittel |
| [#163](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/163) | Schaltpunkte: Kopie-Werte, Dauerlauf, Puffer-Status, Warmwasser-Eco, Laufzeit am ersten Tag | **Teils FIXED** in 3.7.1: Punkte 1, 4, 6, 7. Offen: 2, 3, 5; Issue bleibt offen (noch nicht kommentiert) | mittel |
| [#159](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/159) | Volumenstrom bei den Verdichter-Werten anzeigen | **Offen** (Wunsch); Sensor existiert bereits | niedrig |
| [#167](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/167) | Kompressorstarts täglich unter „Laufzeiten heute“ | **FIXED** in 3.7.1: Kachel „Kompressorstarts heute“ im oberen Bereich, AT-Werte in die Kopfzeile; GitHub geschlossen 14.11.2026 | niedrig–mittel |
| [#169](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/169) | PV-Überschuss mit Kodierung „neg“ zeigt bei Netzbezug Überschuss | **Offen** (Bug, neu 15.11.2026); Karte kennt die Kodierung nicht (wie #155). Hängt an „Funktionen live lesen“ | mittel |
| [#170](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/170) | Brauchwasser: Temperatur oben und unten zeigen | **FIXED** in 3.7.2 (unveröffentlicht): Speicher zeigt oben und unten; GitHub geschlossen 15.11.2026 | niedrig |
| [#166](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/166) | Prototyp: Karte im Stil des Lambda-Displays (alle Heizkreise) | **Beantwortet und geschlossen** 14.11.2026: keine zweite Karte im Projekt, Verlinkung angeboten | – |
| [#165](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/165) | Heizkreise über Register 5006 schaltbar machen | **Nicht geplant** (wie #31, #98, #125, #136); GitHub geschlossen 15.11.2026 | – |
| [#168](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/168) | „Aufnahme“ zeigt 0,00 kW, wenn der Leistungssensor in kW angezeigt wird (BMeyendriesch, EU15L, 3.7.0) | **FIXED** in 3.7.2 (unveröffentlicht): `_n()` rechnet Leistung, Energie und Laufzeit nach der Einheit um, siehe Details; GitHub geschlossen 15.11.2026 | mittel |

Nicht cockpit-spezifisch, aber neu: [#161](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/161) (evcc und Register 102). Ursache wie bei #105: zwei Quellen schreiben in Register 102. Ein Melder hat es gelöst, indem er die PV-Option der Integration abgeschaltet hat und nur evcc schreiben lässt. Einordnung bei #105.

### #160: Entitäten-Suche schließt nach jedem Buchstaben

**Status:** behoben in 3.7.1.

Die Entitäten-Karte baute bei jeder Eingabe und bei jedem HA-Update (alle 5 s) die ganze Ansicht neu auf. Das Suchfeld wurde ersetzt, verlor den Fokus, und auf dem Handy schloss die Tastatur. Jetzt entsteht das Gerüst mit dem Suchfeld einmal; danach werden nur Zähler und Liste erneuert. Mit Playwright in Chrome und Firefox geprüft: alte Karte verliert Fokus und Eingabe, neue behält beides.

**Nächste Schritte:** mit 3.7.1 ausliefern, dann im Issue antworten.

---

### #162: Raumtemperatur an Lambda immer ausgegraut

**Status:** offen. Der Melder hat die Option in der Integration und in der Lambda aktiviert; nach Aktivierung im Code ist der Regler aktiv, der Raumwert wird aber nicht angezeigt.

Zwei verschiedene Dinge sind hier im Spiel:
- **Raum-Soll-Regler:** Die Karte zeigt ihn nur, wenn die Entität `number…hc1_target_room_temperature_number` existiert (`_numCtl`).
- **Raum-Istwert:** Er kommt vom Raumfühler, den die Integration in den Optionen unter der Raumthermostat-Steuerung bekommt. Die Karte zeigt ihn nur, wenn diese Option aktiv ist.

**Nächste Schritte:** Vom Melder die Entitätsliste dieser beiden Entitäten und die Optionen erfragen. Dann klären, ob „ausgegraut“ eine fehlende Entität oder ein Zustand „nicht verfügbar“ ist.

---

### #157: Nur ein Heizkreis sichtbar; PV-Symbol

**Status:** bekannte Grenze, PV-Symbol als Wunsch.

Das Cockpit zeigt wie im Original nur Heizkreis 1 (siehe toDo „Mehrere Wärmepumpen / Heizkreise“). Zwei Melder (#157, maeffjus) haben Heizkreis 2 in der Karten-YAML nicht nutzen können, weil die Karte die Entitäten nur für Heizkreis 1 kennt.

Das PV-Symbol bei den Schaltpunkten ist nur eine Anzeige. Platzierung ist Geschmackssache.

**Umgesetzt am 13.11.2026:** Schritt-für-Schritt-Anleitung in `docs/docs/Anwender/lambda-cockpit.md`: Karte kopieren, `_hc1_` durch `_hc2_` ersetzen, Tabelle der Heizkreis-Schlüssel, Hinweis zum Bild (immer Fußbodenheizung).

**Nächste Schritte:** Im Issue auf die Anleitung verweisen. Eine Auswahl in der Karte bleibt ein größerer Umbau.


#### Lösungsvarianten (13.11.2026)

| | Variante | Für den Nutzer | Aufwand | Risiko |
|---|---|---|---|---|
| A | Option `heating_circuit: 2` in der Cockpit-Karte; die Karte sucht die Entitäten des Heizkreises selbst | eine Zeile YAML, aber weiter ein ganzes Cockpit je Heizkreis | klein | gering |
| B | Eigene Karte `custom:lambda-heating-circuit-card` mit `circuit: 2`: Hydraulik-Kachel, Heizkurve mit Offset, Schaltpunkte Heizkreis, Heizgrenze, max. Vorlauf | kleine Karte, beliebig oft ins Dashboard ziehbar | mittel | gering bis mittel |
| C | Auswahl HK1/HK2/HK3 im Cockpit selbst | alles in einem Dashboard | mittel | mittel (Umbau für alle) |
| D | Integration ergänzt das erzeugte Dashboard um eine Heizkreis-Karte (B) je weiterem Heizkreis | kein Einrichten | klein, wenn B existiert | siehe unten |

**Umgesetzt am 13.11.2026 (3.7.1):** Heizkreis-Karte als Unterklasse der Cockpit-Karte in derselben Datei (keine neue JS-Datei), gemeinsame Bausteine `_hcTile`, `_spHc`, `_vlRow`; bei mehreren Heizkreisen Kachel je Heizkreis im Cockpit (`heating_circuits` in der Karten-Konfiguration) und ein Reiter je Heizkreis (Entscheidung Nutzer 13.11.2026: bei einem Heizkreis keine Reiter); Reparatur `dashboard_heating_circuits` für bestehende. Cockpit vor/nach dem Umbau verglichen: einzige Änderung ist die neue Vorlauf-Zeile.

**Entscheidung:** B + D. D wird nicht automatisch ausgeführt: Bei mehr als einem Heizkreis erscheint eine Reparaturmeldung „Heizkreise 2/3 zum Lambda Cockpit hinzufügen“. Erst die Bestätigung schreibt das Dashboard neu; der Dialog warnt, dass eigene Änderungen am Cockpit verloren gehen. Neuinstallationen bekommen die Heizkreis-Karten direkt. Muster: vorhandene Reparatur mit Bestätigung (`repairs.py`, Neustart).

**Risiken für bestehende Nutzer und Gegenmaßnahmen:**
- Eigene Änderungen am erzeugten Dashboard gehen beim Neuschreiben verloren → nur nach Bestätigung (siehe oben), `DASHBOARD_LAYOUT_VERSION` nicht für alle erhöhen.
- `async_write_dashboard` schaltet nur die Entitäten von Ansicht 0, Karte 0 ein (`dashboard.py`) → auf alle erzeugten Karten ausweiten, sonst bleiben Werte von HK2/3 leer.
- Raumfühler gibt es nur für HK1 (`_external_entities`) → Fühler je Heizkreis aus `room_temperature_entity_{n}`.
- Neue JS-Datei → `lccDefine` (Firefox-Registry) gleich nutzen, in `FRONTEND_CARDS` eintragen.
- Nicht betroffen: eigene Dashboards, die nach der Doku kopierten Heizkreis-Karten, Nutzer mit einem Heizkreis.

**Vorhandene Bausteine:** `resolve_entities(hass, entry, indexes={"hc": 2})` löst schon andere Heizkreise auf, wird aber noch nirgends so aufgerufen. Anzahl der Heizkreise: `entry.runtime_data.counts["hc"]`. Die Darstellung steckt heute in drei Methoden der Cockpit-Karte (Heizkreis-Teil von `_ctrlTiles`, `_tileHeizkurve`, Heizkreis-Block in `_tileSchaltpunkte`); diese als gemeinsame Funktionen herauslösen, die Cockpit und Heizkreis-Karte beide nutzen.

**Mehrwert für andere offene Punkte (gleiche Kacheln, einmal umgesetzt für Cockpit und Heizkreis-Karte):**
- **#156:** VL berechnet, Vorlauf-Offset, VL Soll und VL Ist in der Heizkurve.
- **#128:** Abweichung zwischen dem echten Soll-Vorlauf der Lambda (`hc_soll`, Register 5007) und der Kurve aus der Kopie (`curve_calc`) sichtbar machen. Passt zum Hinweis aus #163 Punkt 7 (Kurvenkopie prüfen).
- **#163 Punkt 4 / toDo „Heizkreis ohne Rücklauffühler“:** leeres RL-Feld und Heizkreis-Block der Schaltpunkte ausblenden, wenn der Fühler fehlt.
- **#162:** Raumfühler je Heizkreis richtig zuordnen; kann den „ausgegrauten“ Raumwert erklären oder beheben (Ursache noch beim Melder klären).
- **#157 (maeffjus):** Option `type: floor | radiator` für das Bild (Fußbodenheizung oder Heizkörper).
- Nicht passend: #113 (Kühl-Soll schreiben, Register mit Zeitlimit), #77 (Spreizung der Wärmepumpe, nicht des Heizkreises), #165 (nicht geplant).

**Prüfung:** Die bestehende Testseite mit nachgebauten HA-Daten (Playwright, Chrome und Firefox) vor und nach dem Herauslösen vergleichen, damit das Cockpit für bestehende Nutzer gleich aussieht. pytest: Dashboard mit zwei Heizkreisen (`controller.install(5100)`), Reparaturmeldung, Bestätigung schreibt die Heizkreis-Karte.

---

### #156: Keine Heizkurvendaten im neuen Dashboard

**Status:** Der Melder bestätigt, dass es nach mehreren Neustarts geht. Ursache offen.

Vermutlich lädt die Karte, bevor die Werte der Heizkurve als Zustände vorliegen, und zeigt dann keine Kurve. Ein Neuladen hilft.

**Vorschlag des Melders (AndiBo62):** In der Heizkurven-Anzeige zusätzlich die Vorlauf-Werte zeigen: **VL berechnet**, **Vorlauf-Offset**, **VL Soll** und **VL Ist** (aktuelle Vorlauftemperatur). Dann lassen sich Konfiguration und Steuerung im Dashboard direkt vergleichen. Der Melder hat dafür einen eigenen Graphen mit Soll- und Ist-Linie gebaut.

**Umgesetzt in 3.7.1:** Zeile unter der Kurve mit VL berechnet, VL Soll, VL ist und Soll − berechnet (ab 1 K hervorgehoben).

**Entschieden (14.11.2026): Issue bleibt offen.** Der Melder zeigt die Werte direkt in der Grafik (Screenshot: Liste oben links, Soll gestrichelt, Ist als rote Linie). Geplant für 3.7.2:
- Waagerechte Linien: VL Soll gestrichelt gelb, VL ist rot; VL berechnet als Punkt im Schnitt der AT-Linie mit der Kurve.
- Werteliste oben links im Diagramm (VL berechnet, Offset, VL Soll, VL ist, Abweichung ab 1 K hervorgehoben) in der Farbe der Linien; die Zeile unter der Kurve entfällt.
- y-Achse um VL ist und VL Soll erweitern, mit Untergrenze (ausgekühlter Vorlauf im Stillstand).
- Fehlender Wert: keine Linie, „–“ in der Liste. Ohne PV-Offset (nur mit unveröffentlichter Firmware).
- Prüfen mit flacher und steiler Kurve, Desktop und Handy; gilt auch für die Heizkreis-Reiter.

**Stützpunkte:** Die drei Kästchen unter der Kurve sind schon mit `heating_curve_cold/mid/warm_outside_temp` verknüpft; ein Klick öffnet den Wert zum Ändern. Beschrieben auf der Hilfeseite im Abschnitt Heizkurve (15.11.2026); ein ✎ in der Karte entfällt, dafür gibt es das „?“.

**Weiter offen:** fehlende Kurvendaten nach dem Start; mit dem Test-Container und einem Neustart nachstellen, Zusammenhang mit dem sporadischen Konfigurationsfehler prüfen.

**Nachtrag 14.11.2026 (AndiBo62):** Wunsch, auch **AT ist** in die Heizkurve einzutragen (bisher AT berechnet und AT Wärmefahrplan). Mit in die Grafik-Umsetzung nehmen. Außerdem meldet er „Ungereimtheiten mit der PV-Überschuss-Steuerung“ und bittet um ein Gespräch; möglicherweise derselbe Punkt wie #169. Antwort steht aus.

---

### #163: Schaltpunkte: Beobachtungen von Sturmi77

**Status:** mehrere berechtigte Punkte. Sturmi77 hat die Kachel über Tage mit dem Verlauf seiner Anlage verglichen (EU10L, Puffer, Boiler, ein Heizkreis mit Mischer).

1. **Kopie-Werte mit Standardwerten:** Die Einstellwerte (Hysteresen, Offset, Spreizung, Heizgrenze) werden mit Standardwerten angelegt. Der Hinweis „bitte vom Display übernehmen“ erscheint nur, wenn die Entitäten fehlen. Sieben von zwölf Werten standen einen Tag lang falsch. **Vorschlag:** Hinweis anzeigen, solange die Werte nie geändert wurden, oder die Werte als „nicht abgeglichen“ kennzeichnen. Passt zum offenen Punkt „Standardwerte der Einstellwerte“ in der toDo.
2. **Dauerlauf:** Die Pumpe moduliert auf Soll minus Spreizung, und die Kachel zeigt „Stopp ab Soll“. **Vorschlag:** Hinweis „Modulationsziel = Soll − Spreizung“.
3. **Puffer „läuft“:** Die Karte markiert den Puffer als laufend, sobald die Betriebsart Heizen ist. **Vorschlag:** `buf_state` oder die Anforderung des Puffers verwenden.
4. **Heizkreis ohne Rücklauffühler:** bekannt, siehe toDo „Heizkreis ohne eigenen Rücklauffühler“.
5. **Warmwasser in der Eco-Zeit:** Die Kachel rechnet mit der Solltemperatur 50 °C, auch in der Eco-Absenkung (−3 K) und außerhalb der Ladezeiten. Abends steht „Start-Bedingung erfüllt“, obwohl die Pumpe zu Recht nicht lädt.
6. **Laufzeiten am ersten Tag:** Die Tageszähler starten mit der Installation. Die Zeit davor zählt als „Ruhe/Sonst.“.
7. **Wärmefahrplan-Verschiebung bei falscher Kurvenkopie (Nachtrag):** Bei ausgeschaltetem Wärmefahrplan zeigte der Sensor −1 K Verschiebung. Ursache: Der Kurvenpunkt 0 °C wurde am Display geändert, die Kopie in HA nicht. **Vorschlag:** Hinweis, dass eine Verschiebung auch auf eine nicht passende Kurvenkopie hinweisen kann. Bei ausgeschaltetem Wärmefahrplan sollte der Sensor ±0,4 K um „AT berechnet“ liegen; das ist ein guter Test für die Kopie.

**Umgesetzt am 13.11.2026:**
- Punkt 1: Hinweis „mit dem Display abgleichen“ erscheint jetzt auch, wenn die Kopie-Werte vorhanden sind; pro Browser ausblendbar.
- Punkt 6: Doku erklärt die Laufzeiten am Installationstag.
- Punkt 7: Hinweis unter der Heizkurve bei angezeigter Verschiebung; Doku beschreibt den Sensor als Kontrolle der Kurvenkopie.

**Offen:** Punkte 2 (Modulationsziel) und 3 (Puffer-Status) beruhen auf Annahmen über die Regelung der Lambda; erst mit Lambda klären. Punkt 5 (Warmwasser-Eco) braucht Daten zur Eco-Zeit.

---

### #159: Volumenstrom bei den Verdichter-Werten

**Status:** Wunsch. Der Sensor existiert (`hp1_volume_flow_heat_sink` bzw. `…energy_source`), die Karte zeigt ihn nicht.

Der Melder schlägt vor, den Wert unter dem Ventil im Heizen- bzw. Warmwasser-Bild anzuzeigen. Die Karten-Kacheln sind groß, das Layout müsste dafür schmaler werden.

**Nächste Schritte:** Anzeige unter dem Ventil prüfen. Die Kacheln wären dann nicht mehr frei wählbar; das bleibt eine Entscheidung.

---

### #167: Kompressorstarts täglich im Cockpit

**Status:** Wunsch (14.11.2026). In „Laufzeiten heute“ stehen „Starts Heizen“, „Starts WW“ und „Umschaltungen“; gewünscht ist ein vierter Zähler „Kompressorstarts“, im gleichen Stil, mit Verlauf beim Anklicken.

Der Sensor existiert: `sensor.*_hp1_compressor_start_cycling_daily`. Er gehört aber nicht zu den Zählern, die das Cockpit eingeschaltet hält (`COCKPIT_COUNTER_KEYS` in `const.py`). Ohne „Perioden-Energiesensoren aktivieren“ ist er deshalb meist deaktiviert.

**Umgesetzt (14.11.2026, 3.7.1):** Kachel „Kompressorstarts heute“ in einer fünften Zeile unter „Umschaltungen“, gleiche Größe wie die übrigen; die drei AT-Werte stehen dafür in der Kopfzeile neben dem Betriebszustand. Höhe des oberen Bereichs in Chrome und Firefox bei 1100, 700 und 390 px gleich oder kleiner als vorher. Test für ein Dashboard aus 3.7.0.

**Umsetzung:**
- Slot `starts_vd` → `compressor_start_cycling_daily` in `dashboard.py` (`_SLOTS`) und in `_resolveMap` der Karte.
- `compressor_start_cycling_daily` in `COCKPIT_COUNTER_KEYS` aufnehmen, damit er mit dem Cockpit eingeschaltet wird.
- Vierter Chip in `_tileRuntime`, Texte de/en.
- **Bestehende Dashboards:** Die eingetragene Entitäten-Liste kennt den neuen Slot nicht. Die Karte sucht Slots aus `LCC_LATE_KEYS` selbst; die Integration schaltet den Zähler beim Start ein (`_LATE_SLOTS` in `dashboard.py`). Kein Neuschreiben nötig.

---

### #166: Prototyp einer Karte im Stil des Lambda-Displays

**Status:** Frage an den Maintainer (14.11.2026), kein Fehler. Manuel2030 hat eine Karte gebaut, die sich an der Bedienoberfläche des Reglers orientiert: Übersicht mit allen Heizkreisen, Detailansicht je Modul, Bedienung erst nach Bestätigung, eigene Grafiken ohne Lambda-Logos. Getestet mit EU13L, 3.7.0, drei Heizkreisen.

Angeboten sind zwei Wege:
1. Eigene Karte in einem eigenen Repo (HACS), in der Doku unter „Vorlagen“ verlinkt wie die Heat Pump Hydraulic Card; Pflege beim Autor.
2. Einzelne Teile per PR ins Cockpit, z. B. alle Heizkreise oder Heizkörper-/FBH-Grafik.

**Einordnung:** Die Punkte aus Weg 2 sind mit 3.7.1 schon umgesetzt (Kachel je Heizkreis, Reiter je Heizkreis, `heating_type: radiator`). Weg 1 passt besser: keine Pflege im Cockpit, keine doppelte Bedienlogik. Für die Antwort an den Autor wichtig: Entitäten über die unique_id finden (wie `_resolveMap` der Cockpit-Karte), nicht über die entity_id; die Slot-Namen der Integration bleiben stabil.

**Nächste Schritte:** Antwort mit Empfehlung Weg 1; Verweis auf 3.7.1 (Heizkreise) erst nach dem Release.

---

### #169: PV-Überschuss mit Kodierung „neg“

**Status:** Bug der Karte (15.11.2026, Qowy, 3.7.1). Gleiches Thema wie #155 (vom Melder ohne Kommentar geschlossen).

Mit „neg“ schickt die Integration den Wert vorzeichenbehaftet an Register 102; die Lambda verhält sich laut Melder richtig. Die Karte wertet aber `emgr_actual_power > 0` immer als Überschuss. Bei „neg“ ist das Netzbezug, und das Cockpit zeigt dann PV-Überschuss an (Kachel und „PV aktiv“ bei den Schaltpunkten).

**Ursache dahinter:** Die Karte bekommt die Funktionen (`features`) nur beim Schreiben des Dashboards. Die Kodierung fehlt dort ganz, und wer PV-Überschuss oder Raumthermostat später ein- oder ausschaltet, sieht im Cockpit weiter den alten Stand.

**Vorschlag:** Kleiner Websocket-Befehl der Integration (z. B. `lambda_heat_pumps/cockpit_features` mit `config_entry`), den die Karte beim Laden abfragt: Raumthermostat, PV-Überschuss, Kodierung. Das Dashboard muss dafür nicht neu geschrieben werden, und eigene Dashboards profitieren mit. In der Karte bei „neg“ das Vorzeichen umdrehen. Vorher mit dem Melder klären, welches Vorzeichen `emgr_actual_power` bei „neg“ für Überschuss liefert (Verlauf oder Screenshot).

---

### #170: Brauchwasser oben und unten

**Status:** behoben in 3.7.2 (unveröffentlicht), GitHub geschlossen 15.11.2026. Wunsch vom 15.11.2026 (tilmancwoerz-web): Der Puffer zeigt oben und unten, das Brauchwasser nur oben.

Der Slot `ww_low` (`boil1_actual_low_temperature`) steht schon im erzeugten Dashboard, die Kachel zeichnet ihn nur nicht. **Umsetzung (klein):** zweites Feld unten im Speicher, wie beim Puffer; ohne Wert kein Feld. Bestehende Dashboards brauchen kein Neuschreiben.

---

### #165: Heizkreise schaltbar machen (Register 5006)

**Status:** geschlossen als „nicht geplant“ (lokal 13.11.2026, GitHub 15.11.2026). Gleiche Entscheidung wie bei #31, #98, #125 und #136.

Register 5006 ist eine Anforderung mit Zeitlimit von etwa 5 Minuten, keine Einstellung. Danach übernimmt die Lambda wieder ihre eigene Betriebsart, und das Register liefert nach dem Zeitlimit „keine Anforderung“ zurück. Die Messungen von Sturmi77 in #136 belegen das. Die Integration bietet deshalb keine Auswahl dafür. Die Aktion `lambda_heat_pumps.write_modbus_register` bleibt für eigene Automationen auf eigene Verantwortung.

Für einen einzelnen Heizkreis verweist die Antwort auf den Raumthermostat je Heizkreis (#13) und auf den Vorlauf-Offset.

---

### #168: „Aufnahme“ zeigt 0,00 kW, wenn der Leistungssensor in kW angezeigt wird

**Status:** Offen (gemeldet 14.11.2026, Melder BMeyendriesch; Lambda EU15L, Integration 3.7.0, HA 2026.11.1). Der Melder hat die Anzeigeeinheit von `sensor.*_hp1_inverter_power_consumption` in HA auf kW gestellt. Die Karte zeigt dann 0,00 kW, obwohl die Wärmepumpe läuft.

**Ursache:** Die Karte nimmt fest Watt an und teilt durch 1000 ([lambda-cockpit-card.js](custom_components/lambda_heat_pumps/frontend/lambda-cockpit-card.js), Kachel „Aufnahme“). `_n()` liest nur den Zustand und ignoriert `unit_of_measurement`. Bei 1,48 kW rechnet die Karte 0,00148 kW.

**Betroffen (gleiche Ursache):**
- Laufprüfung `_n("power") > 30` in `_heroUnit`: bei kW nie erfüllt, fällt nur auf, wenn `rating` fehlt.
- Abgabe (`heat`): Lambda liefert kW, die Karte rechnet nicht um. Bei umgestellter Einheit W steht „4500 kW“.
- PV-Überschuss (`pv_surplus`) und PV-Leistung (`pv_power`) sowie Batterie (`bat_charge`, `bat_discharge`): bei kW steht „5 W“, und die Schwelle `> 5` greift nicht.
- Laufzeit (`lz_*`, `lccHours`): Gerätetyp `duration` kann in Minuten oder Sekunden kommen.
- Energie-Kacheln (`strom_*`, `waerme_*`) sind fest als kWh beschriftet. Der COP stimmt nur, wenn Zähler und Gegenzähler dieselbe Einheit haben.
- Python-Seite ist bereits abgesichert: externe Zähler in [coordinator.py](custom_components/lambda_heat_pumps/coordinator.py) (Wh, kWh, MWh) und PV in [services.py](custom_components/lambda_heat_pumps/services.py) (kW → W).

**Lösungsvorschlag:** Eine zentrale Methode in der Karte (z. B. `_val(key, "W" | "kW" | "kWh" | "h")`), die `unit_of_measurement` liest und in die Zieleinheit umrechnet. Fehlt die Einheit, gilt die native Einheit der Lambda-Sensoren. Der Vorschlag des Melders (`_w()` für W, kW, MW) ist der richtige Kern dafür. Die Umrechnung sollte separat testbar sein, weil [tests/test_cockpit.py](tests/test_cockpit.py) nur Python prüft.

**Umgesetzt (15.11.2026, 3.7.2, unveröffentlicht):** `_n()` multipliziert mit `_unitFactor()`: Leistungen auf W (`power`, `pv_surplus`, `pv_power`, `bat_*`, `src_*`), Abgabe `heat` auf kW, Energien auf kWh (`strom_*`, `waerme_*`, `e_*`, `hz_*`, `ww_*`, `netz_tag`, `eigen_tag`), Laufzeiten `lz_*` auf h (min, s, ms, d). Ohne oder mit unbekannter Einheit bleibt der Wert, wie er ist. Laufprüfung, Batterie-Schwelle und COP rechnen damit automatisch richtig. Geprüft mit einer Mock-Seite (W/kWh gegen kW/Wh: gleiche Anzeige).

**Erledigt:** Antwort an den Melder, Issue geschlossen (15.11.2026).

**Ursprünglich geplant:** Fix als Release 3.7.2 mit Umrechnungs-Helfer und Anpassung der betroffenen Stellen (F30). Antwort an den Melder, dass der Fix in 3.7.2 kommt; er hat um Mitnahme beim nächsten Update gebeten.

---

## Plan 3.7.2 (Lambda Cockpit, Stand 15.11.2026)

Reihenfolge nach Aufwand und Risiko: erst die kleinen Fehler, dann die Darstellung, zuletzt was Klärung braucht.

| # | Aufgabe | Issues | Aufwand | Risiko | Status |
|---|---|---|---|---|---|
| 1 | Einheiten der Leistungen, Energien und Laufzeiten lesen und normieren (W/kW/MW, Wh/kWh/MWh, h/min/s; F30) | #168 | klein | gering | **erledigt** (3.7.2, unveröffentlicht) |
| 2 | Brauchwasser: Temperatur unten zusätzlich zeigen | #170 | klein | gering | **erledigt** (3.7.2, unveröffentlicht) |
| 3 | Cache der Karten: Prüfwert des Inhalts in der Adresse statt nur der Version | – | klein | gering | **erledigt** (3.7.2, unveröffentlicht) |
| 4 | Stützpunkte der Heizkurve: auf der Hilfeseite beschreiben (Klick auf die Kästchen), kein ✎ in der Karte | #156 | klein | gering | **erledigt** (3.7.2, unveröffentlicht) |
| 5 | Vorlauf-Werte in die Grafik der Heizkurve (Linien Soll und Ist, Werteliste, AT ist), Zeile unter der Kurve entfällt | #156, #128 | mittel | gering | offen |
| 6 | Funktionen live lesen (Websocket statt `features` im Dashboard), Kodierung „neg“ beim PV-Überschuss | #169, #155 | mittel | mittel | offen; Vorzeichen mit Melder klären |
| 7 | Schaltpunkte Punkte 2, 3, 5 (Modulationsziel, Puffer-Status, Warmwasser-Eco) | #163 | mittel | mittel | wartet auf Klärung mit Lambda |
| 8 | Volumenstrom anzeigen | #159 | klein–mittel | gering | Entscheidung zum Platz offen |
| 9 | Raumtemperatur an Lambda ausgegraut | #162 | ? | ? | wartet auf Daten vom Melder |

Antworten offen: #156 (Gespräch PV-Überschuss mit AndiBo62), #169 (Vorzeichen), #163 und #128 (Kommentar).

## Umsetzungsplan (noch offen)

| Aufgabe | Issues | Geschätzt | Status |
|---|---|---|---|
| **F9:** Retry bei Timeout in der Modulerkennung | #101 | niedrig | offen |
| **F17:** Abweichungs-Sensor für Heizkurve | #128 | niedrig | offen |
| **F26:** Firmware V1.0.2-3K / V1.0.7-3K zu `FIRMWARE_CONFIG` | #100 | niedrig | offen (wird mit Feedback geklärt) |
| **F27:** Sensoren 1024–1033 / 1051–1060 ab V1.0.x nicht anlegen | #100, #119, #143 | mittel | offen |
| **F28:** Sentinel `32768` für `integer`-Felder | #100 | niedrig | offen |
| **F30:** Cockpit: Einheiten der Sensoren (kW, W, Wh, Minuten) lesen und umrechnen | #168 | mittel | **erledigt** (3.7.2, unveröffentlicht; Plan 3.7.2 Punkt 1) |

