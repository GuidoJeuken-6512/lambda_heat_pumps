from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode, RestoreNumber
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    HC_HEATING_CURVE_NUMBER_CONFIG,
    HC_ROOM_THERMOSTAT_NUMBER_CONFIG,
)
from .utils import (
    build_device_info,
    build_subdevice_info,
    generate_sensor_names,
    load_sensor_translations,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lambda Heat Pump number entities."""
    coordinator_data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if coordinator_data is None:
        _LOGGER.error("No coordinator data found for entry %s", entry.entry_id)
        return

    num_hc = entry.data.get("num_hc", 1)
    use_legacy_modbus_names = entry.data.get("use_legacy_modbus_names", True)
    name_prefix = entry.data.get("name", "").lower().replace(" ", "")
    room_thermostat_enabled = entry.options.get("room_thermostat_control", False)
    sensor_translations = await load_sensor_translations(hass)

    number_entities: list[LambdaHeatingCurveNumber] = []

    for hc_index in range(1, num_hc + 1):
        device_prefix = f"hc{hc_index}"
        for sensor_id, spec in HC_HEATING_CURVE_NUMBER_CONFIG.items():
            names = generate_sensor_names(
                device_prefix,
                spec["name"],
                sensor_id,
                name_prefix,
                use_legacy_modbus_names,
                translations=sensor_translations,
            )

            base_entity_id = names["entity_id"]
            if base_entity_id.startswith("sensor."):
                entity_id = base_entity_id.replace("sensor.", "number.", 1)
            elif "." in base_entity_id:
                entity_id = f"number.{base_entity_id.split('.', 1)[1]}"
            else:
                entity_id = f"number.{base_entity_id}"
            unique_id = f"{names['unique_id']}_number"

            number_entities.append(
                LambdaHeatingCurveNumber(
                    entry=entry,
                    hc_index=hc_index,
                    sensor_id=sensor_id,
                    name=names["name"],
                    entity_id=entity_id,
                    unique_id=unique_id,
                    spec=spec,
                )
            )

        if room_thermostat_enabled:
            for sensor_id, spec in HC_ROOM_THERMOSTAT_NUMBER_CONFIG.items():
                names = generate_sensor_names(
                    device_prefix,
                    spec["name"],
                    sensor_id,
                    name_prefix,
                    use_legacy_modbus_names,
                    translations=sensor_translations,
                )

                base_entity_id = names["entity_id"]
                if base_entity_id.startswith("sensor."):
                    entity_id = base_entity_id.replace("sensor.", "number.", 1)
                elif "." in base_entity_id:
                    entity_id = f"number.{base_entity_id.split('.', 1)[1]}"
                else:
                    entity_id = f"number.{base_entity_id}"
                unique_id = f"{names['unique_id']}_number"

                number_entities.append(
                    LambdaHeatingCurveNumber(
                        entry=entry,
                        hc_index=hc_index,
                        sensor_id=sensor_id,
                        name=names["name"],
                        entity_id=entity_id,
                        unique_id=unique_id,
                        spec=spec,
                    )
                )

    if not number_entities:
        _LOGGER.debug("No heating curve numbers created for entry %s", entry.entry_id)
        return

    _LOGGER.info(
        "Created %d heating curve number entities for %d heating circuits",
        len(number_entities),
        num_hc,
    )
    async_add_entities(number_entities)


class LambdaHeatingCurveNumber(RestoreNumber, NumberEntity):
    """Number entity representing a heating curve support point."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        hc_index: int,
        sensor_id: str,
        name: str,
        entity_id: str,
        unique_id: str,
        spec: dict[str, Any],
    ) -> None:
        self._entry = entry
        self._hc_index = hc_index
        self._sensor_id = sensor_id
        self.entity_id = entity_id
        self._attr_name = name
        self._attr_unique_id = unique_id

        self._attr_native_unit_of_measurement = spec.get("unit")
        self._attr_native_min_value = spec.get("min_value")
        self._attr_native_max_value = spec.get("max_value")
        self._attr_native_step = spec.get("step")
        self._attr_mode = NumberMode.BOX
        self._attr_icon = "mdi:chart-bell-curve-cumulative"
        self._outside_temp_point = spec.get("outside_temp_point")

        default_value = spec.get("default", 0.0)
        self._attr_native_value = float(default_value)
        precision = spec.get("precision")
        if precision is not None:
            self._attr_suggested_display_precision = precision

    async def async_added_to_hass(self) -> None:
        """Restore the previous state when added to Home Assistant."""
        await super().async_added_to_hass()
        last_number_data = await self.async_get_last_number_data()
        if last_number_data and last_number_data.native_value is not None:
            self._attr_native_value = float(last_number_data.native_value)
        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Persist the newly set value."""
        self._attr_native_value = float(value)
        self.async_write_ha_state()

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information for this number entity."""
        if self._hc_index:
            return build_subdevice_info(self._entry, "hc", self._hc_index)
        return build_device_info(self._entry)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes for diagnostics."""
        return {
            "sensor_id": self._sensor_id,
            "hc_index": self._hc_index,
            "outside_temp_point": self._outside_temp_point,
        }

