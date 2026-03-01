---
title: "Energiesensor-Werte anpassen (Entwicklerwerkzeuge)"
---

# Energiesensor-Werte anpassen (Entwicklerwerkzeuge)

Die Lambda Heat Pumps Integration bietet **Energieverbrauchssensoren** nach Betriebsart (Heizen, Warmwasser, Kühlen, Abtauen): sowohl **elektrisch** (Stromverbrauch) als auch **thermisch** (Wärmeabgabe). Diese Werte können Sie bei Bedarf über die Home-Assistant-**Entwicklerwerkzeuge** anpassen – z. B. um Startwerte zu setzen oder Korrekturen vorzunehmen.

## Wann ist eine Anpassung sinnvoll?

### Zyklische Werte starten bei 0

Beim **ersten Start** oder nach einer **Neuinstallation** der Integration starten alle periodenbezogenen Sensoren (täglich, monatlich, jährlich, stündlich) mit dem Wert **0**. Das ist technisch korrekt, kann aber **irreführend** sein:

- Sie nutzent möglicherweise die Integration schon länger, dann starten die thermishen Energiewerte bei 0 und die elektischen sind schon erfasst.
- Oder sie wollen die monatlich / jährlichen Werte anpassen.
- Die **Total**-Sensoren werden ab dem ersten Tag korrekt hochgezählt; die zyklischen Werte (Daily, Monthly, Yearly, Hourly) bauen sich erst im Lauf der Zeit aus dem Total auf.
- Wenn Sie z. B. einen **bekannten Verbrauch** aus der Vergangenheit übernehmen möchten, können Sie die entsprechenden Sensoren einmalig über die Entwicklerwerkzeuge setzen.

### Manuelle Korrektur


Falls ein Sensor durch Fehlmessung oder Konfigurationswechsel einen falschen Wert anzeigt, können Sie den Wert korrigieren. Danach zählt die Integration wieder normal weiter.

**Verwenden Sie am besten den Verlauf, um die jeweiligen Werte zu ermitteln.**
Nehmen Sie hier die Sensoren 

- sensor.eu08l_hp1_compressor_power_consumption_accumulated
- sensor.eu08l_hp1_compressor_thermal_energy_output_accumulated

und ermitteln die Deltas für den jeweiligen zyklischen Sensor.

**Die COP Sensoren zu den zeitlichen Zyklen nicht anpassen, die berechnen sich neu aus den beiden anderen Sensoren**

<img src="../../assets/home_assistant_verlauf_de.png" alt="Home Assistant Verlauf" style="width: 100%; max-width: 600px; height: auto; border-radius: 8px;">

## Sensoren über Entwicklerwerkzeuge anpassen

### Entwicklerwerkzeuge → Zustände

1. Öffnen Sie in Home Assistant **Einstellungen** → **Entwicklerwerkzeuge**.
2. Wechseln Sie zum Tab **Zustände** („States“).
3. Im Suchfeld können Sie nach Ihrem Sensor suchen, z. B.:
   - `heating_energy_total`
   - `heating_thermal_energy_daily`
   - `eu08l_hp1` (zeigt alle Sensoren Ihrer Wärmepumpe, sofern Ihr Präfix `eu08l_hp1` ist)

### Welche Sensoren gibt es?

- **Elektrisch (Stromverbrauch):**  
  `sensor.<prefix>_heating_energy_total`, `_daily`, `_monthly`, `_yearly`, sowie für hot_water, cooling, defrost (je nach Zeitraum).
- **Thermisch (Wärmeabgabe):**  
  `sensor.<prefix>_heating_thermal_energy_total`, `_daily`, `_monthly`, `_yearly`, sowie für hot_water, cooling, defrost.

Ersetzen Sie `<prefix>` durch Ihren tatsächlichen Entity-Präfix (z. B. `eu08l_hp1`). Die genauen Entity-IDs finden Sie unter **Einstellungen** → **Geräte & Dienste** → **Geräte** → Ihre Lambda-Integration.

### Wert setzen

- Klicken Sie auf die gewünschte **Entity** (z. B. `sensor.eu08l_hp1_heating_energy_total`).
- Sie können den **Zustand** (State) und ggf. **Attribute** anpassen.
- Für Energieverbrauchssensoren ist der State in der Regel eine **Zahl** (kWh). Tragen Sie den gewünschten Start- oder Korrekturwert ein (z. B. `1234.56`).
- Bestätigen Sie die Änderung.

**Hinweis:** Nach einem Neustart von Home Assistant oder einem Reload der Integration können Werte aus der **Persistierung** wieder geladen werden. Wenn Sie dauerhafte Korrekturen wünschen, setzen Sie den Wert einmalig; die Integration speichert den State und rechnet ab diesem Wert weiter. Bei **Total**-Sensoren ist der gesetzte Wert die neue Basis; bei **Daily/Monthly/Yearly/Hourly** hängt die Anzeige von der internen Logik (Total minus Baseline) ab – in Zweifelsfällen zuerst den **Total**-Sensor anpassen.

## Kurz zusammengefasst

| Ziel | Vorgehen |
|------|----------|
| Startwerte setzen (zyklische Werte waren „falsch“, weil alles bei 0 gestartet ist) | **Entwicklerwerkzeuge** → **Zustände** → Sensor suchen (z. B. nach `heating_energy` oder Ihrem Präfix) → State auf gewünschten Wert setzen. |
| Elektrischen oder thermischen Verbrauch nach Betriebsart korrigieren | Gleicher Weg: Sensor in den Zuständen finden und State anpassen. |
| Entity-IDs Ihrer Sensoren finden | **Einstellungen** → **Geräte & Dienste** → **Geräte** → Lambda Heat Pumps → gewünschte Wärmepumpe → Entities. |

Weitere Informationen zu den Sensoren und zur Berechnung: [Energie- und Wärmeverbrauchsberechnung](Energieverbrauchsberechnung.md), [COP-Sensoren](cop-sensoren.md).
