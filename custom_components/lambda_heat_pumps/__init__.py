"""The Lambda Heat Pumps integration."""

from __future__ import annotations
from datetime import timedelta

import logging
import asyncio

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv


from .const import (
    DOMAIN,
    DEBUG_PREFIX,
)

from .coordinator import LambdaDataUpdateCoordinator
from .services import async_setup_services, async_unload_services, setup_scheduled_timer
from .utils import generate_base_addresses, ensure_lambda_config
from .automations import setup_cycling_automations, cleanup_cycling_automations
# from .migration import async_migrate_entry as migrate_entry

from .module_auto_detect import auto_detect_modules, update_entry_with_detected_modules

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=30)
VERSION = "1.2.0"  # Updated version for cycling sensors feature

# Diese Konstante teilt Home Assistant mit, dass die Integration
# Übersetzungen hat
TRANSLATION_SOURCES = {DOMAIN: "translations"}

# Lock für das Reloading
_reload_lock = asyncio.Lock()

PLATFORMS = [
    Platform.SENSOR,
    Platform.CLIMATE,
]

# Config schema - only config entries are supported
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


def setup_debug_logging(hass: HomeAssistant, config: ConfigType) -> None:
    """Set up debug logging for the integration."""
    if config.get("debug", False):
        logging.getLogger(DEBUG_PREFIX).setLevel(logging.DEBUG)
        _LOGGER.info("Debug logging enabled for %s", DEBUG_PREFIX)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Lambda integration."""
    setup_debug_logging(hass, config)
    return True


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate config entry to new version using structured migration system."""
    _LOGGER.info(
        "Starting structured migration for config entry %s (version %s)",
        config_entry.entry_id, config_entry.version
    )
    
    try:
        # Import der neuen Migration
        from .migration import perform_structured_migration
        
        # Führe strukturierte Migration durch
        migration_success = await perform_structured_migration(hass, config_entry)
        
        if migration_success:
            _LOGGER.info(
                "Structured migration completed successfully for config entry %s",
                config_entry.entry_id
            )
        else:
            _LOGGER.error(
                "Structured migration failed for config entry %s", 
                config_entry.entry_id
            )
        
        return migration_success
        
    except Exception as e:
        _LOGGER.error(
            "Error during structured migration for config entry %s: %s",
            config_entry.entry_id, e
        )
        return False


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Lambda Heat Pumps from a config entry."""
    # Check if already set up
    if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        _LOGGER.debug("Entry %s already loaded, skipping setup", entry.entry_id)
        return True

    _LOGGER.debug("Setting up Lambda integration with config: %s", entry.data)

    # Ensure lambda_wp_config.yaml exists (create from template if missing)
    await ensure_lambda_config(hass)

    # --- Intelligente Auto-Detection ---
    # Erstelle einen Coordinator für beide Zwecke (Auto-Detection + Produktivbetrieb)
    coordinator = LambdaDataUpdateCoordinator(hass, entry)
    await coordinator.async_init()
    
    # Prüfe ob Module Counts bereits vorhanden sind (bestehendes Setup)
    has_module_counts = (
        "num_hps" in entry.data and 
        "num_hc" in entry.data
    )
    
    if has_module_counts:
        # Bestehende Config: Auto-Detection im Hintergrund (non-blocking)
        _LOGGER.info("Using existing module counts, starting background auto-detection")
        
        async def background_auto_detect():
            try:
                _LOGGER.debug("Background auto-detection started")
                detected = await auto_detect_modules(coordinator.client, coordinator.slave_id)
                updated = await update_entry_with_detected_modules(hass, entry, detected)
                if updated:
                    _LOGGER.info("Background auto-detection updated module counts: %s", detected)
                else:
                    _LOGGER.debug("Background auto-detection: no module count changes needed")
            except Exception as ex:
                _LOGGER.debug("Background auto-detection failed: %s", ex)
        
        # Starte Auto-Detection im Hintergrund (non-blocking)
        hass.async_create_task(background_auto_detect())
        _LOGGER.info("Started background auto-detection (non-blocking)")
        
        # Verwende vorhandene Module Counts
        num_hps = entry.data.get("num_hps", 1)
        num_boil = entry.data.get("num_boil", 1)
        num_buff = entry.data.get("num_buff", 0)
        num_sol = entry.data.get("num_sol", 0)
        num_hc = entry.data.get("num_hc", 1)
    else:
        # Ersteinrichtung: Auto-Detection synchron (blockierend)
        _LOGGER.info("First-time setup, running auto-detection synchronously")
        detected_counts = None
        for attempt in range(2):  # Reduziert von 3 auf 2 Versuche
            try:
                detected_counts = await auto_detect_modules(coordinator.client, coordinator.slave_id)
                updated = await update_entry_with_detected_modules(hass, entry, detected_counts)
                if updated:
                    _LOGGER.info("Auto-detection updated module counts: %s", detected_counts)
                break
            except Exception as ex:
                _LOGGER.warning(
                    "[Auto-detect attempt %d/2] Module auto-detection failed: %s",
                    attempt + 1,
                    ex,
                )
                if attempt < 1:  # Nur einmal retry
                    await asyncio.sleep(0.5)  # Reduziert von 1s auf 0.5s
        
        # Use detected counts if available, else fallback to defaults
        if detected_counts:
            num_hps = detected_counts.get("hp", 1)
            num_boil = detected_counts.get("boil", 1)
            num_buff = detected_counts.get("buff", 0)
            num_sol = detected_counts.get("sol", 0)
            num_hc = detected_counts.get("hc", 1)
        else:
            num_hps = entry.data.get("num_hps", 1)
            num_boil = entry.data.get("num_boil", 1)
            num_buff = entry.data.get("num_buff", 0)
            num_sol = entry.data.get("num_sol", 0)
            num_hc = entry.data.get("num_hc", 1)

    _LOGGER.debug(
        "Device counts - HPs: %d, Boilers: %d, Buffers: %d, Solar: %d, HCs: %d",
        num_hps,
        num_boil,
        num_buff,
        num_sol,
        num_hc,
    )

    _LOGGER.debug(
        "Generated base addresses - HP: %s, Boil: %s, Buff: %s, Sol: %s, HC: %s",
        generate_base_addresses("hp", num_hps),
        generate_base_addresses("boil", num_boil),
        generate_base_addresses("buff", num_buff),
        generate_base_addresses("sol", num_sol),
        generate_base_addresses("hc", num_hc),
    )
    # Coordinator ist bereits erstellt und initialisiert - verwende den bestehenden
    try:
        
        # ⭐ KORRIGIERT: Endianness-Konfiguration VOR dem ersten async_refresh()
        from .modbus_utils import get_int32_byte_order
        try:
            coordinator._int32_byte_order = await get_int32_byte_order(hass)
            _LOGGER.info("Int32 Byte-Order konfiguriert: %s", coordinator._int32_byte_order)
        except Exception as e:
            _LOGGER.warning("Fehler bei Byte-Order-Bestimmung: %s", e)
            coordinator._int32_byte_order = "big"  # Fallback auf Standard
        
        # Warte auf die erste Datenabfrage mit optimierter Retry-Logik
        max_retries = 2  # Reduziert von 3 auf 2
        for attempt in range(max_retries):
            try:
                await coordinator.async_refresh()
                if coordinator.data:
                    break
                else:
                    _LOGGER.warning(
                        "Attempt %d/%d: No data received from Lambda device",
                        attempt + 1,
                        max_retries,
                    )
                    if attempt < max_retries - 1:
                        await asyncio.sleep(0.3)  # Reduziert von 1s auf 0.3s
            except Exception as ex:
                _LOGGER.warning(
                    "Attempt %d/%d: Error refreshing coordinator: %s",
                    attempt + 1,
                    max_retries,
                    ex,
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.3)  # Reduziert von 1s auf 0.3s

        if not coordinator.data:
            _LOGGER.error(
                "Failed to fetch initial data from Lambda device after %d attempts",
                max_retries,
            )
            return False

        # Store coordinator in hass.data (always overwrite to ensure fresh coordinator)
        if DOMAIN not in hass.data:
            hass.data[DOMAIN] = {}
        hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

        # Set up platforms with error handling
        try:
            await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        except Exception as platform_ex:
            _LOGGER.error("Error setting up platforms: %s", platform_ex, exc_info=True)
            # Clean up partially setup platforms
            try:
                await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
            except Exception as unload_ex:
                _LOGGER.error(
                    "Error cleaning up platforms: %s", unload_ex, exc_info=True
                )
            return False

        # Set up services (only once, regardless of number of entries)
        if not hass.services.has_service(DOMAIN, "read_modbus_register"):
            await async_setup_services(hass)
        else:
            # Services existieren bereits, aber Timer müssen neu gestartet werden nach Reload
            _LOGGER.info("Services already registered, restarting scheduled timer after reload")
            await setup_scheduled_timer(hass)

        # Set up cycling automations
        setup_cycling_automations(hass, entry.entry_id)

        # Add update listener
        entry.async_on_unload(entry.add_update_listener(async_reload_entry))

        _LOGGER.info("Lambda Heat Pumps integration setup completed")
        return True

    except Exception as ex:
        _LOGGER.error("Failed to setup Lambda integration: %s", ex, exc_info=True)

        # Clean up any partial setup
        try:
            if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
                if "coordinator" in hass.data[DOMAIN][entry.entry_id]:
                    await hass.data[DOMAIN][entry.entry_id][
                        "coordinator"
                    ].async_shutdown()
                hass.data[DOMAIN].pop(entry.entry_id, None)
        except Exception as cleanup_ex:
            _LOGGER.error(
                "Error during cleanup after failed setup: %s", cleanup_ex, exc_info=True
            )

        return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Lambda integration for entry: %s", entry.entry_id)

    unload_ok = True

    try:
        # Clean up cycling automations first
        cleanup_cycling_automations(hass, entry.entry_id)

        # Try to unload platforms - handle gracefully if they weren't loaded
        try:
            platforms_unloaded = await hass.config_entries.async_unload_platforms(
                entry, PLATFORMS
            )
            if not platforms_unloaded:
                _LOGGER.warning("Some platforms failed to unload")
                unload_ok = False
        except ValueError as ve:
            if "Config entry was never loaded" in str(ve):
                _LOGGER.debug("Platforms were not loaded, skipping unload")
                platforms_unloaded = True
            else:
                _LOGGER.warning("Error unloading platforms: %s", ve)
                unload_ok = False
                platforms_unloaded = False
        except Exception:
            _LOGGER.exception("Error unloading platforms")
            unload_ok = False
            platforms_unloaded = False

        # Remove coordinator
        if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
            try:
                coordinator_data = hass.data[DOMAIN][entry.entry_id]
                if "coordinator" in coordinator_data:
                    coordinator = coordinator_data["coordinator"]
                    await coordinator.async_shutdown()
            except Exception:
                _LOGGER.exception("Error during coordinator shutdown")
                unload_ok = False
            finally:
                hass.data[DOMAIN].pop(entry.entry_id, None)

        # If this was the last entry, unload services
        if DOMAIN in hass.data and not hass.data[DOMAIN]:
            try:
                await async_unload_services(hass)
            except Exception:
                _LOGGER.exception("Error unloading services")
                unload_ok = False
            finally:
                hass.data.pop(DOMAIN, None)

        if not unload_ok:
            _LOGGER.warning("Failed to fully unload Lambda Heat Pumps integration")
        else:
            _LOGGER.info("Lambda Heat Pumps integration unloaded successfully")

        return unload_ok

    except Exception:
        _LOGGER.exception("Unexpected error during unload")
        return False


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    _LOGGER.debug("Reloading Lambda integration for entry: %s", entry.entry_id)

    async with _reload_lock:
        try:
            # First check if entry is still valid
            if entry.entry_id not in hass.config_entries.async_entry_ids():
                _LOGGER.error("Entry not found in config entries, cannot reload")
                return

            # Unload current entry
            if not await async_unload_entry(hass, entry):
                _LOGGER.error("Failed to unload entry during reload")
                # Try to continue anyway to avoid getting stuck

            # Ensure all platforms are properly unloaded
            await asyncio.sleep(1)

            # Double check entry still exists
            if entry.entry_id not in hass.config_entries.async_entry_ids():
                _LOGGER.error("Entry disappeared during reload")
                return

            # Reload entry using fresh setup
            try:
                await async_setup_entry(hass, entry)
                _LOGGER.info("Lambda Heat Pumps integration reloaded successfully")
            except Exception as setup_ex:
                _LOGGER.error(
                    "Failed to setup after reload: %s", setup_ex, exc_info=True
                )
                # Try standard reload as last resort
                try:
                    await hass.config_entries.async_reload(entry.entry_id)
                except Exception as std_reload_ex:
                    _LOGGER.error(
                        "Standard reload also failed: %s", std_reload_ex, exc_info=True
                    )
                    raise

        except Exception as ex:
            _LOGGER.error("Critical error during reload: %s", ex, exc_info=True)
            raise
