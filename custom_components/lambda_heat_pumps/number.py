"""Number entities for Lambda Heat Pumps integration."""

from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DOMAIN,
    DEFAULT_HEATING_CURVE_LOW,
    DEFAULT_HEATING_CURVE_NULL,
    DEFAULT_HEATING_CURVE_HIGH,
    HEATING_CURVE_MIN,
    HEATING_CURVE_MAX,
    HEATING_CURVE_STEP,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lambda Heat Pumps number entities from a config entry."""
    # Get number of heating circuits
    num_hc = config_entry.data.get("num_hc", 1)

    entities = []

    # Create heating curve number entities for each heating circuit
    for hc_idx in range(1, num_hc + 1):
        for curve_type in ["low", "null", "high"]:
            entities.append(
                LambdaHeatingCurveNumber(
                    config_entry=config_entry,
                    hc_index=hc_idx,
                    curve_type=curve_type,
                )
            )

    async_add_entities(entities)


class LambdaHeatingCurveNumber(NumberEntity, RestoreEntity):
    """Number entity for heating curve configuration."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    _attr_native_min_value = HEATING_CURVE_MIN
    _attr_native_max_value = HEATING_CURVE_MAX
    _attr_native_step = HEATING_CURVE_STEP
    _attr_native_unit_of_measurement = "°C"

    def __init__(
        self,
        config_entry: ConfigEntry,
        hc_index: int,
        curve_type: str,
    ) -> None:
        """Initialize the heating curve number entity."""
        super().__init__()
        self._config_entry = config_entry
        self._hc_index = hc_index
        self._curve_type = curve_type
        self._cached_value = None

        # Set unique ID
        self._attr_unique_id = (
            f"{config_entry.entry_id}_hc{hc_index}_heating_curve_{curve_type}"
        )

        # Set entity ID
        self._attr_entity_id = (
            f"number.eu08l_hc{hc_index}_heating_curve_{curve_type}"
        )

        # Set name
        curve_names = {
            "low": "Low",
            "null": "Null",
            "high": "High"
        }
        self._attr_name = f"Heating Curve {curve_names[curve_type]}"

        # Set device info for HC device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{config_entry.entry_id}_hc{hc_index}")},
            name=f"Heating Circuit {hc_index}",
            manufacturer="Lambda",
            model="EU08L",
            via_device=(DOMAIN, config_entry.entry_id),
        )

    @property
    def native_value(self) -> float | None:
        """Return the current value of the heating curve parameter."""
        # Return cached value if available for immediate UI update
        if self._cached_value is not None:
            return self._cached_value

        # Get default value based on curve type
        default_values = {
            "low": DEFAULT_HEATING_CURVE_LOW,
            "null": DEFAULT_HEATING_CURVE_NULL,
            "high": DEFAULT_HEATING_CURVE_HIGH,
        }

        return default_values[self._curve_type]

    async def async_set_native_value(self, value: float) -> None:
        """Update the heating curve parameter value."""
        # Cache the value immediately for instant UI update
        self._cached_value = value

        # Trigger immediate state update for instant UI response
        self.async_write_ha_state()

        _LOGGER.info(
            "Updated heating curve %s for HC%d to %.1f°C",
            self._curve_type,
            self._hc_index,
            value,
        )

    async def async_added_to_hass(self) -> None:
        """Restore the state when entity is added to hass."""
        await super().async_added_to_hass()

        # Restore previous state if available
        if (last_state := await self.async_get_last_state()) is not None:
            if last_state.state not in ("unknown", "unavailable"):
                try:
                    self._cached_value = float(last_state.state)
                    _LOGGER.debug(
                        "Restored heating curve %s for HC%d: %.1f°C",
                        self._curve_type,
                        self._hc_index,
                        self._cached_value,
                    )
                except ValueError:
                    _LOGGER.warning(
                        "Could not restore heating curve %s for HC%d: invalid state %s",
                        self._curve_type,
                        self._hc_index,
                        last_state.state,
                    )
