---
title: "Attribute eines Sensors auslesen"
---

# Attribute auslesen

*Zuletzt geändert am 17.10.2026*

Attribute sind Zusatzinformationen einer Entität neben ihrem Wert, z. B. Einheit, Geräteklasse oder Anzeigename.

!!! info "Seit Version 3.5 kein Attribut `register` mehr"
    Bis Version 2.x trug jeder Sensor ein Attribut `register` mit seiner Modbus-Adresse. In Version 3.5 gibt es dieses Attribut nicht mehr. Die Register-Adresse eines Sensors finden Sie in der [Sensorübersicht für Entwickler](../Entwickler/sensoren-uebersicht.md): Dort steht die Adresse relativ zum Modul, die tatsächliche Adresse ergibt sich aus der Basisadresse des Moduls (z. B. HP1 = 1000, HC1 = 5000).

    Das einzige eigene Attribut der Integration ist `applied_offset` an den Gesamtzählern: der Offset aus der `lambda_wp_config.yaml`, der im Wert bereits enthalten ist (siehe [Offsets](offsets.md)).

## Über den Sensor

<div style="display: flex; gap: 20px; align-items: flex-start; margin: 20px 0; flex-wrap: wrap;">
  <div style="flex: 0 0 50%; min-width: 300px;">
    <img src="../assets/find_register_de.png" alt="Detailansicht eines Sensors mit geöffnetem Menü und dem Eintrag „Attribute“" style="width: 100%; height: auto; border-radius: 8px;">
  </div>
  <div style="flex: 1; min-width: 300px;">
    <p>Die Detailansicht des Sensors öffnen und über die „⋮“ auf <strong>Attribute</strong> klicken.</p>
    <p>Dann werden die Attribute sichtbar.</p>
    <img src="../assets/baustelle_3_5.svg" alt="Baustelle: Screenshot der Attribut-Ansicht in Version 3.5 folgt" style="width: 100%; height: auto; border-radius: 8px; margin-top: 20px;">
  </div>
</div>

## Über die Entwicklerwerkzeuge

Unter **Entwicklerwerkzeuge** → **Zustände** den Sensor über seinen Namen suchen. In der rechten Spalte stehen alle Attribute.

<img src="../assets/baustelle_3_5.svg" alt="Baustelle: Screenshot der Entwicklerwerkzeuge mit den Attributen eines Sensors in Version 3.5 folgt" style="width:100%;max-width:650px;margin:20px 0;border-radius:8px;">

## Über ein Jinja2 Template

Unter **Entwicklerwerkzeuge** → **Template** eingeben:

```jinja2
{% set entity_id = 'sensor.eu08l_hc1_flow_line_temperature' %}
{% if states[entity_id] is defined %}
Zustand: {{ states[entity_id].state }}
{% for k in states[entity_id].attributes.keys() %}
- {{ k }}: {{ states[entity_id].attributes[k] }}
{% endfor %}
{% else %}
Sensor nicht verfügbar.
{% endif %}
```
