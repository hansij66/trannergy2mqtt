"""
  Rename to config.py

  Configure:
  - MQTT client
  - Debug level
  - Home Assistant
  - InfluxDB

"""

# [ LOGLEVELS ]
# DEBUG, INFO, WARNING, ERROR, CRITICAL
loglevel = "INFO"

# Using local dns names was not always reliable with PAHO
MQTT_BROKER = "192.168.1.1"
MQTT_PORT = 1883
# has to be unique across all MQTT clients
MQTT_CLIENT_UNIQ = 'mqtt-trannergy'
MQTT_QOS = 1
MQTT_USERNAME = "username"
MQTT_PASSWORD = "secret"

MQTT_TOPIC_PREFIX = "solar/trannergy/roof_w"

# [ InfluxDB ]
# Add a influxdb database tag, for Telegraf processing.
# This is not required for core functionality of this parser
# Set to None if Telegraf is not used
INFLUXDB = "solar"
#INFLUXDB = None

#[ TRANNERGY INVERTER ]
# This is used to validate packages
INV_SERIAL = "PVL5400Nxxxxxxxx"

# Required when using TCPCLIENT reader
INV_SERIAL_LOGGER = 123456780
# ip address of the i nverter
INV_IP = "192.168.1.53"
INV_TCPCLIENTPORT = 8899
INV_MAXRETRIES = 60

# NROF parameter reads from inverter per hour (60 equals every minute); only when INV_READER="TCPCLIENT"
INV_READ_RATE = 60

# Select one of the two available readers
# If supported: can read high(er) frequent all inverter parameters --> INV_READ_RATE
INV_READER="TCPCLIENT"



# Inverter sends every 5 minutes an update of all parameters
# When starting this script....be patient at least for 5minutes
# Configure in inverter:
#   Advanced settings
#   Remote Server
#   Add Server B (ip address to ip where this python script is running; port 3203)
#INV_READER="LISTEN"

# [ Home Assistant ]
HA_DISCOVERY = True

# HA MQTT auto discovery only supports one level of hierarchy (eg "trannergy", and not "trannergy/roof_w")
HA_MQTT_DISCOVERY_TOPIC_PREFIX = "trannergy"

# Default is False; when True removes the auto config message when this program exits
HA_DELETECONFIG = False

# Discovery messages per hour
# At start-up, always a discovery message is send
# Default is 12 ==> 1 message every 5 minutes. If the MQTT broker is restarted
# it can take up to 5 minutes before the dsmr device re-appears in HA
HA_INTERVAL = 12