## Lambda Heat Pumps – Entity Creation Flow

### Scope and Example

This document describes how **sensor entities** for the Lambda Heat Pumps integration are created, focusing on:

- **Template name**
- **sensor_id**
- **entity_id**
- **unique_id**

The example used throughout this document is the sensor:

- Device name: **`EU08L`** (config entry name)
- Subdevice: **`HP1`** (heat pump index 1)
- Sensor template: **`return_line_temperature`** from `HP_SENSOR_TEMPLATES` in `const.py`

For this example, the resulting IDs are:

- Internal sensor key (`sensor_id_final`): **`hp1_return_line_temperature`**
- Entity ID: **`sensor.eu08l_hp1_return_line_temperature`**
- Unique ID: **`eu08l_hp1_return_line_temperature`**

---

### Step 1 – Sensor Template Definition (`const.py`)

- **Source**: `HP_SENSOR_TEMPLATES` in `const.py`
- **Relevant entry** (simplified):

  - Template key: **`return_line_temperature`**
  - Fields:
    - **`relative_address`**: `5`
    - **`name`**: `"Return Line Temperature"`
    - **`unit`**: `"°C"`
    - **`scale`**: `0.01`
    - **`precision`**: `1`
    - **`data_type`**: `"int16"`
    - **`device_type`**: `"Hp"`
    - **`state_class`**: `"measurement"`

At this point there is **no entity yet**, only a template describing how the Modbus register should be interpreted.

---

### Step 2 – Entry Setup (`async_setup_entry` in `sensor.py`)

The function **`async_setup_entry`** in `sensor.py` is called by Home Assistant to set up all sensor entities for a given config entry.

Key inputs:

- `entry.data["name"]` → example: `"EU08L"`
- `entry.data.get("use_legacy_modbus_names", True)` → typically `True`

Derived values:

- **`name_prefix`**: `entry.data["name"].lower().replace(" ", "")` → **`"eu08l"`**
- **`use_legacy_modbus_names`**: controls how `entity_id` and `unique_id` are constructed.

The function:

1. Retrieves a **`LambdaDataUpdateCoordinator`** instance for the entry.
2. Reads configured device counts (`num_hps`, `num_boil`, `num_buff`, `num_sol`, `num_hc`).
3. **Loads sensor translations** via `load_sensor_translations(hass)` from `utils.py`:
   - This function loads all translation keys from Home Assistant's translation system for the current language.
   - Returns a dictionary mapping `sensor_id` → translated name (e.g., `{"return_line_temperature": "Rücklauf", ...}`).
4. Determines the numeric firmware version via `get_firmware_version_int(entry)`.
5. Builds a list `TEMPLATES` with device types and their filtered sensor templates.

---

### Step 3 – Firmware-Based Template Filtering

Two utility functions in `utils.py` are involved:

- **`get_firmware_version_int(entry)`**
  - Reads the selected firmware from `entry.options` or `entry.data`.
  - Maps the firmware string to an integer (e.g. `1`, `2`, …) via `FIRMWARE_VERSION`.

- **`get_compatible_sensors(sensor_templates, fw_version)`**
  - Filters the given template dictionary to keep only sensors whose `firmware_version` is compatible with `fw_version`.
  - `return_line_temperature` remains present if its `firmware_version` is less than or equal to `fw_version` (or not numeric).

In `async_setup_entry` this is used as:

- `("hp", num_hps, get_compatible_sensors(HP_SENSOR_TEMPLATES, fw_version))`

So `return_line_temperature` becomes part of the active HP sensor templates for all configured heat pumps.

---

### Step 4 – Base Address per Subdevice (`generate_base_addresses`)

For each device type (e.g. `"hp"`, `"boil"`, `"hc"`) and index (`1`, `2`, …), a base Modbus address is generated.

- **Function**: `generate_base_addresses(device_type, count)` in `utils.py`
- **Input** for our example:
  - `device_type = "hp"`
  - `count = num_hps` (at least `1`)
- **Logic**:
  - Uses `BASE_ADDRESSES["hp"]` from `const.py` as `start_address`.
  - Returns a mapping like `{1: start_address, 2: start_address + 100, ...}`.

For **HP1**:

- `base_address = generate_base_addresses("hp", num_hps)[1]`
- The **absolute Modbus register** for `return_line_temperature` is:
  - `address = base_address + relative_address`
  - Here: `address = base_address + 5`

---

### Step 5 – Selecting the Concrete Sensor in the Loop

Inside `async_setup_entry`, for each device type:

- Loop over **indices**: `idx` from `1` to `num_hps`.
- Compute `base_address` for each index.
- Loop over all `sensor_id, sensor_info` in the filtered HP template dictionary.

For our example:

- `prefix = "hp"`
- `idx = 1`
- `device_prefix = "hp1"`
- `sensor_id = "return_line_temperature"`
- `sensor_info["name"] = "Return Line Temperature"`
- `relative_address = 5`

This prepares all values needed to build the final identifiers.

---

### Step 6 – Name and ID Generation (`generate_sensor_names`)

Within `async_setup_entry`, the code first checks for possible name overrides:

- If `use_legacy_modbus_names` is `True` and the coordinator provides a `sensor_overrides` mapping, an override name can be used.
- In the normal case (no override), it calls **`generate_sensor_names`** from `utils.py`.

Call parameters for our example:

- `device_prefix = "hp1"`
- `sensor_name = "Return Line Temperature"`
- `sensor_id = "return_line_temperature"`
- `name_prefix = "eu08l"`
- `use_legacy_modbus_names = True`
- `translations = {...}` (dictionary loaded in Step 2, e.g., `{"return_line_temperature": "Rücklauf", ...}`)

**`generate_sensor_names`** then:

1. **Resolves the translated sensor name**:
   - Looks up `sensor_id` in the `translations` dictionary.
   - If found: `resolved_sensor_name = translations["return_line_temperature"]` → **`"Rücklauf"`** (German).
   - If not found: `resolved_sensor_name = sensor_name` → **`"Return Line Temperature"`** (fallback).
   - Logs a warning if translation is missing (only once per `sensor_id`).
2. Builds the **display name**:
   - Because `device_prefix != sensor_id` →  
     `display_name = resolved_sensor_name` → **`"Rücklauf"`** (already translated).
   - Note: In the current implementation, the device prefix is **not** prepended to the display name.
3. Normalises the name prefix:
   - `name_prefix_lc = "eu08l"`.
4. Creates **entity_id** and **unique_id** (legacy mode):
   - `entity_id = "sensor.eu08l_hp1_return_line_temperature"`
   - `unique_id = "eu08l_hp1_return_line_temperature"`

Back in `async_setup_entry`:

- A separate **internal sensor key** is constructed:
  - `sensor_id_final = "hp1_return_line_temperature"`
  - This key links coordinator data to the concrete entity.

---

### Step 7 – Entity Construction (`LambdaSensor`)

The final sensor entity is instantiated as a **`LambdaSensor`** object:

- **Class**: `LambdaSensor` in `sensor.py`
- Key constructor arguments for our example:
  - `sensor_id = "hp1_return_line_temperature"`
  - `name = "Rücklauf"` (already translated display name from `generate_sensor_names`)
  - `entity_id = "sensor.eu08l_hp1_return_line_temperature"`
  - `unique_id = "eu08l_hp1_return_line_temperature"`
  - `relative_address = 5`
  - `address = base_address + 5`
  - `device_type = "HP"` (derived from the `prefix`)

Inside `LambdaSensor.__init__`:

- `self._sensor_id` is set to `"hp1_return_line_temperature"`.
- `self.entity_id` is set to `"sensor.eu08l_hp1_return_line_temperature"`.
- `self._attr_unique_id` is set to `"eu08l_hp1_return_line_temperature"`.
- **`self._attr_name`** is set to the translated name: **`"Rücklauf"`** (from Step 6).
- **Note**: The current implementation does **not** use `translation_key` attributes. Translations are applied **before** entity construction via `load_sensor_translations()` and `generate_sensor_names()`.

The sensor is appended to an internal list and later registered with Home Assistant via `async_add_entities(sensors)`.

---

### Step 8 – Display Name in Home Assistant UI

The actual name shown in the Home Assistant UI comes from the **`_attr_name`** attribute, which was set during entity construction:

- **`LambdaSensor.name`** property (in `sensor.py`) returns `self._attr_name` (or an override name if configured).
- The name was already translated in **Step 6** via `generate_sensor_names()`, which used the translations loaded in **Step 2**.

Translation lookup process:

1. **`load_sensor_translations(hass)`** in `utils.py`:
   - Calls Home Assistant's `async_get_translations()` for the current language.
   - Extracts translation keys from `component.lambda_heat_pumps.entity.sensor.*` namespace.
   - Returns a dictionary: `{"return_line_temperature": "Rücklauf", ...}`

2. **`generate_sensor_names()`** in `utils.py`:
   - Looks up `sensor_id` in the translations dictionary.
   - Uses the translated name if found, otherwise falls back to the template name.

Relevant translation entry (German):

- File: `custom_components/lambda_heat_pumps/translations/de.json`
- Path: `entity.sensor.return_line_temperature.name`
- Value: `"Rücklauf"`

Result:

- Within the device context of **`EU08L`** and subdevice **`HP1`**, the user sees a sensor with the translated name **"Rücklauf"** associated with the heat pump module.

The **entity_id** and **unique_id** remain:

- `entity_id`: `sensor.eu08l_hp1_return_line_temperature`
- `unique_id`: `eu08l_hp1_return_line_temperature`

---

### End-to-End Function Chain (Summary)

The complete chain of functions involved in creating the example entity is:

1. **`HP_SENSOR_TEMPLATES`** in `const.py`  
   – Static definition of `return_line_temperature` (template).
2. **`async_setup_entry`** in `sensor.py`  
   – Main setup function, reads configuration and orchestrates entity creation.
3. **`load_sensor_translations(hass)`** in `utils.py`  
   – Loads all translation keys from Home Assistant's translation system for the current language.
   – Returns a dictionary mapping `sensor_id` → translated name.
4. **`get_firmware_version_int(entry)`** in `utils.py`  
   – Resolves firmware as integer for compatibility checking.
5. **`get_compatible_sensors(HP_SENSOR_TEMPLATES, fw_version)`** in `utils.py`  
   – Filters the sensor templates by firmware.
6. **`generate_base_addresses("hp", num_hps)`** in `utils.py`  
   – Computes Modbus base addresses per HP index.
7. **`generate_sensor_names(device_prefix, sensor_name, sensor_id, name_prefix, use_legacy_modbus_names, translations)`** in `utils.py`  
   – Looks up translated name from `translations` dictionary.
   – Generates display name (already translated), `entity_id` and `unique_id`.
8. **`LambdaSensor.__init__`** in `sensor.py`  
   – Binds `sensor_id_final`, `entity_id`, `unique_id`, address and sets `_attr_name` to the translated name.
9. **`LambdaSensor.name` property** in `sensor.py`  
   – Returns `_attr_name` (or override name if configured) for display in Home Assistant UI.

---

### Mermaid Diagram – Entity Creation Flow (Example: EU08L / HP1 / return_line_temperature)

```mermaid
flowchart TD
    %% Config entry and templates
    A[ConfigEntry<br/>name = 'EU08L'<br/>use_legacy_modbus_names = true] --> B[async_setup_entry<br/>sensor.py]
    C[HP_SENSOR_TEMPLATES<br/>const.py<br/>key = 'return_line_temperature'] --> B

    %% Translation loading
    B --> T1[load_sensor_translations(hass)<br/>utils.py]
    T1 --> T2[async_get_translations<br/>Home Assistant API]
    T2 --> T3[translations/de.json<br/>entity.sensor.return_line_temperature.name = 'Rücklauf']
    T3 --> T4[translations dict<br/>{'return_line_temperature': 'Rücklauf', ...}]

    %% Firmware and compatibility
    B --> D[get_firmware_version_int(entry)<br/>utils.py]
    D --> E[get_compatible_sensors(HP_SENSOR_TEMPLATES, fw_version)<br/>utils.py]
    E --> F{template contains<br/>'return_line_temperature'?}
    F -->|yes| G[Loop: prefix = 'hp', idx = 1<br/>device_prefix = 'hp1']

    %% Base address and Modbus register
    G --> H[generate_base_addresses('hp', num_hps)<br/>utils.py]
    H --> I[base_address for hp1]
    I --> J[address = base_address + 5<br/>(relative_address)]

    %% Name and IDs with translations
    G --> K[generate_sensor_names(<br/>device_prefix='hp1',<br/>sensor_name='Return Line Temperature',<br/>sensor_id='return_line_temperature',<br/>name_prefix='eu08l',<br/>legacy=true,<br/>translations=dict)<br/>utils.py]
    T4 --> K
    K --> L[name = 'Rücklauf'<br/>already translated]
    K --> M[entity_id = 'sensor.eu08l_hp1_return_line_temperature']
    K --> N[unique_id = 'eu08l_hp1_return_line_temperature']
    G --> O[sensor_id_final = 'hp1_return_line_temperature']

    %% Entity construction
    J --> P[LambdaSensor.__init__<br/>sensor.py]
    L --> P
    M --> P
    N --> P
    O --> P
    C --> P
    P --> Q[LambdaSensor instance<br/>(_sensor_id='hp1_return_line_temperature',<br/>_attr_name='Rücklauf',<br/>entity_id, unique_id)]

    %% Registration and UI
    Q --> R[LambdaSensor.name property<br/>returns _attr_name = 'Rücklauf']
    Q --> S[async_add_entities([...])<br/>sensor.py]
    S --> T[Home Assistant Entity Registry<br/>and State Machine]
    T --> U[UI: device 'EU08L'<br/>subdevice 'HP1'<br/>sensor 'Rücklauf'<br/>(entity_id 'sensor.eu08l_hp1_return_line_temperature')]
```



