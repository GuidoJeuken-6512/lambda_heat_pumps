---
title: "Heatpump Flow Card"
---

# Heatpump Flow Card

*Zuletzt geändert am 30.10.2026*

Vielen Dank an Sturmi77 für diese schöne FlowCard! 

Eine externe Dashboard-Karte, die die Wärmepumpen-Anlage als animiertes hydraulisches Schaltschema darstellt.

![Heatpump Flow Card Demo](https://raw.githubusercontent.com/Sturmi77/heatpump-flow-card/main/docs/demo.gif)

## Was die Karte zeigt

- **Energiefluss:** PV-Überschuss, Batterie oder Netzbezug in die Wärmepumpe
- **Diverter-Ventil:** Schaltung zwischen Warmwasser und Heizung, mit animiertem Volumenstrom
- **Speicher:** Warmwassertank und Puffer mit Temperaturgradient
- **Heizkreise:** Fußbodenheizung oder Heizkörper
- **Live-Werte:** COP-Momentanwert, täglicher COP für Heizung und Warmwasser, Verdichter-Starts, Abtauzyklus, Fehlernummern
- **Außentemperatur und Raumtemperatur**

## Installation

Die Karte wird über [HACS](https://hacs.xyz/) als Custom Repository installiert:

1. **HACS öffnen** → Custom Repositories
2. **Repository hinzufügen:**
   - URL: `https://github.com/Sturmi77/heatpump-flow-card`
   - Kategorie: `Lovelace`
3. **Installieren** und HA neustarten

Die Karte ist auch im [HACS Default Store](https://hacs.xyz/docs/faq/custom_repositories#can-i-add-a-repository-to-the-default-store) gelistet (Genehmigung ausstehend).

## Konfiguration für Lambda Heat Pumps

Keine Entity-Zuordnung nötig — die Karte erkennt automatisch:

```yaml
type: custom:heatpump-flow-card
preset: lambda
```

**Optionale Anpassungen im UI-Editor:**
- Wärmepumpen-Index (bei mehreren HP)
- Boiler-, Puffer- und Heizkreis-Indizes
- Anzeigeoptionen

Die Karte erkennt automatisch:
- beide Entity-Namensformen: `sensor.eu08l_hp1_…` (legacy) und `sensor.hp1_…` (neu)
- alle Betriebsmodi der Lambda (Heizen, Warmwasser, Abtau, etc.)

## Weitere Informationen

- **Repository:** [Sturmi77/heatpump-flow-card](https://github.com/Sturmi77/heatpump-flow-card)
- **Lizenz:** MIT
- **Maintainer:** @Sturmi77

## Verwandte Vorlagen

- [Lambda Heizkurven Card](Lambda_heizkurve_card.md) — Interaktive Heizkurven-Visualisierung
- [Energy Dashboard](Lambda_energy_dashboard.md) — Energieverbräuche und -bilanzen
