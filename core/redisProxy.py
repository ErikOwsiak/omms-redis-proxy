#!/usr/bin/env python3

import time
import redis
import serial

# -- dev --
# DEV_NAME = "/dev/pts/7"
# REDIS_HOST = "localhost"
# REDIS_PORT = 16379
# -- prod --
DEV_NAME = "/dev/ttyUSB0"
REDIS_HOST = "10.0.0.122"
REDIS_PORT = 6379
# -- fixed --
REDIS_PWD = "Q@@bcd!234##!"
REDIS_PUB_CHANNEL = "CK_PZEM_READER_ROOF"


class redisProxy(object):

   def __init__(self, dev):
      self.dev = dev
      self.ser: serial.Serial = serial.Serial(port=self.dev)
      self.red: redis.Redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PWD)

   def run(self):
      while True:
         buff = None
         if self.ser.inWaiting():
            buff = self.__read_string()
         if buff is not None:
            print(buff)
            self.red.publish(REDIS_PUB_CHANNEL, buff)
         time.sleep(0.480)

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


# -- -- test -- --
if __name__ == "__main__":
    obj: redisProxy = redisProxy(DEV_NAME)
    obj.run()
