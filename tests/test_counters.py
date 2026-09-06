"""The counters: what they count, what survives a restart, and what rolls over."""

from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.util import dt as dt_util
import pytest
from pytest_homeassistant_custom_component.common import (
    async_fire_time_changed,
    mock_restore_cache,
    mock_restore_cache_with_extra_data,
)

from custom_components.lambda_heat_pumps.const import (
    PERIOD_2H,
    PERIOD_4H,
    PERIOD_DAILY,
    PERIOD_HOURLY,
    PERIOD_MONTHLY,
    PERIOD_YEARLY,
    SIGNAL_PERIOD_ROLLOVER,
)
from custom_components.lambda_heat_pumps.coordinator import _periods_ending

from .conftest import Controller
from .test_init import enable_sensors, setup_entry, state_of

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


async def _poll(hass: HomeAssistant, seconds: int) -> None:
    """Let the fast poll run, which is what watches for a cycle."""
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=seconds))
    # The fast poll runs as a background task, which is not waited for by default.
    await hass.async_block_till_done(wait_background_tasks=True)


def _rollover(hass: HomeAssistant, entry_id: str, period: str) -> None:
    """End a period, as the hourly tick does."""
    async_dispatcher_send(
        hass, SIGNAL_PERIOD_ROLLOVER.format(entry_id=entry_id, period=period)
    )


@pytest.mark.parametrize(
    ("moment", "expected"),
    [
        # A plain hour ends only the hourly counters.
        ("2026-07-14 11:00", {PERIOD_HOURLY}),
        # An even hour ends the two-hourly ones too, and every fourth the rest.
        ("2026-07-14 14:00", {PERIOD_HOURLY, PERIOD_2H}),
        ("2026-07-14 16:00", {PERIOD_HOURLY, PERIOD_2H, PERIOD_4H}),
        # Midnight ends the day, and with it the hour, 2h and 4h windows.
        (
            "2026-07-14 00:00",
            {PERIOD_HOURLY, PERIOD_2H, PERIOD_4H, PERIOD_DAILY},
        ),
        # The first of the month ends the month; the first of January the year.
        (
            "2026-08-01 00:00",
            {PERIOD_HOURLY, PERIOD_2H, PERIOD_4H, PERIOD_DAILY, PERIOD_MONTHLY},
        ),
        (
            "2027-01-01 00:00",
            {
                PERIOD_HOURLY,
                PERIOD_2H,
                PERIOD_4H,
                PERIOD_DAILY,
                PERIOD_MONTHLY,
                PERIOD_YEARLY,
            },
        ),
    ],
)
def test_which_periods_end_when(moment: str, expected: set[str]) -> None:
    """An hour boundary ends exactly the periods that finish on it."""
    now = datetime.fromisoformat(moment)
    assert set(_periods_ending(now)) == expected


async def test_a_mode_change_counts_a_cycle(
    hass: HomeAssistant, controller: Controller
) -> None:
    """Entering a mode counts one cycle; staying in it counts no more."""
    await setup_entry(hass, controller, legacy=True)
    assert state_of(hass, "eu08l_hp1_hot_water_cycling_total") == "0"

    controller.registers[1003] = 2  # the heat pump switches to hot water
    await _poll(hass, 3)
    assert state_of(hass, "eu08l_hp1_hot_water_cycling_total") == "1"

    await _poll(hass, 6)  # still in hot water
    assert state_of(hass, "eu08l_hp1_hot_water_cycling_total") == "1"

    controller.registers[1003] = 1  # back to heating...
    await _poll(hass, 9)
    controller.registers[1003] = 2  # ...and into hot water again
    await _poll(hass, 12)
    assert state_of(hass, "eu08l_hp1_hot_water_cycling_total") == "2"


async def test_a_compressor_start_counts_a_cycle(
    hass: HomeAssistant, controller: Controller
) -> None:
    """The compressor beginning to run is a start, whatever the mode."""
    controller.registers[1010] = 0  # the compressor is not running
    await setup_entry(hass, controller, legacy=True)
    assert state_of(hass, "eu08l_hp1_compressor_start_cycling_total") == "0"

    controller.registers[1010] = 4200
    await _poll(hass, 3)
    assert state_of(hass, "eu08l_hp1_compressor_start_cycling_total") == "1"

    await _poll(hass, 6)  # it keeps running; that is not another start
    assert state_of(hass, "eu08l_hp1_compressor_start_cycling_total") == "1"


async def test_energy_is_booked_against_the_current_mode(
    hass: HomeAssistant, controller: Controller
) -> None:
    """What the controller's counter climbed by is charged to the mode it is in."""
    entry = await setup_entry(hass, controller, legacy=True)

    # The heat pump is heating. Its electrical counter climbs by 2000 Wh and its
    # thermal one by 8000 Wh.
    controller.registers[1021] = 0x86A0 + 2000
    controller.registers[1023] = 0x1A80 + 8000
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    assert state_of(hass, "eu08l_hp1_heating_energy_total") == "2.0"
    assert state_of(hass, "eu08l_hp1_heating_thermal_energy_total") == "8.0"
    # Nothing was spent in any other mode.
    assert state_of(hass, "eu08l_hp1_cooling_energy_total") == "0.0"
    # And the coefficient of performance follows from the two.
    assert state_of(hass, "eu08l_hp1_heating_cop_total") == "4.0"


async def test_the_first_reading_is_not_counted(
    hass: HomeAssistant, controller: Controller
) -> None:
    """The controller's counter is already high; only what it climbs by counts."""
    await setup_entry(hass, controller, legacy=True)

    # 100 kWh were on the electrical counter before Home Assistant ever saw it.
    assert state_of(hass, "eu08l_hp1_heating_energy_total") == "0.0"


async def test_a_counter_survives_a_restart(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A counter picks its own value back up, and keeps counting from there."""
    # The entity id Home Assistant gives it, from the device and the sensor's name.
    mock_restore_cache_with_extra_data(
        hass,
        (
            (
                State("sensor.eu08l_hp1_heating_cycling_total", "7"),
                {"native_value": 7, "native_unit_of_measurement": "cycles"},
            ),
        ),
    )
    await setup_entry(hass, controller, legacy=True)
    assert state_of(hass, "eu08l_hp1_heating_cycling_total") == "7"

    controller.registers[1003] = 2  # leave heating...
    await _poll(hass, 3)
    controller.registers[1003] = 1  # ...and come back to it
    await _poll(hass, 6)

    assert state_of(hass, "eu08l_hp1_heating_cycling_total") == "8"


async def test_a_day_ends(hass: HomeAssistant, controller: Controller) -> None:
    """The daily counter starts again, and yesterday keeps the day that ended."""
    entry = await setup_entry(hass, controller, legacy=True)
    await enable_sensors(
        hass,
        entry,
        "eu08l_hp1_hot_water_cycling_daily",
        "eu08l_hp1_hot_water_cycling_yesterday",
    )

    controller.registers[1003] = 2
    await _poll(hass, 3)
    assert state_of(hass, "eu08l_hp1_hot_water_cycling_daily") == "1"
    assert state_of(hass, "eu08l_hp1_hot_water_cycling_yesterday") == "0"

    _rollover(hass, entry.entry_id, PERIOD_DAILY)
    await hass.async_block_till_done()

    assert state_of(hass, "eu08l_hp1_hot_water_cycling_daily") == "0"
    assert state_of(hass, "eu08l_hp1_hot_water_cycling_yesterday") == "1"
    # A total is a total: it does not care that a day ended.
    assert state_of(hass, "eu08l_hp1_hot_water_cycling_total") == "1"


async def test_a_period_that_ends_does_not_end_the_others(
    hass: HomeAssistant, controller: Controller
) -> None:
    """An hour ending leaves the day's counter alone."""
    entry = await setup_entry(hass, controller, legacy=True)
    await enable_sensors(
        hass,
        entry,
        "eu08l_hp1_heating_energy_hourly",
        "eu08l_hp1_heating_energy_daily",
    )

    controller.registers[1021] = 0x86A0 + 3000
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert state_of(hass, "eu08l_hp1_heating_energy_hourly") == "3.0"
    assert state_of(hass, "eu08l_hp1_heating_energy_daily") == "3.0"

    _rollover(hass, entry.entry_id, PERIOD_HOURLY)
    await hass.async_block_till_done()

    assert state_of(hass, "eu08l_hp1_heating_energy_hourly") == "0.0"
    assert state_of(hass, "eu08l_hp1_heating_energy_daily") == "3.0"

    # And what it counts after the hour ended starts from there.
    controller.registers[1021] = 0x86A0 + 4000
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert state_of(hass, "eu08l_hp1_heating_energy_hourly") == "1.0"
    assert state_of(hass, "eu08l_hp1_heating_energy_daily") == "4.0"


async def test_a_counter_restores_from_an_older_installation(
    hass: HomeAssistant, controller: Controller
) -> None:
    """An install upgrading from before typed restore data keeps its totals.

    Those versions recorded only the state, with none of the extra data a sensor
    restores from now — so without falling back to it, upgrading would quietly
    start every cumulative counter again at zero.
    """
    mock_restore_cache(hass, (State("sensor.eu08l_hp1_heating_cycling_total", "42"),))
    await setup_entry(hass, controller, legacy=True)

    assert state_of(hass, "eu08l_hp1_heating_cycling_total") == "42"
