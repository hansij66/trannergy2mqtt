"""
  Parses Trannergy telegrams to MQTT messages
  Queue MQTT messages

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

import threading
import copy
import time
import binascii
import json
import config as cfg

# Logging
import __main__
import logging
import os
script = os.path.basename(__main__.__file__)
script = os.path.splitext(script)[0]
logger = logging.getLogger(script + "." + __name__)


class ParseTelegrams(threading.Thread):
  """
  """

  def __init__(self, trigger, stopper, mqtt, telegram):
    """
    Args:
      :param threading.Event() trigger: signals that new telegram is available
      :param threading.Event() stopper: stops thread
      :param mqtt.mqttclient() mqtt: reference to mqtt worker
      :param list() telegram: Trannergy telegram
    """
    logger.debug(">>")
    super().__init__()
    self.__trigger = trigger
    self.__stopper = stopper
    self.__telegram = telegram
    self.__mqtt = mqtt
    self.__prevjsondict = {}

  def __del__(self):
    logger.debug(">>")

  def __publish_telegram(self, json_dict):
    """
    publish the dictionary content

    :param json_dict:
    :return:
    """

    # make resilient against double forward slashes in topic
    topic = cfg.MQTT_TOPIC_PREFIX
    topic = topic.replace('//', '/')
    message = json.dumps(json_dict, sort_keys=True, separators=(',', ':'))
    self.__mqtt.do_publish(topic, message, retain=False)

  def __decode_telegrams(self, telegram):
    """
    Args:
      :param list telegram: counter and actual data

    Returns:

    """
    logger.debug(f">>")
    values = dict()

    # epoch, mqtt timestamp
    ts = int(time.time())
    logger.debug(f"Received telegram0 {telegram[0]}")
    logger.debug(f"Received telegram1 {telegram[1]}")

    counter = telegram[0]
    hexdata = telegram[1]

    # Convert from binary and remove first character
    # offset...deepcopy causes this or adding to a list; not sure why.
    offset = 2

    # Build a dict of key:value, for MQTT JSON
    values["timestamp"] = ts
    values["counter"] = counter

    if cfg.INFLUXDB:
      values["database"] = cfg.INFLUXDB

    # Reference
    # https://github.com/XtheOne/Inverter-Data-Logger/blob/master/InverterMsg.py
    # Current Trannergy is one phase system
    # For 3 phase, uncomment
    values["msg"] = hexdata[24+offset:28+offset]
    values["serial"] = binascii.unhexlify(hexdata[30 + offset:62 + offset]).decode('utf-8')
    values["temperature"] = float(int(hexdata[62+offset:66+offset], 16)) / 10.0
    values["v_pv1"] = float(int(hexdata[66+offset:70+offset], 16)) / 10.0
    values["v_pv2"] = float(int(hexdata[70+offset:74+offset], 16)) / 10.0
    # values["v_pv3"] = float(int(hexdata[74:78], 16))/10
    values["i_pv1"] = float(int(hexdata[78+offset:82+offset], 16)) / 10.0
    values["i_pv2"] = float(int(hexdata[82+offset:86+offset], 16)) / 10.0
    # values["i_pv3"] = float(int(hexdata[86:90], 16))/10
    values["i_ac1"] = int(hexdata[90+offset:94+offset], 16) / 10.0
    # values["i_ac2"] = float(int(hexdata[94:98], 16))/10
    # values["i_ac3"] = float(int(hexdata[98:102], 16))/10
    values["v_ac1"] = float(int(hexdata[102+offset:106+offset], 16)) / 10.0
    # values["v_ac2"] = float(int(hexdata[106:110], 16))/10
    # values["v_ac3"] = float(int(hexdata[110:114], 16))/10
    values["f_ac"] = float(int(hexdata[114+offset:118+offset], 16)) / 100.0
    values["p_ac1"] = int(hexdata[118+offset:122+offset], 16)
    # values["p_ac2"] = float(int(hexdata[122:126], 16))
    # values["p_ac3"] = float(int(hexdata[126:130], 16))
    # unknown = float(int(hexdata[130:134],16))/100
    values["yield_today"] = int(hexdata[138+offset:142+offset], 16) * 10
    #values["yield_yesterday"] = int(hexdata[134+offset:138+offset], 16) * 10  # not implemented
    values["yield_total"] = int(hexdata[142+offset:150+offset], 16) * 100
    values["hrs_total"] = int(hexdata[150+offset:158+offset], 16)
    values["runstate"] = int(hexdata[158 + offset:160 + offset], 16)
    values["GVFault_1"] = int(hexdata[162 + offset:164 + offset], 16)
    values["GVFault_2"] = int(hexdata[166 + offset:168 + offset], 16)
    values["GZFault"] = int(hexdata[170 + offset:172 + offset], 16)
    values["TmpFault"] = int(hexdata[174 + offset:176 + offset], 16)
    values["PVFault"] = int(hexdata[178 + offset:180 + offset], 16)
    values["GFCIFault"] = int(hexdata[182 + offset:184 + offset], 16)


#    1: 1,  # len(1)
#    2: 12,  # msg(12)
#    3: 15,  # id(15)
#    4: 31,  # temperature(31)
#    5: 33,  # v_pv(33,35,37)
#    6: 39,  # i_pv(39,41,43)
#    7: 45,  # i_ac(45,47,49)
#    8: 51,  # v_ac(51,53,55)
#    9: 57,  # f_ac(57,62,65)
#    10: 59,  # p_ac(59,63,67)
#    11: 69,  # e_today(69)
#    12: 71,  # e_total(71)
#    13: 75,  # h_total(75)
#    14: 79,  # run_state(79)
#    15: 81,  # GVFaultValue(81)
#    16: 83,  # GVFaultValue(83)
#    17: 85,  # GZFaultValue(85)
#    18: 87,  # TmpFaultValue(87)
#    19: 89,  # PVFaultValue(89)
#    20: 91,  # GFCIFaultValue(91)
#    21: 93,  # errorMsg(93)
#    22: 101,  # main_fwver(101)
#    23: 121, }  # slave_fwver(121)

    logger.debug(f"Received values = {values}")
    self.__publish_telegram(values)

  def run(self):
    logger.debug(">>")

    while not self.__stopper.is_set():
      # block till event is set, but implement timeout to allow stopper
      self.__trigger.wait(timeout=1)
      if self.__trigger.is_set():
        logger.debug(f"Trigger set")

        # Make copy of the telegram, for further parsing
        telegram = copy.deepcopy(self.__telegram)
        logger.debug(f"Copy after deepcopy = {telegram}")

        # Clear trigger to allow serial reader to read next telegram
        self.__trigger.clear()

        # Clear telegram list for next capture by ReadSerial class
        self.__telegram.clear()

        self.__decode_telegrams(telegram)

    logger.debug("<<")
