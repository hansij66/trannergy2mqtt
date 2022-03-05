#!/usr/bin/python3

"""
 DESCRIPTION
   Read Trannergy solar converter
   Tested on raspberry pi4

4 Worker threads:
  - serial port reader
  - Trannergy telegram parser to MQTT messages
  - MQTT client
  - HA Discovery


V1.0.0:
  - Initial version

V1.1.0
  - Extend with high(er) frequent read out via tcpclient
  inspired by: https://github.com/jbouwh/omnikdatalogger/blob/dev/apps/omnikdatalogger/omnik/plugin_client/tcpclient.py

V1.2.0
  - Enabled homeassistant autodiscovery

        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 3 of the License, or
        (at your option) any later version.

        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.

        You should have received a copy of the GNU General Public License
        along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

__version__ = "1.2.2"
__author__  = "Hans IJntema"
__license__ = "GPLv3"

import signal
import socket
import time
import sys
import threading

# Local imports
import config as cfg
import trannergy_serial as trannergy
import trannergy_parser as convert
import hadiscovery as ha
import mqtt as mqtt

import trannergy_tcpclient as tcpclient

from log import logger
logger.setLevel(cfg.loglevel)


# ------------------------------------------------------------------------------------
# Instance running?
# ------------------------------------------------------------------------------------
import os
script=os.path.basename(__file__)
script=os.path.splitext(script)[0]

# Ensure that only one instance is started
if sys.platform == "linux":
  lockfile = "\0" + script + "_lockfile"
  try:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    # Create an abstract socket, by prefixing it with null.
    s.bind(lockfile)
    logger.info( f"Starting {__file__}; version = {__version__}" )
  except IOError as err:
    logger.info( f"{lockfile} already running. Exiting; {err}" )
    sys.exit(1)


def close(exit_code):
  """
  Args:
    :param int exit_code: 0 success; 1 error

  Returns:
    None
  """

  logger.info(f"Exitcode = {exit_code} >>")
  sys.exit(exit_code)


# ------------------------------------------------------------------------------------
# LATE GLOBALS
# ------------------------------------------------------------------------------------
trigger = threading.Event()
threads_stopper = threading.Event()
mqtt_stopper = threading.Event()

# mqtt thread
t_mqtt = mqtt.mqttclient(cfg.MQTT_BROKER,
                         cfg.MQTT_PORT,
                         cfg.MQTT_CLIENT_UNIQ,
                         cfg.MQTT_RATE,
                         cfg.MQTT_QOS,
                         cfg.MQTT_USERNAME,
                         cfg.MQTT_PASSWORD,
                         mqtt_stopper,
                         threads_stopper)

telegram = list()

# Select which reader will be used; setup SerialPort thread
try:
  if cfg.INV_READER == "TCPCLIENT":
    t_serial = tcpclient.TaskReadSerial(trigger, threads_stopper, telegram)
  elif cfg.INV_READER == "LISTEN":
    t_serial = trannergy.TaskReadSerial(trigger, threads_stopper, telegram)
  else:
    logger.error(f"Wrong READER specified {cfg.INV_READER}")
    threads_stopper.set()
    t_serial = None
except Exception as e:
  logger.debug(f"Exception {e}")
  threads_stopper.set()
  t_serial = None
  close(1)


# Telegram parser thread
t_parse = convert.ParseTelegrams(trigger, threads_stopper, t_mqtt, telegram)

# Send Home Assistant auto discovery MQTT's
t_discovery = ha.Discovery(threads_stopper, t_mqtt, __version__)

def exit_gracefully(signal, stackframe):
  """
  Exit_gracefully

  Keyword arguments:
    :param int signal: the associated signalnumber
    :param str stackframe: current stack frame
    :return:
  """

  logger.debug(f"Signal {signal}: >>")
  threads_stopper.set()
  logger.info("<<")


def main():
  logger.debug(">>")

  # Set last will/testament
  t_mqtt.will_set(cfg.MQTT_TOPIC_PREFIX + "/status", payload="interrupted", qos=cfg.MQTT_QOS, retain=True)

  # Start all threads
  t_mqtt.start()
  t_parse.start()
  t_discovery.start()
  t_serial.start()

  # Set status to online
  t_mqtt.set_status(cfg.MQTT_TOPIC_PREFIX + "/status", "online", retain=True)
  t_mqtt.do_publish(cfg.MQTT_TOPIC_PREFIX + "/sw-version", f"{__version__}", retain=True)

  # block till t_serial stops receiving telegrams/exits
  t_serial.join()
  logger.debug("t_serial.join exited; set stopper for other threats")
  threads_stopper.set()

  # Set status to offline
  t_mqtt.set_status(cfg.MQTT_TOPIC_PREFIX + "/status", "offline", retain=True)

  # Todo check if MQTT queue is empty before setting stopper
  # Use a simple delay of 1sec before closing mqtt
  time.sleep(1)
  mqtt_stopper.set()

  logger.debug("<<" )
  return

# ------------------------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------------------------
if __name__ == '__main__':
  logger.debug("__main__: >>")
  signal.signal(signal.SIGINT, exit_gracefully)
  signal.signal(signal.SIGTERM, exit_gracefully)

  # start main program
  main()

  logger.debug("__main__: <<")
  close(0)
