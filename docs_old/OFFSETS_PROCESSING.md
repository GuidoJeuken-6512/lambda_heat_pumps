# Offset Processing: Cycling and Energy Consumption

This document describes the complete processing flow for **cycling offsets** and **energy consumption offsets** in the Lambda Heat Pumps integration.

## Table of Contents

1. [Overview](#overview)
2. [Configuration](#configuration)
3. [Cycling Offsets](#cycling-offsets)
4. [Energy Consumption Offsets](#energy-consumption-offsets)
5. [Offset Application Flow](#offset-application-flow)
6. [Persistence and Restoration](#persistence-and-restoration)
7. [Examples](#examples)

---

## Overview

Offsets allow you to adjust sensor values to account for historical data that existed before the integration started tracking. This is particularly useful when:

- **Replacing a heat pump** with one that already has operational history
- **Resetting counters** while maintaining historical continuity
- **Migrating data** from another system

### Key Concepts

- **Offsets only apply to `*_total` sensors** (not daily/monthly/yearly)
- **Offsets are additive**: They add to the calculated sensor value
- **Offset tracking prevents double-application**: The system remembers what offset was already applied
- **Dynamic updates**: Offsets can be changed in configuration, and only the difference is applied

---

## Configuration

Offsets are configured in `lambda_wp_config.yaml`:

### Cycling Offsets

```yaml
cycling_offsets:
  hp1:
    heating_cycling_total: 0      # Offset for HP1 heating total cycles
    hot_water_cycling_total: 0    # Offset for HP1 hot water total cycles
    cooling_cycling_total: 0      # Offset for HP1 cooling total cycles
    defrost_cycling_total: 0      # Offset for HP1 defrost total cycles
  hp2:
    heating_cycling_total: 1500   # Example: HP2 already had 1500 heating cycles
    hot_water_cycling_total: 800  # Example: HP2 already had 800 hot water cycles
    cooling_cycling_total: 200    # Example: HP2 already had 200 cooling cycles
    defrost_cycling_total: 50     # Example: HP2 already had 50 defrost cycles
```

### Energy Consumption Offsets

**Important: All values must be specified in kWh!**

```yaml
energy_consumption_offsets:
  hp1:
    heating_energy_total: 0.0       # kWh offset for HP1 heating total
    hot_water_energy_total: 0.0     # kWh offset for HP1 hot water total
    cooling_energy_total: 0.0       # kWh offset for HP1 cooling total
    defrost_energy_total: 0.0       # kWh offset for HP1 defrost total
  hp2:
    heating_energy_total: 150.5     # Example: HP2 already consumed 150.5 kWh for heating
    hot_water_energy_total: 45.25   # Example: HP2 already consumed 45.25 kWh for hot water
    cooling_energy_total: 12.8      # Example: HP2 already consumed 12.8 kWh for cooling
    defrost_energy_total: 3.1       # Example: HP2 already consumed 3.1 kWh for defrost
```

---

## Cycling Offsets

### Initialization and Loading

1. **Coordinator Initialization** (`coordinator.py:375-408`):
   - During coordinator setup, `_load_offsets_and_persisted()` is called
   - Loads configuration from `lambda_wp_config.yaml` via `load_lambda_config()`
   - Stores offsets in `self._cycling_offsets` dictionary
   - Structure: `{"hp1": {"heating_cycling_total": 1500, ...}, ...}`

2. **Sensor Creation**:
   - Cycling sensors are created with `_cycling_value = 0` and `_applied_offset = 0`
   - When added to Home Assistant, `async_added_to_hass()` is called
   - This triggers `restore_state()` to restore previous values from the database

### Application Process

The offset application happens in `LambdaCyclingSensor._apply_cycling_offset()` (`sensor.py:879-932`):

```python
async def _apply_cycling_offset(self):
    # 1. Load configuration from lambda_wp_config.yaml
    config = await load_lambda_config(self.hass)
    cycling_offsets = config.get("cycling_offsets", {})
    
    # 2. Determine device key (e.g., "hp1")
    device_key = f"hp{self._hp_index}"
    
    # 3. Get current offset from configuration
    current_offset = cycling_offsets[device_key].get(self._sensor_id, 0)
    
    # 4. Get previously applied offset from entity attributes
    applied_offset = getattr(self, "_applied_offset", 0)
    
    # 5. Calculate difference to prevent double-application
    offset_difference = current_offset - applied_offset
    
    # 6. Apply only the difference if it changed
    if offset_difference != 0:
        self._cycling_value = int(self._cycling_value + offset_difference)
        self._applied_offset = current_offset
        self.async_write_ha_state()  # Update Home Assistant immediately
```

### When Offsets Are Applied

1. **During `restore_state()`** (`sensor.py:828-877`):
   - Called when sensor is added to Home Assistant (`async_added_to_hass`)
   - Restores previous sensor value from Home Assistant's state database
   - Restores `applied_offset` from entity attributes
   - **Automatically calls `_apply_cycling_offset()`** for total sensors only

2. **During Runtime Updates**:
   - Cycling offsets are also applied to daily sensors during coordinator updates
   - In `coordinator.py:1767-1781`, offsets are added to daily cycling values

### Offset Tracking Mechanism

The system uses intelligent tracking to prevent double-application:

- **`_applied_offset`**: Instance variable tracking currently applied offset
- **`applied_offset` attribute**: Stored in entity's `extra_state_attributes` for persistence
- **Difference calculation**: Only applies `current_offset - applied_offset`
- **Supports bidirectional changes**: Handles both increases and decreases

**Example Scenarios:**

**Scenario 1: First Application**
```
Configuration: heating_cycling_total: 30
Sensor value: 0, applied_offset: 0
Calculation: offset_difference = 30 - 0 = 30
Result: 0 + 30 = 30 ✅
```

**Scenario 2: Offset Increase**
```
Configuration: heating_cycling_total: 50 (was 30)
Sensor value: 100, applied_offset: 30
Calculation: offset_difference = 50 - 30 = 20
Result: 100 + 20 = 120 ✅
```

**Scenario 3: Offset Decrease**
```
Configuration: heating_cycling_total: 20 (was 30)
Sensor value: 150, applied_offset: 30
Calculation: offset_difference = 20 - 30 = -10
Result: 150 + (-10) = 140 ✅
```

---

## Energy Consumption Offsets

### Initialization and Loading

1. **Coordinator Initialization** (`coordinator.py:375-408`):
   - Loaded alongside cycling offsets during `_load_offsets_and_persisted()`
   - Stored in `self._energy_offsets` dictionary
   - Structure: `{"hp1": {"heating_energy_total": 150.5, ...}, ...}`

2. **Sensor Creation**:
   - Energy sensors are created with `_energy_value = 0.0` and `_applied_offset = 0.0`
   - When added to Home Assistant, `restore_state()` restores previous values

### Application Process

The offset application happens in `LambdaEnergyConsumptionSensor._apply_energy_offset()` (`sensor.py:1165-1213`):

```python
async def _apply_energy_offset(self):
    # 1. Load configuration from lambda_wp_config.yaml
    config = await load_lambda_config(self.hass)
    energy_offsets = config.get("energy_consumption_offsets", {})
    
    # 2. Determine device key (e.g., "hp1")
    device_key = f"hp{self._hp_index}"
    
    # 3. Build sensor ID: "{mode}_energy_total"
    sensor_id = f"{self._mode}_energy_total"
    current_offset = energy_offsets[device_key].get(sensor_id, 0.0)
    
    # 4. Get previously applied offset
    applied_offset = getattr(self, "_applied_offset", 0.0)
    
    # 5. Calculate difference
    offset_difference = current_offset - applied_offset
    
    # 6. Apply only the difference
    if offset_difference > 0:
        self._energy_value += float(offset_difference)
        self._applied_offset = current_offset
        self.async_write_ha_state()
    elif offset_difference < 0:
        # Offset was reduced, subtract the difference
        self._energy_value += float(offset_difference)  # negative value
        self._applied_offset = current_offset
        self.async_write_ha_state()
```

### When Offsets Are Applied

**Important**: Unlike cycling offsets, `_apply_energy_offset()` is **NOT automatically called** in `restore_state()`. 

1. **Manual Application** (when needed):
   - Can be called directly if needed, but this is typically not required
   
2. **During Runtime Updates** (`utils.py:1410-1423`):
   - In `increment_energy_consumption_counter()`, offsets are checked and applied:
   ```python
   if period == "total" and energy_offsets is not None:
       device_key = device_prefix  # e.g., "hp1"
       sensor_id = f"{mode}_energy_total"
       offset = float(device_offsets.get(sensor_id, 0.0))
       
       # Check if offset needs to be applied/updated
       if hasattr(energy_entity, "_applied_offset"):
           if energy_entity._applied_offset != offset:
               new_value += offset - energy_entity._applied_offset
               energy_entity._applied_offset = offset
   ```

3. **During Coordinator Updates** (`coordinator.py:1773-1789`):
   - Energy offsets are also applied to daily sensors during coordinator updates
   - Similar to cycling offsets, added to daily energy values

### Offset Tracking Mechanism

Same intelligent tracking as cycling offsets:

- **`_applied_offset`**: Instance variable (float) tracking currently applied offset
- **`applied_offset` attribute**: Stored in entity attributes for persistence
- **Difference calculation**: Only applies the difference
- **Supports bidirectional changes**: Handles increases and decreases

---

## Offset Application Flow

### Complete Flow Diagram

```
1. Integration Starts
   ↓
2. Coordinator._load_offsets_and_persisted()
   ├─ Loads lambda_wp_config.yaml
   ├─ Stores in self._cycling_offsets
   └─ Stores in self._energy_offsets
   ↓
3. Sensor Entities Created
   ├─ LambdaCyclingSensor.__init__()
   │  ├─ _cycling_value = 0
   │  └─ _applied_offset = 0
   └─ LambdaEnergyConsumptionSensor.__init__()
      ├─ _energy_value = 0.0
      └─ _applied_offset = 0.0
   ↓
4. Sensor Added to Home Assistant
   ├─ async_added_to_hass() called
   └─ restore_state(last_state) called
      ├─ Restore value from database
      ├─ Restore applied_offset from attributes
      └─ [Cycling Only] _apply_cycling_offset()
         ├─ Load current offset from config
         ├─ Calculate difference
         ├─ Apply difference to value
         └─ Update applied_offset
   ↓
5. Runtime Updates
   ├─ Coordinator updates sensor values
   ├─ Offsets applied to daily sensors
   └─ [Energy] Offsets checked in increment_energy_consumption_counter()
```

### Detailed Step-by-Step: Cycling Offset Application

1. **Sensor Initialization**:
   ```
   sensor = LambdaCyclingSensor(...)
   → _cycling_value = 0
   → _applied_offset = 0
   ```

2. **Added to Home Assistant**:
   ```
   async_added_to_hass()
   → RestoreEntity.async_added_to_hass()
   → restore_state(last_state)
   ```

3. **State Restoration**:
   ```
   if last_state is not None:
       _cycling_value = int(last_state.state)  # e.g., 100
       _applied_offset = last_state.attributes.get("applied_offset", 0)  # e.g., 0
   else:
       _cycling_value = 0
       _applied_offset = 0
   ```

4. **Offset Application** (only for `*_total` sensors):
   ```
   if self._sensor_id.endswith("_total"):
       await _apply_cycling_offset()
   ```

5. **Offset Calculation**:
   ```
   current_offset = config["cycling_offsets"]["hp1"]["heating_cycling_total"]  # e.g., 1500
   applied_offset = getattr(self, "_applied_offset", 0)  # e.g., 0
   offset_difference = 1500 - 0 = 1500
   ```

6. **Value Update**:
   ```
   _cycling_value = 100 + 1500 = 1600
   _applied_offset = 1500
   async_write_ha_state()  # Update Home Assistant immediately
   ```

---

## Persistence and Restoration

### How Offsets Are Persisted

1. **Entity Attributes**:
   - `applied_offset` is stored in the sensor's `extra_state_attributes`
   - This persists across Home Assistant restarts
   - For cycling sensors (`sensor.py:1012-1023`):
     ```python
     @property
     def extra_state_attributes(self):
         attrs = {...}
         if self._sensor_id.endswith("_total"):
             attrs["applied_offset"] = getattr(self, "_applied_offset", 0)
         return attrs
     ```

2. **State Database**:
   - The sensor value (already including offset) is stored in Home Assistant's state database
   - The `applied_offset` attribute is also stored in the database

### Restoration Process

1. **On Home Assistant Restart**:
   ```
   Integration reloads
   → Coordinator loads offsets from lambda_wp_config.yaml
   → Sensors restore_state()
   → Restores value from database (already includes offset)
   → Restores applied_offset from attributes
   → Re-applies offset (calculates difference)
   → Result: Correct value maintained
   ```

2. **Offset Change Detection**:
   ```
   If config changed:
   → current_offset = new_value (e.g., 2000)
   → applied_offset = old_value from attributes (e.g., 1500)
   → offset_difference = 2000 - 1500 = 500
   → _cycling_value = old_value + 500
   → _applied_offset = 2000 (updated)
   ```

### Preventing Double-Application

The system prevents double-application through:

1. **Tracking Applied Offset**: Always remembers what was already applied
2. **Difference Calculation**: Only applies `current - applied`
3. **Attribute Persistence**: `applied_offset` survives restarts
4. **State Restoration**: Restored value already includes offset

**Example: Why This Matters**

```
Scenario: User restarts Home Assistant

Initial state:
- Config offset: 1500
- Sensor value: 1600 (includes offset)
- applied_offset: 1500

After restart:
- Config offset: 1500 (unchanged)
- Restored value: 1600
- Restored applied_offset: 1500
- Calculation: 1500 - 1500 = 0
- Result: 1600 + 0 = 1600 ✅ (no change, correct!)
```

---

## Examples

### Example 1: New Installation with Historical Data

**Situation**: Installing integration for a heat pump that already has 2000 heating cycles.

**Configuration**:
```yaml
cycling_offsets:
  hp1:
    heating_cycling_total: 2000
```

**Process**:
1. Integration starts, sensor initialized with value 0
2. `restore_state()` called (no previous state)
3. `_apply_cycling_offset()` called:
   - `current_offset = 2000`
   - `applied_offset = 0`
   - `offset_difference = 2000`
   - `_cycling_value = 0 + 2000 = 2000`
   - `_applied_offset = 2000`
4. Sensor now shows 2000 cycles
5. New cycles are added on top: 2001, 2002, 2003...

### Example 2: Changing Offset After Installation

**Situation**: Realize the historical data was actually 2500 cycles, not 2000.

**Original State**:
- Config: `heating_cycling_total: 2000`
- Sensor value: 2100 (2000 offset + 100 new cycles)
- `applied_offset: 2000`

**Update Configuration**:
```yaml
cycling_offsets:
  hp1:
    heating_cycling_total: 2500  # Changed from 2000
```

**After Restart**:
1. `restore_state()` restores:
   - `_cycling_value = 2100`
   - `applied_offset = 2000`
2. `_apply_cycling_offset()` called:
   - `current_offset = 2500`
   - `applied_offset = 2000` (from attributes)
   - `offset_difference = 2500 - 2000 = 500`
   - `_cycling_value = 2100 + 500 = 2600`
   - `_applied_offset = 2500` (updated)
3. Sensor now shows 2600 cycles (2500 offset + 100 new cycles)

### Example 3: Energy Consumption Offset

**Situation**: Heat pump was replaced, new unit starts with 150.5 kWh historical heating energy.

**Configuration**:
```yaml
energy_consumption_offsets:
  hp1:
    heating_energy_total: 150.5  # kWh
```

**Process**:
1. Energy sensor initialized with `_energy_value = 0.0`
2. During first coordinator update, `increment_energy_consumption_counter()` is called
3. Offset check:
   - `offset = 150.5`
   - `applied_offset = 0.0`
   - `offset_difference = 150.5`
   - `new_value = 0.0 + 150.5 = 150.5`
   - `_applied_offset = 150.5`
4. Sensor now shows 150.5 kWh
5. New energy consumption is added on top

### Example 4: Multiple Heat Pumps

**Configuration**:
```yaml
cycling_offsets:
  hp1:
    heating_cycling_total: 1000
  hp2:
    heating_cycling_total: 3000

energy_consumption_offsets:
  hp1:
    heating_energy_total: 50.0
  hp2:
    heating_energy_total: 200.5
```

**Result**:
- HP1 heating cycles: Starts at 1000, increments from there
- HP2 heating cycles: Starts at 3000, increments from there
- HP1 heating energy: Starts at 50.0 kWh, increments from there
- HP2 heating energy: Starts at 200.5 kWh, increments from there

Each heat pump's offsets are applied independently.

---

## Summary

### Key Points

1. **Offset Loading**: Loaded once during coordinator initialization from `lambda_wp_config.yaml`
2. **Offset Application**: 
   - Cycling: Applied automatically in `restore_state()` for total sensors
   - Energy: Applied during runtime updates via `increment_energy_consumption_counter()`
3. **Offset Tracking**: System tracks `applied_offset` to prevent double-application
4. **Dynamic Updates**: Changing offset in config only applies the difference
5. **Persistence**: `applied_offset` stored in entity attributes, survives restarts
6. **Total Sensors Only**: Offsets only apply to `*_total` sensors, not daily/monthly/yearly

### Important Notes

- ⚠️ **Energy offsets must be in kWh** (not Wh)
- ⚠️ **Only `*_total` sensors** receive offsets
- ⚠️ **Offsets are additive** (added to calculated values)
- ✅ **System prevents double-application** through intelligent tracking
- ✅ **Offsets can be changed** after installation (only difference is applied)
- ✅ **Offsets persist** across Home Assistant restarts

