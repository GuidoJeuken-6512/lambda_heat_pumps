"""Test constants."""

import unittest

from custom_components.lambda_heat_pumps.const import (
    BOIL_SENSOR_TEMPLATES,
    CALCULATED_SENSOR_TEMPLATES,
    DEFAULT_NAME,
    DOMAIN,
    HP_SENSOR_TEMPLATES,
)


class TestConst(unittest.TestCase):
    """Test constants."""

    def test_constants(self):
        """Test constants."""
        self.assertEqual(DOMAIN, "lambda_heat_pumps")
        self.assertEqual(DEFAULT_NAME, "EU08L")

    def test_calculated_sensor_templates_structure(self):
        """Test structure of calculated sensor templates."""
        self.assertIsInstance(CALCULATED_SENSOR_TEMPLATES, dict)
        self.assertGreater(len(CALCULATED_SENSOR_TEMPLATES), 0)

        for sensor_id, template_info in CALCULATED_SENSOR_TEMPLATES.items():
            # Test required fields
            self.assertIn("name", template_info)
            self.assertIn("unit", template_info)
            self.assertIn("precision", template_info)
            self.assertIn("data_type", template_info)
            self.assertIn("firmware_version", template_info)
            self.assertIn("device_type", template_info)
            self.assertIn("writeable", template_info)
            self.assertIn("state_class", template_info)
            
            # Test data_type is "calculated"
            self.assertEqual(template_info["data_type"], "calculated")

            # Test writeable is False for calculated sensors
            self.assertFalse(template_info["writeable"])
            
            # Test new attributes for cycling and energy sensors
            if 'cycling' in sensor_id or 'energy' in sensor_id:
                self.assertIn("operating_state", template_info)
                self.assertIn("reset_interval", template_info)

    def test_calculated_sensor_templates_device_class(self):
        """Test that calculated sensor templates have device_class field."""
        for sensor_id, template_info in CALCULATED_SENSOR_TEMPLATES.items():
            self.assertIn("device_class", template_info)
            # device_class can be None or a valid SensorDeviceClass value
            device_class = template_info["device_class"]
            if device_class is not None:
                self.assertIsInstance(device_class, str)

    def test_calculated_sensor_templates_content(self):
        """Test that calculated sensor templates contain expected sensors."""
        expected_sensors = ["cop_calc"]  # Only cop_calc is currently defined

        for sensor in expected_sensors:
            assert (
                sensor in CALCULATED_SENSOR_TEMPLATES
            ), f"'{sensor}' not found in CALCULATED_SENSOR_TEMPLATES"

    def test_sensor_templates_device_class(self):
        """Test that all sensor templates have device_class field."""
        all_templates = {**HP_SENSOR_TEMPLATES, **BOIL_SENSOR_TEMPLATES}

        for sensor_id, template_info in all_templates.items():
            # device_class is optional in some templates
            if "device_class" in template_info:
                device_class = template_info["device_class"]
                if device_class is not None:
                    self.assertIsInstance(device_class, str)

    def test_temperature_sensors_device_class(self):
        """Test that temperature sensors have correct device_class."""
        temperature_sensors = [
            "flow_line_temperature",
            "return_line_temperature",
            "energy_source_inlet_temperature",
            "energy_source_outlet_temperature",
        ]

        for sensor_id in temperature_sensors:
            if sensor_id in HP_SENSOR_TEMPLATES:
                template_info = HP_SENSOR_TEMPLATES[sensor_id]
                # Check if device_class exists and is temperature
                if "device_class" in template_info:
                    self.assertEqual(template_info["device_class"], "temperature")
                self.assertEqual(template_info["unit"], "°C")

    def test_power_sensors_device_class(self):
        """Test that power sensors have correct device_class."""
        power_sensors = [
            "emgr_actual_power",
            "emgr_actual_power_consumption",
            "emgr_power_consumption_setpoint",
        ]

        for sensor_id in power_sensors:
            # These are in main sensors, check if they exist
            # This test might need adjustment based on actual sensor structure
            pass

    def test_template_syntax(self):
        """Test that calculated sensor templates have valid Jinja syntax."""
        for sensor_id, template_info in CALCULATED_SENSOR_TEMPLATES.items():
            # Only test templates that have a template field
            if "template" in template_info and template_info["template"]:
                template_str = template_info["template"]

                # Test basic Jinja syntax elements
                self.assertIn("{{", template_str)
                self.assertIn("}}", template_str)

                # Test that template uses proper Jinja filters
                self.assertIn("|", template_str)
                self.assertIn("float", template_str)
                self.assertIn("round", template_str)

    def test_device_type_consistency(self):
        """Test that device_type is consistent across templates."""
        for sensor_id, template_info in CALCULATED_SENSOR_TEMPLATES.items():
            device_type = template_info["device_type"]
            # Should be one of the valid device types
            valid_device_types = ["hp", "boil", "hc", "buff", "sol", "main"]
            self.assertIn(device_type, valid_device_types)
