"""Tests for V2.7.0 changes: slugify_name_prefix_for_lookup and firmware-dependent register order."""

import pytest
from unittest.mock import AsyncMock, Mock, patch


# ---------------------------------------------------------------------------
# slugify_name_prefix_for_lookup (utils.py) — Issue #93
# ---------------------------------------------------------------------------

class TestSlugifyNamePrefixForLookup:
    """Tests for the new read-only lookup helper added in V2.7.0."""

    def setup_method(self):
        from custom_components.lambda_heat_pumps.utils import (
            slugify_name_prefix_for_lookup,
            normalize_name_prefix,
        )
        self.fn = slugify_name_prefix_for_lookup
        self.old_fn = normalize_name_prefix

    def test_ascii_only_identical_to_normalize(self):
        assert self.fn("EU08L") == "eu08l"
        assert self.fn("EU08L") == self.old_fn("EU08L")

    def test_ascii_with_space_identical_to_normalize(self):
        assert self.fn("Lambda WP") == "lambdawp"
        assert self.fn("Lambda WP") == self.old_fn("Lambda WP")

    def test_umlaut_transliterated(self):
        """Key fix: ä must become a, matching HA entity_registry slugify output."""
        assert self.fn("Wärmepumpe") == "warmepumpe"

    def test_umlaut_o(self):
        assert self.fn("Böhler") == "bohler"

    def test_umlaut_u(self):
        assert self.fn("Wärme Pumpe Ü") == "warmepumpeu"

    def test_empty_string_returns_empty(self):
        assert self.fn("") == ""

    def test_none_returns_empty(self):
        assert self.fn(None) == ""

    def test_non_string_returns_empty(self):
        assert self.fn(42) == ""
        assert self.fn([]) == ""

    def test_regression_normalize_name_prefix_unchanged(self):
        """normalize_name_prefix must NOT transliterate — no behaviour change."""
        assert self.old_fn("Wärmepumpe") == "wärmepumpe"
        assert self.old_fn("EU08L") == "eu08l"
        assert self.old_fn("Lambda WP") == "lambdawp"


# ---------------------------------------------------------------------------
# FIRMWARE_CONFIG / FIRMWARE_VERSION (const_base.py) — V2.7.0
# ---------------------------------------------------------------------------

class TestFirmwareConfig:
    """FIRMWARE_CONFIG is the new primary structure; FIRMWARE_VERSION must be derived from it."""

    def setup_method(self):
        from custom_components.lambda_heat_pumps.const_base import (
            FIRMWARE_CONFIG,
            FIRMWARE_VERSION,
            DEFAULT_FIRMWARE,
        )
        self.config = FIRMWARE_CONFIG
        self.version = FIRMWARE_VERSION
        self.default_fw = DEFAULT_FIRMWARE

    def test_firmware_config_has_required_keys(self):
        expected = {
            "V1.1.0-3K", "V0.0.10-3K", "V0.0.9-3K", "V0.0.8-3K",
            "V0.0.7-3K", "V0.0.6-3K", "V0.0.5-3K", "V0.0.4-3K", "V0.0.3-3K",
        }
        assert expected == set(self.config.keys())

    def test_each_entry_has_version_and_reg_order(self):
        for fw_str, cfg in self.config.items():
            assert "version" in cfg, f"{fw_str} missing 'version'"
            assert "reg_order" in cfg, f"{fw_str} missing 'reg_order'"
            assert cfg["reg_order"] in ("high_first", "low_first"), \
                f"{fw_str} has invalid reg_order: {cfg['reg_order']}"

    def test_firmware_version_derived_correctly(self):
        """FIRMWARE_VERSION must equal {k: v['version'] for k, v in FIRMWARE_CONFIG.items()}."""
        expected = {k: v["version"] for k, v in self.config.items()}
        assert self.version == expected

    def test_well_known_version_integers(self):
        assert self.version["V0.0.3-3K"] == 1
        assert self.version["V0.0.8-3K"] == 6
        assert self.version["V0.0.9-3K"] == 7
        assert self.version["V0.0.10-3K"] == 8

    def test_default_firmware_in_config(self):
        assert self.default_fw in self.config, \
            f"DEFAULT_FIRMWARE '{self.default_fw}' not found in FIRMWARE_CONFIG"

    def test_version_integers_are_unique_or_expected(self):
        """V1.1.0-3K should have a higher or equal version integer than V0.0.10-3K."""
        assert self.version["V1.1.0-3K"] >= self.version["V0.0.10-3K"]


# ---------------------------------------------------------------------------
# get_int32_register_order with firmware-dependent default (modbus_utils.py)
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_entry_fw(request):
    """Config entry mock with configurable firmware version."""
    fw = getattr(request, "param", "V0.0.8-3K")
    entry = Mock()
    entry.options = {"firmware_version": fw}
    entry.data = {}
    return entry


@pytest.fixture
def mock_hass_local():
    hass = Mock()
    hass.data = {}
    hass.config = Mock()
    hass.config.config_dir = "/tmp/test_config"
    return hass


class TestGetInt32RegisterOrder:
    """get_int32_register_order must prefer YAML over FW-default, FW-default over hardcoded."""

    @pytest.mark.asyncio
    async def test_no_yaml_uses_fw_default(self, mock_hass_local):
        """When YAML has no entry and FW maps to high_first, result is high_first."""
        entry = Mock()
        entry.options = {"firmware_version": "V0.0.8-3K"}
        entry.data = {}

        with patch(
            "custom_components.lambda_heat_pumps.utils.load_lambda_config",
            new_callable=AsyncMock,
            return_value={"modbus": {}},
        ):
            from custom_components.lambda_heat_pumps.modbus_utils import get_int32_register_order
            result = await get_int32_register_order(mock_hass_local, entry)
        assert result == "high_first"

    @pytest.mark.asyncio
    async def test_yaml_explicit_overrides_fw_default(self, mock_hass_local):
        """Explicit YAML value wins over FW-default."""
        entry = Mock()
        entry.options = {"firmware_version": "V0.0.8-3K"}
        entry.data = {}

        with patch(
            "custom_components.lambda_heat_pumps.utils.load_lambda_config",
            new_callable=AsyncMock,
            return_value={"modbus": {"int32_register_order": "low_first"}},
        ):
            from custom_components.lambda_heat_pumps.modbus_utils import get_int32_register_order
            result = await get_int32_register_order(mock_hass_local, entry)
        assert result == "low_first"

    @pytest.mark.asyncio
    async def test_no_entry_falls_back_to_default_firmware(self, mock_hass_local):
        """entry=None must still work, using DEFAULT_FIRMWARE for fw_default lookup."""
        with patch(
            "custom_components.lambda_heat_pumps.utils.load_lambda_config",
            new_callable=AsyncMock,
            return_value={"modbus": {}},
        ):
            from custom_components.lambda_heat_pumps.modbus_utils import get_int32_register_order
            result = await get_int32_register_order(mock_hass_local, None)
        assert result in ("high_first", "low_first")

    @pytest.mark.asyncio
    async def test_unknown_fw_version_fallback(self, mock_hass_local):
        """Unknown FW string must fall back to 'high_first'."""
        entry = Mock()
        entry.options = {"firmware_version": "V99.99.99-UNKNOWN"}
        entry.data = {}

        with patch(
            "custom_components.lambda_heat_pumps.utils.load_lambda_config",
            new_callable=AsyncMock,
            return_value={"modbus": {}},
        ):
            from custom_components.lambda_heat_pumps.modbus_utils import get_int32_register_order
            result = await get_int32_register_order(mock_hass_local, entry)
        assert result == "high_first"

    @pytest.mark.asyncio
    async def test_fw_default_low_first_applied(self, mock_hass_local):
        """If FIRMWARE_CONFIG has low_first for a FW version, it must be returned without YAML."""
        entry = Mock()
        entry.options = {"firmware_version": "V0.0.8-3K"}
        entry.data = {}

        patched_config = {"V0.0.8-3K": {"version": 6, "reg_order": "low_first"}}

        with patch(
            "custom_components.lambda_heat_pumps.utils.load_lambda_config",
            new_callable=AsyncMock,
            return_value={"modbus": {}},
        ), patch(
            "custom_components.lambda_heat_pumps.const_base.FIRMWARE_CONFIG",
            patched_config,
        ):
            from custom_components.lambda_heat_pumps.modbus_utils import get_int32_register_order
            result = await get_int32_register_order(mock_hass_local, entry)
        assert result == "low_first"

    @pytest.mark.asyncio
    async def test_legacy_byte_order_still_works(self, mock_hass_local):
        """Legacy int32_byte_order key in YAML must still be respected."""
        entry = Mock()
        entry.options = {"firmware_version": "V0.0.8-3K"}
        entry.data = {}

        with patch(
            "custom_components.lambda_heat_pumps.utils.load_lambda_config",
            new_callable=AsyncMock,
            return_value={"modbus": {"int32_byte_order": "little"}},
        ):
            from custom_components.lambda_heat_pumps.modbus_utils import get_int32_register_order
            result = await get_int32_register_order(mock_hass_local, entry)
        assert result == "low_first"

    @pytest.mark.asyncio
    async def test_invalid_yaml_value_falls_back(self, mock_hass_local):
        """Invalid YAML value must fall back to 'high_first' with warning."""
        entry = Mock()
        entry.options = {"firmware_version": "V0.0.8-3K"}
        entry.data = {}

        with patch(
            "custom_components.lambda_heat_pumps.utils.load_lambda_config",
            new_callable=AsyncMock,
            return_value={"modbus": {"int32_register_order": "invalid_value"}},
        ):
            from custom_components.lambda_heat_pumps.modbus_utils import get_int32_register_order
            result = await get_int32_register_order(mock_hass_local, entry)
        assert result == "high_first"
