"""Adding a controller, and bringing an older entry forward."""

from __future__ import annotations

from pathlib import Path

import pytest
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_USER, ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.lambda_heat_pumps.const import (
    CONF_FIRMWARE_VERSION,
    CONF_INT32_REGISTER_ORDER,
    CONF_SLAVE_ID,
    CONF_USE_LEGACY_MODBUS_NAMES,
    DEFAULT_INT32_REGISTER_ORDER,
    DOMAIN,
    ENTRY_VERSION,
    REGISTER_ORDER_LOW_FIRST,
)

from .conftest import HOST, PORT, SLAVE_ID, Controller

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


async def test_adding_a_controller(hass: HomeAssistant, controller: Controller) -> None:
    """The user is asked how to reach it, and nothing about its modules."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    # The modules are the controller's business, not the user's.
    assert not any("num_" in str(key) for key in result["data_schema"].schema)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "EU08L",
            CONF_HOST: HOST,
            CONF_PORT: PORT,
            CONF_SLAVE_ID: SLAVE_ID,
            CONF_FIRMWARE_VERSION: "V1.1.0-3K",
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "EU08L"
    # A controller added now names its entities the way Home Assistant does.
    assert result["data"][CONF_USE_LEGACY_MODBUS_NAMES] is False

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data.counts["hp"] == 1


@pytest.mark.usefixtures("unreachable")
async def test_a_controller_that_is_not_there(hass: HomeAssistant) -> None:
    """Nothing is created for an address that does not answer."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "EU08L",
            CONF_HOST: HOST,
            CONF_PORT: PORT,
            CONF_SLAVE_ID: SLAVE_ID,
            CONF_FIRMWARE_VERSION: "V1.1.0-3K",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


@pytest.fixture
def old_config_file(hass: HomeAssistant):
    """The config file the integration used to keep, holding a register order."""
    path = Path(hass.config.path("lambda_wp_config.yaml"))
    path.write_text("modbus:\n  int32_register_order: low_first\n")
    yield path
    path.unlink()


async def test_an_older_entry_is_brought_forward(
    hass: HomeAssistant, controller: Controller, old_config_file
) -> None:
    """The one real setting in the old config file moves onto the entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=8,
        data={
            CONF_NAME: "EU08L",
            CONF_HOST: HOST,
            # The old number selector stored these as floats.
            CONF_PORT: float(PORT),
            CONF_SLAVE_ID: float(SLAVE_ID),
            # The module counts used to be config; they are probed now.
            "num_hps": 3,
            "num_boil": 2,
            "num_hc": 5,
        },
        options={CONF_FIRMWARE_VERSION: "V0.0.8-3K"},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.version == ENTRY_VERSION
    # The counts the user once typed in are gone; what the controller says wins.
    assert "num_hps" not in entry.data
    # The port and unit id are normalised to ints the Modbus frame can pack.
    assert type(entry.data[CONF_PORT]) is int
    assert type(entry.data[CONF_SLAVE_ID]) is int
    assert entry.runtime_data.counts == {"hp": 1, "boil": 1, "buff": 0, "sol": 0, "hc": 1}
    # An entry from before this keeps its entities' names.
    assert entry.data[CONF_USE_LEGACY_MODBUS_NAMES] is True
    # The firmware version is on the entry, not split across it and the options.
    assert entry.data[CONF_FIRMWARE_VERSION] == "V0.0.8-3K"
    # And the register order came across from the file that is no longer read.
    assert entry.options[CONF_INT32_REGISTER_ORDER] == REGISTER_ORDER_LOW_FIRST


async def test_an_older_entry_without_the_config_file(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A user who never had the file gets the default the file would have had."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=8,
        data={
            CONF_NAME: "EU08L",
            CONF_HOST: HOST,
            CONF_PORT: PORT,
            CONF_SLAVE_ID: SLAVE_ID,
            CONF_FIRMWARE_VERSION: "V0.0.8-3K",
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.options[CONF_INT32_REGISTER_ORDER] == DEFAULT_INT32_REGISTER_ORDER


async def test_dhcp_does_not_reoffer_a_configured_controller(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A controller that is already set up is not offered again as new.

    Its entry predates discovery, so it has no MAC to match on; the address it
    was set up with is what stops the re-offer.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=ENTRY_VERSION,
        data={
            CONF_NAME: "EU08L",
            CONF_HOST: HOST,
            CONF_PORT: PORT,
            CONF_SLAVE_ID: SLAVE_ID,
            CONF_FIRMWARE_VERSION: "V0.0.8-3K",
            CONF_USE_LEGACY_MODBUS_NAMES: True,
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(ip=HOST, hostname="lambda", macaddress="0050f4aabbcc"),
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
