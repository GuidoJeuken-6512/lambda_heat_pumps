"""The `lambda_wp_config.yaml` file in the Home Assistant configuration folder.

Most of what this integration needs is on the config entry, where Home Assistant
can edit it. Three things cannot be, and they live here:

* **Manual offsets** on the cumulative counters. The controller has no lifetime
  totals of its own, so the counters here are only ever "since this integration
  started watching". Replacing a heat pump, or carrying figures over from
  somewhere else, means saying what the totals were before that — which is not a
  setting so much as a statement about history.
* **An external meter** to count a heat pump's energy from, in place of the
  controller's own register, for an installation that has a real meter on it.

The file is written from a template on first run, all of it commented out, and
read once per setup. It is a hand-edited file, so nothing in it is required and
nothing in it can fail the integration: a section that is missing or malformed is
reported and skipped, and the rest is used.

Editing it takes a reload of the integration, as it always has.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
from pathlib import Path
from typing import Any

import voluptuous as vol
import yaml
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

FILENAME = "lambda_wp_config.yaml"

TEMPLATE = """# Configuration for the Lambda Heat Pumps integration.
#
# Everything here is optional, and everything here is commented out. Uncomment
# what you need and reload the integration.
#
# Renaming an entity, hiding one, or disabling one is done in Home Assistant
# itself now, not here.

# The totals the counters should start from — what was already accumulated
# before this integration began counting. Use them after replacing a heat pump,
# or to carry figures over from another system. They are added to the totals, so
# changing one adjusts the total by the difference; they do not apply to a
# counter over a period (daily, monthly and so on).
#cycling_offsets:
#  hp1:
#    heating_cycling_total: 0
#    hot_water_cycling_total: 0
#    cooling_cycling_total: 0
#    defrost_cycling_total: 0
#    compressor_start_cycling_total: 0

#energy_consumption_offsets:
#  hp1:
#    heating_energy_total: 0.0
#    hot_water_energy_total: 0.0
#    cooling_energy_total: 0.0
#    defrost_energy_total: 0.0
#    heating_thermal_energy_total: 0.0
#    hot_water_thermal_energy_total: 0.0
#    cooling_thermal_energy_total: 0.0
#    defrost_thermal_energy_total: 0.0

# Count a heat pump's energy from a meter of your own instead of the
# controller's own register. Give an entity that reports a rising total in Wh,
# kWh or MWh. Leave a heat pump out to use the controller's register.
#energy_consumption_sensors:
#  hp1:
#    sensor_entity_id: sensor.heat_pump_electricity_meter
#    thermal_sensor_entity_id: sensor.heat_pump_heat_meter
"""

# A hand-edited file, so it is described rather than trusted. Every section is
# optional; a key that is not a number, or a heat pump that is not named
# `hp<n>`, is a mistake worth reporting rather than guessing at.
_HEAT_PUMP = vol.Match(r"^hp\d+$", msg="expected a heat pump named hp1, hp2, ...")

_SCHEMA = vol.Schema(
    {
        vol.Optional("cycling_offsets", default=dict): {
            _HEAT_PUMP: {str: vol.Coerce(int)}
        },
        vol.Optional("energy_consumption_offsets", default=dict): {
            _HEAT_PUMP: {str: vol.Coerce(float)}
        },
        vol.Optional("energy_consumption_sensors", default=dict): {
            _HEAT_PUMP: {
                vol.Optional("sensor_entity_id"): str,
                vol.Optional("thermal_sensor_entity_id"): str,
            }
        },
    },
    extra=vol.ALLOW_EXTRA,  # `modbus:` and anything a previous version wrote
)


@dataclass(frozen=True)
class LambdaFileConfig:
    """What the file says, by heat pump key (`hp1`, `hp2`, ...)."""

    cycling_offsets: dict[str, dict[str, int]] = field(default_factory=dict)
    energy_offsets: dict[str, dict[str, float]] = field(default_factory=dict)
    energy_sensors: dict[str, dict[str, str]] = field(default_factory=dict)

    def offset(self, index: int, key: str) -> float:
        """The offset configured for one heat pump's total, or nothing."""
        offsets = (
            self.cycling_offsets
            if key.endswith("_cycling_total")
            else self.energy_offsets
        )
        return float(offsets.get(f"hp{index}", {}).get(key, 0.0))

    def meter(self, index: int, thermal: bool) -> str | None:
        """The entity a heat pump's energy is counted from, if it is not the
        controller's own register."""
        key = "thermal_sensor_entity_id" if thermal else "sensor_entity_id"
        return self.energy_sensors.get(f"hp{index}", {}).get(key)


async def async_load(hass: HomeAssistant) -> LambdaFileConfig:
    """Read the file, writing it from the template first if it is not there."""
    path = Path(hass.config.path(FILENAME))

    def _read() -> LambdaFileConfig:
        if not path.is_file():
            path.write_text(TEMPLATE)
            _LOGGER.debug("Wrote a %s to start from", FILENAME)
            return LambdaFileConfig()

        config: Any = yaml.safe_load(path.read_text()) or {}
        if not isinstance(config, dict):
            _LOGGER.error("%s should describe sections; ignoring it", FILENAME)
            return LambdaFileConfig()
        try:
            config = _SCHEMA(config)
        except vol.Invalid as err:
            # One bad section should not cost the user the others, so the file is
            # re-read a section at a time to keep what does make sense.
            _LOGGER.error("%s: %s", FILENAME, err)
            config = _salvage(config)
        return LambdaFileConfig(
            cycling_offsets=config.get("cycling_offsets", {}),
            energy_offsets=config.get("energy_consumption_offsets", {}),
            energy_sensors=config.get("energy_consumption_sensors", {}),
        )

    try:
        return await hass.async_add_executor_job(_read)
    except (OSError, yaml.YAMLError) as err:
        _LOGGER.error("Could not read %s: %s", FILENAME, err)
        return LambdaFileConfig()


def _salvage(config: dict) -> dict:
    """Keep the sections that are well formed, and drop the ones that are not."""
    kept = {}
    for section, value in config.items():
        try:
            kept |= _SCHEMA({section: value})
        except vol.Invalid:
            _LOGGER.warning("%s: ignoring the %s section", FILENAME, section)
    return kept
