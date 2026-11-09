# Analyse der offenen Bug-Issues gegen Branch `3.5`

- **Stand:** 09.11.2026 (neue Issues nach V3.6.1: #151, #152, #153; Fix für #153 auf Branch `fix/3.6.3`, noch nicht gepusht)
- **Geschlossene Issues (V3.6.1):** #82, #85, #90, #94, #95, #104, #119, #120, #121, #122 (Duplikat #85), #132, #133, #134, #136, #140, #141 (Duplikat #121), #144. 
- **Geschlossen nach V3.6.1:** #138 (Doku Hydraulic Card), #142 (gelöst), #149 (tmodbus-Anforderung, 3.6.2)
- **Offene Issues, noch in Arbeit:** #153 (behoben in 3.6.3, unveröffentlicht), #152, #151, #137, #143 (Feedback ausstehend)
- **Technische Schulden (Enhancement):** #128, #101, #105 (Tests/Regressionen ausstehend)
- **Register ohne Werte nach Firmware:** eigene Auswertung in [`REGISTER_OHNE_WERTE.md`](REGISTER_OHNE_WERTE.md) (44 Issues, Tabelle Firmware → Register, F26–F29).

---

## Offene Issues

| Issue | Titel | Status | Priorität |
|---|---|---|---|
| [#137](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/137) | E-Manager-Sollleistung ≠ 0 ohne PV-Überschuss | Verhalten der Lambda (Schließ-Kommentar entworfen, auf GitHub noch offen) | niedrig |
| [#153](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/153) | Außentemperatur „unbekannt“ bei 0 °C | **Bug, behoben in 3.6.3** (Branch `fix/3.6.3`): −0,1 °C wurde als Sonderwert 0xFFFF verworfen | mittel |
| [#152](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/152) | `ambient_temperature` fehlt nach 3.6.1 | Firmware-Sperre `"1-7"`; Rückfrage Firmware und Werte vor dem Update | niedrig–mittel |
| [#151](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/151) | PV-Modus endet nicht, Psoll springt auf 0 (2.6.0) | Lambda-Verhalten wie #137; 0-Sprünge vermutlich evcc parallel | niedrig |
| [#143](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/143) | Viele Entitäten ohne Messwert (Puffer) | Feedback zu Screenshot (EU13, V1.0.4-3K) | niedrig–mittel |
| [#101](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/101) | Solarthermiemodul wird nicht erkannt | Logs fehlen; Timeout-Logik prüfen (F9) | niedrig |
| [#105](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/105) | E-Manager-Register springt auf 0 | Nutzer-Hinweis: ohne evcc keine 0-Werte → zweiter Modbus-Client als Ursache wahrscheinlich | niedrig |
| [#128](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/128) | Heizkurve: Abweichung zum Sollwert (Enhancement) | Doku OK, Abweichungs-Sensor offen (F17) | niedrig |

---

## Details

### #153: Außentemperatur „unbekannt“ bei 0 °C

**Status:** Bug der Integration, behoben auf Branch `fix/3.6.3` (Version 3.6.3, nicht gepusht, nicht veröffentlicht).

Seit 3.5.2 (Commit c2b07d1) filterte `Ambient.temperature` (Register 2) zusätzlich 0xFFFF als „kein externer Fühler“. Bei Faktor 0,1 ist 0xFFFF aber −0,1 °C, ein echter Messwert. Um den Gefrierpunkt sprang der Sensor deshalb bei jedem Abruf mit −0,1 °C auf „unbekannt“. Die CSV des Melders bestätigt das: 32 × unbekannt, 24 × −0,2, 8 × 0,0, kein einziges Mal −0,1. Ein fehlender Fühler meldet −3000 (0xF448, `NO_SENSOR`) und wird weiter gefiltert.

**Fix:** `NO_REQUEST` bei `Ambient.temperature` entfernt (`lambda_modbus/general.py`); Test `test_a_no_request_or_no_sensor_register_reads_unknown` erwartet jetzt −0,1 °C. Die Puffer-Anforderungsregister und die Heizkreis-Betriebsart behalten den Filter (dort bedeutet −1 wirklich „keine Anforderung“).

**Nächste Schritte:** Push und Release 3.6.3 nach Freigabe, dann im Issue antworten.

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

## Umsetzungsplan (noch offen)

| Aufgabe | Issues | Geschätzt | Status |
|---|---|---|---|
| **F9:** Retry bei Timeout in der Modulerkennung | #101 | niedrig | offen |
| **F17:** Abweichungs-Sensor für Heizkurve | #128 | niedrig | offen |
| **F26:** Firmware V1.0.2-3K / V1.0.7-3K zu `FIRMWARE_CONFIG` | #100 | niedrig | offen (wird mit Feedback geklärt) |
| **F27:** Sensoren 1024–1033 / 1051–1060 ab V1.0.x nicht anlegen | #100, #119, #143 | mittel | offen |
| **F28:** Sentinel `32768` für `integer`-Felder | #100 | niedrig | offen |

