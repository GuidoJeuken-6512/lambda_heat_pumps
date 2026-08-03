"""Base entity for the Lambda Heat Pumps integration.

Every module the controller has — each heat pump, boiler, buffer, solar module
and heating circuit — is its own sub-device, linked to the controller via
`via_device`. The two always-present sub-systems (ambient and the e-manager)
belong to the controller itself.

The unique-id shape here is load-bearing: it is what keeps an existing
installation's entities attached to their history.
"""

from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_NAME_PREFIX, CONF_USE_LEGACY_MODBUS_NAMES
from .coordinator import LambdaCoordinator


class LambdaEntity(CoordinatorEntity[LambdaCoordinator]):
    """Identity and device info shared by every Lambda entity.

    `module` and `index` name the sub-device the entity belongs to — ("hp", 1) —
    or are None for an entity that belongs to the controller itself.
    """

    _attr_has_entity_name = True

    # The platform this entity belongs to, set by each platform's classes. It is
    # only needed to propose an entity id, so a class that leaves it unset simply
    # gets Home Assistant's own naming.
    _entity_domain: str = ""

    def __init__(
        self,
        coordinator: LambdaCoordinator,
        key: str,
        module: str | None = None,
        index: int | None = None,
    ) -> None:
        """Give the entity its unique id and its device."""
        super().__init__(coordinator)
        self._module = module
        self._index = index

        entry = coordinator.config_entry
        # Installations created before Home Assistant named entities from their
        # device prefix every unique id with the entry's name.
        legacy = (
            f"{entry.data[CONF_NAME_PREFIX].lower()}_"
            if entry.data[CONF_USE_LEGACY_MODBUS_NAMES]
            else ""
        )
        module_prefix = f"{module}{index}_" if module else ""
        self._attr_unique_id = f"{legacy}{module_prefix}{key}"
        self._attr_device_info = coordinator.device_info(module, index)

        # Left alone, Home Assistant builds the entity id out of the entity's
        # *translated* name: a German instance gets `sensor.eu08l_aussentemperatur`,
        # and two names differing only by a sign ("Heizkurve-22°C" and
        # "Heizkurve+22°C") slugify to the same id and are quietly suffixed `_2`.
        # Proposing one built from the register's key instead keeps it the same in
        # every language, and unambiguous, while the displayed name stays
        # translated. It is a proposal, not a demand — an id already taken is
        # still resolved by the registry, and an entity that already exists keeps
        # the id it was registered with.
        if self._entity_domain:
            prefix = entry.data[CONF_NAME_PREFIX].lower()
            self.entity_id = (
                f"{self._entity_domain}.{prefix}_{module_prefix}{key}"
            )
