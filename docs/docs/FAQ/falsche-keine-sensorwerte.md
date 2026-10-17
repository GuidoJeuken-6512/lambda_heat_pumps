---
title: "FAQ – Falsche / keine Sensorwerte"
---

# Falsche oder keine Sensorwerte

*Zuletzt geändert am 17.10.2026*

Hier finden Sie die häufigsten Ursachen und Lösungen, wenn Sensoren **falsche Werte** anzeigen oder **gar keine Werte** liefern.

---

## 1. Falsche Werte bei Energie- bzw. int32-Sensoren

### Problematik

- **Symptome:** Die akkumulierten Energiezähler (`hpX_compressor_power_consumption_accumulated`, `hpX_compressor_thermal_energy_output_accumulated`) zeigen **völlig falsche** Werte, oft im Bereich von Hunderten Millionen bis Milliarden Wh oder negativ.
- Die **Lambda** zeigt in ihrer Statistik dagegen korrekte Werte.
- Betroffen sind die **32-Bit-Werte**, die aus zwei 16-Bit-Modbus-Registern zusammengesetzt werden (die beiden Energiezähler jeder Wärmepumpe, der Solar-Ertragszähler).

**Ursache:** Die **Register-Reihenfolge** (`high_first` oder `low_first`) passt nicht zu Ihrer Lambda. Es geht nicht um die Byte-Reihenfolge innerhalb eines Registers, sondern darum, ob das höherwertige oder das niederwertige Register zuerst steht.

Seit Version 3.5 verwendet die Integration automatisch die Reihenfolge der **eingestellten Firmware** (`high_first` bis V0.0.9-3K, `low_first` ab V0.0.10-3K). Falsche Werte haben daher meist eine dieser Ursachen:

- Die eingestellte **Firmware-Version** passt nicht zu Ihrer Lambda.
- Die Register-Reihenfolge wurde unter **Konfigurieren** fest auf einen falschen Wert gesetzt. Das passierte bei Installationen, die vor Version 3.5.7 von 2.x aktualisiert wurden: Dort wurde ohne Eintrag in der alten `lambda_wp_config.yaml` fest `high_first` gespeichert.
- Ihre Lambda weicht von der dokumentierten Reihenfolge ihrer Firmware ab (selten).

### Lösung

1. **Firmware-Version prüfen.** Stimmt sie nicht, ändern Sie sie über **⋮ → Neu konfigurieren**, siehe [Firmware-Version ändern](../Anwender/firmware-wechsel.md). Dabei wird eine selbst gewählte Register-Reihenfolge zurückgesetzt, und es gilt die Reihenfolge der neuen Firmware.
2. **Register-Reihenfolge prüfen:** **Einstellungen** → **Geräte & Dienste** → Lambda → **Konfigurieren**, Option **Register-Reihenfolge**. Stimmen die Werte nach Schritt 1 noch nicht, stellen Sie die jeweils andere Reihenfolge ein (`high_first` ↔ `low_first`). Die Integration lädt sich nach dem Speichern automatisch neu.
3. **Werte vergleichen:** Bei richtiger Einstellung stimmen die Zähler mit der Statistik am Display der Lambda überein.

### Langzeitstatistik nach falschen Werten

Die Gesamtzähler der Integration (`*_energy_total`, COP) schützt ein Sprungfilter: Ein Sprung von mehr als 100 kWh pro Abfrage wird verworfen. Die akkumulierten Zähler selbst haben in der Langzeitstatistik aber die falschen Werte, und Auswertungen darauf (z. B. Verbrauchszähler-Helfer oder das Energie-Dashboard) zeigen dadurch einen riesigen Sprung. Korrigieren lässt sich das unter **Entwicklerwerkzeuge** → **Statistiken**: beim betroffenen Sensor den Sprung über „Summe anpassen“ (engl. „Adjust sum“) ausgleichen, oder die Statistik des Sensors löschen (siehe [Historische Daten löschen](../Anwender/historische_daten_loeschen.md)).

---

## 2. Sensoren liefern keine Werte oder fehlen

### Sensor fehlt ganz

- **Falsche Firmware-Version:** Die Integration legt nur Sensoren an, die die eingestellte Firmware kennt. Prüfen und ändern Sie die Firmware über **⋮ → Neu konfigurieren**, siehe [Firmware-Version ändern](../Anwender/firmware-wechsel.md). Wo die Firmware hinterlegt ist, steht in [Anpassungen der Sensoren abhängig von der Firmware](../Anwender/anpassungen-sensoren-firmware.md).
- **Modul nicht erkannt:** Welche Module (Wärmepumpen, Speicher, Puffer, Solar, Heizkreise) vorhanden sind, ermittelt die Integration bei jedem Start. Antwortet die Lambda dabei zu langsam, kann ein Modul fehlen. Laden Sie die Integration neu (**⋮ → Neu laden**).
- **Standardmäßig deaktiviert:** Die Tages-, Monats- und Jahreszähler sind bei einer Neuinstallation deaktiviert, nur die Gesamtzähler sind aktiv. Sie finden sie beim Gerät unter „Entitäten“ und können sie dort aktivieren.

### Sensor zeigt „nicht verfügbar“ (unavailable)

- Antwortet ein ganzes Modul nicht, werden alle Sensoren dieses Moduls „nicht verfügbar“, bis es wieder antwortet. Im Log steht dazu **einmal** eine Warnung `Failed to fetch …`, nicht bei jeder Abfrage.
- Antwortet die Lambda auf ein Modul nicht mehr, das sie bei der Einrichtung noch bedient hat (z. B. nach einem Umbau oder Firmware-Update), lädt sich die Integration automatisch neu und erkennt die Module neu.
- Hilft das nicht: Verbindung prüfen und ein [Debug-Log](../Anwender/debug-logs-erzeugen.md) erstellen.

### Sensor zeigt „unbekannt“ (unknown)

Die Lambda meldet für manche Register einen Sonderwert, wenn sie keinen Wert hat, z. B. bei Eingaberegistern, die nur gefüllt sind, wenn sie per Modbus beschrieben werden (Raumtemperatur eines Heizkreises ohne aktive Raumthermostat-Steuerung). Die Integration zeigt diese Sonderwerte als „unbekannt“ statt als scheinbaren Messwert an. Das ist kein Fehler.

### Sensoren, die Sie nicht brauchen

Seit Version 3.5 gibt es kein `disabled_registers` in der `lambda_wp_config.yaml` mehr. Blenden Sie den Sensor stattdessen in Home Assistant aus: Entität öffnen → **Zahnrad** → **deaktivieren**. Ausführliche Anleitung: [Entitäten löschen](../Anwender/entitaeten_loeschen.md).

!!! note "Deaktivieren ändert nichts an der Abfrage"
    Seit Version 3.5 liest die Integration die Lambda blockweise, unabhängig davon, welche Entitäten aktiv sind. Eine deaktivierte Entität erscheint nicht mehr in Home Assistant, die Abfrage per Modbus und eventuelle Log-Meldungen ändern sich dadurch aber nicht.

---

## 3. Außentemperatur oder Puffer-Anforderung zeigt -300 °C / eine unrealistische Anforderung

### Problematik

- Die Außentemperatur (`ambient_temperature`) zeigt exakt **-300 °C**, oder eine
  Puffer-Anforderung (z. B. Vorlauf-/Rücklauf-Sollwert) zeigt einen
  unrealistischen, konstanten Wert.
- Betroffen sind Installationen ohne extern eingespeisten Außenfühler bzw.
  ohne aktive Anforderung an einen Puffer.

**Ursache:** Die Lambda-Steuerung meldet auf diesen Registern `0xFFFF` (−1),
wenn kein externer Sensor eingespeist ist bzw. keine Anforderung besteht.
Skaliert sieht das wie ein echter Messwert aus (−300,0 °C), ist aber keiner.
Bis einschließlich Version 3.5.1 wurde dieser Sonderwert bei diesen Registern
nicht herausgefiltert.

### Lösung

Ab Version 3.5.2 wird `0xFFFF` bei den betroffenen Registern (Außentemperatur
sowie den Puffer-/Heizkreis-Anforderungsregistern) als „nicht verfügbar“
(`unknown`) statt als Messwert angezeigt. Ein Update der Integration behebt
dies ohne weitere Konfiguration.
