---
title: "Entity-Duplikate (_2, _3) – Cleanup"
---

# Entity-Duplikate (_2, _3) – Cleanup

*Zuletzt geändert am 06.09.2026*

**Stand:** Release 3.5.2 (Rewrite auf [`modbus-connection`](https://github.com/home-assistant-libs/modbus-connection)/`tmodbus`, Branch `3.5`; Hintergrund zum Rewrite: [Issue #99](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/99))

Diese Seite beschreibt, warum die Integration seit dem 3.5-Rewrite **keinen**
aktiven Cleanup-Durchlauf für doppelt angelegte Entities (`sensor.xyz_2`,
`climate.xyz_3`) mehr braucht.

## `entity_id` ist nur ein Vorschlag

`LambdaEntity.__init__` (`entity.py`) setzt `self.entity_id` explizit auf einen
selbst gebildeten Wert:

```python
if self._entity_domain:
    object_id = slugify(f"{prefix}_{module_prefix}{key}")
    self.entity_id = f"{self._entity_domain}.{object_id}"
```

Das ist bewusst ein **Vorschlag**, kein Zwang: Home Assistant löst eine
Kollision mit einer bereits registrierten `entity_id` genauso auf wie bei jeder
anderen Integration auch — über den eingebauten `_2`/`_3`-Suffix-Mechanismus
der Entity-Registry. Eine bereits registrierte Entity behält ohnehin ihre
bestehende `entity_id`; der Vorschlag wird nur beim allerersten Anlegen
verwendet.

## Warum das früher ein eigenes Problem war

In der Vor-Rewrite-Integration wurde die `entity_id` aus dem **übersetzten**
Anzeigenamen abgeleitet. Zwei unterschiedliche Namen konnten dabei auf denselben
Slug abbilden (z. B. „Heizkurve-22°C“ und „Heizkurve+22°C“ → beide
`heizkurve22c`), was bei jedem Neustart erneut Duplikat-Suffixe erzeugte, die
eine eigene Bereinigungsfunktion (`migration.py::async_remove_duplicate_entity_suffixes`)
regelmäßig entfernen musste.

Der Rewrite behebt die Ursache statt das Symptom zu bereinigen: Der
`entity_id`-Vorschlag wird aus dem **unübersetzten Register-Schlüssel**
gebildet (`slugify(f"{prefix}_{module_prefix}{key}")`, siehe
[Ablaufdiagramm – Entity-Klassen](Ablaufdiagramm.md#4-entity-klassen-und-device-hierarchie)),
der sprachunabhängig und pro Sensor eindeutig ist. Zwei verschiedene Sensoren
schlagen also nie mehr dieselbe `entity_id` vor, und eine eigene
Bereinigungsfunktion ist überflüssig geworden — `migration.py` mit der
alten Cleanup-Funktion existiert nicht mehr.

## Was `unique_id` betrifft

Das eigentlich unveränderliche Merkmal einer Entity, die `unique_id`, war von
diesem Problem nie betroffen und ändert sich weiterhin nie automatisch. Details
dazu: [unique_id – Kopplung an name_prefix](unique-id-name-prefix-kopplung.md).
