# Trannergy MQTT
MQTT client for Trannergy solar inverter (PVL5400). Written in Python 3.x
This program might also work for Ginlong and Omnik inverters.
The inverter has to be connected to the LAN network where this script is running.

Includes Home Assistant MQTT Auto Discovery.
## Usage:
* Copy `systemd/trannergy-mqtt.service` to `/etc/systemd/system`
* Adapt path in `trannergy-mqtt.service` to your install location (default: `/opt/iot/trannergy`)
* Copy `config.rename.py` to `config.py` and adapt for your configuration (minimal: mqtt ip, username, password)
* `sudo systemctl enable trannery-mqtt`
* `sudo systemctl start trannergy-mqtt`

Use
http://mqtt-explorer.com/
to test & inspect MQTT messages

## Requirements
* paho-mqtt
* python 3.x

Tested under Linux; there is no reason why it does not work under Windows.

## Licence
GPL v3

## Versions
1.2.2:
* Initial version on github