---
title: "Firmware-Version ändern"
---

# Firmware-Version ändern

*Zuletzt geändert am 17.10.2026*

Die in der Integration eingestellte Firmware-Version muss zur Firmware Ihrer Lambda passen. Sie bestimmt, welche Sensoren angelegt werden und wie die beiden 32-Bit-Energiezähler gelesen werden (Register-Reihenfolge). Diese Seite beschreibt, wann und wie Sie die Firmware-Version in Home Assistant ändern.

!!! warning "Seit Version 3.5 nur über „Neu konfigurieren“"
    Die Firmware-Version lässt sich **nicht mehr** über **Konfigurieren** (Zahnrad, Integrations-Optionen) ändern, wie es bis Version 3.4 bzw. in 2.x möglich war. Sie wird nur bei der Ersteinrichtung und über **⋮ → Neu konfigurieren** gesetzt.

## Wann muss die Firmware-Version geändert werden?

- **Die Lambda hat ein Firmware-Update erhalten**, z. B. durch den Installateur oder bei einem Service-Termin.
- **Die Steuerung wurde getauscht**, z. B. gegen die neue Steuerung mit V1.0.4-3K oder V1.1.0-3K.
- **Bei der Einrichtung wurde eine falsche Version gewählt.** Typische Anzeichen: Sensoren fehlen, die es geben müsste, oder die akkumulierten Energiezähler zeigen unsinnige Werte.
- **Nach dem Update von 2.x auf 3.5:** Die Integration übernimmt die Firmware-Version aus der alten Konfiguration. Prüfen Sie einmal, ob sie noch stimmt, besonders wenn Sie die Firmware in 2.x nachträglich geändert haben.

## Welche Firmware-Version hat meine Lambda?

Gemeint ist die Version im Format **`V…-3K`**, z. B. `V0.0.9-3K` oder `V1.1.0-3K`. Sie steht unten in der Statuszeile der Wärmepumpen-Seite der Lambda-Bedienoberfläche. Alternativ:

1. Klicken Sie auf der Lambda-Bedienoberfläche auf die Wärmepumpe.
2. Klicken Sie auf die „i“-Taste auf der linken Seite.
3. Klicken Sie auf die Taste rechts, die wie ein Computerchip aussieht (letzte Taste).

!!! info "Nicht die Software-Version der Steuerung"
    Die neue Steuerung zeigt in den Systemeinstellungen zusätzlich eine **Software-Version** wie `V1.3.10`. Diese ist **nicht** gemeint. Maßgeblich ist die `V…-3K`-Version der Wärmepumpe.

## Firmware-Version ändern

1. Öffnen Sie **Einstellungen** → **Geräte & Dienste** → **Lambda Heat Pumps**.
2. Öffnen Sie beim Eintrag Ihrer Lambda das Menü **⋮** und wählen Sie **Neu konfigurieren**.
3. Wählen Sie die neue **Firmware-Version**. Name, Host, Port und Slave-ID bleiben unverändert.
4. Klicken Sie auf **Absenden**.

Die Integration prüft die Verbindung, speichert die neue Version und lädt sich automatisch neu. Ein Neustart von Home Assistant ist nicht nötig.

## Was beim Wechsel passiert

### Sensoren

Die Integration legt nur Sensoren an, die die gewählte Firmware kennt **und** die Ihre Steuerung tatsächlich beantwortet. Nach einem Wechsel können deshalb Sensoren hinzukommen oder wegfallen.

Ein Beispiel ist der Vorlauf-Sollwert der Heizkreise:

| Firmware | Sensor |
|---|---|
| bis V0.0.4-3K | `hcX_flow_line_temperature_setpoint` (Vorlauf-Sollwert, beschreibbar) |
| ab V0.0.5-3K | `hcX_target_temp_flow_line` (Vorlauf-Sollwert, mit dem die Lambda arbeitet, nur lesbar) |

Weggefallene Sensoren bleiben in Home Assistant als „nicht mehr bereitgestellt“ stehen. Dashboards, Helfer und Automationen, die sie nutzen, funktionieren dann nicht mehr. So gehen Sie damit um:

- **Nicht mehr benötigt:** die verwaiste Entität löschen (siehe [Entitäten löschen](entitaeten_loeschen.md)).
- **Verlauf weiterführen:** zuerst die verwaiste Entität löschen, dann dem Ersatz-Sensor die alte Entitäts-ID geben (Entität öffnen → ⚙ → Entitäts-ID). Die Langzeitstatistik läuft dann unter der alten ID weiter.

Alle übrigen Sensoren behalten ihre Entitäts-ID und ihren Verlauf.

### Register-Reihenfolge der Energiezähler

Jede Firmware schreibt ihre 32-Bit-Zähler in einer festen Register-Reihenfolge. Die Integration verwendet automatisch die Reihenfolge der eingestellten Firmware:

| Firmware | Register-Reihenfolge |
|---|---|
| V0.0.3-3K bis V0.0.9-3K | `high_first` |
| V0.0.10-3K, V1.0.4-3K, V1.1.0-3K | `low_first` |

Haben Sie unter **Konfigurieren** eine eigene Register-Reihenfolge gewählt, setzt **Neu konfigurieren** diese bei einem Firmwarewechsel zurück (ab Version 3.5.7). Danach gilt die Reihenfolge der neuen Firmware. Weicht Ihre Lambda davon ab, wählen Sie die passende Reihenfolge anschließend wieder unter **Konfigurieren**. Ändern Sie unter „Neu konfigurieren“ nur Host, Port oder Slave-ID, bleibt Ihre Einstellung erhalten.

## Nach dem Wechsel prüfen

1. **Energiezähler:** Vergleichen Sie `hpX_compressor_power_consumption_accumulated` und `hpX_compressor_thermal_energy_output_accumulated` mit der Statistik am Display der Lambda. Stimmen sie nicht, siehe [Falsche / keine Sensorwerte](../FAQ/falsche-keine-sensorwerte.md).
2. **Sensoren:** Sind alle erwarteten Sensoren vorhanden? Gibt es Entitäten mit „nicht mehr bereitgestellt“?
3. **Dashboards und Automationen:** Verweisen sie auf weggefallene Sensoren?

## Meine Firmware-Version steht nicht in der Liste

Die Lambda veröffentlicht neue Firmware-Versionen nicht automatisch. Sie werden in die Integration aufgenommen, sobald sie gemeldet werden.

- Wählen Sie vorübergehend die **neueste** Version aus der Liste.
- Melden Sie Ihre Version in einem [GitHub-Issue](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues), am besten mit den Werten der beiden Energiezähler vom Display und aus Home Assistant. Daran lässt sich die Register-Reihenfolge Ihrer Firmware erkennen.

## Siehe auch

- [Anpassungen der Sensoren abhängig von der Firmware](anpassungen-sensoren-firmware.md)
- [Optionen des Config Flow](optionen-config-flow.md)
- [Falsche / keine Sensorwerte](../FAQ/falsche-keine-sensorwerte.md)
