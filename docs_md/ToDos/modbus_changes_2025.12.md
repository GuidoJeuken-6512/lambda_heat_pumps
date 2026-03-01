

# Vergleich: Modbus-Integration Home Assistant (Alt vs. Neu)

| **Operation**       | **Alt (bis 2025.11)**                | **Neu (ab 2025.12)**                | **Hinweis**                                      |
|----------------------|--------------------------------------|--------------------------------------|--------------------------------------------------|
| **Write**           | `modbus.write_register`             | `modbus.write`                      | Einheitlicher Service für Schreiboperationen    |
|                      | `value: 123`                        | `data: 123`                         | Parametername geändert                          |
|                      | `device_address: 1`                 | `slave: 1`                          | Terminologie angepasst                          |
|                      | `device_class: Current`             | `device_class: current`             | Nur noch Kleinbuchstaben                       |
|                      | `data_type: float32` + `count: 2`   | `data_type: float32`                | **`count` entfällt**, wird intern berechnet    |
| **Read**            | `modbus.read_register`              | `modbus.read`                       | Einheitlicher Service für Leseoperationen      |
|                      | `device_address: 1`                 | `slave: 1`                          | Terminologie angepasst                          |
|                      | `count: 2` bei float32              | entfällt bei `data_type: float32`   | Automatische Berechnung                        |
| **Allgemein**       | `value`                             | `data`                              | Einheitliche Parameternamen                    |
|                      | `device_address`                    | `slave`                             | Konsistente Terminologie                       |
|                      | `device_class: Current`             | `device_class: current`             | Kleinbuchstaben für Device-Class               |
