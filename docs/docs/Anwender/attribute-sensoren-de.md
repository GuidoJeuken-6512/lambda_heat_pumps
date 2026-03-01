---
title: "Attribute eines Sensors auslesen"
---

# Attribute auslesen

Um die Attribute eines Sensors asuzulesen gibt es mehrere Möglichkeiten.

## Über den Sensor

<div style="display: flex; gap: 20px; align-items: flex-start; margin: 20px 0; flex-wrap: wrap;">
  <div style="flex: 0 0 50%; min-width: 300px;">
    <img src="../../assets/find_register_de.png" alt="Attribute eines Sensors" style="width: 100%; height: auto; border-radius: 8px;">
  </div>
  <div style="flex: 1; min-width: 300px;">
    <p>Die Detailansicht des Sensors öffnen und über die "..." auf Attribute abspringen.</p>
    <p>Dann werden die Attribute sichtbar.</p>
    <img src="../../assets/register_sensor_de.png" alt="Register Sensor" style="width: 100%; height: auto; border-radius: 8px; margin-top: 20px;">
  </div>
</div>

## Über die Entwicklertools

In den Entwicklertools über den Namen den Sensor suchen, in der rechten Spalte sind alle Attribute zu finden.
<img src="../../assets/attributes_sensor_devtools_de.png" alt="Attribute eines Sensors in den Entwicklertools anzeigen" style="width:100%;max-width:650px;margin:20px 0;border-radius:8px;">

## Über ein Jinja2 Template

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