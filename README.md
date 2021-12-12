# HHCN8I8OP-MQTT
MQTT Middleman for the HHC-N8I8OP

Features:
- Turn outputs on or off via MQTT message
- Subscribe to input changes via MQTT
- Home Assistant compatible as Binary Sensor and Switch entity

## Device setup
Use the manufacturer's tool to configure the IP address on the device and set the device to operate in TCP Server mode.  The default port for this is 5000 but you may also use a custom port.

## Running
All configuration of the tool is done via environment variables.  This enables easy Docker support as well.

Options:
- MQTT_HOSTNAME - IP Address or DNS name of the MQTT server
- MQTT_PORT - Port number of the MQTT server (optional: default 1883)
- MQTT_USERNAME - Username to connect to the MQTT server (optional: default no authentication)
- MQTT_PASSWORD - Password to connect to the MQTT server (optional: default no authentication)
- MQTT_PREFIX - Prefix to use when building MQTT topics
- DEVICE_HOSTNAME - IP Address or DNS name of the Relay device
- DEVICE_PORT - Port number of the TCP Server of the Relay device (optional: default 5000)
- HA_COMPATIBLE - Set this to true to enable Home Assistant-compatible auto-discovery (optional: default false)
