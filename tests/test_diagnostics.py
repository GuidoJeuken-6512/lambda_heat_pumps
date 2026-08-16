"""The diagnostics download: raw registers, and what surrounds them."""

from __future__ import annotations

import pytest
from homeassistant.components.diagnostics import REDACTED
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.diagnostics import (
    get_diagnostics_for_config_entry,
)

from custom_components.lambda_heat_pumps.const import CONF_HOST

from .conftest import Controller
from .test_init import setup_entry

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


async def _diagnostics(
    hass: HomeAssistant, entry: MockConfigEntry, hass_client
) -> dict:
    return await get_diagnostics_for_config_entry(hass, hass_client, entry)


async def test_the_dump_carries_the_raw_registers(
    hass: HomeAssistant, controller: Controller, hass_client
) -> None:
    """The registers come out undecoded — the words, not the values."""
    entry = await setup_entry(hass, controller, legacy=True)
    registers = (await _diagnostics(hass, entry, hass_client))["registers"]

    # The raw word, not the 34.12 °C the entity shows for it.
    assert registers["1004"] == 3412
    # A 32-bit counter is two separate words here; the dump does not combine them.
    assert registers["1020"] == 0x0001
    assert registers["1021"] == 0x86A0


async def test_the_dump_covers_the_installed_modules_only(
    hass: HomeAssistant, controller: Controller, hass_client
) -> None:
    """It reads the blocks the controller answers for, and no others."""
    entry = await setup_entry(hass, controller, legacy=True)
    diagnostics = await _diagnostics(hass, entry, hass_client)

    addresses = {int(address) for address in diagnostics["registers"]}
    assert 1004 in addresses  # the one heat pump
    assert 2002 in addresses  # the one boiler
    # A second heat pump is not installed, so its block is never read.
    assert not any(1100 <= address < 1200 for address in addresses)
    assert diagnostics["detected_modules"] == {
        "hp": 1,
        "boil": 1,
        "buff": 0,
        "sol": 0,
        "hc": 1,
    }


async def test_the_dump_keeps_going_past_a_refused_register(
    hass: HomeAssistant, controller: Controller, hass_client
) -> None:
    """A register the controller refuses drops out; the rest still comes through.

    A truncated controller is the one whose dump is worth having, so the read
    falls back to one register at a time and does not stop at the first refusal.
    """
    controller.refuse(2004)  # inside the boiler block
    controller.refuse(2005)
    entry = await setup_entry(hass, controller, legacy=True)
    registers = (await _diagnostics(hass, entry, hass_client))["registers"]

    # The served registers on both sides of the refusal are there.
    assert registers["2002"] == 480
    assert registers["2050"] == 520
    # The refused ones are simply absent, not an error that ended the dump.
    assert "2004" not in registers
    assert registers["5002"] == 340  # a later module still got read


async def test_the_host_is_redacted(
    hass: HomeAssistant, controller: Controller, hass_client
) -> None:
    """The one thing that says where the user is does not go in the download."""
    entry = await setup_entry(hass, controller, legacy=True)
    diagnostics = await _diagnostics(hass, entry, hass_client)

    assert diagnostics["entry"]["data"][CONF_HOST] == REDACTED

async def test_the_dump_still_carries_the_capacity_limits(
    hass: HomeAssistant, controller: Controller, hass_client
) -> None:
    """Reading them on their own poll does not take them out of the dump.

    The dump reads what the controller serves, not what any one schedule happens
    to ask for, so moving these off the full poll must not quietly drop eleven
    registers out of every issue report.
    """
    entry = await setup_entry(hass, controller, legacy=True)
    registers = (await _diagnostics(hass, entry, hass_client))["registers"]

    for address in range(1050, 1061):
        assert str(address) in registers, f"{address} is missing from the dump"


async def test_the_dump_does_not_pass_for_a_poll(
    hass: HomeAssistant, controller: Controller, hass_client
) -> None:
    """Downloading diagnostics does not write a state for every entity.

    The dump reads the controller's registers straight off the unit rather than
    through the model, so it refreshes no field and fires no listener. A user
    downloading diagnostics is asking what the controller holds, not asking for
    an extra poll — and an entity's last-changed should not move because of it.
    """
    entry = await setup_entry(hass, controller, legacy=True)
    device = entry.runtime_data.device

    fired: list[str] = []
    device.ambient.add_update_listener(lambda: fired.append("ambient"))
    device.heat_pumps[0].add_update_listener(lambda: fired.append("hp1"))

    await _diagnostics(hass, entry, hass_client)
    assert not fired, "the diagnostics download passed for a poll"

    # A real poll does fire them, so the listeners were wired up correctly.
    await entry.runtime_data.async_refresh()
    assert sorted(fired) == ["ambient", "hp1"]


async def test_the_dump_says_what_the_last_poll_made_of_the_controller(
    hass: HomeAssistant, controller: Controller, hass_client
) -> None:
    """A module that is not answering shows up in the download."""
    entry = await setup_entry(hass, controller, legacy=True)

    controller.answer_busy(1004)
    await entry.runtime_data.async_refresh()
    diagnostics = await _diagnostics(hass, entry, hass_client)

    assert list(diagnostics["poll"]["failed"]) == ["hp1"]
    assert "boil1" in diagnostics["poll"]["updated"]
