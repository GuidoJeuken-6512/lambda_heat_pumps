# Changelog

**Deutsche Version siehe unten / [German version see below](#deutsche-version)**

> 📜 Full version history: [CHANGELOG_ALL_CHANGES.md](CHANGELOG_ALL_CHANGES.md) · Vollständige Versionshistorie: [CHANGELOG_ALL_CHANGES.md](CHANGELOG_ALL_CHANGES.md)

<!-- lang:en -->
## English Version

> **📚 Documentation**: A German documentation is currently being built at [https://guidojeuken-6512.github.io/lambda_heat_pumps](https://guidojeuken-6512.github.io/lambda_heat_pumps)

### [2.7.0] - 2026-07-12

#### Bug Fixes
- **Umlauts in device name no longer break energy sensor lookup** ([#93](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/93)): When the integration's device name contained umlauts (e.g. `Wärmepumpe`), the internal fallback lookup for the own energy consumption sensor always returned `None`. Home Assistant's entity registry silently transliterates umlauts on first entity creation (e.g. `ä` → `a`), so the actual entity ID was `sensor.warmepumpe_hp1_…` while the lookup constructed `sensor.wärmepumpe_hp1_…`. A new helper function `slugify_name_prefix_for_lookup()` now applies the same transliteration for read-only state lookups, so the names match. The fix is limited to the two read-only lookup sites (`coordinator.py`); all `unique_id`-generating paths remain unchanged to avoid orphaning existing entities.
- **Wrong 32-bit register order default on newest firmware**: The firmware-dependent default for `int32_register_order` (introduced in this release) was `"high_first"` for every firmware entry, including the two newest (`V1.1.0-3K`, `V0.0.10-3K`). Those two now default to `"low_first"` in `FIRMWARE_CONFIG`, matching the register order actually used by that firmware generation. A manual `int32_register_order` override in `lambda_wp_config.yaml` still takes precedence and is unaffected.

<!-- /lang:en -->
## Deutsche Version {#deutsche-version}

<!-- lang:de -->

> **📚 Dokumentation**: Eine deutsche Dokumentation wird derzeit unter [https://guidojeuken-6512.github.io/lambda_heat_pumps](https://guidojeuken-6512.github.io/lambda_heat_pumps) aufgebaut

### [2.7.0] - 2026-07-12

#### Fehlerbehebungen
- **Umlaute im Gerätenamen führen nicht mehr zu fehlgeschlagenem Energie-Sensor-Lookup** ([#93](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/93)): Enthielt der Gerätename der Integration Umlaute (z. B. `Wärmepumpe`), lieferte der interne Fallback-Lookup für den eigenen Energieverbrauchs-Sensor stets `None`. Home Assistants Entity Registry transliteriert Umlaute beim ersten Anlegen einer Entity intern (z. B. `ä` → `a`), sodass die tatsächliche Entity-ID `sensor.warmepumpe_hp1_…` lautete, der Lookup aber `sensor.wärmepumpe_hp1_…` konstruierte. Eine neue Hilfsfunktion `slugify_name_prefix_for_lookup()` wendet nun dieselbe Transliteration für rein lesende Status-Lookups an, sodass die Namen übereinstimmen. Der Fix beschränkt sich auf die zwei rein lesenden Lookup-Stellen (`coordinator.py`); alle `unique_id`-erzeugenden Pfade bleiben unverändert, um bestehende Entities nicht zu verwaisen.
- **Falscher Default für 32-Bit-Register-Reihenfolge bei neuester Firmware**: Der in diesem Release eingeführte firmware-abhängige Default für `int32_register_order` stand für alle Firmware-Einträge auf `"high_first"`, auch für die beiden neuesten (`V1.1.0-3K`, `V0.0.10-3K`). Diese beiden stehen in `FIRMWARE_CONFIG` nun auf `"low_first"`, passend zur tatsächlich von dieser Firmware-Generation verwendeten Register-Reihenfolge. Ein manueller `int32_register_order`-Override in `lambda_wp_config.yaml` hat weiterhin Vorrang und ist davon nicht betroffen.

<!-- /lang:de -->
