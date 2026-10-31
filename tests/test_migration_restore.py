"""Restoring a lifetime total across an old-to-new version upgrade.

Kept apart from `test_config_file.py`: a test that needs the real recorder
(`recorder_mock`) has to have it hook in before `hass` is created, which means
`recorder_mock` must be the first fixture resolved - `enable_custom_integrations`
is requested explicitly here (instead of the module-wide mark the other test
files use) so it, and `hass` along with it, only resolve afterwards.
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from homeassistant.components.recorder.models import (
    StatisticData,
    StatisticMeanType,
    StatisticMetaData,
)
from homeassistant.components.recorder.statistics import async_import_statistics
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.recorder import get_instance
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import mock_restore_cache_with_extra_data

from custom_components.lambda_heat_pumps.config_file import FILENAME

from .conftest import Controller
from .test_config_file import write_config
from .test_init import setup_entry, state_of


async def test_a_restart_from_unavailable_restores_from_statistics(
    recorder_mock, enable_custom_integrations, hass: HomeAssistant, controller: Controller
) -> None:
    """An old version's entities go unavailable while it unloads for an upgrade -
    that alone must not reset a lifetime total back to zero.

    Home Assistant's long-term statistics still hold the real last value even
    when the plain state - and the attribute `applied_offset` normally rides
    on - is gone. `_restored_value()`'s statistics fallback picks the value
    back up, and the configured offset is treated as already included in it
    rather than added a second time on top.
    """
    # The test configuration folder is shared across the whole session, not
    # just this file - clean up rather than pulling in test_config_file's own
    # autouse fixture for that, which would force `hass` to resolve before
    # `recorder_mock` does (see the module docstring).
    config_path = Path(hass.config.path(FILENAME))
    config_path.unlink(missing_ok=True)
    try:
        async_import_statistics(
            hass,
            StatisticMetaData(
                source="recorder",
                statistic_id="sensor.eu08l_hp1_heating_energy_total",
                unit_of_measurement="kWh",
                has_sum=True,
                mean_type=StatisticMeanType.NONE,
                name=None,
                unit_class=None,
            ),
            [
                StatisticData(
                    start=dt_util.utcnow().replace(minute=0, second=0, microsecond=0)
                    - timedelta(hours=2),
                    state=736.17,
                    sum=736.17,
                )
            ],
        )
        await get_instance(hass).async_block_till_done()

        mock_restore_cache_with_extra_data(
            hass,
            (
                (
                    State(
                        "sensor.eu08l_hp1_heating_energy_total", STATE_UNAVAILABLE, {}
                    ),
                    None,
                ),
            ),
        )
        write_config(
            hass,
            "energy_consumption_offsets:\n  hp1:\n    heating_energy_total: 445.974\n",
        )
        await setup_entry(hass, controller, legacy=True)

        # 736.17 restored from statistics; the offset (445.974) is treated as
        # already included in it, not added a second time on top.
        assert state_of(hass, "eu08l_hp1_heating_energy_total") == "736.17"
    finally:
        config_path.unlink(missing_ok=True)
