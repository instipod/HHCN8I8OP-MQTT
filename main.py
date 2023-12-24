#!python3

from HHCIODriver import HHCIODriver
import logging
import os
import paho.mqtt.client as mqtt
import sys
import threading
import time
import hashlib

mqtt_prefix = os.getenv("MQTT_PREFIX")
mqtt_base = "devices/" + str(mqtt_prefix) + "/"
mqtt_client_id = "HHC-MQTT-Bridge-" + str(hashlib.sha256(os.urandom(32)).hexdigest()[:7])
mqtt_client = mqtt.Client(mqtt_client_id)
device_driver = None


def on_mqtt_message(client, userdata, message):
    global mqtt_base, device_driver
    payload = str(message.payload.decode("utf-8"))
    topic = str(message.topic)

    try:
        if (mqtt_base + "outputs") in topic:
            topic_parts = topic.split("/")
            if len(topic_parts) == 5:
                output_number = int(topic_parts[3])
                logging.info("Received MQTT message to command output {} to state {}".format(output_number, payload))
                device_driver.operate_relay(output_number, (payload == "ON"))
                if payload == "ON":
                    client.publish(mqtt_base + "outputs/{}/state".format(output_number), "ON")
                else:
                    client.publish(mqtt_base + "outputs/{}/state".format(output_number), "OFF")

        # Check whether Home Assistant was rebooted needs to 
        # republish discovery info to re-register the device
        elif "homeassistant/status" in topic:
            if os.getenv("HA_COMPATIBLE") is not None:
                if payload == "online":
                    publish_ha_discovery_info(client)

    except ConnectionError as e:
        #device is not available at this time
        pass
    except Exception as e:
        logging.warning("Ignoring an exception ({}) that occurred while processing an incoming MQTT message.".format(e))


def on_mqtt_connect(client, userdata, flags, rc):
    global mqtt_base
    client.subscribe(mqtt_base + "outputs/1/command")
    client.subscribe(mqtt_base + "outputs/2/command")
    client.subscribe(mqtt_base + "outputs/3/command")
    client.subscribe(mqtt_base + "outputs/4/command")
    client.subscribe(mqtt_base + "outputs/5/command")
    client.subscribe(mqtt_base + "outputs/6/command")
    client.subscribe(mqtt_base + "outputs/7/command")
    client.subscribe(mqtt_base + "outputs/8/command")

    if os.getenv("HA_COMPATIBLE") is not None:
        client.subscribe("homeassistant/status")

    logging.info("MQTT is now connected!")


def on_mqtt_disconnect(client, userdata, rc):
    global device_driver
    logging.warning("MQTT is now disconnected!")


def on_device_connect():
    global mqtt_client, mqtt_base
    logging.info("Device has come online.")
    mqtt_client.publish(mqtt_base + "connection", "online", retain=True)


def on_device_disconnect():
    global mqtt_client, mqtt_base, device_driver
    logging.warning("Device has gone offline!")
    mqtt_client.publish(mqtt_base + "connection", "offline", retain=True)

    while not device_driver.connect(skip=True):
        logging.warning("Failed to reconnect to the device, backing off for 30 seconds...")
        time.sleep(30)


def periodic_input_update(mqtt_client):
    global device_driver, mqtt_base

    values = {}

    while True:
        for input in range(1, 9):
            try:
                value = device_driver.read_input(input)

                should_publish = False
                if input in values.keys():
                    if value != values[input]:
                        should_publish = True
                else:
                    should_publish = True

                if should_publish:
                    values[input] = value
                    if (value == "0"):
                        logging.info("Publishing new input value to MQTT:  Input {} is now OFF".format(input))
                        mqtt_client.publish(mqtt_base + "inputs/{}".format(input), "OFF", retain=True)
                    else:
                        logging.info("Publishing new input value to MQTT:  Input {} is now ON".format(input))
                        mqtt_client.publish(mqtt_base + "inputs/{}".format(input), "ON", retain=True)
            except ConnectionError as e:
                # device is not available at this time
                time.sleep(3)
            except Exception as e:
                logging.warning("Ignoring exception ({}) that occurred while reading value of input {}.".format(e, input))

        time.sleep(0.5)


def publish_ha_discovery_info(mqtt_client):
    global mqtt_prefix, mqtt_base

    logging.info("Publishing Home Assistant-compatible discovery messages.")

    for input in range(1, 9):
        mqtt_client.publish("homeassistant/binary_sensor/{}-input-{}/config".format(mqtt_prefix, input), '{{"name": "{} Input {}", "object_id": "{}_input_{}", "unique_id": "{}_input_{}", "state_topic": "{}inputs/{}", "avty_t": "{}connection", "dev": {{"mf": "Unbranded", "mdl": "HHC-N8I8OP", "ids": "{}", "name": "{}"}}}}'.format(mqtt_prefix, input, mqtt_prefix, input, mqtt_prefix, input, mqtt_base, input, mqtt_base, "HHC-" + mqtt_prefix, mqtt_prefix))
    for output in range(1, 9):
        mqtt_client.publish("homeassistant/switch/{}-output-{}/config".format(mqtt_prefix, output), '{{"name": "{} Output {}", "object_id": "{}_output_{}", "unique_id": "{}_output_{}", "command_topic": "{}outputs/{}/command", "state_topic": "{}outputs/{}/state", "avty_t": "{}connection", "dev": {{"mf": "Unbranded", "mdl": "HHC-N8I8OP", "ids": "{}", "name": "{}"}}}}'.format(mqtt_prefix, output, mqtt_prefix, output, mqtt_prefix, output, mqtt_base, output, mqtt_base, output, mqtt_base, "HHC-" + mqtt_prefix, mqtt_prefix))


def startup():
    global mqtt_client, device_driver, mqtt_prefix, mqtt_base
    mqtt_hostname = os.getenv("MQTT_HOSTNAME")
    mqtt_port = os.getenv("MQTT_PORT")
    mqtt_username = os.getenv("MQTT_USERNAME")
    mqtt_password = os.getenv("MQTT_PASSWORD")

    device_hostname = os.getenv("DEVICE_HOSTNAME")
    device_port = os.getenv("DEVICE_PORT")

    log_level = os.getenv("LOG_LEVEL")

    if log_level is None:
        log_level = logging.INFO
    elif log_level == "DEBUG":
        log_level = logging.DEBUG
    logging.basicConfig(level=log_level)

    if mqtt_hostname is None:
        logging.critical("MQTT hostname is not defined!")
        sys.exit(1)
        return

    if mqtt_prefix is None:
        logging.critical("MQTT prefix is not defined!")
        sys.exit(1)
        return

    if mqtt_port is None or mqtt_port == 0:
        logging.info("MQTT port is not defined, assuming default of 1883.")
        mqtt_port = 1883
    else:
        mqtt_port = int(mqtt_port)

    if device_hostname is None:
        logging.critical("Device hostname is not defined!")
        sys.exit(1)
        return

    if device_port is None or device_port == 0:
        logging.info("Device port is not defined, assuming default of 5000.")
        device_port = 5000
    else:
        device_port = int(device_port)

    mqtt_client.on_message = on_mqtt_message
    mqtt_client.on_connect = on_mqtt_connect
    mqtt_client.on_disconnect = on_mqtt_disconnect

    if mqtt_username is not None and mqtt_password is not None:
        logging.info("Using MQTT password authentication.")
        mqtt_client.username_pw_set(mqtt_username, mqtt_password)

    try:
        mqtt_client.will_set(mqtt_base + "connection", "offline", retain=True)
        mqtt_client.connect(mqtt_hostname, mqtt_port)
    except:
        logging.critical("Could not connect to MQTT server!")
        sys.exit(1)
        return

    mqtt_client.loop_start()

    if os.getenv("HA_COMPATIBLE") is not None:
        publish_ha_discovery_info(mqtt_client)

    device_driver = HHCIODriver(device_hostname, device_port, on_device_connect, on_device_disconnect)
    if not device_driver.connect():
        logging.critical("Could not connect to the device at startup!")

    input_thread = threading.Thread(target=periodic_input_update, args=(mqtt_client,))
    input_thread.start()


startup()