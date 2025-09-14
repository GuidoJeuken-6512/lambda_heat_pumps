"""
Automatischer Setup für modulare Lambda Heat Pump Integration.

Dieses Modul ermöglicht automatische Erkennung und Setup aller verfügbaren
Lambda Heat Pump Module basierend auf Hardware-Scans.
"""

from __future__ import annotations
import logging
from pathlib import Path

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .modular_coordinator import LambdaModularCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_modular_integration(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> bool:
    """Setup der modularen Integration mit automatischer Hardware-Erkennung."""

    # Suche nach Hardware-Scan Dateien
    scan_file = _find_latest_scan_file()

    if scan_file:
        _LOGGER.info("Found hardware scan file: %s", scan_file)

        # Setup modular coordinator
        try:
            coordinator = LambdaModularCoordinator(hass, config_entry, scan_file)

            # Setup coordinator
            if await coordinator.async_setup():
                # Store coordinator
                if DOMAIN not in hass.data:
                    hass.data[DOMAIN] = {}
                hass.data[DOMAIN][config_entry.entry_id] = coordinator

                # Log discovered modules
                available_modules = coordinator.get_available_modules()
                system_info = coordinator.get_system_info()

                _LOGGER.info(
                    "Modular setup complete: %d modules discovered",
                    len(available_modules),
                )

                for module_name in available_modules:
                    _LOGGER.info("✅ Module '%s' available", module_name)

                # Log undocumented features
                if coordinator.has_undocumented_features():
                    undoc_count = len(coordinator.get_undocumented_registers())
                    _LOGGER.info(
                        "🆕 Found %d undocumented register features", undoc_count
                    )

                return True
            else:
                _LOGGER.error("Failed to setup modular coordinator")
                return False

        except Exception as e:
            _LOGGER.exception("Error setting up modular integration: %s", e)
            return False
    else:
        _LOGGER.warning(
            "No hardware scan file found, falling back to standard integration"
        )
        return False


def _find_latest_scan_file() -> str | None:
    """Finde die neueste Hardware-Scan Datei."""

    # Suche im Integration-Verzeichnis
    integration_path = Path(__file__).parent
    scan_files = list(integration_path.glob("lambda_comprehensive_scan_*.json"))

    if scan_files:
        # Sortiere nach Änderungsdatum und nimm die neueste
        latest_file = max(scan_files, key=lambda f: f.stat().st_mtime)
        return str(latest_file)

    return None


async def async_unload_modular_integration(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> bool:
    """Unload der modularen Integration."""

    if DOMAIN in hass.data and config_entry.entry_id in hass.data[DOMAIN]:
        coordinator = hass.data[DOMAIN][config_entry.entry_id]

        if isinstance(coordinator, LambdaModularCoordinator):
            await coordinator.async_shutdown()

        del hass.data[DOMAIN][config_entry.entry_id]

        if not hass.data[DOMAIN]:
            del hass.data[DOMAIN]

    return True


def get_modular_coordinator(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> LambdaModularCoordinator | None:
    """Hole den modularen Coordinator für einen Config Entry."""

    if DOMAIN in hass.data and config_entry.entry_id in hass.data[DOMAIN]:
        coordinator = hass.data[DOMAIN][config_entry.entry_id]
        if isinstance(coordinator, LambdaModularCoordinator):
            return coordinator

    return None


async def async_setup_module_entities(
    hass: HomeAssistant, config_entry: ConfigEntry, platform: str
) -> list:
    """Setup Entitäten für alle verfügbaren Module."""

    coordinator = get_modular_coordinator(hass, config_entry)
    if not coordinator:
        return []

    entities = []
    available_modules = coordinator.get_available_modules()

    _LOGGER.info(
        "Setting up %s entities for %d modules", platform, len(available_modules)
    )

    for module_name in available_modules:
        module_configs = coordinator.get_module_sensor_configs(module_name)

        for config in module_configs:
            if platform == "sensor":
                entities.append(_create_sensor_entity(coordinator, config))
            elif platform == "climate":
                # Climate entities nur für bestimmte Module
                if module_name in ["heating_circuit", "boiler"]:
                    entities.append(_create_climate_entity(coordinator, config))

    _LOGGER.info("Created %d %s entities", len(entities), platform)
    return entities


def _create_sensor_entity(coordinator: LambdaModularCoordinator, config: dict):
    """Erstelle eine Sensor-Entität basierend auf der Konfiguration."""
    # Import hier um zirkuläre Importe zu vermeiden
    from .sensor import LambdaModularSensor

    return LambdaModularSensor(coordinator, config)


def _create_climate_entity(coordinator: LambdaModularCoordinator, config: dict):
    """Erstelle eine Climate-Entität basierend auf der Konfiguration."""
    # Import hier um zirkuläre Importe zu vermeiden
    from .climate import LambdaModularClimate

    return LambdaModularClimate(coordinator, config)


async def async_generate_system_report(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> dict:
    """Generiere einen umfassenden System-Bericht."""

    coordinator = get_modular_coordinator(hass, config_entry)
    if not coordinator:
        return {"error": "Modular coordinator not found"}

    system_info = coordinator.get_system_info()

    # Erweitere mit detaillierten Informationen
    report = {
        "lambda_system_overview": system_info["system_overview"],
        "available_modules": system_info["available_modules"],
        "active_registers": system_info["active_registers"],
        "connection_status": system_info["connection_status"],
        "last_update": system_info["last_update"],
        "undocumented_features": coordinator.has_undocumented_features(),
        "undocumented_registers": len(coordinator.get_undocumented_registers()),
        "module_details": {},
    }

    # Details für jedes Modul
    for module_name in coordinator.get_available_modules():
        module_data = coordinator.get_module_data(module_name)
        sensor_configs = coordinator.get_module_sensor_configs(module_name)

        report["module_details"][module_name] = {
            "register_count": len(module_data),
            "sensor_count": len(sensor_configs),
            "last_values": {
                addr: data.get("value") for addr, data in module_data.items()
            },
        }

    return report
