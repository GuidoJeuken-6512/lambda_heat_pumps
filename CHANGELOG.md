# Changelog

**Deutsche Version siehe unten / [German version see below](#deutsche-version)**

> 📜 Full version history: [CHANGELOG_ALL_CHANGES.md](CHANGELOG_ALL_CHANGES.md) · Vollständige Versionshistorie: [CHANGELOG_ALL_CHANGES.md](CHANGELOG_ALL_CHANGES.md)

<!-- lang:en -->
## English Version

> **📚 Documentation**: A German documentation is currently being built at [https://guidojeuken-6512.github.io/lambda_heat_pumps](https://guidojeuken-6512.github.io/lambda_heat_pumps)

### [2.6.0] - 2026-06-24

#### New Features
- **Cooling Circuit Climate Entity**: New `climate.<prefix>_hc<n>_cooling_circuit` entity per detected heating circuit, analogous to the existing `heating_circuit` climate entity. Shares the same current-temperature source (room device temperature) as `heating_circuit`, but writes its setpoint to the dedicated cooling setpoint register (offset 52, e.g. register 5052 for HC1, 5152 for HC2, …). Disabled by default — enable via the new `cooling_mode_enabled` option in the integration's Options Flow.

<!-- /lang:en -->
## Deutsche Version {#deutsche-version}

<!-- lang:de -->

> **📚 Dokumentation**: Eine deutsche Dokumentation wird derzeit unter [https://guidojeuken-6512.github.io/lambda_heat_pumps](https://guidojeuken-6512.github.io/lambda_heat_pumps) aufgebaut

### [2.6.0] - 2026-06-24

#### Neue Funktionen
- **Kühlkreis-Climate-Entity**: Neue Entity `climate.<prefix>_hc<n>_cooling_circuit` je erkanntem Heizkreis, analog zur bestehenden `heating_circuit`-Climate-Entity. Nutzt dieselbe Quelle für die Ist-Temperatur (Raum-Gerätetemperatur) wie `heating_circuit`, schreibt den Sollwert aber auf das dedizierte Kühl-Sollwert-Register (Offset 52, z. B. Register 5052 für HC1, 5152 für HC2, …). Standardmäßig deaktiviert — Aktivierung über die neue Option `cooling_mode_enabled` im Options-Flow der Integration.

<!-- /lang:de -->
