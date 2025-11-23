"""Tests for Lambda Heat Pumps integration."""

import json
import os
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import after path modification
from custom_components.lambda_heat_pumps import config_flow  # noqa: E402

TRANSLATION_PATH = os.path.join(
    os.path.dirname(__file__),
    "../custom_components/lambda_heat_pumps/translations/de.json",
)


class TestTranslations(unittest.TestCase):
    """Test translation files."""

    def test_translation_file_exists(self):
        """Test that translation file exists."""
        self.assertTrue(os.path.exists(TRANSLATION_PATH), "de.json nicht gefunden!")

    def test_translation_keys(self):
        """Test that required translation keys exist."""
        with open(TRANSLATION_PATH, encoding="utf-8") as f:
            data = json.load(f)
        # Prüfe einige wichtige Schlüssel
        self.assertIn("config", data)
        self.assertIn("step", data["config"])
        self.assertIn("user", data["config"]["step"])
        self.assertIn("data", data["config"]["step"]["user"])
        self.assertIn("num_buff", data["config"]["step"]["user"]["data"])
        self.assertIn("num_sol", data["config"]["step"]["user"]["data"])
        self.assertIn("use_legacy_modbus_names", data["config"]["step"]["user"]["data"])
        self.assertIn("options", data)  # options is at root level, not under config
        self.assertIn("step", data["options"])
        self.assertIn("init", data["options"]["step"])
        self.assertIn("data", data["options"]["step"]["init"])
        self.assertIn("hot_water_min_temp", data["options"]["step"]["init"]["data"])
        
        # Prüfe Entity-Übersetzungen für neue Features
        self.assertIn("entity", data)
        self.assertIn("sensor", data["entity"])
        self.assertIn("compressor_start_cycling_total", data["entity"]["sensor"])
        self.assertIn("compressor_start_cycling_daily", data["entity"]["sensor"])
        self.assertIn("compressor_start_cycling_2h", data["entity"]["sensor"])
        self.assertIn("compressor_start_cycling_4h", data["entity"]["sensor"])
        self.assertIn("compressor_start_cycling_monthly", data["entity"]["sensor"])


class TestConfigFlow(unittest.TestCase):
    """Test config flow."""

    def test_config_flow_class_exists(self):
        """Test that config flow class exists."""
        self.assertTrue(hasattr(config_flow, "LambdaConfigFlow"))
        self.assertTrue(callable(getattr(config_flow, "LambdaConfigFlow")))


if __name__ == "__main__":
    unittest.main()
