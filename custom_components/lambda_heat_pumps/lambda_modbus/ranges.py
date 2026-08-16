"""The controller's readable address ranges.

The planner merges fields into one block read only inside a range, never across a
boundary, so these ranges are what keep the pooled reads to blocks the controller
actually answers.

Two things shape them:

* **The address map itself.** Each module owns a 100-register block, and inside a
  block the values sit in a few contiguous runs with unmapped holes between them
  (a heat pump has nothing at 14, or between 34 and 49). A range per run means a
  hole is never read.
* **Registers the controller only serves one at a time.** The capacity limits
  (relative 50-60) and a heating circuit's flow-line setpoint (relative 7) return
  garbage when they are read as part of a wider block, so each gets a range of
  its own, which forces a single-register read. The two 32-bit counters
  (relative 20-23) likewise get a range per counter — a range wide enough for
  the pair, so each counter is still read in one shot.
"""

from __future__ import annotations

from modbus_connection.model import Range

# Where each module type's first block starts; module n sits 100 registers further.
BASE_ADDRESSES = {"hp": 1000, "boil": 2000, "buff": 3000, "sol": 4000, "hc": 5000}
BLOCK_STRIDE = 100

# Readable runs within one module's block, relative to its base address.
_MAIN_RANGES: tuple[Range, ...] = ((0, 4), (100, 104))
_HP_RANGES: tuple[Range, ...] = (
    (0, 13),
    (15, 19),
    (20, 21),  # compressor_power_consumption_accumulated (int32)
    (22, 23),  # compressor_thermal_energy_output_accumulated (int32)
    (24, 33),
)

# The capacity limits, one read each. They are the heat pump's own component on
# its own poll: eleven requests for settings an installer changes, against five
# for everything a heat pump measures.
HP_CAPACITY_RANGES: tuple[Range, ...] = tuple((n, n) for n in range(50, 61))
_BOIL_RANGES: tuple[Range, ...] = ((0, 5), (50, 50))
_BUFF_RANGES: tuple[Range, ...] = ((0, 9), (50, 50))
_SOL_RANGES: tuple[Range, ...] = ((0, 4), (5, 6), (50, 51))  # 5-6 is energy_total
_HC_RANGES: tuple[Range, ...] = (
    (0, 6),
    (7, 7),  # flow-line setpoint — only answered on its own
    (50, 52),
)

_MODULE_RANGES = {
    "hp": _HP_RANGES,
    "boil": _BOIL_RANGES,
    "buff": _BUFF_RANGES,
    "sol": _SOL_RANGES,
    "hc": _HC_RANGES,
}


def base_address(module: str, index: int) -> int:
    """The absolute base address of module `index` (1-based) of `module` type."""
    return BASE_ADDRESSES[module] + (index - 1) * BLOCK_STRIDE


# The controller's own two sub-systems sit at fixed addresses, not in a module
# block: ambient at 0-4, the e-manager at 100-104. Each reads within its own run.
AMBIENT_RANGES: tuple[Range, ...] = ((0, 4),)
E_MANAGER_RANGES: tuple[Range, ...] = ((100, 104),)


def module_ranges(module: str) -> tuple[Range, ...]:
    """The readable runs within one module's block, relative to its base address.

    A run is a stretch the controller answers as one block read; the gaps between
    runs are unmapped, and a register that only answers on its own is a run of
    one. See this module's docstring.
    """
    return _MODULE_RANGES[module]


def readable_ranges(counts: dict[str, int]) -> tuple[Range, ...]:
    """The absolute readable ranges for a controller with these module counts.

    `counts` maps a module type (`hp`, `boil`, `buff`, `sol`, `hc`) to how many
    of it are installed.
    """
    ranges = list(_MAIN_RANGES)
    for module, count in counts.items():
        relative = _MODULE_RANGES[module]
        if module == "hp":
            # Polled apart from the rest of the heat pump, but readable all the
            # same — a diagnostics dump reads what the controller serves, not
            # what any one schedule happens to ask for.
            relative += HP_CAPACITY_RANGES
        for index in range(1, count + 1):
            base = base_address(module, index)
            ranges += [(base + low, base + high) for low, high in relative]
    return tuple(sorted(ranges))
