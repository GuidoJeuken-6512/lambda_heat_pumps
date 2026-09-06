---
title: "unique_id und name_prefix"
---

# unique_id und name_prefix

*Zuletzt geändert am 06.09.2026*

**Stand:** Release 3.5.2 (Rewrite auf [`modbus-connection`](https://github.com/home-assistant-libs/modbus-connection)/`tmodbus`, Branch `3.5`; Hintergrund zum Rewrite: [Issue #99](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/99))

Diese Seite beschreibt, wie `unique_id` heute gebildet wird und warum das
früher hier dokumentierte Problem (unique_id ändert sich mit dem
Anzeigenamen) für neue Installationen gar nicht mehr entstehen kann.

## Zwei Modi, ein Flag

`LambdaEntity.__init__` (`entity.py`) bildet die `unique_id` abhängig von
`CONF_USE_LEGACY_MODBUS_NAMES`:

```python
prefix = entry.data[CONF_NAME_PREFIX].lower().replace(" ", "")
legacy = f"{prefix}_" if entry.data[CONF_USE_LEGACY_MODBUS_NAMES] else ""
module_prefix = f"{module}{index}_" if module else ""
self._attr_unique_id = f"{legacy}{module_prefix}{key}"
```

| Modus | unique_id | Wer bekommt ihn |
|---|---|---|
| Legacy (`use_legacy_modbus_names=True`) | `{name_prefix}_{module}{index}_{key}` | Jede Config-Entry, die vor 3.5 angelegt wurde (per Migration auf `True` gesetzt) |
| Standard (`use_legacy_modbus_names=False`) | `{module}{index}_{key}` — **ohne** `name_prefix` | Jede Config-Entry, die ab 3.5 neu angelegt wird (`config_flow.py` setzt das Flag explizit auf `False`) |

Das Flag wird **einmalig** beim Anlegen der Entry gesetzt und ändert sich
danach nie mehr — auch nicht, wenn der Nutzer später den Anzeigenamen ändert.

## Warum das die alte Kopplung auflöst

Für **neue** Installationen (Standard-Modus) taucht `name_prefix` in der
`unique_id` überhaupt nicht mehr auf — eine Umbenennung der Integration kann
sie also gar nicht mehr berühren. Für **bestehende** Installationen
(Legacy-Modus) bleibt die `unique_id` bewusst exakt in der Form erhalten, mit
der sie ursprünglich registriert wurde: Der `entity.py`-Docstring hält das
ausdrücklich fest —

> *„The unique-id shape here is load-bearing: it is what keeps an existing
> installation's entities attached to their history."*

Eine spätere Umbenennung der Integration in Home Assistant ändert dort nur den
Anzeigenamen (`entry.data[CONF_NAME_PREFIX]`), nicht `use_legacy_modbus_names`
und damit auch nicht mehr, welchen Wert `prefix` in der obigen Formel annimmt
— **außer** in genau dem einen Fall, den der Legacy-Modus absichtlich
konserviert: `prefix` wird bei jedem Setup neu aus dem aktuellen
Anzeigenamen berechnet. Wer eine Legacy-Installation umbenennt, verschiebt
also weiterhin alle `unique_id`s auf einmal — das ist unverändert zum
Verhalten vor 3.5. Der Unterschied ist, dass **jede ab 3.5 neu eingerichtete**
Installation dieses Risiko von vornherein nicht hat, weil ihre `unique_id`
den Namen nie enthält.

## Was aus der ursprünglich geplanten Migration wurde

Eine frühere Fassung dieser Seite skizzierte eine geplante Migration
(„Version 9: `entry_id`-basierte unique_id für alle Installationen“, über
`entity_registry.async_update_entity()`). Diese Migration wurde **nicht**
umgesetzt. Stattdessen entkoppelt der Rewrite `unique_id` und `name_prefix`
nur für neue Installationen (siehe Tabelle oben); bestehende Installationen
behalten ihr angestammtes Schema unverändert bei, statt einmalig umgeschrieben
zu werden. `ENTRY_VERSION` in `const.py` ist zwar mittlerweile bei `9`
angekommen, aber aus einem anderen Grund — siehe
[Migrationssystem](migration-system.md).
