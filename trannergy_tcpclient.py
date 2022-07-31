"""
Read Trannergy telegrams via TCP Client.


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
import config as cfg
#import inverter_msg as msg

# Logging
import __main__
import logging
import os
script = os.path.basename(__main__.__file__)
script = os.path.splitext(script)[0]
logger = logging.getLogger(script + "." + __name__)


class TaskReadSerial(threading.Thread):

  def __init__(self, trigger, stopper, telegram):
    """
    Args:
      :param threading.Event() trigger: signals that new telegram is available
      :param threading.Event() stopper: stops thread
      :param list() telegram: trannergy telegram
    """

    logger.debug(">>")
    super().__init__()
    self.__trigger = trigger
    self.__stopper = stopper
    self.__telegram = telegram
    self.__counter = 0
    self.__lastread = 0
    self.__interval = 3600/cfg.INV_READ_RATE
    self.__requestmsg = self.__request_string(cfg.INV_SERIAL_LOGGER)
    self.__sock = None

  def __del__(self):
    logger.debug(">>")

  def __socket_connect(self):
    """
    Create socket/connection to inverter
    """

    # Exit after too many attempts
    counter = 0

    while not self.__stopper.is_set():
      try:
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__sock.connect((cfg.INV_IP, cfg.INV_TCPCLIENTPORT))
        return
      except Exception as e:
        logger.info(f"Read SOCKS: {type(e).__name__}: {str(e)}")
        time.sleep(30)
        counter += 1
        if counter > cfg.INV_MAXRETRIES:
          self.__stopper.set()

  def __request_string(self, ser):
    """
    Reuse from
    https://github.com/jbouwh/omnikdatalogger/blob/dev/apps/omnikdatalogger/omnik/InverterMsg.py
    The request string is build from several parts. The first part is a
    fixed 4 char string; the second part is the reversed hex notation of
    the Wi-Fi logger s/n twice; then again a fixed string of two chars; a checksum of
    the double s/n with an offset; and finally a fixed ending char.

    Args:
      :param str ser: s/n inverter wifi module
    """
    responseString = b"\x68\x02\x40\x30"

    doublehex = hex(ser)[2:] * 2
    hexlist = [
      bytes.fromhex(doublehex[i: i + 2])
      for i in reversed(range(0, len(doublehex), 2))
    ]

    cs_count = 115 + sum([ord(c) for c in hexlist])
    cs = bytes.fromhex(hex(cs_count)[-2:])
    responseString += b"".join(hexlist) + b"".join([b"\x01\x00", cs, b"\x16"])
    return responseString

  def __read_serial(self):
    """
      Reads Trannergy telegrams; stores in global variable (self.__telegram)
      Sets threading event to signal other clients (parser) that
      new telegram is available.

      :raises Exceptions
    """
    logger.debug(">>")

    while not self.__stopper.is_set():

      # wait till parser has copied telegram content
      # ...we need the opposite of trigger.wait()...block when set; not available
      while self.__trigger.is_set():
        time.sleep(0.5)

      self.__telegram.clear()

      # Sending request message to Inverter
      self.__sock.sendall(self.__requestmsg)

      # Wait for response (listen and block thread)
      rawdata = self.__sock.recv(1024)

      serial = str(rawdata[15:31], encoding="UTF-8")

      logger.debug(f"SERIAL={serial}")
      if serial != cfg.INV_SERIAL:
        logger.debug(f"INCORRECT MESSAGE={serial}")
        # try again...start over....
        continue

      # convert to more readable
      hexdata = binascii.hexlify(rawdata)
      #hexdata = str(binascii.b2a_base64(rawmsg))

      ## Often, a zero length message is received
      ## A valid payload is 206 bytes
      #if len(hexdata) >= 206:
      # convert to more readable & add to telegram
      logger.debug(f"hexdata = {hexdata}")

      self.__counter += 1

      # add a counter as first field to the list
      self.__telegram.append(f"{self.__counter}")
      self.__telegram.append(f"{hexdata}")

      # Trigger that new telegram is available for MQTT
      logger.debug("Set trigger")
      self.__trigger.set()

      while not self.__stopper.is_set():
        t_elapsed = int(time.time()) - self.__lastread
        if t_elapsed > self.__interval:
            self.__lastread = int(time.time())
            break
        else:
          # wait...
          time.sleep(1)

    logger.debug("<<")

  def run(self):
    logger.debug(">>")

    self.__socket_connect()

    while not self.__stopper.is_set():
      try:
        self.__read_serial()
      except Exception as e:
        logger.warning(f"Exception {e}")
        time.sleep(10)
        self.__sock.close()
        self.__socket_connect()

    self.__sock.close()

    logger.debug("<<")
