#!/usr/bin/env python3

import hashlib
import redis, configparser as cp
try:
   from core.utils import sysUtils as utils
   from core.logutils import logUtils
except:
   # -- in package testing --
   from utils import sysUtils as utils
   from logutils import logUtils


class redisProxy(object):

   def __init__(self, conf: cp.ConfigParser, CONN_SEC: str = "PROD_REDIS_CONN"):
      self.cp = conf
      self.CONN_SEC = CONN_SEC
      self.host = self.cp[self.CONN_SEC]["HOST"]
      self.port: int = int(self.cp[self.CONN_SEC]["PORT"])
      self.pwd = self.cp["REDIS"]["PWD"]
      self.red: redis.Redis = redis.Redis(host=self.host, port=self.port, password=self.pwd)
      self.host_ping: bool = self.__ping_host()

   def save_read(self, path: str, buff: str):
      try:
         read_db_idx = int(self.cp["REDIS"]["DB_IDX_READS"])
         self.red.select(read_db_idx)
         md5 = hashlib.md5(bytearray(buff.encode("utf-8")))
         md5str = f"0x{md5.hexdigest().upper()}"
         last_msg_dtsutc = utils.dts_utc()
         _dict = {"dts_utc": last_msg_dtsutc, "msg_md5": md5str, "msg": buff}
         rv = self.red.delete(path)
         print(f"rv: {rv}")
         rv = self.red.hset(path, mapping=_dict)
         print(f"rv: {rv}")
      except Exception as e:
         logUtils.log_exp(e)

   def pub_diag_debug(self, buff: str):
      channel: str = self.cp["REDIS"]["PUB_DIAG_DEBUG_CHANNEL"]
      rv = self.red.publish(channel, buff)
      print(f"rv: {rv}")

   def pub_read(self, buff: str):
      channel: str = self.cp["REDIS"]["PUB_READS_CHANNEL"]
      rv = self.red.publish(channel, buff)
      print(f"rv: {rv}")

   def save_heartbeat(self, path: str, buff: str):
      try:
         heartbeat_db_idx: int = int(self.cp["REDIS"]["DB_IDX_HEARTBEATS"])
         heartbeat_ttl: int = int(self.cp["REDIS"]["HEARTBEAT_TTL"])
         self.red.select(heartbeat_db_idx)
         md5 = hashlib.md5(bytearray(buff.encode("utf-8")))
         md5str = f"0x{md5.hexdigest().upper()}"
         last_msg_dtsutc = utils.dts_utc()
         _dict = {"last_msg_dts_utc": last_msg_dtsutc, "last_msg_md5": md5str}
         rv = self.red.hset(path, mapping=_dict)
         if heartbeat_ttl not in [None, -1]:
            self.red.expire(path, heartbeat_ttl)
         print(f"rv: {rv}")
      except Exception as e:
         logUtils.log_exp(e)

   def __ping_host(self) -> bool:
      try:
         return self.red.ping()
      except Exception as e:
         print(e)
         return False


# -- -- test -- --
if __name__ == "__main__":
    _cp: cp.ConfigParser = cp.ConfigParser()
    _cp.read("../conf/conf.ini")
    rp: redisProxy = redisProxy(_cp, CONN_SEC="DEV_REDIS_CONN")
    rp.pub_diag_debug("hello")
    rp.pub_read("xxxxxxxxxxxxxxxxxxxxxx")
    rp.save_read("xxxx", "asdfasdfasdfasdfasfdasfdasfdf")
    rp.save_heartbeat("xxxxxx", "asdfasdfasfasfasfassafasfasfasfasdf")
