# Release 2.3

Alle Commits des Branches Release2.3 (seit Release2.2). Oben Stichpunkte mit Verlinkung zum Detail unten.

---

## Stichpunkte (Übersicht)

- [docs: Lambda Heizkurven-Card (Vorlage)](#heizkurven-card)
- [Merge branch 'Release2.3' (5b970a4)](#commit-1)
- [feat: add German and English translations for compressor start cycling sensor (477b743)](#commit-2)
- [Merge branch 'Release2.3' (dfca789)](#commit-3)
- [doku korrigiert (caff460)](#commit-4)
- [feat: add compressor start cycling sensor for yesterday's data (55f979b)](#commit-5)
- [Maximum boiler temperature aus Sensor-Templates entfernt (2f5031a)](#commit-6)
- [fix: improve raw value conversion for Modbus registers (e11ad7d)](#commit-7)
- [test: enhance energy consumption sensor tests and update assertions (5c54a50)](#commit-8)
- [feat: enhance energy sensor state management and persistence (28862bd)](#commit-9)
- [docs: update sensor templates and configuration documentation (34f954e)](#commit-10)
- [docs: remove obsolete image asset pv_surplus_de_3.png (7ca8c5f)](#commit-11)
- [docs: enhance config_flow options documentation (1de61a0)](#commit-12)
- [Merge branch 'Release2.3' (1e70c7d)](#commit-13)
- [docs: add Modbus integration comparison 2025.11 to 2025.12 (c4dfde7)](#commit-14)
- [docs: remove redundant line from PV-Überschuss-Modi section (7eff03c)](#commit-15)
- [chore: remove specific branch triggers from documentation workflow (8fecc70)](#commit-16)
- [docs: add PV Überschuss Steuerung section and related assets (cd56046)](#commit-17)
- [Refactor reset logic – ResetManager für alle Sensor-Typen (f6af7ff)](#commit-18)
- [Refactor energy consumption counter, yesterday sensors (d07f444)](#commit-19)
- [Arbeitszahlen COP für heizen/kühlen/Warmwasser (1479540)](#commit-20)
- [feat: add thermal energy consumption sensors and tracking logic (9dda198)](#commit-21)
- [manifest update (83f3f8b)](#commit-22)
- [Merge branch 'Release2.3' (2afa869)](#commit-23)
- [Doku ergänzt (ba9b0ed)](#commit-24)
- [feat: add state_class to sensor templates (31bb282)](#commit-25)
- [fix: update room thermostat offset range and Modbus conversion (208e358)](#commit-26)
- [docs: update Modbus documentation, heating curve typos (08a0a8e)](#commit-27)
- [docs: fix link case sensitivity in installation guide for HACS (eeccd12)](#commit-28)
- [workflow changed (3535fa8)](#commit-29)
- [github workflow changed to work with current Release (91d3b53)](#commit-30)
- [Docu link in manifest corrected (ba2f7c9)](#commit-31)

---

## Commit-Details

<a id="heizkurven-card"></a>
### Lambda Heizkurven-Card (Vorlage)
- **Lovelace-Custom-Card** zur Darstellung der Heizkurve einer Lambda-Wärmepumpe: X-Achse Außentemperatur (22 °C bis -22 °C), Y-Achse Vorlauftemperatur (10–75 °C), Linie durch drei Stützpunkte und aktueller Betriebspunkt (roter Punkt) aus Sensoren.
- Y-Werte der Stützpunkte wahlweise fest oder aus Number-Entities (z. B. `heating_curve_warm_outside_temp`, `heating_curve_mid_outside_temp`, `heating_curve_cold_outside_temp`).
- Vorlage inkl. vollständigem JavaScript-Modul (ohne externe Bibliotheken), YAML-Konfiguration und Einrichtungsanleitung in der Doku.
- **Dokumentation:** [Vorlagen → Lambda_heizkurve_card](../Vorlagen/Lambda_heizkurve_card.md). Dateien: `docs/lovelace/lambda_heizkurve_card.js`, `dashboard_heizkurve.yaml`, `heizkurve_card.yaml`.

---

<a id="commit-1"></a>
### 1 · 5b970a4 – Merge branch 'Release2.3'
Merge branch 'Release2.3' of https://github.com/GuidoJeuken-6512/lambda_heat_pumps into Release2.3

---

<a id="commit-2"></a>
### 2 · 477b743 – feat: add German and English translations for compressor start cycling sensor
- Added translations for the new compressor start cycling sensor for yesterday's data in both German and English language files, enhancing localization support for users.

---

<a id="commit-3"></a>
### 3 · dfca789 – Merge branch 'Release2.3'
Merge branch 'Release2.3' of https://github.com/GuidoJeuken-6512/lambda_heat_pumps into Release2.3

---

<a id="commit-4"></a>
### 4 · caff460 – doku korrigiert
Dokumentationskorrekturen.

---

<a id="commit-5"></a>
### 5 · 55f979b – feat: add compressor start cycling sensor for yesterday's data
- Introduced a new sensor template for tracking the compressor start cycling values from yesterday, enhancing the monitoring capabilities of heat pump operations.
- Updated the sensor setup to include the new compressor start cycling sensor in the configuration.

---

<a id="commit-6"></a>
### 6 · 2f5031a – Maximum boiler temperature aus Sensor-Templates entfernt
- Removed the maximum boiler temperature configuration from the sensor templates by commenting it out for clarity and potential future use.
- Maximum boiler temperature reads the same register as target_high_temperature.

---

<a id="commit-7"></a>
### 7 · e11ad7d – fix: improve raw value conversion for Modbus registers
- Updated the conversion logic for signed int16 to unsigned for Modbus, ensuring proper handling of negative values using Two's Complement.
- Introduced a utility function `clamp_to_int16` to clamp values to the int16 range before conversion, enhancing robustness and preventing overflow issues.
- Added context to the clamping process for better debugging and clarity.

---

<a id="commit-8"></a>
### 8 · 5c54a50 – test: enhance energy consumption sensor tests and update assertions
- Updated test cases for async data updates to ensure the coordinator returns a data dictionary instead of None when no client is available or when a read error occurs.
- Improved mock setups in energy consumption sensor tests to accurately reflect state and attributes, ensuring proper handling of energy values and offsets.
- Added comments for clarity on the behavior of the tests and the expected outcomes.

---

<a id="commit-9"></a>
### 9 · 28862bd – feat: enhance energy sensor state management and persistence
- Introduced `_energy_sensor_states` to store the state and attributes of energy consumption entities for better persistence.
- Updated the coordinator to collect and save energy sensor states, ensuring values are preserved across restarts.
- Improved the logic for handling energy values in `set_energy_value()` to prevent decreases and avoid stale data overwrites.
- Enhanced documentation to clarify the new state management features and migration process for existing sensors.

---

<a id="commit-10"></a>
### 10 · 34f954e – docs: update sensor templates and configuration documentation
Update sensor templates and configuration documentation to include new device classes and firmware version changes.

---

<a id="commit-11"></a>
### 11 · 7ca8c5f – docs: remove obsolete image asset pv_surplus_de_3.png
Obsolete image asset removed from documentation.

---

<a id="commit-12"></a>
### 12 · 1de61a0 – docs: enhance config_flow options documentation
Improved layout and accessibility features in config_flow options documentation.

---

<a id="commit-13"></a>
### 13 · 1e70c7d – Merge branch 'Release2.3'
Merge branch 'Release2.3' of https://github.com/GuidoJeuken-6512/lambda_heat_pumps into Release2.3

---

<a id="commit-14"></a>
### 14 · c4dfde7 – docs: add Modbus integration comparison 2025.11 to 2025.12
Documentation of Modbus integration comparison for changes in Home Assistant from 2025.11 to 2025.12.

---

<a id="commit-15"></a>
### 15 · 7eff03c – docs: remove redundant line from PV-Überschuss-Modi section
Redundant line removed from PV-Überschuss-Modi section in configuration flow documentation.

---

<a id="commit-16"></a>
### 16 · 8fecc70 – chore: remove specific branch triggers from documentation workflow
Documentation workflow no longer triggers on specific branch only.

---

<a id="commit-17"></a>
### 17 · cd56046 – docs: add PV Überschuss Steuerung section and related assets
PV Überschuss Steuerung section and related assets added to documentation.

---

<a id="commit-18"></a>
### 18 · f6af7ff – Refactor reset logic – ResetManager für alle Sensor-Typen
Refactor reset logic by introducing ResetManager to centralize reset automations for all sensor types. Replace previous cycling automation functions with ResetManager methods, ensuring consistent handling of reset signals across daily, 2h, 4h, monthly, and yearly periods. Update documentation to reflect these changes and improve clarity on reset operations.

---

<a id="commit-19"></a>
### 19 · d07f444 – Refactor energy consumption counter, yesterday sensors
Refactor energy consumption counter to read current values directly from energy entities for accurate calculations. Update documentation to include new cycling and reset logic for yesterday sensors.

---

<a id="commit-20"></a>
### 20 · 1479540 – Arbeitszahlen COP für heizen/kühlen/Warmwasser
Arbeitszahlen für heizen / kühlen und Warmwasser eingeführt, als daily / monthly / total COP, Doku aktualisiert.

---

<a id="commit-21"></a>
### 21 · 9dda198 – feat: add thermal energy consumption sensors and tracking logic
Thermal energy consumption sensors and tracking logic for heat pumps added.

---

<a id="commit-22"></a>
### 22 · 83f3f8b – manifest update
Manifest aktualisiert.

---

<a id="commit-23"></a>
### 23 · 2afa869 – Merge branch 'Release2.3'
Merge branch 'Release2.3' of https://github.com/GuidoJeuken-6512/lambda_heat_pumps into Release2.3

---

<a id="commit-24"></a>
### 24 · ba9b0ed – Doku ergänzt
Dokumentation ergänzt.

---

<a id="commit-25"></a>
### 25 · 31bb282 – feat: add state_class to sensor templates
state_class zu Sensor-Templates hinzugefügt für verbesserte Datenbehandlung.

---

<a id="commit-26"></a>
### 26 · 208e358 – fix: update room thermostat offset range and Modbus conversion
Room thermostat offset range and Modbus conversion for signed values updated.

---

<a id="commit-27"></a>
### 27 · 08a0a8e – docs: update Modbus documentation, heating curve typos
Modbus documentation updated and minor typos in heating curve sections fixed.

---

<a id="commit-28"></a>
### 28 · eeccd12 – docs: fix link case sensitivity in installation guide for HACS
Link case sensitivity in installation guide for HACS corrected.

---

<a id="commit-29"></a>
### 29 · 3535fa8 – workflow changed
Workflow geändert.

---

<a id="commit-30"></a>
### 30 · 91d3b53 – github workflow changed to work with current Release
GitHub Workflow an aktuelles Release angepasst.

---

<a id="commit-31"></a>
### 31 · ba2f7c9 – Docu link in manifest corrected
Dokumentations-Link im Manifest korrigiert.
