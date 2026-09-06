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
from homeassistant.util import slugify

from .const import CONF_NAME_PREFIX, CONF_USE_LEGACY_MODBUS_NAMES
from .coordinator import LambdaCapacityLimitCoordinator, LambdaCoordinator

type AnyLambdaCoordinator = LambdaCoordinator | LambdaCapacityLimitCoordinator


class LambdaEntity(CoordinatorEntity[AnyLambdaCoordinator]):
    """Identity and device info shared by every Lambda entity.

    `module` and `index` name the sub-device the entity belongs to — ("hp", 1) —
    or are None for an entity that belongs to the controller itself.

    `component` names the sub-system a poll has to have read for this entity's
    value to be current. An entity whose value is derived, accumulated or set by
    the user names none, and stays available whatever the controller answered.
    """

    _attr_has_entity_name = True

    # The platform this entity belongs to, set by each platform's classes. It is
    # only needed to propose an entity id, so a class that leaves it unset simply
    # gets Home Assistant's own naming.
    _entity_domain: str = ""

    def __init__(
        self,
        coordinator: AnyLambdaCoordinator,
        key: str,
        module: str | None = None,
        index: int | None = None,
        *,
        component: str | None = None,
    ) -> None:
        """Give the entity its unique id and its device."""
        super().__init__(coordinator)
        self._module = module
        self._index = index
        self._polled = component

        entry = coordinator.config_entry
        # Installations created before Home Assistant named entities from their
        # device prefix every unique id with the entry's name. The name is free
        # text, and the shape the entities were registered under folds it to
        # lower case and drops its spaces — so "Lambda EU10L" is `lambdaeu10l`.
        # This has to match that exactly: a unique id that does not is a
        # different entity as far as Home Assistant is concerned, and the one it
        # replaces is orphaned along with its history and its settings.
        prefix = entry.data[CONF_NAME_PREFIX].lower().replace(" ", "")
        legacy = f"{prefix}_" if entry.data[CONF_USE_LEGACY_MODBUS_NAMES] else ""
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
        # Slugified, unlike the unique id: that one has to keep whatever shape an
        # existing installation registered it under, while this one has to be a
        # valid entity id. A name Home Assistant would not accept — anything
        # accented, say — differs between the two for that reason, and a plain
        # one does not differ at all.
        if self._entity_domain:
            object_id = slugify(f"{prefix}_{module_prefix}{key}")
            self.entity_id = f"{self._entity_domain}.{object_id}"

    @property
    def available(self) -> bool:
        """Whether what this entity reports is what the controller holds.

        A module the last poll could not read kept the values it had, which are
        no longer the controller's — so its entities go unavailable while the
        rest of the controller carries on reporting.

        An entity that names no sub-system holds its own value and stays
        available whatever happened to the poll, including a controller that is
        gone for good: a gap in a running total reads as a counter reset and
        takes the long-term statistics with it, and heat pumps are switched off
        for the season as inverters are at night. That test comes first, above
        the coordinator's own — a controller answering nothing at all is exactly
        the case the totals and the derived sensors have to survive. Saying
        whether the controller is answering is a connectivity entity's job, not
        a counter's.
        """
        return self._polled is None or (
            super().available and self._polled not in self.coordinator.failed
        )
