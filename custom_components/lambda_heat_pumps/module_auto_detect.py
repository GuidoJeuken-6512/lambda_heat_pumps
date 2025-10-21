"""Module auto-detection utilities for Lambda Heat Pumps integration."""

from __future__ import annotations

import logging
import asyncio

from typing import TYPE_CHECKING, Any
from .modbus_utils import async_read_holding_registers

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# Test registers for each module type
MODULE_TEST_REGISTERS = {
    "hp": [1000, 1001, 1002],  # Heat pump error, state registers
    "boil": [2000, 2001, 2002],  # Boiler error, state, temp registers
    "buff": [3000, 3001, 3002],  # Buffer error, state, temp registers
    "sol": [4000, 4001, 4002],  # Solar error, state, temp registers
    "hc": [5000, 5001, 5002],  # Heating circuit error, state, temp registers
}

# Maximum expected modules per type
MAX_MODULE_COUNTS = {
    "hp": 3,
    "boil": 5,
    "buff": 5,
    "sol": 2,
    "hc": 12,
}


async def auto_detect_modules(client: Any, slave_id: int) -> dict[str, int]:
    """
    Automatically detect installed modules by testing register accessibility.

    Args:
        client: Modbus client
        slave_id: Modbus slave ID

    Returns:
        Dict with detected module counts: {
            "hp": 1, "boil": 1, "hc": 2, "buff": 0, "sol": 0
        }

    """
    # Gesamt-Timeout für komplette Auto-Detection: 15 Sekunden
    async def _auto_detect_internal():
        detected = {"hp": 0, "boil": 0, "buff": 0, "sol": 0, "hc": 0}

        for module_type, test_registers in MODULE_TEST_REGISTERS.items():
            max_count = MAX_MODULE_COUNTS[module_type]

            _LOGGER.debug("Testing %s modules (max: %s)", module_type, max_count)

            for module_idx in range(max_count):
                # Calculate base address for this module instance
                if module_type == "hp":
                    # HP: 1000, 1100, 1200
                    base_address = 1000 + (module_idx * 100)
                elif module_type == "boil":
                    # Boiler: 2000, 2100, 2200, etc.
                    base_address = 2000 + (module_idx * 100)
                elif module_type == "buff":
                    # Buffer: 3000, 3100, 3200, etc.
                    base_address = 3000 + (module_idx * 100)
                elif module_type == "sol":
                    # Solar: 4000, 4100
                    base_address = 4000 + (module_idx * 100)
                elif module_type == "hc":
                    # HC: 5000, 5100, 5200, etc.
                    base_address = 5000 + (module_idx * 100)
                else:
                    continue

                # Test if this module instance exists by reading first test register
                test_register = base_address + (test_registers[0] % 100)

                try:
                    # Verwende die Kompatibilitätsfunktion mit Timeout
                    result = await asyncio.wait_for(
                        async_read_holding_registers(
                            client, test_register, 1, slave_id
                        ),
                        timeout=2.0  # 2 Sekunden Timeout pro Register-Read
                    )

                    if not result.isError():
                        detected[module_type] = module_idx + 1
                        _LOGGER.debug(
                            "Detected %s module %s at address %s",
                            module_type,
                            module_idx + 1,
                            test_register,
                        )
                    else:
                        # No more modules of this type
                        _LOGGER.debug(
                            "No %s module %s found at address %s",
                            module_type,
                            module_idx + 1,
                            test_register,
                        )
                        break

                except asyncio.TimeoutError:
                    _LOGGER.debug(
                        "Timeout testing %s module %s at %s (2s timeout)",
                        module_type,
                        module_idx + 1,
                        test_register,
                    )
                    # Stop checking this module type on timeout
                    break
                except (AttributeError, ConnectionError, TimeoutError) as ex:
                    _LOGGER.debug(
                        "Error testing %s module %s at %s: %s",
                        module_type,
                        module_idx + 1,
                        test_register,
                        ex,
                    )
                    # Stop checking this module type on error
                    break

        # Ensure minimum counts for critical modules
        if detected["hp"] == 0:
            detected["hp"] = 1  # Always assume at least 1 heat pump
            _LOGGER.info("No heat pump detected, assuming 1 (minimum required)")

        _LOGGER.info("Auto-detected modules: %s", detected)
        return detected

    try:
        return await asyncio.wait_for(_auto_detect_internal(), timeout=15.0)
    except asyncio.TimeoutError:
        _LOGGER.warning("Auto-detection timed out after 15 seconds, using fallback values")
        return {"hp": 1, "boil": 1, "buff": 0, "sol": 0, "hc": 1}  # Fallback-Werte


async def update_entry_with_detected_modules(
    hass: HomeAssistant, entry: ConfigEntry, detected_modules: dict
) -> bool:
    """
    Update config entry with auto-detected module counts.

    Args:
        hass: HomeAssistant instance
        entry: Config entry to update
        detected_modules: Dict with detected module counts

    Returns:
        True if entry was updated, False if no changes needed

    """
    current_data = dict(entry.data)
    updated = False

    for module_type, count in detected_modules.items():
        key = f"num_{module_type}s" if module_type == "hp" else f"num_{module_type}"
        if module_type == "hc":
            key = "num_hc"

        current_count = current_data.get(key, 0)
        if current_count != count:
            current_data[key] = count
            updated = True
            _LOGGER.info("Updated %s from %s to %s", key, current_count, count)

    if updated:
        hass.config_entries.async_update_entry(entry, data=current_data)
        _LOGGER.info("Config entry updated with auto-detected module counts")
        return True

    _LOGGER.debug("No module count changes needed")
    return False
