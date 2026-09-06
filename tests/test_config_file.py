"""What `lambda_wp_config.yaml` does: manual offsets, and an external meter."""

from __future__ import annotations

from pathlib import Path

from homeassistant.core import HomeAssistant, State
import pytest
from pytest_homeassistant_custom_component.common import mock_restore_cache_with_extra_data

from custom_components.lambda_heat_pumps.config_file import FILENAME
from custom_components.lambda_heat_pumps.const import ATTR_APPLIED_OFFSET

from .conftest import Controller
from .test_init import enable_sensors, setup_entry, state_of

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


@pytest.fixture(autouse=True)
def no_config_file(hass: HomeAssistant):
    """Start each test without one, and leave none behind.

    The test configuration folder is shared, so a file one test writes would
    otherwise be read by the next.
    """
    path = Path(hass.config.path(FILENAME))
    path.unlink(missing_ok=True)
    yield
    path.unlink(missing_ok=True)


def write_config(hass: HomeAssistant, text: str) -> Path:
    """Put a config file where the integration keeps it."""
    path = Path(hass.config.path(FILENAME))
    path.write_text(text)
    return path


async def test_the_file_is_written_to_start_from(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A fresh installation gets one, so there is something to edit."""
    path = Path(hass.config.path(FILENAME))
    assert not path.exists()

    await setup_entry(hass, controller, legacy=True)

    assert path.exists()
    # All of it commented out, so it changes nothing until someone edits it.
    assert not [
        line
        for line in path.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]


async def test_an_offset_is_added_to_a_lifetime_total(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A total starts from what the heat pump had done before this counted it."""
    write_config(
        hass,
        "cycling_offsets:\n  hp1:\n    heating_cycling_total: 1500\n",
    )
    await setup_entry(hass, controller, legacy=True)

    assert state_of(hass, "eu08l_hp1_heating_cycling_total") == "1500"


async def test_an_offset_does_not_touch_a_counter_over_a_period(
    hass: HomeAssistant, controller: Controller
) -> None:
    """What happened today is not changed by what happened before it."""
    write_config(
        hass,
        "cycling_offsets:\n  hp1:\n    heating_cycling_total: 1500\n",
    )
    entry = await setup_entry(hass, controller, legacy=True)
    await enable_sensors(hass, entry, "eu08l_hp1_heating_cycling_daily")

    assert state_of(hass, "eu08l_hp1_heating_cycling_daily") == "0"


async def test_a_changed_offset_moves_a_restored_total_by_the_difference(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A restart with a changed offset applies only the difference, once.

    The restored value already has the old offset baked in; `_apply_offset()`
    tracks that baseline itself (`applied_offset`) precisely so a changed
    offset moves the total by the delta instead of being added again on top of
    what a previous run already applied.
    """
    mock_restore_cache_with_extra_data(
        hass,
        (
            (
                # The applied offset is a plain state attribute (see
                # `extra_state_attributes`), not part of the typed sensor data.
                State(
                    "sensor.eu08l_hp1_heating_cycling_total",
                    "1500",
                    {ATTR_APPLIED_OFFSET: 1500},
                ),
                {"native_value": 1500, "native_unit_of_measurement": "cycles"},
            ),
        ),
    )
    write_config(
        hass,
        "cycling_offsets:\n  hp1:\n    heating_cycling_total: 2000\n",
    )
    await setup_entry(hass, controller, legacy=True)

    # 1500 (restored) + (2000 - 1500) = 2000 - the new offset applied exactly
    # once, not 1500 + 2000 stacked on top of each other.
    assert state_of(hass, "eu08l_hp1_heating_cycling_total") == "2000"


async def test_a_broken_section_does_not_cost_the_others(
    hass: HomeAssistant, controller: Controller
) -> None:
    """It is hand-edited, so one mistake keeps what still makes sense."""
    write_config(
        hass,
        "cycling_offsets:\n"
        "  not_a_heat_pump:\n"
        "    heating_cycling_total: 1500\n"
        "energy_consumption_offsets:\n"
        "  hp1:\n"
        "    heating_energy_total: 12.5\n",
    )
    await setup_entry(hass, controller, legacy=True)

    assert state_of(hass, "eu08l_hp1_heating_energy_total") == "12.5"
    assert state_of(hass, "eu08l_hp1_heating_cycling_total") == "0"


async def test_energy_is_counted_from_a_meter_when_one_is_given(
    hass: HomeAssistant, controller: Controller
) -> None:
    """An installation with its own meter counts that instead of the register."""
    write_config(
        hass,
        "energy_consumption_sensors:\n"
        "  hp1:\n"
        "    sensor_entity_id: sensor.house_heat_pump_meter\n",
    )
    hass.states.async_set(
        "sensor.house_heat_pump_meter", "40", {"unit_of_measurement": "kWh"}
    )
    entry = await setup_entry(hass, controller, legacy=True)
    coordinator = entry.runtime_data

    # The heat pump is heating, so what the meter counts is booked there.
    hass.states.async_set(
        "sensor.house_heat_pump_meter", "42.5", {"unit_of_measurement": "kWh"}
    )
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert coordinator.totals[1].electrical["heating"] == pytest.approx(2.5)


async def test_a_meter_that_is_not_reporting_books_nothing(
    hass: HomeAssistant, controller: Controller
) -> None:
    """An unavailable meter is not quietly replaced by the register.

    The register counts something else, so falling back to it would book a jump
    the moment the meter came back.
    """
    write_config(
        hass,
        "energy_consumption_sensors:\n"
        "  hp1:\n"
        "    sensor_entity_id: sensor.house_heat_pump_meter\n",
    )
    hass.states.async_set(
        "sensor.house_heat_pump_meter", "unavailable", {"unit_of_measurement": "kWh"}
    )
    entry = await setup_entry(hass, controller, legacy=True)
    coordinator = entry.runtime_data
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert not coordinator.totals[1].electrical
