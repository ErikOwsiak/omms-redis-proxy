
import datetime
import socket
import os, time, re
import serial, typing as t
from serial.tools import list_ports as ser_tools


BAUDRATES = (9600, 19200, 38400, 57600, 115200)
DEVINFO_QRY = "#GET|DEVINFO!\n"
DEVSN_QRY = "#GET|DEVSN!\n"
RESP_TIMEOUT = 2.0


class sysUtils(object):

   GEOLOC = ""
   BUILDING = ""
   with open("/etc/hostname") as f:
      HOST = f.read().strip()

   def __init__(self):
      self.ports: t.List[serial.Serial] = []
      self.found: {} = {}

   @staticmethod
   def lan_ip():
      try:
         s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
         s.connect(("8.8.8.8", 80))
         lanip = s.getsockname()[0]
         s.close()
         return lanip
      except Exception as e:
         print(e)

   @staticmethod
   def dts_utc():
      d = datetime.datetime.utcnow()
      return f"{d.year}-{d.month:02d}-{d.day:02d}T" \
         f"{d.hour:02d}:{d.minute:02d}:{d.second:02d}"

   @staticmethod
   def syspath(channel: str, endpoint: str):
      try:
         if sysUtils.GEOLOC == "":
            with open("/etc/iotech/geoloc") as f:
               sysUtils.GEOLOC = f.read().strip()
         if sysUtils.BUILDING == "":
            with open("/etc/iotech/building") as f:
               sysUtils.BUILDING = f.read().strip()
         if sysUtils.HOST == "":
            with open("/etc/hostname") as f:
               sysUtils.HOST = f.read().strip()
         # -- -- -- --
         return f"/{sysUtils.GEOLOC}/{sysUtils.BUILDING}/{sysUtils.HOST}/{channel}/{endpoint}"
      except Exception as e:
         print(e)
         exit(1)

   def load_serial_ports(self):
      self.ports = ser_tools.comports()

   def print_ports(self):
      print("-> system ports")
      if self.ports is None or len(self.ports) == 0:
         self.load_serial_ports()
      for p in self.ports:
         print(f"\tport: {p}")
      print("-> done")

   def scan_system(self):
      if self.ports is None:
         self.load_serial_ports()
      for port in self.ports:
         if self.probe_port(port.device):
            break
      # -- --
      print("\n\t-- the end --\n")

   def probe_port(self, dev: str) -> bool:
      for bdrate in BAUDRATES:
         print(f"\nprobing device: {dev} @ {bdrate}")
         try:
            ser: serial.Serial = serial.Serial(port=dev, baudrate=bdrate
               , timeout=RESP_TIMEOUT, dsrdtr=False)
            if not ser.isOpen():
               ser.open()
         except serial.SerialException as e:
            print(e)
            continue
         # send dev query
         self.found[dev] = None
         if not self.__read(ser):
            self.found[dev] = {"Status": "NotFound"}
            return False
         else:
            print(f"GotResponse @ {bdrate}")
            self.found[dev] = {"Status": "Found", "Baudrate": bdrate}
            return True
      # - - - - - - - - - - - - - - - - - -
      return False

   def __read(self, _ser: serial.Serial) -> bool:
      try:
         if self.__read_devinfo(_ser):
            self.__read_serialnum(_ser)
            return True
         else:
            print("NoDevInfoFound!")
            return False
      except serial.SerialTimeoutException as e:
         print(e)
         return False
      except Exception as e:
         print(e)
         return False

   def __read_devinfo(self, _ser: serial.Serial) -> bool:
      print(f"sending: {DEVINFO_QRY}")
      _ser.write_timeout = 1.0
      cnt = _ser.write(bytearray(DEVINFO_QRY.encode("ascii")))
      # print(f"bytes sent: {cnt}")
      time.sleep(RESP_TIMEOUT)
      if _ser.inWaiting() == 0:
         return False
      else:
         # print(f"_ser.inWaiting: {_ser.inWaiting()}")
         buff: str = _ser.read_all().decode("utf-8")
         pos = buff.find("#DEVINFO|")
         if pos != -1:
            sub = buff[pos:-1]
            print(f"found: {sub}")
         return True

   def __read_serialnum(self, _ser: serial.Serial) -> bool:
      print(f"sending: {DEVSN_QRY}")
      _ser.write_timeout = 1.0
      cnt = _ser.write(bytearray(DEVSN_QRY.encode("ascii")))
      # print(f"bytes sent: {cnt}")
      time.sleep(RESP_TIMEOUT)
      if _ser.inWaiting() == 0:
         return False
      else:
         # print(f"_ser.inWaiting: {_ser.inWaiting()}")
         buff: str = _ser.read_all().decode("utf-8")
         pos = buff.find("#DEVINFO|")
         if pos != -1:
            sub = buff[pos:-1]
            print(f"found: {sub}")
         return True
