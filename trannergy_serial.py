"""
Read Trannergy telegrams.


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

import socket
import threading
import time
import binascii

# Logging
import __main__
import logging
import os
script = os.path.basename(__main__.__file__)
script = os.path.splitext(script)[0]
logger = logging.getLogger(script + "." +  __name__)

class TaskReadSerial(threading.Thread):

  def __init__(self, trigger, stopper, telegram):
    """

    Args:
      :param threading.Event() trigger: signals that new telegram is available
      :param threading.Event() stopper: stops thread
      :param list() telegram: dsmr telegram
    """

    logger.debug(">>")
    super().__init__()
    self.__trigger = trigger
    self.__stopper = stopper
    self.__telegram = telegram
    self.__counter = 0

    listen_address = '0.0.0.0'
    listen_port = int('3202')

    try:
      self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.__sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      self.__sock.bind((listen_address, listen_port))
      self.__sock.listen(1)
      self.__sock.settimeout(5.0)
    except Exception as e:
      logger.error(f"Read SOCKS: {type(e).__name__}: {str(e)}")
      self.__stopper.set()
      raise ValueError('Cannot open socks port', listen_address)

  def __del__(self):
    logger.debug(">>")

  def __read_serial(self):
    """
      Reads Trannergy telegrams; stores in global variable (self.__telegram)
      Sets threading event to signal other clients (parser) that
      new telegram is available.
    """
    logger.debug(">>")

    rawdata = None
    while not self.__stopper.is_set():

      # wait till parser has copied telegram content
      # ...we need the opposite of trigger.wait()...block when set; not available
      while self.__trigger.is_set():
        time.sleep(0.1)

      self.__telegram.clear()

      # Wait for a connection with Trannergy
      logger.debug(f"Open socks connection...")
      try:
        conn, addr = self.__sock.accept()
        logger.info(f"Connected to: {str(conn)} {str(addr)}")
      except socket.timeout:
        continue

      # Infinite loop to receive data; conn.recv will time out every 60secs
      data_received = False
      while (not data_received) and (not self.__stopper.is_set()):
        logger.debug(f"connection from {str(addr)}")
        try:
          # Wait for a chunk of data & read; typically timeout after 60sec
          rawdata = conn.recv(1024)
          data_received = True
        except Exception as e:
          logger.warning(f"Exception in receiving data {e}")
          continue

      # convert to more readable
      hexdata = binascii.hexlify(rawdata)

      # Often, a zero length message is received
      # A valid payload is 206 bytes
      if len(hexdata) >= 206:
        # convert to more readable & add to telegram
        logger.debug(f"hexdata = {hexdata}")

        self.__counter += 1

        # add a counter as first field to the list
        self.__telegram.append(f"{self.__counter}")
        self.__telegram.append(f"{hexdata}")
      else:
        logger.debug(f"Data received with insufficient content - restart read loop {len(hexdata)}")
        continue

      # Trigger that new telegram is available for MQTT
      logger.debug("Set trigger")
      self.__trigger.set()

    logger.debug("<<")


  def run(self):
    logger.debug(">>")
    try:
      self.__read_serial()
    except Exception as e:
      logger.error(f"While calling self.__sock.accept(), exception {e} occurred")

    finally:
      self.__stopper.set()
      self.__sock.close()

    logger.debug("<<")
