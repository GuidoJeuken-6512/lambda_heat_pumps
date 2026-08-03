"""Which registers a firmware serves.

A controller's register map changes between firmware versions: registers are
added, and occasionally withdrawn and later reintroduced. Probing finds what a
controller answers for, but not what it answers *meaningfully* — a register can
be reserved on one firmware and still reply — so the versions a sensor is known
to be good on are declared alongside it.

A sensor says so in one of two ways, and says nothing at all if it applies
everywhere:

* ``firmware_version`` — the first version the register exists on, and every
  version after it.
* ``firmware_versions`` — the exact set, for a register that is not simply
  present from some version onwards. Its notation is ``"X-Y"`` for an inclusive
  range, ``"-X"`` to take one version back out, and a bare ``X`` for a single
  one, so ``["1-7"]`` is "up to and including 7" and ``["1-9", "-4"]`` is
  "everything up to 9, except 4".

``firmware_versions`` wins where both are given.
"""

from __future__ import annotations

from collections.abc import Iterable

from .const import CONF_FIRMWARE_VERSION, FIRMWARE_CONFIG


def parse_firmware_versions(spec: Iterable[int | str]) -> set[int]:
    """Return the version ordinals a ``firmware_versions`` spec covers.

    Supported elements:
      "X-Y"  -> range X to Y inclusive
      "-X"   -> exclude version X
      X      -> include version X (int)
    """
    included: set[int] = set()
    excluded: set[int] = set()
    for item in spec:
        if isinstance(item, int):
            included.add(item)
        elif isinstance(item, str):
            if item.startswith("-"):
                excluded.add(int(item[1:]))
            elif "-" in item:
                low, high = item.split("-", 1)
                included.update(range(int(low), int(high) + 1))
            else:
                included.add(int(item))
    return included - excluded


def firmware_level(entry) -> int:
    """The version ordinal of the firmware this entry is configured for."""
    name = entry.data.get(CONF_FIRMWARE_VERSION)
    firmware = FIRMWARE_CONFIG.get(name)
    # An unknown name means an entry written by a newer version than this one, or
    # by hand; the oldest map is the one every controller serves.
    return int(firmware["version"]) if firmware else 1


def default_register_order(name: str) -> str | None:
    """How this firmware lays out its 32-bit counters, if it is known."""
    firmware = FIRMWARE_CONFIG.get(name)
    return str(firmware["reg_order"]) if firmware else None


def serves(description, level: int) -> bool:
    """Whether the firmware at ``level`` serves this sensor's register.

    Mirrors the precedence the templates have always used: the exact set if one
    is given, else the first version it appeared on, else every version.
    """
    if description.firmware_versions is not None:
        return level in parse_firmware_versions(description.firmware_versions)
    if description.firmware_version is not None:
        return description.firmware_version <= level
    return True
