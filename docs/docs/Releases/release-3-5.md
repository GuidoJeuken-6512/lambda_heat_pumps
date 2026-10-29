---
title: "Release 3.5"
---

# Release 3.5

*Zuletzt geändert am 17.10.2026*

Version 3.5 ist eine von Grund auf neu geschriebene Fassung der Integration. Sie nutzt die überarbeitete Modbus-Anbindung von Home Assistant ([`modbus-connection`](https://github.com/home-assistant-libs/modbus-connection)) und benötigt **Home Assistant 2026.9.0 oder neuer**.

Alle Einzeländerungen stehen im [Changelog](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/blob/main/CHANGELOG.md){:target="_blank" rel="noopener noreferrer"}. Diese Seite fasst zusammen, was sich für Anwender ändert.

## Was neu ist

- **Stabilere Modbus-Kommunikation:** Lese- und Schreibzugriffe werden sauber nacheinander abgewickelt; eine unterbrochene Verbindung baut sich bei der nächsten Abfrage von selbst wieder auf.
- **Mehrere Wärmepumpen:** Jedes Modul wird eindeutig über seine Nummer angesprochen. Die Fehler, bei denen Sensoren einer zweiten Wärmepumpe falsch zugeordnet wurden, können so nicht mehr auftreten.
- **Automatische Erkennung** der Lambda im Netzwerk (Home Assistant schlägt sie unter „Entdeckt“ vor).
- **Register-Reihenfolge der Energiezähler** folgt automatisch der eingestellten Firmware und ist als Option einstellbar, nicht mehr in der YAML-Datei.
- **Firmware-Version** wird über **⋮ → Neu konfigurieren** geändert, siehe [Firmware-Version ändern](../Anwender/firmware-wechsel.md). Firmware V1.0.4-3K ist auswählbar.
- **Diagnose-Download** mit den Rohwerten aller Register.
- **Zählerstände** überstehen Neustarts und Updates über die Bordmittel von Home Assistant; die frühere Datei `cycle_energy_persist.json` gibt es nicht mehr.

## Was sich gegenüber 2.x ändert

| Bisher (2.x) | Ab 3.5 |
|---|---|
| Firmware in den Optionen („Konfigurieren“) | Firmware über **⋮ → Neu konfigurieren** |
| `lambda_wp_config.yaml`: `disabled_registers`, `sensors_names_override` | Entität in Home Assistant deaktivieren bzw. umbenennen |
| `lambda_wp_config.yaml`: `modbus: int32_register_order` | Option „32-Bit-Registerreihenfolge“; ohne Eintrag gilt die Firmware |
| Warmwasser-Solltemperatur als Zahl-Entität | Klima-Entität **Warmwasser** (`climate.<name>_boil1_hot_water`) |
| Attribut `register` an jedem Sensor | entfallen, siehe [Attribute](../Anwender/attribute-sensoren-de.md) |
| Volumenströme in `l/h` / `l/min`, Statistik als Summe | `L/h` / `L/min`, Statistik als Messwert |
| `hcX_flow_line_temperature_setpoint` bei jeder Firmware | ab V0.0.5-3K ersetzt durch `hcX_target_temp_flow_line` |
| – | Bei Neuinstallationen sind nur die Gesamtzähler aktiv; Tages-, Monats- und Jahreszähler lassen sich beim Gerät einschalten |

Was in `lambda_wp_config.yaml` bleibt: Offsets und externe Energiezähler, siehe [lambda_wp_config.yaml](../Anwender/lambda-wp-config.md).

## Update von 2.x

1. **Backup** von Home Assistant erstellen.
2. Integration in HACS aktualisieren und Home Assistant neu starten. Der bestehende Eintrag wird automatisch übernommen; Entitäts-IDs und Verlauf bleiben erhalten.
3. **Firmware-Version prüfen** und bei Bedarf über **⋮ → Neu konfigurieren** korrigieren, siehe [Firmware-Version ändern](../Anwender/firmware-wechsel.md).
4. **Energiezähler prüfen:** `hpX_compressor_power_consumption_accumulated` und `hpX_compressor_thermal_energy_output_accumulated` mit dem Display der Lambda vergleichen. Bei unsinnigen Werten siehe [Falsche / keine Sensorwerte](../FAQ/falsche-keine-sensorwerte.md).
5. **Reparaturen** unter **Einstellungen** → **Reparaturen** abarbeiten:
    - „… hat keine Zustandsklasse mehr“ (Fehlernummern, `config_parameter_*`): ignorieren oder Statistik löschen.
    - „Die Einheit … hat sich geändert“ und „Der Mittelwert-Typ … hat sich geändert“ (Volumenströme): **„Alle alten Statistikdaten für diese Entität löschen“** wählen. Erst dann zeichnet Home Assistant für diese Sensoren wieder Langzeitstatistik auf.
6. **Weggefallene Entitäten** („nicht mehr bereitgestellt“) löschen oder ihre ID auf den Nachfolger übertragen, siehe [Entitäten löschen](../Anwender/entitaeten_loeschen.md).
7. **Klima-Entitäten mit `sensor.`-ID** (`sensor.<name>_boil1_hot_water`, `sensor.<name>_hc1_heating_circuit`) in `climate.…` umbenennen, siehe [Warmwasser](../Anwender/warmwasser-solltemperatur.md).

## Versionen 3.5.x

| Version | Wichtigste Änderung |
|---|---|
| 3.5.7 | Registerreihenfolge wurde beim Update von 2.x fest auf `high_first` gesetzt (#133); Firmware V1.0.4-3K; Zurücksetzen der Reihenfolge bei Firmwarewechsel |
| 3.5.6 | Gesamtzähler fielen beim Update von 2.x auf 0 zurück |
| 3.5.5 | Doppelte Belegung von Heizkreis-Register 7 bei Firmware ab V0.0.5-3K (#112) |
| 3.5.4 | Veraltete Home-Assistant-Funktion ersetzt (#121) |
| 3.5.3 | Schreibzugriffe schlugen fehl (falscher Modbus-Funktionscode) |
| 3.5.2 | Sonderwert 0xFFFF (−0,1 °C) wird bei Außentemperatur und Anforderungen als „unbekannt“ angezeigt; Modbus-Zugriffe sauber serialisiert |
| 3.5.0 | Neu geschriebene Integration |
