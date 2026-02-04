---
title: "Lambda Energy Dashboard"
---

# Lambda Energy Dashboard (Vorlage)

### ⚠️ ⚠️ Achtung, dies dashboard nebötigt Sensoren, die erst mit der Version 2.3 der Lambda Integration herauskommen. Mit der aktuellen Version 2.2 werden viele Werte nicht gefunden

Diese Vorlage erstellt ein Lovelace-Dashboard **„lambda Energy“** mit vier Spalten: **Täglich**, **Monatlich**, **Jährlich** und **Total**. Pro Spalte werden für Heizen, Warmwasser, Kühlen und Abtauen die elektrische Energie, die thermische Energie und der COP angezeigt (Abtau ohne COP).

<a href="../../assets/dashboard-lambda-energy.png" target="_blank" rel="noopener noreferrer" title="Bild groß öffnen"><img src="../../assets/dashboard-lambda-energy.png" alt="Lambda Energy Dashboard" width="600" style="max-width: 100%; height: auto;" /></a>

## Einbindung in Home Assistant

1. **Einstellungen** → **Dashboard** → **„+ Dashboard“** → **„Importieren“**  
   oder ein bestehendes Dashboard bearbeiten und den Inhalt einfügen.
2. Den unten stehenden YAML-Code kopieren und einfügen.
3. **Variable anpassen:** Einmal **`ENTITY_PREFIX`** durch deinen Entity-Präfix ersetzen (z. B. `eu08l_hp1` oder `lambda_hp1` – aus **Einstellungen** → **Geräte & Dienste** → **Geräte** → deine Lambda-Integration). Suchen & Ersetzen: `ENTITY_PREFIX` → dein_präfix.

## YAML (Copy & Paste)

Oben im YAML ist die Variable **ENTITY_PREFIX** dokumentiert; unten werden die Entity-IDs daraus zusammengesetzt (`sensor.ENTITY_PREFIX_heating_energy_daily` usw.). Einmal ersetzen, dann funktioniert das gesamte Dashboard.

```yaml
# Variable (einmal ersetzen): ENTITY_PREFIX = eu08l_hp1
title: lambda Energy
views:
  - title: lambda Energy
    path: lambda-energy
    panel: true
    cards:
      - type: horizontal-stack
        cards:
          - type: vertical-stack
            cards:
              - type: markdown
                content: "## Täglich"
              - type: entities
                title: Heizen
                entities:
                  - entity: sensor.ENTITY_PREFIX_heating_energy_daily
                  - entity: sensor.ENTITY_PREFIX_heating_thermal_energy_daily
                  - entity: sensor.ENTITY_PREFIX_heating_cop_daily
              - type: entities
                title: Warmwasser
                entities:
                  - entity: sensor.ENTITY_PREFIX_hot_water_energy_daily
                  - entity: sensor.ENTITY_PREFIX_hot_water_thermal_energy_daily
                  - entity: sensor.ENTITY_PREFIX_hot_water_cop_daily
              - type: entities
                title: Kühlen
                entities:
                  - entity: sensor.ENTITY_PREFIX_cooling_energy_daily
                  - entity: sensor.ENTITY_PREFIX_cooling_thermal_energy_daily
                  - entity: sensor.ENTITY_PREFIX_cooling_cop_daily
              - type: entities
                title: Abtauen
                entities:
                  - entity: sensor.ENTITY_PREFIX_defrost_energy_daily
                  - entity: sensor.ENTITY_PREFIX_defrost_thermal_energy_daily
          - type: vertical-stack
            cards:
              - type: markdown
                content: "## Monatlich"
              - type: entities
                title: Heizen
                entities:
                  - entity: sensor.ENTITY_PREFIX_heating_energy_monthly
                  - entity: sensor.ENTITY_PREFIX_heating_thermal_energy_monthly
                  - entity: sensor.ENTITY_PREFIX_heating_cop_monthly
              - type: entities
                title: Warmwasser
                entities:
                  - entity: sensor.ENTITY_PREFIX_hot_water_energy_monthly
                  - entity: sensor.ENTITY_PREFIX_hot_water_thermal_energy_monthly
                  - entity: sensor.ENTITY_PREFIX_hot_water_cop_monthly
              - type: entities
                title: Kühlen
                entities:
                  - entity: sensor.ENTITY_PREFIX_cooling_energy_monthly
                  - entity: sensor.ENTITY_PREFIX_cooling_thermal_energy_monthly
                  - entity: sensor.ENTITY_PREFIX_cooling_cop_monthly
              - type: entities
                title: Abtauen
                entities:
                  - entity: sensor.ENTITY_PREFIX_defrost_energy_monthly
                  - entity: sensor.ENTITY_PREFIX_defrost_thermal_energy_monthly
          - type: vertical-stack
            cards:
              - type: markdown
                content: "## Jährlich"
              - type: entities
                title: Heizen
                entities:
                  - entity: sensor.ENTITY_PREFIX_heating_energy_yearly
                  - entity: sensor.ENTITY_PREFIX_heating_thermal_energy_yearly
                  - entity: sensor.ENTITY_PREFIX_heating_cop_yearly
              - type: entities
                title: Warmwasser
                entities:
                  - entity: sensor.ENTITY_PREFIX_hot_water_energy_yearly
                  - entity: sensor.ENTITY_PREFIX_hot_water_thermal_energy_yearly
                  - entity: sensor.ENTITY_PREFIX_hot_water_cop_yearly
              - type: entities
                title: Kühlen
                entities:
                  - entity: sensor.ENTITY_PREFIX_cooling_energy_yearly
                  - entity: sensor.ENTITY_PREFIX_cooling_thermal_energy_yearly
                  - entity: sensor.ENTITY_PREFIX_cooling_cop_yearly
              - type: entities
                title: Abtauen
                entities:
                  - entity: sensor.ENTITY_PREFIX_defrost_energy_yearly
                  - entity: sensor.ENTITY_PREFIX_defrost_thermal_energy_yearly
          - type: vertical-stack
            cards:
              - type: markdown
                content: "## Total"
              - type: entities
                title: Heizen
                entities:
                  - entity: sensor.ENTITY_PREFIX_heating_energy_total
                  - entity: sensor.ENTITY_PREFIX_heating_thermal_energy_total
                  - entity: sensor.ENTITY_PREFIX_heating_cop_total
              - type: entities
                title: Warmwasser
                entities:
                  - entity: sensor.ENTITY_PREFIX_hot_water_energy_total
                  - entity: sensor.ENTITY_PREFIX_hot_water_thermal_energy_total
                  - entity: sensor.ENTITY_PREFIX_hot_water_cop_total
              - type: entities
                title: Kühlen
                entities:
                  - entity: sensor.ENTITY_PREFIX_cooling_energy_total
                  - entity: sensor.ENTITY_PREFIX_cooling_thermal_energy_total
                  - entity: sensor.ENTITY_PREFIX_cooling_cop_total
              - type: entities
                title: Abtauen
                entities:
                  - entity: sensor.ENTITY_PREFIX_defrost_energy_total
                  - entity: sensor.ENTITY_PREFIX_defrost_thermal_energy_total
```

## Hinweise

- **panel: true** sorgt dafür, dass die View die volle Seitenbreite nutzt.
- Die Entity-IDs basieren auf der Lambda Heat Pumps Integration; bei mehreren Wärmepumpen z. B. `hp2` verwenden und den Präfix anpassen.
