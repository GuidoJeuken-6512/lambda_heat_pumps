# Analyse der offenen Bug-Issues gegen Branch `3.5`

- **Stand:** 09.11.2026 (neue Issues nach V3.6.1: #151, #152, #153; #153 behoben in 3.7.0)
- **Geschlossene Issues (V3.6.1):** #82, #85, #90, #94, #95, #104, #119, #120, #121, #122 (Duplikat #85), #132, #133, #134, #136, #140, #141 (Duplikat #121), #144. 
- **Geschlossen nach V3.6.1:** #138 (Doku Hydraulic Card), #142 (gelöst), #149 (tmodbus-Anforderung, 3.6.2)
- **Geschlossen (Stand 13.11.2026):** #105 (evcc-Konflikt), #161 (evcc und Register 102), #165 (Heizkreis-Betriebsart, nicht geplant)
- **Offene Issues, noch in Arbeit:** #153 (behoben in 3.7.0), #152, #151, #137, #143 (Feedback ausstehend)
- **Technische Schulden (Enhancement):** #128, #101, #105 (Tests/Regressionen ausstehend)
- **Register ohne Werte nach Firmware:** eigene Auswertung in [`REGISTER_OHNE_WERTE.md`](REGISTER_OHNE_WERTE.md) (44 Issues, Tabelle Firmware → Register, F26–F29).

---

## Offene Issues

| Issue | Titel | Status | Priorität |
|---|---|---|---|
| [#137](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/137) | E-Manager-Sollleistung ≠ 0 ohne PV-Überschuss | Verhalten der Lambda (Schließ-Kommentar entworfen, auf GitHub noch offen) | niedrig |
| [#153](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/153) | Außentemperatur „unbekannt“ bei 0 °C | **Bug, behoben in 3.7.0**: −0,1 °C wurde als Sonderwert 0xFFFF verworfen | mittel |
| [#152](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/152) | `ambient_temperature` fehlt nach 3.6.1 | Firmware-Sperre `"1-7"`; Rückfrage Firmware und Werte vor dem Update | niedrig–mittel |
| [#151](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/151) | PV-Modus endet nicht, Psoll springt auf 0 (2.6.0) | Lambda-Verhalten wie #137; 0-Sprünge vermutlich evcc parallel | niedrig |
| [#143](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/143) | Viele Entitäten ohne Messwert (Puffer) | Feedback zu Screenshot (EU13, V1.0.4-3K) | niedrig–mittel |
| [#101](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/101) | Solarthermiemodul wird nicht erkannt | Logs fehlen; Timeout-Logik prüfen (F9) | niedrig |
| [#105](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/105) | E-Manager-Register springt auf 0 | **Geschlossen** (Ursache: zweiter Modbus-Client, evcc) | – |
| [#128](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/128) | Heizkurve: Abweichung zum Sollwert (Enhancement) | Doku OK, Abweichungs-Sensor offen (F17) | niedrig |

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

**Status:** Verhalten der Lambda, nicht der Integration. Schließ-Kommentar entworfen, auf GitHub noch nicht gepostet.

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

## Lambda Cockpit: offene Issues (Stand 13.11.2026)

Neues Dashboard aus 3.7.0. Alle Meldungen stammen vom 10. bis 12.11.2026. Nichts davon ist beantwortet oder geschlossen. 

| Issue | Titel | Einordnung | Priorität |
|---|---|---|---|
| [#160](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/160) | Entitäten-Suche: Eingabe schließt nach jedem Buchstaben | Fehler, Karte baut die Suche bei jeder Eingabe neu auf | mittel |
| [#162](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/162) | Raumtemperatur an Lambda immer ausgegraut | Offen, Ursache nicht gefunden (Raum-Regler und Raum-Anzeige getrennt prüfen) | mittel |
| [#157](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/157) | Nur ein Heizkreis sichtbar (3 vorhanden); PV-Symbol schwer zu sehen | Bekannte Grenze, siehe toDo „Mehrere Wärmepumpen / Heizkreise“; PV-Symbol ist Wunsch | mittel |
| [#156](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/156) | Keine Heizkurvendaten im Dashboard; Wunsch: VL berechnet, Vorlauf-Offset, VL Soll und VL Ist in der Heizkurve | Nach Neustarts da, Ursache offen; Vorschlag für die Heizkurve | niedrig–mittel |
| [#163](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/163) | Schaltpunkte: Kopie-Werte, Dauerlauf, Puffer-Status, Warmwasser-Eco, Laufzeit am ersten Tag | Mehrere berechtigte Punkte, siehe Details | mittel |
| [#159](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/159) | Volumenstrom bei den Verdichter-Werten anzeigen | Wunsch; Sensor existiert bereits | niedrig |
| [#165](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/165) | Heizkreise über Register 5006 schaltbar machen | **Geschlossen, nicht geplant** (wie #31, #98, #125, #136): Anforderung mit Zeitlimit, kein Rücklesen | – |

Nicht cockpit-spezifisch, aber neu: [#161](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/161) (evcc und Register 102). Ursache wie bei #105: zwei Quellen schreiben in Register 102. Ein Melder hat es gelöst, indem er die PV-Option der Integration abgeschaltet hat und nur evcc schreiben lässt. Einordnung bei #105.

### #160: Entitäten-Suche schließt nach jedem Buchstaben

**Status:** Fehler, Ursache wahrscheinlich bekannt.

Die Entitäten-Karte baut bei jeder Eingabe in das Suchfeld die ganze Ansicht neu auf (`lambda-entities-card.js`, Eingabe-Handler `_render(true)`). Das Eingabefeld wird dabei ersetzt und verliert den Fokus.

**Nächste Schritte:** Eingabefeld beim Neuaufbau erhalten oder nur die Liste neu zeichnen. Danach mit Playwright testen (Tippen Buchstabe für Buchstabe).

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

**Nächste Schritte:** Entscheiden, ob das Cockpit weitere Heizkreise per Auswahl anzeigt (größerer Umbau). Bis dahin in der Antwort auf die YAML-Möglichkeit verweisen und die Schlüssel für Heizkreis 2 nennen.

---

### #156: Keine Heizkurvendaten im neuen Dashboard

**Status:** Der Melder bestätigt, dass es nach mehreren Neustarts geht. Ursache offen.

Vermutlich lädt die Karte, bevor die Werte der Heizkurve als Zustände vorliegen, und zeigt dann keine Kurve. Ein Neuladen hilft.

**Vorschlag des Melders (AndiBo62):** In der Heizkurven-Anzeige zusätzlich die Vorlauf-Werte zeigen: **VL berechnet**, **Vorlauf-Offset**, **VL Soll** und **VL Ist** (aktuelle Vorlauftemperatur). Dann lassen sich Konfiguration und Steuerung im Dashboard direkt vergleichen. Der Melder hat dafür einen eigenen Graphen mit Soll- und Ist-Linie gebaut.

**Nächste Schritte:** Prüfen, ob die Heizkurven-Werte beim ersten Laden fehlen; mit dem Test-Container und einem Neustart nachstellen. Zusammenhang mit dem offenen Konfigurationsfehler (siehe toDo) prüfen. Die vier Vorlauf-Werte in die Heizkurven-Kachel aufnehmen (Werte sind im Cockpit schon vorhanden, nur nicht in der Kurve).

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

**Nächste Schritte:** Punkte 1, 2 und 7 als Verbesserung umsetzen. Punkt 3 und 5 prüfen, Punkt 6 als Hinweis in der Doku. Dem Melder kurz antworten, dass die Punkte aufgenommen sind.

---

### #159: Volumenstrom bei den Verdichter-Werten

**Status:** Wunsch. Der Sensor existiert (`hp1_volume_flow_heat_sink` bzw. `…energy_source`), die Karte zeigt ihn nicht.

Der Melder schlägt vor, den Wert unter dem Ventil im Heizen- bzw. Warmwasser-Bild anzuzeigen. Die Karten-Kacheln sind groß, das Layout müsste dafür schmaler werden.

**Nächste Schritte:** Anzeige unter dem Ventil prüfen. Die Kacheln wären dann nicht mehr frei wählbar; das bleibt eine Entscheidung.

---

### #165: Heizkreise schaltbar machen (Register 5006)

**Status:** geschlossen als „nicht geplant“ (13.11.2026). Gleiche Entscheidung wie bei #31, #98, #125 und #136.

Register 5006 ist eine Anforderung mit Zeitlimit von etwa 5 Minuten, keine Einstellung. Danach übernimmt die Lambda wieder ihre eigene Betriebsart, und das Register liefert nach dem Zeitlimit „keine Anforderung“ zurück. Die Messungen von Sturmi77 in #136 belegen das. Die Integration bietet deshalb keine Auswahl dafür. Die Aktion `lambda_heat_pumps.write_modbus_register` bleibt für eigene Automationen auf eigene Verantwortung.

Für einen einzelnen Heizkreis verweist die Antwort auf den Raumthermostat je Heizkreis (#13) und auf den Vorlauf-Offset.

---

## Umsetzungsplan (noch offen)

| Aufgabe | Issues | Geschätzt | Status |
|---|---|---|---|
| **F9:** Retry bei Timeout in der Modulerkennung | #101 | niedrig | offen |
| **F17:** Abweichungs-Sensor für Heizkurve | #128 | niedrig | offen |
| **F26:** Firmware V1.0.2-3K / V1.0.7-3K zu `FIRMWARE_CONFIG` | #100 | niedrig | offen (wird mit Feedback geklärt) |
| **F27:** Sensoren 1024–1033 / 1051–1060 ab V1.0.x nicht anlegen | #100, #119, #143 | mittel | offen |
| **F28:** Sentinel `32768` für `integer`-Felder | #100 | niedrig | offen |

