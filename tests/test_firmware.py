"""Which firmware serves which register: the version arithmetic itself.

Pure functions, no controller needed - `test_init.py` and `test_platforms.py`
already exercise `serves()` end to end through real sensors.
"""

from __future__ import annotations

from types import SimpleNamespace

from custom_components.lambda_heat_pumps.const import CONF_FIRMWARE_VERSION
from custom_components.lambda_heat_pumps.firmware import (
    default_register_order,
    firmware_level,
    parse_firmware_versions,
    serves,
)


def test_a_bare_int_is_included() -> None:
    assert parse_firmware_versions([3]) == {3}


def test_a_bare_numeral_string_is_included() -> None:
    assert parse_firmware_versions(["3"]) == {3}


def test_a_range_is_inclusive_of_both_ends() -> None:
    assert parse_firmware_versions(["1-4"]) == {1, 2, 3, 4}


def test_a_leading_dash_excludes_one_version_from_the_rest() -> None:
    assert parse_firmware_versions(["1-9", "-4"]) == {1, 2, 3, 5, 6, 7, 8, 9}


def test_firmware_level_of_a_known_name() -> None:
    entry = SimpleNamespace(data={CONF_FIRMWARE_VERSION: "V0.0.8-3K"})
    assert firmware_level(entry) == 6


def test_firmware_level_of_an_unknown_name_is_the_oldest() -> None:
    """An entry from a newer version of the integration, or hand-edited."""
    entry = SimpleNamespace(data={CONF_FIRMWARE_VERSION: "not-a-real-firmware"})
    assert firmware_level(entry) == 1


def test_default_register_order_of_a_known_firmware() -> None:
    assert default_register_order("V0.0.8-3K") == "high_first"


def test_default_register_order_of_an_unknown_firmware_is_unset() -> None:
    assert default_register_order("not-a-real-firmware") is None


def test_a_sensor_with_no_firmware_restriction_serves_everywhere() -> None:
    description = SimpleNamespace(firmware_versions=None, firmware_version=None)
    assert serves(description, 1)


def test_a_sensor_with_a_minimum_version_does_not_serve_below_it() -> None:
    description = SimpleNamespace(firmware_versions=None, firmware_version=5)
    assert not serves(description, 4)
    assert serves(description, 5)
    assert serves(description, 6)


def test_an_exact_set_wins_over_a_minimum_version() -> None:
    description = SimpleNamespace(firmware_versions=["1-3"], firmware_version=5)
    assert serves(description, 2)
    assert not serves(description, 5)
