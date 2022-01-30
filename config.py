#!/usr/bin/python3

"""
  Rename to config.py

  Configure:
  - MQTT client
  - Debug level

"""

# [ LOGLEVELS ]
# DEBUG, INFO, WARNING, ERROR, CRITICAL
loglevel = "INFO"

# Using local dns names was not always reliable with PAHO
MQTT_BROKER = "192.168.1.1"
MQTT_PORT = 1883
MQTT_CLIENT_UNIQ = 'mqtt-trannergy'
MQTT_QOS = 1
MQTT_USERNAME = "ijntema"
MQTT_PASSWORD = "mosquitto0000"

# Max nrof MQTT messages per second
# Set to 0 for unlimited rate
MQTT_RATE = 100

MQTT_TOPIC_PREFIX = "solar/trannergy/roof_w"

# [ InfluxDB ]
# Add a influxdb database tag, for Telegraf processing (database:INFLUXDB)
# This is not required for core functionality of this parser
# Set to None if Telegraf is not used
INFLUXDB = "solar"
#INFLUXDB = None