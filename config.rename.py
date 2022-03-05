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

# Max nrof MQTT messages per second transmitted by MQTT client
# Set to 0 for unlimited rate
MQTT_RATE = 100

MQTT_TOPIC_PREFIX = "solar/trannergy/roof_w"

# [ InfluxDB ]
# Add a influxdb database tag, for Telegraf processing (database:INFLUXDB)
# This is not required for core functionality of this parser
# Set to None if Telegraf is not used
INFLUXDB = "solar"
#INFLUXDB = None

#[ TRANNERGY INVERTER ]
INV_SERIAL = "PVL5400N177E4008"

# Required when using TCPCLIENT reader
INV_SERIAL_LOGGER = 625830567
INV_IP = "192.168.1.53"
INV_TCPCLIENTPORT = 8899

# NROF parameter reads from inverter per hour (60 equals every minute)
INV_READ_RATE = 60

# Select one of the two available readers
#
# If supported: can read high frequent all inverter parameters
INV_READER="TCPCLIENT"

# Inverter sends every 5 minutes an update of all parameters
# Configure in inverter
# Advanced settings
# Server: ip address to ip where this python script is running; port 3203
#INV_READER="LISTEN"