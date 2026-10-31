---
title: "Release 3.6"
---

# Release 3.6

*Zuletzt geändert am 31.10.2026*

Version 3.x ist eine von Grund auf neu geschriebene Fassung der Integration. Sie nutzt die überarbeitete Modbus-Anbindung von Home Assistant ([`modbus-connection`](https://github.com/home-assistant-libs/modbus-connection)) und benötigt **Home Assistant 2026.9.0 oder neuer**. **3.6.1 ist das erste über HACS verteilte Release nach 2.8.6.** Wer bisher 2.8.x nutzt, springt damit direkt auf den neuen Stand.

Alle Einzeländerungen stehen im [Changelog](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/blob/main/CHANGELOG.md){:target="_blank" rel="noopener noreferrer"}. Diese Seite fasst zusammen, was sich für Anwender ändert.

## Was neu ist

- **Stabilere Modbus-Kommunikation:** Lese- und Schreibzugriffe werden sauber nacheinander abgewickelt; eine unterbrochene Verbindung baut sich bei der nächsten Abfrage von selbst wieder auf.
- **Mehrere Wärmepumpen:** Jedes Modul wird eindeutig über seine Nummer angesprochen. Die Fehler, bei denen Sensoren einer zweiten Wärmepumpe falsch zugeordnet wurden, können so nicht mehr auftreten.
- **Automatische Erkennung** der Lambda im Netzwerk (Home Assistant schlägt sie unter „Entdeckt“ vor).
- **Register-Reihenfolge der Energiezähler** folgt automatisch der eingestellten Firmware und ist als Option einstellbar. Ein in `lambda_wp_config.yaml` ausdrücklich gesetzter Wert wird beim Update von 2.x einmal übernommen.
- **Falsch gelesene Energiezähler werden erkannt** (3.6.0): Passen die Zählerwerte nur zur anderen Registerreihenfolge, erscheint unter **Einstellungen** → **Reparaturen** der Hinweis **„32-Bit-Registerreihenfolge prüfen“** mit der richtigen Einstellung. Bis dahin wird keine Energie aus diesen Zählern gebucht, die Langzeitstatistik bleibt sauber.
- **Firmware-Version** wird über **⋮ → Neu konfigurieren** geändert, siehe [Firmware-Version ändern](../Anwender/firmware-wechsel.md). Für die neue Steuerung sind V1.0.2-3K, V1.0.4-3K, V1.0.7-3K und V1.0.8-3K auswählbar.
- **Perioden-Sensoren mit einem Schalter** (3.6.1): Unter **Konfigurieren** → **Perioden-Energiesensoren aktivieren** lassen sich alle stündlichen bis jährlichen Zähler und die Gestern-Werte auf einmal ein- und ausschalten, z. B. für das [Lambda Energy Dashboard](../Vorlagen/Lambda_energy_dashboard.md).
- **PV-Überschuss:** Liefert der gewählte Sensor keinen Zahlenwert, sendet die Integration 0 W. Der E-Manager meldet dann keinen Fehler 6 mehr, siehe [PV Überschuss Steuerung](../Anwender/pv_ueberschuss_steuerung.md).
- **Diagnose-Download** mit den Rohwerten aller Register.
- **Zählerstände** überstehen Neustarts und Updates über die Bordmittel von Home Assistant; die frühere Datei `cycle_energy_persist.json` gibt es nicht mehr.

## Was sich gegenüber 2.x ändert

| Bisher (2.x) | Ab 3.x |
|---|---|
| Firmware in den Optionen („Konfigurieren“) | Firmware über **⋮ → Neu konfigurieren** |
| `lambda_wp_config.yaml`: `disabled_registers`, `sensors_names_override` | Entität in Home Assistant deaktivieren bzw. umbenennen |
| `lambda_wp_config.yaml`: `modbus: int32_register_order` | Option „32-Bit-Registerreihenfolge“; ohne Eintrag gilt die Firmware |
| Warmwasser-Solltemperatur als Zahl-Entität | Klima-Entität **Warmwasser** (`climate.<name>_boil1_hot_water`) |
| Attribut `register` an jedem Sensor | entfallen, siehe [Attribute](../Anwender/attribute-sensoren-de.md) |
| Volumenströme in `l/h` / `l/min`, Statistik als Summe | `L/h` / `L/min`, Statistik als Messwert |
| `hcX_flow_line_temperature_setpoint` bei jeder Firmware | ab V0.0.5-3K ersetzt durch `hcX_target_temp_flow_line` |
| Sensoren auf den Registern 1024–1033 und 1051–1060 (Heißgas, Sauggas, Expansionsventil, Leistungsgrenzen, Konfigurationsparameter …) | auf der neuen Steuerung (V1.0.x) nicht mehr angelegt, weil sie dort keine Werte liefern; V1.1.0-3K behält sie |
| Unsinnige Werte wie −32768 W oder 32768 | „unbekannt“ |
| – | Bei Neuinstallationen sind nur die Gesamtzähler aktiv; die Perioden-Zähler schaltet der Schalter **Perioden-Energiesensoren aktivieren** unter **Konfigurieren** ein |
| – | Bei Neuinstallationen sind Anforderungsregister (z. B. Puffer 3005–3009), die nur bei einer aktiven Anforderung einen Wert haben, standardmäßig deaktiviert |

Was in `lambda_wp_config.yaml` bleibt: Offsets und externe Energiezähler, siehe [lambda_wp_config.yaml](../Anwender/lambda-wp-config.md).

## Update von 2.x

!!! warning "Kein einfacher Rückweg"
    Nach dem Update lässt sich nicht einfach auf 2.8.x zurückgehen: Home Assistant lehnt den umgestellten Eintrag mit einer älteren Version ab. Rückweg ist entweder das Backup oder: Lambda-Integration löschen, in HACS 2.8.6 installieren und die Integration neu einrichten.

1. **Backup** von Home Assistant erstellen und prüfen, dass **Home Assistant 2026.9.0 oder neuer** läuft.
2. Integration in HACS aktualisieren und Home Assistant neu starten. Der bestehende Eintrag wird automatisch übernommen; Entitäts-IDs, Verlauf und Zählerstände bleiben erhalten.
3. **Firmware-Version prüfen** und bei Bedarf über **⋮ → Neu konfigurieren** korrigieren, siehe [Firmware-Version ändern](../Anwender/firmware-wechsel.md).
4. **Energiezähler prüfen:** `hpX_compressor_power_consumption_accumulated` und `hpX_compressor_thermal_energy_output_accumulated` mit dem Display der Lambda vergleichen. Erscheint die Reparatur **„32-Bit-Registerreihenfolge prüfen“**, die dort genannte Reihenfolge unter **Konfigurieren** einstellen. Weitere Hilfe und die Bereinigung falscher Statistik: [Falsche / keine Sensorwerte](../FAQ/falsche-keine-sensorwerte.md).
5. **Reparaturen** unter **Einstellungen** → **Reparaturen** abarbeiten:
    - „… hat keine Zustandsklasse mehr“ (Fehlernummern, `config_parameter_*`): ignorieren oder Statistik löschen.
    - „Die Einheit … hat sich geändert“ und „Der Mittelwert-Typ … hat sich geändert“ (Volumenströme): **„Alle alten Statistikdaten für diese Entität löschen“** wählen. Erst dann zeichnet Home Assistant für diese Sensoren wieder Langzeitstatistik auf.
6. **Weggefallene Entitäten** („nicht mehr bereitgestellt“) löschen oder ihre ID auf den Nachfolger übertragen, siehe [Entitäten löschen](../Anwender/entitaeten_loeschen.md). Dashboards und Automationen, die `hcX_flow_line_temperature_setpoint` nutzen, auf `hcX_target_temp_flow_line` umstellen.
7. **`lambda_wp_config.yaml` und eigene Warmwasser-Automationen** einmal gegenprüfen.

## Versionen 3.x

| Version | Wichtigste Änderung |
|---|---|
| 3.6.1 | Schalter „Perioden-Energiesensoren aktivieren“ unter **Konfigurieren**, wirkt auch auf bestehende Installationen |
| 3.6.0 | Falsch gelesene Energiezähler werden erkannt (Reparatur „32-Bit-Registerreihenfolge prüfen“, #104); Firmware V1.0.2/V1.0.7/V1.0.8-3K; keine Sensoren ohne Werte mehr auf V1.0.x; −32768 als „unbekannt“ (#91); PV-Überschuss 0 W bei ausgefallener Quelle (#120); zweiter Versuch bei der Modulerkennung (#101); beim Update von 2.x wird eine später geänderte Firmware übernommen (#82) |
| 3.5.7 | Registerreihenfolge wurde beim Update von 2.x fest auf `high_first` gesetzt (#133); Firmware V1.0.4-3K; Zurücksetzen der Reihenfolge bei Firmwarewechsel |
| 3.5.6 | Gesamtzähler fielen beim Update von 2.x auf 0 zurück |
| 3.5.5 | Doppelte Belegung von Heizkreis-Register 7 bei Firmware ab V0.0.5-3K (#112) |
| 3.5.4 | Veraltete Home-Assistant-Funktion ersetzt (#121) |
| 3.5.3 | Schreibzugriffe schlugen fehl (falscher Modbus-Funktionscode) |
| 3.5.2 | Sonderwert 0xFFFF (−0,1 °C) wird bei Außentemperatur und Anforderungen als „unbekannt“ angezeigt; Modbus-Zugriffe sauber serialisiert |
| 3.5.0 | Neu geschriebene Integration |
