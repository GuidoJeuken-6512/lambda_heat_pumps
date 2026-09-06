---
title: "Energiesensor-Startwerte setzen"
---

# Energiesensor-Startwerte setzen

*Zuletzt geändert am 06.09.2026*

Die Lambda Heat Pumps Integration bietet **Energieverbrauchssensoren** nach Betriebsart (Heizen, Warmwasser, Kühlen, Abtauen): sowohl **elektrisch** (Stromverbrauch) als auch **thermisch** (Wärmeabgabe). Bei einer Neuinstallation starten alle diese Zähler bei **0** – wer historische Werte übernehmen oder einen falschen Wert korrigieren möchte, tut das über **Offsets**, nicht mehr über die Entwicklerwerkzeuge.

!!! warning "Entwicklerwerkzeuge → Zustände funktionieren seit 3.5 nicht mehr zuverlässig"
    Seit dem 3.5-Rewrite berechnet jeder Energie- und Cycling-Zähler seinen Wert bei **jedem** Poll (Standard alle 30 Sekunden) neu aus dem, was der Coordinator seit dem letzten Blick gezählt hat. Ein manuell über **Entwicklerwerkzeuge → Zustände** gesetzter Wert wird von diesem laufenden Objekt im Speicher nicht übernommen – er wird spätestens beim nächsten Poll wieder überschrieben. Nutzen Sie stattdessen die unten beschriebenen **Offsets**.

## Wann ist eine Anpassung sinnvoll?

### Zyklische Werte starten bei 0

Beim **ersten Start** oder nach einer **Neuinstallation** der Integration starten alle periodenbezogenen Sensoren (täglich, monatlich, jährlich, stündlich) mit dem Wert **0**. Das ist technisch korrekt, kann aber **irreführend** sein:

- Sie nutzen möglicherweise die Integration schon länger, dann starten die thermischen Energiewerte bei 0, während die elektrischen schon erfasst sind.
- Die **Total**-Sensoren werden ab dem ersten Tag korrekt hochgezählt; die zyklischen Werte (Daily, Monthly, Yearly, Hourly) bauen sich erst im Lauf der Zeit aus dem Total auf – das ist normal und braucht keine Korrektur.
- Wenn Sie einen **bekannten Verbrauch** aus der Vergangenheit übernehmen möchten (z. B. beim Wärmepumpenwechsel), setzen Sie das über einen **Offset**.

### Manuelle Korrektur

Falls ein **Total**-Sensor durch Fehlmessung oder Sensorwechsel einen falschen Wert anzeigt, korrigieren Sie ihn über einen Offset statt über einen manuell gesetzten Zustand – ein Offset überlebt auch den nächsten Poll und jeden Neustart.

**Verwenden Sie am besten den Verlauf, um die jeweiligen Werte zu ermitteln.** Nehmen Sie hier die Sensoren

- `sensor.eu08l_hp1_compressor_power_consumption_accumulated`
- `sensor.eu08l_hp1_compressor_thermal_energy_output_accumulated`

und ermitteln Sie die Differenz zum aktuellen Stand des betroffenen Total-Sensors.

**Die COP-Sensoren nicht anpassen** – sie berechnen sich bei jedem Blick direkt aus den beiden anderen Zählern und halten keinen eigenen Wert.

<img src="../../assets/home_assistant_verlauf_de.png" alt="Home Assistant Verlauf" style="width: 100%; max-width: 600px; height: auto; border-radius: 8px;">

## Startwert oder Korrektur über einen Offset setzen

1. Ermitteln Sie den gewünschten Ausgangswert (siehe oben).
2. Tragen Sie ihn in `lambda_wp_config.yaml` unter `energy_consumption_offsets` (bzw. `cycling_offsets` für Zyklenzähler) ein – nur für **Total**-Sensoren, in **kWh**:

   ```yaml
   energy_consumption_offsets:
     hp1:
       heating_energy_total: 1234.56
       heating_thermal_energy_total: 2200.0
   ```

3. Integration neu laden (oder Home Assistant neu starten).

Der Offset wird beim Hinzufügen der Entity **einmalig** angewendet und übersteht sowohl den nächsten Poll als auch jeden weiteren Neustart – ändert sich der Offset später, wird nur die **Differenz** zum vorher angewendeten Wert addiert, nie der volle Betrag erneut.

Ausführliche Anleitung, alle Szenarien und negative Offsets: [Offsets – Historische Daten übernehmen](offsets.md).

## Entity-IDs finden

Die genauen Entity-IDs Ihrer Sensoren finden Sie unter **Einstellungen** → **Geräte & Dienste** → **Geräte** → Ihre Lambda-Integration → gewünschte Wärmepumpe → Entitäten.

## Kurz zusammengefasst

| Ziel | Vorgehen |
|------|----------|
| Startwert für einen Total-Zähler setzen (Wärmepumpenwechsel, historische Werte) | `energy_consumption_offsets` bzw. `cycling_offsets` in `lambda_wp_config.yaml` |
| Falschen Total-Wert korrigieren | Gleicher Weg: Differenz als (ggf. negativen) Offset eintragen |
| Entity-IDs Ihrer Sensoren finden | **Einstellungen** → **Geräte & Dienste** → **Geräte** → Lambda Heat Pumps → gewünschte Wärmepumpe → Entities |

Weitere Informationen zu den Sensoren und zur Berechnung: [Energie- und Wärmeverbrauchsberechnung](Energieverbrauchsberechnung.md), [COP-Sensoren](cop-sensoren.md), [Offsets](offsets.md).
