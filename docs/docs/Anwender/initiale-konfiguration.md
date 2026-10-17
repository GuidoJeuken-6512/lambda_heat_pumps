---
title: "Initiale Konfiguration"
---

# Initiale Konfiguration

*Zuletzt geändert am 17.10.2026*

Nach der [Installation](installation.md) richten Sie die Integration in Home Assistant ein. Die Einrichtung besteht aus einem einzigen Dialog.

## Integration hinzufügen

- **Lambda wurde entdeckt:** Unter **Einstellungen** → **Geräte & Dienste** erscheint sie als **Entdeckt**. Auf **Hinzufügen** klicken; die IP-Adresse ist dann schon eingetragen.
- **Sonst:** **Einstellungen** → **Geräte & Dienste** → **Integration hinzufügen** → „Lambda Heat Pumps“ suchen und auswählen.

## Der Einrichtungsdialog „Wie ist der Regler erreichbar?“

#### Name
- Ein Name für Ihre Lambda, z. B. `EU08L`.
- Aus dem Namen werden die Gerätenamen (z. B. „EU08L - HP1“) und die Entitäts-IDs gebildet, z. B. `sensor.eu08l_hp1_flow_line_temperature`.

#### Host
- IP-Adresse oder Hostname der Lambda, z. B. `192.168.1.100`.
- Home Assistant muss diese Adresse erreichen können.

#### Port
- Der Modbus-TCP-Port, Standard `502`.

#### Modbus-Einheit
- Die Modbus-Adresse (Slave-ID) der Lambda, Standard `1`. Nur ändern, wenn Ihre Lambda anders eingestellt ist.

#### Firmware-Version
- Die Firmware Ihrer Lambda im Format `V…-3K`, z. B. `V0.0.9-3K` oder `V1.1.0-3K`. Sie steht unten in der Statuszeile der Wärmepumpen-Seite der Lambda-Bedienoberfläche. Alternativ: auf der Bedienoberfläche die Wärmepumpe anklicken → „i“-Taste links → rechts die Taste mit dem Computerchip (letzte Taste).
- **Wichtig:** Die Firmware-Version bestimmt, welche Sensoren angelegt werden und in welcher Register-Reihenfolge die Energiezähler gelesen werden. Gemeint ist **nicht** die Software-Version der Steuerung (z. B. `V1.3.10`).
- Steht Ihre Version nicht in der Liste, wählen Sie die neueste und lesen Sie [Firmware-Version ändern](firmware-wechsel.md#meine-firmware-version-steht-nicht-in-der-liste).

Nach **Absenden** prüft die Integration, ob die Lambda unter der Adresse antwortet. Erst dann wird der Eintrag angelegt.

## Was danach automatisch passiert

- **Modulerkennung:** Die Integration fragt die Lambda, welche Module vorhanden sind (Wärmepumpen, Warmwasserspeicher, Puffer, Solar, Heizkreise). Das passiert bei **jedem** Start der Integration, Sie müssen nichts einstellen.
- **Geräte und Entitäten:** Jedes Modul wird ein eigenes Gerät unter der Lambda (z. B. „EU08L - HP1“, „EU08L - HC1“) mit seinen Sensoren, Klima- und Zahlen-Entitäten.
- **Standardmäßig aktiv** sind die Gesamtzähler (z. B. `*_energy_total`, `*_cycling_total`). Tages-, Monats- und Jahreszähler sind zunächst deaktiviert und lassen sich beim Gerät unter „Entitäten“ einschalten.
- **`lambda_wp_config.yaml`:** Beim ersten Start legt die Integration diese Datei im Konfigurationsordner an, komplett auskommentiert. Sie wird nur für Offsets und externe Energiezähler gebraucht, siehe [lambda_wp_config.yaml](lambda-wp-config.md).

## Nach der Einrichtung

1. **Entitäten prüfen:** **Einstellungen** → **Geräte & Dienste** → Lambda → Geräte bzw. Entitäten.
2. **Optionen einstellen:** Beim Eintrag auf **Konfigurieren** klicken, siehe [Optionen des Config Flow](optionen-config-flow.md) (Temperaturgrenzen, Abfrageintervall, Raumthermostat, PV-Überschuss, Kühlen).
3. **Heizkurve eintragen:** Die Stützpunkte der Heizkurve sind Handwerte, siehe [Heizkurve](heizkurve.md).
4. **Energiezähler prüfen:** `hpX_compressor_power_consumption_accumulated` und `hpX_compressor_thermal_energy_output_accumulated` mit der Statistik am Display vergleichen. Stimmen sie nicht, siehe [Falsche / keine Sensorwerte](../FAQ/falsche-keine-sensorwerte.md).

## Häufige Probleme

### „Verbindung fehlgeschlagen. Prüfen Sie die Adresse und ob der Regler erreichbar ist.“
- IP-Adresse und Port prüfen.
- Ist Modbus TCP an der Lambda aktiviert?
- Erreicht Home Assistant das Netz der Lambda (VLAN, Firewall)?

### „Dieser Regler ist bereits eingerichtet.“
- Es gibt schon einen Eintrag mit derselben IP-Adresse, demselben Port und derselben Modbus-Einheit.
- Hat die Lambda nur eine neue IP-Adresse bekommen, ändern Sie den bestehenden Eintrag über **⋮ → Neu konfigurieren**, statt einen neuen anzulegen.

### Falsche oder fehlende Sensoren
- Meist ist die falsche Firmware-Version gewählt. Ändern über **⋮ → Neu konfigurieren**, siehe [Firmware-Version ändern](firmware-wechsel.md). Die Integration muss dafür nicht entfernt werden.

## Nächste Schritte

- [Optionen des Config Flow](optionen-config-flow.md)
- [Warmwasser Solltemperatur Steuerung](warmwasser-solltemperatur.md)
- [Raumthermometer](raumthermometer.md)
- [Energie- und Wärmeverbrauchsberechnung](Energieverbrauchsberechnung.md)
- [Historische Daten übernehmen](historische-daten.md) bei Wärmepumpenwechsel
