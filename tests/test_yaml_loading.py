#!/usr/bin/env python3
"""
Test für YAML-Loading-Problem
"""

import sys
import os
import asyncio
from unittest.mock import Mock

# Füge den Pfad zur Integration hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components', 'lambda_heat_pumps'))

# Mock der Home Assistant Abhängigkeiten
sys.modules['homeassistant.core'] = Mock()
sys.modules['homeassistant.helpers.entity_registry'] = Mock()
sys.modules['homeassistant.const'] = Mock()
sys.modules['homeassistant.helpers.entity_component'] = Mock()

def test_yaml_loading():
    """Test der YAML-Ladung."""
    print("🧪 Teste YAML-Loading...")
    
    # Test 1: Direkte YAML-Ladung
    import yaml
    with open('lambda_wp_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    print(f"✅ YAML direkt geladen: {config}")
    print(f"✅ modbus: {config.get('modbus', {})}")
    print(f"✅ int32_byte_order: {config.get('modbus', {}).get('int32_byte_order', 'NOT_FOUND')}")
    
    # Test 2: load_lambda_config Funktion
    try:
        from utils import load_lambda_config
        
        async def test_load_lambda_config():
            mock_hass = Mock()
            mock_hass.config.config_dir = os.path.dirname(os.path.abspath('lambda_wp_config.yaml'))
            
            config = await load_lambda_config(mock_hass)
            print(f"✅ load_lambda_config: {config}")
            print(f"✅ modbus: {config.get('modbus', {})}")
            print(f"✅ int32_byte_order: {config.get('modbus', {}).get('int32_byte_order', 'NOT_FOUND')}")
            
            return config
        
        asyncio.run(test_load_lambda_config())
        
    except Exception as e:
        print(f"❌ Fehler bei load_lambda_config: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: get_int32_byte_order Funktion
    try:
        from modbus_utils import get_int32_byte_order
        
        async def test_get_int32_byte_order():
            mock_hass = Mock()
            mock_hass.config.config_dir = os.path.dirname(os.path.abspath('lambda_wp_config.yaml'))
            
            byte_order = await get_int32_byte_order(mock_hass)
            print(f"✅ get_int32_byte_order: {byte_order}")
            
            return byte_order
        
        asyncio.run(test_get_int32_byte_order())
        
    except Exception as e:
        print(f"❌ Fehler bei get_int32_byte_order: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_yaml_loading()
