#!/usr/bin/env python3

import configparser as cp
import time, serial
from core.utils import sysUtils
from core.redisProxy import redisProxy


class serialReader(object):

   def __init__(self, procname: str, _cp: cp.ConfigParser, red: redisProxy):
      self.procname = procname
      self.cp = _cp
      self.dev: str = str(self.cp["SERIAL"]["DEV"])
      self.baudrate: int = int(self.cp["SERIAL"]["BAUDRATE"])
      self.ser: serial.Serial = serial.Serial(port=self.dev, baudrate=self.baudrate)
      self.red_proxy: redisProxy = red
      self.channel = str(self.cp["SYSPATH"]["CHANNEL"])

   def run(self):
      while True:
         self.__run_loop()

   def __read_string(self) -> str:
      barr: bytearray = bytearray()
      while True:
         __char = self.ser.read()
         # -- start char --
         if chr(__char[0]) == '#':
            barr.clear()
         barr.extend(__char)
         # -- test end --
         if chr(__char[0]) == '!':
            break
      # -- --
      return barr.decode("utf-8")

   def __run_loop(self):
      try:
         # -- -- -- -- -- -- -- -- -- -- -- --
         buff = None
         if self.ser.inWaiting():
            buff = self.__read_string()
         # -- -- -- -- -- -- -- -- -- -- -- --
         if buff is not None:
            print(buff)
            self.red_proxy.pub_diag_debug(buff)
            # -- #RPT|PZEM:SS_1|F:50.00|V:229.90|A:0.86|W:192.80|kWh:5.94! --
            if buff.startswith("#RPT|PZEM:SS_"):
               arr: [] = buff.split("|")
               pzem_ss = arr[1].split(":")[1]
               arr.insert(1, f"DTSUTC:{sysUtils.dts_utc()}")
               syspath: str = sysUtils.syspath(self.channel, pzem_ss)
               arr.insert(2, f"PATH:{syspath}")
               buff = "|".join(arr)
               # -- -- publish & set -- --
               self.red_proxy.pub_read(buff)
               self.red_proxy.save_read(syspath, buff)
               self.red_proxy.save_heartbeat(syspath, buff)
               # -- -- -- --
         time.sleep(0.48)
         # -- -- -- -- -- -- -- -- -- -- -- --
      except Exception as e:
         time.sleep(2.0)
         print(e)
