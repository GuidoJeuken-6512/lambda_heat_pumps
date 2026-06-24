# Analyse: Issue #85 – Climate-Entity mit falscher Domain (`sensor` statt `climate`)

Quelle: https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/85

## Bug Report (Zusammenfassung)

- **Titel:** Entity registered with wrong domain (`sensor` instead of `climate`)
- **Betroffene Entity:** `sensor.eu13l_boil1_hot_water` (erwartet: `climate.eu13l_boil1_hot_water`)
- **Umgebung:** Integration V2.4.0, HA Core 17.3, OS 2026.5.1, Lambda EU13L mit Boiler/Hot-Water-Modul
- **Reproduktion:** Integration installieren, EU13L konfigurieren, HA neu starten → Warnung erscheint zweimal pro Start im Log
- **Ankündigung im Issue:** Dieses Verhalten wird ab **HA 2027.5.0 vollständig abgelehnt** (Entity funktioniert dann nicht mehr)
- **Label:** `bug`

## Root Cause (im Code verifiziert)

`generate_sensor_names()` in [`utils.py:732-748`](../../custom_components/lambda_heat_pumps/utils.py#L732-L748) baut den `entity_id`-String **immer** mit hartkodiertem `sensor.`-Domain-Präfix, unabhängig davon, für welche Plattform er bestimmt ist:

```python
entity_id = f"sensor.{name_prefix_lc}_{device_prefix}_{sensor_id}"
```

[`climate.py:85`](../../custom_components/lambda_heat_pumps/climate.py#L85) übernimmt diesen Wert direkt:

```python
self.entity_id = names["entity_id"]
```

Betroffen ist damit jede über `LambdaClimateEntity` erzeugte Entity – aktuell `hot_water` und `heating_circuit`, perspektivisch auch jede künftige Climate-Entity (z. B. ein geplantes `cooling_circuit`), sofern sie dieselbe Routine verwendet.

## Warum die Auswirkung inkonsistent ist

Home Assistant tolerier­t aktuell (mit Deprecation-Warning), dass eine Entity mit einem explizit gesetzten `entity_id` registriert wird, dessen Domain nicht zur Plattform passt. Die **Entity Registry** merkt sich einen einmal vergebenen `(domain, unique_id)`-Eintrag dauerhaft:

- Wurde eine Entity (z. B. `heating_circuit` bei einer Bestandsinstallation) bereits früher korrekt unter `climate` registriert, bleibt sie dauerhaft `climate.xxx`, auch wenn der Code weiterhin einen `sensor.`-Präfix anfordert.
- Bei neu angelegten unique_ids (z. B. `boil1_hot_water` im gemeldeten Fall) wird der fehlerhafte `sensor.`-Präfix tatsächlich zur registrierten Domain.

Das erklärt, warum manche Climate-Entities korrekt erscheinen und andere nicht – es hängt vom Zeitpunkt/Verlauf der Erstregistrierung ab, nicht vom aktuellen Code-Zustand.

## Auswirkung bei Umsetzung eines Fixes

- Eine Domain lässt sich bei HA **nicht in-place umbenennen** – `sensor.x` → `climate.x` ist technisch eine komplett neue Entity, kein Rename.
- Die alte Entity verschwindet, eine neue mit leerer Historie entsteht. **Bestehende Recorder-Historie / Long-Term-Statistics unter der alten `sensor.xxx`-ID gehen für die neue Entity verloren** (alte Daten bleiben nur eingefroren unter der alten ID sichtbar).
- **Automatisierungen, Skripte, Dashboards und Templates**, die `sensor.eu13l_boil1_hot_water` referenzieren, brechen und müssen manuell auf `climate.eu13l_boil1_hot_water` umgestellt werden.
- Zusätzlich ändert sich die **State-Semantik**: bei `sensor` ist der State direkt die Temperatur, bei `climate` ist der State der HVAC-Mode (z. B. `heat`/`off`), die Temperatur wandert in die Attribute `current_temperature`/`temperature`. Reine ID-Umbenennung in Automationen reicht daher nicht – betroffene State-Trigger müssen umgebaut werden.
- Ein saurberer Fix erfordert eine echte Migration (alten Entity-Registry-Eintrag entfernen, Nutzer informieren), nicht nur eine Code-Korrektur.

## Auswirkung bei Nicht-Umsetzung

- Bis HA 2027.5.0: keine Funktionseinbußen, nur wiederkehrende Log-Warnungen beim Start (zweimal pro Start, wie im Issue beschrieben).
- Ab HA 2027.5.0: Die Entity wird laut Ankündigung vollständig abgelehnt. Das bedeutet ein **unkontrollierter Bruch beim HA-Core-Update** – alle abhängigen Automatisierungen/Dashboards fallen plötzlich aus, statt kontrolliert migriert zu werden.

## Empfehlung

Als eigenständiges Follow-up vormerken (nicht Teil aktueller Feature-Arbeit wie dem geplanten `cooling_circuit`), da:

1. Es alle bestehenden Climate-Entities betrifft, nicht nur eine.
2. Ein Fix eine eigene Migrationsstrategie braucht (Datenverlust/Automations-Breakage minimieren), die sorgfältig kommuniziert werden sollte (Release Notes, ggf. Übergangszeitraum).
3. Es zeitlich unkritisch ist (Frist erst ab HA 2027.5.0), aber rechtzeitig vor diesem Termin angegangen werden sollte.

**Nächste Schritte (falls priorisiert):**
- Entscheiden, ob `generate_sensor_names()` plattformspezifisch (`sensor.`/`climate.`/...) erweitert wird, oder ob Climate-Entities eine eigene, einfachere Namens-Routine erhalten.
- Migrationslogik schreiben, die betroffene alte `sensor.*`-Registry-Einträge für bekannte Climate-unique_ids erkennt und entfernt, bevor die neue `climate.*`-Entity angelegt wird.
- Release Notes mit klarer Anleitung für Nutzer, ihre Automatisierungen/Dashboards auf die neue Entity-ID umzustellen.
