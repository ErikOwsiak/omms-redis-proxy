#!/usr/bin/env python3

import setproctitle
import configparser as cp
import time, serial
from core.utils import sysUtils
from core.redisProxy import redisProxy


# -- dev --
# DEV_NAME = "/dev/pts/11"
# REDIS_HOST = "localhost"
# REDIS_PORT = 16379
# -- prod --
# DEV_NAME = "/dev/ttyUSB0"
# REDIS_HOST = "10.0.0.122"
# REDIS_PORT = 6379
# -- fixed --
# DEV_SPEED = 19200
# REDIS_PWD = "Q@@bcd!234##!"
# DIAGNOSTICS_DEBUG = "DIAGNOSTICS_DEBUG"
# REDIS_PUB_CHANNEL_READS = "CK_PZEM_READER_ROOF_READS"
# REDIS_DB_READS = 2
# GEOLOC: str = ""
# BUILDING: str = ""
# HOST: str = ""
# CHANNEL: str = "PZEM_READER"
# PROC_NAME: str = "PzemRedProxy"

# try:
#    with open("/etc/iotech/geoloc") as f:
#       GEOLOC = f.read().strip()
#    with open("/etc/iotech/building") as f:
#       BUILDING = f.read().strip()
#    with open("/etc/hostname") as f:
#       HOST = f.read().strip()
# except Exception as e:
#    print(e)
#    exit(1)


class serialReader(object):

   def __init__(self, _cp: cp.ConfigParser, red: redisProxy):
      self.cp = _cp
      self.dev: str = str(self.cp["SERIAL"]["DEV"])
      self.baudrate: int = int(self.cp["SERIAL"]["BAUDRATE"])
      self.ser: serial.Serial = serial.Serial(port=self.dev, baudrate=self.baudrate)
      self.red_proxy: redisProxy = red
      self.channel = str(self.cp["SYSPATH"]["CHANNEL"])

   def run(self):
      setproctitle.setproctitle("SER_RED_PROXY")
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
         # hr1secs = 3600
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
               # key = f"/{GEOLOC}/{BUILDING}/{HOST}/{CHANNEL}/{pzem_ss}"
               arr.insert(2, f"PATH:{syspath}")
               buff = "|".join(arr)
               # -- -- publish & set -- --
               self.red_proxy.pub_read(buff)
               self.red_proxy.save_read(syspath, buff)
               # -- -- -- --
         time.sleep(0.48)
         # -- -- -- -- -- -- -- -- -- -- -- --
      except Exception as e:
         time.sleep(2.0)
         print(e)


# -- -- test -- --
# if __name__ == "__main__":
#     obj: serialReader = serialReader(DEV_NAME)
#     obj.run()
