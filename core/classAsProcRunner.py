
import time
import multiprocessing as mp


class classAsProcRunner(object):

   def __init__(self, procname: str, obj: object, method2run: str):
      self.procname = procname
      self.obj = obj
      self.method2run = method2run
      self.proc = None
      self._target = None

   def init(self):
      self._target = getattr(self.obj, self.method2run)
      if self._target is None:
         raise Exception(f"MethodNotFound: {self.method2run}")

   def run_main_loop(self):
      while True:
         try:
            if self.proc is None:
               self.proc: mp.Process = mp.Process(target=self._target, name=self.procname)
            if not self.proc.is_alive():
               if self.proc.exitcode:
                  self.proc: mp.Process = mp.Process(target=self._target, name=self.procname)
               self.proc.start()
            else:
               pass
            # -- dump info --
            print(f"run_main_loop: {self.proc.name}")
            time.sleep(8.0)
         except Exception as e:
            print(e)
            continue
