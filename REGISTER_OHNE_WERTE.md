# Register ohne Werte nach Firmware-Stand

- **Stand:** 22.10.2026
- **Branch:** `3.5` (`main`/2.x wird nicht mehr geändert)
- **Grundlage:** 44 GitHub-Issues (Text und alle Kommentare) sowie die Sonderwerte im Code von `3.5`
- **Ziel:** Register finden, die auf einem bestimmten Firmware-Stand nachweislich keinen Wert liefern, damit die Integration die zugehörigen Sensoren dort gar nicht erst anlegt.

## Begriffe

**Firmware** meint hier immer die Firmware der Wärmepumpe im Format `V…-3K`. Sie steht unten in der Statuszeile der Wärmepumpen-Seite. Die Software-Version der Steuerung (z. B. `SW V1.3.10`) ist etwas anderes.

| Firmware | Stufe in `FIRMWARE_CONFIG` (3.5.7) |
|---|---|
| V0.0.3-3K … V0.0.9-3K | 1 … 7 |
| V0.0.10-3K | 8 |
| V1.0.2-3K | fehlt (F26) |
| V1.0.4-3K | 9 |
| V1.1.0-3K | 10 |

**Sonderwerte**, die die Lambda statt eines Messwerts liefert:

| Rohwert | Bedeutung | Behandlung in 3.5 |
|---|---|---|
| `0x8000` (32768 / −32768) | Register auf dieser Firmware nicht vorhanden | `SENTINELS`, Standard für `gauge()`/`enum()` |
| `0xF448` (−3000, skaliert −300,0 °C) | kein Fühler angeschlossen | `SENTINELS`, Standard für `gauge()`/`enum()` |
| `0xFFFF` (−1, skaliert z. B. −0,1 °C) | keine Anforderung / nichts eingespeist | nur opt-in (`NO_REQUEST`): Register 0002, 3005–3009, 5006 |
| Modbus-Exception 2 | Adresse ungültig | Lesefehler |

> **Lücke:** `integer()` filtert keine Sonderwerte (`lambda_modbus/model.py`, nur `gauge()` und `enum()` setzen `nan`). Ganzzahl-Felder zeigen 32768 bzw. −32768 deshalb als Zahl an: `config_parameter_24/33/50/60`, `request_type` (1015), `emgr_actual_power` (102), u. a.

## Datenpunkte

| # | Quelle | Modell | Firmware | Steuerung | Betrieb | Rohwerte |
|---|---|---|---|---|---|---|
| A | [#100](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/100#issuecomment-5088880938) madmaxx425, 24./27.07.2026 | EU10L Luft-Monoblock | **V1.0.4-3K** | SW V1.3.10 | Standby / Sommer | vollständiger Dump 0–5152 |
| B | [#100](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/100#issuecomment-6310216535) BMeyendriesch, 21.10.2026 | EU15L Luft/Wasser | **V1.0.2-3K** | SW V1.3.10 | **Heizen, Kompressor läuft**, Display verglichen | vollständiger Dump 0–5007 |
| C | [#107](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/107#issuecomment-5511732954) PhilippHS, 02.09.2026 | EU10L | V1.0.4-3K („SW“ genannt) | – | – | Register 0–4: `0, 1, 65236, 157, 164` |
| D | [#108](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/108#issuecomment-5200845821) foerdecoder, 06.08.2026 | EU08L | V1.0.4 (V1.1.0-3K zurückgezogen) | – | – | Register 2 gültig, Außentemperatur wird extern eingespeist |
| E | [#100](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/100#issuecomment-5068349040) Heimerdinger2000 | EU10L | V1.0.4-3K | SW 1.3.10 | – | `ambient_temperature` = −300, Display zeigt Außentemperatur |
| F | [#91](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/91) pinkpanther84, 07.06.2026 | EU13L | V0.0.8-3K | – | – | 102 = −32768 W (Display −5,74 kW), 103 = 0 |
| G | [#67](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/67#issuecomment-3943524391) joachimpfeifer, 23.02.2026 | EU08L | V0.0.8-3K | – | Kompressor lief | 2004/2005: Exception 2 |
| H | [#70](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/70#issuecomment-4065252701) SynAck91, 16.03.2026 | EU15L | nicht genannt (alte Steuerung, Integration 2.3) | – | – | 1010 und **1025 liefern Werte** |
| I | [#88](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/88) Zeppelin-PV, 30.05.2026 | EU10L | V0.0.10-3K | – | – | „viele Sensoren −300, manche 32768“, **keine Adressen** |
| J | [#87](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/87), [#31](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/31), [#136](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/136) | EU08L/EU13L/EU10L | V0.0.9-3K, V1.0.4-3K | – | – | 5005 → −300 nach Timeout; 5006 → −1 nach ~5 min |
| K | [#39](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/39) | EU13L u. a. | V0.0.9-3K | – | – | 5002–5007 im Block nicht lesbar (in 3.5 durch Einzelabfrage von 5n07 gelöst); 5n02/5n03 liefern Werte |

Weitere Aussagen aus den Issues:
- Register ab 1024 stehen nicht in der Lambda-Modbus-Doku; sie wurden zusammengesucht (#70).
- „Wenn ein Register 32768 liefert, gibt Lambda dort keine Werte mehr aus“ (#91). Was geliefert wird, hängt von Firmware **und** Steuerungs-Software ab (#81).
- Laut Lambda-Protokoll 1.0 ist Register 0002 ein Schreibregister für einen extern eingespeisten Außenwert (#100, Datenpunkt A).
- Nicht über Modbus verfügbar (unabhängig von der Firmware): Heizkurven-Stützpunkte, Taktzähler (#107), Druck (#111), EqM-/Lüfterleistung (#86), PV-Temperaturerhöhungen (#124), Zirkulation (#135).

## Tabelle: Firmware → Register ohne Wert

❌ = kein Wert (Sonderwert) · ✅ = Wert · ? = kein Beleg

| Register | Sensor in 3.5 | Typ | V0.0.3–V0.0.9 | V0.0.10 | V1.0.2 | V1.0.4 | V1.1.0 | Bewertung |
|---|---|---|---|---|---|---|---|---|
| 1024 | `config_parameter_24` | integer | ? | ? | ❌ B | ❌ A | ? | **gesichert ab V1.0.x** |
| 1025 | `vda_rating` | gauge | ✅ H | ? | ❌ B | ❌ A | ? | **gesichert ab V1.0.x** |
| 1026 | `hot_gas_temperature` | gauge | ? | ? | ❌ B (Display: Wert) | ❌ A | ? | **gesichert ab V1.0.x** |
| 1027 | `subcooling_temperature` | gauge | ? | ? | ❌ B (Display: Wert) | ❌ A | ? | **gesichert ab V1.0.x** |
| 1028 | `suction_gas_temperature` | gauge | ? | ? | ❌ B (Display: Wert) | ❌ A | ? | **gesichert ab V1.0.x** |
| 1029 | `condensation_temperature` | gauge | ? | ? | ❌ B (Display: Wert) | ❌ A | ? | **gesichert ab V1.0.x** |
| 1030 | `evaporation_temperature` | gauge | ? | ? | ❌ B (Display: Wert) | ❌ A | ? | **gesichert ab V1.0.x** |
| 1031 | `eqm_rating` | gauge | ? | ? | ❌ B (Display: Wert) | ❌ A | ? | **gesichert ab V1.0.x** |
| 1032 | `expansion_valve_opening_angle` | gauge | ? | ? | ❌ B (Display: Wert) | ❌ A | ? | **gesichert ab V1.0.x** |
| 1033 | `config_parameter_33` | integer | ? | ? | ❌ B | ❌ A | ? | **gesichert ab V1.0.x** |
| 1050 | `config_parameter_50` | integer | ? | ? | 0 B | 0 A (einmal 32768) | ? | nicht ausschließen |
| 1051–1059 | `dhw_output_power_15c` … `cooling_max_output_power` | gauge | ? | ? | ❌ B | ❌ A | ? | **gesichert ab V1.0.x** |
| 1060 | `config_parameter_60` | integer | ? | ? | ❌ B | ❌ A | ? | **gesichert ab V1.0.x** |
| 1015 | `request_type` | integer | ? | ? | ❌ B | ❌ A | ? | gesichert, aber Anforderungsregister: Sonderwert filtern statt ausschließen |
| 1016–1018 | `requested_*` | gauge | ? | ? | ❌ B | ❌ A | ? | wie 1015, bereits gefiltert |
| 1008 | `energy_source_outlet_temperature` | gauge | ? | ? | ❌ B | ❌ A | ? | **nicht nach Firmware**: beide Anlagen Luft-Monoblock ohne Fühler (Bauart), bereits gefiltert |
| 0002 | `ambient_temperature` | gauge | ✅ (Annahme bis 2.8.0) | ? | ❌ −3000 B | ❌ −3000 A/E, **−300** C, ✅ D (extern eingespeist) | ? | **nicht nach Firmware**: Schreibregister, Wert nur bei externer Einspeisung |
| 3005–3009 | Puffer-Anforderung | gauge/enum | −1 | ? | −1 B | −1 A | ? | „keine Anforderung“, bereits gefiltert |
| 5003–5005 | Raum-/Vorlauf-Soll (Schreibregister) | gauge | −300 nach Timeout J | ? | −3000 B | −3000 A | ? | Schreibregister, bereits gefiltert |
| 5006 | `operating_mode` | enum | −1 J | ? | −1 B | −1 A | ? | Anforderung mit Timeout (#136), bereits gefiltert |
| 102 | `emgr_actual_power` | integer | −32768 F (V0.0.8) | ? | ? | ✅ A, #105, #120 | ? | **nicht nach Firmware**: hängt von der E-Manager-Einstellung ab; Sonderwert filtern |
| 2004/2005 | Warmwasser-Register | – | Exception 2 G (V0.0.8) | ? | ? | ✅ A | ? | **nicht nach Firmware**: hängt von der Konfiguration ab (#39) |

**Gegenproben (liefern Werte):** auf V1.0.2 und V1.0.4: 0003/0004, 1000–1007, 1009–1014, 1019–1023 (Zähler `low_first`), 5007; nur auf V1.0.4 gemeldet (A): 0000/0001, 100–104, 2000–2005, 2050, 3000–3003, 3050, 5000–5002, 5050–5052.

## Bewertung

**Gesichert ausschließbar ab Firmware-Stufe 9 (V1.0.x):** 21 Sensoren auf 1024–1033 und 1051–1060.
- Zwei unabhängige Anlagen (verschiedene Modelle, Firmware V1.0.2 und V1.0.4, Standby und Heizbetrieb) liefern dort ausnahmslos 32768.
- Bei laufendem Kompressor zeigt das Display Werte für Heißgas, Kondensation, Sauggas, Verdampfung, Unterkühlung, Expansionsventil und EqM. Die Steuerung gibt sie nur nicht über Modbus aus. Ein Fehlen „weil die Pumpe steht“ ist damit ausgeschlossen.

**Einschränkungen:**
1. **V1.1.0-3K ist nirgends belegt.** Alle Meldungen mit „V1.1.0-3K“ betrafen tatsächlich V1.0.4-3K mit dieser Option in der Integration (#108 zurückgezogen, #100 b-bremer, #133/#134 Sturmi77). Ein Ausschluss für Stufe 10 ist eine Annahme.
2. **V0.0.10-3K ist offen.** #88 meldet „viele Sensoren −300 / 32768“ ohne Adressen; relcead (#100) hat V0.0.10-3K auf der neuen Steuerung (SW 1.3.8), ohne Dump.
3. **Steuerungs-Software:** Beide Dumps stammen von SW V1.3.10. Ob eine andere Steuerungs-Software die Register wieder liefert, ist offen. BMeyendriesch hat beim Lambda-Support angefragt (21.10.2026).
4. Die Register stehen nicht in der Lambda-Doku. Lambda kann sie ohne Ankündigung wieder freigeben.

**Nicht nach Firmware ausschließen:** 1008, 0002, 1015–1018, 3005–3009, 5003–5006, 102, 2004/2005. Ob sie einen Wert liefern, hängt von Bauart, Konfiguration oder einer aktiven Anforderung ab.

## Vorschlag für die Umsetzung (3.5)

| # | Änderung | Ort | Aufwand |
|---|---|---|---|
| F26 | V1.0.2-3K in `FIRMWARE_CONFIG` (Stufe 9, `low_first`; V1.0.4 → 10, V1.1.0 → 11). `low_first` belegt durch Datenpunkt B (Zähler 17.563 / 98.159 Wh). | `const.py`, `tests/test_firmware.py` | S |
| F27 | Die 21 Sensoren auf 1024–1033 und 1051–1060 mit `firmware_versions=("1-8",)` versehen. **Entscheidung offen:** V1.1.0-3K mit ausschließen (Annahme) oder nur V1.0.x. | `sensor.py:223-248` | S |
| F27a | Prüfen, ob die Integration die Register dann auch nicht mehr liest. Vor allem die elf Einzelabfragen der Leistungsgrenzen (1050–1060). | `coordinator.py`, `lambda_modbus/ranges.py` | S–M |
| F28 | Sonderwerte auch für Ganzzahl-Felder filtern (`config_parameter_*`, `request_type`, `emgr_actual_power`). Achtung bei `config_parameter_*`: laut `model.py` kann dort jede Zahl gültig sein, daher nur 0x8000. | `lambda_modbus/model.py`, `heat_pump.py`, `general.py` | S |
| F3 | **Nicht** umsetzen, solange Register 0002 auf V1.0.4 den Rohwert −300 liefern kann (Datenpunkt C, ergäbe −30,0 °C). Wenn überhaupt: −300 zusätzlich als Sonderwert für 0002 aufnehmen. | `lambda_modbus/general.py` | S |
| F29 | Doku/Changelog 3.5.2 korrigieren: 0xFFFF ergibt −0,1 °C, nicht −300 °C (−300 °C ist −3000). Ebenso der Kommentar in `general.py:15` und die Aussage zu `ambient_temperature` in `docs/docs/Entwickler/sensoren-uebersicht.md:41`. | Doku, Changelog, Kommentar | S |

**Folge für Anwender (F27):** Auf V1.0.x verschwinden die 21 Entitäten. Wer sie in der Registry hat, sieht sie als „nicht mehr bereitgestellt“ und kann sie löschen. Gehört in den Changelog.

## Offene Fragen an Tester

- Dump der Register 1024–1060 auf **V0.0.10-3K** (alte und neue Steuerung) und auf einer echten **V1.1.0-3K**.
- Register 1034–1049 wurden in keinem Dump gemeldet.
- Antwort des Lambda-Supports zu den Kältekreiswerten (#100).
