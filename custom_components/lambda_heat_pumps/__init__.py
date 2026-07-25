"""The Lambda Heat Pumps integration.

The integration owns the Modbus link: it opens one connection to the controller,
takes a unit handle on it, and hands that to the `lambda_modbus` device library.
Which modules the controller has is discovered here, once, by probing it — a
Lambda system's hardware is fixed, so there is nothing for the user to configure
and nothing to re-detect until the entry is reloaded.
"""

from __future__ import annotations

import logging
from pathlib import Path

import yaml
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry
from modbus_connection import ModbusError
from modbus_connection.tmodbus import connect_tcp

from .const import (
    CONF_FIRMWARE_VERSION,
    CONF_HOST,
    CONF_INT32_REGISTER_ORDER,
    CONF_PORT,
    CONF_SLAVE_ID,
    CONF_USE_LEGACY_MODBUS_NAMES,
    DEFAULT_INT32_REGISTER_ORDER,
    ENTRY_VERSION,
    FIRMWARE_VERSIONS,
    REGISTER_ORDER_HIGH_FIRST,
    REGISTER_ORDER_LOW_FIRST,
)
from .coordinator import LambdaConfigEntry, LambdaCoordinator
from .module_auto_detect import async_detect_modules
from .services import async_setup_services, async_setup_writers

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.CLIMATE, Platform.NUMBER, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: LambdaConfigEntry) -> bool:
    """Set up a Lambda controller from a config entry."""
    # The port and unit id are read straight into a Modbus frame, which needs
    # ints; the number selector that set them hands back floats, and older
    # entries were stored that way.
    port = int(entry.data[CONF_PORT])
    slave_id = int(entry.data[CONF_SLAVE_ID])
    try:
        connection = await connect_tcp(entry.data[CONF_HOST], port=port)
    except ModbusError as err:
        raise ConfigEntryNotReady(f"Could not connect to the controller: {err}") from err

    unit = connection.for_unit(slave_id)
    try:
        counts = await async_detect_modules(unit)
    except ModbusError as err:
        await connection.close()
        raise ConfigEntryNotReady(f"Could not probe the controller: {err}") from err
    except Exception:
        # Anything else would leak the open connection, and setup retries — so it
        # would leak one per attempt.
        await connection.close()
        raise

    # From here the coordinator owns the connection: it closes it on unload, and
    # Home Assistant unloads the entry even when this first refresh fails.
    coordinator = LambdaCoordinator(hass, entry, connection, unit, counts)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    # Nothing here reloads the entry, and the two things that used to are both
    # better off without it: a dropped link is re-established by the next poll,
    # which keeps the entities and the probed register map in place rather than
    # rebuilding them for a blip, and an options change is reloaded by the
    # options flow itself, being an OptionsFlowWithReload.

    # Every module is a device hanging off the controller, so the controller has
    # to exist before any of them — a platform that only creates modules would
    # otherwise be pointing its entities at a device that is not there yet.
    device_registry.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id, **coordinator.device_info(None, None)
    )

    async_setup_services(hass)
    async_setup_writers(coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: LambdaConfigEntry) -> bool:
    """Unload a config entry; the coordinator closes the connection it owns."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: LambdaConfigEntry) -> bool:
    """Bring an older entry up to date.

    Everything the integration is configured with now lives on the entry. What
    used to live in `lambda_wp_config.yaml` was either something Home Assistant
    already does — disabling an entity, renaming one — or, in the single case of
    the 32-bit register order, a real setting, which is moved here.
    """
    if entry.version >= ENTRY_VERSION:
        return True

    data = dict(entry.data)
    options = dict(entry.options)

    # The module counts are probed on every setup now.
    for key in ("num_hps", "num_boil", "num_buff", "num_sol", "num_hc"):
        data.pop(key, None)

    # The number selector stored these as floats; the Modbus frame needs ints.
    data[CONF_PORT] = int(data[CONF_PORT])
    data[CONF_SLAVE_ID] = int(data[CONF_SLAVE_ID])

    # Entries that predate this were all named with the prefix.
    data.setdefault(CONF_USE_LEGACY_MODBUS_NAMES, True)
    # The firmware version was written to the options by some flows and the data
    # by others; the entry is the one place it belongs.
    firmware = data.get(CONF_FIRMWARE_VERSION) or options.pop(
        CONF_FIRMWARE_VERSION, None
    )
    data[CONF_FIRMWARE_VERSION] = (
        firmware if firmware in FIRMWARE_VERSIONS else FIRMWARE_VERSIONS[-1]
    )

    options.setdefault(
        CONF_INT32_REGISTER_ORDER, await _async_read_register_order(hass)
    )

    hass.config_entries.async_update_entry(
        entry, data=data, options=options, version=ENTRY_VERSION
    )
    return True


async def _async_read_register_order(hass: HomeAssistant) -> str:
    """The 32-bit register order the retired YAML config file was set to."""
    path = Path(hass.config.path("lambda_heat_pumps", "lambda_wp_config.yaml"))

    def _read() -> str:
        if not path.is_file():
            return DEFAULT_INT32_REGISTER_ORDER
        config = yaml.safe_load(path.read_text()) or {}
        modbus = config.get("modbus") or {}
        # The key was renamed once, and before that used Modbus's own words for
        # it, which described the wrong thing.
        order = modbus.get("int32_register_order") or modbus.get("int32_byte_order")
        return {
            "high_first": REGISTER_ORDER_HIGH_FIRST,
            "big": REGISTER_ORDER_HIGH_FIRST,
            "low_first": REGISTER_ORDER_LOW_FIRST,
            "little": REGISTER_ORDER_LOW_FIRST,
        }.get(order, DEFAULT_INT32_REGISTER_ORDER)

    try:
        return await hass.async_add_executor_job(_read)
    except (OSError, yaml.YAMLError) as err:
        _LOGGER.warning(
            "Could not read the old config file, assuming the default "
            "32-bit register order: %s",
            err,
        )
        return DEFAULT_INT32_REGISTER_ORDER
