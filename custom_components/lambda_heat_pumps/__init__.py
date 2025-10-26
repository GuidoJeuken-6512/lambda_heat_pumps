"""The Lambda Heat Pumps integration."""

from __future__ import annotations
from datetime import timedelta

import logging
import asyncio
import os

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
from .services import async_setup_services, async_unload_services
from .utils import generate_base_addresses, ensure_lambda_config
from .automations import setup_cycling_automations, cleanup_cycling_automations
from .migration import async_migrate_entry

from .module_auto_detect import auto_detect_modules, update_entry_with_detected_modules
from .const import AUTO_DETECT_RETRIES, AUTO_DETECT_RETRY_DELAY
from .modbus_utils import wait_for_stable_connection

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=30)
VERSION = "1.4.2"  # Updated version for service optimization and test fixes



# Diese Konstante teilt Home Assistant mit, dass die Integration
# Übersetzungen hat
TRANSLATION_SOURCES = {DOMAIN: "translations"}

# Lock für das Reloading - verhindert mehrere gleichzeitige Reloads
_reload_lock = asyncio.Lock()
_reload_in_progress = False

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
    _LOGGER.info("Setting up Lambda Heat Pumps integration")

    # Set up debug logging if configured
    setup_debug_logging(hass, config)

    # Initialize domain data structure
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Reload config entry."""
    global _reload_in_progress
    
    # Prüfe ob bereits ein Reload läuft
    if _reload_in_progress:
        _LOGGER.warning("🔄 RELOAD: Another reload is already in progress, skipping this reload request")
        return True  # Return True da der andere Reload das übernimmt
    
    _LOGGER.info("🔄 RELOAD: Starting reload for entry: %s", entry.entry_id)

    async with _reload_lock:
        if _reload_in_progress:
            _LOGGER.warning("🔄 RELOAD: Reload already in progress, skipping")
            return True
            
        _reload_in_progress = True
        _LOGGER.info("🔄 RELOAD: Reload lock acquired, proceeding with reload")
        
        try:
            # Unload the current entry
            _LOGGER.info("🔄 RELOAD: Unloading current entry...")
            unload_ok = await async_unload_entry(hass, entry)
            if not unload_ok:
                _LOGGER.error("❌ RELOAD: Failed to unload entry during reload")
                return False

            # Set up the entry again
            _LOGGER.info("🔄 RELOAD: Setting up entry again...")
            setup_ok = await async_setup_entry(hass, entry)
            if not setup_ok:
                _LOGGER.error("❌ RELOAD: Failed to setup entry during reload")
                return False

            _LOGGER.info("✅ RELOAD: Successfully reloaded Lambda Heat Pumps integration")
            return True

        except Exception as ex:
            _LOGGER.error("❌ RELOAD: Error during reload: %s", ex, exc_info=True)
            return False
        finally:
            _reload_in_progress = False
            _LOGGER.info("🔄 RELOAD: Reload lock released")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Lambda Heat Pumps from a config entry."""
    _LOGGER.info("🔧 SETUP: Setting up Lambda Heat Pumps integration for entry: %s", entry.entry_id)

    # Check if entry is already loaded
    if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        _LOGGER.warning("🔧 SETUP: Entry %s already loaded, skipping setup", entry.entry_id)
        return True

    _LOGGER.debug("Setting up Lambda integration with config: %s", entry.data)

    # Ensure lambda_wp_config.yaml exists (create from template if missing)
    await ensure_lambda_config(hass)

    # --- Intelligente Auto-Detection mit Performance-Optimierungen ---
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
        
        # 🎯 NEUE LOGIK: Unterscheidung zwischen erstem Start und Reload
        is_reload = hass.data.get(DOMAIN, {}).get(entry.entry_id) is not None
        
        async def background_auto_detect():
            try:
                _LOGGER.info("🔍 AUTO-DETECT: Background auto-detection started (coordinator_id=%s)", id(coordinator))
                
                if is_reload:
                    # 🎯 RELOAD: 38 Sekunden Verzögerung für stabile Verbindung
                    _LOGGER.info("⏳ AUTO-DETECT: Reload detected - waiting 38 seconds for coordinator to complete initial read cycles...")
                    await asyncio.sleep(38)  # 38 Sekunden warten
                    _LOGGER.info("✅ AUTO-DETECT: 38 seconds elapsed, starting auto-detection...")
                else:
                    # 🎯 ERSTER START: Sofort starten (Config Flow)
                    _LOGGER.info("✅ AUTO-DETECT: First startup detected - starting auto-detection immediately...")
                
                # Zusätzlich: Warte auf stabile Verbindung vor Auto-Detection
                _LOGGER.info("🔍 AUTO-DETECT: Waiting for stable connection before starting...")
                await wait_for_stable_connection(coordinator)
                _LOGGER.info("✅ AUTO-DETECT: Connection stable, starting module detection...")
                
                detected = await auto_detect_modules(coordinator.client, coordinator.slave_id)
                updated = await update_entry_with_detected_modules(hass, entry, detected)
                if updated:
                    _LOGGER.info("🔍 AUTO-DETECT: Background auto-detection updated module counts: %s (coordinator_id=%s)", detected, id(coordinator))
                else:
                    _LOGGER.info("🔍 AUTO-DETECT: Background auto-detection: no module count changes needed (coordinator_id=%s)", id(coordinator))
            except Exception as ex:
                _LOGGER.info("❌ AUTO-DETECT: Background auto-detection failed: %s (coordinator_id=%s)", ex, id(coordinator))
        
        # Starte Auto-Detection im Hintergrund (non-blocking)
        hass.async_create_task(background_auto_detect())
        _LOGGER.info("🔍 AUTO-DETECT: Started background auto-detection (non-blocking) (coordinator_id=%s)", id(coordinator))
        
        # Verwende vorhandene Module Counts
        num_hps = entry.data.get("num_hps", 1)
        num_boil = entry.data.get("num_boil", 1)
        num_buff = entry.data.get("num_buff", 0)
        num_sol = entry.data.get("num_sol", 0)
        num_hc = entry.data.get("num_hc", 1)
    else:
        # Neue Config: Auto-Detection mit Retry (blocking für Setup)
        _LOGGER.info("🔍 AUTO-DETECT: New configuration detected, performing auto-detection (coordinator_id=%s)", id(coordinator))
        detected_counts = None
        for attempt in range(AUTO_DETECT_RETRIES):
            try:
                _LOGGER.info("🔍 AUTO-DETECT: Attempt %d/%d (coordinator_id=%s)", attempt + 1, AUTO_DETECT_RETRIES, id(coordinator))
                if await coordinator.client.connect():
                    _LOGGER.info("🔍 AUTO-DETECT: Connected, starting module detection (coordinator_id=%s)", id(coordinator))
                    detected_counts = await auto_detect_modules(coordinator.client, coordinator.slave_id)
                    updated = await update_entry_with_detected_modules(hass, entry, detected_counts)
                    if updated:
                        _LOGGER.info("🔍 AUTO-DETECT: Config entry updated with detected module counts: %s (coordinator_id=%s)", detected_counts, id(coordinator))
                    else:
                        _LOGGER.info("🔍 AUTO-DETECT: No module count changes needed (coordinator_id=%s)", id(coordinator))
                    break
                else:
                    _LOGGER.info(
                        "❌ AUTO-DETECT: Could not connect to Modbus device for auto-detection (attempt %d/%d) (coordinator_id=%s)",
                        attempt + 1, AUTO_DETECT_RETRIES, id(coordinator)
                    )
            except Exception as ex:
                _LOGGER.info(
                    "❌ AUTO-DETECT: Module auto-detection failed (attempt %d/%d): %s (coordinator_id=%s)",
                    attempt + 1, AUTO_DETECT_RETRIES, ex, id(coordinator)
                )
            finally:
                if detected_counts is None and attempt < AUTO_DETECT_RETRIES - 1:
                    _LOGGER.info("🔍 AUTO-DETECT: Retrying in %d seconds (coordinator_id=%s)", AUTO_DETECT_RETRY_DELAY, id(coordinator))
                    await asyncio.sleep(AUTO_DETECT_RETRY_DELAY)
        
        # Use detected counts if available, else fallback to config
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

    # Generate base addresses for all modules
    base_addresses = {
        **generate_base_addresses("hp", num_hps),
        **generate_base_addresses("boil", num_boil),
        **generate_base_addresses("buff", num_buff),
        **generate_base_addresses("sol", num_sol),
        **generate_base_addresses("hc", num_hc),
    }

    # Coordinator ist bereits erstellt und initialisiert - verwende den bestehenden
    try:
        # ⭐ KORRIGIERT: Endianness-Konfiguration VOR dem ersten async_refresh()
        from .modbus_utils import get_int32_byte_order
        coordinator.byte_order = get_int32_byte_order(hass)

        # Setze die generierten Base Addresses
        coordinator.base_addresses = base_addresses

        # Starte den ersten Datenupdate (mit Performance-Optimierungen)
        _LOGGER.info("🔄 PRODUCTION: Starting first data update (coordinator_id=%s)", id(coordinator))
        await coordinator.async_refresh()
        _LOGGER.info("✅ PRODUCTION: First data update completed (coordinator_id=%s)", id(coordinator))

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
            from .utils import async_cleanup_all_components
            await async_cleanup_all_components(hass, entry.entry_id)
        except Exception as cleanup_ex:
            _LOGGER.error(
                "Error during cleanup after failed setup: %s", cleanup_ex, exc_info=True
            )

        return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("🧹 UNLOAD: Unloading Lambda integration for entry: %s", entry.entry_id)

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

        # Use centralized cleanup function
        try:
            from .utils import async_cleanup_all_components
            await async_cleanup_all_components(hass, entry.entry_id)
        except Exception:
            _LOGGER.exception("Error during centralized cleanup")
        
        # Services cleanup is now handled by centralized cleanup function
        
        # Clean up domain data if this is the last entry
        if DOMAIN in hass.data and len(hass.data[DOMAIN]) == 0:
            hass.data.pop(DOMAIN, None)

        if not unload_ok:
            _LOGGER.warning("Failed to fully unload Lambda Heat Pumps integration")
        else:
            _LOGGER.info("Lambda Heat Pumps integration unloaded successfully")

        return unload_ok

    except Exception as ex:
        _LOGGER.error("Error during unload: %s", ex, exc_info=True)
        return False


# Export für Home Assistant
__all__ = ['async_migrate_entry']