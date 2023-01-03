#!/usr/bin/env python3

import setproctitle
import time, redis, serial
from core.sysutils import sysUtils


# -- dev --
# DEV_NAME = "/dev/pts/11"
# REDIS_HOST = "localhost"
# REDIS_PORT = 16379
# -- prod --
# DEV_NAME = "/dev/ttyUSB0"
# REDIS_HOST = "10.0.0.122"
# REDIS_PORT = 6379
# -- fixed --
DEV_SPEED = 19200
REDIS_PWD = "Q@@bcd!234##!"
REDIS_PUB_CHANNEL = "CK_PZEM_READER_ROOF"
REDIS_DB_READS = 2
GEOLOC: str = ""
BUILDING: str = ""
HOST: str = ""
CHANNEL: str = "PZEM_READER"
PROC_NAME: str = "PzemRedProxy"


try:
   with open("/etc/iotech/geoloc") as f:
      GEOLOC = f.read().strip()
   with open("/etc/iotech/building") as f:
      BUILDING = f.read().strip()
   with open("/etc/hostname") as f:
      HOST = f.read().strip()
except Exception as e:
   print(e)
   exit(1)


class redisProxy(object):

   def __init__(self, dev, red_host, red_port, red_pwd):
      self.dev = dev
      self.ser: serial.Serial = serial.Serial(port=self.dev, baudrate=DEV_SPEED)
      self.red: redis.Redis = redis.Redis(host=red_host, port=red_port, password=red_pwd)
      self.red.select(REDIS_DB_READS)

   def run(self):
      setproctitle.setproctitle(PROC_NAME)
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
            # -- publish all --
            self.red.publish(REDIS_PUB_CHANNEL, buff)
            # -- #RPT|PZEM:SS_1|F:50.00|V:229.90|A:0.86|W:192.80|kWh:5.94! --
            if buff.startswith("#RPT|PZEM:"):
               arr: [] = buff.split("|")
               pzem_ss = arr[1].split(":")[1]
               arr.insert(1, f"DTSUTC:{sysUtils.dts_utc()}")
               key = f"/{GEOLOC}/{BUILDING}/{HOST}/{CHANNEL}/{pzem_ss}"
               buff = "|".join(arr)
               rval = self.red.set(key, buff)
               print(f"rval: {rval} ~ {buff}")
         time.sleep(0.48)
         # -- -- -- -- -- -- -- -- -- -- -- --
      except Exception as e:
         time.sleep(2.0)
         print(e)


# -- -- test -- --
# if __name__ == "__main__":
#     obj: redisProxy = redisProxy(DEV_NAME)
#     obj.run()
