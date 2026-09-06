---
title: "Warmwasser Solltemperatur Steuerung"
---

# Warmwasser Solltemperatur Steuerung

*Zuletzt geändert am 06.09.2026*

Die Lambda Heat Pumps Integration ermöglicht die Steuerung der Warmwasser-Solltemperatur über Home Assistant. Sie können die gewünschte Warmwassertemperatur direkt in Home Assistant einstellen, und die Integration schreibt diese Werte an die Lambda-Wärmepumpe.

!!! info "Seit Version 3.5: Climate-Entity statt Number-Entity"
    Die Warmwasser-Solltemperatur wird nicht mehr über eine separate Number-Entity gesteuert, sondern über die **Climate-Entity** des Boilers – dieselbe Entity, die auch die aktuelle Warmwassertemperatur anzeigt.

## Verfügbare Entität

Für jeden Kessel (Boiler) wird automatisch eine Climate-Entity erstellt:

- **Entity-ID**: `climate.*_hot_water` (für Boiler 1)
- **Bereich**: 25°C bis 65°C (Standard, in den Integrations-Optionen anpassbar)
- **Aktuelle Temperatur**: `actual_high_temperature` (oberer Fühler)
- **Zieltemperatur**: `target_high_temperature`

**Beispiel-Entity-ID:** `climate.eu08l_boil1_hot_water`

Bei mehreren Boilern erhält jeder seine eigene Climate-Entity (`hp1_hot_water`, `hp2_hot_water`, …). Der zugehörige Register-Wert bleibt zusätzlich als reiner **Sensor** (`sensor.*_boil1_target_high_temperature`) sichtbar – schreibbar ist aber nur die Climate-Entity.

## Verwendung

### Über die Home Assistant Benutzeroberfläche

1. **Öffnen Sie Home Assistant:**
   - Gehen Sie zu **Einstellungen** → **Geräte & Dienste**
   - Suchen Sie nach Ihrer Lambda-Integration
   - Klicken Sie auf die Integration

2. **Wählen Sie Ihren Kessel:**
   - Klicken Sie auf den entsprechenden Kessel (z.B. "Boil1")

3. **Climate-Entity öffnen:**
   - Öffnen Sie die Thermostat-Kachel des Boilers

4. **Temperatur anpassen:**
   - Stellen Sie die gewünschte Solltemperatur ein (zwischen 25°C und 65°C)
   - Die Änderung wird direkt an die Lambda geschrieben

### Über Automatisierungen

Sie steuern die Warmwasser-Solltemperatur über den Standard-Climate-Service `climate.set_temperature`:

```yaml
automation:
  - alias: "Warmwasser Temperatur erhöhen"
    trigger:
      - platform: time
        at: "06:00:00"
    actions:
      - action: climate.set_temperature
        target:
          entity_id: climate.eu08l_boil1_hot_water
        data:
          temperature: 55
    mode: single
```

### Über Services (Entwicklertools)

```yaml
actions:
  - action: climate.set_temperature
    target:
      entity_id: climate.eu08l_boil1_hot_water
    data:
      temperature: 50
mode: single
```

## Temperaturgrenzen

Die Integration verwendet standardmäßig folgende Grenzen:

- **Minimum**: 25°C
- **Maximum**: 65°C

Diese Grenzen können in den Integration-Optionen angepasst werden:

1. Gehen Sie zu **Einstellungen** → **Geräte & Dienste**
2. Klicken Sie auf Ihre Lambda-Integration
3. Klicken Sie auf **Konfigurieren**
4. Scrollen Sie zu **Warmwasser-Temperaturgrenzen**
5. Passen Sie die Werte an

**Hinweis**: Die Anpassung der Grenzen in den Optionen wirkt sich auf alle Kessel aus, und erst nach einem Reload der Integration (automatisch nach dem Speichern der Optionen).

## Bidirektionale Synchronisation

Die Integration synchronisiert die Warmwasser-Solltemperatur bidirektional:

- **Lesen**: Die Climate-Entity liest sowohl die aktuelle als auch die Soll-Temperatur direkt aus dem Modbus-Register
- **Schreiben**: Änderungen in Home Assistant werden direkt an die Lambda geschrieben und lösen sofort einen erneuten Poll aus
- **Automatische Aktualisierung**: Änderungen an der Lambda selbst werden beim nächsten regulären Poll (Standard alle 30 s) übernommen

## Beispiel-Szenarien

### Szenario 1: Tägliche Temperaturanpassung

Erhöhen Sie die Warmwasser-Temperatur morgens und senken Sie sie abends:

```yaml
automation:
  - alias: "Warmwasser morgens erhöhen"
    trigger:
      - platform: time
        at: "06:00:00"
    actions:
      - action: climate.set_temperature
        target:
          entity_id: climate.eu08l_boil1_hot_water
        data:
          temperature: 55
    mode: single

  - alias: "Warmwasser abends senken"
    trigger:
      - platform: time
        at: "22:00:00"
    actions:
      - action: climate.set_temperature
        target:
          entity_id: climate.eu08l_boil1_hot_water
        data:
          temperature: 45
    mode: single
```

### Szenario 2: Temperatur basierend auf Tageszeit

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
    actions:
      - choose:
          - conditions:
              - condition: time
                after: "06:00:00"
                before: "12:00:00"
            sequence:
              - action: climate.set_temperature
                target:
                  entity_id: climate.eu08l_boil1_hot_water
                data:
                  temperature: 55
          - conditions:
              - condition: time
                after: "12:00:00"
                before: "18:00:00"
            sequence:
              - action: climate.set_temperature
                target:
                  entity_id: climate.eu08l_boil1_hot_water
                data:
                  temperature: 50
          - conditions:
              - condition: time
                after: "18:00:00"
                before: "22:00:00"
            sequence:
              - action: climate.set_temperature
                target:
                  entity_id: climate.eu08l_boil1_hot_water
                data:
                  temperature: 48
          - conditions:
              - condition: time
                after: "22:00:00"
                before: "06:00:00"
            sequence:
              - action: climate.set_temperature
                target:
                  entity_id: climate.eu08l_boil1_hot_water
                data:
                  temperature: 45
    mode: single
```

## Häufige Probleme

### "Temperatur wird nicht übernommen"
- **Ursache**: Modbus-Verbindungsproblem
- **Lösung**: 
  - Überprüfen Sie die Modbus-Verbindung
  - Überprüfen Sie die Logs auf Fehlermeldungen
  - Starten Sie Home Assistant neu

### "Temperatur außerhalb des Bereichs"
- **Ursache**: Wert liegt außerhalb der erlaubten Grenzen (Standard 25°C – 65°C, siehe Integrations-Optionen)
- **Lösung**: Verwenden Sie einen Wert innerhalb der konfigurierten Grenzen

### "Temperatur ändert sich nicht"
- **Ursache**: Lambda-Wärmepumpe akzeptiert den Wert nicht
- **Lösung**: 
  - Überprüfen Sie die Lambda-Bedienoberfläche
  - Überprüfen Sie, ob die Lambda im richtigen Modus ist
  - Überprüfen Sie die Modbus-Verbindung

## Nächste Schritte

Nach der Einrichtung der Warmwasser-Solltemperatur-Steuerung können Sie:

- [Raumthermostat](raumthermometer.md) konfigurieren
- [Energie- und Wärmeverbrauchsberechnung](Energieverbrauchsberechnung.md) einrichten
- [Optionen des config_flow](optionen-config-flow.md) anpassen
