# Dashboard: Attribut „register“ dynamisch anzeigen

In **Entities-Karten** wird das Feld `name:` **nicht** als Jinja-Template ausgewertet – es wird als Text angezeigt. Daher erscheint dort z. B. `R{{ state_attr(...) }}` wörtlich.

Damit das Attribut `register` trotzdem genutzt werden kann, gibt es zwei Wege:

---

## 1. Template-Syntax für Attribute (wo HA Templates auswertet)

In Kontexten, in denen Home Assistant Jinja auswertet (z. B. Markdown-Karte, Automation, Template-Sensor), sind diese Varianten möglich:

| Ansatz | Syntax | Hinweis |
|--------|--------|--------|
| **state_attr** (empfohlen) | `{{ state_attr('sensor.eu08l_ambient_error_number', 'register') }}` | Sauber, funktioniert überall. |
| **states + attributes** | `{{ states['sensor.eu08l_ambient_error_number'].attributes.get('register') }}` | Vollständige Entity-Referenz. |
| **states mit Punkt** | `{{ states.sensor.eu08l_ambient_error_number.attributes }}` | Problematisch: `entity_id` enthält einen Punkt (`sensor.xxx`), die Auflösung kann fehlschlagen. Besser Klammer-Notation mit vollem `entity_id` verwenden. |
| **expand()** | `{{ expand("sensor.eu08l_ambient_error_number") }}` | **Nicht geeignet:** `expand()` erweitert Gruppen/Areas zu einer Liste von Entity-IDs und liefert **keine** Attribute. |

**Praktisch:** In diesem Dashboard werden **Markdown-Karten** mit `content:` verwendet; dort wird Jinja ausgewertet, und `state_attr(e, 'register')` funktioniert.

---

## 2. Wo das Template ausgewertet wird

- **Markdown-Karte** (`type: markdown`, `content: |` mit Jinja): wird ausgewertet → Register-Anzeige möglich.
- **Entities-Karte** (`name: "{{ ... }}"`): wird **nicht** ausgewertet → nur statischer Text.
- **Template-Sensor, Automation, Script:** werden ausgewertet → `state_attr('entity_id', 'register')` nutzbar.

Das Lambda-Register-Dashboard nutzt deshalb **Markdown-Karten** mit einer Schleife über die Entity-IDs und `state_attr(e, 'register')` / `state_attr(e, 'friendly_name')` / `states(e)` für die Tabelle.
