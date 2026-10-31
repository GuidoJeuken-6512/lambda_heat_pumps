"""Adding a controller, and bringing an older entry forward."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_USER, ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.lambda_heat_pumps.const import (
    CONF_FIRMWARE_VERSION,
    CONF_INT32_REGISTER_ORDER,
    CONF_SLAVE_ID,
    CONF_UPDATE_INTERVAL,
    CONF_USE_LEGACY_MODBUS_NAMES,
    DEFAULT_INT32_REGISTER_ORDER,
    DOMAIN,
    ENTRY_VERSION,
    FIRMWARE_VERSIONS,
    ISSUE_UNKNOWN_FIRMWARE,
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


async def test_an_unreadable_old_config_file_falls_back_to_the_firmware_order(
    hass: HomeAssistant,
    controller: Controller,
    old_config_file,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A migration should not fail the whole entry over an unreadable old file."""
    with patch("yaml.safe_load", side_effect=yaml.YAMLError("broken")):
        entry = MockConfigEntry(
            domain=DOMAIN,
            version=8,
            data={
                CONF_NAME: "EU08L",
                CONF_HOST: HOST,
                CONF_PORT: float(PORT),
                CONF_SLAVE_ID: float(SLAVE_ID),
            },
            options={CONF_FIRMWARE_VERSION: "V0.0.8-3K"},
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    # Nothing is pinned: the firmware's own order applies.
    assert CONF_INT32_REGISTER_ORDER not in entry.options
    assert "Could not read the old config file" in caplog.text


async def test_an_older_entry_without_the_config_file(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A user who never had the file keeps the firmware's own order, as in 2.x."""
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

    assert CONF_INT32_REGISTER_ORDER not in entry.options


async def test_a_firmware_changed_in_the_old_options_wins(
    hass: HomeAssistant, controller: Controller
) -> None:
    """2.x read the options first, so the firmware chosen there is the current one (#82).

    The data still holds the one picked when the entry was created.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=8,
        data={
            CONF_NAME: "EU08L",
            CONF_HOST: HOST,
            CONF_PORT: PORT,
            CONF_SLAVE_ID: SLAVE_ID,
            CONF_FIRMWARE_VERSION: "V0.0.9-3K",
        },
        options={CONF_FIRMWARE_VERSION: "V0.0.10-3K"},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.data[CONF_FIRMWARE_VERSION] == "V0.0.10-3K"
    # And nothing is left behind in the options.
    assert CONF_FIRMWARE_VERSION not in entry.options


async def test_an_unknown_firmware_is_reported_until_one_is_chosen(
    hass: HomeAssistant, controller: Controller, caplog: pytest.LogCaptureFixture
) -> None:
    """A name this version does not know is not swapped silently for the oldest."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=8,
        title="EU08L",
        data={
            CONF_NAME: "EU08L",
            CONF_HOST: HOST,
            CONF_PORT: PORT,
            CONF_SLAVE_ID: SLAVE_ID,
            CONF_FIRMWARE_VERSION: "V9.9.9-test",
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    issue_id = f"{ISSUE_UNKNOWN_FIRMWARE}_{entry.entry_id}"
    issues = ir.async_get(hass)
    assert entry.data[CONF_FIRMWARE_VERSION] == FIRMWARE_VERSIONS[-1]
    assert issues.async_get_issue(DOMAIN, issue_id) is not None
    assert "Unknown firmware version 'V9.9.9-test'" in caplog.text

    # Picking the firmware under Reconfigure clears it.
    result = await _reconfigure(hass, entry, "V1.1.0-3K")
    assert result["reason"] == "reconfigure_successful"
    assert issues.async_get_issue(DOMAIN, issue_id) is None


async def test_an_old_config_file_without_a_register_order(
    hass: HomeAssistant, controller: Controller
) -> None:
    """An empty file, or one with the key commented out, pins nothing (#133).

    V1.1.0-3K writes its counters low word first. The migration used to store
    high_first here, which turned the energy counters into absurd values.
    """
    path = Path(hass.config.path("lambda_wp_config.yaml"))
    path.write_text("modbus:\n  # int32_register_order: high_first\n")
    controller.registers[1020] = 0x86A0  # 100000 Wh, low word first
    controller.registers[1021] = 0x0001
    try:
        entry = MockConfigEntry(
            domain=DOMAIN,
            version=8,
            data={
                CONF_NAME: "EU08L",
                CONF_HOST: HOST,
                CONF_PORT: float(PORT),
                CONF_SLAVE_ID: float(SLAVE_ID),
            },
            options={CONF_FIRMWARE_VERSION: "V1.1.0-3K"},
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    finally:
        path.unlink()

    assert CONF_INT32_REGISTER_ORDER not in entry.options
    assert (
        hass.states.get(
            "sensor.eu08l_hp1_compressor_power_consumption_accumulated"
        ).state
        == "100000"
    )


async def test_an_old_config_file_set_to_high_first_is_kept(
    hass: HomeAssistant, controller: Controller
) -> None:
    """An explicit choice in the old file still wins over the firmware's order."""
    path = Path(hass.config.path("lambda_wp_config.yaml"))
    path.write_text("modbus:\n  int32_register_order: high_first\n")
    try:
        entry = MockConfigEntry(
            domain=DOMAIN,
            version=8,
            data={
                CONF_NAME: "EU08L",
                CONF_HOST: HOST,
                CONF_PORT: PORT,
                CONF_SLAVE_ID: SLAVE_ID,
                CONF_FIRMWARE_VERSION: "V1.1.0-3K",
            },
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    finally:
        path.unlink()

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


async def test_reconfiguring_a_controller_that_moved(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A new address is accepted once it answers, and the entry is reloaded."""
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

    result = await entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "EU08L",
            CONF_HOST: "192.168.1.99",
            CONF_PORT: PORT,
            CONF_SLAVE_ID: SLAVE_ID,
            CONF_FIRMWARE_VERSION: "V0.0.8-3K",
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_HOST] == "192.168.1.99"


def _reconfigure_entry(options: dict) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        version=ENTRY_VERSION,
        data={
            CONF_NAME: "EU08L",
            CONF_HOST: HOST,
            CONF_PORT: PORT,
            CONF_SLAVE_ID: SLAVE_ID,
            CONF_FIRMWARE_VERSION: "V0.0.9-3K",
            CONF_USE_LEGACY_MODBUS_NAMES: True,
        },
        options=options,
    )


async def _reconfigure(hass: HomeAssistant, entry, firmware: str) -> dict:
    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "EU08L",
            CONF_HOST: HOST,
            CONF_PORT: PORT,
            CONF_SLAVE_ID: SLAVE_ID,
            CONF_FIRMWARE_VERSION: firmware,
        },
    )
    await hass.async_block_till_done()
    return result


async def test_a_firmware_change_drops_the_register_order(
    hass: HomeAssistant, controller: Controller
) -> None:
    """The new firmware's own order applies after a firmware change.

    Set for V0.0.9-3K, high_first would misread a V1.1.0-3K controller, which
    writes its counters low word first.
    """
    controller.registers[1020] = 0x86A0  # 100000 Wh, low word first
    controller.registers[1021] = 0x0001
    entry = _reconfigure_entry(
        {CONF_INT32_REGISTER_ORDER: "high_first", CONF_UPDATE_INTERVAL: 45}
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await _reconfigure(hass, entry, "V1.1.0-3K")

    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_FIRMWARE_VERSION] == "V1.1.0-3K"
    assert CONF_INT32_REGISTER_ORDER not in entry.options
    # Every other option is kept.
    assert entry.options[CONF_UPDATE_INTERVAL] == 45
    assert (
        hass.states.get(
            "sensor.eu08l_hp1_compressor_power_consumption_accumulated"
        ).state
        == "100000"
    )


async def test_the_same_firmware_keeps_the_register_order(
    hass: HomeAssistant, controller: Controller
) -> None:
    """Changing only the address leaves a chosen order alone."""
    entry = _reconfigure_entry({CONF_INT32_REGISTER_ORDER: "low_first"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await _reconfigure(hass, entry, "V0.0.9-3K")

    assert result["reason"] == "reconfigure_successful"
    assert entry.options[CONF_INT32_REGISTER_ORDER] == "low_first"


async def test_reconfiguring_to_an_address_that_does_not_answer(
    hass: HomeAssistant, controller: Controller
) -> None:
    """The old address is kept until the new one proves it is reachable."""
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

    # Refused only now, so the probe made at setup already succeeded.
    controller.refuse(0)

    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "EU08L",
            CONF_HOST: "192.168.1.100",
            CONF_PORT: PORT,
            CONF_SLAVE_ID: SLAVE_ID,
            CONF_FIRMWARE_VERSION: "V0.0.8-3K",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
    assert entry.data[CONF_HOST] == HOST
