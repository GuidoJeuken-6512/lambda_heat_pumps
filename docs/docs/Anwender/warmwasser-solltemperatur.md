---
title: "Warmwasser Solltemperatur Steuerung"
---

# Warmwasser Solltemperatur Steuerung

Die Lambda Heat Pumps Integration ermöglicht die Steuerung der Warmwasser-Solltemperatur über Home Assistant. Sie können die gewünschte Warmwassertemperatur direkt in Home Assistant einstellen, und die Integration schreibt diese Werte an die Lambda-Wärmepumpe.

## Verfügbare Entitäten

Für jeden Kessel (Boiler) werden automatisch folgende Entitäten erstellt:

### Number-Entity für Warmwasser-Solltemperatur

- **Entity-ID**: `number.*_boil1_target_temperature` (für Boiler 1)
- **Bereich**: 25°C bis 65°C (Lambda-Standard)
- **Schrittweite**: 0.1°C
- **Einheit**: °C
- **Beschreibung**: Solltemperatur für Warmwasser

**Beispiel-Entity-IDs:**
- `number.eu08l_boil1_target_temperature` (für Boiler 1)
- `number.eu08l_boil2_target_temperature` (für Boiler 2)

## Verwendung

### Über die Home Assistant Benutzeroberfläche

1. **Öffnen Sie Home Assistant:**
   - Gehen Sie zu **Einstellungen** → **Geräte & Dienste**
   - Suchen Sie nach Ihrer Lambda-Integration
   - Klicken Sie auf die Integration

2. **Wählen Sie Ihren Kessel:**
   - Klicken Sie auf den entsprechenden Kessel (z.B. "Boil1")

3. **Warmwasser-Solltemperatur finden:**
   - Scrollen Sie zu den Number-Entities
   - Suchen Sie nach "Target Temperature" oder "Solltemperatur"

4. **Temperatur anpassen:**
   - Klicken Sie auf die Number-Entity
   - Geben Sie die gewünschte Temperatur ein (zwischen 25°C und 65°C)
   - Klicken Sie auf **Speichern**

### Über Automatisierungen

Sie können die Warmwasser-Solltemperatur auch über Automatisierungen steuern:

```yaml
automation:
  - alias: "Warmwasser Temperatur erhöhen"
    trigger:
      - platform: time
        at: "06:00:00"
    action:
      - service: number.set_value
        target:
          entity_id: number.eu08l_boil1_target_temperature
        data:
          value: 55
```

### Über Services

Sie können die Warmwasser-Solltemperatur auch direkt über Services setzen:

```yaml
service: number.set_value
target:
  entity_id: number.eu08l_boil1_target_temperature
data:
  value: 50
```

## Temperaturgrenzen

Die Integration verwendet die Lambda-Standard-Temperaturgrenzen:

- **Minimum**: 25°C
- **Maximum**: 65°C
- **Schrittweite**: 0.1°C

Diese Grenzen können in den Integration-Optionen angepasst werden:

1. Gehen Sie zu **Einstellungen** → **Geräte & Dienste**
2. Klicken Sie auf Ihre Lambda-Integration
3. Klicken Sie auf **Konfigurieren**
4. Scrollen Sie zu **Warmwasser-Temperaturgrenzen**
5. Passen Sie die Werte an

**Hinweis**: Die Anpassung der Grenzen in den Optionen wirkt sich auf alle Kessel aus.

## Bidirektionale Synchronisation

Die Integration synchronisiert die Warmwasser-Solltemperatur bidirektional:

- **Lesen**: Die Integration liest den aktuellen Wert aus dem Modbus-Register
- **Schreiben**: Änderungen in Home Assistant werden direkt an die Lambda geschrieben
- **Automatische Aktualisierung**: Änderungen an der Lambda werden automatisch in Home Assistant übernommen

## Beispiel-Szenarien

### Szenario 1: Tägliche Temperaturanpassung

Erhöhen Sie die Warmwasser-Temperatur morgens und senken Sie sie abends:

```yaml
automation:
  - alias: "Warmwasser morgens erhöhen"
    trigger:
      - platform: time
        at: "06:00:00"
    action:
      - service: number.set_value
        target:
          entity_id: number.eu08l_boil1_target_temperature
        data:
          value: 55

  - alias: "Warmwasser abends senken"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: number.set_value
        target:
          entity_id: number.eu08l_boil1_target_temperature
        data:
          value: 45
```

### Szenario 2: Temperatur basierend auf Tageszeit

Passen Sie die Temperatur basierend auf der Tageszeit an:

```yaml
automation:
  - alias: "Warmwasser Temperatur nach Zeit"
    trigger:
      - platform: time
        at:
          - "06:00:00"
          - "12:00:00"
          - "18:00:00"
          - "22:00:00"
    action:
      - choose:
          - conditions:
              - condition: time
                after: "06:00:00"
                before: "12:00:00"
            sequence:
              - service: number.set_value
                target:
                  entity_id: number.eu08l_boil1_target_temperature
                data:
                  value: 55
          - conditions:
              - condition: time
                after: "12:00:00"
                before: "18:00:00"
            sequence:
              - service: number.set_value
                target:
                  entity_id: number.eu08l_boil1_target_temperature
                data:
                  value: 50
          - conditions:
              - condition: time
                after: "18:00:00"
                before: "22:00:00"
            sequence:
              - service: number.set_value
                target:
                  entity_id: number.eu08l_boil1_target_temperature
                data:
                  value: 48
          - conditions:
              - condition: time
                after: "22:00:00"
                before: "06:00:00"
            sequence:
              - service: number.set_value
                target:
                  entity_id: number.eu08l_boil1_target_temperature
                data:
                  value: 45
```

## Häufige Probleme

### "Temperatur wird nicht übernommen"
- **Ursache**: Modbus-Verbindungsproblem
- **Lösung**: 
  - Überprüfen Sie die Modbus-Verbindung
  - Überprüfen Sie die Logs auf Fehlermeldungen
  - Starten Sie Home Assistant neu

### "Temperatur außerhalb des Bereichs"
- **Ursache**: Wert liegt außerhalb der erlaubten Grenzen (25°C - 65°C)
- **Lösung**: Verwenden Sie einen Wert zwischen 25°C und 65°C

### "Temperatur ändert sich nicht"
- **Ursache**: Lambda-Wärmepumpe akzeptiert den Wert nicht
- **Lösung**: 
  - Überprüfen Sie die Lambda-Bedienoberfläche
  - Überprüfen Sie, ob die Lambda im richtigen Modus ist
  - Überprüfen Sie die Modbus-Verbindung

## Nächste Schritte

Nach der Einrichtung der Warmwasser-Solltemperatur-Steuerung können Sie:

- [Raumthermostat](raumthermostat.md) konfigurieren
- [Stromverbrauchsberechnung](stromverbrauchsberechnung.md) einrichten
- [Optionen des config_flow](optionen-config-flow.md) anpassen

