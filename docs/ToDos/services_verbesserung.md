# Service-Optimierung für Lambda Heat Pumps Integration

## Problem-Analyse

### Aktueller Zustand
- **Timer läuft immer**: Alle 30 Sekunden wird `scheduled_update_callback` ausgelöst
- **Ressourcenverschwendung**: Auch wenn beide Optionen deaktiviert sind (`room_thermostat_control=False, pv_surplus=False`), läuft der Timer weiter
- **Unnötige Logs**: Jede 30 Sekunden: `"Scheduled update callback triggered"` + `"Entry options: room_thermostat_control=False, pv_surplus=False"`

### Log-Beispiel (aktuell)
```
2025-10-24 10:38:10.551 INFO [custom_components.lambda_heat_pumps.services] Scheduled update callback triggered
2025-10-24 10:38:10.552 INFO [custom_components.lambda_heat_pumps.services] Entry 01K88E0VNBD5EDB0PCGJSAY6EM options: room_thermostat_control=False, pv_surplus=False
2025-10-24 10:38:40.550 INFO [custom_components.lambda_heat_pumps.services] Scheduled update callback triggered
2025-10-24 10:38:40.550 INFO [custom_components.lambda_heat_pumps.services] Entry 01K88E0VNBD5EDB0PCGJSAY6EM options: room_thermostat_control=False, pv_surplus=False
```

## Lösungsansatz

### 1. Service-Registrierung von Timer-Setup trennen

**Aktuell:**
```python
async def async_setup_services(hass: HomeAssistant) -> None:
    # Services registrieren
    # Timer IMMER starten
    setup_scheduled_updates()  # Läuft immer!
```

**Verbessert:**
```python
async def async_setup_services(hass: HomeAssistant) -> None:
    # Services registrieren (für manuelle Nutzung)
    hass.services.async_register(DOMAIN, "update_room_temperature", ...)
    hass.services.async_register(DOMAIN, "read_modbus_register", ...)
    hass.services.async_register(DOMAIN, "write_modbus_register", ...)
    hass.services.async_register(DOMAIN, "write_room_and_pv", ...)
    
    # Timer nur starten wenn nötig
    await async_setup_scheduler_if_needed(hass)
```

### 2. Intelligente Timer-Aktivierung

```python
def should_start_scheduler(hass: HomeAssistant) -> bool:
    """Prüfe ob mindestens eine Option aktiv ist."""
    lambda_entries = hass.data.get(DOMAIN, {})
    for entry_id, entry_data in lambda_entries.items():
        config_entry = hass.config_entries.async_get_entry(entry_id)
        if config_entry and config_entry.options:
            if (config_entry.options.get("room_thermostat_control", False) or 
                config_entry.options.get("pv_surplus", False)):
                return True
    return False

async def async_setup_scheduler_if_needed(hass: HomeAssistant) -> None:
    """Starte Timer nur wenn mindestens eine Option aktiv ist."""
    if should_start_scheduler(hass):
        await async_start_scheduler(hass)
        _LOGGER.info("Scheduler started - at least one service option is active")
    else:
        _LOGGER.info("Scheduler not started - no service options are active")
```

### 3. Dynamisches Timer-Management

```python
@callback
def config_entry_updated(event):
    """Reagiere auf Konfigurationsänderungen."""
    _LOGGER.debug("Config entry updated, re-evaluating scheduler")
    
    if should_start_scheduler(hass):
        if not is_scheduler_running():
            await async_start_scheduler(hass)
            _LOGGER.info("Scheduler started due to config change")
    else:
        if is_scheduler_running():
            await async_stop_scheduler(hass)
            _LOGGER.info("Scheduler stopped - no active service options")
```

### 4. Scheduler-Management

```python
async def async_start_scheduler(hass: HomeAssistant) -> None:
    """Starte den Service-Timer."""
    if "_lambda_scheduler_active" in hass.data:
        return  # Bereits aktiv
    
    update_interval = timedelta(seconds=DEFAULT_WRITE_INTERVAL)
    
    async def scheduled_update_callback(_):
        _LOGGER.debug("Scheduled update callback triggered")
        await async_write_room_and_pv()
    
    unsub = async_track_time_interval(
        hass,
        scheduled_update_callback,
        update_interval,
    )
    
    hass.data["_lambda_scheduler_active"] = True
    hass.data["_lambda_scheduler_unsub"] = unsub
    _LOGGER.info("Service scheduler started with %s second interval", DEFAULT_WRITE_INTERVAL)

async def async_stop_scheduler(hass: HomeAssistant) -> None:
    """Stoppe den Service-Timer."""
    if "_lambda_scheduler_unsub" in hass.data:
        unsub = hass.data["_lambda_scheduler_unsub"]
        unsub()
        del hass.data["_lambda_scheduler_unsub"]
    
    hass.data.pop("_lambda_scheduler_active", None)
    _LOGGER.info("Service scheduler stopped")

def is_scheduler_running(hass: HomeAssistant) -> bool:
    """Prüfe ob der Scheduler läuft."""
    return hass.data.get("_lambda_scheduler_active", False)
```

## Implementierungsplan

### Phase 1: Service-Registrierung trennen
1. `async_setup_services()` umstrukturieren
2. Service-Registrierung von Timer-Setup trennen
3. `should_start_scheduler()` Funktion implementieren

### Phase 2: Intelligente Timer-Aktivierung
1. `async_setup_scheduler_if_needed()` implementieren
2. Timer nur bei aktiven Optionen starten
3. Logging verbessern

### Phase 3: Dynamisches Management
1. Config-Change-Listener erweitern
2. Timer bei Option-Änderungen neu evaluieren
3. Cleanup bei Deaktivierung

### Phase 4: Testing & Optimierung
1. Tests für verschiedene Config-Szenarien
2. Performance-Messung
3. Logging-Optimierung

## Vorteile

### Ressourcenschonung
- ✅ **Kein Timer** wenn keine Services aktiv
- ✅ **Reduzierte CPU-Last** bei deaktivierten Optionen
- ✅ **Saubere Logs** ohne unnötige Messages

### Flexibilität
- ✅ **Services verfügbar** für manuelle Nutzung
- ✅ **Dynamische Aktivierung** bei Config-Änderungen
- ✅ **Intelligente Erkennung** aktiver Optionen

### Wartbarkeit
- ✅ **Klare Trennung** zwischen Services und Timer
- ✅ **Bessere Logs** für Debugging
- ✅ **Einfache Erweiterung** für neue Services

## Konfigurationsszenarien

### Szenario 1: Beide Services deaktiviert
```
room_thermostat_control: false
pv_surplus: false
→ Kein Timer, Services verfügbar für manuelle Nutzung
```

### Szenario 2: Nur Raumthermostat aktiv
```
room_thermostat_control: true
pv_surplus: false
→ Timer läuft, nur Raumthermostat wird geschrieben
```

### Szenario 3: Nur PV-Surplus aktiv
```
room_thermostat_control: false
pv_surplus: true
→ Timer läuft, nur PV-Surplus wird geschrieben
```

### Szenario 4: Beide Services aktiv
```
room_thermostat_control: true
pv_surplus: true
→ Timer läuft, beide Services werden geschrieben
```

## Migration

### Bestehende Installationen
- **Keine Breaking Changes**: Services bleiben verfügbar
- **Automatische Optimierung**: Timer startet nur bei aktiven Optionen
- **Rückwärtskompatibel**: Bestehende Configs funktionieren weiter

### Neue Installationen
- **Optimiert von Anfang an**: Keine unnötigen Timer
- **Bessere Performance**: Ressourcenschonend
- **Saubere Logs**: Weniger Spam in den Logs

## Fazit

Diese Optimierung macht die Integration **deutlich effizienter** und **ressourcenschonender**. Besonders bei Installationen ohne aktive Service-Optionen wird die Performance erheblich verbessert, da der 30-Sekunden-Timer komplett entfällt.

Die Lösung ist **rückwärtskompatibel** und **erweiterbar** für zukünftige Service-Optionen.
