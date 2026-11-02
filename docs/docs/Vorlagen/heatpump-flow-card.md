---
title: "Heat Pump Hydraulic Card"
---

# Heat Pump Hydraulic Card

*Zuletzt geändert am 02.11.2026*

Vielen Dank an Sturmi77 für diese Karte!

Eine externe Dashboard-Karte, die die Wärmepumpen-Anlage als animiertes hydraulisches Schaltschema darstellt (früher „Heatpump Flow Card“).

![Heat Pump Hydraulic Card](https://raw.githubusercontent.com/Sturmi77/heatpump-hydraulic-card/v0.17.0/docs/release-0.17.png)

## Was die Karte zeigt

- **Energiefluss:** PV, Batterie und Netzbezug in die Wärmepumpe, aus dem Energie-Dashboard oder eigenen Sensoren
- **Umschaltventil:** zwischen Warmwasser und Heizung, mit animiertem Volumenstrom
- **Speicher:** Warmwasserspeicher und Puffer mit Temperaturverlauf, Heizstäbe (2. Heizstufe)
- **Heizkreise:** bis zu sechs (Fußbodenheizung, Platten- oder Gliederheizkörper), optional mit Mischer; das Haus zeigt Raumtemperatur und Raum-Soll jedes Heizkreises
- **Live-Werte:** COP, Abtauen, Fehlernummern, 24-Stunden-Zeitleiste, Kennzahl-Kacheln (COP, Energie, Starts …), Detailbereich mit Kältekreis, Schnellbedienung
- **PV-Überschuss:** Überschussbetrieb des Lambda E-Managers als Chip und als eigene Phase in der Zeitleiste
- **Sprachen:** Deutsch, Englisch, Niederländisch, Slowakisch, Tschechisch

## Installation

Die Karte ist im HACS Default Store gelistet:

1. HACS öffnen und nach **Heat Pump Hydraulic Card** suchen
2. Herunterladen
3. Browser neu laden (ein Neustart von Home Assistant ist nicht nötig)

## Konfiguration für Lambda Heat Pumps

Keine Entity-Zuordnung nötig. Wird die Karte über die Kartenauswahl hinzugefügt, erkennt sie die Lambda-Integration selbst:

```yaml
type: custom:heatpump-hydraulic-card
preset: lambda
```

Die bisherige Angabe `type: custom:heatpump-flow-card` funktioniert weiterhin, bestehende Dashboards müssen nicht geändert werden.

Die Karte erkennt automatisch:

- beide Entity-Namensformen: `sensor.eu08l_hp1_…` (legacy) und `sensor.hp1_…` (neu)
- alle Betriebsmodi der Lambda (Heizen, Warmwasser, Abtauen …)

Bei mehreren Wärmepumpen oder falscher Erkennung lassen sich Präfix (`prefix: eu08l`) und Gerätenummern (`index: {hp: 2, hc: 2}`) angeben. Weitere Optionen im UI-Editor: Heizkreise, Anzeige, Kacheln und Farben.

## Weitere Informationen

- **Repository:** [Sturmi77/heatpump-hydraulic-card](https://github.com/Sturmi77/heatpump-hydraulic-card)
- **Lambda-Seite der Karte:** [docs/presets/lambda.md](https://github.com/Sturmi77/heatpump-hydraulic-card/blob/main/docs/presets/lambda.md)
- **Live-Demo ohne Home Assistant:** [sturmi77.github.io/heatpump-hydraulic-card/demo](https://sturmi77.github.io/heatpump-hydraulic-card/demo/)
- **Lizenz:** MIT
- **Maintainer:** @Sturmi77

## Verwandte Vorlagen

- [Lambda Heizkurven Card](Lambda_heizkurve_card.md) — Interaktive Heizkurven-Visualisierung
- [Energy Dashboard](Lambda_energy_dashboard.md) — Energieverbräuche und -bilanzen
