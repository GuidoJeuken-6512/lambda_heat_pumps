---
title: "FAQ – Known Issue: async_get_device-Deprecation-Warnung"
---

# Known Issue: Deprecation-Warnung zu `async_get_device()` im Log

*Zuletzt geändert am 09.09.2026*

## Symptom

Auf Installationen mit **Home Assistant >= 2026.9** erscheint bei jedem
Setup bzw. Reload der Integration eine Deprecation-Warnung im
HA-System-Log, die auf `device_registry.async_get_device()` verweist.

## Ursache

Sub-Devices (HP, HC, Boiler, Puffer, Solar) werden über `via_device_id`
mit dem Haupt-Device verknüpft. Um dessen Registry-ID aufzulösen, ruft
`build_subdevice_info()` in `utils.py` aktuell die generische
`async_get_device(identifiers=...)`-API auf. Home Assistant 2026.9
markiert diese API als deprecated zugunsten von
`async_get_device_by_identifier()` (bzw. `async_get_device_by_connection()`
oder `async_get_devices()`) und kündigt die Entfernung für
**HA 2027.8.0** an.

## Auswirkung

Rein kosmetisch: Es handelt sich ausschließlich um eine Log-Warnung, keine
Funktionseinbuße. Sub-Devices und ihre Entities werden weiterhin korrekt
angelegt und mit dem Haupt-Device verknüpft.

## Lösungsansatz / Status

Der Rewrite auf Branch `3.5` (Voraussetzung: HA >= 2026.9) hat diese
Deprecation bereits in Version 3.5.4 behoben, durch Umstellung auf
`async_get_device_by_identifier()`.

Für main/2.8.x ist bewusst **kein eigener Fix geplant**: main soll bis zur
angekündigten Entfernung der alten API in HA 2027.8.0 durch den Rewrite
(aktuell Branch `3.5`) abgelöst sein. Wer die Warnung vorher loswerden
möchte, kann auf Branch `3.5` wechseln. Bis dahin kann die Warnung
gefahrlos ignoriert werden.
