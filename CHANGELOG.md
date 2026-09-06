# Changelog

**Deutsche Version siehe unten / [German version see below](#deutsche-version)**

> 📜 Full version history: [CHANGELOG_ALL_CHANGES.md](CHANGELOG_ALL_CHANGES.md) · Vollständige Versionshistorie: [CHANGELOG_ALL_CHANGES.md](CHANGELOG_ALL_CHANGES.md)

<!-- lang:en -->
## English Version

> **📚 Documentation**: A German documentation is currently being built at [https://guidojeuken-6512.github.io/lambda_heat_pumps](https://guidojeuken-6512.github.io/lambda_heat_pumps)

### [3.5.2] - 2026-09-06

Follow-up to the 3.5.0 rewrite adoption: fixed three gaps found by auditing every 2.7.x/2.8.x bugfix from the pre-rewrite `main` branch against the rewritten codebase — a `via_device` deprecation warning on sub-devices, a `0xFFFF` sentinel ("no request"/"no external sensor") read as a real value (e.g. exactly -300.0 °C for the outside temperature), and Modbus reads/writes not actually being serialized against each other (the class of issue behind #105). See [CHANGELOG_ALL_CHANGES.md](CHANGELOG_ALL_CHANGES.md) for details and the new regression tests.

### [3.5.0] - 2026-09-06

Adopted a ground-up rewrite of the integration (PR #115): the Modbus layer moves from `pymodbus` to [`modbus-connection`](https://github.com/home-assistant-libs/modbus-connection)/`tmodbus`, heat pumps and other modules are addressed by index and object reference instead of reconstructed entity-id strings (removing the bug class behind Issues #93/#107), and counters persist via plain Home Assistant `RestoreSensor`s. Minimum Home Assistant version is now 2026.9.0. See [CHANGELOG_ALL_CHANGES.md](CHANGELOG_ALL_CHANGES.md) for the full breakdown.

### [2.6.0] - 2026-06-24

#### New Features
- **Cooling Circuit Climate Entity**: New `climate.<prefix>_hc<n>_cooling_circuit` entity per detected heating circuit, analogous to the existing `heating_circuit` climate entity. Shares the same current-temperature source (room device temperature) as `heating_circuit`, but writes its setpoint to the dedicated cooling setpoint register (offset 52, e.g. register 5052 for HC1, 5152 for HC2, …). Disabled by default — enable via the new `cooling_mode_enabled` option in the integration's Options Flow.

<!-- /lang:en -->
## Deutsche Version {#deutsche-version}

<!-- lang:de -->

> **📚 Dokumentation**: Eine deutsche Dokumentation wird derzeit unter [https://guidojeuken-6512.github.io/lambda_heat_pumps](https://guidojeuken-6512.github.io/lambda_heat_pumps) aufgebaut

### [3.5.2] - 2026-09-06

Nachzieharbeiten zur 3.5.0-Rewrite-Übernahme: drei Lücken behoben, gefunden bei der Prüfung aller 2.7.x/2.8.x-Bugfixes des Vor-Rewrite-Branches `main` gegen den neu geschriebenen Code — eine `via_device`-Deprecation-Warnung bei Sub-Geräten, ein als echter Wert gelesener `0xFFFF`-Sonderwert ("keine Anforderung"/"kein externer Sensor", z. B. exakt -300,0 °C bei der Außentemperatur) sowie nicht tatsächlich serialisierte Modbus-Lese-/Schreibvorgänge (dieselbe Fehlerklasse wie Issue #105). Details und die neuen Regressionstests siehe [CHANGELOG_ALL_CHANGES.md](CHANGELOG_ALL_CHANGES.md).

### [3.5.0] - 2026-09-06

Übernahme eines von Grund auf neu geschriebenen Codes für die Integration (PR #115): Die Modbus-Schicht wechselt von `pymodbus` zu [`modbus-connection`](https://github.com/home-assistant-libs/modbus-connection)/`tmodbus`, Wärmepumpen und andere Module werden über Index und Objektreferenz statt rekonstruierter entity_id-Strings adressiert (behebt die Fehlerklasse hinter den Issues #93/#107), und Zähler persistieren über normale Home-Assistant-`RestoreSensor`s. Mindest-Home-Assistant-Version ist jetzt 2026.9.0. Vollständige Aufschlüsselung siehe [CHANGELOG_ALL_CHANGES.md](CHANGELOG_ALL_CHANGES.md).

### [2.6.0] - 2026-06-24

#### Neue Funktionen
- **Kühlkreis-Climate-Entity**: Neue Entity `climate.<prefix>_hc<n>_cooling_circuit` je erkanntem Heizkreis, analog zur bestehenden `heating_circuit`-Climate-Entity. Nutzt dieselbe Quelle für die Ist-Temperatur (Raum-Gerätetemperatur) wie `heating_circuit`, schreibt den Sollwert aber auf das dedizierte Kühl-Sollwert-Register (Offset 52, z. B. Register 5052 für HC1, 5152 für HC2, …). Standardmäßig deaktiviert — Aktivierung über die neue Option `cooling_mode_enabled` im Options-Flow der Integration.

<!-- /lang:de -->
